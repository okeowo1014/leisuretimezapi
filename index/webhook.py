"""
Stripe webhook handlers for processing payment events.

Handles payment_intent.succeeded, payment_intent.payment_failed,
and checkout.session.completed events.
"""

import logging

import stripe
from django.conf import settings
from django.db import transaction as db_transaction
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import Booking, Transaction, Wallet

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def stripe_webhook(request):
    """Process incoming Stripe webhook events."""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        logger.warning("Invalid webhook payload received")
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        logger.warning("Invalid webhook signature")
        return HttpResponse(status=400)

    event_type = event['type']
    data_object = event['data']['object']

    if event_type == 'payment_intent.succeeded':
        _handle_successful_payment(data_object)
    elif event_type == 'payment_intent.payment_failed':
        _handle_failed_payment(data_object)
    elif event_type == 'checkout.session.completed':
        _handle_checkout_session_completed(data_object)
    elif event_type == 'checkout.session.expired':
        _handle_checkout_session_expired(data_object)
    else:
        logger.info("Unhandled webhook event type: %s", event_type)

    return HttpResponse(status=200)


def _handle_checkout_session_completed(session):
    """Handle a completed checkout session by crediting the wallet.

    Uses atomic transactions with select_for_update to prevent
    double-crediting from duplicate webhook deliveries.
    """
    with db_transaction.atomic():
        try:
            txn = Transaction.objects.select_for_update().get(
                stripe_payment_intent_id=session['id']
            )
            if txn.status != Transaction.COMPLETED:
                txn.status = Transaction.COMPLETED
                txn.save()
                wallet = Wallet.objects.select_for_update().get(pk=txn.wallet_id)
                wallet.balance += txn.amount
                wallet.save()
                logger.info(
                    "Checkout deposit of %s completed for wallet %s",
                    txn.amount, wallet.id,
                )
            return
        except Transaction.DoesNotExist:
            pass

    # Try finding by metadata transaction_id
    transaction_id = session.get('metadata', {}).get('transaction_id')
    if transaction_id:
        with db_transaction.atomic():
            try:
                txn = Transaction.objects.select_for_update().get(id=transaction_id)
                if txn.status != Transaction.COMPLETED:
                    txn.status = Transaction.COMPLETED
                    txn.save()
                    wallet = Wallet.objects.select_for_update().get(pk=txn.wallet_id)
                    wallet.balance += txn.amount
                    wallet.save()
                    logger.info(
                        "Deposit of %s completed for wallet %s (via metadata)",
                        txn.amount, wallet.id,
                    )
                return
            except Transaction.DoesNotExist:
                pass

    # Try finding wallet directly from metadata
    wallet_id = session.get('metadata', {}).get('wallet_id')
    if wallet_id:
        with db_transaction.atomic():
            try:
                wallet = Wallet.objects.select_for_update().get(id=wallet_id)
                amount = session.get('amount_total', 0) / 100
                Transaction.objects.create(
                    wallet=wallet,
                    amount=amount,
                    transaction_type=Transaction.DEPOSIT,
                    status=Transaction.COMPLETED,
                    stripe_payment_intent_id=session['id'],
                    description="Deposit via Stripe Checkout",
                )
                wallet.balance += amount
                wallet.save()
                logger.info(
                    "New deposit of %s created for wallet %s", amount, wallet.id
                )
            except Wallet.DoesNotExist:
                logger.warning(
                    "Wallet %s not found for checkout session %s",
                    wallet_id, session['id'],
                )


def _handle_successful_payment(payment_intent):
    """Handle a successful payment intent.

    Uses atomic transactions with select_for_update to prevent
    double-crediting from duplicate webhook deliveries.
    """
    with db_transaction.atomic():
        try:
            txn = Transaction.objects.select_for_update().get(
                stripe_payment_intent_id=payment_intent['id']
            )
            if txn.status != Transaction.COMPLETED:
                txn.status = Transaction.COMPLETED
                txn.save()
                if txn.transaction_type == Transaction.DEPOSIT:
                    wallet = Wallet.objects.select_for_update().get(pk=txn.wallet_id)
                    wallet.balance += txn.amount
                    wallet.save()
                    logger.info(
                        "Deposit of %s completed for wallet %s",
                        txn.amount, wallet.id,
                    )
        except Transaction.DoesNotExist:
            if payment_intent.get('metadata', {}).get('type') == 'wallet_deposit':
                customer_id = payment_intent.get('customer')
                if customer_id:
                    try:
                        wallet = Wallet.objects.select_for_update().get(
                            stripe_customer_id=customer_id
                        )
                        amount = payment_intent.get('amount', 0) / 100
                        Transaction.objects.create(
                            wallet=wallet,
                            amount=amount,
                            transaction_type=Transaction.DEPOSIT,
                            status=Transaction.COMPLETED,
                            stripe_payment_intent_id=payment_intent['id'],
                        )
                        wallet.balance += amount
                        wallet.save()
                        logger.info(
                            "New deposit of %s created for wallet %s",
                            amount, wallet.id,
                        )
                    except Wallet.DoesNotExist:
                        logger.warning(
                            "Wallet not found for Stripe customer %s", customer_id
                        )


def _handle_failed_payment(payment_intent):
    """Handle a failed payment intent."""
    try:
        txn = Transaction.objects.get(
            stripe_payment_intent_id=payment_intent['id']
        )
        txn.status = Transaction.FAILED
        txn.save()
        logger.info(
            "Payment %s marked as failed", payment_intent['id']
        )
    except Transaction.DoesNotExist:
        logger.warning(
            "Transaction not found for failed payment %s",
            payment_intent['id'],
        )


def _handle_checkout_session_expired(session):
    """Handle an expired checkout session.

    For split payments, refunds the wallet amount that was deducted
    when the Stripe portion was not completed.
    """
    metadata = session.get('metadata', {})
    payment_type = metadata.get('type', '')

    if payment_type != 'split_booking_payment':
        return

    booking_id = metadata.get('booking_id')
    if not booking_id:
        return

    try:
        booking = Booking.objects.get(
            booking_id=booking_id,
            payment_method='split',
        )
    except Booking.DoesNotExist:
        logger.warning(
            "Booking %s not found for expired split checkout session %s",
            booking_id, session['id'],
        )
        return

    # Only refund if booking hasn't already been paid
    if booking.payment_status == 'paid':
        return

    wallet_amount = booking.wallet_amount_paid
    if wallet_amount <= 0:
        return

    try:
        with db_transaction.atomic():
            wallet = Wallet.objects.select_for_update().get(
                user=booking.customer.user
            )
            refund_txn = wallet.deposit(wallet_amount)
            refund_txn.description = (
                f'Refund: split payment expired for booking {booking.booking_id}'
            )
            refund_txn.reference = booking.booking_id
            refund_txn.save()

            booking.payment_method = ''
            booking.wallet_amount_paid = 0
            booking.stripe_amount_due = 0
            booking.checkout_session_id = None
            booking.status = 'pending'
            booking.save()

        logger.info(
            "Refunded %s to wallet for expired split payment on booking %s",
            wallet_amount, booking.booking_id,
        )
    except Wallet.DoesNotExist:
        logger.error(
            "Cannot refund wallet for booking %s — wallet not found",
            booking.booking_id,
        )
