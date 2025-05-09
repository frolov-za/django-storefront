from django.db import models

class LabelTemplate(models.Model):
    BARCODE_TYPES = [
        ('CODE128', 'CODE128'),
        ('CODE39', 'CODE39'),
    ]
    
    name = models.CharField(max_length=255, unique=True)
    font_name = models.CharField(max_length=50, default='E:TT0003M_.FNT')
    font_letter = models.CharField(max_length=1, default='0')
    barcode_type = models.CharField(max_length=50, choices=BARCODE_TYPES, default='CODE128')
    barcode_height = models.PositiveIntegerField(default=100)
    barcode_human_readable = models.BooleanField(default=True)
    product_name_font_size = models.PositiveIntegerField(default=30)
    date_font_size = models.PositiveIntegerField(default=20)
    date_format = models.CharField(max_length=50, default='%d/%m/%Y')

    def __str__(self):
        return self.name

class Printer(models.Model):
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    port = models.IntegerField(default=9100)
    is_active = models.BooleanField(default=True)
    label_template = models.ForeignKey(LabelTemplate, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.name

    @classmethod
    def get_first_active(cls):
        return cls.objects.filter(is_active=True).first()