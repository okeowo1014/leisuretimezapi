from rest_framework import generics, serializers, permissions
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.http import JsonResponse
from .models import Package, PackageImage, GuestImage, Destination, Event, CustomerProfile, Booking, Locations

# Serializers
class PackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Package
        fields = '__all__'

class PackageImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PackageImage
        fields = '__all__'

class GuestImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = GuestImage
        fields = '__all__'

class DestinationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Destination
        fields = '__all__'

class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = '__all__'

class CustomerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerProfile
        fields = '__all__'

class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = '__all__'

class LocationsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Locations
        fields = '__all__'

# API Views
@api_view(['GET'])
def index(request):
    packages = Package.objects.filter(status='active')
    destinations = Destination.objects.filter(status='active')
    events = Event.objects.filter(status='active')
    return Response({
        'packages': PackageSerializer(packages, many=True).data,
        'destinations': DestinationSerializer(destinations, many=True).data,
        'events': EventSerializer(events, many=True).data,
    })

@api_view(['GET'])
def package_list(request):
    packages = Package.objects.filter(status='active').order_by('-id', 'category')
    return Response(PackageSerializer(packages, many=True).data)

@api_view(['GET'])
def package_details(request, pid):
    package = get_object_or_404(Package, package_id=pid)
    package_images = PackageImage.objects.filter(package=package)
    guest_images = GuestImage.objects.filter(package=package)
    return Response({
        'package': PackageSerializer(package).data,
        'package_images': PackageImageSerializer(package_images, many=True).data,
        'guest_images': GuestImageSerializer(guest_images, many=True).data,
    })

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def personal_booking(request):
    profile = get_object_or_404(CustomerProfile, user=request.user)
    return Response(CustomerProfileSerializer(profile).data)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def booking_history(request):
    history = Booking.objects.filter(customer__user=request.user)
    return Response(BookingSerializer(history, many=True).data)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def account_settings(request):
    profile = get_object_or_404(CustomerProfile, user=request.user)
    history = Booking.objects.filter(customer__user=request.user)
    return Response({
        'profile': CustomerProfileSerializer(profile).data,
        'booking_histories': BookingSerializer(history, many=True).data
    })

@api_view(['GET'])
def search_locations(request):
    country = request.GET.get('country')
    states = request.GET.get('state', '').split('-')
    location_type = request.GET.get('type')

    state_queries = Q()
    for state in states:
        state_queries |= Q(state__icontains=state)

    locations = Locations.objects.filter(
        Q(country__iexact=country) & state_queries & Q(type__iexact=location_type)
    )
    return Response(LocationsSerializer(locations, many=True).data)

# URLs (in urls.py)
from django.urls import path
urlpatterns = [
    path('api/index/', index, name='api-index'),
    path('api/packages/', package_list, name='api-packages'),
    path('api/packages/<str:pid>/', package_details, name='api-package-details'),
    path('api/personal-booking/', personal_booking, name='api-personal-booking'),
    path('api/booking-history/', booking_history, name='api-booking-history'),
    path('api/account-settings/', account_settings, name='api-account-settings'),
    path('api/search-locations/', search_locations, name='api-search-locations'),
]
