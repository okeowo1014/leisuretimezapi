"""
Security utilities for user activity logging, device fingerprinting,
and session management.
"""

import hashlib
import logging

from django.utils import timezone

logger = logging.getLogger(__name__)


def get_client_ip(request):
    """Extract the real client IP from the request."""
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')


def get_user_agent(request):
    """Get the User-Agent string from request headers."""
    return request.META.get('HTTP_USER_AGENT', '')


def get_device_fingerprint(ip, user_agent):
    """Generate a SHA-256 fingerprint from IP + User-Agent."""
    raw = f"{ip}|{user_agent}"
    return hashlib.sha256(raw.encode()).hexdigest()


def parse_device_name(user_agent):
    """Extract a human-readable device/browser name from User-Agent."""
    ua = user_agent.lower()

    # Browser detection
    browser = 'Unknown Browser'
    if 'edg/' in ua or 'edge/' in ua:
        browser = 'Edge'
    elif 'opr/' in ua or 'opera' in ua:
        browser = 'Opera'
    elif 'chrome/' in ua and 'safari/' in ua:
        browser = 'Chrome'
    elif 'firefox/' in ua:
        browser = 'Firefox'
    elif 'safari/' in ua:
        browser = 'Safari'
    elif 'postman' in ua:
        browser = 'Postman'
    elif 'curl' in ua:
        browser = 'cURL'

    # OS detection
    os_name = 'Unknown OS'
    if 'iphone' in ua or 'ipad' in ua:
        os_name = 'iOS'
    elif 'android' in ua:
        os_name = 'Android'
    elif 'mac os' in ua or 'macintosh' in ua:
        os_name = 'macOS'
    elif 'windows' in ua:
        os_name = 'Windows'
    elif 'linux' in ua:
        os_name = 'Linux'

    return f"{browser} on {os_name}"


def log_user_activity(user, action, request=None, risk_level='low',
                      details=None, email=None):
    """Create a UserActivityLog entry.

    Can be called with or without a request (e.g. from management commands).
    """
    from index.models import UserActivityLog

    ip = get_client_ip(request) if request else ''
    ua = get_user_agent(request) if request else ''
    fingerprint = get_device_fingerprint(ip, ua) if ip else ''

    return UserActivityLog.objects.create(
        user=user,
        email=email or (user.email if user else ''),
        action=action,
        ip_address=ip or None,
        user_agent=ua,
        device_fingerprint=fingerprint,
        risk_level=risk_level,
        details=details or {},
    )


def create_or_update_session(user, token_key, request):
    """Create or update an ActiveSession for the given token.

    Returns (session, is_new, concurrent_count).
    """
    from index.models import ActiveSession

    ip = get_client_ip(request)
    ua = get_user_agent(request)
    fingerprint = get_device_fingerprint(ip, ua)
    device_name = parse_device_name(ua)

    session, created = ActiveSession.objects.update_or_create(
        token_key=token_key,
        defaults={
            'user': user,
            'ip_address': ip,
            'user_agent': ua,
            'device_fingerprint': fingerprint,
            'device_name': device_name,
            'is_current': True,
            'last_activity': timezone.now(),
        },
    )

    # Count other active sessions for this user
    concurrent_count = ActiveSession.objects.filter(
        user=user, is_current=True,
    ).exclude(token_key=token_key).count()

    return session, created, concurrent_count


def end_session(token_key):
    """Mark a session as ended when a user logs out or token expires."""
    from index.models import ActiveSession

    ActiveSession.objects.filter(token_key=token_key).update(
        is_current=False,
    )


def check_new_device(user, fingerprint):
    """Check if this device fingerprint is new for the user.

    Returns True if the fingerprint has never been seen before.
    """
    from index.models import UserActivityLog

    return not UserActivityLog.objects.filter(
        user=user,
        device_fingerprint=fingerprint,
        action='login_success',
    ).exists()
