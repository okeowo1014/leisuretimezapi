"""
Serializers for the Leisuretimez API.

Handles serialization/deserialization for users, profiles, bookings,
packages, invoices, payments, destinations, events, contacts, wallets,
and transactions.
"""

from rest_framework import serializers

from .models import (
    AdminProfile, Booking, Contact, CustomUser, CustomerProfile,
    Destination, DestinationImage, Event, EventImage, GuestImage,
    Invoice, Locations, Package, PackageImage, Payment,
    Transaction, Wallet,
)


# ---------------------------------------------------------------------------
# User Serializers
# ---------------------------------------------------------------------------

class CustomUserSerializer(serializers.ModelSerializer):
    """Serializer for user registration and basic user data."""

    class Meta:
        model = CustomUser
        fields = ('id', 'email', 'firstname', 'lastname', 'password')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        return CustomUser.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            firstname=validated_data.get('firstname', ''),
            lastname=validated_data.get('lastname', ''),
        )


class UserSerializer(serializers.ModelSerializer):
    """Minimal user serializer for nested representations."""

    class Meta:
        model = CustomUser
        fields = ['id', 'email']


class CustomUserProfileSerializer(serializers.ModelSerializer):
    """User serializer for profile updates (email read-only)."""

    class Meta:
        model = CustomUser
        fields = ['email', 'firstname', 'lastname']
        read_only_fields = ['email']


# ---------------------------------------------------------------------------
# Profile Serializers
# ---------------------------------------------------------------------------

class CustomerProfileSerializer(serializers.ModelSerializer):
    """Full customer profile serializer with nested user data."""

    user = CustomUserSerializer()

    class Meta:
        model = CustomerProfile
        fields = '__all__'

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user = CustomUser.objects.create_user(**user_data)
        return CustomerProfile.objects.create(user=user, **validated_data)


class CustomerProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating customer profile (excludes user and image)."""

    class Meta:
        model = CustomerProfile
        exclude = ['user', 'image']


class CustomersProfileSerializer(serializers.ModelSerializer):
    """Profile serializer with updatable user fields."""

    user = CustomUserProfileSerializer()

    class Meta:
        model = CustomerProfile
        fields = [
            'id', 'user', 'address', 'city', 'state', 'country',
            'phone', 'date_of_birth', 'marital_status', 'profession',
            'image', 'status',
        ]
        read_only_fields = ['id', 'status']

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        if user_data:
            user = instance.user
            user.firstname = user_data.get('firstname', user.firstname)
            user.lastname = user_data.get('lastname', user.lastname)
            user.save()

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class AdminProfileSerializer(serializers.ModelSerializer):
    """Serializer for admin profiles."""

    user = CustomUserSerializer()

    class Meta:
        model = AdminProfile
        fields = '__all__'


# ---------------------------------------------------------------------------
# Location Serializer
# ---------------------------------------------------------------------------

class LocationsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Locations
        fields = '__all__'


# ---------------------------------------------------------------------------
# Booking Serializer
# ---------------------------------------------------------------------------

class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        exclude = ['customer']


# ---------------------------------------------------------------------------
# Package Serializers
# ---------------------------------------------------------------------------

class PackageImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PackageImage
        fields = '__all__'


class PackageSerializer(serializers.ModelSerializer):
    """Package serializer with nested images and saved status."""

    package_images = PackageImageSerializer(many=True, read_only=True)
    is_saved = serializers.BooleanField(read_only=True, default=False)

    class Meta:
        model = Package
        fields = '__all__'


class GuestImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = GuestImage
        fields = '__all__'


# ---------------------------------------------------------------------------
# Invoice & Payment Serializers
# ---------------------------------------------------------------------------

class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = '__all__'


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'


# ---------------------------------------------------------------------------
# Destination Serializers
# ---------------------------------------------------------------------------

class DestinationImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = DestinationImage
        fields = '__all__'


class DestinationSerializer(serializers.ModelSerializer):
    """Destination serializer with nested images."""

    destination_images = DestinationImageSerializer(many=True, read_only=True)

    class Meta:
        model = Destination
        fields = '__all__'


# ---------------------------------------------------------------------------
# Event Serializers
# ---------------------------------------------------------------------------

class EventImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventImage
        fields = '__all__'


class EventSerializer(serializers.ModelSerializer):
    """Event serializer with nested images."""

    event_images = EventImageSerializer(many=True, read_only=True)

    class Meta:
        model = Event
        fields = '__all__'


# ---------------------------------------------------------------------------
# Contact Serializer
# ---------------------------------------------------------------------------

class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = '__all__'


# ---------------------------------------------------------------------------
# Authentication Serializers
# ---------------------------------------------------------------------------

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(style={'input_type': 'password'})


class AuthTokenSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(style={'input_type': 'password'})
    token = serializers.CharField(max_length=255, read_only=True)


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)


class ResetConfirmationSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)


class ResetPasswordConfirmSerializer(serializers.Serializer):
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)


# ---------------------------------------------------------------------------
# Wallet & Transaction Serializers
# ---------------------------------------------------------------------------

class WalletSerializer(serializers.ModelSerializer):
    """Wallet serializer with nested user data."""

    user = UserSerializer(read_only=True)

    class Meta:
        model = Wallet
        fields = ['id', 'user', 'balance', 'created_at', 'updated_at', 'is_active']
        read_only_fields = ['balance']


class WalletUserSerializer(serializers.ModelSerializer):
    """Minimal wallet serializer for embedded use."""

    class Meta:
        model = Wallet
        fields = ['id', 'balance', 'updated_at', 'is_active']
        read_only_fields = ['balance']


class TransactionSerializer(serializers.ModelSerializer):
    """Transaction serializer with nested recipient data."""

    recipient = UserSerializer(read_only=True)

    class Meta:
        model = Transaction
        fields = [
            'id', 'amount', 'transaction_type', 'status',
            'recipient', 'description', 'created_at', 'updated_at',
        ]
        read_only_fields = ['status', 'wallet', 'recipient']


class DepositSerializer(serializers.Serializer):
    amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=1
    )
    payment_method_id = serializers.CharField(max_length=100, required=False)
    success_url = serializers.URLField(required=False)
    cancel_url = serializers.URLField(required=False)


class WithdrawalSerializer(serializers.Serializer):
    amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=1
    )


class TransferSerializer(serializers.Serializer):
    recipient_id = serializers.UUIDField()
    amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=1
    )
