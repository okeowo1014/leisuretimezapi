from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.core.mail import EmailMessage
from django.conf import settings
from django.http import JsonResponse
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth import update_session_auth_hash
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import CustomUser, CustomerProfile
from .serializers import (
    CustomerRegistrationSerializer, LoginSerializer, ActivateAccountSerializer,
    PasswordResetRequestSerializer, PasswordResetConfirmSerializer,
    UpdatePasswordSerializer, UpdateProfileSerializer, UpdateEmailSerializer,
    ProfilePictureSerializer
)

### CUSTOMER REGISTRATION ###
@api_view(['POST'])
def customer_registration(request):
    serializer = CustomerRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()

        # Send email verification
        current_site = get_current_site(request)
        mail_subject = 'Activate your account'
        message = f"""
        Hello {user.first_name}, 
        Click the link below to verify your email:
        http://{current_site.domain}/api/activate/{urlsafe_base64_encode(force_bytes(user.pk))}/{default_token_generator.make_token(user)}/
        """
        email = EmailMessage(mail_subject, message, to=[user.email])
        email.send()

        return Response({'message': 'Signup successful. Check your email for confirmation.'}, status=201)
    
    return Response(serializer.errors, status=400)


### EMAIL VERIFICATION ###
@api_view(['GET'])
def activate_account(request, uidb64, token):
    serializer = ActivateAccountSerializer(data={'uidb64': uidb64, 'token': token})
    if serializer.is_valid():
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = CustomUser.objects.get(pk=uid)
            if default_token_generator.check_token(user, token):
                user.is_active = True
                user.save()
                return Response({'message': 'Account activated successfully.'})
            return Response({'error': 'Invalid activation link'}, status=400)
        except:
            return Response({'error': 'Activation failed'}, status=400)
    return Response(serializer.errors, status=400)


### LOGIN ###
@api_view(['POST'])
def customer_login(request):
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']
        user = authenticate(email=email, password=password)
        
        if user:
            if not user.is_active:
                return Response({'error': 'Verify your email first'}, status=403)
            login(request, user)
            token, created = Token.objects.get_or_create(user=user)
            return Response({'message': 'Login successful', 'token': token.key})

        return Response({'error': 'Invalid email or password'}, status=400)

    return Response(serializer.errors, status=400)


### LOGOUT ###
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_customer(request):
    request.user.auth_token.delete()
    logout(request)
    return Response({'message': 'Logout successful'})


### PASSWORD RESET (Request Email) ###
@api_view(['POST'])
def password_reset_request(request):
    serializer = PasswordResetRequestSerializer(data=request.data)
    if serializer.is_valid():
        email = serializer.validated_data['email']
        user = CustomUser.objects.filter(email=email).first()
        if user:
            mail_subject = 'Reset Your Password'
            message = f"""
            Hello {user.first_name}, 
            Click the link below to reset your password:
            http://{get_current_site(request).domain}/api/password-reset/{urlsafe_base64_encode(force_bytes(user.pk))}/{default_token_generator.make_token(user)}/
            """
            email = EmailMessage(mail_subject, message, to=[email])
            email.send()
            return Response({'message': 'Password reset link sent to your email'}, status=200)
        
        return Response({'error': 'User not found'}, status=404)

    return Response(serializer.errors, status=400)


### PASSWORD RESET (Submit New Password) ###
@api_view(['POST'])
def password_reset_confirm(request, uidb64, token):
    serializer = PasswordResetConfirmSerializer(data=request.data)
    if serializer.is_valid():
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = CustomUser.objects.get(pk=uid)
            if default_token_generator.check_token(user, token):
                user.set_password(serializer.validated_data['password'])
                user.save()
                return Response({'message': 'Password reset successful'})
            return Response({'error': 'Invalid reset link'}, status=400)
        except:
            return Response({'error': 'Reset failed'}, status=400)
    return Response(serializer.errors, status=400)


