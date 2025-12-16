from rest_framework import serializers
from business_units.models import BusinessUnit
from services.models import Service
from appointments.models import Appointment


class BusinessUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessUnit
        fields = ["id", "name", "slug", "address", "description", "photo_url"]


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ["id", "business_unit", "title", "service_type", "price", "is_available", "description", "photo_url"]


class AppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = [
            "id",
            "business_unit",
            "service",
            "client_name",
            "client_phone",
            "client_email",
            "start_at",
            "end_at",
            "total_price",
            "is_confirmed",
        ]
