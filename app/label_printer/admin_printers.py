import logging

from django.contrib import admin, messages
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html

from label_printer.integrations.printers.preview import zpl_to_png
from label_printer.integrations.printers.zpl import generate_zpl
from label_printer.models_printers import LabelTemplate, Printer


logger = logging.getLogger(__name__)


@admin.register(Printer)
class PrinterAdmin(admin.ModelAdmin):
    list_display = ("name", "label_template", "connection_type", "status_indicator", "active_status", "device_info")
    list_filter = ("is_active", "connection_type")
    actions = ["make_active", "make_deactive"]
    change_list_template = "admin/printer_change_list.html"
    fieldsets = (
        (None, {"fields": ("name", "is_active", "label_template")} ),
        ("Network Settings", {"fields": ("address", "port")} ),
        ("USB Settings", {"fields": ("device_path",)}),
        ("DPI Settings", {"fields": ("printer_dpi",)}),
        ("Connection Type", {"fields": ("connection_type",)}),
    )

    @admin.display(description="Status")
    def active_status(self, obj):
        return "Active" if obj.is_active else "Inactive"

    @admin.display(description="Device Info")
    def device_info(self, obj):
        return f"{obj.address}:{obj.port}" if obj.connection_type == "network" else obj.device_path or "-"

    @admin.display(description="Доступен")
    def status_indicator(self, obj):
        available = obj.is_available()
        color = "gray" if available is None else ("green" if available else "red")
        return format_html('<span style="display:block;text-align:center;color:{};">●</span>', color)

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context["show_find_usb_button"] = True
        return super().changelist_view(request, extra_context=extra_context)

    def get_urls(self):
        return [
            path("find_usb/", self.admin_site.admin_view(self.find_usb_printers_action), name="find_usb_printers"),
            path("found_usb_printers/", self.admin_site.admin_view(self.found_usb_printers_view), name="found_usb_printers"),
        ] + super().get_urls()

    def find_usb_printers_action(self, request):
        found = Printer.find_usb_printers()
        if not found:
            messages.warning(request, "USB-принтеры не найдены")
            return HttpResponseRedirect(reverse("admin:label_printer_printer_changelist"))
        request.session["found_printers"] = found
        return HttpResponseRedirect(reverse("admin:found_usb_printers"))

    def found_usb_printers_view(self, request):
        return TemplateResponse(request, "admin/found_usb_printers.html", {
            "title": "Найденные USB-принтеры",
            "found_printers": request.session.get("found_printers", []),
            "opts": self.model._meta,
        })

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
    list_display = ("name", "label_hight", "label_wight", "product_name_via_pillow")
    change_form_template = "admin/labeltemplate.html"

    def get_urls(self):
        return [
            path("<int:pk>/preview/", self.admin_site.admin_view(self.preview_label), name="labeltemplate_preview"),
        ] + super().get_urls()

    def preview_label(self, request, pk):
        template = get_object_or_404(LabelTemplate, pk=pk)
        zpl = generate_zpl("Test Drink Очень Хорош", "2360825880688", template)
        try:
            return HttpResponse(zpl_to_png(zpl), content_type="image/png")
        except Exception as error:
            logger.exception("Unable to render label template preview")
            return HttpResponse(f"Ошибка рендеринга ZPL: {error}", status=500)
