import random
import urllib.parse
import urllib.request
from io import BytesIO

from django.core.files import File
from django.core.management.base import BaseCommand

from cars.models import Car


# Список источников — пробуем по очереди
def get_picsum_url(seed):
    """Picsum — быстрый и надёжный, но фото не по теме машины"""
    return f"https://picsum.photos/seed/car{seed}/800/600"


def get_loremflickr_url(brand, model, seed):
    """LoremFlickr — по теме, но медленный"""
    query = f"{brand},{model}".replace(' ', ',')
    return f"https://loremflickr.com/800/600/{query}/all?lock={seed}"


def get_placehold_url(brand, model, seed):
    """Placehold.co — SVG-заглушка с текстом"""
    text = urllib.parse.quote(f"{brand} {model}")
    return f"https://placehold.co/800x600/2a5298/white?text={text}&font=roboto"


def download_image(url, timeout=15):
    """Скачивает изображение и возвращает байты или None"""
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        with urllib.request.urlopen(req, timeout=timeout) as response:
            if response.status == 200:
                data = response.read()
                if len(data) > 1000:  # отсеиваем пустые ответы
                    return data
    except Exception:
        return None
    return None


class Command(BaseCommand):
    help = 'Скачивает и прикрепляет фото к машинам'

    def add_arguments(self, parser):
        parser.add_argument(
            '--overwrite',
            action='store_true',
            help='Перезаписать существующие фото',
        )
        parser.add_argument(
            '--source',
            choices=['auto', 'picsum', 'loremflickr', 'placeholder'],
            default='auto',
            help='Источник фото',
        )

    def handle(self, *args, **options):
        cars = Car.objects.all()
        if options['overwrite']:
            self.stdout.write('Режим перезаписи всех фото')
            cars = Car.objects.all()
        else:
            cars = cars.filter(image='') | cars.filter(image__isnull=True)

        total = cars.count()
        if total == 0:
            self.stdout.write(self.style.WARNING('Нет машин без фото. Используй --overwrite'))
            return

        self.stdout.write(f'Обрабатываю {total} машин...\n')

        success = 0
        for i, car in enumerate(cars, 1):
            self.stdout.write(f'  [{i}/{total}] {car.brand} {car.model}... ', ending='')
            self.stdout.flush()

            # Определяем URL в зависимости от источника
            seed = car.pk * 7 + 13  # псевдослучайный но стабильный seed

            image_data = None

            if options['source'] == 'picsum':
                urls = [get_picsum_url(seed)]
            elif options['source'] == 'loremflickr':
                urls = [get_loremflickr_url(car.brand, car.model, seed)]
            elif options['source'] == 'placeholder':
                urls = [get_placehold_url(car.brand, car.model, seed)]
            else:  # auto
                urls = [
                    get_loremflickr_url(car.brand, car.model, seed),
                    get_picsum_url(seed),
                    get_placehold_url(car.brand, car.model, seed),
                ]

            # Пробуем источники по очереди
            for url in urls:
                self.stdout.write(f'\n    → {url[:70]}... ', ending='')
                self.stdout.flush()
                image_data = download_image(url)
                if image_data:
                    break

            if not image_data:
                self.stdout.write(self.style.ERROR('✗ Не удалось'))
                continue

            # Сохраняем в модель
            filename = f"{car.slug}.jpg"

            # Удаляем старое фото если есть
            if car.image:
                try:
                    car.image.delete(save=False)
                except Exception:
                    pass

            car.image.save(filename, File(BytesIO(image_data)), save=True)
            self.stdout.write(self.style.SUCCESS(f' ✓ ({len(image_data) // 1024} KB)'))
            success += 1

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'📷 Успешно: {success}/{total}'))