from django.urls import path
from . import views

urlpatterns = [
    path('print/', views.print_label, name='print_label'),
    path('dashboard/', views.sales_dashboard, name='sales_dashboard'),
]