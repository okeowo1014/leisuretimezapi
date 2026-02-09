"""
Wallet and transaction management views.

Handles wallet creation, deposits (via Stripe), withdrawals, transfers,
and transaction history.
"""

import logging

import stripe
from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Transaction as TransactionModel, Wallet
from .serializers import (
    DepositSerializer, TransactionSerializer, TransferSerializer,
    WalletSerializer, WalletUserSerializer, WithdrawalSerializer,
)
from index.wallet_utils import (
    create_checkout_session, create_payment_intent, create_stripe_customer,
)

logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY


class WalletViewSet(viewsets.ModelViewSet):
    """ViewSet for wallet CRUD, deposits, withdrawals, and transfers."""

    serializer_class = WalletSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return only the authenticated user's wallet."""
        return Wallet.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        """Create a wallet for the authenticated user."""
        if Wallet.objects.filter(user=self.request.user).exists():
            return Response(
                {'detail': 'You already have a wallet'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        stripe_customer_id = None
        if self.request.user.email:
            try:
                stripe_customer_id = create_stripe_customer(self.request.user)
            except Exception:
                logger.exception(
                    "Failed to create Stripe customer for %s",
                    self.request.user.email,
                )

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        wallet = serializer.save(
            user=self.request.user,
            stripe_customer_id=stripe_customer_id,
            is_active=True,
        )

        response_serializer = self.get_serializer(wallet)
        headers = self.get_success_headers(serializer.data)
        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers,
        )

    @action(detail=False, methods=['post'], url_path='deposit')
    def deposit(self, request):
        """Add funds to the authenticated user's wallet using Stripe Checkout."""
        wallet = Wallet.objects.filter(user=request.user).first()
        if not wallet:
            return Response(
                {'detail': 'Wallet not found'},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = DepositSerializer(data=request.data)
        if serializer.is_valid():
            amount = serializer.validated_data['amount']
            payment_method_id = serializer.validated_data.get('payment_method_id')
            success_url = serializer.validated_data.get('success_url')
            cancel_url = serializer.validated_data.get('cancel_url')

            base_url = request.build_absolute_uri('/').rstrip('/')

            if (success_url and cancel_url) or not payment_method_id:
                success_url = success_url or f"{base_url}/wallet/deposit/success"
                cancel_url = cancel_url or f"{base_url}/wallet/deposit/cancel"

                try:
                    transaction_obj = TransactionModel.objects.create(
                        wallet=wallet,
                        amount=amount,
                        transaction_type=TransactionModel.DEPOSIT,
                        status=TransactionModel.PENDING,
                    )

                    checkout_session = create_checkout_session(
                        amount=amount,
                        customer_id=wallet.stripe_customer_id,
                        success_url=success_url,
                        cancel_url=cancel_url,
                        metadata={
                            'transaction_id': str(transaction_obj.id),
                            'wallet_id': str(wallet.id),
                            'user_id': str(wallet.user.id),
                        },
                    )

                    transaction_obj.stripe_payment_intent_id = checkout_session.id
                    transaction_obj.save()

                    return Response({
                        'checkout_url': checkout_session.url,
                        'session_id': checkout_session.id,
                        'transaction_id': str(transaction_obj.id),
                    })
                except ValueError as e:
                    return Response(
                        {'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST
                    )
            else:
                try:
                    with transaction.atomic():
                        payment_intent = create_payment_intent(
                            amount=amount,
                            payment_method_id=payment_method_id,
                            customer_id=wallet.stripe_customer_id,
                        )

                        if payment_intent.status == 'succeeded':
                            transaction_obj = wallet.deposit(amount)
                            transaction_obj.stripe_payment_intent_id = payment_intent.id
                            transaction_obj.save()
                            return Response({
                                'detail': 'Deposit successful',
                                'transaction': TransactionSerializer(
                                    transaction_obj
                                ).data,
                            })
                        elif payment_intent.status in [
                            'requires_action', 'requires_confirmation'
                        ]:
                            return Response({
                                'requires_action': True,
                                'payment_intent_client_secret': (
                                    payment_intent.client_secret
                                ),
                                'payment_intent_id': payment_intent.id,
                            })
                        elif payment_intent.status == 'requires_payment_method':
                            transaction_obj = TransactionModel.objects.create(
                                wallet=wallet,
                                amount=amount,
                                transaction_type=TransactionModel.DEPOSIT,
                                status=TransactionModel.PENDING,
                                stripe_payment_intent_id=payment_intent.id,
                            )
                            return Response({
                                'detail': 'Payment method required',
                                'payment_intent_id': payment_intent.id,
                                'client_secret': payment_intent.client_secret,
                                'transaction_id': str(transaction_obj.id),
                            })
                        else:
                            return Response({
                                'detail': (
                                    f'Payment not completed. '
                                    f'Status: {payment_intent.status}'
                                ),
                                'payment_intent_id': payment_intent.id,
                            }, status=status.HTTP_400_BAD_REQUEST)
                except ValueError as e:
                    return Response(
                        {'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST
                    )

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
                    transaction_obj = wallet.withdraw(amount)
                    return Response({
                        'detail': 'Withdrawal successful',
                        'transaction': TransactionSerializer(transaction_obj).data,
                    })
            except ValueError as e:
                return Response(
                    {'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST
                )

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
                recipient_wallet = get_object_or_404(Wallet, id=recipient_id)
                with transaction.atomic():
                    transaction_obj = wallet.transfer(recipient_wallet, amount)
                    return Response({
                        'detail': 'Transfer successful',
                        'transaction': TransactionSerializer(transaction_obj).data,
                    })
            except ValueError as e:
                return Response(
                    {'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST
                )
            except Wallet.DoesNotExist:
                return Response(
                    {'detail': 'Recipient wallet not found'},
                    status=status.HTTP_404_NOT_FOUND,
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def transactions(self, request, pk=None):
        """Get all transactions for the wallet."""
        wallet = self.get_object()
        transactions_qs = TransactionModel.objects.filter(
            wallet=wallet
        ).order_by('-created_at')

        transaction_type = request.query_params.get('type')
        if transaction_type:
            transactions_qs = transactions_qs.filter(
                transaction_type=transaction_type
            )

        page = self.paginate_queryset(transactions_qs)
        if page is not None:
            serializer = TransactionSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = TransactionSerializer(transactions_qs, many=True)
        return Response(serializer.data)


class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only viewset for viewing transaction history."""

    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return the authenticated user's completed/failed transactions."""
        return TransactionModel.objects.filter(
            wallet__user=self.request.user,
            status__in=['completed', 'failed'],
        ).order_by('-created_at')

    @action(detail=False, methods=['get'], url_path='wallettransactions')
    def wallet_and_transactions(self, request):
        """Returns the user's wallet and transaction history."""
        try:
            wallet = Wallet.objects.get(user=request.user)
        except Wallet.DoesNotExist:
            return Response(
                {'detail': 'Wallet not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        transactions_qs = TransactionModel.objects.filter(
            wallet=wallet, status__in=['completed', 'failed']
        ).order_by('-created_at')

        return Response({
            'wallet': WalletUserSerializer(wallet).data,
            'transactions': TransactionSerializer(transactions_qs, many=True).data,
        })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def verify_stripe_payment(request, session_id):
    """Verify a Stripe checkout session payment status."""
    if not session_id:
        return Response(
            {'error': 'Session ID not provided.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        session = stripe.checkout.Session.retrieve(session_id)
        payment_status = session.get('payment_status')

        if payment_status == 'paid':
            return Response({
                'payment_successful': True,
                'session_id': session_id,
                'customer_email': session.get('customer_email'),
                'amount_total': session.get('amount_total'),
                'currency': session.get('currency'),
            })
        return Response({
            'payment_successful': False,
            'payment_status': payment_status,
        })
    except stripe.error.InvalidRequestError as e:
        return Response(
            {'error': str(e)}, status=status.HTTP_400_BAD_REQUEST
        )
