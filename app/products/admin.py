from django.contrib import admin
from .models import Product#, Printer

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'barcode', 'barcode15')
    search_fields = ('name', 'barcode', 'barcode15')

# @admin.register(Printer)
# class ProductAdmin(admin.ModelAdmin):
#     list_display = ('id','in_use', 'name', 'location', 'type')
#     search_fields = ('name', 'location')
