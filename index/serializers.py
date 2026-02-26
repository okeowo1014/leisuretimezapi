"""
Serializers for the Leisuretimez API.

Handles serialization/deserialization for users, profiles, bookings,
packages, invoices, payments, destinations, events, contacts, wallets,
and transactions.
"""

from decimal import Decimal

from rest_framework import serializers

from django.utils import timezone

from .models import (
    AdminProfile, BlogComment, BlogPost, BlogReaction,
    Booking, BookingActivityLog, BookingService, Carousel, Contact,
    CruiseType, CustomUser, CustomerProfile, Destination, DestinationImage,
    Event, EventImage, EventType, GuestImage, Invoice, Locations,
    Notification, Package, PackageImage, Payment, PaymentSchedule,
    PersonalisedBooking, PersonalisedBookingAttachment,
    PersonalisedBookingInvoice, PersonalisedBookingMessage,
    PersonalisedBookingPayment, PromoCode, Quotation, QuotationLineItem,
    Review, ServiceCatalog, SupportMessage, SupportTicket, Transaction,
    Wallet,
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


# ---------------------------------------------------------------------------
# Dynamic Lookup Serializers (EventType, CruiseType, ServiceCatalog)
# ---------------------------------------------------------------------------

class EventTypeSerializer(serializers.ModelSerializer):
    """Read-only serializer — apps fetch this to populate event-type pickers."""

    class Meta:
        model = EventType
        fields = ['id', 'slug', 'name', 'description', 'icon', 'position']


class CruiseTypeSerializer(serializers.ModelSerializer):
    """Read-only serializer — apps fetch this to populate cruise-type pickers."""

    class Meta:
        model = CruiseType
        fields = ['id', 'slug', 'name', 'description', 'icon', 'position']


class ServiceCatalogSerializer(serializers.ModelSerializer):
    """Read-only serializer — apps fetch this to render the service picker."""

    class Meta:
        model = ServiceCatalog
        fields = [
            'id', 'slug', 'name', 'category', 'description',
            'base_price', 'icon', 'position',
        ]


# ---------------------------------------------------------------------------
# Booking Service (through table)
# ---------------------------------------------------------------------------

class BookingServiceSerializer(serializers.ModelSerializer):
    """Read serializer for services attached to a personalised booking."""

    service_name = serializers.CharField(source='service.name', read_only=True)
    service_slug = serializers.SlugField(source='service.slug', read_only=True)
    service_category = serializers.CharField(source='service.category', read_only=True)
    line_total = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True,
    )

    class Meta:
        model = BookingService
        fields = [
            'id', 'service', 'service_name', 'service_slug',
            'service_category', 'quantity', 'unit_price',
            'notes', 'line_total', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class BookingServiceWriteSerializer(serializers.ModelSerializer):
    """Write serializer for adding/updating a service on a booking."""

    class Meta:
        model = BookingService
        fields = ['service', 'quantity', 'notes']


# ---------------------------------------------------------------------------
# Personalised Booking Messages & Attachments
# ---------------------------------------------------------------------------

class PersonalisedBookingMessageSerializer(serializers.ModelSerializer):
    """Read serializer for booking conversation messages."""

    sender_email = serializers.EmailField(source='sender.email', read_only=True)
    sender_name = serializers.SerializerMethodField()

    class Meta:
        model = PersonalisedBookingMessage
        fields = ['id', 'sender_email', 'sender_name', 'message', 'created_at']
        read_only_fields = ['id', 'sender_email', 'sender_name', 'created_at']

    def get_sender_name(self, obj):
        return f"{obj.sender.firstname} {obj.sender.lastname}"


class PersonalisedBookingMessageCreateSerializer(serializers.Serializer):
    """Write serializer for posting a message on a booking thread."""
    message = serializers.CharField()


class PersonalisedBookingAttachmentSerializer(serializers.ModelSerializer):
    """Read serializer for booking attachments."""

    uploaded_by_email = serializers.EmailField(
        source='uploaded_by.email', read_only=True,
    )

    class Meta:
        model = PersonalisedBookingAttachment
        fields = [
            'id', 'uploaded_by_email', 'file', 'category',
            'description', 'created_at',
        ]
        read_only_fields = ['id', 'uploaded_by_email', 'created_at']


class PersonalisedBookingAttachmentCreateSerializer(serializers.ModelSerializer):
    """Write serializer for uploading an attachment."""

    class Meta:
        model = PersonalisedBookingAttachment
        fields = ['file', 'category', 'description']


# ---------------------------------------------------------------------------
# Personalised Booking Serializers
# ---------------------------------------------------------------------------

class PersonalisedBookingSerializer(serializers.ModelSerializer):
    """Full read serializer for personalised bookings.

    Returns nested event_type/cruise_type objects, computed services list,
    message count, and quote info — everything both mobile and web apps need.
    """

    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.SerializerMethodField()
    event_type = serializers.SlugRelatedField(slug_field='slug', read_only=True)
    cruise_type = serializers.SlugRelatedField(slug_field='slug', read_only=True)
    event_type_detail = EventTypeSerializer(source='event_type', read_only=True)
    cruise_type_detail = CruiseTypeSerializer(source='cruise_type', read_only=True)
    legacy_services = serializers.SerializerMethodField()
    booking_services = BookingServiceSerializer(many=True, read_only=True)
    messages_count = serializers.SerializerMethodField()
    attachments_count = serializers.SerializerMethodField()
    allowed_transitions = serializers.SerializerMethodField()
    assigned_to_email = serializers.EmailField(
        source='assigned_to.email', read_only=True, default=None,
    )

    class Meta:
        model = PersonalisedBooking
        fields = [
            'id', 'user_email', 'user_name',
            # Event info
            'event_type', 'event_type_detail', 'event_name',
            # Dates
            'date_from', 'date_to', 'duration_hours', 'duration_days',
            # Cruise
            'cruise_type', 'cruise_type_detail',
            # Location
            'continent', 'country', 'state', 'preferred_destination',
            # Guests
            'guests', 'adults', 'children',
            # Legacy service booleans (backward compat for current mobile app)
            'catering', 'bar_attendance', 'decoration',
            'special_security', 'photography', 'entertainment',
            'legacy_services',
            # New flexible services
            'booking_services',
            # Budget & Pricing
            'budget_min', 'budget_max',
            'quote_amount', 'quote_expires_at',
            'deposit_amount', 'deposit_paid',
            # Accommodation
            'requires_accommodation', 'accommodation_type',
            # Notes
            'additional_comments', 'special_requests',
            # Status & Admin
            'status', 'allowed_transitions', 'admin_notes',
            'assigned_to', 'assigned_to_email',
            'rejection_reason', 'cancellation_reason',
            # Terms
            'terms_accepted',
            # Counts
            'messages_count', 'attachments_count',
            # Timestamps
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'user_email', 'user_name', 'status',
            'admin_notes', 'assigned_to', 'assigned_to_email',
            'rejection_reason', 'quote_amount', 'quote_expires_at',
            'deposit_amount', 'deposit_paid',
            'created_at', 'updated_at',
        ]

    def get_user_name(self, obj):
        return f"{obj.user.firstname} {obj.user.lastname}"

    def get_legacy_services(self, obj):
        """Backward-compatible list of selected legacy boolean services."""
        service_fields = [
            ('catering', 'Catering'),
            ('bar_attendance', 'Bar Attendance'),
            ('decoration', 'Decoration'),
            ('special_security', 'Special Security'),
            ('photography', 'Photography'),
            ('entertainment', 'Entertainment'),
        ]
        return [label for field, label in service_fields if getattr(obj, field)]

    def get_messages_count(self, obj):
        return obj.messages.count()

    def get_attachments_count(self, obj):
        return obj.attachments.count()

    def get_allowed_transitions(self, obj):
        return obj.ALLOWED_STATUS_TRANSITIONS.get(obj.status, [])


class PersonalisedBookingCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a personalised booking request.

    Includes full cross-field validation for dates, guest counts,
    cruise-specific requirements, and budget range.
    """

    event_type = serializers.SlugRelatedField(
        slug_field='slug', queryset=EventType.objects.all(),
    )
    cruise_type = serializers.CharField(
        required=False, allow_blank=True, default='',
    )
    service_ids = serializers.ListField(
        child=serializers.IntegerField(), required=False, write_only=True,
        help_text='List of ServiceCatalog IDs to attach to the booking',
    )

    class Meta:
        model = PersonalisedBooking
        fields = [
            'id',
            'event_type', 'event_name',
            'date_from', 'date_to', 'duration_hours', 'duration_days',
            'cruise_type',
            'continent', 'country', 'state', 'preferred_destination',
            'guests', 'adults', 'children',
            # Legacy booleans (still accepted for backward compat)
            'catering', 'bar_attendance', 'decoration',
            'special_security', 'photography', 'entertainment',
            # New flexible services
            'service_ids',
            # Budget
            'budget_min', 'budget_max',
            # Accommodation
            'requires_accommodation', 'accommodation_type',
            # Notes
            'additional_comments', 'special_requests',
            # Terms
            'terms_accepted',
        ]

    # ------------------------------------------------------------------
    # Field-level validation
    # ------------------------------------------------------------------

    def validate_date_from(self, value):
        if value < timezone.now().date():
            raise serializers.ValidationError('Start date cannot be in the past.')
        return value

    def validate_event_type(self, value):
        if not value.is_active:
            raise serializers.ValidationError('This event type is currently unavailable.')
        return value

    def validate_cruise_type(self, value):
        if not value:
            return None
        try:
            ct = CruiseType.objects.get(slug=value)
        except CruiseType.DoesNotExist:
            raise serializers.ValidationError(f'Unknown cruise type: {value}')
        if not ct.is_active:
            raise serializers.ValidationError('This cruise type is currently unavailable.')
        return ct

    # ------------------------------------------------------------------
    # Cross-field validation
    # ------------------------------------------------------------------

    def validate(self, attrs):
        errors = {}

        # date_to >= date_from
        date_from = attrs.get('date_from')
        date_to = attrs.get('date_to')
        if date_from and date_to and date_to < date_from:
            errors['date_to'] = 'End date must be on or after the start date.'

        # Cruise-specific: cruise_type required
        event_type = attrs.get('event_type')
        if event_type and event_type.slug == 'cruise' and not attrs.get('cruise_type'):
            errors['cruise_type'] = 'Cruise type is required for cruise bookings.'

        # Guest consistency
        adults = attrs.get('adults', 1)
        children = attrs.get('children', 0)
        guests = attrs.get('guests', 0)
        if guests and guests != (adults + children):
            # Auto-correct guests to match adults + children
            attrs['guests'] = adults + children

        # Budget range
        budget_min = attrs.get('budget_min')
        budget_max = attrs.get('budget_max')
        if budget_min is not None and budget_max is not None:
            if budget_max < budget_min:
                errors['budget_max'] = 'Maximum budget must be >= minimum budget.'

        # Accommodation type required if accommodation requested
        if attrs.get('requires_accommodation') and not attrs.get('accommodation_type'):
            errors['accommodation_type'] = (
                'Please select an accommodation type.'
            )

        # Validate service_ids exist
        service_ids = attrs.get('service_ids', [])
        if service_ids:
            existing = set(
                ServiceCatalog.objects.filter(
                    id__in=service_ids, is_active=True,
                ).values_list('id', flat=True)
            )
            invalid = set(service_ids) - existing
            if invalid:
                errors['service_ids'] = (
                    f'Invalid or inactive service IDs: {sorted(invalid)}'
                )

        if errors:
            raise serializers.ValidationError(errors)

        return attrs

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    def create(self, validated_data):
        service_ids = validated_data.pop('service_ids', [])

        # Auto-set guests = adults + children
        validated_data['guests'] = (
            validated_data.get('adults', 1) + validated_data.get('children', 0)
        )

        booking = super().create(validated_data)

        # Attach selected services via through table
        if service_ids:
            BookingService.objects.bulk_create([
                BookingService(booking=booking, service_id=sid)
                for sid in service_ids
            ])

        return booking


class PersonalisedBookingUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a personalised booking (user-facing).

    Users can update details while status is pending/quoted.
    """

    cruise_type = serializers.CharField(
        required=False, allow_blank=True, default='',
    )
    service_ids = serializers.ListField(
        child=serializers.IntegerField(), required=False, write_only=True,
    )

    class Meta:
        model = PersonalisedBooking
        fields = [
            'event_name',
            'date_from', 'date_to', 'duration_hours', 'duration_days',
            'cruise_type',
            'continent', 'country', 'state', 'preferred_destination',
            'guests', 'adults', 'children',
            'catering', 'bar_attendance', 'decoration',
            'special_security', 'photography', 'entertainment',
            'service_ids',
            'budget_min', 'budget_max',
            'requires_accommodation', 'accommodation_type',
            'additional_comments', 'special_requests',
        ]

    def validate_cruise_type(self, value):
        if not value:
            return None
        try:
            ct = CruiseType.objects.get(slug=value)
        except CruiseType.DoesNotExist:
            raise serializers.ValidationError(f'Unknown cruise type: {value}')
        if not ct.is_active:
            raise serializers.ValidationError('This cruise type is currently unavailable.')
        return ct

    def validate(self, attrs):
        instance = self.instance
        if instance and instance.status not in ('pending', 'quoted'):
            raise serializers.ValidationError(
                'Booking can only be modified while in pending or quoted status.'
            )

        date_from = attrs.get('date_from', instance.date_from if instance else None)
        date_to = attrs.get('date_to', instance.date_to if instance else None)
        if date_from and date_to and date_to < date_from:
            raise serializers.ValidationError(
                {'date_to': 'End date must be on or after the start date.'}
            )

        budget_min = attrs.get('budget_min', getattr(instance, 'budget_min', None))
        budget_max = attrs.get('budget_max', getattr(instance, 'budget_max', None))
        if budget_min is not None and budget_max is not None and budget_max < budget_min:
            raise serializers.ValidationError(
                {'budget_max': 'Maximum budget must be >= minimum budget.'}
            )

        # Validate service_ids
        service_ids = attrs.get('service_ids', [])
        if service_ids:
            existing = set(
                ServiceCatalog.objects.filter(
                    id__in=service_ids, is_active=True,
                ).values_list('id', flat=True)
            )
            invalid = set(service_ids) - existing
            if invalid:
                raise serializers.ValidationError(
                    {'service_ids': f'Invalid or inactive service IDs: {sorted(invalid)}'}
                )

        return attrs

    def update(self, instance, validated_data):
        service_ids = validated_data.pop('service_ids', None)

        # Auto-correct guests
        adults = validated_data.get('adults', instance.adults)
        children = validated_data.get('children', instance.children)
        validated_data['guests'] = adults + children

        instance = super().update(instance, validated_data)

        # Replace services if provided
        if service_ids is not None:
            instance.booking_services.all().delete()
            BookingService.objects.bulk_create([
                BookingService(booking=instance, service_id=sid)
                for sid in service_ids
            ])

        return instance


class PersonalisedBookingAdminSerializer(serializers.ModelSerializer):
    """Serializer for admin-only fields (status, quote, notes, assignment)."""

    class Meta:
        model = PersonalisedBooking
        fields = [
            'status', 'admin_notes', 'assigned_to',
            'quote_amount', 'quote_expires_at',
            'deposit_amount', 'rejection_reason',
        ]

    def validate_status(self, value):
        instance = self.instance
        if instance and not instance.can_transition_to(value):
            allowed = instance.ALLOWED_STATUS_TRANSITIONS.get(instance.status, [])
            raise serializers.ValidationError(
                f"Cannot transition from '{instance.status}' to '{value}'. "
                f"Allowed: {allowed}"
            )
        return value

    def validate(self, attrs):
        new_status = attrs.get('status')
        if new_status == 'rejected' and not attrs.get('rejection_reason'):
            if self.instance and not self.instance.rejection_reason:
                raise serializers.ValidationError(
                    {'rejection_reason': 'A reason is required when rejecting a booking.'}
                )
        if new_status == 'quoted':
            if not attrs.get('quote_amount') and (
                not self.instance or self.instance.quote_amount is None
            ):
                raise serializers.ValidationError(
                    {'quote_amount': 'A quote amount is required when setting status to quoted.'}
                )
        return attrs


# ---------------------------------------------------------------------------
# Quotation Serializers
# ---------------------------------------------------------------------------

class QuotationLineItemSerializer(serializers.ModelSerializer):
    """Read/write serializer for quotation line items."""

    service_name = serializers.CharField(source='service.name', read_only=True, default=None)

    class Meta:
        model = QuotationLineItem
        fields = [
            'id', 'service', 'service_name', 'description',
            'quantity', 'unit_price', 'total', 'position',
        ]
        read_only_fields = ['id', 'total']


class QuotationSerializer(serializers.ModelSerializer):
    """Full read serializer for quotations with nested line items."""

    line_items = QuotationLineItemSerializer(many=True, read_only=True)
    created_by_email = serializers.EmailField(
        source='created_by.email', read_only=True, default=None,
    )
    balance_from_accepted = serializers.SerializerMethodField()

    class Meta:
        model = Quotation
        fields = [
            'id', 'quotation_number', 'booking', 'version', 'status',
            'subtotal', 'tax_rate', 'tax_amount',
            'discount_amount', 'discount_reason', 'total',
            'notes', 'payment_terms', 'valid_until',
            'revision_reason', 'previous_version',
            'accepted_at', 'rejected_at', 'rejection_reason',
            'created_by', 'created_by_email',
            'line_items', 'balance_from_accepted',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'quotation_number', 'version', 'subtotal',
            'tax_amount', 'total', 'accepted_at', 'rejected_at',
            'created_by', 'created_by_email',
            'created_at', 'updated_at',
        ]

    def get_balance_from_accepted(self, obj):
        if obj.status != 'accepted':
            return None
        paid = obj.invoices.filter(
            status__in=['paid', 'partially_paid'],
        ).aggregate(total_paid=models.Sum('amount_paid'))['total_paid'] or 0
        return str(obj.total - paid)


class QuotationCreateSerializer(serializers.Serializer):
    """Serializer for creating a new quotation (admin-only).

    Accepts line items inline so the admin can build the full quote
    in one request.
    """

    tax_rate = serializers.DecimalField(max_digits=5, decimal_places=2, default=0)
    discount_amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, default=0,
    )
    discount_reason = serializers.CharField(required=False, default='')
    notes = serializers.CharField(required=False, default='')
    payment_terms = serializers.CharField(required=False, default='')
    valid_until = serializers.DateTimeField(required=False, allow_null=True)
    revision_reason = serializers.CharField(required=False, default='')
    line_items = QuotationLineItemSerializer(many=True)

    def validate_line_items(self, value):
        if not value:
            raise serializers.ValidationError('At least one line item is required.')
        return value


