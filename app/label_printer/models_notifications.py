from django.core.validators import EmailValidator
from django.db import models


class EmailServerConfig(models.Model):
    name = models.CharField(max_length=100, unique=True, default="default")
    is_active = models.BooleanField(default=True)
    smtp_host = models.CharField(max_length=255, default="smtp.gmail.com")
    smtp_port = models.PositiveIntegerField(default=587)
    smtp_use_tls = models.BooleanField(default=True)
    smtp_use_ssl = models.BooleanField(default=False)
    smtp_username = models.CharField(max_length=255)
    smtp_password = models.CharField(max_length=255)
    from_email = models.EmailField()
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Настройка почтового сервера"
        verbose_name_plural = "Настройки почтового сервера"

    def __str__(self):
        return f"{self.name} ({self.smtp_host})"

    def get_recipients_list(self):
        return list(self.recipients.filter(is_active=True).values_list("email", flat=True))


class EmailRecipient(models.Model):
    config = models.ForeignKey(EmailServerConfig, related_name="recipients", on_delete=models.CASCADE)
    email = models.EmailField(validators=[EmailValidator()])
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Получатель логов"
        verbose_name_plural = "Получатели логов"
        unique_together = ("config", "email")

    def __str__(self):
        return self.email
