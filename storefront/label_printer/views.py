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
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    
    printer = Printer.get_first_active()
    if not printer or not printer.label_template:
        return JsonResponse({'error': 'Active printer not found'}, status=400)
    
    zpl_data = generate_zpl(product_name, barcode, printer.label_template)
    if send_zpl_to_printer(zpl_data, printer):
        return JsonResponse({'status': 'Label sent successfully'})
    return JsonResponse({'error': 'Failed to send label'}, status=500)