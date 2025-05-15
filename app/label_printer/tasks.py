from celery import shared_task
from .utils.telegram import send_daily_volume_stats, send_telegram_message
from datetime import timedelta, datetime
from django.utils import timezone
from .models import LabelPrintLog
import shutil
import requests
import os
import zipfile
from django.conf import settings
from pathlib import Path

BASE_DIR = Path(settings.BASE_DIR)
STATIC_DIR = BASE_DIR / 'static'
MEDIA_DIR = BASE_DIR / 'media'
DB_PATH = BASE_DIR / 'db.sqlite3'
BACKUP_DIR = BASE_DIR / 'backups'
# Исключения — не попадут в архив при полном бэкапе
EXCLUDE_DIRS = {'backups', '__pycache__', '.git', '.venv', 'env', 'venv', 'node_modules'}


@shared_task
def send_daily_stats_to_telegram():
    message = send_daily_volume_stats()
    success = send_telegram_message(message)   
    if success:
        return(f"Сообщение отправлено")
    else:
        return(f"Не удалось отправить сообщение")


@shared_task
def delete_old_label_logs():
    threshold_date = timezone.now() - timedelta(days=90)
    deleted_count, _ = LabelPrintLog.objects.filter(printed_at__lt=threshold_date).delete()
    return f"Удалено {deleted_count} записей старше 90 дней"

@shared_task
def backup_and_send_to_telegram():
    now = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    backup_name = f'backup_{now}'
    temp_backup_path = os.path.join(BACKUP_DIR, backup_name)

    # Шаг 1: Создание временной папки для бэкапа
    os.makedirs(temp_backup_path, exist_ok=True)
    shutil.copytree(STATIC_DIR, os.path.join(temp_backup_path, 'static'))
    shutil.copytree(MEDIA_DIR, os.path.join(temp_backup_path, 'media'))
    shutil.copy(DB_PATH, os.path.join(temp_backup_path, 'db.sqlite3'))

    # Шаг 2: Архивация
    zip_path = os.path.join(BACKUP_DIR, f'{backup_name}.zip')
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as backup_zip:
        for foldername, subfolders, filenames in os.walk(temp_backup_path):
            for filename in filenames:
                file_path = os.path.join(foldername, filename)
                arcname = os.path.relpath(file_path, temp_backup_path)
                backup_zip.write(file_path, arcname)

    # Шаг 3: Отправка в Telegram
    try:
        with open(zip_path, 'rb') as f:
            response = requests.post(
                url=f'https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendDocument',
                data={'chat_id': settings.TELEGRAM_CHAT_ID, 'caption': f'📦 Резервная копия: {backup_name}'},
                files={'document': f}
            )
        response.raise_for_status()
    except Exception as e:
        return f"Backup created but failed to send to Telegram: {str(e)}"

    # Шаг 4: Очистка временной папки
    shutil.rmtree(temp_backup_path)

    return f"Backup {backup_name}.zip created and sent to Telegram."


@shared_task
def full_project_backup():
    now = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    zip_name = f'full_backup_{now}.zip'
    zip_path = BACKUP_DIR / zip_name

    # Убедиться, что директория для бэкапов существует
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    # Создать zip-архив всего проекта
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(BASE_DIR):
            # Относительный путь от BASE_DIR
            rel_dir = os.path.relpath(root, BASE_DIR)

            # Пропуск исключённых директорий
            if any(part in EXCLUDE_DIRS for part in Path(rel_dir).parts):
                continue

            for file in files:
                file_path = Path(root) / file
                arcname = file_path.relative_to(BASE_DIR)
                zipf.write(file_path, arcname=arcname)

    # Отправка в Telegram
    send_zip_to_telegram(zip_path)

    return f"Full project backup complete and sent: {zip_name}"

def send_zip_to_telegram(zip_path: Path):
    url = f'https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendDocument'
    with zip_path.open('rb') as f:
        response = requests.post(
            url,
            data={'chat_id': settings.TELEGRAM_CHAT_ID, 'caption': f'Full Django project backup: {zip_path.name}'},
            files={'document': f}
        )
    response.raise_for_status()