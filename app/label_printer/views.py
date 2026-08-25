from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Sum, Count, Q, F, FloatField, ExpressionWrapper
from django.db.models.functions import TruncDate
from django.shortcuts import render
from datetime import datetime, timedelta
import json
import logging

from .models import Printer, LabelPrintLog
from products.models import Product
from .utils.zpl_generator import generate_zpl
from .utils.printer_service import (
    send_zpl_to_printer,
    parse_zpl_help_output,
    get_zpl_diagnostics,
    parse_zebra_hs_response,
)
from django.utils.timezone import localtime

logger = logging.getLogger(__name__)


def validate_date_range(start_date_str, end_date_str):
    try:
        naive_start = datetime.strptime(start_date_str, "%Y-%m-%d")
        naive_end = datetime.strptime(end_date_str, "%Y-%m-%d")

        tz = timezone.get_current_timezone()
        start_date = timezone.make_aware(naive_start, tz)
        end_date = timezone.make_aware(naive_end, tz)

        now = timezone.now()

        if start_date > now:
            raise ValueError("Дата начала не может быть в будущем")
        if end_date > now:
            raise ValueError("Дата окончания не может быть в будущем")
        if start_date > end_date:
            raise ValueError("Дата начала должна быть раньше даты окончания")

        return start_date.date(), end_date.date()

    except ValueError as e:
        if "unconverted data remains" in str(e):
            raise ValueError("Некорректный формат даты. Используйте YYYY-MM-DD")

        logger.error(f"Date validation error: {e}")
        raise


@require_POST
def print_label(request):
    try:
        data = json.loads(request.body)
        product_name = data.get("product_name")
        barcode = data.get("barcode")
        volume = data.get("volume")  # ожидаем миллилитры (1000, 1500)
        

        if not product_name or not barcode or not volume:
            return JsonResponse(
                {"success": False, "error": "Отсутствуют обязательные поля"}, status=400
            )

        product = Product.objects.filter(Q(barcode=barcode) | Q(barcode15=barcode)).first()

        if not product:
            return JsonResponse({"success": False, "error": "Продукт не найден"}, status=404)

        printer = Printer.get_first_active()
        if not printer or not printer.label_template:
            return JsonResponse({"success": False, "error": "Принтер не настроен"}, status=400)

        zpl_data = generate_zpl(product_name, barcode, printer.label_template)
        if send_zpl_to_printer(zpl_data, printer):
            # Записываем лог печати
            LabelPrintLog.objects.create(
                product_name=product.name,
                barcode=barcode,
                volume=int(volume),  # в мл
            )
            return JsonResponse({"success": True})

        return JsonResponse({"success": False, "error": "Ошибка печати"}, status=500)

    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Неверный формат данных"}, status=400)
    except Exception as e:
        logger.error(f"Print error: {str(e)}")
        return JsonResponse(
            {"success": False, "error": "Внутренняя ошибка сервера"}, status=500
        )

@require_POST
def print_custom_product_labels(request):
    try:
        data = json.loads(request.body)

        product_name = data.get("product_name")
        barcode = data.get("barcode")
        quantity = data.get("quantity")

        if not product_name or barcode is None or quantity is None:
            return JsonResponse(
                {"success": False, "error": "Отсутствуют обязательные поля"},
                status=400,
            )

        try:
            barcode = int(barcode)
            quantity = int(quantity)
        except (TypeError, ValueError):
            return JsonResponse(
                {
                    "success": False,
                    "error": "barcode и quantity должны быть числами",
                },
                status=400,
            )

        if quantity <= 0:
            return JsonResponse(
                {
                    "success": False,
                    "error": "Количество должно быть больше 0",
                },
                status=400,
            )

        # Получаем настроенный принтер
        printer = Printer.get_first_active()

        if not printer or not printer.label_template:
            return JsonResponse(
                {"success": False, "error": "Принтер не настроен"},
                status=400,
            )

        # Генерируем одну этикетку
        zpl_label = generate_zpl(
            product_name,
            barcode,
            printer.label_template,
        )

        # Формируем нужное количество этикеток
        zpl_data = zpl_label * quantity

        # Отправляем на настроенный принтер
        if send_zpl_to_printer(zpl_data, printer):
            return JsonResponse(
                {
                    "success": True,
                    "quantity": quantity,
                }
            )

        return JsonResponse(
            {
                "success": False,
                "error": "Ошибка печати",
            },
            status=500,
        )

    except json.JSONDecodeError:
        return JsonResponse(
            {
                "success": False,
                "error": "Неверный формат данных",
            },
            status=400,
        )

    except Exception as e:
        logger.exception("Print product labels error")

        return JsonResponse(
            {
                "success": False,
                "error": "Внутренняя ошибка сервера",
            },
            status=500,
        )

