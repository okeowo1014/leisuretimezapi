"""
Serializers for the Leisuretimez API.

Handles serialization/deserialization for users, profiles, bookings,
packages, invoices, payments, destinations, events, contacts, wallets,
and transactions.
"""

from decimal import Decimal

from rest_framework import serializers

from .models import (
    AdminProfile, BlogComment, BlogPost, BlogReaction,
    Booking, Contact, CustomUser, CustomerProfile,
    Destination, DestinationImage, Event, EventImage, GuestImage,
    Invoice, Locations, Notification, Package, PackageImage, Payment,
    PromoCode, Review, SupportMessage, SupportTicket,
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
        read_only_fields = ['booking_id']
        extra_kwargs = {
            'package': {'required': False},
        }


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
            'recipient', 'reference', 'description', 'created_at', 'updated_at',
        ]
        read_only_fields = ['status', 'wallet', 'recipient']


class DepositSerializer(serializers.Serializer):
    amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=Decimal('1.00')
    )
    payment_method_id = serializers.CharField(max_length=100, required=False)
    success_url = serializers.URLField(required=False)
    cancel_url = serializers.URLField(required=False)


class WithdrawalSerializer(serializers.Serializer):
    amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=Decimal('1.00')
    )


class TransferSerializer(serializers.Serializer):
    recipient_id = serializers.UUIDField()
    amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, min_value=Decimal('1.00')
    )


# ---------------------------------------------------------------------------
# Review Serializers
# ---------------------------------------------------------------------------

class ReviewSerializer(serializers.ModelSerializer):
    """Serializer for package reviews."""

    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = [
            'id', 'user_email', 'user_name', 'package', 'rating',
            'comment', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'user_email', 'user_name', 'created_at', 'updated_at']

    def get_user_name(self, obj):
        return f"{obj.user.firstname} {obj.user.lastname}"


class ReviewCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a review (package set via URL)."""

    class Meta:
        model = Review
        fields = ['rating', 'comment']


# ---------------------------------------------------------------------------
# Promo Code Serializers
# ---------------------------------------------------------------------------

class PromoCodeApplySerializer(serializers.Serializer):
    """Serializer for applying a promo code to a booking."""
    code = serializers.CharField(max_length=50)


# ---------------------------------------------------------------------------
# Notification Serializers
# ---------------------------------------------------------------------------

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            'id', 'notification_type', 'title', 'message',
            'is_read', 'booking', 'created_at',
        ]
        read_only_fields = [
            'id', 'notification_type', 'title', 'message',
            'booking', 'created_at',
        ]


# ---------------------------------------------------------------------------
# Support Ticket Serializers
# ---------------------------------------------------------------------------

class SupportMessageSerializer(serializers.ModelSerializer):
    """Serializer for messages within a support ticket."""

    sender_email = serializers.EmailField(source='sender.email', read_only=True)

    class Meta:
        model = SupportMessage
        fields = ['id', 'sender_email', 'message', 'created_at']
        read_only_fields = ['id', 'sender_email', 'created_at']


class SupportTicketSerializer(serializers.ModelSerializer):
    """Serializer for support tickets with nested messages."""

    messages = SupportMessageSerializer(many=True, read_only=True)

    class Meta:
        model = SupportTicket
        fields = [
            'id', 'subject', 'status', 'priority',
            'created_at', 'updated_at', 'messages',
        ]
        read_only_fields = ['id', 'status', 'created_at', 'updated_at']


class SupportTicketCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a support ticket with initial message."""

    message = serializers.CharField(write_only=True)

    class Meta:
        model = SupportTicket
        fields = ['subject', 'priority', 'message']


class SupportReplySerializer(serializers.Serializer):
    """Serializer for replying to a support ticket."""
    message = serializers.CharField()


# ---------------------------------------------------------------------------
# Booking Cancellation / Modification Serializers
# ---------------------------------------------------------------------------

