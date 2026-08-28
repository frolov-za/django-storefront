import json
import logging

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
        raise PrintingError("Неверный формат данных") from error


@require_POST
def print_label(request):
    """Print a catalogue product; product data is resolved server-side."""
    try:
        data = _json_body(request)
        print_product_label(product_id=data.get("product_id"), volume=data.get("volume"))
    except PrintingError as error:
        return JsonResponse({"success": False, "error": str(error)}, status=400)
    except Exception:
        logger.exception("Catalogue label printing failed")
        return JsonResponse({"success": False, "error": "Внутренняя ошибка сервера"}, status=500)
    return JsonResponse({"success": True})


@require_POST
def print_custom_product_labels(request):
    try:
        data = _json_body(request)
        result = print_custom_labels(
            product_name=data.get("product_name", "").strip(),
            barcode=data.get("barcode"),
            quantity=data.get("quantity"),
        )
    except PrintingError as error:
        return JsonResponse({"success": False, "error": str(error)}, status=400)
    except Exception:
        logger.exception("Custom label printing failed")
        return JsonResponse({"success": False, "error": "Внутренняя ошибка сервера"}, status=500)
    return JsonResponse({"success": True, "quantity": result.quantity})


def custom_label(request):
    return render(request, "custom_label.html")


def zpl_diagnostics_view(request):
    try:
        printer = get_active_printer()
    except PrintingError as error:
        return render(request, "printer/error.html", {"error": str(error)})

    result = get_diagnostics(printer)
    if result.get("error"):
        return render(request, "printer/error.html", {"error": result["error"]})
    return render(request, "printer/diagnostics.html", {"data": result, "printer": printer})


def sales_dashboard(request):
    context = {"error_message": None}
    try:
        if "start_date" in request.GET and "end_date" in request.GET:
            start_date, end_date = validate_date_range(
                request.GET["start_date"], request.GET["end_date"]
            )
            context.update(
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat(),
                date_stats=get_date_stats(start_date, end_date),
                date_by_product=get_products_stats(start_date, end_date),
            )
        context.update(get_dashboard_data())
    except ValueError as error:
        context["error_message"] = str(error)
    except Exception:
        logger.exception("Unable to build sales dashboard")
        context["error_message"] = "Ошибка загрузки статистики"
    return render(request, "dashboard.html", context)
