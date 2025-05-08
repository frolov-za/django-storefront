from django.shortcuts import render
from django.http import JsonResponse
from .models import Product
from django.views.decorators.csrf import csrf_exempt
import json

def product_list(request):
    products = Product.objects.all()[:50]
    return render(request, 'product_list.html', {'products': products})

# @csrf_exempt
# def handle_action(request):
#     if request.method == 'POST':
#         data = json.loads(request.body)
#         product_name = data.get('product_name')
#         barcode = data.get('barcode')
#         print(f"[POST] product_name: {product_name}, barcode: {barcode}")
#         return JsonResponse({'status': 'ok'})
