from rest_framework import serializers

from index.models import Payment, PaymentSchedule, PersonalisedBookingPayment


class AdminLegacyPaymentSerializer(serializers.ModelSerializer):
    invoice_id_str = serializers.CharField(source='invoice.invoice_id', read_only=True)

    class Meta:
        model = Payment
        fields = (
            'id', 'payment_id', 'invoice', 'invoice_id_str',
            'transaction_id', 'status', 'amount', 'admin_fee',
            'vat', 'total', 'paid', 'created_at', 'updated_at',
        )


class AdminPBPaymentSerializer(serializers.ModelSerializer):
    invoice_number = serializers.CharField(
        source='invoice.invoice_number', read_only=True,
    )
    booking_id = serializers.IntegerField(
        source='invoice.booking_id', read_only=True,
    )

    class Meta:
        model = PersonalisedBookingPayment
        fields = (
            'id', 'payment_id', 'invoice', 'invoice_number', 'booking_id',
            'payment_type', 'payment_method', 'amount', 'status',
            'stripe_session_id', 'stripe_payment_intent_id',
            'wallet_transaction_id', 'transaction_reference',
            'notes', 'completed_at', 'created_at',
        )


class AdminRecordPaymentSerializer(serializers.Serializer):
    invoice_id = serializers.IntegerField(
        help_text='PersonalisedBookingInvoice PK',
    )
    payment_type = serializers.ChoiceField(
        choices=['deposit', 'installment', 'final_balance', 'full_payment'],
    )
    payment_method = serializers.ChoiceField(
        choices=['stripe', 'wallet', 'bank_transfer', 'split'],
    )
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    transaction_reference = serializers.CharField(required=False, default='')
    notes = serializers.CharField(required=False, default='')


class AdminPaymentScheduleSerializer(serializers.ModelSerializer):
    payment_id_str = serializers.CharField(
        source='payment.payment_id', read_only=True, default=None,
    )

    class Meta:
        model = PaymentSchedule
        fields = (
            'id', 'booking', 'invoice', 'milestone_name', 'amount',
            'due_date', 'status', 'payment', 'payment_id_str',
            'paid_at', 'position', 'created_at',
        )


class AdminPaymentScheduleCreateSerializer(serializers.Serializer):
    booking_id = serializers.IntegerField()
    invoice_id = serializers.IntegerField(required=False, allow_null=True)
    milestones = serializers.ListField(
        child=serializers.DictField(),
        help_text='List of {milestone_name, amount, due_date}',
    )
