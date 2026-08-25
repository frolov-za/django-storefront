from django.utils import timezone
from django.db.models.functions import Cast
from label_printer.models import LabelPrintLog
from products.models import Product
import logging
import requests
from django.conf import settings
from django.db.models import Sum, FloatField, F, ExpressionWrapper
from datetime import datetime

logger = logging.getLogger(__name__)

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': settings.TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'MarkDown',
    }
    try:
        response = requests.post(url, data=payload, timeout=5)
        response.raise_for_status()
        return True
    except requests.RequestException as e:
        logger.error(f"Ошибка отправки в Telegram: {e}")
        return False


def send_daily_volume_stats():
    today_tg = datetime.now().strftime('%Y-%m-%d')
    today = timezone.now().date()
    start = timezone.make_aware(datetime.combine(today, datetime.min.time()))

    stats = (
        LabelPrintLog.objects
        .filter(printed_at__gte=start)
        .values('product_name')
        .annotate(
            volume_sum=Sum(
                ExpressionWrapper(F('volume') / 1000.0, output_field=FloatField())
            )
        )
        .order_by('-volume_sum')
    )

    if not stats:
        return f"Сегодня {today_tg} не было напечатано ни одной этикетки."

    total_volume = sum(row['volume_sum'] or 0 for row in stats)

    message_lines = [f"📊 Статистика за сегодня {today_tg} (в литрах):\n"]
    for row in stats:
        product = row['product_name']
        volume = round(row['volume_sum'] or 0, 2)
        message_lines.append(f"• {product}: {volume} л.")

    message_lines.append(f"\n🔹 Итого: {round(total_volume, 2)} л.")

    return "\n".join(message_lines)