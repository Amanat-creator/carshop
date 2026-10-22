management/commands/create_superuser.py
import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Создает суперпользователя из переменных окружения'

    def handle(self, *args, **options):
        User = get_user_model()
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')

        if not username or not password:
            self.stdout.write(self.style.WARNING('Переменные для суперпользователя не заданы. Пропускаем.'))
            return

        if not User.objects.filter(username=username).exists():
            self.stdout.write(f'Создаем суперпользователя {username}...')
            User.objects.create_superuser(username=username, email=email, password=password)
            self.stdout.write(self.style.SUCCESS('Суперпользователь успешно создан!'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Суперпользователь {username} уже существует.'))