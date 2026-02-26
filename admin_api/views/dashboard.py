from decimal import Decimal

from django.db.models import Count, Q, Sum
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from admin_api.permissions import IsAdminStaff
from index.models import (
    Booking, CustomUser, Invoice, Payment, PersonalisedBooking,
    PersonalisedBookingInvoice, PersonalisedBookingPayment,
    Quotation, SupportTicket,
)


class AdminDashboardView(APIView):
    permission_classes = [IsAdminStaff]

    def get(self, request):
        now = timezone.now()
        seven_days_ago = now - timezone.timedelta(days=7)
        thirty_days_ago = now - timezone.timedelta(days=30)

        # Users
        total_users = CustomUser.objects.count()
        new_users_7d = CustomUser.objects.filter(date_joined__gte=seven_days_ago).count()
        new_users_30d = CustomUser.objects.filter(date_joined__gte=thirty_days_ago).count()
        active_users = CustomUser.objects.filter(is_active=True).count()

        # Legacy bookings
        booking_stats = Booking.objects.aggregate(
            total=Count('id'),
            pending=Count('id', filter=Q(status='pending')),
            paid=Count('id', filter=Q(payment_status='paid')),
            cancelled=Count('id', filter=Q(status='cancelled')),
        )

        # Personalised bookings
        pb_stats = PersonalisedBooking.objects.aggregate(
            total=Count('id'),
            pending=Count('id', filter=Q(status='pending')),
            quoted=Count('id', filter=Q(status='quoted')),
            confirmed=Count('id', filter=Q(status='confirmed')),
            completed=Count('id', filter=Q(status='completed')),
        )

        # Revenue
        revenue_bookings = Payment.objects.filter(paid=True).aggregate(
            total=Sum('total')
        )['total'] or Decimal('0.00')

        revenue_personalised = PersonalisedBookingPayment.objects.filter(
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        # Support
        support_stats = SupportTicket.objects.aggregate(
            open=Count('id', filter=Q(status='open')),
            in_progress=Count('id', filter=Q(status='in_progress')),
        )

        # Pending work
        pending_quotations = Quotation.objects.filter(status='draft').count()
        pending_invoices = PersonalisedBookingInvoice.objects.filter(
            status__in=['draft', 'sent']
        ).count()

        # Recent activity
        from index.models import BookingActivityLog
        from admin_api.serializers.bookings import AdminBookingActivityLogSerializer
        recent_activity = BookingActivityLog.objects.select_related('actor').order_by(
            '-created_at'
        )[:10]

        return Response({
            'stats': {
                'total_users': total_users,
                'new_users_7d': new_users_7d,
                'new_users_30d': new_users_30d,
                'active_users': active_users,
                'total_bookings': booking_stats['total'],
                'bookings_pending': booking_stats['pending'],
                'bookings_paid': booking_stats['paid'],
                'bookings_cancelled': booking_stats['cancelled'],
                'total_personalised_bookings': pb_stats['total'],
                'pb_pending': pb_stats['pending'],
                'pb_quoted': pb_stats['quoted'],
                'pb_confirmed': pb_stats['confirmed'],
                'pb_completed': pb_stats['completed'],
                'revenue_bookings': str(revenue_bookings),
                'revenue_personalised': str(revenue_personalised),
                'support_open': support_stats['open'],
                'support_in_progress': support_stats['in_progress'],
                'pending_quotations': pending_quotations,
                'pending_invoices': pending_invoices,
            },
            'recent_activity': AdminBookingActivityLogSerializer(
                recent_activity, many=True
            ).data,
        })
