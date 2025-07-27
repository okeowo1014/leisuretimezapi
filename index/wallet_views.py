from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from django.shortcuts import get_object_or_404
import stripe
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .models import Wallet, Transaction
from .serializers import (
    WalletSerializer, TransactionSerializer, 
    DepositSerializer, WalletUserSerializer, WithdrawalSerializer, TransferSerializer
)
from index.wallet_utils import create_stripe_customer, create_payment_intent, create_payout,create_checkout_session
stripe.api_key = 'sk_test_51RJjB32KJEgBmA6Bs0Zhd2qh8ElLfOcg1bLi718romNjC54V4WTbr4eNhOKf3ySOK0AyjBECzUsFxpvsKsNvljY000b2rmr9JE'


# class WalletViewSet(viewsets.ModelViewSet):
#     serializer_class = WalletSerializer
#     permission_classes = [permissions.IsAuthenticated]
    
#     def get_queryset(self):
#         """Return only the authenticated user's wallet."""
#         return Wallet.objects.filter(user=self.request.user)
    
#     def create(self, serializer):
#         print('perform_create called')
#         print('user is',self.request.user)
#         Wallet.objects.all().delete()
#         print(Wallet.objects.filter(user=self.request.user).exists())

#         """Create a wallet for the authenticated user."""
#         if Wallet.objects.filter(user=self.request.user).exists():
#             print('user already exists',self.request.user)
#             return Response(
#                 {"detail": "You already have a wallet"}, 
#                 status=status.HTTP_400_BAD_REQUEST
#             )
#         print('user is',self.request.user)
            
