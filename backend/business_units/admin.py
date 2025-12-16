from django.contrib import admin
from .models import BusinessUnit


@admin.register(BusinessUnit)
class BusinessUnitAdmin(admin.ModelAdmin):
    list_display = ("name", "business_type", "slug", "api_key")
    list_filter = ("business_type",)
    prepopulated_fields = {"slug": ("name",)}
