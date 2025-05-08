from django.urls import path
from . import views

app_name = 'label_printer'

urlpatterns = [
    path('print/', views.print_label, name='print_label'),
    path('preview/<int:pk>/', views.preview_label, name='preview'),
]