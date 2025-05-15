from django.utils import timezone
from django.db.models import Sum, When, Value, Case, FloatField
from django.db.models.functions import Cast
from label_printer.models import LabelPrintLog
from products.models import Product
import logging
import requests
from django.conf import settings
from django.db.models import OuterRef, Subquery

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
    today = timezone.now().date()
    start = timezone.make_aware(timezone.datetime.combine(today, timezone.datetime.min.time()))

    # Вычисляем объем как в предыдущих функциях
    has_barcode_subquery = Product.objects.filter(barcode=OuterRef('barcode')).values('pk')[:1]
    has_barcode15_subquery = Product.objects.filter(barcode15=OuterRef('barcode')).values('pk')[:1]

    stats = (
        LabelPrintLog.objects
        .filter(printed_at__gte=start)
        .annotate(
            has_barcode=Subquery(has_barcode_subquery),
            has_barcode15=Subquery(has_barcode15_subquery),
        )
        .annotate(
            computed_volume=Case(
                When(has_barcode__isnull=False, then=Value(1.0)),
                When(has_barcode15__isnull=False, then=Value(1.5)),
                default=Value(None),
                output_field=FloatField()
            )
        )
        .values('product_name')
        .annotate(volume_sum=Sum('volume'))
        .order_by('-volume_sum')
    )

    if not stats:
        send_telegram_message("Сегодня не было напечатано ни одной этикетки.")
        return

    message_lines = ["📊 Статистика за сегодня (в литрах):\n"]
    for row in stats:
        product = row['product_name']
        volume = round(row['volume_sum'] or 0, 2)
        message_lines.append(f"• {product}: {volume} л.")

    message = "\n".join(message_lines)
    return(message)