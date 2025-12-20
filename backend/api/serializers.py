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
        fields = [
            "id",
            "business_unit",
            "title",
            "service_type",
            "price",
            "is_available",
            "description",
            "photo_url",
            "tour_widget",
        ]


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
            "payment_status",
            "payment_provider",
            "payment_id",
            "paid_amount",
            "paid_at",
            "payment_meta",
        ]

    def validate(self, attrs):
        start = attrs.get("start_at")
        end = attrs.get("end_at")
        service = attrs.get("service")

        if start and end and end <= start:
            raise serializers.ValidationError("Окончание не может быть раньше или равно началу.")

        if service and start and end:
            qs = Appointment.objects.filter(
                service=service,
                business_unit=service.business_unit,
            ).exclude(status="cancelled")
            overlap = qs.filter(start_at__lt=end, end_at__gt=start).exists()
            if overlap:
                raise serializers.ValidationError("На выбранное время услуга уже занята.")

        return attrs

    def create(self, validated_data):
        # Публичные запросы: по умолчанию не подтверждаем.
        validated_data.setdefault("is_confirmed", False)
        return super().create(validated_data)
