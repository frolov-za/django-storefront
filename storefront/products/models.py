from django.db import models
from cropperjs.models import CropperImageField

class Product(models.Model):
    name = models.CharField(max_length=100, help_text="Наименование товара")
    barcode = models.CharField(max_length=50, help_text="Артикул для тары 1 литр") 
    barcode15 = models.CharField(max_length=50, help_text="Артикул для тары 1.5 литра")
    description = models.TextField(blank=True, help_text="Описание товара, отображается при выборе товара")
    image = CropperImageField(dimensions=(350, 350), upload_to='product_images/')
    #image = models.ImageField(upload_to='product_images/')

    def __str__(self):
        return self.name

# class DeviceType(models.TextChoices):
#     USB = 'USB', 'USB'
#     NETWORK = 'NETWORK', 'Network'

# class Printer(models.Model):
#     name = models.CharField(max_length=100)
#     location = models.CharField(max_length=50) 
#     type = models.CharField(max_length=10, choices=DeviceType.choices, default=DeviceType.USB)
#     in_use = models.BooleanField(default=False)

#     def __str__(self):
#         return self.name