#         # Create Stripe customer if needed
#         stripe_customer_id = None
#         if self.request.user.email:
#             stripe_customer_id = create_stripe_customer(self.request.user)
#         print('Before save - is_active should be True by default')
#         wallet = serializer.save(user=self.request.user, stripe_customer_id=stripe_customer_id)
#         print(f'After save - is_active is: {wallet.is_active}')
#         # serializer.save(user=self.request.user, stripe_customer_id=stripe_customer_id)
class WalletViewSet(viewsets.ModelViewSet):
    serializer_class = WalletSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return only the authenticated user's wallet."""
        print('get_queryset called')
        print('user is', self.request.user)
        print('Wallet.objects.filter(user=self.request.user)', Wallet.objects.filter(user=self.request.user))
        return Wallet.objects.filter(user=self.request.user)
    
    def create(self, request, *args, **kwargs):
        """Override create method to handle wallet creation properly"""
        print('Create method called')
        print('user is', self.request.user)
        # Wallet.objects.all().delete()
        
        # Check if user already has a wallet
        if Wallet.objects.filter(user=self.request.user).exists():
            print('user already has a wallet:', self.request.user)
            return Response(
                {"detail": "You already have a wallet"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create a new wallet
        print('Creating wallet for user:', self.request.user)
        
        # Create Stripe customer if needed
        stripe_customer_id = None
        if self.request.user.email:
            stripe_customer_id = create_stripe_customer(self.request.user)
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        wallet = serializer.save(
            user=self.request.user,
            stripe_customer_id=stripe_customer_id,
            is_active=True  # Explicitly set is_active to True
        )
        
        # Get the serializer for the response
        response_serializer = self.get_serializer(wallet)
        headers = self.get_success_headers(serializer.data)
        
        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )
    
    # We don't need perform_create anymore as we're overriding create
    # def perform_create(self, serializer):
    #     """This method is not used anymore"""
    #     pass    
    # @action(detail=True, methods=['post'])
    # def deposit(self, request, pk=None):
    #     """Add funds to wallet using Stripe Checkout."""
    #     wallet = self.get_object()
    #     serializer = DepositSerializer(data=request.data)
        
    #     if serializer.is_valid():
    #         amount = serializer.validated_data['amount']
            
    #         # Check if specific payment method is provided or if using Checkout
    #         payment_method_id = serializer.validated_data.get('payment_method_id')
    #         success_url = serializer.validated_data.get('success_url')
    #         cancel_url = serializer.validated_data.get('cancel_url')
            
    #         # Get base URL from request
    #         base_url = request.build_absolute_uri('/').rstrip('/')
            
    #         # Use Stripe Checkout if success/cancel URLs are provided or no payment method
    #         if (success_url and cancel_url) or not payment_method_id:
    #             # Use provided URLs or defaults
    #             success_url = success_url or f"{base_url}/wallet/deposit/success"
    #             cancel_url = cancel_url or f"{base_url}/wallet/deposit/cancel"
                
    #             try:
    #                 # Create a pending transaction
    #                 transaction_obj = Transaction.objects.create(
    #                     wallet=wallet,
    #                     amount=amount,
    #                     transaction_type=Transaction.DEPOSIT,
    #                     status=Transaction.PENDING
    #                 )
                    
    #                 # Create Stripe Checkout session
    #                 checkout_session = create_checkout_session(
    #                     amount=amount,
    #                     customer_id=wallet.stripe_customer_id,
    #                     success_url=success_url,
    #                     cancel_url=cancel_url,
    #                     metadata={
    #                         'transaction_id': str(transaction_obj.id),
    #                         'wallet_id': str(wallet.id),
    #                         'user_id': str(wallet.user.id)
    #                     }
    #                 )
                    
    #                 # Update transaction with session ID
    #                 transaction_obj.stripe_payment_intent_id = checkout_session.id
    #                 transaction_obj.save()
                    
    #                 # Return checkout URL
    #                 return Response({
    #                     'checkout_url': checkout_session.url,
    #                     'session_id': checkout_session.id,
    #                     'transaction_id': str(transaction_obj.id)
    #                 })
                    
    #             except ValueError as e:
    #                 return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
            
    #         # If specifically requesting payment intent (legacy flow)
    #         else:
    #             try:
    #                 with transaction.atomic():
    #                     # Create Stripe payment intent
    #                     payment_intent = create_payment_intent(
    #                         amount=amount,
    #                         payment_method_id=payment_method_id,
    #                         customer_id=wallet.stripe_customer_id
    #                     )
                        
    #                     # Check if payment was successful
    #                     if payment_intent.status == 'succeeded':
    #                         # Add funds to wallet
    #                         transaction_obj = wallet.deposit(amount)
    #                         transaction_obj.stripe_payment_intent_id = payment_intent.id
    #                         transaction_obj.save()
                            
    #                         return Response({
    #                             'detail': 'Deposit successful',
    #                             'transaction': TransactionSerializer(transaction_obj).data
    #                         })
    #                     elif payment_intent.status == 'requires_action' or payment_intent.status == 'requires_confirmation':
    #                         # Return client secret for handling authentication on client side
    #                         return Response({
    #                             'requires_action': True,
    #                             'payment_intent_client_secret': payment_intent.client_secret,
    #                             'payment_intent_id': payment_intent.id
    #                         })
    #                     elif payment_intent.status == 'requires_payment_method':
    #                         # Create a transaction in pending state
    #                         transaction_obj = Transaction.objects.create(
    #                             wallet=wallet,
    #                             amount=amount,
    #                             transaction_type=Transaction.DEPOSIT,
    #                             status=Transaction.PENDING,
    #                             stripe_payment_intent_id=payment_intent.id
    #                         )
                            
    #                         # Return information needed for the client to complete payment
    #                         return Response({
    #                             'detail': 'Payment method required',
    #                             'payment_intent_id': payment_intent.id,
    #                             'client_secret': payment_intent.client_secret,
    #                             'transaction_id': str(transaction_obj.id)
    #                         })
    #                     else:
    #                         return Response({
    #                             'detail': f'Payment not completed. Status: {payment_intent.status}',
    #                             'payment_intent_id': payment_intent.id
    #                         }, status=status.HTTP_400_BAD_REQUEST)
                            
    #             except ValueError as e:
    #                 return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    @action(detail=False, methods=['post'], url_path='deposit')
    def deposit(self, request):
        """Add funds to the authenticated user's wallet using Stripe Checkout."""
        user = request.user
        wallet = Wallet.objects.filter(user=user).first()

        if not wallet:
            return Response({'detail': 'Wallet not found for user'}, status=status.HTTP_404_NOT_FOUND)

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
                    transaction_obj = Transaction.objects.create(
                        wallet=wallet,
                        amount=amount,
                        transaction_type=Transaction.DEPOSIT,
                        status=Transaction.PENDING
                    )

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

                    transaction_obj.stripe_payment_intent_id = checkout_session.id
                    transaction_obj.save()

                    return Response({
                        'checkout_url': checkout_session.url,
                        'session_id': checkout_session.id,
                        'transaction_id': str(transaction_obj.id)
                    })

                except ValueError as e:
                    return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

            else:
                try:
                    with transaction.atomic():
                        payment_intent = create_payment_intent(
                            amount=amount,
                            payment_method_id=payment_method_id,
                            customer_id=wallet.stripe_customer_id
                        )

                        if payment_intent.status == 'succeeded':
                            transaction_obj = wallet.deposit(amount)
                            transaction_obj.stripe_payment_intent_id = payment_intent.id
                            transaction_obj.save()

                            return Response({
                                'detail': 'Deposit successful',
                                'transaction': TransactionSerializer(transaction_obj).data
                            })
                        elif payment_intent.status in ['requires_action', 'requires_confirmation']:
                            return Response({
                                'requires_action': True,
                                'payment_intent_client_secret': payment_intent.client_secret,
                                'payment_intent_id': payment_intent.id
                            })
                        elif payment_intent.status == 'requires_payment_method':
                            transaction_obj = Transaction.objects.create(
                                wallet=wallet,
                                amount=amount,
                                transaction_type=Transaction.DEPOSIT,
                                status=Transaction.PENDING,
                                stripe_payment_intent_id=payment_intent.id
                            )
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
            wallet__user=self.request.user,status__in=['completed','failed']
        ).order_by('-created_at')

    @action(detail=False, methods=['get'], url_path='wallettransactions')
    def wallet_and_transactions(self, request):
        """Returns the user's wallet and transaction history."""
        try:
            wallet = Wallet.objects.get(user=request.user)
        except Wallet.DoesNotExist:
            return Response({'detail': 'Wallet not found.'}, status=404)

        transactions = Transaction.objects.filter(wallet=wallet,status__in=['completed','failed']).order_by('-created_at')

        wallet_data = WalletUserSerializer(wallet).data
        transaction_data = TransactionSerializer(transactions, many=True).data

        return Response({
            'wallet': wallet_data,
            'transactions': transaction_data
        })


