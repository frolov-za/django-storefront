import json
import logging

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from label_printer.integrations.printers.diagnostics import get_diagnostics
from label_printer.services.printing import (
    PrintingError,
    get_active_printer,
    print_custom_labels,
    print_product_label,
)
from label_printer.services.statistics import (
    get_dashboard_data,
    get_date_stats,
    get_products_stats,
    validate_date_range,
)


logger = logging.getLogger(__name__)


def _json_body(request):
    try:
        return json.loads(request.body)
    except json.JSONDecodeError as error:
        logger.warning(
            "Получен некорректный JSON: %s",
            error,
        )
        raise PrintingError("Неверный формат данных") from error


@require_POST
def print_label(request):
    """Print a catalogue product; product data is resolved server-side."""
    try:
        data = _json_body(request)

        logger.debug(
            "Запрос на печать этикетки: product_id=%s, volume=%s",
            data.get("product_id"),
            data.get("volume"),
        )

        print_product_label(
            product_id=data.get("product_id"),
            volume=data.get("volume"),
        )

    except PrintingError as error:
        logger.warning(
            "Ошибка печати этикетки: %s",
            error,
        )
        return JsonResponse(
            {"success": False, "error": str(error)},
            status=400,
        )

    except Exception:
        logger.exception(
            "Непредвиденная ошибка при печати этикетки"
        )
        return JsonResponse(
            {
                "success": False,
                "error": "Внутренняя ошибка сервера",
            },
            status=500,
        )

    logger.info(
        "Этикетка успешно напечатана: product_id=%s, volume=%s",
        data.get("product_id"),
        data.get("volume"),
    )

    return JsonResponse({"success": True})


@require_POST
def print_custom_product_labels(request):
    try:
        data = _json_body(request)

        logger.debug(
            "Запрос на печать пользовательских этикеток: "
            "product_name=%s, barcode=%s, quantity=%s",
            data.get("product_name"),
            data.get("barcode"),
            data.get("quantity"),
        )

        result = print_custom_labels(
            product_name=data.get("product_name", "").strip(),
            barcode=data.get("barcode"),
            quantity=data.get("quantity"),
        )

    except PrintingError as error:
        logger.warning(
            "Ошибка печати пользовательских этикеток: %s",
            error,
        )
        return JsonResponse(
            {"success": False, "error": str(error)},
            status=400,
        )

    except Exception:
        logger.exception(
            "Непредвиденная ошибка при печати пользовательских этикеток"
        )
        return JsonResponse(
            {
                "success": False,
                "error": "Внутренняя ошибка сервера",
            },
            status=500,
        )

    logger.info(
        "Пользовательские этикетки успешно напечатаны: "
        "количество=%s",
        result.quantity,
    )

    return JsonResponse({
        "success": True,
        "quantity": result.quantity,
    })


def custom_label(request):
    logger.debug("Открытие страницы пользовательской печати")
    return render(request, "custom_label.html")

def logs(request):
    return render(request, "logs.html")

def zpl_diagnostics_view(request):
    logger.debug("Запуск диагностики принтера")

    try:
        printer = get_active_printer()

    except PrintingError as error:
        logger.warning(
            "Не удалось получить активный принтер: %s",
            error,
        )
        return render(
            request,
            "printer/error.html",
            {"error": str(error)},
        )

    except Exception:
        logger.exception(
            "Непредвиденная ошибка при получении активного принтера"
        )
        return render(
            request,
            "printer/error.html",
            {"error": "Внутренняя ошибка сервера"},
        )

    try:
        result = get_diagnostics(printer)

    except Exception:
        logger.exception(
            "Ошибка при выполнении диагностики принтера"
        )
        return render(
            request,
            "printer/error.html",
            {"error": "Ошибка диагностики принтера"},
        )

    if result.get("error"):
        logger.error(
            "Диагностика принтера завершилась с ошибкой: %s",
            result["error"],
        )
        return render(
            request,
            "printer/error.html",
            {"error": result["error"]},
        )

    logger.info("Диагностика принтера успешно завершена")

    return render(
        request,
        "printer/diagnostics.html",
        {
            "data": result,
            "printer": printer,
        },
    )


def sales_dashboard(request):
    context = {"error_message": None}

    try:
        if "start_date" in request.GET and "end_date" in request.GET:
            logger.debug(
                "Загрузка статистики за период: %s - %s",
                request.GET["start_date"],
                request.GET["end_date"],
            )

            start_date, end_date = validate_date_range(
                request.GET["start_date"],
                request.GET["end_date"],
            )

            context.update(
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat(),
                date_stats=get_date_stats(start_date, end_date),
                date_by_product=get_products_stats(start_date, end_date),
            )

        context.update(get_dashboard_data())

    except ValueError as error:
        logger.warning(
            "Некорректный период статистики: %s",
            error,
        )
        context["error_message"] = str(error)

    except Exception:
        logger.exception(
            "Ошибка при загрузке статистики"
        )
        context["error_message"] = "Ошибка загрузки статистики"

    return render(request, "dashboard.html", context)


def django_logs(request):
    log_file = settings.BASE_DIR / "logs" / "django.log"

    if not log_file.exists():
        return JsonResponse({"logs": []})

    with log_file.open("r", encoding="utf-8") as f:
        lines = f.readlines()

    return JsonResponse({
        "logs": lines[-200:]
    })