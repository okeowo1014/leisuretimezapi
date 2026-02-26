from rest_framework import serializers

from index.models import CruiseType, EventType, ServiceCatalog


class AdminEventTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventType
        fields = '__all__'


class AdminCruiseTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CruiseType
        fields = '__all__'


class AdminServiceCatalogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceCatalog
        fields = '__all__'
