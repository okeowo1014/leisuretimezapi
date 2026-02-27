from rest_framework import generics
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser

from admin_api.permissions import IsAdminStaff
from admin_api.serializers.lookups import (
    AdminCruiseTypeSerializer, AdminEventTypeSerializer,
    AdminServiceCatalogSerializer,
)
from index.models import CruiseType, EventType, ServiceCatalog


class AdminEventTypeListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAdminStaff]
    serializer_class = AdminEventTypeSerializer
    queryset = EventType.objects.order_by('position', 'name')


class AdminEventTypeDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAdminStaff]
    serializer_class = AdminEventTypeSerializer
    queryset = EventType.objects.all()


class AdminCruiseTypeListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAdminStaff]
    serializer_class = AdminCruiseTypeSerializer
    queryset = CruiseType.objects.order_by('position', 'name')


class AdminCruiseTypeDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAdminStaff]
    serializer_class = AdminCruiseTypeSerializer
    queryset = CruiseType.objects.all()


class AdminServiceCatalogListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAdminStaff]
    serializer_class = AdminServiceCatalogSerializer

    def get_queryset(self):
        qs = ServiceCatalog.objects.order_by('position', 'name')

        category = self.request.query_params.get('category')
        if category:
            qs = qs.filter(category=category)

        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() == 'true')

        return qs


class AdminServiceCatalogDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAdminStaff]
    serializer_class = AdminServiceCatalogSerializer
    queryset = ServiceCatalog.objects.all()
