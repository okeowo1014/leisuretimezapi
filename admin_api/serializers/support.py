from rest_framework import serializers

from index.models import SupportMessage, SupportTicket


class AdminSupportMessageSerializer(serializers.ModelSerializer):
    sender_email = serializers.CharField(source='sender.email', read_only=True)
    sender_name = serializers.SerializerMethodField()
    is_staff = serializers.BooleanField(source='sender.is_staff', read_only=True)

    class Meta:
        model = SupportMessage
        fields = (
            'id', 'sender', 'sender_email', 'sender_name',
            'is_staff', 'message', 'created_at',
        )

    def get_sender_name(self, obj):
        return f"{obj.sender.firstname} {obj.sender.lastname}"


class AdminSupportTicketListSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_name = serializers.SerializerMethodField()
    message_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = SupportTicket
        fields = (
            'id', 'user', 'user_email', 'user_name', 'subject',
            'status', 'priority', 'message_count', 'created_at', 'updated_at',
        )

    def get_user_name(self, obj):
        return f"{obj.user.firstname} {obj.user.lastname}"


class AdminSupportTicketDetailSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_name = serializers.SerializerMethodField()
    messages = AdminSupportMessageSerializer(many=True, read_only=True)

    class Meta:
        model = SupportTicket
        fields = (
            'id', 'user', 'user_email', 'user_name', 'subject',
            'status', 'priority', 'messages', 'created_at', 'updated_at',
        )

    def get_user_name(self, obj):
        return f"{obj.user.firstname} {obj.user.lastname}"


class AdminSupportTicketUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportTicket
        fields = ('status', 'priority')


class AdminSupportReplySerializer(serializers.Serializer):
    message = serializers.CharField()
