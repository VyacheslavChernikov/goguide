from django.contrib import admin
from .models import Appointment


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ("id", "business_unit", "service", "client_name", "start_at", "end_at", "is_confirmed")
    list_filter = ("business_unit", "service", "is_confirmed")
    search_fields = ("client_name", "client_phone", "client_email")
