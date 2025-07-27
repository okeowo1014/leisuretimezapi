## utils.py - Add this function

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

```javascript
// Example frontend code for handling wallet deposits with Stripe Checkout

async function initiateCheckoutDeposit(walletId, amount) {
  try {
    // 1. Request checkout session from your server
    const response = await fetch(`/api/wallets/${walletId}/deposit/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer YOUR_AUTH_TOKEN'
      },
      body: JSON.stringify({ 
        amount,
        // Optional: provide custom success and cancel URLs
        success_url: `${window.location.origin}/deposit-success?session_id={CHECKOUT_SESSION_ID}`,
        cancel_url: `${window.location.origin}/deposit-cancel`
      })
    });
    
    const data = await response.json();
    
    if (data.checkout_url) {
      // 2. Redirect to Stripe Checkout
      window.location.href = data.checkout_url;
    } else {
      // Handle any errors
      console.error('Error creating checkout session:', data);
      showErrorMessage(data.detail || 'Could not create checkout session');
    }
  } catch (error) {
    console.error('Error during checkout process:', error);
    showErrorMessage('An unexpected error occurred.');
  }
}

// Helper function to show error messages
function showErrorMessage(message) {
  const errorElement = document.getElementById('error-message');
  errorElement.textContent = message;
  errorElement.style.display = 'block';
}
```

## HTML Form Example for Stripe Checkout

```html
<div class="checkout-container">
  <h2>Deposit to Your Wallet</h2>
  
  <form id="checkout-form">
    <div class="amount-container">
      <label for="amount">Amount to Deposit</label>
      <input type="number" id="amount" min="0.01" step="0.01" value="10.00" />
    </div>
    
    <button id="checkout-button" type="submit">
      <span id="button-text">Proceed to Checkout</span>
    </button>
    
    <div id="error-message" class="hidden"></div>
  </form>
</div>

<script>
  document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('checkout-form');
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      
      const amountInput = document.getElementById('amount');
      const amount = parseFloat(amountInput.value);
      
      if (amount < 0.01) {
        showErrorMessage('Amount must be at least 0.01');
        return;
      }
      
      // Replace 'YOUR_WALLET_ID' with actual wallet ID
      await initiateCheckoutDeposit('YOUR_WALLET_ID', amount);
    });
  });
</script>
```

## Success Page Example

```html
<div class="success-container">
  <h1>Payment Successful!</h1>
  <p>Thank you for your deposit. Your wallet has been credited.</p>
  
  <div id="transaction-details">
    <!-- Transaction details will be loaded here if available -->
  </div>
  
  <a href="/wallet" class="button">Return to Wallet</a>
</div>

<script>
  document.addEventListener('DOMContentLoaded', function() {
    // Get session_id from URL if present
    const urlParams = new URLSearchParams(window.location.search);
    const sessionId = urlParams.get('session_id');
    
    if (sessionId) {
      // Optionally: fetch transaction details using session ID
      fetchTransactionDetails(sessionId);
    }
  });
  
  async function fetchTransactionDetails(sessionId) {
    try {
      const response = await fetch(`/api/transactions/?session_id=${sessionId}`, {
        headers: {
          'Authorization': 'Bearer YOUR_AUTH_TOKEN'
        }
      });
      
      const data = await response.json();
      
      if (data.results && data.results.length > 0) {
        const transaction = data.results[0];
        const detailsElement = document.getElementById('transaction-details');
        
        detailsElement.innerHTML = `
          <div class="transaction-summary">
            <p><strong>Amount:</strong> ${transaction.amount}</p>
            <p><strong>Date:</strong> ${new Date(transaction.created_at).toLocaleString()}</p>
            <p><strong>Status:</strong> ${transaction.status}</p>
            <p><strong>Transaction ID:</strong> ${transaction.id}</p>
          </div>
        `;
      }
    } catch (error) {
      console.error('Error fetching transaction details:', error);
    }
  }
</script>
```# Django REST Framework Wallet System with Stripe API

## Project Structure
```
wallet_app/
├── __init__.py
├── admin.py
├── apps.py
├── models.py
├── serializers.py
├── urls.py
├── views.py
└── utils.py
```

## models.py

```python
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid

