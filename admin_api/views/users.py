from django.db.models import Count, Q, Subquery, OuterRef, DecimalField
from django.db.models.functions import Coalesce
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView

from admin_api.permissions import IsAdminStaff
from admin_api.serializers.users import (
    AdminUserDetailSerializer, AdminUserListSerializer, AdminUserUpdateSerializer,
)
from admin_api.serializers.bookings import AdminBookingListSerializer
from admin_api.serializers.personalised_bookings import AdminPBListSerializer
from index.models import (
    Booking, CustomUser, PersonalisedBooking, Transaction, Wallet,
)


class AdminUserListView(generics.ListAPIView):
    permission_classes = [IsAdminStaff]
    serializer_class = AdminUserListSerializer

    def get_queryset(self):
        qs = CustomUser.objects.annotate(
            booking_count=Count('customerprofile__booking', distinct=True),
            wallet_balance=Coalesce(
                Subquery(
                    Wallet.objects.filter(user=OuterRef('pk')).values('balance')[:1]
                ),
                0,
                output_field=DecimalField(),
            ),
        ).order_by('-date_joined')

        # Search
        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(
                Q(email__icontains=search) |
                Q(firstname__icontains=search) |
                Q(lastname__icontains=search)
            )

        # Filters
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() == 'true')

        is_staff = self.request.query_params.get('is_staff')
        if is_staff is not None:
            qs = qs.filter(is_staff=is_staff.lower() == 'true')

        user_status = self.request.query_params.get('status')
        if user_status:
            qs = qs.filter(status=user_status)

        return qs


class AdminUserDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAdminStaff]
    queryset = CustomUser.objects.all()

    def get_serializer_class(self):
        if self.request.method in ('PATCH', 'PUT'):
            return AdminUserUpdateSerializer
        return AdminUserDetailSerializer


class AdminUserActivateView(APIView):
    permission_classes = [IsAdminStaff]

    def post(self, request, pk):
        try:
            user = CustomUser.objects.get(pk=pk)
        except CustomUser.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        user.is_active = True
        user.status = 'active'
        user.save(update_fields=['is_active', 'status'])
        return Response({'detail': f'User {user.email} activated.'})


class AdminUserDeactivateView(APIView):
    permission_classes = [IsAdminStaff]

    def post(self, request, pk):
        try:
            user = CustomUser.objects.get(pk=pk)
        except CustomUser.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        user.is_active = False
        user.status = 'deactivated'
        user.save(update_fields=['is_active', 'status'])
        return Response({'detail': f'User {user.email} deactivated.'})


class AdminUserBookingsView(generics.ListAPIView):
    permission_classes = [IsAdminStaff]
    serializer_class = AdminBookingListSerializer

    def get_queryset(self):
        return Booking.objects.filter(
            customer__user_id=self.kwargs['pk']
        ).order_by('-created_at')


class AdminUserPersonalisedBookingsView(generics.ListAPIView):
    permission_classes = [IsAdminStaff]
    serializer_class = AdminPBListSerializer

    def get_queryset(self):
        return PersonalisedBooking.objects.filter(
            user_id=self.kwargs['pk']
        ).select_related('event_type', 'assigned_to').order_by('-created_at')


class AdminUserTransactionsView(generics.ListAPIView):
    permission_classes = [IsAdminStaff]

    def get_queryset(self):
        return Transaction.objects.filter(
            wallet__user_id=self.kwargs['pk']
        ).order_by('-created_at')

    def list(self, request, *args, **kwargs):
        qs = self.get_queryset()
        from index.serializers import TransactionSerializer
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = TransactionSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = TransactionSerializer(qs, many=True)
        return Response(serializer.data)