# class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
#     serializer_class = TransactionSerializer
#     permission_classes = [permissions.IsAuthenticated]
    
#     def get_queryset(self):
#         """Return only the authenticated user's transactions."""
#         return Transaction.objects.filter(
#             wallet__user=self.request.user
#         ).order_by('-created_at')
    
#     @action(detail=True, methods=['get'])
#     def check_status(self, request, pk=None):
#         """Check the status of a transaction with Stripe if applicable."""
#         transaction = self.get_object()
        
#         if transaction.stripe_payment_intent_id:
#             # Here you would check with Stripe API for the current status
#             # This is a simplified example
#             return Response({
#                 'transaction': TransactionSerializer(transaction).data,
#                 'stripe_status': 'Would fetch from Stripe API'
#             })
        
#         return Response({
#             'transaction': TransactionSerializer(transaction).data,
#         })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def verify_stripe_payment(request,session_id):
    # session_id = request.GET.get('session_id')

    if not session_id:
        return Response({'error': 'Session ID not provided.'}, status=400)

    try:
        session = stripe.checkout.Session.retrieve(session_id)
        payment_status = session.get('payment_status')
        customer_email = session.get('customer_email')

        if payment_status == 'paid':
            return Response({
                'payment_successful': True,
                'session_id': session_id,
                'customer_email': customer_email,
                'amount_total': session.get('amount_total'),
                'currency': session.get('currency'),
            })
        else:
            return Response({'payment_successful': False, 'payment_status': payment_status})
    except stripe.error.InvalidRequestError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)



# class WalletViewSet(viewsets.ModelViewSet):
#     serializer_class = WalletSerializer
#     permission_classes = [permissions.IsAuthenticated]
    
#     def get_queryset(self):
#         """Return only the authenticated user's wallet."""
#         return Wallet.objects.filter(user=self.request.user)
    
#     def perform_create(self, serializer):
#         """Create a wallet for the authenticated user."""
#         if Wallet.objects.filter(user=self.request.user).exists():
#             return Response(
#                 {"detail": "You already have a wallet"}, 
#                 status=status.HTTP_400_BAD_REQUEST
#             )
            
