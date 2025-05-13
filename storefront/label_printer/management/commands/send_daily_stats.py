from django.core.management.base import BaseCommand
from label_printer.utils.telegram import send_daily_volume_stats, send_telegram_message

class Command(BaseCommand):
    help = "Отправить дневную статистику по напиткам в Telegram"

    def handle(self, *args, **kwargs):
        message = send_daily_volume_stats()
        success = send_telegram_message(message)
        if success:
            self.stdout.write(self.style.SUCCESS("Сообщение отправлено"))
        else:
            self.stdout.write(self.style.ERROR("Не удалось отправить сообщение"))