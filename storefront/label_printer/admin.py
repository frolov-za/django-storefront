from django.contrib import admin
from .models import Printer, LabelTemplate

@admin.register(Printer)
class PrinterAdmin(admin.ModelAdmin):
    list_display = ('name', 'connection_type', 'active_status', 'device_info')
    list_filter = ('is_active', 'connection_type')
    fieldsets = (
        (None, {'fields': ('name', 'is_active', 'label_template')}),
        ('Network Settings', {
            'fields': ('address', 'port'),
            'classes': ('collapse',)
        }),
        ('USB Settings', {
            'fields': ('device_path',),
            'classes': ('collapse',)
        }),
        ('Connection Type', {
            'fields': ('connection_type',)
        })
    )

    def active_status(self, obj):
        return "Active" if obj.is_active else "Inactive"
    active_status.short_description = 'Status'

    def device_info(self, obj):
        if obj.connection_type == 'network':
            return f"{obj.address}:{obj.port}"
        return obj.device_path
    device_info.short_description = 'Device Info'

@admin.register(LabelTemplate)
class LabelTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'barcode_type', 'barcode_height', 'date_format')