class QuotationActionSerializer(serializers.Serializer):
    """Serializer for accepting/rejecting a quotation."""

    action = serializers.ChoiceField(choices=['accept', 'reject'])
    reason = serializers.CharField(required=False, default='')


# ---------------------------------------------------------------------------
# Personalised Booking Invoice Serializers
# ---------------------------------------------------------------------------

class PersonalisedBookingInvoiceSerializer(serializers.ModelSerializer):
    """Full read serializer for personalised booking invoices."""

    created_by_email = serializers.EmailField(
        source='created_by.email', read_only=True, default=None,
    )
    balance_due = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True,
    )
    is_fully_paid = serializers.BooleanField(read_only=True)
    payments = serializers.SerializerMethodField()

    class Meta:
        model = PersonalisedBookingInvoice
        fields = [
            'id', 'invoice_number', 'booking', 'quotation', 'status',
            'subtotal', 'tax_rate', 'tax_amount',
            'discount_amount', 'total', 'amount_paid',
            'balance_due', 'is_fully_paid',
            'due_date', 'paid_at',
            'adjustment_reason', 'original_total',
            'cancellation_reason', 'cancelled_at',
            'notes',
            'created_by', 'created_by_email',
            'payments',
            'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'invoice_number', 'amount_paid', 'paid_at',
            'created_by', 'created_by_email',
            'created_at', 'updated_at',
        ]

    def get_payments(self, obj):
        return PersonalisedBookingPaymentSerializer(
            obj.payments.all(), many=True,
        ).data


