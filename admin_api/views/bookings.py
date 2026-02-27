from django.db.models import Q
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from admin_api.permissions import IsAdminStaff
from admin_api.serializers.bookings import (
    AdminBookingActivityLogSerializer, AdminBookingCancelSerializer,
    AdminBookingDetailSerializer, AdminBookingListSerializer,
    AdminBookingUpdateSerializer,
)
from index.models import Booking, BookingActivityLog


class AdminBookingListView(generics.ListAPIView):
    permission_classes = [IsAdminStaff]
    serializer_class = AdminBookingListSerializer

    def get_queryset(self):
        qs = Booking.objects.select_related('customer__user').order_by('-created_at')

        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(
                Q(booking_id__icontains=search) |
                Q(email__icontains=search) |
                Q(firstname__icontains=search) |
                Q(lastname__icontains=search)
            )

        booking_status = self.request.query_params.get('status')
        if booking_status:
            qs = qs.filter(status=booking_status)

        payment_status = self.request.query_params.get('payment_status')
        if payment_status:
            qs = qs.filter(payment_status=payment_status)

        date_from = self.request.query_params.get('date_from')
        if date_from:
            qs = qs.filter(created_at__date__gte=date_from)

        date_to = self.request.query_params.get('date_to')
        if date_to:
            qs = qs.filter(created_at__date__lte=date_to)

        package = self.request.query_params.get('package')
        if package:
            qs = qs.filter(package__icontains=package)

        return qs


class AdminBookingDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAdminStaff]
    queryset = Booking.objects.select_related('customer__user')
    lookup_field = 'booking_id'

    def get_serializer_class(self):
        if self.request.method in ('PATCH', 'PUT'):
            return AdminBookingUpdateSerializer
        return AdminBookingDetailSerializer


class AdminBookingCancelView(APIView):
    permission_classes = [IsAdminStaff]

    def post(self, request, booking_id):
        try:
            booking = Booking.objects.get(booking_id=booking_id)
        except Booking.DoesNotExist:
            return Response({'error': 'Booking not found'}, status=status.HTTP_404_NOT_FOUND)

        if booking.status == 'cancelled':
            return Response(
                {'error': 'Booking is already cancelled.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = AdminBookingCancelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        old_status = booking.status
        booking.status = 'cancelled'
        booking.cancelled_at = timezone.now()
        booking.cancellation_reason = data['cancellation_reason']
        booking.refund_amount = data.get('refund_amount', 0)
        if booking.refund_amount > 0:
            booking.refund_status = 'pending'

        # Refund to wallet
        if data.get('refund_to_wallet') and booking.refund_amount > 0:
            try:
                from index.models import Wallet
                wallet = Wallet.objects.get(user=booking.customer.user)
                wallet.deposit(booking.refund_amount)
                booking.refund_status = 'processed'
            except Exception:
                pass  # Wallet refund failed; stays 'pending' for manual processing

        booking.save()

        BookingActivityLog.objects.create(
            booking_id=booking.id,
            action='cancelled',
            actor=request.user,
            description=f'Admin cancelled booking. Reason: {data["cancellation_reason"]}',
            old_value=old_status,
            new_value='cancelled',
        )

        return Response({'detail': f'Booking {booking_id} cancelled.'})


class AdminBookingActivityView(generics.ListAPIView):
    permission_classes = [IsAdminStaff]
    serializer_class = AdminBookingActivityLogSerializer

    def get_queryset(self):
        return BookingActivityLog.objects.filter(
            booking__booking_id=self.kwargs.get('booking_id')
        ).select_related('actor').order_by('-created_at')
