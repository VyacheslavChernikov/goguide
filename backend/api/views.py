from rest_framework import generics
from rest_framework.permissions import AllowAny

from business_units.models import BusinessUnit
from services.models import Service
from appointments.models import Appointment

from .serializers import BusinessUnitSerializer, ServiceSerializer, AppointmentSerializer


# =============================
#      HOTELS
# =============================
class BusinessUnitListAPIView(generics.ListAPIView):
    queryset = BusinessUnit.objects.all()
    serializer_class = BusinessUnitSerializer
    permission_classes = [AllowAny]   # 👈 ОТКРЫЛИ ЭНДПОИНТ ДЛЯ БОТА


# =============================
#      ROOMS
# =============================
class ServiceListAPIView(generics.ListAPIView):
    serializer_class = ServiceSerializer
    permission_classes = [AllowAny]   # 👈 ОТКРЫЛИ ДЛЯ БОТА

    def get_queryset(self):
        """
        Возвращает только свободные комнаты.
        Возможна фильтрация по отелю: /api/rooms/?hotel=1
        """
        qs = Service.objects.filter(is_available=True)

        unit_id = self.request.query_params.get("business_unit")
        if unit_id:
            qs = qs.filter(business_unit_id=unit_id)

        return qs


# =============================
#      ROOM DETAIL
# =============================
class ServiceDetailAPIView(generics.RetrieveAPIView):
    """Получение конкретной услуги по ID"""
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    permission_classes = [AllowAny]


# =============================
#      BOOKING (POST)
# =============================
class AppointmentCreateAPIView(generics.CreateAPIView):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    permission_classes = [AllowAny]   # 👈 чтобы бот мог создавать бронь
