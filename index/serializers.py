from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    CustomUser, CustomerProfile, AdminProfile, Booking, Package, 
    PackageImage, Invoice, Payment, Destination, DestinationImage,
    Event, EventImage, GuestImage, Contact, Locations, Transaction, Wallet
)
# serializers.py

# CustomUser = get_user_model()

class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('id', 'email', 'firstname', 'lastname', 'password')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = CustomUser.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            firstname=validated_data.get('firstname', ''),
            lastname=validated_data.get('lastname', ''),
        )
        return user

# class CustomerProfileUpdateSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = CustomerProfile
#         # Customize fields to exclude or include
#         exclude = ['user']  # For example, do not allow editing user from here

class CustomerProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerProfile
        # Customize fields to exclude or include
        exclude = ['user','image']  # For example, do not allow editing user from here



class CustomerProfileSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer()

    class Meta:
        model = CustomerProfile
        fields = '__all__'

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user = CustomUser.objects.create_user(**user_data)
        customer_profile = CustomerProfile.objects.create(user=user, **validated_data)
        return customer_profile
    

class AdminProfileSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer()

    class Meta:
        model = AdminProfile
        fields = '__all__'

class LocationsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Locations
        fields = '__all__'

class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        # fields = '__all__'
        exclude = ["customer"]


class PackageImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PackageImage
        fields = '__all__'

class PackageSerializer(serializers.ModelSerializer):
    package_images = PackageImageSerializer(many=True, read_only=True)
    is_saved = serializers.BooleanField(read_only=True,default=False)  # Add this field

    class Meta:
        model = Package
        fields = '__all__'

class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = '__all__'

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'

class DestinationImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = DestinationImage
        fields = '__all__'

class DestinationSerializer(serializers.ModelSerializer):
    destination_images = DestinationImageSerializer(many=True, read_only=True)
    
    class Meta:
        model = Destination
        fields = '__all__'

class EventImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventImage
        fields = '__all__'

class EventSerializer(serializers.ModelSerializer):
    event_images = EventImageSerializer(many=True, read_only=True)
    
    class Meta:
        model = Event
        fields = '__all__'

class GuestImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = GuestImage
        fields = '__all__'

class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = '__all__'

# Authentication Serializers
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




class CustomUserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['email', 'firstname', 'lastname']
        read_only_fields = ['email']  # Email can't be changed

class CustomersProfileSerializer(serializers.ModelSerializer):
    user = CustomUserProfileSerializer()
    
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


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        # fields = '__all__'
        fields = ['id','email']

class WalletSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Wallet
        fields = ['id', 'user', 'balance', 'created_at', 'updated_at', 'is_active']
        read_only_fields = ['balance']

class TransactionSerializer(serializers.ModelSerializer):
    # wallet = serializers.PrimaryKeyRelatedField(read_only=True)
    recipient = UserSerializer(read_only=True)
    
    class Meta:
        model = Transaction
        fields = [
            'id','amount', 'transaction_type', 
            'status', 'recipient', 'description', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['status', 'wallet', 'recipient']
        

class DepositSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=1)
    payment_method_id = serializers.CharField(max_length=100, required=False)
    success_url = serializers.URLField(required=False)
    cancel_url = serializers.URLField(required=False)
    
class WithdrawalSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=1)
    
class TransferSerializer(serializers.Serializer):
    recipient_id = serializers.UUIDField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=1)

class WalletUserSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Wallet
        fields = ['id','balance','updated_at', 'is_active']
        read_only_fields = ['balance']

# class WalletSerializer(serializers.ModelSerializer):
#     user = UserSerializer(read_only=True)
    
#     class Meta:
#         model = Wallet
#         fields = ['id', 'user', 'balance', 'created_at', 'updated_at', 'is_active']
#         read_only_fields = ['balance']

# class TransactionSerializer(serializers.ModelSerializer):
#     wallet = serializers.PrimaryKeyRelatedField(read_only=True)
#     recipient = UserSerializer(read_only=True)
    
#     class Meta:
#         model = Transaction
#         fields = [
#             'id', 'wallet', 'amount', 'transaction_type', 
#             'status', 'recipient', 'description', 
#             'created_at', 'updated_at'
#         ]
#         read_only_fields = ['status', 'wallet', 'recipient']

# class DepositSerializer(serializers.Serializer):
#     amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0.01)
#     payment_method_id = serializers.CharField(max_length=100,required=False)
    
# class WithdrawalSerializer(serializers.Serializer):
#     amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0.01)
    
# # class TransferSerializer(serializers.Serializer):
#     recipient_id = serializers.UUIDField()
#     amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0.01)