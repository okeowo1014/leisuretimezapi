"""
Management command to auto-cancel stale or expired bookings.

Run periodically via cron (recommended: every hour) or a task scheduler::

    # Cron example — every hour
    0 * * * * cd /path/to/project && python manage.py auto_cancel_bookings

Cancellation rules (all configurable via CLI flags):

1. **Date passed** — travel start date (``datefrom``) is in the past and the
   booking was never paid.

2. **Pending too long** — booking has been in ``pending`` status longer than
   ``--max-pending-hours`` (default: 72 hours / 3 days).

3. **Availability exhausted** — the package linked to the booking has been
   deactivated (``status != 'active'``).

All cancelled bookings receive:
- ``status = 'cancelled'``
- ``auto_cancelled = True``
- ``cancellation_reason`` with a human-readable explanation
- An in-app notification + email to the customer

The command is idempotent — running it multiple times will not re-process
already-cancelled bookings.
"""

import logging
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from index.models import Booking, Package
from index.utils import notify_booking_auto_cancelled

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Auto-cancel stale/expired bookings (date passed, pending too long, package unavailable)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--max-pending-hours',
            type=int,
            default=72,
            help='Cancel pending bookings older than this many hours (default: 72)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview which bookings would be cancelled without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        max_pending_hours = options['max_pending_hours']
        now = timezone.now()
        today = now.date()
        pending_cutoff = now - timedelta(hours=max_pending_hours)

        total_cancelled = 0

        # --- Rule 1: Travel date has passed (unpaid bookings only) ---
        date_passed_qs = Booking.objects.filter(
            status__in=['pending'],
            datefrom__lt=today,
        )
        for booking in date_passed_qs:
            if dry_run:
                self.stdout.write(
                    f'  [DRY-RUN] Would cancel {booking.booking_id} '
                    f'(date passed: {booking.datefrom})'
                )
            else:
                self._cancel_booking(
                    booking,
                    reason='date_passed',
                    explanation=(
                        f'Auto-cancelled: travel start date ({booking.datefrom}) '
                        f'has passed without payment.'
                    ),
                )
                total_cancelled += 1

        # --- Rule 2: Pending too long ---
        stale_qs = Booking.objects.filter(
            status='pending',
            created_at__lt=pending_cutoff,
        )
        # Exclude those already caught by rule 1
        stale_qs = stale_qs.filter(datefrom__gte=today)
        for booking in stale_qs:
            if dry_run:
                self.stdout.write(
                    f'  [DRY-RUN] Would cancel {booking.booking_id} '
                    f'(pending since {booking.created_at})'
                )
            else:
                self._cancel_booking(
                    booking,
                    reason='pending_too_long',
                    explanation=(
                        f'Auto-cancelled: booking remained pending for over '
                        f'{max_pending_hours} hours without payment.'
                    ),
                )
                total_cancelled += 1

        # --- Rule 3: Package no longer available ---
        # Find packages that are deactivated, then cancel their pending bookings
        inactive_package_ids = set(
            Package.objects.exclude(status='active')
            .values_list('package_id', flat=True)
        )
        if inactive_package_ids:
            unavailable_qs = Booking.objects.filter(
                status='pending',
                package__in=inactive_package_ids,
            )
            for booking in unavailable_qs:
                if dry_run:
                    self.stdout.write(
                        f'  [DRY-RUN] Would cancel {booking.booking_id} '
                        f'(package {booking.package} no longer active)'
                    )
                else:
                    self._cancel_booking(
                        booking,
                        reason='availability_exhausted',
                        explanation=(
                            f'Auto-cancelled: package {booking.package} is no '
                            f'longer available.'
                        ),
                    )
                    total_cancelled += 1

        prefix = '[DRY-RUN] ' if dry_run else ''
        self.stdout.write(
            self.style.SUCCESS(
                f'{prefix}Auto-cancel complete: {total_cancelled} booking(s) cancelled.'
            )
        )

    def _cancel_booking(self, booking, reason, explanation):
        """Cancel a single booking and send notifications."""
        booking.status = 'cancelled'
        booking.auto_cancelled = True
        booking.cancelled_at = timezone.now()
        booking.cancellation_reason = explanation
        booking.save()

        try:
            notify_booking_auto_cancelled(booking, reason)
        except Exception:
            logger.exception(
                "Failed to send auto-cancel notification for %s",
                booking.booking_id,
            )

        logger.info("Auto-cancelled booking %s: %s", booking.booking_id, reason)
