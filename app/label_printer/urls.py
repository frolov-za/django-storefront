from django.urls import path
from . import views
from .views import zpl_diagnostics_view

urlpatterns = [
    path('print/', views.print_label, name='print_label'),
    path(
        'custom_label/',
        views.custom_label,
        name='custom_label',
    ),

    path(
        'print-custom-product-labels/',
        views.print_custom_product_labels,
        name='print_custom_product_labels',
    ),
    path('dashboard/', views.sales_dashboard, name='sales_dashboard'),
    path('printer/diagnostics/', zpl_diagnostics_view, name='zpl_diagnostics'),
    path("api/logs/", views.django_logs, name="django_logs"),
    path("logs/", views.logs, name="logs"),
]