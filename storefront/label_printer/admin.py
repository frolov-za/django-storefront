from django.contrib import admin
from django.contrib import messages
from django.urls import reverse, path
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.utils.html import format_html
from .models import Printer, LabelTemplate

@admin.register(Printer)
class PrinterAdmin(admin.ModelAdmin):
    list_display = ('name', 'connection_type', 'active_status', 'device_info')
    list_filter = ('is_active', 'connection_type')
    change_list_template = 'admin/printer_change_list.html'
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
        ('DPI Settings', {
            'fields': ('printer_dpi',),
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
        return obj.device_path or "-"
    device_info.short_description = 'Device Info'

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_find_usb_button'] = True
        return super().changelist_view(request, extra_context=extra_context)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('find_usb/',
                self.admin_site.admin_view(self.find_usb_printers_action),
                name='find_usb_printers'
            ),
            path('found_usb_printers/',
                self.admin_site.admin_view(self.found_usb_printers_view),
                name='found_usb_printers'
            ),
        ]
        return custom_urls + urls

    def find_usb_printers_action(self, request):
        found = Printer.find_usb_printers()
        
        if not found:
            messages.warning(request, "USB-принтеры не найдены")
            return HttpResponseRedirect(reverse('admin:label_printer_printer_changelist'))
        
        request.session['found_printers'] = found
        return HttpResponseRedirect(reverse('admin:found_usb_printers'))

    def found_usb_printers_view(self, request):
        context = {
            'title': "Найденные USB-принтеры",
            'found_printers': request.session.get('found_printers', []),
            'opts': self.model._meta,
        }
        return TemplateResponse(
            request,
            'admin/found_usb_printers.html',
            context
        )


@admin.register(LabelTemplate)
class LabelTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'barcode_height', 'date_format')