### UPDATE PASSWORD ###
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_password(request):
    serializer = UpdatePasswordSerializer(data=request.data)
    if serializer.is_valid():
        if not request.user.check_password(serializer.validated_data['old_password']):
            return Response({'error': 'Incorrect old password'}, status=400)

        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        update_session_auth_hash(request, request.user)
        return Response({'message': 'Password updated successfully'})

    return Response(serializer.errors, status=400)




# from django.shortcuts import get_object_or_404
# from django.contrib.auth import authenticate, login, logout
# from django.contrib.auth.tokens import default_token_generator
# from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
# from django.utils.encoding import force_bytes
# from django.core.mail import EmailMessage
# from django.conf import settings
# from django.http import JsonResponse
# from django.views.decorators.csrf import csrf_exempt
# from django.contrib.sites.shortcuts import get_current_site
# from django.contrib.auth.decorators import login_required
# from django.contrib.auth.forms import PasswordResetForm
# from django.contrib.auth import update_session_auth_hash
# from rest_framework.authtoken.models import Token
# from rest_framework.decorators import api_view, permission_classes
# from rest_framework.permissions import IsAuthenticated
# from .models import CustomUser, CustomerProfile
# from .forms import (
#     UpdateNameForm, UpdateEmailForm, UpdatePasswordForm,
#     UpdatePhoneForm, UpdateAddressForm, UpdateDobForm, CustomerRegistrationForm
# )
# import json

# ### CUSTOMER REGISTRATION ###
# @csrf_exempt
# @api_view(['POST'])
# def customer_registration(request):
#     form = CustomerRegistrationForm(request.data)
#     if form.is_valid():
#         user = form.save()

#         # Create customer profile
#         CustomerProfile.objects.create(user=user)

#         # Send email verification
#         current_site = get_current_site(request)
#         mail_subject = 'Activate your account'
#         message = f"""
#         Hello {user.first_name}, 
#         Click the link below to verify your email:
#         http://{current_site.domain}/api/activate/{urlsafe_base64_encode(force_bytes(user.pk))}/{default_token_generator.make_token(user)}/
#         """
#         email = EmailMessage(mail_subject, message, to=[form.cleaned_data['email']])
#         email.send()

#         return JsonResponse({'message': 'Signup successful. Check your email for confirmation.'}, status=201)
    
#     return JsonResponse({'error': form.errors}, status=400)

# ### EMAIL VERIFICATION ###
# @api_view(['GET'])
# def activate_account(request, uidb64, token):
#     try:
#         uid = urlsafe_base64_decode(uidb64).decode()
#         user = CustomUser.objects.get(pk=uid)
#         if default_token_generator.check_token(user, token):
#             user.is_active = True
#             user.save()
#             return JsonResponse({'message': 'Account activated successfully.'})
#         return JsonResponse({'error': 'Invalid activation link'}, status=400)
#     except:
#         return JsonResponse({'error': 'Activation failed'}, status=400)

# ### LOGIN ###
# @csrf_exempt
# @api_view(['POST'])
# def customer_login(request):
#     data = json.loads(request.body)
#     email = data.get('email')
#     password = data.get('password')

#     user = authenticate(email=email, password=password)
#     if user:
#         if not user.is_active:
#             return JsonResponse({'error': 'Verify your email first'}, status=403)
#         login(request, user)
#         token, created = Token.objects.get_or_create(user=user)
#         return JsonResponse({'message': 'Login successful', 'token': token.key})
    
#     return JsonResponse({'error': 'Invalid email or password'}, status=400)

# ### LOGOUT ###
# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# def logout_customer(request):
#     request.user.auth_token.delete()  # Remove token
#     logout(request)
#     return JsonResponse({'message': 'Logout successful'})

# ### PASSWORD RESET (Request Email) ###
# @csrf_exempt
# @api_view(['POST'])
# def password_reset_request(request):
#     data = json.loads(request.body)
#     email = data.get('email')

