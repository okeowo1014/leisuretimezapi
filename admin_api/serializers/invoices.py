from rest_framework import serializers

from index.models import Invoice, PersonalisedBookingInvoice, PersonalisedBookingPayment


class AdminLegacyInvoiceSerializer(serializers.ModelSerializer):
    booking_id_str = serializers.CharField(source='booking.booking_id', read_only=True)
    customer_email = serializers.CharField(source='booking.email', read_only=True)

    class Meta:
        model = Invoice
        fields = (
            'id', 'invoice_id', 'booking', 'booking_id_str', 'customer_email',
            'status', 'items', 'subtotal', 'tax', 'tax_amount',
            'admin_percentage', 'admin_fee', 'total', 'paid',
            'transaction_id', 'created_at', 'updated_at',
        )


class AdminPBInvoicePaymentInlineSerializer(serializers.ModelSerializer):
    class Meta:
        model = PersonalisedBookingPayment
        fields = (
            'id', 'payment_id', 'payment_type', 'payment_method',
            'amount', 'status', 'completed_at', 'created_at',
        )


class AdminPBInvoiceListSerializer(serializers.ModelSerializer):
    booking_user_email = serializers.CharField(
        source='booking.user.email', read_only=True,
    )
    event_type_name = serializers.CharField(
        source='booking.event_type.name', read_only=True,
    )
    balance_due = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True,
    )

    class Meta:
        model = PersonalisedBookingInvoice
        fields = (
            'id', 'invoice_number', 'booking', 'booking_user_email',
            'event_type_name', 'quotation', 'status', 'subtotal',
            'tax_amount', 'discount_amount', 'total', 'amount_paid',
            'balance_due', 'due_date', 'created_at',
        )


class AdminPBInvoiceDetailSerializer(serializers.ModelSerializer):
    booking_user_email = serializers.CharField(
        source='booking.user.email', read_only=True,
    )
    payments = AdminPBInvoicePaymentInlineSerializer(many=True, read_only=True)
    balance_due = serializers.DecimalField(
        max_digits=12, decimal_places=2, read_only=True,
    )
    is_fully_paid = serializers.BooleanField(read_only=True)
    created_by_email = serializers.CharField(
        source='created_by.email', read_only=True, default=None,
    )

    class Meta:
        model = PersonalisedBookingInvoice
        fields = '__all__'


class AdminInvoiceFromQuotationSerializer(serializers.Serializer):
    quotation_id = serializers.IntegerField()
    due_date = serializers.DateField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, default='')


class AdminInvoiceAdjustSerializer(serializers.Serializer):
    new_total = serializers.DecimalField(max_digits=12, decimal_places=2)
    adjustment_reason = serializers.CharField(required=True)


class AdminInvoiceCancelSerializer(serializers.Serializer):
    cancellation_reason = serializers.CharField(required=True)


class AdminInvoiceMarkPaidSerializer(serializers.Serializer):
    payment_method = serializers.ChoiceField(
        choices=['stripe', 'wallet', 'bank_transfer', 'split'],
    )
    transaction_reference = serializers.CharField(required=False, default='')
    notes = serializers.CharField(required=False, default='')
