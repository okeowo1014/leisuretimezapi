import uuid

from django.db.models import Q
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from admin_api.permissions import IsAdminStaff
from admin_api.serializers.quotations import (
    AdminQuotationCreateSerializer, AdminQuotationDetailSerializer,
    AdminQuotationListSerializer, AdminQuotationUpdateSerializer,
)
from index.models import (
    BookingActivityLog, PersonalisedBooking, Quotation, QuotationLineItem,
)


def _next_quotation_number(booking, version):
    seq = Quotation.objects.count() + 1
    return f"QTN-{str(seq).zfill(6)}-v{version}"


class AdminQuotationListView(generics.ListAPIView):
    permission_classes = [IsAdminStaff]
    serializer_class = AdminQuotationListSerializer

    def get_queryset(self):
        qs = Quotation.objects.select_related(
            'booking__user', 'booking__event_type',
        ).order_by('-created_at')

        q_status = self.request.query_params.get('status')
        if q_status:
            qs = qs.filter(status=q_status)

        booking_id = self.request.query_params.get('booking')
        if booking_id:
            qs = qs.filter(booking_id=booking_id)

        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(
                Q(quotation_number__icontains=search) |
                Q(booking__user__email__icontains=search)
            )

        return qs


class AdminQuotationDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAdminStaff]
    serializer_class = AdminQuotationDetailSerializer
    queryset = Quotation.objects.select_related(
        'booking__user', 'created_by',
    ).prefetch_related('line_items__service')


class AdminQuotationCreateView(APIView):
    permission_classes = [IsAdminStaff]

    def post(self, request):
        serializer = AdminQuotationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            booking = PersonalisedBooking.objects.get(pk=data['booking_id'])
        except PersonalisedBooking.DoesNotExist:
            return Response(
                {'error': 'Booking not found'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Determine version
        latest = Quotation.objects.filter(booking=booking).order_by('-version').first()
        version = (latest.version + 1) if latest else 1

        quotation = Quotation.objects.create(
            quotation_number=_next_quotation_number(booking, version),
            booking=booking,
            version=version,
            status='draft',
            tax_rate=data.get('tax_rate', 0),
            discount_amount=data.get('discount_amount', 0),
            discount_reason=data.get('discount_reason', ''),
            notes=data.get('notes', ''),
            payment_terms=data.get('payment_terms', ''),
            valid_until=data.get('valid_until'),
            created_by=request.user,
        )

        # Create line items
        for idx, item in enumerate(data.get('line_items', [])):
            QuotationLineItem.objects.create(
                quotation=quotation,
                service_id=item.get('service'),
                description=item['description'],
                quantity=item.get('quantity', 1),
                unit_price=item['unit_price'],
                total=item['unit_price'] * item.get('quantity', 1),
                position=idx,
            )

        quotation.recalculate_totals()

        BookingActivityLog.objects.create(
            booking=booking,
            action='quote_created',
            actor=request.user,
            description=f'Quotation {quotation.quotation_number} created (v{version})',
            new_value=str(quotation.total),
            metadata={'quotation_id': quotation.id},
        )

        return Response(
            AdminQuotationDetailSerializer(quotation).data,
            status=status.HTTP_201_CREATED,
        )


class AdminQuotationUpdateView(APIView):
    permission_classes = [IsAdminStaff]

    def patch(self, request, pk):
        try:
            quotation = Quotation.objects.get(pk=pk)
        except Quotation.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        if quotation.status != 'draft':
            return Response(
                {'error': 'Only draft quotations can be edited.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = AdminQuotationUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        for field in ('tax_rate', 'discount_amount', 'discount_reason', 'notes',
                      'payment_terms', 'valid_until'):
            if field in data:
                setattr(quotation, field, data[field])
        quotation.save()

        # Replace line items if provided
        if 'line_items' in data:
            quotation.line_items.all().delete()
            for idx, item in enumerate(data['line_items']):
                QuotationLineItem.objects.create(
                    quotation=quotation,
                    service_id=item.get('service'),
                    description=item['description'],
                    quantity=item.get('quantity', 1),
                    unit_price=item['unit_price'],
                    total=item['unit_price'] * item.get('quantity', 1),
                    position=idx,
                )
            quotation.recalculate_totals()

        return Response(AdminQuotationDetailSerializer(quotation).data)


class AdminQuotationSendView(APIView):
    permission_classes = [IsAdminStaff]

    def post(self, request, pk):
        try:
            quotation = Quotation.objects.get(pk=pk)
        except Quotation.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        if quotation.status not in ('draft',):
            return Response(
                {'error': 'Only draft quotations can be sent.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        quotation.status = 'sent'
        quotation.save(update_fields=['status', 'updated_at'])

        # Transition booking to quoted if still pending
        booking = quotation.booking
        if booking.can_transition_to('quoted'):
            old_status = booking.status
            booking.transition_to('quoted')
            BookingActivityLog.objects.create(
                booking=booking,
                action='status_changed',
                actor=request.user,
                description=f'Status changed to quoted (quotation sent)',
                old_value=old_status,
                new_value='quoted',
            )

        return Response({'detail': f'Quotation {quotation.quotation_number} sent.'})


class AdminQuotationReviseView(APIView):
    permission_classes = [IsAdminStaff]

    def post(self, request, pk):
        try:
            old_quotation = Quotation.objects.get(pk=pk)
        except Quotation.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        if old_quotation.status in ('draft', 'accepted'):
            return Response(
                {'error': 'Cannot revise a draft or already accepted quotation.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Supersede old
        old_quotation.status = 'superseded'
        old_quotation.save(update_fields=['status', 'updated_at'])

        # Create new version
        new_version = old_quotation.version + 1
        new_quotation = Quotation.objects.create(
            quotation_number=_next_quotation_number(old_quotation.booking, new_version),
            booking=old_quotation.booking,
            version=new_version,
            status='draft',
            tax_rate=old_quotation.tax_rate,
            discount_amount=old_quotation.discount_amount,
            discount_reason=old_quotation.discount_reason,
            notes=old_quotation.notes,
            payment_terms=old_quotation.payment_terms,
            valid_until=old_quotation.valid_until,
            previous_version=old_quotation,
            revision_reason=request.data.get('revision_reason', ''),
            created_by=request.user,
        )

        # Copy line items
        for item in old_quotation.line_items.all():
            QuotationLineItem.objects.create(
                quotation=new_quotation,
                service=item.service,
                description=item.description,
                quantity=item.quantity,
                unit_price=item.unit_price,
                total=item.total,
                position=item.position,
            )
        new_quotation.recalculate_totals()

        BookingActivityLog.objects.create(
            booking=old_quotation.booking,
            action='quote_revised',
            actor=request.user,
            description=f'Quotation revised: {old_quotation.quotation_number} → {new_quotation.quotation_number}',
            old_value=old_quotation.quotation_number,
            new_value=new_quotation.quotation_number,
            metadata={'old_quotation_id': old_quotation.id, 'new_quotation_id': new_quotation.id},
        )

        return Response(
            AdminQuotationDetailSerializer(new_quotation).data,
            status=status.HTTP_201_CREATED,
        )
