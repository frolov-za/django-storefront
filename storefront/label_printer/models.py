# label_printer/models.py
from django.db import models
from django.core.validators import MinValueValidator

class Printer(models.Model):
    name = models.CharField(max_length=100)
    ip_address = models.CharField(max_length=15)
    port = models.IntegerField(default=9100)
    
    def __str__(self):
        return f"{self.name} ({self.ip_address})"

class Font(models.Model):
    name = models.CharField(max_length=50)
    printer_code = models.CharField(max_length=2)
    width_dot = models.IntegerField()
    height_dot = models.IntegerField()
    
    def __str__(self):
        return f"{self.name} ({self.printer_code})"

class LabelConfig(models.Model):
    # Остальные поля должны быть объявлены ПОСЛЕ Printer и Font
    name = models.CharField(max_length=100)
    printer = models.ForeignKey(Printer, on_delete=models.CASCADE)

class LabelConfig(models.Model):
    # Существующие поля
    name = models.CharField(max_length=100, verbose_name="Название конфигурации")
    printer = models.ForeignKey('Printer', on_delete=models.CASCADE, verbose_name="Принтер")
    width_mm = models.FloatField(validators=[MinValueValidator(10)], verbose_name="Ширина (мм)")
    height_mm = models.FloatField(validators=[MinValueValidator(10)], verbose_name="Высота (мм)")
    dpi = models.IntegerField(default=203, choices=[(203, '203 DPI'), (300, '300 DPI')], verbose_name="Разрешение")
    
    # Новые поля для текста продукта
    product_font = models.ForeignKey('Font', on_delete=models.SET_NULL, null=True, verbose_name="Шрифт названия")
    product_max_width_mm = models.FloatField(verbose_name="Макс. ширина текста (мм)")
    product_pos_x_mm = models.FloatField(verbose_name="Позиция X текста (мм)")
    product_pos_y_mm = models.FloatField(verbose_name="Позиция Y текста (мм)")

    # Поля для штрих-кода
    BARCODE_TYPES = [
        ('CODE128', 'CODE128'),
        ('EAN13', 'EAN13'),
        ('QRCODE', 'QR Code')
    ]
    barcode_type = models.CharField(max_length=20, choices=BARCODE_TYPES, default='CODE128', verbose_name="Тип штрих-кода")
    barcode_height_mm = models.FloatField(verbose_name="Высота штрих-кода (мм)")
    barcode_pos_x_mm = models.FloatField(verbose_name="Позиция X штрих-кода (мм)")
    barcode_pos_y_mm = models.FloatField(verbose_name="Позиция Y штрих-кода (мм)")

    # Поля для даты
    date_font = models.ForeignKey('Font', on_delete=models.SET_NULL, null=True, related_name='date_fonts', verbose_name="Шрифт даты")
    date_rotation = models.IntegerField(
        choices=[(0, '0°'), (90, '90°'), (180, '180°'), (270, '270°')],
        default=90,
        verbose_name="Поворот даты"
    )
    date_pos_x_mm = models.FloatField(verbose_name="Позиция X даты (мм)")
    date_pos_y_mm = models.FloatField(verbose_name="Позиция Y даты (мм)")

    def mm_to_dots(self, mm):
        return int(mm * (self.dpi / 25.4))

    class Meta:
        verbose_name = "Конфигурация этикетки"
        verbose_name_plural = "Конфигурации этикеток"
    
    def generate_zpl(self, product_name, barcode, date):
        zpl = [
            "^XA",
            f"^PW{self.mm_to_dots(self.width_mm)}",
            f"^LL{self.mm_to_dots(self.height_mm)}",
            # Дата
            f"^FO{self.mm_to_dots(self.date_pos_x_mm)},{self.mm_to_dots(self.date_pos_y_mm)}",
            f"^A{self.date_font.printer_code},,{self.mm_to_dots(3)}",
            f"^FB{self.mm_to_dots(20)},1,0,{self.date_rotation},0",
            f"^FD{date.strftime('%d %m %y %H %M')}^FS",
            # Штрих-код
            f"^FO{self.mm_to_dots(self.barcode_pos_x_mm)},{self.mm_to_dots(self.barcode_pos_y_mm)}",
            f"^BY2,,{self.mm_to_dots(self.barcode_height_mm)}",
            f"^B{self.barcode_type},N,N,N",
            f"^FD{barcode}^FS",
            # Текст продукта
            f"^FO{self.mm_to_dots(self.product_pos_x_mm)},{self.mm_to_dots(self.product_pos_y_mm)}",
            f"^A{self.product_font.printer_code},,{self.mm_to_dots(4)}",
            f"^FB{self.mm_to_dots(self.product_max_width_mm)},1,0,C,0",
            f"^FD{product_name}^FS",
            "^XZ"
        ]
        return '\n'.join(zpl)

    def __str__(self):
        return f"{self.name} ({self.printer})"