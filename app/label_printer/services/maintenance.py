import tempfile
from datetime import datetime, timedelta
from pathlib import Path

from django.utils import timezone

from label_printer.integrations.telegram import send_document, send_message
from label_printer.models import EmailServerConfig, LabelPrintLog
from label_printer.services.backup import create_backup_archive
from label_printer.services.email import build_backup_email, send_email
from label_printer.services.notifications import build_daily_volume_message, build_print_log_message


LOCAL_BACKUP_DIRECTORY = Path("/tmp/backup")


def send_daily_statistics():
    return "Сообщение отправлено" if send_message(build_daily_volume_message()) else "Не удалось отправить сообщение"


def remove_old_print_logs(days=90):
    threshold = timezone.now() - timedelta(days=days)
    deleted_count, _ = LabelPrintLog.objects.filter(printed_at__lt=threshold).delete()
    return f"Удалено {deleted_count} записей старше {days} дней"


def create_local_backup():
    try:
        archive = create_backup_archive(LOCAL_BACKUP_DIRECTORY)
    except Exception as error:
        return f"Local backup failed: {error}"
    return f"Local backup created: {archive.name}"


def send_backup_to_telegram():
    with tempfile.TemporaryDirectory() as temporary_directory:
        try:
            archive = create_backup_archive(Path(temporary_directory))
            send_document(archive)
        except Exception as error:
            return f"Backup failed: {error}"
    return f"Backup sent to Telegram: {archive.name}"


def send_backup_to_email():
    config, recipients, error = _active_email_delivery()
    if error:
        return error
    with tempfile.TemporaryDirectory() as temporary_directory:
        try:
            archive = create_backup_archive(Path(temporary_directory))
            backup_date = datetime.now()
            size_mb = archive.stat().st_size / (1024 * 1024)
            html, plain = build_backup_email(archive.name, size_mb, backup_date)
            send_email(
                config,
                f"Резервная копия StoreFront {backup_date:%d.%m.%y}",
                plain,
                recipients,
                html_body=html,
                attachment_path=archive,
            )
        except Exception as error:
            return f"Backup email failed: {error}"
    return f"Backup email sent to {', '.join(recipients)}"


def send_print_logs_by_email():
    config, recipients, error = _active_email_delivery()
    if error:
        return error
    try:
        send_email(
            config,
            f"Логи печати за {timezone.localdate():%Y-%m-%d}",
            build_print_log_message(),
            recipients,
        )
    except Exception as error:
        return f"Не удалось отправить логи по почте: {error}"
    return f"Логи отправлены на {', '.join(recipients)}"


def _active_email_delivery():
    config = EmailServerConfig.objects.filter(is_active=True).first()
    if not config:
        return None, None, "Нет активной конфигурации email-сервера"
    recipients = config.get_recipients_list()
    if not recipients:
        return None, None, "Не указаны получатели логов"
    return config, recipients, None
