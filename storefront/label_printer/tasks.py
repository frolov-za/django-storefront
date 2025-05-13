from celery import shared_task
from .utils.telegram import send_daily_volume_stats, send_telegram_message
from datetime import timedelta
from django.utils import timezone
from .models import LabelPrintLog

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