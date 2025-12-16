from django.urls import path
from .views import BusinessUnitListAPIView, ServiceListAPIView, ServiceDetailAPIView, AppointmentCreateAPIView

urlpatterns = [
    path("business-units/", BusinessUnitListAPIView.as_view(), name="businessunit-list"),
    path("services/", ServiceListAPIView.as_view(), name="service-list"),
    path("services/<int:pk>/", ServiceDetailAPIView.as_view(), name="service-detail"),
    path("appointments/", AppointmentCreateAPIView.as_view(), name="appointment-create"),
]
