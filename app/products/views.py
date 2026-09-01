from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie

from products.models import Product, Tare


@ensure_csrf_cookie
def product_list(request):
    products = Product.objects.all()[:50]

    tares = Tare.objects.filter(
        type=Tare.TareType.VOLUME
    ).order_by("value")

    return render(
        request,
        "product_list.html",
        {
            "products": products,
            "tares": tares,
        }
    )