#     user = CustomUser.objects.filter(email=email).first()
#     if user:
#         mail_subject = 'Reset Your Password'
#         message = f"""
#         Hello {user.first_name}, 
#         Click the link below to reset your password:
#         http://{get_current_site(request).domain}/api/password-reset/{urlsafe_base64_encode(force_bytes(user.pk))}/{default_token_generator.make_token(user)}/
#         """
#         email = EmailMessage(mail_subject, message, to=[email])
#         email.send()
#         return JsonResponse({'message': 'Password reset link sent to your email'}, status=200)

#     return JsonResponse({'error': 'User not found'}, status=404)

# ### PASSWORD RESET (Submit New Password) ###
# @csrf_exempt
# @api_view(['POST'])
# def password_reset_confirm(request, uidb64, token):
#     try:
#         uid = urlsafe_base64_decode(uidb64).decode()
#         user = CustomUser.objects.get(pk=uid)
#         if default_token_generator.check_token(user, token):
#             data = json.loads(request.body)
#             new_password = data.get('password')
#             user.set_password(new_password)
#             user.save()
#             return JsonResponse({'message': 'Password reset successful'})
#         return JsonResponse({'error': 'Invalid reset link'}, status=400)
#     except:
#         return JsonResponse({'error': 'Reset failed'}, status=400)

# ### UPDATE PASSWORD ###
# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# def update_password(request):
#     data = json.loads(request.body)
#     old_password = data.get('old_password')
#     new_password = data.get('new_password')

#     if not request.user.check_password(old_password):
#         return JsonResponse({'error': 'Incorrect old password'}, status=400)

#     request.user.set_password(new_password)
#     request.user.save()
#     update_session_auth_hash(request, request.user)  # Keep the user logged in
#     return JsonResponse({'message': 'Password updated successfully'})

# ### UPDATE PROFILE DETAILS ###
# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# def update_profile(request, field):
#     form_classes = {
#         'name': UpdateNameForm,
#         'email': UpdateEmailForm,
#         'phone': UpdatePhoneForm,
#         'address': UpdateAddressForm,
#         'dob': UpdateDobForm
#     }

#     if field not in form_classes:
#         return JsonResponse({'error': 'Invalid update field'}, status=400)

#     form = form_classes[field](request.data, instance=request.user.customerprofile if field != 'email' else request.user)
#     if form.is_valid():
#         form.save()
#         return JsonResponse({'message': f'{field.capitalize()} updated successfully'})
    
#     return JsonResponse({'error': form.errors}, status=400)

# ### UPDATE PROFILE PICTURE ###
# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# def update_display_picture(request):
#     picture = request.FILES.get('file')
#     if not picture:
#         return JsonResponse({'error': 'No file uploaded'}, status=400)

#     profile = request.user.customerprofile
#     profile.image = picture
#     profile.save()
#     return JsonResponse({'image': profile.image.url})











# from rest_framework import status
# from rest_framework.decorators import api_view, permission_classes
# from rest_framework.permissions import IsAuthenticated
# from rest_framework.response import Response
# from django.contrib.auth import authenticate, login, logout
# from django.contrib.sites.shortcuts import get_current_site
# from django.template.loader import render_to_string
# from django.utils.http import urlsafe_base64_encode
# from django.utils.encoding import force_bytes
# from django.core.mail import EmailMessage
# from django.contrib.auth.tokens import default_token_generator
# from django.contrib.auth.decorators import login_required
# from .models import CustomUser, CustomerProfile
# from .serializers import (
#     CustomerRegistrationSerializer, UpdateNameSerializer, UpdateEmailSerializer,
#     UpdatePasswordSerializer, UpdatePhoneSerializer, UpdateAddressSerializer, UpdateDobSerializer
# )

