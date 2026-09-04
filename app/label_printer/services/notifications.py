import logging
from datetime import datetime, timedelta

from django.db.models import ExpressionWrapper, F, FloatField, Sum
from django.utils import timezone

from label_printer.models import LabelPrintLog


logger = logging.getLogger(__name__)


def build_daily_volume_message(today=None):
    today = today or timezone.localdate()

    logger.debug(
        "Формирование дневной статистики печати за дату: %s",
        today,
    )

    try:
        start = timezone.make_aware(
            datetime.combine(today, datetime.min.time())
        )

        stats = (
            LabelPrintLog.objects
            .filter(printed_at__gte=start)
            .values("product_name")
            .annotate(
                volume_sum=Sum(
                    ExpressionWrapper(
                        F("volume") / 1000.0,
                        output_field=FloatField(),
                    )
                )
            )
            .order_by("-volume_sum")
        )

        if not stats:
            logger.info(
                "За %s этикетки не печатались",
                today,
            )

            return (
                f"Сегодня {today:%Y-%m-%d} "
                "не было напечатано ни одной этикетки."
            )

        total_volume = sum(
            row["volume_sum"] or 0
            for row in stats
        )

        products_count = len(stats)

        lines = [
            f"📊 Статистика за сегодня {today:%Y-%m-%d} (в литрах):\n"
        ]

        lines.extend(
            f"• {row['product_name']}: "
            f"{round(row['volume_sum'] or 0, 2)} л."
            for row in stats
        )

        lines.append(
            f"\n🔹 Итого: {round(total_volume, 2)} л."
        )

        logger.info(
            "Дневная статистика печати сформирована: "
            "дата=%s, продуктов=%s, общий объём=%.2f л.",
            today,
            products_count,
            total_volume,
        )

        return "\n".join(lines)

    except Exception:
        logger.exception(
            "Ошибка при формировании дневной статистики печати за %s",
            today,
        )
        raise


def build_print_log_message():
    since = timezone.now() - timedelta(days=1)

    logger.debug(
        "Формирование лога печати за последние сутки: начиная с %s",
        since,
    )

    try:
        logs = list(
            LabelPrintLog.objects
            .filter(printed_at__gte=since)
            .order_by("-printed_at")
        )

        if not logs:
            logger.info(
                "За последние сутки печать не выполнялась"
            )

            return "Логов за последние сутки нет."

        logger.info(
            "Лог печати сформирован: записей=%s",
            len(logs),
        )

        return "\n".join(
            f"{log.printed_at:%Y-%m-%d %H:%M:%S} — {log}"
            for log in logs
        )

    except Exception:
        logger.exception(
            "Ошибка при формировании лога печати за последние сутки"
        )
        raise