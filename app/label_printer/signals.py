# label_printer/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import LabelConfig

@receiver(post_save, sender=LabelConfig)
def config_updated(sender, instance, **kwargs):
    """Пример обработчика сигнала при изменении конфигурации"""
    print(f"Конфигурация {instance.name} была обновлена")