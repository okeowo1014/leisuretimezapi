from django.db.models import Q
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from admin_api.permissions import IsAdminStaff
from admin_api.serializers.personalised_bookings import (
    AdminPBAssignSerializer, AdminPBDetailSerializer,
    AdminPBListSerializer, AdminPBMessageCreateSerializer,
    AdminPBMessageSerializer, AdminPBTransitionSerializer,
    AdminPBUpdateSerializer,
)
from admin_api.serializers.bookings import AdminBookingActivityLogSerializer
from index.models import (
    BookingActivityLog, CustomUser, PersonalisedBooking,
    PersonalisedBookingMessage,
)


class AdminPBListView(generics.ListAPIView):
    permission_classes = [IsAdminStaff]
    serializer_class = AdminPBListSerializer

    def get_queryset(self):
        qs = PersonalisedBooking.objects.select_related(
            'user', 'event_type', 'assigned_to',
        ).order_by('-created_at')

        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(
                Q(user__email__icontains=search) |
                Q(user__firstname__icontains=search) |
                Q(user__lastname__icontains=search) |
                Q(event_name__icontains=search)
            )

        pb_status = self.request.query_params.get('status')
        if pb_status:
            qs = qs.filter(status=pb_status)

        event_type = self.request.query_params.get('event_type')
        if event_type:
            qs = qs.filter(event_type_id=event_type)

        assigned_to = self.request.query_params.get('assigned_to')
        if assigned_to:
            qs = qs.filter(assigned_to_id=assigned_to)

        date_from = self.request.query_params.get('date_from')
        if date_from:
            qs = qs.filter(created_at__date__gte=date_from)

        date_to = self.request.query_params.get('date_to')
        if date_to:
            qs = qs.filter(created_at__date__lte=date_to)

        return qs


class AdminPBDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAdminStaff]
    queryset = PersonalisedBooking.objects.select_related(
        'user', 'event_type', 'cruise_type', 'assigned_to',
    ).prefetch_related(
        'booking_services__service', 'messages__sender', 'attachments__uploaded_by',
    )

    def get_serializer_class(self):
        if self.request.method in ('PATCH', 'PUT'):
            return AdminPBUpdateSerializer
        return AdminPBDetailSerializer


class AdminPBTransitionView(APIView):
    permission_classes = [IsAdminStaff]

    def post(self, request, pk):
        try:
            pb = PersonalisedBooking.objects.get(pk=pk)
        except PersonalisedBooking.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = AdminPBTransitionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        old_status = pb.status
        new_status = data['new_status']

        if not pb.can_transition_to(new_status):
            allowed = pb.ALLOWED_STATUS_TRANSITIONS.get(pb.status, [])
            return Response(
                {
                    'error': f"Cannot transition from '{pb.status}' to '{new_status}'.",
                    'allowed_transitions': allowed,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        kwargs = {}
        if new_status == 'rejected' and data.get('reason'):
            kwargs['rejection_reason'] = data['reason']
        elif new_status == 'cancelled' and data.get('reason'):
            kwargs['cancellation_reason'] = data['reason']

        pb.transition_to(new_status, **kwargs)

        BookingActivityLog.objects.create(
            booking=pb,
            action='status_changed',
            actor=request.user,
            description=f'Status changed from {old_status} to {new_status}',
            old_value=old_status,
            new_value=new_status,
        )

        return Response({
            'detail': f'Status changed to {new_status}.',
            'old_status': old_status,
            'new_status': new_status,
        })


class AdminPBAssignView(APIView):
    permission_classes = [IsAdminStaff]

    def post(self, request, pk):
        try:
            pb = PersonalisedBooking.objects.get(pk=pk)
        except PersonalisedBooking.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = AdminPBAssignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            staff_user = CustomUser.objects.get(
                pk=serializer.validated_data['assigned_to'],
                is_staff=True,
            )
        except CustomUser.DoesNotExist:
            return Response(
                {'error': 'Staff user not found'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        old_assigned = pb.assigned_to.email if pb.assigned_to else 'unassigned'
        pb.assigned_to = staff_user
        pb.save(update_fields=['assigned_to', 'updated_at'])

        BookingActivityLog.objects.create(
            booking=pb,
            action='assigned',
            actor=request.user,
            description=f'Assigned to {staff_user.email}',
            old_value=old_assigned,
            new_value=staff_user.email,
        )

        return Response({'detail': f'Assigned to {staff_user.email}'})


class AdminPBMessagesView(generics.ListAPIView):
    permission_classes = [IsAdminStaff]
    serializer_class = AdminPBMessageSerializer

    def get_queryset(self):
        return PersonalisedBookingMessage.objects.filter(
            booking_id=self.kwargs['pk']
        ).select_related('sender').order_by('created_at')


class AdminPBMessageCreateView(APIView):
    permission_classes = [IsAdminStaff]

    def post(self, request, pk):
        try:
            pb = PersonalisedBooking.objects.get(pk=pk)
        except PersonalisedBooking.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = AdminPBMessageCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        msg = PersonalisedBookingMessage.objects.create(
            booking=pb,
            sender=request.user,
            message=serializer.validated_data['message'],
        )

        BookingActivityLog.objects.create(
            booking=pb,
            action='message_sent',
            actor=request.user,
            description='Admin sent a message',
        )

        return Response(
            AdminPBMessageSerializer(msg).data,
            status=status.HTTP_201_CREATED,
        )


class AdminPBActivityView(generics.ListAPIView):
    permission_classes = [IsAdminStaff]
    serializer_class = AdminBookingActivityLogSerializer

    def get_queryset(self):
        return BookingActivityLog.objects.filter(
            booking_id=self.kwargs['pk']
        ).select_related('actor').order_by('-created_at')
