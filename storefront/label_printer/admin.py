# label_printer/admin.py
from django.contrib import admin
from django.urls import path
from django.http import HttpResponse
from django.utils.html import format_html
from .models import Printer, Font, LabelConfig
from .utils.zpl_utils import generate_preview


@admin.register(Printer)
class PrinterAdmin(admin.ModelAdmin):
    list_display = ('name', 'ip_address', 'port')
    search_fields = ('name', 'ip_address')

@admin.register(Font)
class FontAdmin(admin.ModelAdmin):
    list_display = ('name', 'printer_code', 'width_dot', 'height_dot')
    search_fields = ('name', 'printer_code')

@admin.register(LabelConfig)
class LabelConfigAdmin(admin.ModelAdmin):
    list_display = ('name', 'printer', 'width_mm', 'height_mm')
    search_fields = ('name', 'printer__name')
    readonly_fields = ('label_preview',)
    
    fieldsets = (
        ('Основные настройки', {
            'fields': ('name', 'printer', 'width_mm', 'height_mm', 'dpi')
        }),
        ('Текст продукта', {
            'fields': ('product_font', 'product_max_width_mm', 
                      'product_pos_x_mm', 'product_pos_y_mm')
        }),
        ('Штрих-код', {
            'fields': ('barcode_type', 'barcode_height_mm',
                      'barcode_pos_x_mm', 'barcode_pos_y_mm')
        }),
        ('Дата', {
            'fields': ('date_font', 'date_rotation', 
                      'date_pos_x_mm', 'date_pos_y_mm')
        }),
        ('Предпросмотр', {
            'fields': ('label_preview',)
        })
    )

    def label_preview(self, obj):
        return format_html(
            '<a class="button" href="preview/{}/">Сгенерировать предпросмотр</a>'
            '<div style="margin-top:10px;">'
            '<img src="/admin/label_printer/labelconfig/{}/preview/" style="border:1px solid #ddd;padding:5px;"/>'
            '</div>',
            obj.id, obj.id
        )
    label_preview.short_description = "Предварительный просмотр"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('preview/<int:pk>/', self.admin_site.admin_view(self.preview_view))
        ]
        return custom_urls + urls

    def preview_view(self, request, pk):
        try:
            config = LabelConfig.objects.get(pk=pk)
            image_bytes = generate_preview(config)
            return HttpResponse(image_bytes, content_type="image/png")
        except Exception as e:
            error_msg = f"Ошибка генерации: {str(e)}"
            return HttpResponse(error_msg, status=500)