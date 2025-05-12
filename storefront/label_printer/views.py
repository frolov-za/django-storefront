from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json
from .models import Printer, LabelPrintLog
from products.models import Product
from .utils.zpl_generator import generate_zpl
from .utils.printer_service import send_zpl_to_printer
from django.db.models import Q
from django.http import JsonResponse

from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum
from label_printer.models import LabelPrintLog


@require_POST
def print_label(request):
    try:
        data = json.loads(request.body)
        barcode = data['barcode']
        
        # Находим продукт по barcode или barcode15
        product = Product.objects.filter(
            Q(barcode=barcode) | Q(barcode15=barcode)
        ).first()
        
        if not product:
            return JsonResponse({'success': False, 'error': 'Продукт не найден'}, status=400)
        
        # Определяем объем
        volume = '1.5' if product.barcode15 == barcode else '1'
        
        # Создаем запись в логе
        LabelPrintLog.objects.create(
            product_name=product.name,
            barcode=barcode,
            volume=volume
        )
        
    except (KeyError, json.JSONDecodeError) as e:
        return JsonResponse({'success': False, 'error': 'Некорректные данные'}, status=400)

    printer = Printer.get_first_active()
    if not printer or not printer.label_template:
        return JsonResponse({'success': False, 'error': 'Активный принтер или шаблон не найден'}, status=400)

    zpl_data = generate_zpl(product_name, barcode, printer.label_template)
    if send_zpl_to_printer(zpl_data, printer):
        return JsonResponse({'success': True, 'message': 'Этикетка успешно отправлена на печать'})

    return JsonResponse({'success': False, 'error': 'Не удалось отправить данные на принтер'}, status=500)


def sales_dashboard(request):
    today = timezone.now().date()
    start_of_day = timezone.make_aware(timezone.datetime(today.year, today.month, today.day))
    
    # Данные за день
    daily_sales = LabelPrintLog.objects.filter(
        printed_at__gte=start_of_day
    ).aggregate(
        total=Sum('volume')
    )['total'] or 0
    
    # Данные за неделю
    start_of_week = start_of_day - timedelta(days=7)
    weekly_sales = LabelPrintLog.objects.filter(
        printed_at__gte=start_of_week
    ).aggregate(
        total=Sum('volume')
    )['total'] or 0
    
    # Детализация по дням
    daily_breakdown = (
        LabelPrintLog.objects
        .extra({'date': "date(printed_at)"})
        .values('date')
        .annotate(total=Sum('volume'))
        .order_by('-date')
    )
    
    return render(request, 'dashboard.html', {
        'daily_total': float(daily_sales),
        'weekly_total': float(weekly_sales),
        'daily_breakdown': daily_breakdown,
    })