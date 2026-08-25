from django.utils.html import format_html
from django.contrib import admin
from django.contrib import messages
from django.urls import reverse, path
from django.http import HttpResponseRedirect, HttpResponse
from django.template.response import TemplateResponse
from django.shortcuts import redirect
from django.urls import path
from django.contrib import messages
from .models import EmailServerConfig, EmailRecipient
from django.shortcuts import get_object_or_404, render
from .models import Printer, LabelTemplate
from .utils.zpl_generator import generate_zpl
from .utils.zpl_to_png import zpl_to_png


@admin.register(Printer)
class PrinterAdmin(admin.ModelAdmin):
    list_display = ('name', 'label_template', 'connection_type', 'status_indicator', 'active_status', 'device_info')
    list_filter = ('is_active', 'connection_type')
    actions = ['make_active', 'make_deactive']
    change_list_template = 'admin/printer_change_list.html'
    fieldsets = (
        (None, {'fields': ('name', 'is_active', 'label_template')}),
        ('Network Settings', {
            'fields': ('address', 'port'),
        }),
        ('USB Settings', {
            'fields': ('device_path',),
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

    def status_indicator(self, obj):
        available = obj.is_available()
        color = 'gray' if available is None else ('green' if available else 'red')
        return format_html(
            '<span style="display: block; text-align: center; color: {};">●</span>', color
        )         
    status_indicator.short_description = "Доступен"

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
    
    @admin.action(description="Активировать выбранные принтеры")
    def make_active(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"Активировано {updated} принтер(ов).", messages.SUCCESS)

    @admin.action(description="Деактивировать выбранные принтеры")
    def make_deactive(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"Деактивировано {updated} принтер(ов).", messages.SUCCESS)


@admin.register(LabelTemplate)
class LabelTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'label_hight', "label_wight" , 'product_name_via_pillow')
    change_form_template = 'admin/labeltemplate.html'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:pk>/preview/', self.admin_site.admin_view(self.preview_label), name='labeltemplate_preview'),
        ]
        return custom_urls + urls

    def preview_label(self, request, pk):
        print(f"✅ Вызван preview_label c pk={pk}")
        barcode="2360825880688"
        product_name="Test Drink Очень Хорош"

        template = get_object_or_404(LabelTemplate, pk=pk)
        zpl = generate_zpl(product_name, barcode, template)
        print("Отправка на генерацию PNG")
        try:
            print(zpl)
            png_data = zpl_to_png(zpl)
            return HttpResponse(png_data, content_type='image/png')
        except Exception as e:
            return HttpResponse(f"Ошибка рендеринга ZPL: {e}", status=500)

class EmailRecipientInline(admin.TabularInline):
    model = EmailRecipient
    extra = 1
    fields = ('email', 'is_active')


@admin.register(EmailServerConfig)
class EmailServerConfigAdmin(admin.ModelAdmin):
    list_display = ('name', 'smtp_host', 'smtp_port', 'is_active', 'recipients_count', 'updated_at')
    inlines = [EmailRecipientInline]
    fieldsets = (
        ('Основное', {'fields': ('name', 'is_active')}),
        ('SMTP (отправка)', {
            'fields': ('smtp_host', 'smtp_port', 'smtp_use_tls', 'smtp_use_ssl',
                       'smtp_username', 'smtp_password', 'from_email')
        }),
    )

    def recipients_count(self, obj):
        return obj.recipients.filter(is_active=True).count()
    recipients_count.short_description = 'Получателей'

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path('<int:object_id>/send-test-email/',
                 self.admin_site.admin_view(self.send_test_email),
                 name='emailserverconfig_send_test'),
        ]
        return custom + urls

    def send_test_email(self, request, object_id):
        from .tasks import send_test_email_task
        config = self.get_object(request, object_id)
        result = send_test_email_task(config.id)
        if result.get('success'):
            messages.success(request, f"Тестовое письмо отправлено: {result['detail']}")
        else:
            messages.error(request, f"Ошибка отправки: {result['detail']}")
        return redirect('..')

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_test_email_button'] = True
        return super().change_view(request, object_id, form_url, extra_context)
