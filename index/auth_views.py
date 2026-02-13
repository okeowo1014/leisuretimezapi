"""
Authentication views for user registration, login, logout, and password management.
"""

import logging
from decimal import Decimal

from django.contrib.auth import authenticate
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from rest_framework.response import Response

from .models import AccountDeletionLog, CustomerProfile, CustomUser, Wallet
from .serializers import (
    AuthTokenSerializer, ChangePasswordSerializer, CustomUserSerializer,
    ResetConfirmationSerializer, ResetPasswordConfirmSerializer,
    ResetPasswordSerializer,
)
from index.wallet_utils import create_stripe_customer

logger = logging.getLogger(__name__)


class AuthViewSet(viewsets.GenericViewSet):
    """Handles user registration, login, and logout."""

    permission_classes = [AllowAny]
    serializer_class = AuthTokenSerializer

    def get_serializer_class(self):
        if self.action == 'register':
            return CustomUserSerializer
        elif self.action == 'login':
            return AuthTokenSerializer
        return self.serializer_class

    @action(detail=False, methods=['post'])
    def register(self, request):
        """Register a new user account with email verification."""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            user.is_active = False
            user.activation_sent_at = timezone.now()
            user.save()

            token, _ = Token.objects.get_or_create(user=user)
            CustomerProfile.objects.create(user=user)

            current_site = get_current_site(request)
            verification_token = default_token_generator.make_token(user)
            message = render_to_string('myadmin/verifymail.html', {
                'user': user,
                'domain': current_site.domain,
                'utoken': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': verification_token,
            })

            email = EmailMessage(
                'Activate your account', message, to=[user.email]
            )
            email.content_subtype = 'html'
            email.send()

            return Response(
                {'user': serializer.data, 'token': token.key},
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def login(self, request):
        """Authenticate and return a token with user profile data."""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            user = authenticate(email=email, password=password)

            if not user:
                return Response(
                    {'error': 'Invalid credentials'},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            profile, _ = CustomerProfile.objects.get_or_create(user=user)
            wallet, created = Wallet.objects.get_or_create(user=user)

            if created:
                try:
                    stripe_customer_id = create_stripe_customer(user)
                    wallet.stripe_customer_id = stripe_customer_id
                    wallet.save()
                except Exception:
                    logger.exception(
                        "Failed to create Stripe customer for user %s", user.email
                    )

            token, _ = Token.objects.get_or_create(user=user)

            return Response({
                'token': token.key,
                'id': user.pk,
                'email': user.email,
                'firstname': user.firstname,
                'lastname': user.lastname,
                'wallet': str(wallet.balance),
                'image': profile.image.url if profile.image else None,
            })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def logout(self, request):
        """Delete the user's authentication token."""
        try:
            request.user.auth_token.delete()
            return Response(
                {'message': 'Successfully logged out.'},
                status=status.HTTP_200_OK,
            )
        except Exception:
            logger.exception("Error during logout for user %s", request.user.email)
            return Response(status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(generics.UpdateAPIView):
    """Change the authenticated user's password."""

    permission_classes = [IsAuthenticated]
    serializer_class = ChangePasswordSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            if user.check_password(serializer.data.get('old_password')):
                user.set_password(serializer.data.get('new_password'))
                user.save()
                user.auth_token.delete()
                token, _ = Token.objects.get_or_create(user=user)
                return Response(
                    {'message': 'Password updated successfully', 'token': token.key},
                    status=status.HTTP_200_OK,
                )
            return Response(
                {'error': 'Incorrect old password'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResetPasswordView(generics.GenericAPIView):
    """Send a password reset email to the user."""

    serializer_class = ResetPasswordSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            email_address = serializer.validated_data['email']
            user = get_object_or_404(CustomUser, email=email_address)
            current_site = get_current_site(request)
            email_body = render_to_string('myadmin/password_reset_email.html', {
                'user': user,
                'domain': current_site.domain,
                'utoken': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            email_message = EmailMessage(
                'Reset Your Password', email_body, to=[email_address]
            )
            email_message.content_subtype = 'html'
            email_message.send()
            return Response(
                {'message': 'Password reset email sent'},
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResendConfirmationView(generics.GenericAPIView):
    """Resend the account activation email."""

    serializer_class = ResetConfirmationSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            email_address = serializer.validated_data['email']
            user = get_object_or_404(CustomUser, email=email_address)
            if user.is_active:
                return Response(
                    {'message': 'Your account is already active. Please log in.'},
                    status=status.HTTP_200_OK,
                )

            current_site = get_current_site(request)
            message = render_to_string('myadmin/verifymail.html', {
                'user': user,
                'domain': current_site.domain,
                'utoken': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            email_message = EmailMessage(
                'Activate your account', message, to=[email_address]
            )
            email_message.content_subtype = 'html'
            email_message.send()

            user.activation_sent_at = timezone.now()
            user.save()
            return Response(
                {'message': 'Activation email sent. Please check your inbox.'},
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteAccountView(generics.DestroyAPIView):
    """Soft-delete the authenticated user's account.

    Deactivates the account and anonymizes personal data while preserving
    booking, invoice, and transaction records for business/legal compliance.
    """

    permission_classes = [IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        user = request.user
        password = request.data.get('password')

        if not password or not user.check_password(password):
            return Response(
                {'status': 'error', 'message': 'Password confirmation required'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Preserve original identity in audit log before anonymizing
        wallet_balance = Decimal('0.00')
        try:
            wallet = Wallet.objects.get(user=user)
            wallet_balance = wallet.balance
        except Wallet.DoesNotExist:
            wallet = None

        phone = ''
        try:
            profile = CustomerProfile.objects.get(user=user)
            phone = profile.phone or ''
        except CustomerProfile.DoesNotExist:
            profile = None

        AccountDeletionLog.objects.create(
            user_id=user.pk,
            email=user.email,
            firstname=user.firstname,
            lastname=user.lastname,
            phone=phone,
            date_joined=user.date_joined,
            wallet_balance_at_deletion=wallet_balance,
        )

        original_email = user.email

        # Revoke auth token
        try:
            user.auth_token.delete()
        except Exception:
            pass

        # Deactivate and anonymize the user record
        user.is_active = False
        user.email = f'deleted_{user.pk}@deactivated.local'
        user.firstname = 'Deleted'
        user.lastname = 'User'
        user.set_unusable_password()
        user.save()

        # Anonymize the customer profile
        if profile:
            profile.phone = ''
            profile.address = ''
            profile.date_of_birth = None
            profile.image = 'default.svg'
            profile.status = 'deleted'
            profile.save()

        # Deactivate wallet (keep records for audit)
        if wallet:
            wallet.is_active = False
            wallet.save()

        logger.info("Account soft-deleted for user %s (pk=%s)", original_email, user.pk)

        return Response(
            {'status': 'success', 'message': 'Your account has been deleted and personal data anonymized'},
            status=status.HTTP_200_OK,
        )


class ResetPasswordConfirmView(generics.GenericAPIView):
    """Confirm a password reset using the token from the email."""

    serializer_class = ResetPasswordConfirmSerializer
    permission_classes = [AllowAny]

    def post(self, request, utoken=None, token=None):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            try:
                uid = urlsafe_base64_decode(utoken).decode()
                user = CustomUser.objects.get(pk=uid)
            except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
                return Response(
                    {'error': 'Invalid reset link'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if not default_token_generator.check_token(user, token):
                return Response(
                    {'error': 'Invalid or expired reset token'},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response(
                {'message': 'Password has been reset successfully'},
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
