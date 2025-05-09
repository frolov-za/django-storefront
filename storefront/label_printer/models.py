from django.db import models
from django.core.exceptions import ValidationError
import subprocess

class LabelTemplate(models.Model):
    # BARCODE_TYPES = [
    #     ('CODE128', 'CODE128'),
    #     ('CODE39', 'CODE39'),
    #     ('EAN13', 'EAN13'),
    # ]
    
    name = models.CharField(max_length=255, unique=True)
    label_hight = models.CharField(max_length=20, default='160',blank=True, null=True, help_text="Указывается в точках")
    label_wight = models.CharField(max_length=20, default='240',blank=True, null=True, help_text="Указывается в точках")
    font_name = models.CharField(max_length=50, default='E:TT0003M_.FNT')
    font_letter = models.CharField(max_length=1, default='0')
    #barcode_type = models.CharField(max_length=50, choices=BARCODE_TYPES, default='EAN13')
    barcode_height = models.PositiveIntegerField(default=100)
    barcode_position = models.CharField(max_length=20, default='20,1', help_text="Указывается в точках в формате 0,0 (^FOx,y)")
    barcode_human_readable = models.BooleanField(default=True)
    product_name_font_size = models.PositiveIntegerField(default=30)
    product_position = models.CharField(max_length=20, default='20,1', help_text="Указывается в точках в формате 0,0 (^FOx,y)")
    date_font_size = models.PositiveIntegerField(default=12)
    date_format = models.CharField(max_length=50, default='%d/%m/%y-%H:%M')
    date_position = models.CharField(max_length=20, default='70,10', help_text="Указывается в точках в формате 0,0 (^FOx,y)")

    def __str__(self):
        return self.name

class Printer(models.Model):
    CONNECTION_TYPES = [
        ('network', 'Сетевой принтер'),
        ('usb', 'USB-принтер'),
    ]

    DPI = [
        ('203', '203 dpi — 1 точка ≈ 0.125 мм'),
        ('300', '300 dpi — 1 точка ≈ 0.085 мм'),
    ]    

    name = models.CharField(max_length=255)
    connection_type = models.CharField(max_length=7, choices=CONNECTION_TYPES, default='network')
    address = models.CharField(max_length=255, blank=True, null=True, help_text="Указать IP или Hostname/DNS")
    port = models.IntegerField(default=9100, blank=True, null=True)
    device_path = models.CharField(max_length=255, blank=True, null=True, help_text="Пример: /dev/usb/lp0")
    printer_dpi = models.CharField(max_length=3, choices=DPI, default='203', help_text="Разрешение принтера (пока не учитывается)")
    is_active = models.BooleanField(default=True, help_text="Поставить чекбокс для используемого принтера, если подлкючен USB принтер и активны сетевой и USB, приоритет у USB принтера. Если USB принтер не подключен, но выбран как Active, скорее всего будет ошибка и печать не уйдет на сетевой принтер (надо проверить)")
    label_template = models.ForeignKey('LabelTemplate', on_delete=models.SET_NULL, null=True, help_text="Для каждого принтера могут быть свои настройки этикетки")

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