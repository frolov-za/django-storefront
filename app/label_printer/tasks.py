from celery import shared_task
from .utils.telegram import send_daily_volume_stats, send_telegram_message
from datetime import timedelta, datetime
from django.utils import timezone
from .models import LabelPrintLog, EmailServerConfig
import shutil
import requests
import os
import zipfile
import smtplib
import tempfile
from email.message import EmailMessage
from email.utils import formatdate
from django.conf import settings
from pathlib import Path
import time

BASE_DIR = Path(settings.BASE_DIR)
STATIC_DIR = BASE_DIR / 'static'
MEDIA_DIR = BASE_DIR / 'media'
DB_PATH = BASE_DIR / 'db.sqlite3'
BACKUP_DIR = BASE_DIR / 'backups'
LOCAL_BACKUP_DIR = Path('/tmp/backup')
# Исключения — не попадут в архив при полном бэкапе
EXCLUDE_DIRS = {'backups', '__pycache__', '.git', '.venv', 'env', 'venv', 'node_modules'}

RU_MONTHS = {
    1: 'января', 2: 'февраля', 3: 'марта', 4: 'апреля',
    5: 'мая', 6: 'июня', 7: 'июля', 8: 'августа',
    9: 'сентября', 10: 'октября', 11: 'ноября', 12: 'декабря',
}


def format_ru_date(dt):
    return f"{dt.day} {RU_MONTHS[dt.month]} {dt.year}"

def format_short_date(dt):
    return dt.strftime('%d.%m.%y')

# ---------------------------------------------------------------------------
# Существующие таски (без изменений)
# ---------------------------------------------------------------------------

@shared_task
def send_daily_stats_to_telegram():
    message = send_daily_volume_stats()
    success = send_telegram_message(message)
    if success:
        return "Сообщение отправлено"
    else:
        return "Не удалось отправить сообщение"


@shared_task
def delete_old_label_logs():
    threshold_date = timezone.now() - timedelta(days=90)
    deleted_count, _ = LabelPrintLog.objects.filter(printed_at__lt=threshold_date).delete()
    return f"Удалено {deleted_count} записей старше 90 дней"


# ---------------------------------------------------------------------------
# Общая логика создания архива
# ---------------------------------------------------------------------------

def _create_full_backup_zip(dest_dir: Path) -> Path:
    """Создаёт полный zip-архив проекта в указанной директории и возвращает путь к нему."""
    now = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    zip_name = f'full_backup_{now}.zip'
    dest_dir.mkdir(parents=True, exist_ok=True)
    zip_path = dest_dir / zip_name

    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(BASE_DIR):
            rel_dir = os.path.relpath(root, BASE_DIR)
            if any(part in EXCLUDE_DIRS for part in Path(rel_dir).parts):
                continue
            for file in files:
                file_path = Path(root) / file
                arcname = file_path.relative_to(BASE_DIR)
                zipf.write(file_path, arcname=arcname)

    return zip_path


# ---------------------------------------------------------------------------
# Таск 1: локальный бэкап в /tmp/backup
# ---------------------------------------------------------------------------

@shared_task
def full_backup_local():
    try:
        zip_path = _create_full_backup_zip(LOCAL_BACKUP_DIR)
    except Exception as e:
        return f"Local backup failed: {str(e)}"

    return f"Local backup created: {zip_path.name}"


# ---------------------------------------------------------------------------
# Таск 2: бэкап в Telegram
# ---------------------------------------------------------------------------

@shared_task
def full_backup_to_telegram():
    with tempfile.TemporaryDirectory() as tmp:
        try:
            zip_path = _create_full_backup_zip(Path(tmp))
        except Exception as e:
            return f"Backup creation failed: {str(e)}"

        try:
            send_zip_to_telegram(zip_path)
        except Exception as e:
            return f"Backup created but failed to send to Telegram: {str(e)}"

    return f"Backup sent to Telegram: {zip_path.name}"


def send_zip_to_telegram(zip_path: Path, max_retries: int = 3, backoff_seconds: int = 5):
    url = f'https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendDocument'
    last_error = None

    for attempt in range(1, max_retries + 1):
        try:
            with zip_path.open('rb') as f:
                response = requests.post(
                    url,
                    data={'chat_id': settings.TELEGRAM_CHAT_ID, 'caption': f'📦 Резервная копия: {zip_path.name}'},
                    files={'document': f},
                    timeout=60,
                )
            response.raise_for_status()
            return
        except Exception as e:
            last_error = e
            if attempt < max_retries:
                time.sleep(backoff_seconds * attempt)

    raise last_error


