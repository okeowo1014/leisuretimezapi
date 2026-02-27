from rest_framework import serializers

from index.models import (
    BookingActivityLog, BookingService, PersonalisedBooking,
    PersonalisedBookingAttachment, PersonalisedBookingMessage,
)


class AdminBookingServiceSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source='service.name', read_only=True)
    line_total = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True,
    )

    class Meta:
        model = BookingService
        fields = (
            'id', 'service', 'service_name', 'quantity',
            'unit_price', 'notes', 'line_total', 'created_at',
        )


class AdminPBMessageSerializer(serializers.ModelSerializer):
    sender_email = serializers.CharField(source='sender.email', read_only=True)
    sender_name = serializers.SerializerMethodField()

    class Meta:
        model = PersonalisedBookingMessage
        fields = ('id', 'sender', 'sender_email', 'sender_name', 'message', 'created_at')

    def get_sender_name(self, obj):
        return f"{obj.sender.firstname} {obj.sender.lastname}"


class AdminPBAttachmentSerializer(serializers.ModelSerializer):
    uploaded_by_email = serializers.CharField(source='uploaded_by.email', read_only=True)

    class Meta:
        model = PersonalisedBookingAttachment
        fields = (
            'id', 'uploaded_by', 'uploaded_by_email', 'file', 'category',
            'description', 'created_at',
        )


class AdminPBListSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_name = serializers.SerializerMethodField()
    event_type_name = serializers.CharField(source='event_type.name', read_only=True)
    assigned_to_email = serializers.CharField(
        source='assigned_to.email', read_only=True, default=None,
    )

    class Meta:
        model = PersonalisedBooking
        fields = (
            'id', 'user_email', 'user_name', 'event_type', 'event_type_name',
            'event_name', 'date_from', 'date_to', 'country', 'guests',
            'adults', 'children', 'budget_min', 'budget_max', 'quote_amount',
            'status', 'assigned_to', 'assigned_to_email', 'created_at',
        )

    def get_user_name(self, obj):
        return f"{obj.user.firstname} {obj.user.lastname}"


class AdminPBDetailSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_name = serializers.SerializerMethodField()
    event_type_name = serializers.CharField(source='event_type.name', read_only=True)
    cruise_type_name = serializers.CharField(
        source='cruise_type.name', read_only=True, default=None,
    )
    assigned_to_email = serializers.CharField(
        source='assigned_to.email', read_only=True, default=None,
    )
    booking_services = AdminBookingServiceSerializer(many=True, read_only=True)
    messages = AdminPBMessageSerializer(many=True, read_only=True)
    attachments = AdminPBAttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = PersonalisedBooking
        fields = '__all__'

    def get_user_name(self, obj):
        return f"{obj.user.firstname} {obj.user.lastname}"


class AdminPBUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PersonalisedBooking
        fields = (
            'admin_notes', 'quote_amount', 'quote_expires_at',
            'deposit_amount', 'rejection_reason', 'cancellation_reason',
        )


class AdminPBTransitionSerializer(serializers.Serializer):
    new_status = serializers.ChoiceField(
        choices=PersonalisedBooking.STATUS_CHOICES,
    )
    reason = serializers.CharField(required=False, default='')


class AdminPBAssignSerializer(serializers.Serializer):
    assigned_to = serializers.IntegerField(help_text='Staff user ID to assign')


class AdminPBMessageCreateSerializer(serializers.Serializer):
    message = serializers.CharField()
