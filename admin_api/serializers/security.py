from rest_framework import serializers

from index.models import ActiveSession, UserActivityLog


class AdminUserActivityLogSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True, default=None)

    class Meta:
        model = UserActivityLog
        fields = (
            'id', 'user', 'user_email', 'email', 'action', 'ip_address',
            'user_agent', 'device_fingerprint', 'risk_level',
            'details', 'created_at',
        )


class AdminActiveSessionSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = ActiveSession
        fields = (
            'id', 'user', 'user_email', 'user_name', 'token_key',
            'ip_address', 'user_agent', 'device_fingerprint',
            'device_name', 'is_current', 'last_activity', 'created_at',
        )

    def get_user_name(self, obj):
        return f"{obj.user.firstname} {obj.user.lastname}"


class AdminThrottleResetSerializer(serializers.Serializer):
    scope = serializers.ChoiceField(
        choices=[
            ('all', 'All scopes'),
            ('login', 'Login lockout'),
            ('register', 'Registration rate limit'),
            ('password_reset', 'Password reset rate limit'),
            ('resend_activation', 'Resend activation rate limit'),
        ],
        default='all',
    )
    ip_address = serializers.IPAddressField(
        required=False, allow_null=True,
        help_text='Specific IP to reset. If blank, resets for all IPs.',
    )
    user_id = serializers.IntegerField(
        required=False, allow_null=True,
        help_text='User ID to reset DRF throttle for.',
    )


class AdminRevokeSessionSerializer(serializers.Serializer):
    session_id = serializers.IntegerField(
        required=False, allow_null=True,
        help_text='Specific session to revoke',
    )
    revoke_all = serializers.BooleanField(
        required=False, default=False,
        help_text='Revoke all sessions for the user',
    )
    user_id = serializers.IntegerField(
        help_text='User whose sessions to revoke',
    )


class AdminSecurityAlertSerializer(serializers.Serializer):
    """Summary of security alerts for the dashboard."""
    failed_logins_24h = serializers.IntegerField()
    lockouts_24h = serializers.IntegerField()
    new_devices_24h = serializers.IntegerField()
    concurrent_sessions = serializers.IntegerField()
    high_risk_events_24h = serializers.IntegerField()
    users_with_multiple_sessions = serializers.ListField(
        child=serializers.DictField(),
    )
    recent_high_risk = serializers.ListField(
        child=serializers.DictField(),
    )
