from django.contrib import admin
from .models import Service


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("title", "service_type", "price", "business_unit", "is_available")
    list_filter = ("business_unit", "is_available")
    search_fields = ("title", "service_type", "description")