# @api_view(['POST'])
# def customer_registration(request):
#     serializer = CustomerRegistrationSerializer(data=request.data)
#     if serializer.is_valid():
#         user = serializer.save()
#         CustomerProfile.objects.create(user=user)
#         current_site = get_current_site(request)
#         mail_subject = 'Activate your account'
#         message = render_to_string('myadmin/verifymail.html', {
#             'user': user,
#             'domain': current_site.domain,
#             'utoken': urlsafe_base64_encode(force_bytes(user.pk)),
#             'token': default_token_generator.make_token(user),
#         })
#         email = EmailMessage(mail_subject, message, to=[user.email])
#         email.content_subtype = "html"
#         email.send()
#         return Response({'message': 'Signup successful. Check your email for confirmation'}, status=status.HTTP_201_CREATED)
#     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# @api_view(['POST'])
# def customer_login(request):
#     email = request.data.get('email')
#     password = request.data.get('password')
#     user = authenticate(request, email=email, password=password)
#     if user:
#         login(request, user)
#         return Response({'message': 'Login successful'}, status=status.HTTP_200_OK)
#     return Response({'error': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)

# @api_view(['POST'])
# def logout_customer(request):
#     logout(request)
#     return Response({'message': 'Logged out successfully'}, status=status.HTTP_200_OK)

# @api_view(['PATCH'])
# @permission_classes([IsAuthenticated])
# def update_name(request):
#     serializer = UpdateNameSerializer(request.user, data=request.data, partial=True)
#     if serializer.is_valid():
#         serializer.save()
#         return Response({'message': 'Name updated successfully'}, status=status.HTTP_200_OK)
#     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# @api_view(['PATCH'])
# @permission_classes([IsAuthenticated])
# def update_email(request):
#     serializer = UpdateEmailSerializer(request.user, data=request.data, partial=True)
#     if serializer.is_valid():
#         if request.user.check_password(request.data.get('password')):
#             serializer.save()
#             return Response({'message': 'Email updated successfully'}, status=status.HTTP_200_OK)
#         return Response({'error': 'Incorrect password'}, status=status.HTTP_400_BAD_REQUEST)
#     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# @api_view(['PATCH'])
# @permission_classes([IsAuthenticated])
# def update_password(request):
#     serializer = UpdatePasswordSerializer(user=request.user, data=request.data)
#     if serializer.is_valid():
#         user = serializer.save()
#         return Response({'message': 'Password changed successfully'}, status=status.HTTP_200_OK)
#     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# @api_view(['PATCH'])
# @permission_classes([IsAuthenticated])
# def update_phone(request):
#     profile = request.user.customerprofile
#     serializer = UpdatePhoneSerializer(profile, data=request.data, partial=True)
#     if serializer.is_valid():
#         serializer.save()
#         return Response({'message': 'Phone updated successfully'}, status=status.HTTP_200_OK)
#     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# @api_view(['PATCH'])
# @permission_classes([IsAuthenticated])
# def update_address(request):
#     profile = request.user.customerprofile
#     serializer = UpdateAddressSerializer(profile, data=request.data, partial=True)
#     if serializer.is_valid():
#         serializer.save()
#         return Response({'message': 'Address updated successfully'}, status=status.HTTP_200_OK)
#     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# @api_view(['PATCH'])
# @permission_classes([IsAuthenticated])
# def update_dob(request):
#     profile = request.user.customerprofile
#     serializer = UpdateDobSerializer(profile, data=request.data, partial=True)
#     if serializer.is_valid():
#         serializer.save()
#         return Response({'message': 'Date of birth updated successfully'}, status=status.HTTP_200_OK)
#     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# def update_display_picture(request):
#     profile = request.user.customerprofile
#     if 'file' in request.FILES:
#         profile.image = request.FILES['file']
#         profile.save()
#         return Response({'image_url': profile.image.url}, status=status.HTTP_200_OK)
#     return Response({'error': 'No file uploaded'}, status=status.HTTP_400_BAD_REQUEST)
