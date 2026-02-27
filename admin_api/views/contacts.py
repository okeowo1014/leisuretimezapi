from django.db.models import Q
from rest_framework import generics

from admin_api.permissions import IsAdminStaff
from index.models import Contact
from index.serializers import ContactSerializer


class AdminContactListView(generics.ListAPIView):
    permission_classes = [IsAdminStaff]
    serializer_class = ContactSerializer

    def get_queryset(self):
        qs = Contact.objects.order_by('-created_at')

        contact_status = self.request.query_params.get('status')
        if contact_status:
            qs = qs.filter(status=contact_status)

        search = self.request.query_params.get('search')
        if search:
            qs = qs.filter(
                Q(fullname__icontains=search) |
                Q(email__icontains=search) |
                Q(subject__icontains=search)
            )

        return qs


class AdminContactUpdateView(generics.UpdateAPIView):
    permission_classes = [IsAdminStaff]
    serializer_class = ContactSerializer
    queryset = Contact.objects.all()
