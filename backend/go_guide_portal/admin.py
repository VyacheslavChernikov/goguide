from django.contrib import admin
from .models import BusinessUnitUser, KnowledgeFile, KnowledgeDocument


@admin.register(BusinessUnitUser)
class BusinessUnitUserAdmin(admin.ModelAdmin):
    list_display = ('user', 'business_unit')
    search_fields = ('user__username', 'business_unit__name')


@admin.register(KnowledgeFile)
class KnowledgeFileAdmin(admin.ModelAdmin):
    list_display = ('filename', 'business_unit', 'uploaded_at')
    search_fields = ('filename', 'business_unit__name')


@admin.register(KnowledgeDocument)
class KnowledgeDocumentAdmin(admin.ModelAdmin):
    list_display = ("original_name", "business_unit", "status", "uploaded_at")
    list_filter = ("status", "business_unit")
    search_fields = ("original_name",)


admin.site.site_header = "Go&Guide — администрирование"
admin.site.site_title = "Go&Guide"
admin.site.index_title = "Панель управления"