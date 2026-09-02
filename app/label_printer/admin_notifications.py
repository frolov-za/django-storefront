from django.contrib import admin, messages
from django.shortcuts import redirect
from django.urls import path

from label_printer.models_notifications import EmailRecipient, EmailServerConfig
from label_printer.services.email import send_test_email as send_test_email_service


class EmailRecipientInline(admin.TabularInline):
    model = EmailRecipient
    extra = 1
    fields = ("email", "is_active")


@admin.register(EmailServerConfig)
class EmailServerConfigAdmin(admin.ModelAdmin):
    change_form_template = "admin/test_email_button.html"

    list_display = (
        "name",
        "smtp_host",
        "smtp_port",
        "is_active",
        "recipients_count",
        "updated_at",
    )

    inlines = [EmailRecipientInline]

    fieldsets = (
        (
            "Основное",
            {
                "fields": (
                    "name",
                    "is_active",
                )
            },
        ),
        (
            "SMTP (отправка)",
            {
                "fields": (
                    "smtp_host",
                    "smtp_port",
                    "smtp_use_tls",
                    "smtp_use_ssl",
                    "smtp_username",
                    "smtp_password",
                    "from_email",
                )
            },
        ),
    )

    @admin.display(description="Получателей")
    def recipients_count(self, obj):
        return obj.recipients.filter(is_active=True).count()

    def get_urls(self):
        custom_urls = [
            path(
                "<int:object_id>/send-test-email/",
                self.admin_site.admin_view(self.send_test_email),
                name="label_printer_emailserverconfig_send_test",
            ),
        ]

        return custom_urls + super().get_urls()

    def send_test_email(self, request, object_id):
        result = send_test_email_service(object_id)

        if result["success"]:
            messages.success(
                request,
                f"Тестовое письмо отправлено: {result['detail']}",
            )
        else:
            messages.error(
                request,
                f"Ошибка отправки: {result['detail']}",
            )

        return redirect("..")

    def change_view(
        self,
        request,
        object_id,
        form_url="",
        extra_context=None,
    ):
        extra_context = extra_context or {}
        extra_context["show_test_email_button"] = True

        return super().change_view(
            request,
            object_id,
            form_url,
            extra_context=extra_context,
        )