
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import authenticate, login, logout
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import EmailMessage
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.decorators import login_required
from .models import CustomUser, CustomerProfile
from .serializers import (
    CustomerRegistrationSerializer, UpdateNameSerializer, UpdateEmailSerializer,
    UpdatePasswordSerializer, UpdatePhoneSerializer, UpdateAddressSerializer, UpdateDobSerializer
)

@api_view(['POST'])
def customer_registration(request):
    serializer = CustomerRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        CustomerProfile.objects.create(user=user)
        current_site = get_current_site(request)
        mail_subject = 'Activate your account'
        message = render_to_string('myadmin/verifymail.html', {
            'user': user,
            'domain': current_site.domain,
            'utoken': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': default_token_generator.make_token(user),
        })
        email = EmailMessage(mail_subject, message, to=[user.email])
        email.content_subtype = "html"
        email.send()
        return Response({'message': 'Signup successful. Check your email for confirmation'}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def customer_login(request):
    email = request.data.get('email')
    password = request.data.get('password')
    user = authenticate(request, email=email, password=password)
    if user:
        login(request, user)
        return Response({'message': 'Login successful'}, status=status.HTTP_200_OK)
    return Response({'error': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def logout_customer(request):
    logout(request)
    return Response({'message': 'Logged out successfully'}, status=status.HTTP_200_OK)

@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_name(request):
    serializer = UpdateNameSerializer(request.user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response({'message': 'Name updated successfully'}, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_email(request):
    serializer = UpdateEmailSerializer(request.user, data=request.data, partial=True)
    if serializer.is_valid():
        if request.user.check_password(request.data.get('password')):
            serializer.save()
            return Response({'message': 'Email updated successfully'}, status=status.HTTP_200_OK)
        return Response({'error': 'Incorrect password'}, status=status.HTTP_400_BAD_REQUEST)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_password(request):
    serializer = UpdatePasswordSerializer(user=request.user, data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response({'message': 'Password changed successfully'}, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_phone(request):
    profile = request.user.customerprofile
    serializer = UpdatePhoneSerializer(profile, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response({'message': 'Phone updated successfully'}, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_address(request):
    profile = request.user.customerprofile
    serializer = UpdateAddressSerializer(profile, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response({'message': 'Address updated successfully'}, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_dob(request):
    profile = request.user.customerprofile
    serializer = UpdateDobSerializer(profile, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response({'message': 'Date of birth updated successfully'}, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_display_picture(request):
    profile = request.user.customerprofile
    if 'file' in request.FILES:
        profile.image = request.FILES['file']
        profile.save()
        return Response({'image_url': profile.image.url}, status=status.HTTP_200_OK)
    return Response({'error': 'No file uploaded'}, status=status.HTTP_400_BAD_REQUEST)