class Wallet(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    stripe_customer_id = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.username}'s Wallet (Balance: {self.balance})"

    def deposit(self, amount):
        """Add funds to wallet"""
        if amount <= 0:
            raise ValueError("Amount must be positive")
        self.balance += amount
        self.save()
        return Transaction.objects.create(
            wallet=self,
            amount=amount,
            transaction_type=Transaction.DEPOSIT,
            status=Transaction.COMPLETED
        )

    def withdraw(self, amount):
        """Withdraw funds from wallet"""
        if amount <= 0:
            raise ValueError("Amount must be positive")
        if self.balance < amount:
            raise ValueError("Insufficient funds")
        self.balance -= amount
        self.save()
        return Transaction.objects.create(
            wallet=self,
            amount=amount,
            transaction_type=Transaction.WITHDRAWAL,
            status=Transaction.COMPLETED
        )

    def transfer(self, recipient_wallet, amount):
        """Transfer funds to another wallet"""
        if amount <= 0:
            raise ValueError("Amount must be positive")
        if self.balance < amount:
            raise ValueError("Insufficient funds")
        
        self.balance -= amount
        recipient_wallet.balance += amount
        self.save()
        recipient_wallet.save()
        
        transaction = Transaction.objects.create(
            wallet=self,
            amount=amount,
            transaction_type=Transaction.TRANSFER,
            recipient=recipient_wallet.user,
            status=Transaction.COMPLETED
        )
        return transaction


class Transaction(models.Model):
    # Transaction types
    DEPOSIT = 'deposit'
    WITHDRAWAL = 'withdrawal'
    TRANSFER = 'transfer'
    
    # Transaction statuses
    PENDING = 'pending'
    COMPLETED = 'completed'
    FAILED = 'failed'
    
    TRANSACTION_TYPE_CHOICES = [
        (DEPOSIT, 'Deposit'),
        (WITHDRAWAL, 'Withdrawal'),
        (TRANSFER, 'Transfer'),
    ]
    
    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (COMPLETED, 'Completed'),
        (FAILED, 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPE_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDING)
    recipient = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='received_transactions')
    stripe_payment_intent_id = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.transaction_type.capitalize()} of {self.amount} by {self.wallet.user.username}"
```

## serializers.py

```python
from rest_framework import serializers
from .models import Wallet, Transaction
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class WalletSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Wallet
        fields = ['id', 'user', 'balance', 'created_at', 'updated_at', 'is_active']
        read_only_fields = ['balance']

class TransactionSerializer(serializers.ModelSerializer):
    wallet = serializers.PrimaryKeyRelatedField(read_only=True)
    recipient = UserSerializer(read_only=True)
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'wallet', 'amount', 'transaction_type', 
            'status', 'recipient', 'description', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['status', 'wallet', 'recipient']

class DepositSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0.01)
    payment_method_id = serializers.CharField(max_length=100, required=False)
    success_url = serializers.URLField(required=False)
    cancel_url = serializers.URLField(required=False)
    
class WithdrawalSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0.01)
    
class TransferSerializer(serializers.Serializer):
    recipient_id = serializers.UUIDField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0.01)
```

## utils.py

```python
import stripe
from django.conf import settings
from rest_framework.exceptions import APIException

stripe.api_key = settings.STRIPE_SECRET_KEY