class CancelBookingSerializer(serializers.Serializer):
    """Serializer for booking cancellation request."""
    reason = serializers.CharField(required=False, allow_blank=True, default='')


class ModifyBookingSerializer(serializers.Serializer):
    """Serializer for modifying a pending booking."""
    datefrom = serializers.DateField(required=False)
    dateto = serializers.DateField(required=False)
    adult = serializers.IntegerField(required=False, min_value=1)
    children = serializers.IntegerField(required=False, min_value=0)
    guests = serializers.IntegerField(required=False, min_value=0)


# ---------------------------------------------------------------------------
# Blog Serializers
# ---------------------------------------------------------------------------

class BlogReactionSerializer(serializers.ModelSerializer):
    """Serializer for blog post reactions."""

    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = BlogReaction
        fields = ['id', 'user_email', 'reaction_type', 'created_at']
        read_only_fields = ['id', 'user_email', 'created_at']


class BlogCommentSerializer(serializers.ModelSerializer):
    """Serializer for blog comments with user info and replies."""

    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.SerializerMethodField()
    replies = serializers.SerializerMethodField()

    class Meta:
        model = BlogComment
        fields = [
            'id', 'user_email', 'user_name', 'parent',
            'content', 'replies', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'user_email', 'user_name', 'created_at', 'updated_at']

    def get_user_name(self, obj):
        return f"{obj.user.firstname} {obj.user.lastname}"

    def get_replies(self, obj):
        if obj.parent is not None:
            return []
        replies = obj.replies.all()
        return BlogCommentSerializer(replies, many=True).data


class BlogCommentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a blog comment."""

    class Meta:
        model = BlogComment
        fields = ['content', 'parent']


class BlogPostSerializer(serializers.ModelSerializer):
    """Serializer for blog posts with aggregated counts."""

    author_name = serializers.SerializerMethodField()
    author_email = serializers.EmailField(source='author.email', read_only=True)
    comments_count = serializers.SerializerMethodField()
    reactions_count = serializers.SerializerMethodField()
    reaction_summary = serializers.SerializerMethodField()
    user_reaction = serializers.SerializerMethodField()
    tags_list = serializers.SerializerMethodField()

    class Meta:
        model = BlogPost
        fields = [
            'id', 'author_name', 'author_email', 'title', 'slug',
            'content', 'excerpt', 'cover_image', 'status', 'tags',
            'tags_list', 'published_at', 'created_at', 'updated_at',
            'comments_count', 'reactions_count', 'reaction_summary',
            'user_reaction',
        ]
        read_only_fields = [
            'id', 'author_name', 'author_email', 'slug',
            'created_at', 'updated_at', 'comments_count',
            'reactions_count', 'reaction_summary', 'user_reaction',
        ]

    def get_author_name(self, obj):
        return f"{obj.author.firstname} {obj.author.lastname}"

    def get_comments_count(self, obj):
        return obj.comments.count()

    def get_reactions_count(self, obj):
        return obj.reactions.count()

    def get_reaction_summary(self, obj):
        from django.db.models import Count
        return dict(
            obj.reactions.values_list('reaction_type')
            .annotate(count=Count('id'))
            .values_list('reaction_type', 'count')
        )

    def get_user_reaction(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            reaction = obj.reactions.filter(user=request.user).first()
            if reaction:
                return reaction.reaction_type
        return None

    def get_tags_list(self, obj):
        if obj.tags:
            return [t.strip() for t in obj.tags.split(',') if t.strip()]
        return []


class BlogPostCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating a blog post (admin only)."""

    class Meta:
        model = BlogPost
        fields = ['title', 'content', 'excerpt', 'cover_image', 'status', 'tags']


class BlogReactSerializer(serializers.Serializer):
    """Serializer for reacting to a blog post."""
    reaction_type = serializers.ChoiceField(
        choices=BlogReaction.REACTION_CHOICES, default='like'
    )
