from django.contrib import admin
from .models import Printer, LabelTemplate

@admin.register(Printer)
class PrinterAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'port', 'is_active', 'label_template')
    list_filter = ('is_active',)

@admin.register(LabelTemplate)
class LabelTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'barcode_type', 'barcode_height', 'date_format')