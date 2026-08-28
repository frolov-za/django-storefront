from datetime import datetime, timedelta

from django.db.models import ExpressionWrapper, F, FloatField, Sum
from django.utils import timezone

from label_printer.models import LabelPrintLog


def build_daily_volume_message(today=None):
    today = today or timezone.localdate()
    start = timezone.make_aware(datetime.combine(today, datetime.min.time()))
    stats = LabelPrintLog.objects.filter(printed_at__gte=start).values("product_name").annotate(
        volume_sum=Sum(ExpressionWrapper(F("volume") / 1000.0, output_field=FloatField()))
    ).order_by("-volume_sum")

    if not stats:
        return f"Сегодня {today:%Y-%m-%d} не было напечатано ни одной этикетки."

    total_volume = sum(row["volume_sum"] or 0 for row in stats)
    lines = [f"📊 Статистика за сегодня {today:%Y-%m-%d} (в литрах):\n"]
    lines.extend(
        f"• {row['product_name']}: {round(row['volume_sum'] or 0, 2)} л." for row in stats
    )
    lines.append(f"\n🔹 Итого: {round(total_volume, 2)} л.")
    return "\n".join(lines)


def build_print_log_message():
    since = timezone.now() - timedelta(days=1)
    logs = LabelPrintLog.objects.filter(printed_at__gte=since).order_by("-printed_at")
    return "\n".join(f"{log.printed_at:%Y-%m-%d %H:%M:%S} — {log}" for log in logs) or (
        "Логов за последние сутки нет."
    )
