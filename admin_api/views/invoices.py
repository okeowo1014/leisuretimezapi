import uuid

from django.db.models import Q
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from admin_api.permissions import IsAdminStaff
from admin_api.serializers.invoices import (
    AdminInvoiceAdjustSerializer, AdminInvoiceCancelSerializer,
    AdminInvoiceFromQuotationSerializer, AdminInvoiceMarkPaidSerializer,
    AdminLegacyInvoiceSerializer, AdminPBInvoiceDetailSerializer,
    AdminPBInvoiceListSerializer,
)
from index.models import (
    BookingActivityLog, Invoice, PersonalisedBookingInvoice,
    PersonalisedBookingPayment, Quotation,
)


def _next_pb_invoice_number():
    count = PersonalisedBookingInvoice.objects.count() + 1
    return f"PBI-{str(count).zfill(6)}"


# ---------------------------------------------------------------------------
# Legacy Invoices (from Booking model)
# ---------------------------------------------------------------------------

class AdminLegacyInvoiceListView(generics.ListAPIView):
    permission_classes = [IsAdminStaff]
    serializer_class = AdminLegacyInvoiceSerializer

    def get_queryset(self):
        qs = Invoice.objects.select_related('booking').order_by('-created_at')

        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(
                Q(invoice_id__icontains=search) |
                Q(booking__email__icontains=search)
            )

        inv_status = self.request.query_params.get('status')
        if inv_status:
            qs = qs.filter(status=inv_status)

        return qs


class AdminLegacyInvoiceDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAdminStaff]
    serializer_class = AdminLegacyInvoiceSerializer
    queryset = Invoice.objects.select_related('booking')
    lookup_field = 'invoice_id'


# ---------------------------------------------------------------------------
# Personalised Booking Invoices
# ---------------------------------------------------------------------------

class AdminPBInvoiceListView(generics.ListAPIView):
    permission_classes = [IsAdminStaff]
    serializer_class = AdminPBInvoiceListSerializer

    def get_queryset(self):
        qs = PersonalisedBookingInvoice.objects.select_related(
            'booking__user', 'booking__event_type',
        ).order_by('-created_at')

        inv_status = self.request.query_params.get('status')
        if inv_status:
            qs = qs.filter(status=inv_status)

        booking_id = self.request.query_params.get('booking')
        if booking_id:
            qs = qs.filter(booking_id=booking_id)

        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(
                Q(invoice_number__icontains=search) |
                Q(booking__user__email__icontains=search)
            )

        return qs


class AdminPBInvoiceDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAdminStaff]
    serializer_class = AdminPBInvoiceDetailSerializer
    queryset = PersonalisedBookingInvoice.objects.select_related(
        'booking__user', 'created_by',
    ).prefetch_related('payments')


