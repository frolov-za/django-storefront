from django.db import models


class LabelPrintLog(models.Model):
    product_name = models.CharField(max_length=255)
    barcode = models.CharField(max_length=128)
    printed_at = models.DateTimeField(auto_now_add=True, verbose_name="Время печати")
    volume = models.IntegerField(verbose_name="Объём (мл)")

    def __str__(self):
        return f"{self.product_name} ({self.barcode}) ({self.volume}) — {self.printed_at}"