class InvoiceCreateFromQuotationSerializer(serializers.Serializer):
    """Create an invoice from an accepted quotation."""

    quotation_id = serializers.IntegerField()
    due_date = serializers.DateField()
    notes = serializers.CharField(required=False, default='')


class InvoiceAdjustSerializer(serializers.Serializer):
    """Adjust an existing invoice total."""

    new_total = serializers.DecimalField(max_digits=12, decimal_places=2)
    reason = serializers.CharField()


class InvoiceCancelSerializer(serializers.Serializer):
    """Cancel an invoice."""

    reason = serializers.CharField()


# ---------------------------------------------------------------------------
# Payment Serializers
# ---------------------------------------------------------------------------

class PersonalisedBookingPaymentSerializer(serializers.ModelSerializer):
    """Read serializer for booking payments."""

    class Meta:
        model = PersonalisedBookingPayment
        fields = [
            'id', 'payment_id', 'invoice', 'payment_type', 'payment_method',
            'amount', 'status',
            'stripe_session_id', 'stripe_payment_intent_id',
            'wallet_transaction_id', 'transaction_reference',
            'notes', 'completed_at', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'payment_id', 'status', 'completed_at',
            'stripe_session_id', 'stripe_payment_intent_id',
            'wallet_transaction_id',
            'created_at', 'updated_at',
        ]