def custom_label(request):
    return render(request, "custom_label.html")

def zpl_diagnostics_view(request):
    try:
        printer = Printer.get_first_active()
    except Printer.DoesNotExist:
        return render(request, "printer/error.html", {"error": "Принтер не найден."})

    result = get_zpl_diagnostics(printer)

    if isinstance(result, dict) and result.get("error"):
        return render(request, "printer/error.html", {"error": result["error"]})

    if isinstance(result, dict) and result.get("raw"):
        raw_output = result["raw"]
        try:
            variables = parse_zpl_help_output(raw_output)
        except Exception as e:
            return render(
                request,
                "printer/error.html",
                {"error": f"Ошибка разбора данных: {str(e)}"},
            )

        data = {**variables, "raw": raw_output}
        return render(
            request,
            "printer/diagnostics.html",
            {
                "data": data,
                "printer": printer,
            },
        )

    if isinstance(result, dict):
        return render(
            request,
            "printer/diagnostics.html",
            {
                "data": result,
                "printer": printer,
            },
        )

    return render(
        request, "printer/error.html", {"error": "Не удалось получить данные от принтера."}
    )


def sales_dashboard(request):
    context = {"error_message": None}
    now = timezone.now()
    today = now.date()

    # Обработка диапазона дат
    try:
        if "start_date" in request.GET and "end_date" in request.GET:
            start_date, end_date = validate_date_range(
                request.GET["start_date"], request.GET["end_date"]
            )
            context.update(
                {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "date_stats": get_date_stats(start_date, end_date),
                    "date_by_product": get_products_stats(start_date, end_date),
                }
            )
    except ValueError as e:
        context["error_message"] = str(e)

    # Основная статистика
    try:
        daily_start = localtime(now).replace(hour=0, minute=0, second=0, microsecond=0)
        daily_data = LabelPrintLog.objects.filter(printed_at__gte=daily_start)

        weekly_start = daily_start - timedelta(days=7)
        weekly_data = LabelPrintLog.objects.filter(printed_at__gte=weekly_start)

        context.update(
            {
                "daily_total": get_total_volume(daily_data),
                "weekly_total": get_total_volume(weekly_data),
                "daily_by_product": get_product_stats(daily_data),
                "weekly_by_product": get_product_stats(weekly_data),
                "daily_breakdown": get_daily_breakdown(),
            }
        )
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        context["error_message"] = "Ошибка загрузки статистики"

    return render(request, "dashboard.html", context)


# --- Helpers для статистики ---


def get_total_volume(queryset):
    return (
        queryset.aggregate(
            total=Sum(ExpressionWrapper(F("volume") / 1000.0, output_field=FloatField()))
        )["total"]
        or 0.0
    )


def get_product_stats(queryset):
    return (
        queryset.values("product_name")
        .annotate(
            total=Sum(
                ExpressionWrapper(F("volume") / 1000.0, output_field=FloatField())
            ),
            count=Count("id"),
        )
        .order_by("-total")
    )


def get_daily_breakdown(days=30):
    return (
        LabelPrintLog.objects.annotate(date=TruncDate("printed_at"))
        .values("date")
        .annotate(
            total=Sum(
                ExpressionWrapper(F("volume") / 1000.0, output_field=FloatField())
            )
        )
        .order_by("-date")[:days]
    )


def get_date_stats(start_date, end_date):
    queryset = LabelPrintLog.objects.filter(
        printed_at__date__gte=start_date, printed_at__date__lte=end_date
    )
    return {
        "total_volume": get_total_volume(queryset),
        "total_labels": queryset.count(),
    }


def get_products_stats(start_date, end_date):
    return get_product_stats(
        LabelPrintLog.objects.filter(
            printed_at__date__gte=start_date, printed_at__date__lte=end_date
        )
    )
