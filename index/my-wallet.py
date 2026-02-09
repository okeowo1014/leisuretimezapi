# Django REST Framework Wallet System with Stripe API

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
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='wallet')
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
from .models import CustomUser, Wallet, Transaction
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
    payment_method_id = serializers.CharField(max_length=100)
    
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
        intent = stripe.PaymentIntent.create(
            amount=int(amount * 100),  # Convert to cents
            currency=currency,
            customer=customer_id,
            payment_method=payment_method_id,
            confirm=True if payment_method_id else False,
            metadata={'type': 'wallet_deposit'}
        )
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
        """Add funds to wallet using Stripe."""
        wallet = self.get_object()
        serializer = DepositSerializer(data=request.data)
        
        if serializer.is_valid():
            amount = serializer.validated_data['amount']
            payment_method_id = serializer.validated_data['payment_method_id']
            
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

    return HttpResponse(status=200)

def handle_successful_payment(payment_intent):
    # Find the transaction by payment intent ID
    try:
        transaction = Transaction.objects.get(stripe_payment_intent_id=payment_intent['id'])
        if transaction.status != Transaction.COMPLETED:
            transaction.status = Transaction.COMPLETED
            transaction.save()
            
            # If this was a pending deposit, update the wallet balance
            if transaction.transaction_type == Transaction.DEPOSIT and transaction.status == Transaction.PENDING:
                wallet = transaction.wallet
                wallet.balance += transaction.amount
                wallet.save()
    except Transaction.DoesNotExist:
        # Handle case where transaction is not found
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