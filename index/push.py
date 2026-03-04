"""
Firebase Cloud Messaging (FCM) push notification service.

Initializes the Firebase Admin SDK once and provides helpers to send
push notifications to individual users or in bulk.

Controlled by settings:
  - FCM_ENABLED: Master switch (default False)
  - FIREBASE_CREDENTIALS_PATH: Path to service account JSON key file
"""

import logging

from django.conf import settings

logger = logging.getLogger(__name__)

_firebase_app = None


def _init_firebase():
    """Lazily initialize the Firebase Admin SDK (once per process)."""
    global _firebase_app
    if _firebase_app is not None:
        return _firebase_app

    creds_path = getattr(settings, 'FIREBASE_CREDENTIALS_PATH', '')
    if not creds_path:
        logger.warning("FIREBASE_CREDENTIALS_PATH not set — push notifications disabled")
        return None

    try:
        import firebase_admin
        from firebase_admin import credentials

        cred = credentials.Certificate(creds_path)
        _firebase_app = firebase_admin.initialize_app(cred)
        logger.info("Firebase Admin SDK initialized")
        return _firebase_app
    except Exception:
        logger.exception("Failed to initialize Firebase Admin SDK")
        return None


def _is_enabled():
    """Check if FCM push is enabled and Firebase is ready."""
    if not getattr(settings, 'FCM_ENABLED', False):
        return False
    return _init_firebase() is not None


def send_push_to_user(user, title, body, data=None, notification_type=None):
    """Send a push notification to all active devices of a user.

    Args:
        user: CustomUser instance
        title: Notification title
        body: Notification body text
        data: Optional dict of extra data (must be string values)
        notification_type: Optional type string for client-side routing

    Returns:
        Number of successfully delivered pushes.
    """
    if not _is_enabled():
        return 0

    from firebase_admin import messaging
    from index.models import PushDevice

    devices = PushDevice.objects.filter(user=user, is_active=True)
    if not devices.exists():
        return 0

    tokens = list(devices.values_list('fcm_token', flat=True))

    # Build the data payload (FCM data must be string values)
    payload = data or {}
    if notification_type:
        payload['notification_type'] = notification_type
    payload = {k: str(v) for k, v in payload.items()}

    message = messaging.MulticastMessage(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        data=payload,
        tokens=tokens,
        # Android-specific: high priority, auto-expand
        android=messaging.AndroidConfig(
            priority='high',
            notification=messaging.AndroidNotification(
                channel_id='default',
                priority='high',
            ),
        ),
        # iOS-specific: badge, sound
        apns=messaging.APNSConfig(
            payload=messaging.APNSPayload(
                aps=messaging.Aps(
                    badge=1,
                    sound='default',
                    content_available=True,
                ),
            ),
        ),
    )

    try:
        response = messaging.send_each_for_multicast(message)
        success_count = response.success_count

        # Deactivate tokens that are no longer valid
        if response.failure_count > 0:
            _handle_failed_tokens(tokens, response.responses)

        logger.info(
            "Push sent to %s: %d/%d delivered",
            user.email, success_count, len(tokens),
        )
        return success_count
    except Exception:
        logger.exception("Failed to send FCM push to user %s", user.email)
        return 0


def send_push_bulk(user_ids, title, body, data=None, notification_type=None):
    """Send a push notification to multiple users.

    Args:
        user_ids: List/queryset of user PKs
        title: Notification title
        body: Notification body text
        data: Optional dict of extra data
        notification_type: Optional type string

    Returns:
        Total number of successfully delivered pushes.
    """
    if not _is_enabled():
        return 0

    from firebase_admin import messaging
    from index.models import PushDevice

    devices = PushDevice.objects.filter(
        user_id__in=user_ids, is_active=True,
    )
    tokens = list(devices.values_list('fcm_token', flat=True))

    if not tokens:
        return 0

    payload = data or {}
    if notification_type:
        payload['notification_type'] = notification_type
    payload = {k: str(v) for k, v in payload.items()}

    # FCM allows max 500 tokens per multicast
    total_success = 0
    batch_size = 500

    for i in range(0, len(tokens), batch_size):
        batch_tokens = tokens[i:i + batch_size]

        message = messaging.MulticastMessage(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data=payload,
            tokens=batch_tokens,
            android=messaging.AndroidConfig(
                priority='high',
                notification=messaging.AndroidNotification(
                    channel_id='default',
                    priority='high',
                ),
            ),
            apns=messaging.APNSConfig(
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(
                        badge=1,
                        sound='default',
                        content_available=True,
                    ),
                ),
            ),
        )

        try:
            response = messaging.send_each_for_multicast(message)
            total_success += response.success_count

            if response.failure_count > 0:
                _handle_failed_tokens(batch_tokens, response.responses)
        except Exception:
            logger.exception("Failed to send FCM batch (tokens %d-%d)", i, i + len(batch_tokens))

    logger.info("Bulk push: %d/%d delivered to %d users", total_success, len(tokens), len(user_ids))
    return total_success


def _handle_failed_tokens(tokens, responses):
    """Deactivate FCM tokens that are permanently invalid.

    Firebase returns specific error codes for tokens that should be removed:
    - UNREGISTERED: App was uninstalled or token was invalidated
    - INVALID_ARGUMENT: Token format is wrong
    """
    from firebase_admin import messaging
    from index.models import PushDevice

    stale_tokens = []
    for token, resp in zip(tokens, responses):
        if resp.exception:
            error_code = getattr(resp.exception, 'code', '')
            if error_code in ('UNREGISTERED', 'INVALID_ARGUMENT', 'NOT_FOUND'):
                stale_tokens.append(token)

    if stale_tokens:
        count = PushDevice.objects.filter(fcm_token__in=stale_tokens).update(is_active=False)
        logger.info("Deactivated %d stale FCM tokens", count)
