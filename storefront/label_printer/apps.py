# label_printer/apps.py
from django.apps import AppConfig

class LabelPrinterConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'label_printer'
    
    def ready(self):
        import label_printer.signals  # Для обработки сигналов при необходимости