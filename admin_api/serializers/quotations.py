from rest_framework import serializers

from index.models import Quotation, QuotationLineItem


class AdminQuotationLineItemSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source='service.name', read_only=True, default=None)

    class Meta:
        model = QuotationLineItem
        fields = (
            'id', 'service', 'service_name', 'description',
            'quantity', 'unit_price', 'total', 'position',
        )
        read_only_fields = ('total',)


class AdminQuotationListSerializer(serializers.ModelSerializer):
    booking_user_email = serializers.CharField(
        source='booking.user.email', read_only=True,
    )
    event_type_name = serializers.CharField(
        source='booking.event_type.name', read_only=True,
    )

    class Meta:
        model = Quotation
        fields = (
            'id', 'quotation_number', 'booking', 'booking_user_email',
            'event_type_name', 'version', 'status', 'subtotal',
            'tax_amount', 'discount_amount', 'total', 'valid_until',
            'created_at',
        )


class AdminQuotationDetailSerializer(serializers.ModelSerializer):
    line_items = AdminQuotationLineItemSerializer(many=True, read_only=True)
    booking_user_email = serializers.CharField(
        source='booking.user.email', read_only=True,
    )
    created_by_email = serializers.CharField(
        source='created_by.email', read_only=True, default=None,
    )

    class Meta:
        model = Quotation
        fields = '__all__'


class AdminQuotationCreateSerializer(serializers.Serializer):
    booking_id = serializers.IntegerField()
    tax_rate = serializers.DecimalField(
        max_digits=5, decimal_places=2, default=0,
    )
    discount_amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, default=0,
    )
    discount_reason = serializers.CharField(required=False, default='')
    notes = serializers.CharField(required=False, default='')
    payment_terms = serializers.CharField(required=False, default='')
    valid_until = serializers.DateTimeField(required=False, allow_null=True, default=None)
    line_items = AdminQuotationLineItemSerializer(many=True)


class AdminQuotationUpdateSerializer(serializers.Serializer):
    tax_rate = serializers.DecimalField(
        max_digits=5, decimal_places=2, required=False,
    )
    discount_amount = serializers.DecimalField(
        max_digits=12, decimal_places=2, required=False,
    )
    discount_reason = serializers.CharField(required=False)
    notes = serializers.CharField(required=False)
    payment_terms = serializers.CharField(required=False)
    valid_until = serializers.DateTimeField(required=False, allow_null=True)
    line_items = AdminQuotationLineItemSerializer(many=True, required=False)
