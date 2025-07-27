from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
import stripe
from django.conf import settings
from .models import Transaction, Wallet

@csrf_exempt
@require_POST
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    print(f"Received webhook payload: {payload}")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        # Invalid signature
        return HttpResponse(status=400)

    # Handle the checkout.session.completed event
    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        handle_successful_payment(payment_intent)
    elif event['type'] == 'payment_intent.payment_failed':
        payment_intent = event['data']['object']
        handle_failed_payment(payment_intent)
    elif event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        handle_checkout_session_completed(session)

    return HttpResponse(status=200)

def handle_checkout_session_completed(session):
    """Handle a completed checkout session."""
    try:
        # First, try to find a transaction by session ID
        # This would be the case if we stored the checkout session ID
        transaction = Transaction.objects.get(stripe_payment_intent_id=session['id'])
        
        if transaction.status != Transaction.COMPLETED:
            transaction.status = Transaction.COMPLETED
            transaction.save()
            
            # Update wallet balance
            wallet = transaction.wallet
            wallet.balance += transaction.amount
            wallet.save()
            print(f"Checkout deposit of {transaction.amount} completed for wallet {wallet.id}")
            
    except Transaction.DoesNotExist:
        # Transaction not found by session ID - try to find by metadata
        try:
            transaction_id = session.get('metadata', {}).get('transaction_id')
            if transaction_id:
                transaction = Transaction.objects.get(id=transaction_id)
                
                if transaction.status != Transaction.COMPLETED:
                    transaction.status = Transaction.COMPLETED
                    transaction.save()
                    
                    # Update wallet balance
                    wallet = transaction.wallet
                    wallet.balance += transaction.amount
                    wallet.save()
            else:
                # Try to find the wallet directly from metadata
                wallet_id = session.get('metadata', {}).get('wallet_id')
                if wallet_id:
                    wallet = Wallet.objects.get(id=wallet_id)
                    amount = session.get('amount_total', 0) / 100  # Convert from cents
                    
                    # Create new transaction
                    transaction = Transaction.objects.create(
                        wallet=wallet,
                        amount=amount,
                        transaction_type=Transaction.DEPOSIT,
                        status=Transaction.COMPLETED,
                        stripe_payment_intent_id=session['id'],
                        description="Deposit via Stripe Checkout"
                    )
                    
                    # Update wallet balance
                    wallet.balance += amount
                    wallet.save()
        except (Transaction.DoesNotExist, Wallet.DoesNotExist):
            # Cannot find associated transaction or wallet
            pass

def handle_successful_payment(payment_intent):
    # Find the transaction by payment intent ID
    try:
        transaction = Transaction.objects.get(stripe_payment_intent_id=payment_intent['id'])
        if transaction.status != Transaction.COMPLETED:
            transaction.status = Transaction.COMPLETED
            transaction.save()
            
            # If this was a pending deposit, update the wallet balance
            if transaction.transaction_type == Transaction.DEPOSIT:
                wallet = transaction.wallet
                wallet.balance += transaction.amount
                wallet.save()
                
                # Log the completion of the transaction
                print(f"Deposit of {transaction.amount} completed for wallet {wallet.id}")
    except Transaction.DoesNotExist:
        # Create a new transaction if it doesn't exist yet
        # This could happen if webhook arrives before the API call completes
        if payment_intent.get('metadata', {}).get('type') == 'wallet_deposit':
            try:
                # Try to find the customer
                customer_id = payment_intent.get('customer')
                if customer_id:
                    wallet = Wallet.objects.get(stripe_customer_id=customer_id)
                    amount = payment_intent.get('amount', 0) / 100  # Convert from cents
                    
                    # Create and complete the transaction
                    transaction = Transaction.objects.create(
                        wallet=wallet,
                        amount=amount,
                        transaction_type=Transaction.DEPOSIT,
                        status=Transaction.COMPLETED,
                        stripe_payment_intent_id=payment_intent['id']
                    )
                    
                    # Update wallet balance
                    wallet.balance += amount
                    wallet.save()
            except Wallet.DoesNotExist:
                # Cannot find associated wallet
                pass

def handle_failed_payment(payment_intent):
    try:
        transaction = Transaction.objects.get(stripe_payment_intent_id=payment_intent['id'])
        transaction.status = Transaction.FAILED
        transaction.save()
    except Transaction.DoesNotExist:
        # Handle case where transaction is not found
        pass
