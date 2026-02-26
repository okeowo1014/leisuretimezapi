from django.db.models import Q
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from admin_api.permissions import IsAdminStaff
from index.models import CustomUser, Notification
from index.serializers import NotificationSerializer


class AdminNotificationListView(generics.ListAPIView):
    permission_classes = [IsAdminStaff]
    serializer_class = NotificationSerializer

    def get_queryset(self):
        qs = Notification.objects.select_related('user').order_by('-created_at')

        user_id = self.request.query_params.get('user')
        if user_id:
            qs = qs.filter(user_id=user_id)

        notification_type = self.request.query_params.get('type')
        if notification_type:
            qs = qs.filter(notification_type=notification_type)

        is_read = self.request.query_params.get('is_read')
        if is_read is not None:
            qs = qs.filter(is_read=is_read.lower() == 'true')

        return qs


class AdminSendNotificationView(APIView):
    permission_classes = [IsAdminStaff]

    def post(self, request):
        user_ids = request.data.get('user_ids', [])
        send_to_all = request.data.get('send_to_all', False)
        title = request.data.get('title')
        message = request.data.get('message')
        notification_type = request.data.get('notification_type', 'system')

        if not title or not message:
            return Response(
                {'error': 'title and message are required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if send_to_all:
            users = CustomUser.objects.filter(is_active=True)
        elif user_ids:
            users = CustomUser.objects.filter(pk__in=user_ids)
        else:
            return Response(
                {'error': 'Provide user_ids or set send_to_all to true.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        notifications = [
            Notification(
                user=user,
                notification_type=notification_type,
                title=title,
                message=message,
            )
            for user in users
        ]
        Notification.objects.bulk_create(notifications)

        return Response({
            'detail': f'Sent {len(notifications)} notification(s).',
            'count': len(notifications),
        })
