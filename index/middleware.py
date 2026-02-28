"""
Custom middleware for the Leisuretimez platform.
"""

import logging
from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework.authtoken.models import Token

logger = logging.getLogger(__name__)


class TokenExpiryMiddleware:
    """Expire authentication tokens after a configurable duration.

    Controlled by ``settings.TOKEN_EXPIRY_HOURS``.  When set to ``0``
    (the default in development), tokens never expire.

    On expiry the token is deleted and the request proceeds as
    unauthenticated — DRF's permission classes will then return 401.
    Also logs the token expiry and ends the associated session.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        expiry_hours = getattr(settings, 'TOKEN_EXPIRY_HOURS', 0)

        if expiry_hours and request.META.get('HTTP_AUTHORIZATION', '').startswith('Token '):
            token_key = request.META['HTTP_AUTHORIZATION'].split(' ', 1)[1].strip()
            try:
                token = Token.objects.get(key=token_key)
                if token.created < timezone.now() - timedelta(hours=expiry_hours):
                    user = token.user
                    token.delete()
                    # Clear auth header so DRF treats as unauthenticated
                    request.META.pop('HTTP_AUTHORIZATION', None)

                    # Log expiry and end session
                    try:
                        from index.security import end_session, log_user_activity
                        end_session(token_key)
                        log_user_activity(
                            user, 'token_expired', request,
                            details={'token_key_prefix': token_key[:8]},
                        )
                    except Exception:
                        logger.exception("Error logging token expiry")
            except Token.DoesNotExist:
                pass

        return self.get_response(request)


class SessionActivityMiddleware:
    """Update last_activity on the user's active session for each request.

    Only fires for authenticated requests with a Token header.
    Throttled to once per 5 minutes to avoid excessive DB writes.
    """

    UPDATE_INTERVAL_SECONDS = 300  # 5 minutes

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Only track for authenticated token-based requests
        if (
            request.META.get('HTTP_AUTHORIZATION', '').startswith('Token ')
            and hasattr(request, 'user')
            and request.user.is_authenticated
        ):
            try:
                token_key = request.META['HTTP_AUTHORIZATION'].split(' ', 1)[1].strip()
                from index.models import ActiveSession
                session = ActiveSession.objects.filter(
                    token_key=token_key, is_current=True,
                ).first()
                if session:
                    # Only update if enough time has passed
                    cutoff = timezone.now() - timedelta(seconds=self.UPDATE_INTERVAL_SECONDS)
                    if session.last_activity < cutoff:
                        session.last_activity = timezone.now()
                        session.save(update_fields=['last_activity'])
            except Exception:
                pass  # Never break the request over session tracking

        return response
