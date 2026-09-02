from django.db import models
from cropperjs.models import CropperImageField

class Product(models.Model):
    name = models.CharField(max_length=100, help_text="Наименование товара")
    barcode = models.CharField(max_length=13, help_text="Артикул товара") 
    barcode15 = models.CharField(max_length=13, help_text="Артикул для тары 1.5 литра")
    weight_product = models.BooleanField(default=False, help_text="Весовой товар EAN13, при формировании штрихкода последние 5 цифр определяются нажатой кнопкой в интерфейсе. Контрольная цифра (13) расчитывается автоматически")
    description = models.TextField(blank=True, help_text="Описание товара, отображается при выборе товара")
    image = CropperImageField(dimensions=(250, 250), upload_to='product_images/')

class Tare(models.Model):
    class TareType(models.TextChoices):
        VOLUME = "volume", "Миллилитры"
        WEIGHT = "weight", "Граммы"

    name = models.CharField(
        max_length=20,
        help_text="Название тары, например: 1 литр, 1.5 литра, 500 г"
    )

    value = models.PositiveIntegerField(
        help_text="Значение в миллилитрах или граммах"
    )

    type = models.CharField(
        max_length=10,
        choices=TareType.choices,
        help_text="Единица измерения значения"
    )


    def __str__(self):
        return self.name