def create_stripe_customer(user):
    """Create a Stripe customer for the given user."""
    try:
        customer = stripe.Customer.create(
            email=user.email,
            name=f"{user.first_name} {user.last_name}",
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
```

## views.py

```python
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from django.shortcuts import get_object_or_404

from .models import Wallet, Transaction
from .serializers import (
    WalletSerializer, TransactionSerializer, 
    DepositSerializer, WithdrawalSerializer, TransferSerializer
)
from .utils import create_stripe_customer, create_payment_intent, create_payout

class WalletViewSet(viewsets.ModelViewSet):
    serializer_class = WalletSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return only the authenticated user's wallet."""
        return Wallet.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Create a wallet for the authenticated user."""
        if Wallet.objects.filter(user=self.request.user).exists():
            return Response(
                {"detail": "You already have a wallet"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Create Stripe customer if needed
        stripe_customer_id = None
        if self.request.user.email:
            stripe_customer_id = create_stripe_customer(self.request.user)
            
        serializer.save(user=self.request.user, stripe_customer_id=stripe_customer_id)
    
    @action(detail=True, methods=['post'])
    def deposit(self, request, pk=None):
        """Add funds to wallet using Stripe Checkout."""
        wallet = self.get_object()
        serializer = DepositSerializer(data=request.data)
        
        if serializer.is_valid():
            amount = serializer.validated_data['amount']
            
            # Check if specific payment method is provided or if using Checkout
            payment_method_id = serializer.validated_data.get('payment_method_id')
            success_url = serializer.validated_data.get('success_url')
            cancel_url = serializer.validated_data.get('cancel_url')
            
            # Get base URL from request
            base_url = request.build_absolute_uri('/').rstrip('/')
            
            # Use Stripe Checkout if success/cancel URLs are provided or no payment method
            if (success_url and cancel_url) or not payment_method_id:
                # Use provided URLs or defaults
                success_url = success_url or f"{base_url}/wallet/deposit/success"
                cancel_url = cancel_url or f"{base_url}/wallet/deposit/cancel"
                
                try:
                    # Create a pending transaction
                    transaction_obj = Transaction.objects.create(
                        wallet=wallet,
                        amount=amount,
                        transaction_type=Transaction.DEPOSIT,
                        status=Transaction.PENDING
                    )
                    
                    # Create Stripe Checkout session
                    checkout_session = create_checkout_session(
                        amount=amount,
                        customer_id=wallet.stripe_customer_id,
                        success_url=success_url,
                        cancel_url=cancel_url,
                        metadata={
                            'transaction_id': str(transaction_obj.id),
                            'wallet_id': str(wallet.id),
                            'user_id': str(wallet.user.id)
                        }
                    )
                    
                    # Update transaction with session ID
                    transaction_obj.stripe_payment_intent_id = checkout_session.id
                    transaction_obj.save()
                    
                    # Return checkout URL
                    return Response({
                        'checkout_url': checkout_session.url,
                        'session_id': checkout_session.id,
                        'transaction_id': str(transaction_obj.id)
                    })
                    
                except ValueError as e:
                    return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
            
            # If specifically requesting payment intent (legacy flow)
            else:
                try:
                    with transaction.atomic():
                        # Create Stripe payment intent
                        payment_intent = create_payment_intent(
                            amount=amount,
                            payment_method_id=payment_method_id,
                            customer_id=wallet.stripe_customer_id
                        )
                        
                        # Check if payment was successful
                        if payment_intent.status == 'succeeded':
                            # Add funds to wallet
                            transaction_obj = wallet.deposit(amount)
                            transaction_obj.stripe_payment_intent_id = payment_intent.id
                            transaction_obj.save()
                            
                            return Response({
                                'detail': 'Deposit successful',
                                'transaction': TransactionSerializer(transaction_obj).data
                            })
                        elif payment_intent.status == 'requires_action' or payment_intent.status == 'requires_confirmation':
                            # Return client secret for handling authentication on client side
                            return Response({
                                'requires_action': True,
                                'payment_intent_client_secret': payment_intent.client_secret,
                                'payment_intent_id': payment_intent.id
                            })
                        elif payment_intent.status == 'requires_payment_method':
                            # Create a transaction in pending state
                            transaction_obj = Transaction.objects.create(
                                wallet=wallet,
                                amount=amount,
                                transaction_type=Transaction.DEPOSIT,
                                status=Transaction.PENDING,
                                stripe_payment_intent_id=payment_intent.id
                            )
                            
                            # Return information needed for the client to complete payment
                            return Response({
                                'detail': 'Payment method required',
                                'payment_intent_id': payment_intent.id,
                                'client_secret': payment_intent.client_secret,
                                'transaction_id': str(transaction_obj.id)
                            })
                        else:
                            return Response({
                                'detail': f'Payment not completed. Status: {payment_intent.status}',
                                'payment_intent_id': payment_intent.id
                            }, status=status.HTTP_400_BAD_REQUEST)
                            
                except ValueError as e:
                    return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def withdraw(self, request, pk=None):
        """Withdraw funds from wallet."""
        wallet = self.get_object()
        serializer = WithdrawalSerializer(data=request.data)
        
        if serializer.is_valid():
            amount = serializer.validated_data['amount']
            
            try:
                with transaction.atomic():
                    # Process withdrawal
                    transaction_obj = wallet.withdraw(amount)
                    
                    # If you're implementing actual withdrawal to a bank account,
                    # you would handle Stripe payout here
                    # payout = create_payout(amount, wallet.user.stripe_account_id)
                    # transaction_obj.stripe_payment_intent_id = payout.id
                    # transaction_obj.save()
                    
                    return Response({
                        'detail': 'Withdrawal successful',
                        'transaction': TransactionSerializer(transaction_obj).data
                    })
                    
            except ValueError as e:
                return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def transfer(self, request, pk=None):
        """Transfer funds to another user's wallet."""
        wallet = self.get_object()
        serializer = TransferSerializer(data=request.data)
        
        if serializer.is_valid():
            recipient_id = serializer.validated_data['recipient_id']
            amount = serializer.validated_data['amount']
            
            try:
                # Find recipient's wallet
                recipient_wallet = get_object_or_404(Wallet, id=recipient_id)
                
                with transaction.atomic():
                    # Process transfer
                    transaction_obj = wallet.transfer(recipient_wallet, amount)
                    
                    return Response({
                        'detail': 'Transfer successful',
                        'transaction': TransactionSerializer(transaction_obj).data
                    })
                    
            except ValueError as e:
                return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
            except Wallet.DoesNotExist:
                return Response(
                    {'detail': 'Recipient wallet not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def transactions(self, request, pk=None):
        """Get all transactions for the wallet."""
        wallet = self.get_object()
        transactions = Transaction.objects.filter(wallet=wallet).order_by('-created_at')
        
        # Optional filtering
        transaction_type = request.query_params.get('type')
        if transaction_type:
            transactions = transactions.filter(transaction_type=transaction_type)
            
        page = self.paginate_queryset(transactions)
        if page is not None:
            serializer = TransactionSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
            
        serializer = TransactionSerializer(transactions, many=True)
        return Response(serializer.data)


class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return only the authenticated user's transactions."""
        return Transaction.objects.filter(
            wallet__user=self.request.user
        ).order_by('-created_at')
    
    @action(detail=True, methods=['get'])
    def check_status(self, request, pk=None):
        """Check the status of a transaction with Stripe if applicable."""
        transaction = self.get_object()
        
        if transaction.stripe_payment_intent_id:
            # Here you would check with Stripe API for the current status
            # This is a simplified example
            return Response({
                'transaction': TransactionSerializer(transaction).data,
                'stripe_status': 'Would fetch from Stripe API'
            })
        
        return Response({
            'transaction': TransactionSerializer(transaction).data,
        })
```

## urls.py

```python
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'wallets', views.WalletViewSet, basename='wallet')
router.register(r'transactions', views.TransactionViewSet, basename='transaction')

urlpatterns = [
    path('', include(router.urls)),
]
```

## settings.py additions

```python
# Add these to your Django settings.py

INSTALLED_APPS = [
    # ...existing apps
    'rest_framework',
    'wallet_app',
]

# Stripe Configuration
STRIPE_PUBLIC_KEY = 'your_stripe_public_key'
STRIPE_SECRET_KEY = 'your_stripe_secret_key'
STRIPE_WEBHOOK_SECRET = 'your_stripe_webhook_secret'
```

## Webhook handling (add to views.py)

```python
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
```

## Add webhook URL (add to urls.py)

```python
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'wallets', views.WalletViewSet, basename='wallet')
router.register(r'transactions', views.TransactionViewSet, basename='transaction')

urlpatterns = [
    path('', include(router.urls)),
    path('webhook/stripe/', views.stripe_webhook, name='stripe-webhook'),
]
```