import uuid
from datetime import datetime

from django.db.models import Q
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from admin_api.permissions import IsAdminStaff
from admin_api.serializers.payments import (
    AdminLegacyPaymentSerializer, AdminPaymentScheduleCreateSerializer,
    AdminPaymentScheduleSerializer, AdminPBPaymentSerializer,
    AdminRecordPaymentSerializer,
)
from index.models import (
    BookingActivityLog, Payment, PaymentSchedule, PersonalisedBooking,
    PersonalisedBookingInvoice, PersonalisedBookingPayment,
)


# ---------------------------------------------------------------------------
# Legacy Payments (from Payment model)
# ---------------------------------------------------------------------------

class AdminLegacyPaymentListView(generics.ListAPIView):
    permission_classes = [IsAdminStaff]
    serializer_class = AdminLegacyPaymentSerializer

    def get_queryset(self):
        qs = Payment.objects.select_related('invoice').order_by('-created_at')

        pay_status = self.request.query_params.get('status')
        if pay_status:
            qs = qs.filter(status=pay_status)

        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(
                Q(payment_id__icontains=search) |
                Q(transaction_id__icontains=search)
            )

        return qs


class AdminLegacyPaymentDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAdminStaff]
    serializer_class = AdminLegacyPaymentSerializer
    queryset = Payment.objects.select_related('invoice')


# ---------------------------------------------------------------------------
# Personalised Booking Payments
# ---------------------------------------------------------------------------

class AdminPBPaymentListView(generics.ListAPIView):
    permission_classes = [IsAdminStaff]
    serializer_class = AdminPBPaymentSerializer

    def get_queryset(self):
        qs = PersonalisedBookingPayment.objects.select_related(
            'invoice__booking',
        ).order_by('-created_at')

        pay_status = self.request.query_params.get('status')
        if pay_status:
            qs = qs.filter(status=pay_status)

        payment_method = self.request.query_params.get('payment_method')
        if payment_method:
            qs = qs.filter(payment_method=payment_method)

        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(
                Q(payment_id__icontains=search) |
                Q(transaction_reference__icontains=search)
            )

        return qs


class AdminPBPaymentDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAdminStaff]
    serializer_class = AdminPBPaymentSerializer
    queryset = PersonalisedBookingPayment.objects.select_related('invoice__booking')


class AdminRecordPaymentView(APIView):
    """Manually record a payment (e.g., bank transfer)."""
    permission_classes = [IsAdminStaff]

    def post(self, request):
        serializer = AdminRecordPaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            invoice = PersonalisedBookingInvoice.objects.get(pk=data['invoice_id'])
        except PersonalisedBookingInvoice.DoesNotExist:
            return Response(
                {'error': 'Invoice not found'},
                status=status.HTTP_404_NOT_FOUND,
            )

        payment = PersonalisedBookingPayment.objects.create(
            payment_id=f"PBP-{uuid.uuid4().hex[:8].upper()}",
            invoice=invoice,
            payment_type=data['payment_type'],
            payment_method=data['payment_method'],
            amount=data['amount'],
            status='completed',
            transaction_reference=data.get('transaction_reference', ''),
            notes=data.get('notes', ''),
            completed_at=timezone.now(),
        )

        # Update invoice amount_paid
        invoice.amount_paid += data['amount']
        if invoice.is_fully_paid:
            invoice.status = 'paid'
            invoice.paid_at = timezone.now()
        elif invoice.amount_paid > 0:
            invoice.status = 'partially_paid'
        invoice.save()

        BookingActivityLog.objects.create(
            booking=invoice.booking,
            action='payment_received',
            actor=request.user,
            description=f'Payment {payment.payment_id} recorded: {data["amount"]} via {data["payment_method"]}',
            new_value=str(data['amount']),
            metadata={
                'invoice_id': invoice.id,
                'payment_id': payment.id,
            },
        )

        return Response(
            AdminPBPaymentSerializer(payment).data,
            status=status.HTTP_201_CREATED,
        )


# ---------------------------------------------------------------------------
# Payment Schedules
# ---------------------------------------------------------------------------

class AdminPaymentScheduleListView(generics.ListAPIView):
    permission_classes = [IsAdminStaff]
    serializer_class = AdminPaymentScheduleSerializer

    def get_queryset(self):
        qs = PaymentSchedule.objects.select_related(
            'booking', 'invoice', 'payment',
        ).order_by('position', 'due_date')

        booking_id = self.request.query_params.get('booking')
        if booking_id:
            qs = qs.filter(booking_id=booking_id)

        schedule_status = self.request.query_params.get('status')
        if schedule_status:
            qs = qs.filter(status=schedule_status)

        return qs


class AdminPaymentScheduleCreateView(APIView):
    permission_classes = [IsAdminStaff]

    def post(self, request):
        serializer = AdminPaymentScheduleCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            booking = PersonalisedBooking.objects.get(pk=data['booking_id'])
        except PersonalisedBooking.DoesNotExist:
            return Response(
                {'error': 'Booking not found'},
                status=status.HTTP_404_NOT_FOUND,
            )

        invoice = None
        if data.get('invoice_id'):
            try:
                invoice = PersonalisedBookingInvoice.objects.get(pk=data['invoice_id'])
            except PersonalisedBookingInvoice.DoesNotExist:
                return Response(
                    {'error': 'Invoice not found'},
                    status=status.HTTP_404_NOT_FOUND,
                )

        created = []
        for idx, milestone in enumerate(data['milestones']):
            item = PaymentSchedule.objects.create(
                booking=booking,
                invoice=invoice,
                milestone_name=milestone['milestone_name'],
                amount=milestone['amount'],
                due_date=milestone['due_date'],
                position=idx,
            )
            created.append(item)

        return Response(
            AdminPaymentScheduleSerializer(created, many=True).data,
            status=status.HTTP_201_CREATED,
        )


class AdminPaymentScheduleUpdateView(APIView):
    permission_classes = [IsAdminStaff]

    def patch(self, request, pk):
        try:
            schedule = PaymentSchedule.objects.get(pk=pk)
        except PaymentSchedule.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        for field in ('milestone_name', 'amount', 'due_date', 'status'):
            if field in request.data:
                setattr(schedule, field, request.data[field])
        schedule.save()

        return Response(AdminPaymentScheduleSerializer(schedule).data)
