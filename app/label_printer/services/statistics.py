from datetime import datetime, timedelta

from django.db.models import Count, ExpressionWrapper, F, FloatField, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone
from django.utils.timezone import localtime

from label_printer.models import LabelPrintLog


def validate_date_range(start_date_str, end_date_str):
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
    today = timezone.localdate()
    if start_date > today or end_date > today:
        raise ValueError("Дата не может быть в будущем")
    if start_date > end_date:
        raise ValueError("Дата начала должна быть раньше даты окончания")
    return start_date, end_date


def get_total_volume(queryset):
    return queryset.aggregate(
        total=Sum(ExpressionWrapper(F("volume") / 1000.0, output_field=FloatField()))
    )["total"] or 0.0


def get_product_stats(queryset):
    return queryset.values("product_name").annotate(
        total=Sum(ExpressionWrapper(F("volume") / 1000.0, output_field=FloatField())),
        count=Count("id"),
    ).order_by("-total")


def get_daily_breakdown(days=30):
    return LabelPrintLog.objects.annotate(date=TruncDate("printed_at")).values("date").annotate(
        total=Sum(ExpressionWrapper(F("volume") / 1000.0, output_field=FloatField()))
    ).order_by("-date")[:days]


def get_date_stats(start_date, end_date):
    queryset = LabelPrintLog.objects.filter(
        printed_at__date__gte=start_date, printed_at__date__lte=end_date
    )
    return {"total_volume": get_total_volume(queryset), "total_labels": queryset.count()}


def get_products_stats(start_date, end_date):
    return get_product_stats(
        LabelPrintLog.objects.filter(
            printed_at__date__gte=start_date, printed_at__date__lte=end_date
        )
    )


def get_dashboard_data(now=None):
    now = now or timezone.now()
    daily_start = localtime(now).replace(hour=0, minute=0, second=0, microsecond=0)
    daily_data = LabelPrintLog.objects.filter(printed_at__gte=daily_start)
    weekly_data = LabelPrintLog.objects.filter(printed_at__gte=daily_start - timedelta(days=7))
    return {
        "daily_total": get_total_volume(daily_data),
        "weekly_total": get_total_volume(weekly_data),
        "daily_by_product": get_product_stats(daily_data),
        "weekly_by_product": get_product_stats(weekly_data),
        "daily_breakdown": get_daily_breakdown(),
    }