# ---------------------------------------------------------------------------
# Таск 3: бэкап на почту
# ---------------------------------------------------------------------------

@shared_task
def full_backup_to_email():
    config = EmailServerConfig.objects.filter(is_active=True).first()
    if not config:
        return "Нет активной конфигурации email-сервера"

    recipients = config.get_recipients_list()
    if not recipients:
        return "Не указаны получатели логов"

    with tempfile.TemporaryDirectory() as tmp:
        try:
            zip_path = _create_full_backup_zip(Path(tmp))
        except Exception as e:
            _try_send_error_email(config, recipients, str(e))
            return f"Backup creation failed: {str(e)}"

        backup_date = datetime.now()
        size_mb = zip_path.stat().st_size / (1024 * 1024)
        subject = f"Резервная копия StoreFront {format_short_date(backup_date)}"

        html_body, plain_body = build_backup_email_html(
            backup_name=zip_path.name,
            size_mb=size_mb,
            backup_date=backup_date,
            status='success',
        )

        try:
            _send_email(
                config, subject, plain_body, recipients,
                html_body=html_body,
                attachment_path=str(zip_path),
            )
        except Exception as e:
            return f"Backup created but failed to send email: {str(e)}"

    return f"Backup email sent to {', '.join(recipients)}"


def _try_send_error_email(config, recipients, error_detail):
    backup_date = datetime.now()
    subject = f"Резервная копия StoreFront {format_short_date(backup_date)} — ошибка"
    html_body, plain_body = build_backup_email_html(
        backup_name='—',
        size_mb=0,
        backup_date=backup_date,
        status='error',
        error_detail=error_detail,
    )
    try:
        _send_email(config, subject, plain_body, recipients, html_body=html_body)
    except Exception:
        pass  # не хотим падать при ошибке отправки письма об ошибке


# ---------------------------------------------------------------------------
# Отправка логов на почту
# ---------------------------------------------------------------------------

@shared_task
def send_logs_via_email():
    config = EmailServerConfig.objects.filter(is_active=True).first()
    if not config:
        return "Нет активной конфигурации email-сервера"

    recipients = config.get_recipients_list()
    if not recipients:
        return "Не указаны получатели логов"

    since = timezone.now() - timedelta(days=1)
    logs = LabelPrintLog.objects.filter(printed_at__gte=since).order_by('-printed_at')
    lines = [f"{log.printed_at:%Y-%m-%d %H:%M:%S} — {log}" for log in logs]
    body = "\n".join(lines) if lines else "Логов за последние сутки нет."

    try:
        _send_email(config, f"Логи печати за {timezone.now():%Y-%m-%d}", body, recipients)
    except Exception as e:
        return f"Не удалось отправить логи по почте: {str(e)}"

    return f"Логи отправлены на {', '.join(recipients)}"


# ---------------------------------------------------------------------------
# Тестовое письмо (вызывается синхронно из админки)
# ---------------------------------------------------------------------------

def send_test_email_task(config_id):
    try:
        config = EmailServerConfig.objects.get(id=config_id)
        recipients = config.get_recipients_list() or [config.smtp_username]
        _send_email(config, 'Тестовое письмо', 'Это тестовое письмо для проверки SMTP-настроек.', recipients)
        return {'success': True, 'detail': ', '.join(recipients)}
    except Exception as e:
        return {'success': False, 'detail': str(e)}


# ---------------------------------------------------------------------------
# Общие вспомогательные функции отправки почты
# ---------------------------------------------------------------------------

def _send_email(config, subject, plain_body, recipients, html_body=None, attachment_path=None):
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = config.from_email
    msg['To'] = ', '.join(recipients)
    msg['Date'] = formatdate(localtime=True)
    msg.set_content(plain_body)

    if html_body:
        msg.add_alternative(html_body, subtype='html')

    if attachment_path:
        with open(attachment_path, 'rb') as f:
            msg.add_attachment(
                f.read(),
                maintype='application',
                subtype='zip',
                filename=os.path.basename(attachment_path),
            )

    if config.smtp_use_ssl:
        server = smtplib.SMTP_SSL(config.smtp_host, config.smtp_port, timeout=30)
    else:
        server = smtplib.SMTP(config.smtp_host, config.smtp_port, timeout=30)
        if config.smtp_use_tls:
            server.starttls()
    try:
        server.login(config.smtp_username, config.smtp_password)
        server.send_message(msg)
    finally:
        server.quit()


