from django.core.cache import cache
from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView

from admin_api.permissions import IsAdminStaff
from admin_api.serializers.security import (
    AdminActiveSessionSerializer, AdminRevokeSessionSerializer,
    AdminThrottleResetSerializer, AdminUserActivityLogSerializer,
)
from index.models import ActiveSession, CustomUser, UserActivityLog


# ---------------------------------------------------------------------------
# Throttle / Rate-Limit Reset
# ---------------------------------------------------------------------------

class AdminThrottleResetView(APIView):
    """Reset throttle/rate-limit locks for a specific user or IP."""
    permission_classes = [IsAdminStaff]

    # Cache key patterns used by auth_views.py and DRF
    SCOPE_KEYS = {
        'login': ['login_lockout:{ip}', 'login_attempts:{ip}'],
        'register': ['register:{ip}'],
        'password_reset': ['password_reset:{ip}'],
        'resend_activation': ['resend_activation:{ip}'],
    }

    def post(self, request):
        serializer = AdminThrottleResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        scope = data.get('scope', 'all')
        ip = data.get('ip_address')
        user_id = data.get('user_id')

        cleared = []

        # Clear custom rate-limit keys (from auth_views.py)
        if ip:
            scopes = self.SCOPE_KEYS.keys() if scope == 'all' else [scope]
            for s in scopes:
                if s in self.SCOPE_KEYS:
                    for pattern in self.SCOPE_KEYS[s]:
                        key = pattern.format(ip=ip)
                        if cache.get(key) is not None:
                            cache.delete(key)
                            cleared.append(key)

        # Clear DRF's built-in throttle keys for a specific user
        if user_id:
            try:
                user = CustomUser.objects.get(pk=user_id)
                # DRF ScopedRateThrottle and UserRateThrottle key patterns
                throttle_scopes = ['registration', 'password_reset', 'payment', 'user']
                for ts in throttle_scopes:
                    key = f'throttle_{ts}_{user.pk}'
                    cache.delete(key)
                    cleared.append(key)
            except CustomUser.DoesNotExist:
                return Response(
                    {'error': 'User not found'},
                    status=status.HTTP_404_NOT_FOUND,
                )

        # If no specific target, clear all throttle keys for the IP
        if not ip and not user_id:
            return Response(
                {'error': 'Provide ip_address or user_id (or both).'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({
            'detail': f'Throttle/rate-limit reset. Cleared {len(cleared)} cache key(s).',
            'cleared_keys': cleared,
            'scope': scope,
            'ip_address': ip,
            'user_id': user_id,
        })


# ---------------------------------------------------------------------------
# User Activity Logs
# ---------------------------------------------------------------------------

class AdminActivityLogListView(generics.ListAPIView):
    """List all user activity logs with filters."""
    permission_classes = [IsAdminStaff]
    serializer_class = AdminUserActivityLogSerializer

    def get_queryset(self):
        qs = UserActivityLog.objects.select_related('user').order_by('-created_at')

        # Filters
        user_id = self.request.query_params.get('user')
        if user_id:
            qs = qs.filter(user_id=user_id)

        action = self.request.query_params.get('action')
        if action:
            qs = qs.filter(action=action)

        risk_level = self.request.query_params.get('risk_level')
        if risk_level:
            qs = qs.filter(risk_level=risk_level)

        ip = self.request.query_params.get('ip')
        if ip:
            qs = qs.filter(ip_address=ip)

        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(
                Q(email__icontains=search) |
                Q(ip_address__icontains=search) |
                Q(user__email__icontains=search)
            )

        date_from = self.request.query_params.get('date_from')
        if date_from:
            qs = qs.filter(created_at__date__gte=date_from)

        date_to = self.request.query_params.get('date_to')
        if date_to:
            qs = qs.filter(created_at__date__lte=date_to)

        return qs


class AdminUserActivityLogView(generics.ListAPIView):
    """Activity logs for a specific user."""
    permission_classes = [IsAdminStaff]
    serializer_class = AdminUserActivityLogSerializer

    def get_queryset(self):
        return UserActivityLog.objects.filter(
            user_id=self.kwargs['pk']
        ).order_by('-created_at')


# ---------------------------------------------------------------------------
# Active Sessions
# ---------------------------------------------------------------------------

class AdminActiveSessionListView(generics.ListAPIView):
    """List all active sessions, optionally filtered."""
    permission_classes = [IsAdminStaff]
    serializer_class = AdminActiveSessionSerializer

    def get_queryset(self):
        qs = ActiveSession.objects.select_related('user').order_by('-last_activity')

        user_id = self.request.query_params.get('user')
        if user_id:
            qs = qs.filter(user_id=user_id)

        is_current = self.request.query_params.get('is_current')
        if is_current is not None:
            qs = qs.filter(is_current=is_current.lower() == 'true')
        else:
            # By default only show active sessions
            qs = qs.filter(is_current=True)

        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(
                Q(user__email__icontains=search) |
                Q(ip_address__icontains=search) |
                Q(device_name__icontains=search)
            )

        return qs


class AdminUserSessionsView(generics.ListAPIView):
    """All sessions for a specific user."""
    permission_classes = [IsAdminStaff]
    serializer_class = AdminActiveSessionSerializer

    def get_queryset(self):
        return ActiveSession.objects.filter(
            user_id=self.kwargs['pk']
        ).order_by('-last_activity')


class AdminRevokeSessionView(APIView):
    """Revoke one or all sessions for a user (force logout)."""
    permission_classes = [IsAdminStaff]

    def post(self, request):
        serializer = AdminRevokeSessionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user_id = data['user_id']
        try:
            user = CustomUser.objects.get(pk=user_id)
        except CustomUser.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND,
            )

        revoked_count = 0

        if data.get('revoke_all'):
            # Revoke all sessions and delete all tokens
            sessions = ActiveSession.objects.filter(user=user, is_current=True)
            revoked_count = sessions.count()
            token_keys = list(sessions.values_list('token_key', flat=True))
            sessions.update(is_current=False)
            Token.objects.filter(user=user).delete()

            from index.security import log_user_activity
            log_user_activity(
                user, 'suspicious_activity', request,
                risk_level='high',
                details={
                    'action': 'admin_revoked_all_sessions',
                    'revoked_by': request.user.email,
                    'sessions_revoked': revoked_count,
                },
            )

        elif data.get('session_id'):
            try:
                session = ActiveSession.objects.get(
                    pk=data['session_id'], user=user,
                )
                session.is_current = False
                session.save(update_fields=['is_current'])
                Token.objects.filter(key=session.token_key).delete()
                revoked_count = 1

                from index.security import log_user_activity
                log_user_activity(
                    user, 'suspicious_activity', request,
                    risk_level='medium',
                    details={
                        'action': 'admin_revoked_session',
                        'revoked_by': request.user.email,
                        'session_id': session.pk,
                        'device': session.device_name,
                    },
                )
            except ActiveSession.DoesNotExist:
                return Response(
                    {'error': 'Session not found'},
                    status=status.HTTP_404_NOT_FOUND,
                )
        else:
            return Response(
                {'error': 'Provide session_id or set revoke_all to true.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({
            'detail': f'Revoked {revoked_count} session(s) for {user.email}.',
            'revoked_count': revoked_count,
        })


# ---------------------------------------------------------------------------
# Security Dashboard / Alerts
# ---------------------------------------------------------------------------

class AdminSecurityDashboardView(APIView):
    """Aggregated security alerts and metrics."""
    permission_classes = [IsAdminStaff]

    def get(self, request):
        now = timezone.now()
        last_24h = now - timezone.timedelta(hours=24)
        last_7d = now - timezone.timedelta(days=7)

        # 24h metrics
        logs_24h = UserActivityLog.objects.filter(created_at__gte=last_24h)

        failed_logins = logs_24h.filter(action='login_failed').count()
        lockouts = logs_24h.filter(action='lockout_triggered').count()
        new_devices = logs_24h.filter(action='new_device').count()
        concurrent = logs_24h.filter(action='concurrent_session').count()
        high_risk = logs_24h.filter(
            risk_level__in=['high', 'critical']
        ).count()

        # Users with multiple active sessions right now
        multi_session_users = (
            ActiveSession.objects
            .filter(is_current=True)
            .values('user__id', 'user__email', 'user__firstname', 'user__lastname')
            .annotate(session_count=Count('id'))
            .filter(session_count__gt=1)
            .order_by('-session_count')[:20]
        )

        users_with_multiple = [
            {
                'user_id': u['user__id'],
                'email': u['user__email'],
                'name': f"{u['user__firstname']} {u['user__lastname']}",
                'active_sessions': u['session_count'],
            }
            for u in multi_session_users
        ]

        # Recent high-risk events
        recent_high = UserActivityLog.objects.filter(
            risk_level__in=['high', 'critical'],
            created_at__gte=last_7d,
        ).select_related('user').order_by('-created_at')[:20]

        recent_high_data = [
            {
                'id': log.id,
                'action': log.action,
                'email': log.email,
                'ip_address': log.ip_address,
                'risk_level': log.risk_level,
                'details': log.details,
                'created_at': log.created_at.isoformat(),
            }
            for log in recent_high
        ]

        # IP addresses with most failed logins (last 7 days)
        suspicious_ips = (
            UserActivityLog.objects
            .filter(action='login_failed', created_at__gte=last_7d)
            .values('ip_address')
            .annotate(failure_count=Count('id'))
            .filter(failure_count__gte=5)
            .order_by('-failure_count')[:10]
        )

        return Response({
            'summary': {
                'failed_logins_24h': failed_logins,
                'lockouts_24h': lockouts,
                'new_devices_24h': new_devices,
                'concurrent_session_alerts_24h': concurrent,
                'high_risk_events_24h': high_risk,
            },
            'users_with_multiple_sessions': users_with_multiple,
            'recent_high_risk_events': recent_high_data,
            'suspicious_ips': list(suspicious_ips),
        })
