"""
Social authentication (Google, Meta/Facebook, Apple) and biometric login.

Flow:
  1. Mobile app obtains an ID token / access token from Google/Facebook/Apple SDK.
  2. App sends it to our API (`POST /auth/social/google/`, `/auth/social/facebook/`,
     or `/auth/social/apple/`).
  3. We verify the token server-side, create or fetch the user, and return
     our own auth token + profile data.

Biometric flow:
  1. After normal login, app calls `POST /auth/biometric/register/` with a
     device_id. We return a long-lived biometric_token tied to that device.
  2. On subsequent launches, app unlocks biometrics and sends the
     biometric_token to `POST /auth/biometric/login/`. We validate and
     return a fresh auth token.
"""

import hashlib
import logging
import secrets

import jwt
import requests as http_requests
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token

from django.conf import settings
from django.db import IntegrityError
from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import BiometricDevice, CustomerProfile, CustomUser, Wallet
from .security import (
    check_new_device, create_or_update_session,
    get_client_ip, get_device_fingerprint, get_user_agent,
    log_user_activity,
)
from index.wallet_utils import create_stripe_customer

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Serializers
# ---------------------------------------------------------------------------

class SocialAuthSerializer(serializers.Serializer):
    access_token = serializers.CharField(
        help_text='ID token (Google) or access token (Facebook) from the mobile SDK',
    )


class AppleAuthSerializer(serializers.Serializer):
    id_token = serializers.CharField(
        help_text='The identity token (JWT) from Sign in with Apple',
    )
    first_name = serializers.CharField(
        required=False, default='',
        help_text='First name (only sent by Apple on initial sign-up)',
    )
    last_name = serializers.CharField(
        required=False, default='',
        help_text='Last name (only sent by Apple on initial sign-up)',
    )


class BiometricRegisterSerializer(serializers.Serializer):
    device_id = serializers.CharField(
        max_length=255,
        help_text='Unique device identifier from the mobile app',
    )
    device_name = serializers.CharField(
        max_length=255, required=False, default='',
        help_text='Human-readable device name (e.g. "iPhone 15 Pro")',
    )


