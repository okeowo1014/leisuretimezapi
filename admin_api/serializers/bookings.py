from rest_framework import serializers

from index.models import Booking, BookingActivityLog, Invoice, Payment


class AdminBookingListSerializer(serializers.ModelSerializer):
    customer_email = serializers.CharField(source='customer.user.email', read_only=True)
    customer_name = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = (
            'id', 'booking_id', 'package', 'customer_email', 'customer_name',
            'purpose', 'datefrom', 'dateto', 'continent', 'travelcountry',
            'guests', 'adult', 'children', 'price', 'discount_amount',
            'status', 'payment_status', 'payment_method',
            'invoiced', 'created_at', 'updated_at',
        )

    def get_customer_name(self, obj):
        return f"{obj.firstname} {obj.lastname}"


class AdminInvoiceInlineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = (
            'id', 'invoice_id', 'status', 'subtotal', 'tax', 'tax_amount',
            'admin_percentage', 'admin_fee', 'total', 'paid',
            'transaction_id', 'created_at',
        )


class AdminPaymentInlineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = (
            'id', 'payment_id', 'transaction_id', 'status', 'amount',
            'admin_fee', 'vat', 'total', 'paid', 'created_at',
        )


class AdminBookingDetailSerializer(serializers.ModelSerializer):
    customer_email = serializers.CharField(source='customer.user.email', read_only=True)
    invoices = serializers.SerializerMethodField()
    payments = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = '__all__'

    def get_invoices(self, obj):
        invoices = Invoice.objects.filter(booking=obj)
        return AdminInvoiceInlineSerializer(invoices, many=True).data

    def get_payments(self, obj):
        invoices = Invoice.objects.filter(booking=obj)
        payments = Payment.objects.filter(invoice__in=invoices)
        return AdminPaymentInlineSerializer(payments, many=True).data


class AdminBookingUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ('status', 'payment_status', 'comment')


class AdminBookingCancelSerializer(serializers.Serializer):
    cancellation_reason = serializers.CharField(required=True)
    refund_amount = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False, default=0,
    )
    refund_to_wallet = serializers.BooleanField(required=False, default=False)


class AdminBookingActivityLogSerializer(serializers.ModelSerializer):
    actor_email = serializers.CharField(source='actor.email', read_only=True, default='system')

    class Meta:
        model = BookingActivityLog
        fields = (
            'id', 'action', 'actor_email', 'description',
            'old_value', 'new_value', 'metadata', 'created_at',
        )
