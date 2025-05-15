import os
import random
import string
import requests
from io import BytesIO

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from products.models import Product

class Command(BaseCommand):
    help = 'Генерирует 50 тестовых товаров с рандомными изображениями'

    def handle(self, *args, **kwargs):
        Product.objects.all().delete()  # Очистить старые товары

        for i in range(50):
            name = f'Товар {i+1}'
            barcode = ''.join(random.choices(string.digits, k=13))

            # Получить случайную картинку
            response = requests.get('https://picsum.photos/200', timeout=10)
            if response.status_code != 200:
                self.stderr.write("Ошибка при загрузке изображения")
                continue

            image = ContentFile(response.content)
            product = Product(name=name, barcode=barcode)
            product.image.save(f'product_{i+1}.jpg', image, save=True)

            self.stdout.write(self.style.SUCCESS(f'Создан: {name}'))

        self.stdout.write(self.style.SUCCESS('Все товары успешно созданы.'))
