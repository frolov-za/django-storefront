from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import LabelConfig
from .utils.zpl_utils import generate_zpl, generate_preview
import socket
import logging
import json

logger = logging.getLogger(__name__)

@require_POST
def print_label(request):
    try:
        # Проверяем наличие обязательных параметров
        # Парсим JSON данные
        data = json.loads(request.body)
        product_name = data.get('product_name')
        barcode = data.get('barcode')
        
        if not product_name or not barcode:
            missing = [name for name, value in [('product_name', product_name), ('barcode', barcode)] if not value]
            return JsonResponse({
                'status': 'error',
                'message': f'Missing parameters: {", ".join(missing)}'
            }, status=400)

        # Получаем конфигурацию с обработкой отсутствия
        try:
            config = LabelConfig.objects.get(name="default")
        except LabelConfig.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Label configuration "default" not found'
            }, status=404)

        # Генерируем ZPL
        zpl_data = generate_zpl(config, product_name, barcode)
        logger.debug(f"Generated ZPL:\n{zpl_data}")

        # Отправляем на принтер
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(5)  # Таймаут 5 секунд
            sock.connect((config.printer.ip_address, config.printer.port))
            sock.sendall(zpl_data.encode('utf-8'))
            
        return JsonResponse({'status': 'success'})

    except socket.timeout:
        logger.error("Printer connection timeout")
        return JsonResponse({
            'status': 'error',
            'message': 'Printer connection timeout'
        }, status=500)

    except socket.error as e:
        logger.error(f"Printer connection error: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': f'Printer connection failed: {str(e)}'
        }, status=500)

    except Exception as e:
        logger.exception("Unexpected error during printing")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
    
def preview_label(request, pk):
    try:
        config = LabelConfig.objects.get(pk=pk)
        image_bytes = generate_preview(config)
        return HttpResponse(image_bytes, content_type="image/png")
    except Exception as e:
        return HttpResponse(f"Error: {str(e)}", status=500)