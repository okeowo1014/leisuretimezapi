from rest_framework import serializers

from index.models import CustomUser, CustomerProfile, Wallet


class AdminCustomerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerProfile
        fields = (
            'id', 'address', 'city', 'state', 'country', 'phone',
            'date_of_birth', 'marital_status', 'profession', 'image',
            'status', 'gender',
        )


class AdminWalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = ('id', 'balance', 'is_active', 'created_at')


class AdminUserListSerializer(serializers.ModelSerializer):
    booking_count = serializers.IntegerField(read_only=True)
    wallet_balance = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True, default=0,
    )

    class Meta:
        model = CustomUser
        fields = (
            'id', 'email', 'firstname', 'lastname', 'is_active', 'is_staff',
            'is_superuser', 'date_joined', 'status', 'booking_count',
            'wallet_balance',
        )


class AdminUserDetailSerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()
    wallet = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = (
            'id', 'email', 'firstname', 'lastname', 'is_active', 'is_staff',
            'is_superuser', 'date_joined', 'status', 'profile', 'wallet',
        )

    def get_profile(self, obj):
        try:
            return AdminCustomerProfileSerializer(obj.customerprofile).data
        except CustomerProfile.DoesNotExist:
            return None

    def get_wallet(self, obj):
        try:
            return AdminWalletSerializer(obj.wallet).data
        except Wallet.DoesNotExist:
            return None


class AdminUserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('firstname', 'lastname', 'is_active', 'is_staff', 'status')