def build_backup_email_html(backup_name, size_mb, backup_date, status='success', error_detail=None):
    date_str = format_ru_date(backup_date)
    time_str = backup_date.strftime('%H:%M:%S')

    if status == 'success':
        status_color = '#22c55e'
        status_bg = '#f0fdf4'
        status_text = 'Бэкап успешно создан'
        icon = '✓'
    else:
        status_color = '#ef4444'
        status_bg = '#fef2f2'
        status_text = 'Ошибка при создании бэкапа'
        icon = '✕'

    error_block = ''
    if error_detail:
        error_block = f"""
        <tr>
          <td style="padding: 0 32px 24px 32px;">
            <div style="background-color: #fef2f2; border: 1px solid #fecaca; border-radius: 8px; padding: 16px; font-family: 'Courier New', monospace; font-size: 13px; color: #991b1b; word-break: break-all;">
              {error_detail}
            </div>
          </td>
        </tr>
        """

    html = f"""\
<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 0; background-color: #f4f4f7; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color: #f4f4f7; padding: 40px 16px;">
    <tr>
      <td align="center">
        <table role="presentation" width="600" cellpadding="0" cellspacing="0" style="max-width: 600px; width: 100%; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.08);">

          <tr>
            <td style="background-color: #1e293b; padding: 32px; text-align: center;">
              <div style="width: 48px; height: 48px; background-color: #334155; border-radius: 10px; display: inline-block; line-height: 48px; text-align: center; margin-bottom: 12px;">
                <span style="font-size: 24px;">📦</span>
              </div>
              <div style="color: #ffffff; font-size: 20px; font-weight: 600; margin-top: 8px;">StoreFront</div>
              <div style="color: #94a3b8; font-size: 13px; margin-top: 4px;">Резервное копирование</div>
            </td>
          </tr>

          <tr>
            <td style="padding: 32px 32px 0 32px;">
              <table role="presentation" cellpadding="0" cellspacing="0" style="background-color: {status_bg}; border-radius: 8px; width: 100%;">
                <tr>
                  <td style="padding: 16px 20px;">
                    <table role="presentation" cellpadding="0" cellspacing="0">
                      <tr>
                        <td style="width: 32px; height: 32px; background-color: {status_color}; border-radius: 50%; text-align: center; vertical-align: middle;">
                          <span style="color: #ffffff; font-size: 16px; font-weight: bold; line-height: 32px;">{icon}</span>
                        </td>
                        <td style="padding-left: 12px; color: {status_color}; font-size: 15px; font-weight: 600;">
                          {status_text}
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <tr>
            <td style="padding: 24px 32px;">
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-collapse: collapse;">
                <tr>
                  <td style="padding: 12px 0; border-bottom: 1px solid #e2e8f0; color: #64748b; font-size: 13px;">Имя файла</td>
                  <td style="padding: 12px 0; border-bottom: 1px solid #e2e8f0; color: #1e293b; font-size: 13px; font-weight: 500; text-align: right;">{backup_name}</td>
                </tr>
                <tr>
                  <td style="padding: 12px 0; border-bottom: 1px solid #e2e8f0; color: #64748b; font-size: 13px;">Дата</td>
                  <td style="padding: 12px 0; border-bottom: 1px solid #e2e8f0; color: #1e293b; font-size: 13px; font-weight: 500; text-align: right;">{date_str}</td>
                </tr>
                <tr>
                  <td style="padding: 12px 0; border-bottom: 1px solid #e2e8f0; color: #64748b; font-size: 13px;">Время</td>
                  <td style="padding: 12px 0; border-bottom: 1px solid #e2e8f0; color: #1e293b; font-size: 13px; font-weight: 500; text-align: right;">{time_str}</td>
                </tr>
                <tr>
                  <td style="padding: 12px 0; color: #64748b; font-size: 13px;">Размер архива</td>
                  <td style="padding: 12px 0; color: #1e293b; font-size: 13px; font-weight: 500; text-align: right;">{size_mb:.2f} МБ</td>
                </tr>
              </table>
            </td>
          </tr>

          {error_block}

          <tr>
            <td style="padding: 24px 32px 32px 32px; border-top: 1px solid #e2e8f0;">
              <p style="margin: 0; color: #94a3b8; font-size: 12px; line-height: 1.5; text-align: center;">
                Автоматическое уведомление системы резервного копирования StoreFront.<br>
                Не отвечайте на это письмо.
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""
    plain_text = (
        f"{status_text}\n\n"
        f"Имя файла: {backup_name}\n"
        f"Дата: {date_str}\n"
        f"Время: {time_str}\n"
        f"Размер: {size_mb:.2f} МБ\n"
        + (f"\nОшибка: {error_detail}\n" if error_detail else '')
    )
    return html, plain_text