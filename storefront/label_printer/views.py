from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json
from .models import Printer
from .utils.zpl_generator import generate_zpl
from .utils.printer_service import send_zpl_to_printer

@require_POST
def print_label(request):
    try:
        data = json.loads(request.body)
        product_name = data['product_name']
        barcode = data['barcode']
    except (KeyError, json.JSONDecodeError):
        return JsonResponse({'success': False, 'error': 'Некорректные данные запроса'}, status=400)

    printer = Printer.get_first_active()
    if not printer or not printer.label_template:
        return JsonResponse({'success': False, 'error': 'Активный принтер или шаблон не найден'}, status=400)

    zpl_data = generate_zpl(product_name, barcode, printer.label_template)
    if send_zpl_to_printer(zpl_data, printer):
        return JsonResponse({'success': True, 'message': 'Этикетка успешно отправлена на печать'})
    
    return JsonResponse({'success': False, 'error': 'Не удалось отправить данные на принтер'}, status=500)