# serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import CustomerProfile

CustomUser = get_user_model()

class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['email', 'firstname', 'lastname']
        read_only_fields = ['email']  # Email can't be changed

class CustomerProfileSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer()
    
    class Meta:
        model = CustomerProfile
        fields = [
            'id', 'user', 'address', 'city', 'state', 'country',
            'phone', 'date_of_birth', 'marital_status', 'profession',
            'image', 'status'
        ]
        read_only_fields = ['id', 'status']

    def update(self, instance, validated_data):
        # Handle nested user data update
        user_data = validated_data.pop('user', {})
        if user_data:
            user = instance.user
            user.firstname = user_data.get('firstname', user.firstname)
            user.lastname = user_data.get('lastname', user.lastname)
            user.save()

        # Update profile data
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        return instance

# views.py
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404

class CustomerProfileDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = CustomerProfileSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def get_object(self):
        """
        Get the profile for the current user
        """
        return get_object_or_404(CustomerProfile, user=self.request.user)

    def patch(self, request, *args, **kwargs):
        """
        Handle partial updates
        """
        profile = self.get_object()
        serializer = self.get_serializer(profile, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, *args, **kwargs):
        """
        Handle full updates
        """
        profile = self.get_object()
        serializer = self.get_serializer(profile, data=request.data)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CustomerProfileImageUpdateView(generics.UpdateAPIView):
    serializer_class = CustomerProfileSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def get_object(self):
        return get_object_or_404(CustomerProfile, user=self.request.user)

    def patch(self, request, *args, **kwargs):
        """
        Handle profile image updates
        """
        profile = self.get_object()
        
        if 'image' not in request.FILES:
            return Response(
                {'error': 'No image file provided'},
                status=status.HTTP_400_BAD_REQUEST
            )

        profile.image = request.FILES['image']
        profile.save()

        serializer = self.get_serializer(profile)
        return Response(serializer.data)

# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('profile/', 
         views.CustomerProfileDetailView.as_view(), 
         name='customer-profile'),
    path('profile/image/', 
         views.CustomerProfileImageUpdateView.as_view(), 
         name='profile-image-update'),
]