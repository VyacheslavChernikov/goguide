from django.contrib import admin
from .models import BusinessUnitUser


@admin.register(BusinessUnitUser)
class BusinessUnitUserAdmin(admin.ModelAdmin):
    list_display = ('user', 'business_unit')
    search_fields = ('user__username', 'business_unit__name')


admin.site.site_header = "Go&Guide — администрирование"
admin.site.site_title = "Go&Guide"
admin.site.index_title = "Панель управления"