from django.urls import path
from . import views

urlpatterns = [
    path('', views.product_list, name='product_list'),
#    path('print/', views.handle_action, name='handle_action'),
]
