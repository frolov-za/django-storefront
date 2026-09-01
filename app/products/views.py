from django.shortcuts import render
from .models import Product
from django.views.decorators.csrf import ensure_csrf_cookie

@ensure_csrf_cookie
def product_list(request):
    products = Product.objects.all()[:50]
    return render(request, 'product_list.html', {'products': products})