"""
Stripe utility functions for customer, payment intent, payout, and checkout management.
"""

import stripe
from django.conf import settings
from rest_framework.exceptions import APIException

stripe.api_key = settings.STRIPE_SECRET_KEY


def create_stripe_customer(user):
    """Create a Stripe customer for the given user and return the customer ID."""
    try:
        customer = stripe.Customer.create(
            email=user.email,
            name=f"{user.firstname} {user.lastname}",
            metadata={'user_id': str(user.id)},
        )
        return customer.id
    except stripe.error.StripeError as e:
        raise APIException(f"Stripe error: {str(e)}")


def create_payment_intent(
    amount, currency="usd", customer_id=None, payment_method_id=None
):
    """Create a Stripe Payment Intent and return it."""
    try:
        params = {
            'amount': int(amount * 100),
            'currency': currency,
            'metadata': {'type': 'wallet_deposit'},
            'automatic_payment_methods': {'enabled': True},
        }

        if customer_id:
            params['customer'] = customer_id

        if payment_method_id:
            params['payment_method'] = payment_method_id
            params['confirm'] = True
            params['automatic_payment_methods'] = {'enabled': False}

        return stripe.PaymentIntent.create(**params)
    except stripe.error.StripeError as e:
        raise APIException(f"Stripe error: {str(e)}")


def confirm_payment_intent(payment_intent_id, payment_method_id):
    """Confirm a Stripe Payment Intent with a payment method."""
    try:
        return stripe.PaymentIntent.confirm(
            payment_intent_id, payment_method=payment_method_id
        )
    except stripe.error.StripeError as e:
        raise APIException(f"Stripe error: {str(e)}")


def create_payout(amount, destination, currency="usd"):
    """Create a Stripe Payout."""
    try:
        return stripe.Payout.create(
            amount=int(amount * 100),
            currency=currency,
            destination=destination,
            metadata={'type': 'wallet_withdrawal'},
        )
    except stripe.error.StripeError as e:
        raise APIException(f"Stripe error: {str(e)}")


def create_checkout_session(
    amount, customer_id=None, currency="usd",
    success_url=None, cancel_url=None, metadata=None
):
    """Create a Stripe Checkout Session for wallet deposits."""
    if metadata is None:
        metadata = {}

    if not success_url or not cancel_url:
        raise ValueError("Success and cancel URLs are required")

    try:
        checkout_params = {
            'payment_method_types': ['card'],
            'line_items': [{
                'price_data': {
                    'currency': currency,
                    'product_data': {
                        'name': 'Wallet Deposit',
                        'description': 'Deposit funds to your wallet',
                    },
                    'unit_amount': int(amount * 100),
                },
                'quantity': 1,
            }],
            'mode': 'payment',
            'success_url': success_url,
            'cancel_url': cancel_url,
            'metadata': {**metadata, 'type': 'wallet_deposit'},
        }

        if customer_id:
            checkout_params['customer'] = customer_id

        return stripe.checkout.Session.create(**checkout_params)
    except stripe.error.StripeError as e:
        raise APIException(f"Stripe error: {str(e)}")
