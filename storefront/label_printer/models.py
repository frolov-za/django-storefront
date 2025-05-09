from django.db import models
from django.core.exceptions import ValidationError
import subprocess

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
    CONNECTION_TYPES = [
        ('network', 'Сетевой принтер'),
        ('usb', 'USB-принтер'),
    ]
    
    name = models.CharField(max_length=255)
    connection_type = models.CharField(max_length=7, choices=CONNECTION_TYPES, default='network')
    address = models.CharField(max_length=255, blank=True, null=True)
    port = models.IntegerField(default=9100, blank=True, null=True)
    device_path = models.CharField(max_length=255, blank=True, null=True, help_text="Пример: /dev/usb/lp0")
    is_active = models.BooleanField(default=True)
    label_template = models.ForeignKey('LabelTemplate', on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.name

    def clean(self):
        if self.connection_type == 'network':
            if not self.address or not self.port:
                raise ValidationError("Для сетевого принтера необходимо указать адрес и порт")
        elif self.connection_type == 'usb':
            if not self.device_path:
                raise ValidationError("Для USB-принтера необходимо указать путь к устройству")
            
    @classmethod
    def find_usb_printers(cls):
        """Поиск подключенных USB-принтеров"""
        try:
            # Ищем устройства в /dev
            result = subprocess.run(
                ['ls /dev/usb/lp* 2>/dev/null'], 
                shell=True, 
                capture_output=True, 
                text=True,
                timeout=5
            )
            devices = result.stdout.split()
            return [{'device_path': dev} for dev in devices if dev]
            
        except Exception as e:
            return []

    @classmethod
    def get_first_active(cls):
        return cls.objects.filter(is_active=True).order_by('connection_type').first()