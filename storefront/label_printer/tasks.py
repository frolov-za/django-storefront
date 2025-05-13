from celery import shared_task
from .utils.telegram import send_daily_volume_stats, send_telegram_message

@shared_task
def send_daily_stats_to_telegram():
    message = send_daily_volume_stats()
    send_telegram_message(message)

