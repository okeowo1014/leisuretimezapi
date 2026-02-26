"""
Custom middleware for the Leisuretimez platform.
"""

from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework.authtoken.models import Token


class TokenExpiryMiddleware:
    """Expire authentication tokens after a configurable duration.

    Controlled by ``settings.TOKEN_EXPIRY_HOURS``.  When set to ``0``
    (the default in development), tokens never expire.

    On expiry the token is deleted and the request proceeds as
    unauthenticated — DRF's permission classes will then return 401.
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
                    token.delete()
                    # Clear auth header so DRF treats as unauthenticated
                    request.META.pop('HTTP_AUTHORIZATION', None)
            except Token.DoesNotExist:
                pass

        return self.get_response(request)
