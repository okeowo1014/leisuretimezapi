from django.db.models import Count, Q
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from admin_api.permissions import IsAdminStaff
from admin_api.serializers.support import (
    AdminSupportReplySerializer, AdminSupportTicketDetailSerializer,
    AdminSupportTicketListSerializer, AdminSupportTicketUpdateSerializer,
)
from index.models import SupportMessage, SupportTicket


class AdminSupportTicketListView(generics.ListAPIView):
    permission_classes = [IsAdminStaff]
    serializer_class = AdminSupportTicketListSerializer

    def get_queryset(self):
        qs = SupportTicket.objects.select_related('user').annotate(
            message_count=Count('messages'),
        ).order_by('-created_at')

        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(
                Q(subject__icontains=search) |
                Q(user__email__icontains=search)
            )

        ticket_status = self.request.query_params.get('status')
        if ticket_status:
            qs = qs.filter(status=ticket_status)

        priority = self.request.query_params.get('priority')
        if priority:
            qs = qs.filter(priority=priority)

        return qs


class AdminSupportTicketDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAdminStaff]
    queryset = SupportTicket.objects.select_related('user').prefetch_related('messages__sender')

    def get_serializer_class(self):
        if self.request.method in ('PATCH', 'PUT'):
            return AdminSupportTicketUpdateSerializer
        return AdminSupportTicketDetailSerializer


class AdminSupportReplyView(APIView):
    permission_classes = [IsAdminStaff]

    def post(self, request, pk):
        try:
            ticket = SupportTicket.objects.get(pk=pk)
        except SupportTicket.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = AdminSupportReplySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        msg = SupportMessage.objects.create(
            ticket=ticket,
            sender=request.user,
            message=serializer.validated_data['message'],
        )

        # Auto-move to in_progress if open
        if ticket.status == 'open':
            ticket.status = 'in_progress'
            ticket.save(update_fields=['status', 'updated_at'])

        from admin_api.serializers.support import AdminSupportMessageSerializer
        return Response(
            AdminSupportMessageSerializer(msg).data,
            status=status.HTTP_201_CREATED,
        )


class AdminSupportCloseView(APIView):
    permission_classes = [IsAdminStaff]

    def post(self, request, pk):
        try:
            ticket = SupportTicket.objects.get(pk=pk)
        except SupportTicket.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

        ticket.status = 'closed'
        ticket.save(update_fields=['status', 'updated_at'])
        return Response({'detail': f'Ticket #{pk} closed.'})