class BiometricLoginSerializer(serializers.Serializer):
    biometric_token = serializers.CharField(
        help_text='The biometric token returned during registration',
    )
    device_id = serializers.CharField(
        max_length=255,
        help_text='The same device_id used during registration',
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_or_create_social_user(email, firstname, lastname, provider, provider_uid):
    """Find existing user by email or create a new one for social login.

    Returns (user, created).
    """
    try:
        user = CustomUser.objects.get(email=email)
        created = False
    except CustomUser.DoesNotExist:
        user = CustomUser.objects.create_user(
            email=email,
            firstname=firstname,
            lastname=lastname,
        )
        # Social users are auto-activated (email is verified by the provider)
        user.is_active = True
        user.set_unusable_password()
        user.save()

        # Create profile and wallet
        CustomerProfile.objects.get_or_create(user=user)
        wallet, wallet_created = Wallet.objects.get_or_create(user=user)
        if wallet_created:
            try:
                wallet.stripe_customer_id = create_stripe_customer(user)
                wallet.save()
            except Exception:
                logger.exception("Failed to create Stripe customer for social user %s", email)

        created = True

    return user, created


def _build_login_response(user, request, provider='email'):
    """Build the standard login response with security tracking."""
    if not user.is_active:
        return Response(
            {'error': 'This account has been deactivated.'},
            status=status.HTTP_403_FORBIDDEN,
        )

    profile, _ = CustomerProfile.objects.get_or_create(user=user)
    wallet, wallet_created = Wallet.objects.get_or_create(user=user)

    if wallet_created:
        try:
            wallet.stripe_customer_id = create_stripe_customer(user)
            wallet.save()
        except Exception:
            logger.exception("Failed to create Stripe customer for user %s", user.email)

    token, _ = Token.objects.get_or_create(user=user)

    # --- Security tracking ---
    ip = get_client_ip(request)
    ua = get_user_agent(request)
    fingerprint = get_device_fingerprint(ip, ua)

    is_new_device = check_new_device(user, fingerprint)
    session, _, concurrent_count = create_or_update_session(user, token.key, request)

    risk_level = 'low'
    login_details = {'provider': provider, 'device': session.device_name}

    if is_new_device:
        risk_level = 'medium'
        login_details['new_device'] = True
        log_user_activity(user, 'new_device', request, risk_level='medium',
                          details={'device': session.device_name, 'provider': provider})

    if concurrent_count > 0:
        risk_level = 'high' if concurrent_count >= 2 else 'medium'
        login_details['concurrent_sessions'] = concurrent_count + 1
        log_user_activity(user, 'concurrent_session', request, risk_level=risk_level,
                          details={'total_active_sessions': concurrent_count + 1,
                                   'device': session.device_name, 'provider': provider})

    log_user_activity(user, 'login_success', request, risk_level=risk_level,
                      details=login_details)

    response_data = {
        'token': token.key,
        'id': user.pk,
        'email': user.email,
        'firstname': user.firstname,
        'lastname': user.lastname,
        'wallet': str(wallet.balance),
        'image': profile.image.url if profile.image else None,
        'provider': provider,
    }

    if is_new_device or concurrent_count > 0:
        response_data['security_notices'] = []
        if is_new_device:
            response_data['security_notices'].append('Login from a new device detected.')
        if concurrent_count > 0:
            response_data['security_notices'].append(
                f'You have {concurrent_count + 1} active sessions.'
            )

    return Response(response_data)


# ---------------------------------------------------------------------------
# Google Login
# ---------------------------------------------------------------------------

class GoogleLoginView(APIView):
    """Verify a Google ID token and log in or register the user.

    Expects: POST { "access_token": "<google_id_token>" }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SocialAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = serializer.validated_data['access_token']

        google_client_id = settings.GOOGLE_CLIENT_ID
        if not google_client_id:
            return Response(
                {'error': 'Google login is not configured.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        try:
            idinfo = google_id_token.verify_oauth2_token(
                token,
                google_requests.Request(),
                google_client_id,
            )
        except ValueError:
            log_user_activity(None, 'login_failed', request, risk_level='medium',
                              details={'provider': 'google', 'reason': 'invalid_token'})
            return Response(
                {'error': 'Invalid Google token.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        email = idinfo.get('email')
        if not email or not idinfo.get('email_verified'):
            return Response(
                {'error': 'Google account email not verified.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user, created = _get_or_create_social_user(
            email=email,
            firstname=idinfo.get('given_name', ''),
            lastname=idinfo.get('family_name', ''),
            provider='google',
            provider_uid=idinfo.get('sub', ''),
        )

        if created:
            logger.info("New user registered via Google: %s", email)

        return _build_login_response(user, request, provider='google')


# ---------------------------------------------------------------------------
# Facebook / Meta Login
# ---------------------------------------------------------------------------

class FacebookLoginView(APIView):
    """Verify a Facebook access token and log in or register the user.

    Expects: POST { "access_token": "<facebook_access_token>" }
    """
    permission_classes = [AllowAny]

    GRAPH_ME_URL = 'https://graph.facebook.com/v19.0/me'
    GRAPH_DEBUG_URL = 'https://graph.facebook.com/debug_token'

    def post(self, request):
        serializer = SocialAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        access_token = serializer.validated_data['access_token']

        app_id = settings.FACEBOOK_APP_ID
        app_secret = settings.FACEBOOK_APP_SECRET
        if not app_id or not app_secret:
            return Response(
                {'error': 'Facebook login is not configured.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        # Step 1: Verify the token is valid and issued for our app
        try:
            debug_resp = http_requests.get(
                self.GRAPH_DEBUG_URL,
                params={
                    'input_token': access_token,
                    'access_token': f'{app_id}|{app_secret}',
                },
                timeout=10,
            )
            debug_data = debug_resp.json().get('data', {})

            if not debug_data.get('is_valid'):
                log_user_activity(None, 'login_failed', request, risk_level='medium',
                                  details={'provider': 'facebook', 'reason': 'invalid_token'})
                return Response(
                    {'error': 'Invalid Facebook token.'},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            if str(debug_data.get('app_id')) != str(app_id):
                log_user_activity(None, 'login_failed', request, risk_level='high',
                                  details={'provider': 'facebook', 'reason': 'app_id_mismatch'})
                return Response(
                    {'error': 'Token was not issued for this application.'},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
        except http_requests.RequestException:
            logger.exception("Failed to verify Facebook token")
            return Response(
                {'error': 'Could not verify Facebook token.'},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        # Step 2: Fetch user profile
        try:
            me_resp = http_requests.get(
                self.GRAPH_ME_URL,
                params={
                    'fields': 'id,email,first_name,last_name',
                    'access_token': access_token,
                },
                timeout=10,
            )
            me_data = me_resp.json()
        except http_requests.RequestException:
            logger.exception("Failed to fetch Facebook profile")
            return Response(
                {'error': 'Could not fetch Facebook profile.'},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        email = me_data.get('email')
        if not email:
            return Response(
                {'error': 'Email permission is required. Please grant email access in Facebook.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user, created = _get_or_create_social_user(
            email=email,
            firstname=me_data.get('first_name', ''),
            lastname=me_data.get('last_name', ''),
            provider='facebook',
            provider_uid=me_data.get('id', ''),
        )

        if created:
            logger.info("New user registered via Facebook: %s", email)

        return _build_login_response(user, request, provider='facebook')


# ---------------------------------------------------------------------------
# Apple Sign In
# ---------------------------------------------------------------------------

# Apple's public keys endpoint — used to verify the signature on Apple ID tokens
APPLE_KEYS_URL = 'https://appleid.apple.com/auth/keys'
APPLE_ISSUER = 'https://appleid.apple.com'

_apple_public_keys_cache = {}  # kid → RSAPublicKey


def _refresh_apple_keys():
    """Fetch Apple's current public keys and cache them by kid."""
    global _apple_public_keys_cache
    try:
        resp = http_requests.get(APPLE_KEYS_URL, timeout=10)
        resp.raise_for_status()
        jwks = resp.json()
        new_cache = {}
        for key_data in jwks.get('keys', []):
            kid = key_data.get('kid')
            if kid:
                public_key = jwt.algorithms.RSAAlgorithm.from_jwk(key_data)
                new_cache[kid] = public_key
        _apple_public_keys_cache = new_cache
        logger.info("Refreshed %d Apple public keys", len(new_cache))
    except Exception:
        logger.exception("Failed to fetch Apple public keys")


def _get_apple_public_key(kid):
    """Return the Apple public key for the given kid, refreshing if needed."""
    if kid not in _apple_public_keys_cache:
        _refresh_apple_keys()
    return _apple_public_keys_cache.get(kid)


class AppleLoginView(APIView):
    """Verify an Apple identity token and log in or register the user.

    Expects: POST {
        "id_token": "<apple_jwt>",
        "first_name": "John",    // optional, only on first sign-up
        "last_name": "Doe"       // optional, only on first sign-up
    }

    Apple only sends the user's name on the VERY FIRST authorization.
    The mobile app must capture it from the ASAuthorization credential
    and send it here. On subsequent logins the name fields can be omitted.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = AppleAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        id_token = serializer.validated_data['id_token']
        first_name = serializer.validated_data.get('first_name', '')
        last_name = serializer.validated_data.get('last_name', '')

        apple_client_id = getattr(settings, 'APPLE_CLIENT_ID', '')
        if not apple_client_id:
            return Response(
                {'error': 'Apple login is not configured.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        # Decode the JWT header to find the key ID (kid)
        try:
            unverified_header = jwt.get_unverified_header(id_token)
        except jwt.DecodeError:
            log_user_activity(None, 'login_failed', request, risk_level='medium',
                              details={'provider': 'apple', 'reason': 'malformed_token'})
            return Response(
                {'error': 'Invalid Apple token.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        kid = unverified_header.get('kid')
        public_key = _get_apple_public_key(kid)
        if not public_key:
            log_user_activity(None, 'login_failed', request, risk_level='medium',
                              details={'provider': 'apple', 'reason': 'unknown_kid', 'kid': kid})
            return Response(
                {'error': 'Unable to verify Apple token signature.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Verify the token: signature, expiry, issuer, and audience
        try:
            payload = jwt.decode(
                id_token,
                key=public_key,
                algorithms=['RS256'],
                audience=apple_client_id,
                issuer=APPLE_ISSUER,
            )
        except jwt.ExpiredSignatureError:
            log_user_activity(None, 'login_failed', request, risk_level='medium',
                              details={'provider': 'apple', 'reason': 'expired_token'})
            return Response(
                {'error': 'Apple token has expired.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        except jwt.InvalidTokenError as exc:
            log_user_activity(None, 'login_failed', request, risk_level='medium',
                              details={'provider': 'apple', 'reason': str(exc)})
            return Response(
                {'error': 'Invalid Apple token.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        email = payload.get('email')
        if not email:
            return Response(
                {'error': 'Email not provided in Apple token. Ensure email scope is requested.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Apple's email_verified can be a string "true" or boolean
        email_verified = payload.get('email_verified')
        if str(email_verified).lower() not in ('true', '1'):
            return Response(
                {'error': 'Apple account email not verified.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        apple_uid = payload.get('sub', '')

        user, created = _get_or_create_social_user(
            email=email,
            firstname=first_name,
            lastname=last_name,
            provider='apple',
            provider_uid=apple_uid,
        )

        if created:
            logger.info("New user registered via Apple: %s", email)

        return _build_login_response(user, request, provider='apple')


# ---------------------------------------------------------------------------
# Biometric Auth
# ---------------------------------------------------------------------------

class BiometricRegisterView(APIView):
    """Register a device for biometric login.

    Requires an authenticated session. Returns a biometric_token that the
    mobile app should store securely in the device keychain.

    Expects: POST { "device_id": "...", "device_name": "iPhone 15 Pro" }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = BiometricRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        device_id = serializer.validated_data['device_id']
        device_name = serializer.validated_data.get('device_name', '')
        user = request.user

        max_devices = getattr(settings, 'BIOMETRIC_MAX_DEVICES', 5)

        # Check device limit
        active_count = BiometricDevice.objects.filter(user=user, is_active=True).count()
        existing = BiometricDevice.objects.filter(user=user, device_id=device_id).first()

        if not existing and active_count >= max_devices:
            return Response(
                {'error': f'Maximum of {max_devices} biometric devices reached. '
                          'Please remove an existing device first.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Generate a secure biometric token
        raw_token = secrets.token_urlsafe(48)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

        ip = get_client_ip(request)
        ua = get_user_agent(request)

        if existing:
            # Re-register existing device
            existing.token_hash = token_hash
            existing.device_name = device_name or existing.device_name
            existing.ip_address = ip
            existing.user_agent = ua
            existing.is_active = True
            existing.last_used = timezone.now()
            existing.save()
        else:
            BiometricDevice.objects.create(
                user=user,
                device_id=device_id,
                device_name=device_name,
                token_hash=token_hash,
                ip_address=ip,
                user_agent=ua,
            )

        log_user_activity(
            user, 'login_success', request,
            details={'action': 'biometric_registered', 'device_id': device_id,
                     'device_name': device_name},
        )

        return Response({
            'biometric_token': raw_token,
            'device_id': device_id,
            'message': 'Biometric login registered successfully.',
        }, status=status.HTTP_201_CREATED)


class BiometricLoginView(APIView):
    """Authenticate using a biometric token.

    The mobile app unlocks via Face ID / fingerprint, retrieves the stored
    biometric_token from the secure keychain, and sends it here.

    Expects: POST { "biometric_token": "...", "device_id": "..." }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = BiometricLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        raw_token = serializer.validated_data['biometric_token']
        device_id = serializer.validated_data['device_id']
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

        try:
            device = BiometricDevice.objects.select_related('user').get(
                device_id=device_id,
                token_hash=token_hash,
                is_active=True,
            )
        except BiometricDevice.DoesNotExist:
            log_user_activity(
                None, 'login_failed', request,
                risk_level='medium',
                details={'provider': 'biometric', 'device_id': device_id,
                         'reason': 'invalid_token'},
            )
            return Response(
                {'error': 'Invalid biometric credentials.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        user = device.user
        if not user.is_active:
            return Response(
                {'error': 'This account has been deactivated.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Update last used
        device.last_used = timezone.now()
        device.ip_address = get_client_ip(request)
        device.user_agent = get_user_agent(request)
        device.save(update_fields=['last_used', 'ip_address', 'user_agent'])

        return _build_login_response(user, request, provider='biometric')


class BiometricDeviceListView(APIView):
    """List all registered biometric devices for the authenticated user."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        devices = BiometricDevice.objects.filter(
            user=request.user, is_active=True,
        ).order_by('-last_used')

        data = [
            {
                'id': d.id,
                'device_id': d.device_id,
                'device_name': d.device_name,
                'last_used': d.last_used.isoformat() if d.last_used else None,
                'created_at': d.created_at.isoformat(),
            }
            for d in devices
        ]
        return Response(data)


class BiometricDeviceRevokeView(APIView):
    """Revoke a specific biometric device."""
    permission_classes = [IsAuthenticated]

    def post(self, request, device_id):
        try:
            device = BiometricDevice.objects.get(
                user=request.user,
                device_id=device_id,
                is_active=True,
            )
        except BiometricDevice.DoesNotExist:
            return Response(
                {'error': 'Device not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        device.is_active = False
        device.save(update_fields=['is_active'])

        log_user_activity(
            request.user, 'logout', request,
            details={'action': 'biometric_revoked', 'device_id': device_id,
                     'device_name': device.device_name},
        )

        return Response({'message': 'Biometric device revoked.'})
