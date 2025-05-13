from django.db import models
from cropperjs.models import CropperImageField

class Product(models.Model):
    name = models.CharField(max_length=100, help_text="Наименование товара")
    barcode = models.CharField(max_length=50, help_text="Артикул для тары 1 литр") 
    barcode15 = models.CharField(max_length=50, help_text="Артикул для тары 1.5 литра")
    description = models.TextField(blank=True, help_text="Описание товара, отображается при выборе товара")
    image = CropperImageField(dimensions=(250, 250), upload_to='product_images/')

    def __str__(self):
        return self.name