class MakePaymentSerializer(serializers.Serializer):
    """Serializer for initiating a payment on an invoice."""

    invoice_id = serializers.IntegerField()
    payment_type = serializers.ChoiceField(
        choices=['deposit', 'installment', 'final_balance', 'full_payment'],
    )
    payment_method = serializers.ChoiceField(choices=['stripe', 'wallet'])
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)


# ---------------------------------------------------------------------------
# Payment Schedule Serializers
# ---------------------------------------------------------------------------

class PaymentScheduleSerializer(serializers.ModelSerializer):
    """Read serializer for payment schedule milestones."""

    class Meta:
        model = PaymentSchedule
        fields = [
            'id', 'booking', 'invoice', 'milestone_name',
            'amount', 'due_date', 'status', 'payment',
            'paid_at', 'position', 'created_at',
        ]
        read_only_fields = ['id', 'payment', 'paid_at', 'created_at']


class PaymentScheduleCreateSerializer(serializers.Serializer):
    """Create a payment schedule with multiple milestones."""

    milestones = serializers.ListField(
        child=serializers.DictField(), min_length=1,
        help_text='List of {milestone_name, amount, due_date}',
    )

    def validate_milestones(self, value):
        for i, m in enumerate(value):
            if not m.get('milestone_name'):
                raise serializers.ValidationError(
                    f'Milestone {i+1}: milestone_name is required.'
                )
            if not m.get('amount'):
                raise serializers.ValidationError(
                    f'Milestone {i+1}: amount is required.'
                )
            if not m.get('due_date'):
                raise serializers.ValidationError(
                    f'Milestone {i+1}: due_date is required.'
                )
        return value


# ---------------------------------------------------------------------------
# Audit Trail Serializer
# ---------------------------------------------------------------------------

class BookingActivityLogSerializer(serializers.ModelSerializer):
    """Read-only serializer for booking activity log entries."""

    actor_email = serializers.EmailField(
        source='actor.email', read_only=True, default=None,
    )
    actor_name = serializers.SerializerMethodField()

    class Meta:
        model = BookingActivityLog
        fields = [
            'id', 'action', 'actor', 'actor_email', 'actor_name',
            'description', 'old_value', 'new_value', 'metadata',
            'created_at',
        ]
        read_only_fields = fields

    def get_actor_name(self, obj):
        if obj.actor:
            return f"{obj.actor.firstname} {obj.actor.lastname}"
        return 'System'


# ---------------------------------------------------------------------------
# Carousel Serializers
# ---------------------------------------------------------------------------

class CarouselSerializer(serializers.ModelSerializer):
    """Serializer for carousel items."""

    class Meta:
        model = Carousel
        fields = [
            'id', 'title', 'subtitle', 'image', 'cta_text',
            'category', 'is_active', 'position',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
