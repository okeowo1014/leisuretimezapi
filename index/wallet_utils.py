import stripe
from django.conf import settings
from rest_framework.exceptions import APIException

# stripe.api_key = 'sk_test_51Q1AmzIdBWRin0jg8ra6JpGiXYhQj7JfcIJne6KzLOY0oHCwsNjkpqdRmHL9HhoaU0rvAKfKnDkKWwG2ulX698TF00BpR6ZCAn'
stripe.api_key = 'sk_test_51RJjB32KJEgBmA6Bs0Zhd2qh8ElLfOcg1bLi718romNjC54V4WTbr4eNhOKf3ySOK0AyjBECzUsFxpvsKsNvljY000b2rmr9JE'


def create_stripe_customer(user):
    """Create a Stripe customer for the given user."""
    try:
        customer = stripe.Customer.create(
            email=user.email,
            name=f"{user.firstname} {user.lastname}",
            metadata={
                'user_id': str(user.id)
            }
        )
        return customer.id
    except stripe.error.StripeError as e:
        raise APIException(f"Stripe error: {str(e)}")

def create_payment_intent(amount, currency="usd", customer_id=None, payment_method_id=None):
    """Create a Stripe Payment Intent."""
    try:
        params = {
            'amount': int(amount * 100),  # Convert to cents
            'currency': currency,
            'metadata': {'type': 'wallet_deposit'},
            'automatic_payment_methods': {'enabled': True},  # Enable automatic payment methods
        }
        
        # Add customer if available
        if customer_id:
            params['customer'] = customer_id
            
        # Add payment method if provided
        if payment_method_id:
            params['payment_method'] = payment_method_id
            params['confirm'] = True
            params['automatic_payment_methods'] = {'enabled': False}  # Disable when specific method provided
            
        intent = stripe.PaymentIntent.create(**params)
        return intent
    except stripe.error.StripeError as e:
        raise APIException(f"Stripe error: {str(e)}")

def confirm_payment_intent(payment_intent_id, payment_method_id):
    """Confirm a Stripe Payment Intent with a payment method."""
    try:
        intent = stripe.PaymentIntent.confirm(
            payment_intent_id,
            payment_method=payment_method_id
        )
        return intent
    except stripe.error.StripeError as e:
        raise APIException(f"Stripe error: {str(e)}")

def create_payout(amount, destination, currency="usd"):
    """Create a Stripe Payout."""
    try:
        payout = stripe.Payout.create(
            amount=int(amount * 100),  # Convert to cents
            currency=currency,
            destination=destination,
            metadata={'type': 'wallet_withdrawal'}
        )
        return payout
    except stripe.error.StripeError as e:
        raise APIException(f"Stripe error: {str(e)}")


def create_checkout_session(amount, customer_id=None, currency="usd", success_url=None, cancel_url=None, metadata=None):
    """Create a Stripe Checkout Session."""
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
                        'description': f'Deposit funds to your wallet',
                    },
                    'unit_amount': int(amount * 100),  # Convert to cents
                },
                'quantity': 1,
            }],
            'mode': 'payment',
            'success_url': success_url,
            'cancel_url': cancel_url,
            'metadata': {**metadata, 'type': 'wallet_deposit'}
        }
        
        # Add customer if available
        if customer_id:
            checkout_params['customer'] = customer_id
            
        session = stripe.checkout.Session.create(**checkout_params)
        return session
    except stripe.error.StripeError as e:
        raise APIException(f"Stripe error: {str(e)}")## Client-Side Implementation for Stripe Checkout




# def create_stripe_customer(user):
#     """Create a Stripe customer for the given user."""
#     try:
#         customer = stripe.Customer.create(
#             email=user.email,
#             name=f"{user.firstname} {user.lastname}",
#             metadata={
#                 'user_id': str(user.id)
#             }
#         )
#         return customer.id
#     except stripe.error.StripeError as e:
#         raise APIException(f"Stripe error: {str(e)}")

# def create_payment_intent(amount, currency="usd", customer_id=None, payment_method_id=None):
#     """Create a Stripe Payment Intent."""
#     try:
#         intent = stripe.PaymentIntent.create(
#             amount=int(amount * 100),  # Convert to cents
#             currency=currency,
#             customer=customer_id,
#             # automatic_payment_methods={"enabled": True},
#             # confirm=True,
#             metadata={'type': 'wallet_deposit'}
#         )
#         return intent
#     except stripe.error.StripeError as e:
#         raise APIException(f"Stripe error: {str(e)}")

# def confirm_payment_intent(payment_intent_id, payment_method_id):
#     """Confirm a Stripe Payment Intent with a payment method."""
#     try:
#         intent = stripe.PaymentIntent.confirm(
#             payment_intent_id,
#             payment_method=payment_method_id,
#         )
#         return intent
#     except stripe.error.StripeError as e:
#         raise APIException(f"Stripe error: {str(e)}")

# def create_payout(amount, destination, currency="usd"):
    """Create a Stripe Payout."""
    try:
        payout = stripe.Payout.create(
            amount=int(amount * 100),  # Convert to cents
            currency=currency,
            destination=destination,
            metadata={'type': 'wallet_withdrawal'}
        )
        return payout
    except stripe.error.StripeError as e:
        raise APIException(f"Stripe error: {str(e)}")