#         # Create Stripe customer if needed
#         stripe_customer_id = None
#         if self.request.user.email:
#             stripe_customer_id = create_stripe_customer(self.request.user)
            
#         serializer.save(user=self.request.user, stripe_customer_id=stripe_customer_id)
    
#     @action(detail=True, methods=['post'])
#     def deposit(self, request, pk=None):
#         """Add funds to wallet using Stripe."""
#         wallet = self.get_object()
#         serializer = DepositSerializer(data=request.data)
        
#         if serializer.is_valid():
#             amount = serializer.validated_data['amount']
#             payment_method_id = serializer.validated_data['payment_method_id']
            
#             try:
#                 with transaction.atomic():
#                     # Create Stripe payment intent
#                     payment_intent = create_payment_intent(
#                         amount=amount,
#                         customer_id=wallet.stripe_customer_id,
#                     )
                    
#                     # Check if payment was successful
#                     if payment_intent.status == 'succeeded':
#                         # Add funds to wallet
#                         transaction_obj = wallet.deposit(amount)
#                         transaction_obj.stripe_payment_intent_id = payment_intent.id
#                         transaction_obj.save()
                        
#                         return Response({
#                             'detail': 'Deposit successful',
#                             'transaction': TransactionSerializer(transaction_obj).data
#                         })
#                     else:
#                         return Response({
#                             'detail': f'Payment not completed. Status: {payment_intent.status}',
#                             'payment_intent_id': payment_intent.id
#                         }, status=status.HTTP_400_BAD_REQUEST)
                        
#             except ValueError as e:
#                 return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
#     @action(detail=True, methods=['post'])
#     def withdraw(self, request, pk=None):
#         """Withdraw funds from wallet."""
#         wallet = self.get_object()
#         serializer = WithdrawalSerializer(data=request.data)
        
#         if serializer.is_valid():
#             amount = serializer.validated_data['amount']
            
#             try:
#                 with transaction.atomic():
#                     # Process withdrawal
#                     transaction_obj = wallet.withdraw(amount)
                    
#                     # If you're implementing actual withdrawal to a bank account,
#                     # you would handle Stripe payout here
#                     # payout = create_payout(amount, wallet.user.stripe_account_id)
#                     # transaction_obj.stripe_payment_intent_id = payout.id
#                     # transaction_obj.save()
                    
#                     return Response({
#                         'detail': 'Withdrawal successful',
#                         'transaction': TransactionSerializer(transaction_obj).data
#                     })
                    
#             except ValueError as e:
#                 return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
#     @action(detail=True, methods=['post'])
#     def transfer(self, request, pk=None):
#         """Transfer funds to another user's wallet."""
#         wallet = self.get_object()
#         serializer = TransferSerializer(data=request.data)
        
#         if serializer.is_valid():
#             recipient_id = serializer.validated_data['recipient_id']
#             amount = serializer.validated_data['amount']
            
#             try:
#                 # Find recipient's wallet
#                 recipient_wallet = get_object_or_404(Wallet, id=recipient_id)
                
#                 with transaction.atomic():
#                     # Process transfer
#                     transaction_obj = wallet.transfer(recipient_wallet, amount)
                    
#                     return Response({
#                         'detail': 'Transfer successful',
#                         'transaction': TransactionSerializer(transaction_obj).data
#                     })
                    
#             except ValueError as e:
#                 return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
#             except Wallet.DoesNotExist:
#                 return Response(
#                     {'detail': 'Recipient wallet not found'}, 
#                     status=status.HTTP_404_NOT_FOUND
#                 )
        
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#     @action(detail=True, methods=['get'])
#     def transactions(self, request, pk=None):
#         """Get all transactions for the wallet."""
#         wallet = self.get_object()
#         transactions = Transaction.objects.filter(wallet=wallet).order_by('-created_at')
        
#         # Optional filtering
#         transaction_type = request.query_params.get('type')
#         if transaction_type:
#             transactions = transactions.filter(transaction_type=transaction_type)
            
#         page = self.paginate_queryset(transactions)
#         if page is not None:
#             serializer = TransactionSerializer(page, many=True)
#             return self.get_paginated_response(serializer.data)
            
#         serializer = TransactionSerializer(transactions, many=True)
#         return Response(serializer.data)


# class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
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