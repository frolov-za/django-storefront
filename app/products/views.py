import logging

from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie

from products.models import Product, Tare


logger = logging.getLogger(__name__)

@ensure_csrf_cookie
def product_list(request):
    try:
        products = Product.objects.all()[:50]
    except Exception:
        logger.exception("Ошибка при загрузке списка товаров")
        raise

    try:
        tares = Tare.objects.filter(
            type=Tare.TareType.VOLUME
        ).order_by("value")
    except Exception:
        logger.exception("Ошибка при загрузке списка тары")
        raise

    return render(
        request,
        "product_list.html",
        {
            "products": products,
            "tares": tares,
        }
    )