class AdminInvoiceFromQuotationView(APIView):
    permission_classes = [IsAdminStaff]

    def post(self, request):
        serializer = AdminInvoiceFromQuotationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            quotation = Quotation.objects.get(pk=data['quotation_id'])
        except Quotation.DoesNotExist:
            return Response(
                {'error': 'Quotation not found'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if quotation.status != 'accepted':
            return Response(
                {'error': 'Invoice can only be created from an accepted quotation.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check for existing invoice from same quotation
        if PersonalisedBookingInvoice.objects.filter(quotation=quotation).exists():
            return Response(
                {'error': 'An invoice already exists for this quotation.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        invoice = PersonalisedBookingInvoice.objects.create(
            invoice_number=_next_pb_invoice_number(),
            booking=quotation.booking,
            quotation=quotation,
            status='sent',
            subtotal=quotation.subtotal,
            tax_rate=quotation.tax_rate,
            tax_amount=quotation.tax_amount,
            discount_amount=quotation.discount_amount,
            total=quotation.total,
            due_date=data.get('due_date'),
            notes=data.get('notes', ''),
            created_by=request.user,
        )

        BookingActivityLog.objects.create(
            booking=quotation.booking,
            action='invoice_created',
            actor=request.user,
            description=f'Invoice {invoice.invoice_number} created from quotation {quotation.quotation_number}',
            new_value=str(invoice.total),
            metadata={
                'invoice_id': invoice.id,
                'quotation_id': quotation.id,
            },
        )

        return Response(
            AdminPBInvoiceDetailSerializer(invoice).data,
            status=status.HTTP_201_CREATED,
        )


class AdminPBInvoiceAdjustView(APIView):
    permission_classes = [IsAdminStaff]

    def post(self, request, pk):
        try:
            invoice = PersonalisedBookingInvoice.objects.get(pk=pk)
        except PersonalisedBookingInvoice.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        if invoice.status in ('cancelled', 'refunded'):
            return Response(
                {'error': 'Cannot adjust a cancelled/refunded invoice.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = AdminInvoiceAdjustSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        old_total = invoice.total
        invoice.original_total = old_total
        invoice.total = data['new_total']
        invoice.adjustment_reason = data['adjustment_reason']
        invoice.status = 'adjusted'
        invoice.save()

        BookingActivityLog.objects.create(
            booking=invoice.booking,
            action='invoice_adjusted',
            actor=request.user,
            description=f'Invoice {invoice.invoice_number} adjusted: {old_total} → {data["new_total"]}',
            old_value=str(old_total),
            new_value=str(data['new_total']),
            metadata={'invoice_id': invoice.id},
        )

        return Response(AdminPBInvoiceDetailSerializer(invoice).data)


class AdminPBInvoiceCancelView(APIView):
    permission_classes = [IsAdminStaff]

    def post(self, request, pk):
        try:
            invoice = PersonalisedBookingInvoice.objects.get(pk=pk)
        except PersonalisedBookingInvoice.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        if invoice.status == 'cancelled':
            return Response(
                {'error': 'Invoice is already cancelled.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = AdminInvoiceCancelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        invoice.status = 'cancelled'
        invoice.cancellation_reason = serializer.validated_data['cancellation_reason']
        invoice.cancelled_at = timezone.now()
        invoice.save()

        BookingActivityLog.objects.create(
            booking=invoice.booking,
            action='invoice_cancelled',
            actor=request.user,
            description=f'Invoice {invoice.invoice_number} cancelled',
            metadata={'invoice_id': invoice.id},
        )

        return Response({'detail': f'Invoice {invoice.invoice_number} cancelled.'})


class AdminPBInvoiceMarkPaidView(APIView):
    permission_classes = [IsAdminStaff]

    def post(self, request, pk):
        try:
            invoice = PersonalisedBookingInvoice.objects.get(pk=pk)
        except PersonalisedBookingInvoice.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        if invoice.status in ('paid', 'cancelled', 'refunded'):
            return Response(
                {'error': f'Cannot mark as paid — current status is {invoice.status}.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = AdminInvoiceMarkPaidSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Create payment record
        payment = PersonalisedBookingPayment.objects.create(
            payment_id=f"PBP-{uuid.uuid4().hex[:8].upper()}",
            invoice=invoice,
            payment_type='full_payment',
            payment_method=data['payment_method'],
            amount=invoice.balance_due,
            status='completed',
            transaction_reference=data.get('transaction_reference', ''),
            notes=data.get('notes', ''),
            completed_at=timezone.now(),
        )

        invoice.amount_paid = invoice.total
        invoice.status = 'paid'
        invoice.paid_at = timezone.now()
        invoice.save()

        BookingActivityLog.objects.create(
            booking=invoice.booking,
            action='payment_received',
            actor=request.user,
            description=f'Invoice {invoice.invoice_number} marked as paid',
            new_value=str(invoice.total),
            metadata={
                'invoice_id': invoice.id,
                'payment_id': payment.id,
            },
        )

        return Response(AdminPBInvoiceDetailSerializer(invoice).data)
