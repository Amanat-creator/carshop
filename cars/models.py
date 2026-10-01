from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse
from django.utils.text import slugify



class Car(models.Model):
    TRANSMISSION_CHOICES = [
        ('auto', 'Автомат'),
        ('manual', 'Механика'),
        ('robot', 'Робот'),
        ('variator', 'Вариатор'),
    ]

    FUEL_CHOICES = [
        ('petrol', 'Бензин'),
        ('diesel', 'Дизель'),
        ('hybrid', 'Гибрид'),
        ('electric', 'Электро'),
    ]

    brand = models.CharField(max_length=100, verbose_name='Марка')
    model = models.CharField(max_length=100, verbose_name='Модель')
    year = models.IntegerField(verbose_name='Год выпуска')
    price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Цена')
    mileage = models.IntegerField(verbose_name='Пробег (км)')
    transmission = models.CharField(max_length=20, choices=TRANSMISSION_CHOICES, verbose_name='Коробка передач')
    fuel = models.CharField(max_length=20, choices=FUEL_CHOICES, default='petrol', verbose_name='Топливо')
    color = models.CharField(max_length=50, blank=True, verbose_name='Цвет')
    engine_volume = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True,
                                        verbose_name='Объём двигателя (л)')
    description = models.TextField(verbose_name='Описание')
    image = models.ImageField(upload_to='cars/', verbose_name='Главное фото', blank=True, null=True)
    slug = models.SlugField(unique=True, blank=True, verbose_name='URL')
    views_count = models.PositiveIntegerField(default=0, verbose_name='Просмотры')
    created_at = models.DateTimeField(auto_now_add=True)
    is_available = models.BooleanField(default=True, verbose_name='В наличии')

    class Meta:
        verbose_name = 'Автомобиль'
        verbose_name_plural = 'Автомобили'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.brand} {self.model} ({self.year})"

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(f"{self.brand}-{self.model}-{self.year}")
            if not base:
                base = 'car'
            slug = base
            counter = 1
            while Car.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('cars:car_detail', kwargs={'slug': self.slug})


class CarImage(models.Model):
    car = models.ForeignKey(Car, related_name='images', on_delete=models.CASCADE, verbose_name='Автомобиль')
    image = models.ImageField(upload_to='cars/gallery/', verbose_name='Фото')
    is_main = models.BooleanField(default=False, verbose_name='Главное')

    class Meta:
        verbose_name = 'Фотография'
        verbose_name_plural = 'Фотографии'




from django.contrib.auth.models import User


class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites', verbose_name='Пользователь')
    car = models.ForeignKey(Car, on_delete=models.CASCADE, verbose_name='Автомобиль')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления')

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        unique_together = ('user', 'car')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} ❤️ {self.car}"


class Compare(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='compares', verbose_name='Пользователь')
    car = models.ForeignKey(Car, on_delete=models.CASCADE, verbose_name='Автомобиль')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Сравнение'
        verbose_name_plural = 'Сравнение'
        unique_together = ('user', 'car')

    def __str__(self):
        return f"{self.user.username} ⚖️ {self.car}"