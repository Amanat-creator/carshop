import random
from decimal import Decimal
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify

from cars.models import Car, CarImage

CARS_DATA = [
    # (brand, model, year, price, mileage, transmission, fuel, color, engine, description)
    ("Toyota", "Camry", 2022, 3200000, 25000, "auto", "petrol", "Белый", 2.5,
     "Отличное состояние, один владелец, полный комплект документов. Обслуживание только у официального дилера."),

    ("Toyota", "Corolla", 2021, 2100000, 42000, "variator", "petrol", "Серебристый", 1.6,
     "Экономичный и надёжный автомобиль. Идеально подходит для города. Не бит, не крашен."),

    ("BMW", "X5", 2020, 6500000, 55000, "auto", "diesel", "Чёрный", 3.0,
     "Полный привод, панорамная крыша, кожаный салон. Все ТО по регламенту. Пакет M-Sport."),

    ("BMW", "3 Series", 2019, 3800000, 78000, "auto", "petrol", "Синий", 2.0,
     "Спортивный седан в идеальном состоянии. Комплектация Luxury Line. Пригнан из Германии."),

    ("Mercedes-Benz", "E-Class", 2021, 5200000, 34000, "auto", "petrol", "Чёрный", 2.0,
     "Бизнес-класс, максимальная комплектация. AMG-пакет, Burmester аудио, панорама."),

    ("Mercedes-Benz", "GLC", 2022, 6100000, 18000, "auto", "diesel", "Серый", 2.0,
     "Кроссовер премиум-класса. Практически новый, состояние шоурума. Гарантия производителя."),

    ("Audi", "A6", 2020, 4500000, 62000, "auto", "petrol", "Серый", 2.0,
     "Кватро-привод, матричные фары, виртуальный кокпит. Вложений не требует."),

    ("Audi", "Q7", 2019, 5800000, 88000, "auto", "diesel", "Белый", 3.0,
     "7-местный семейный внедорожник. Пневмоподвеска, полный электропакет."),

    ("Volkswagen", "Tiguan", 2021, 3200000, 38000, "robot", "petrol", "Синий", 2.0,
     "Популярный кроссовер. DSG, полный привод, кожаный салон. Без ДТП."),

    ("Volkswagen", "Passat", 2019, 2400000, 95000, "robot", "diesel", "Чёрный", 2.0,
     "Надёжный бизнес-седан. Дизель экономичный — 5.5 л/100 км. Полный пакет опций."),

    ("Kia", "Sportage", 2022, 3100000, 22000, "auto", "petrol", "Красный", 2.0,
     "Новое поколение. Полный привод, панорамная крыша. Гарантия до 2027 года."),

    ("Kia", "Rio", 2020, 1450000, 55000, "auto", "petrol", "Белый", 1.6,
     "Компактный городской автомобиль. Экономичный, надёжный. Идеален для начинающих."),

    ("Hyundai", "Tucson", 2021, 3400000, 41000, "auto", "petrol", "Серый", 2.5,
     "Стильный кроссовер. Полный привод, светодиодная оптика. Один владелец по ПТС."),

    ("Hyundai", "Solaris", 2020, 1350000, 68000, "auto", "petrol", "Синий", 1.6,
     "Самый популярный автомобиль в России. Неприхотлив, экономичен, дёшев в обслуживании."),

    ("Nissan", "Qashqai", 2019, 2100000, 87000, "variator", "petrol", "Белый", 2.0,
     "Надёжный японский кроссовер. Вариатор в идеале. Все ТО по регламенту."),

    ("Nissan", "X-Trail", 2020, 2900000, 72000, "variator", "petrol", "Коричневый", 2.5,
     "Просторный семейный кроссовер. Панорамная крыша, камера 360°. Без вложений."),

    ("Mazda", "CX-5", 2021, 3600000, 45000, "auto", "petrol", "Красный", 2.5,
     "Невероятно красивый кроссовер. Кожаный салон, Bose аудио. Ухожен, гаражное хранение."),

    ("Mazda", "6", 2019, 2400000, 82000, "auto", "petrol", "Серый", 2.0,
     "Спортивный седан бизнес-класса. Отличная управляемость и динамика."),

    ("Skoda", "Octavia", 2021, 2600000, 38000, "robot", "petrol", "Зелёный", 1.4,
     "Практичный лифтбек. Огромный багажник, экономичный двигатель. DSG-7."),

    ("Skoda", "Kodiaq", 2020, 3500000, 62000, "auto", "diesel", "Серебристый", 2.0,
     "7-местный семейный кроссовер. Полный привод, панорама, электропривод двери багажника."),
]


class Command(BaseCommand):
    help = 'Загружает 20 тестовых автомобилей в базу данных'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Удалить все существующие машины перед загрузкой',
        )

    def handle(self, *args, **options):
        if options['clear']:
            count = Car.objects.count()
            Car.objects.all().delete()
            self.stdout.write(self.style.WARNING(f'Удалено {count} машин'))

        created_count = 0
        skipped_count = 0

        for i, data in enumerate(CARS_DATA):
            (brand, model, year, price, mileage, transmission,
             fuel, color, engine, description) = data

            # Проверяем, существует ли уже
            if Car.objects.filter(brand=brand, model=model, year=year).exists():
                self.stdout.write(self.style.WARNING(f'⏭  Пропущено: {brand} {model} {year} (уже есть)'))
                skipped_count += 1
                continue

            # Генерируем slug
            base_slug = slugify(f"{brand}-{model}-{year}")
            slug = base_slug
            counter = 1
            while Car.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            # Случайный пробег для реалистичности
            mileage = mileage + random.randint(-5000, 5000)
            mileage = max(0, mileage)

            # Случайные просмотры
            views = random.randint(10, 1500)

            # Дата создания (за последние 6 месяцев, для графика динамики)
            days_ago = random.randint(0, 180)
            created_at = timezone.now() - timedelta(days=days_ago)

            car = Car.objects.create(
                brand=brand,
                model=model,
                year=year,
                price=Decimal(str(price)),
                mileage=mileage,
                transmission=transmission,
                fuel=fuel,
                color=color,
                engine_volume=Decimal(str(engine)),
                description=description,
                slug=slug,
                views_count=views,
                is_available=True,
            )

            # Перезаписываем created_at (auto_now_add нельзя задать напрямую)
            Car.objects.filter(pk=car.pk).update(created_at=created_at)

            created_count += 1
            self.stdout.write(self.style.SUCCESS(f'✓ Создано: {car}  ({car.price} ₽, {car.views_count} 👁)'))

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'📊 Итого: создано {created_count}, пропущено {skipped_count}, всего в БД {Car.objects.count()}'
        ))