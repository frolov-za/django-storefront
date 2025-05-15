# Создать Cron-Job
# crontab -e
# 0 3 1 * * /usr/bin/python3 /home/ubuntu/backup_and_send.py >> /var/log/django_backup.log 2>&1

import os
import tarfile
import datetime
import glob
import requests

# === НАСТРОЙКИ ===
BASE_DIR = './'  # Путь к проекту на хосте
BACKUP_DIR = './backups'
DB_FILENAME = 'db.sqlite3'  # или используем дамп ниже
TOKEN = 'token'
CHAT_ID = '376816770'
KEEP_BACKUPS = 2

# === СОЗДАНИЕ АРХИВА ===
date_str = datetime.datetime.now().strftime('%d-%m-%y_%H:%M')
archive_name = f'django_backup_{date_str}.tar.gz'
archive_path = os.path.join(BACKUP_DIR, archive_name)

os.makedirs(BACKUP_DIR, exist_ok=True)

with tarfile.open(archive_path, 'w:gz') as tar:
    tar.add(BASE_DIR, arcname=os.path.basename(BASE_DIR))

# === ОТПРАВКА В TELEGRAM ===
with open(archive_path, 'rb') as f:
    response = requests.post(
        f'https://api.telegram.org/bot{TOKEN}/sendDocument',
        data={'chat_id': CHAT_ID, 'caption': f'Бэкап Django проекта: {date_str}'},
        files={'document': f}
    )

print('Файл отправлен:', response.status_code == 200)

# === УДАЛЕНИЕ СТАРЫХ БЭКАПОВ ===
backups = sorted(glob.glob(os.path.join(BACKUP_DIR, 'django_backup_*.tar.gz')))
if len(backups) > KEEP_BACKUPS:
    for old_file in backups[:-KEEP_BACKUPS]:
        os.remove(old_file)
        print(f'Удалён старый бэкап: {old_file}')
