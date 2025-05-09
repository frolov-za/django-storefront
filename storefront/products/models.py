from django.db import models
from cropperjs.models import CropperImageField

class Product(models.Model):
    name = models.CharField(max_length=100)
    barcode = models.CharField(max_length=50) #Для объема 1л
    barcode15 = models.CharField(max_length=50) #Для объема 1.5л
    description = models.TextField(blank=True)
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

