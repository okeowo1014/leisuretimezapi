from rest_framework import serializers


class DashboardStatsSerializer(serializers.Serializer):
    total_users = serializers.IntegerField()
    new_users_7d = serializers.IntegerField()
    new_users_30d = serializers.IntegerField()
    active_users = serializers.IntegerField()

    total_bookings = serializers.IntegerField()
    bookings_pending = serializers.IntegerField()
    bookings_paid = serializers.IntegerField()
    bookings_cancelled = serializers.IntegerField()

    total_personalised_bookings = serializers.IntegerField()
    pb_pending = serializers.IntegerField()
    pb_quoted = serializers.IntegerField()
    pb_confirmed = serializers.IntegerField()
    pb_completed = serializers.IntegerField()

    revenue_bookings = serializers.DecimalField(max_digits=12, decimal_places=2)
    revenue_personalised = serializers.DecimalField(max_digits=12, decimal_places=2)

    support_open = serializers.IntegerField()
    support_in_progress = serializers.IntegerField()

    pending_quotations = serializers.IntegerField()
    pending_invoices = serializers.IntegerField()
