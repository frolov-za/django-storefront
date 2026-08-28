import os
import smtplib
from datetime import datetime
from email.message import EmailMessage
from email.utils import formatdate

from django.utils import timezone

from label_printer.models import EmailServerConfig


RU_MONTHS = (
    "января", "февраля", "марта", "апреля", "мая", "июня",
    "июля", "августа", "сентября", "октября", "ноября", "декабря",
)


def send_email(config, subject, plain_body, recipients, *, html_body=None, attachment_path=None):
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = config.from_email
    message["To"] = ", ".join(recipients)
    message["Date"] = formatdate(localtime=True)
    message.set_content(plain_body)
    if html_body:
        message.add_alternative(html_body, subtype="html")
    if attachment_path:
        with open(attachment_path, "rb") as attachment:
            message.add_attachment(
                attachment.read(), maintype="application", subtype="zip",
                filename=os.path.basename(attachment_path),
            )

    server_class = smtplib.SMTP_SSL if config.smtp_use_ssl else smtplib.SMTP
    with server_class(config.smtp_host, config.smtp_port, timeout=30) as server:
        if not config.smtp_use_ssl and config.smtp_use_tls:
            server.starttls()
        server.login(config.smtp_username, config.smtp_password)
        server.send_message(message)


def send_test_email(config_id):
    try:
        config = EmailServerConfig.objects.get(pk=config_id)
        recipients = config.get_recipients_list() or [config.smtp_username]
        send_email(config, "Тестовое письмо", "Это тестовое письмо для проверки SMTP-настроек.", recipients)
    except Exception as error:
        return {"success": False, "detail": str(error)}
    return {"success": True, "detail": ", ".join(recipients)}


def build_backup_email(backup_name, size_mb, backup_date, *, error_detail=None):
    date_text = f"{backup_date.day} {RU_MONTHS[backup_date.month - 1]} {backup_date.year}"
    status = "Ошибка при создании бэкапа" if error_detail else "Бэкап успешно создан"
    plain_text = (
        f"{status}\n\nИмя файла: {backup_name}\nДата: {date_text}\n"
        f"Время: {backup_date:%H:%M:%S}\nРазмер: {size_mb:.2f} МБ\n"
    )
    if error_detail:
        plain_text += f"\nОшибка: {error_detail}\n"
    html = "<br>".join(plain_text.splitlines())
    return html, plain_text
