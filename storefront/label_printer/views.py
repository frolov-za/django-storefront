from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json
from .models import Printer
from .models import LabelPrintLog
from .utils.zpl_generator import generate_zpl
from .utils.printer_service import send_zpl_to_printer
from django.utils import timezone
from django.db.models import Count
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth
from django.shortcuts import render
from django.utils.dateformat import format as date_format
from django.utils.dateparse import parse_date
from datetime import datetime
from django.db.models import Q

@require_POST
def print_label(request):
    try:
        data = json.loads(request.body)
        product_name = data['product_name']
        barcode = data['barcode']
        LabelPrintLog.objects.create(product_name=product_name, barcode=barcode)
    except (KeyError, json.JSONDecodeError):
        return JsonResponse({'success': False, 'error': 'Некорректные данные запроса'}, status=400)

    printer = Printer.get_first_active()
    if not printer or not printer.label_template:
        return JsonResponse({'success': False, 'error': 'Активный принтер или шаблон не найден'}, status=400)

    zpl_data = generate_zpl(product_name, barcode, printer.label_template)
    if send_zpl_to_printer(zpl_data, printer):
        return JsonResponse({'success': True, 'message': 'Этикетка успешно отправлена на печать'})
    
    return JsonResponse({'success': False, 'error': 'Не удалось отправить данные на принтер'}, status=500)

def label_dashboard(request):
    # Фильтрация по дате
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    filters = Q()
    if start_date:
        try:
            filters &= Q(printed_at__date__gte=parse_date(start_date))
        except:
            pass
    if end_date:
        try:
            filters &= Q(printed_at__date__lte=parse_date(end_date))
        except:
            pass

    # Форматирование данных
    def format_data(queryset, period_field):
        formatted = []
        for entry in queryset:
            date_obj = entry[period_field]
            
            if isinstance(date_obj, datetime):
                if period_field == 'day':
                    fmt = '%Y-%m-%d'
                elif period_field == 'week':
                    fmt = '%Y-%W'  # Формат год-номер недели
                elif period_field == 'month':
                    fmt = '%Y-%m'
                entry[period_field] = date_obj.strftime(fmt)
            
            formatted.append(entry)
        return formatted

    # Запросы и форматирование
    daily_data = format_data(
        LabelPrintLog.objects
        .filter(filters)
        .annotate(day=TruncDay('printed_at'))
        .values('day', 'product_name')
        .annotate(count=Count('id'))
        .order_by('day', 'product_name'),
        'day'
    )

    weekly_data = format_data(
        LabelPrintLog.objects
        .filter(filters)
        .annotate(week=TruncWeek('printed_at'))
        .values('week', 'product_name')
        .annotate(count=Count('id'))
        .order_by('week', 'product_name'),
        'week'
    )

    monthly_data = format_data(
        LabelPrintLog.objects
        .filter(filters)
        .annotate(month=TruncMonth('printed_at'))
        .values('month', 'product_name')
        .annotate(count=Count('id'))
        .order_by('month', 'product_name'),
        'month'
    )

    context = {
        'daily_data': daily_data,
        'weekly_data': weekly_data,
        'monthly_data': monthly_data,
        'start_date': start_date or '',
        'end_date': end_date or '',
    }

    return render(request, 'dashboard.html', context)


