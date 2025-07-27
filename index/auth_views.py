
from django.contrib.auth import authenticate
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.core.mail import EmailMessage
from django.contrib.auth.tokens import default_token_generator
from rest_framework import viewsets, status, generics
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from .serializers import (
    CustomUserSerializer, ChangePasswordSerializer, ResetConfirmationSerializer,
    ResetPasswordSerializer, ResetPasswordConfirmSerializer, AuthTokenSerializer
)
from django.contrib.auth.tokens import default_token_generator
from django.utils import timezone
from .models import CustomerProfile,CustomUser,Wallet
from django.shortcuts import get_object_or_404
from django.utils.encoding import force_bytes
from index.wallet_utils import create_stripe_customer
# class AuthViewSet(viewsets.GenericViewSet):
#     permission_classes = [AllowAny]
#     serializer_class = AuthTokenSerializer  # Default serializer class

#     def get_serializer_class(self):
#         if self.action == 'register':
#             return CustomUserSerializer
#         elif self.action == 'login':
#             return AuthTokenSerializer
#         elif self.action == 'logout':
#             return None  # Logout doesn't require a serializer
#         return self.serializer_class

#     @action(detail=False, methods=['post'])
#     def register(self, request):
        # serializer = self.get_serializer(data=request.data)
        # if serializer.is_valid():
        #     user = serializer.save()
        #     token, created = Token.objects.get_or_create(user=user)
        #     current_site = get_current_site(request)
        #     mail_subject = 'Activate your account'
        #     message = render_to_string('myadmin/verifymail.html', {
        #     'user': user,
        #     'domain': current_site.domain,
        #     'utoken': encode_user_pk(user.pk),
        #     'token': default_token_generator.make_token(user),
        #     })
        #     email = EmailMessage(mail_subject, message, to=[user.email])
        #     email.content_subtype = "html"
        #     email.send()
        #     return Response({
        #         'user': serializer.data,
        #         'token': token.key
        #     }, status=status.HTTP_201_CREATED)
        # return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AuthViewSet(viewsets.GenericViewSet):
    permission_classes = [AllowAny]
    serializer_class = AuthTokenSerializer  # Default serializer class

    def get_serializer_class(self):
        if self.action == 'register':
            return CustomUserSerializer
        elif self.action == 'login':
            return AuthTokenSerializer
        elif self.action == 'logout':
            return None  # Logout doesn't require a serializer
        return self.serializer_class

    @action(detail=False, methods=['post'])
    def register(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            user.is_active = False  # Ensure the user is inactive until verification
            user.activation_sent_at = timezone.now()  # Save activation timestamp
            user.save()
            token, created = Token.objects.get_or_create(user=user)
            CustomerProfile.objects.create(user=user)
            current_site = get_current_site(request)
            mail_subject = 'Activate your account'
            verification_token = default_token_generator.make_token(user)

            message = render_to_string('myadmin/verifymail.html', {
                'user': user,
                'domain': current_site.domain,
                'utoken': urlsafe_base64_encode(str(user.pk).encode()),  # Correct encoding
                'token': verification_token,  # Use this token for activation
            })

            email = EmailMessage(mail_subject, message, to=[user.email])
            email.content_subtype = "html"
            email.send()

            return Response({
                'user': serializer.data,
                'token': token.key
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def login(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']
            user = authenticate(email=email, password=password)
            print(user,'is user')
            profile,profile_created=CustomerProfile.objects.get_or_create(user=user)
            wallet,created=Wallet.objects.get_or_create(user=user)
            if created:
                stripe_customer_id = create_stripe_customer(self.request.user)
                wallet.stripe_customer_id = stripe_customer_id
                wallet.save()
                print('wallet created')
            if user:
                token, created = Token.objects.get_or_create(user=user)
                return Response({
                    'token': token.key,
                    'id': user.pk,
                    'email': user.email,
                    'firstname': user.firstname,
                    'lastname': user.lastname,
                    'wallet':str(wallet.balance),
                    'image':profile.image.url,
                    
                })
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def logout(self, request):
        try:
            # Delete the user's token to logout
            request.user.auth_token.delete()
            return Response({'message': 'Successfully logged out.'}, 
                          status=status.HTTP_200_OK)
        except Exception:
            return Response(status=status.HTTP_400_BAD_REQUEST)

class ChangePasswordView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ChangePasswordSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            if user.check_password(serializer.data.get('old_password')):
                user.set_password(serializer.data.get('new_password'))
                user.save()
                # Update token after password change
                user.auth_token.delete()
                token, created = Token.objects.get_or_create(user=user)
                return Response({
                    'message': 'Password updated successfully',
                    'token': token.key
                }, status=status.HTTP_200_OK)
            return Response(
                {'error': 'Incorrect old password'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ResetPasswordView(generics.GenericAPIView):
    serializer_class = ResetPasswordSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            user = get_object_or_404(CustomUser,email=email)
            current_site = get_current_site(request)
            email_subject = 'Reset Your Password'
            email_body = render_to_string('myadmin/password_reset_email.html', {
                 'user': user,
                'domain': current_site.domain,
                'utoken': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            # Send the email
            email = EmailMessage(
                email_subject,
                email_body,
                to=[email],
            )
            email.content_subtype = "html"  # Set the content type to HTML
            email.send()
            # Add your password reset email logic here
            return Response(
                {'message': 'Password reset email sent'},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ResendConfirmationView(generics.GenericAPIView):
    serializer_class = ResetConfirmationSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            user = get_object_or_404(CustomUser,email=email)
            if user.is_active:
                return Response(
                {'message': 'Your account is already active. Please log in'}, status=status.HTTP_200_OK )
            
            current_site = get_current_site(request)
            mail_subject = 'Activate your account'
            message = render_to_string('myadmin/verifymail.html', {
                'user': user,
                'domain': current_site.domain,
                'utoken': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            email = EmailMessage(
                mail_subject, message, to=[email]
            )
            email.content_subtype = "html"  # Set the content type to HTML
            email.send()
            # Update activation sent timestamp
            user.activation_sent_at = timezone.now()
            user.save()
            # Add your password reset email logic here
            return Response(
                {'message': 'Password reset email sent'},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ResetPasswordConfirmView(generics.GenericAPIView):
    serializer_class = ResetPasswordConfirmSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # Add your password reset confirmation logic here
            return Response(
                {'message': 'Password has been reset successfully'},
                status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)