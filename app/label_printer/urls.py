from django.urls import path
from . import views
from .views import zpl_diagnostics_view

urlpatterns = [
    path('print/', views.print_label, name='print_label'),
    path('dashboard/', views.sales_dashboard, name='sales_dashboard'),
    path('printer/diagnostics/', zpl_diagnostics_view, name='zpl_diagnostics'),
]