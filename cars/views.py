from django.db.models import Count, Avg, Max, Min, Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone
from datetime import timedelta
import json
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from .forms import ContactForm, RegisterForm
from .models import Car, Favorite, Compare
from decimal import Decimal
from django.contrib.auth.models import User
from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Q, F
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from .models import Car
from .forms import ContactForm


def car_list(request):
    cars = Car.objects.filter(is_available=True)

    # Поиск
    query = request.GET.get('q', '')
    if query:
        cars = cars.filter(Q(brand__icontains=query) | Q(model__icontains=query))

    # Фильтр по марке
    brand = request.GET.get('brand', '')
    if brand:
        cars = cars.filter(brand=brand)

    # Фильтр по КПП
    transmission = request.GET.get('transmission', '')
    if transmission:
        cars = cars.filter(transmission=transmission)

    # Фильтр по топливу
    fuel = request.GET.get('fuel', '')
    if fuel:
        cars = cars.filter(fuel=fuel)

    # Фильтр по цене
    price_min = request.GET.get('price_min', '')
    price_max = request.GET.get('price_max', '')
    if price_min:
        try:
            cars = cars.filter(price__gte=Decimal(price_min))
        except (ValueError, ArithmeticError):
            pass
    if price_max:
        try:
            cars = cars.filter(price__lte=Decimal(price_max))
        except (ValueError, ArithmeticError):
            pass

    # Сортировка
    sort = request.GET.get('sort', '')
    if sort == 'price_asc':
        cars = cars.order_by('price')
    elif sort == 'price_desc':
        cars = cars.order_by('-price')
    elif sort == 'year_desc':
        cars = cars.order_by('-year')
    elif sort == 'year_asc':
        cars = cars.order_by('year')
    elif sort == 'mileage':
        cars = cars.order_by('mileage')
    elif sort == 'popular':
        cars = cars.order_by('-views_count')

    # Пагинация
    paginator = Paginator(cars, 9)
    page_obj = paginator.get_page(request.GET.get('page'))

    brands = Car.objects.values_list('brand', flat=True).distinct().order_by('brand')

    if request.user.is_authenticated:
        favorites = list(Favorite.objects.filter(user=request.user).values_list('car_id', flat=True))
        compare = list(Compare.objects.filter(user=request.user).values_list('car_id', flat=True))
    else:
        favorites = []
        compare = []

    context = {
        'page_obj': page_obj,
        'brands': brands,
        'query': query,
        'current_brand': brand,
        'current_transmission': transmission,
        'current_fuel': fuel,
        'current_sort': sort,
        'price_min': price_min,
        'price_max': price_max,
        'favorites': favorites,
        'compare': compare,
    }
    return render(request, 'cars/car_list.html', context)


def car_detail(request, slug):
    car = get_object_or_404(Car, slug=slug)

    Car.objects.filter(pk=car.pk).update(views_count=F('views_count') + 1)
    car.refresh_from_db()

    price_min = car.price * Decimal('0.7')
    price_max = car.price * Decimal('1.3')
    similar_cars = Car.objects.filter(
        is_available=True,
        price__gte=price_min,
        price__lte=price_max
    ).exclude(pk=car.pk)[:3]

    if request.user.is_authenticated:
        is_favorite = Favorite.objects.filter(user=request.user, car=car).exists()
        is_compare = Compare.objects.filter(user=request.user, car=car).exists()
    else:
        is_favorite = False
        is_compare = False

    context = {
        'car': car,
        'similar_cars': similar_cars,
        'is_favorite': is_favorite,
        'is_compare': is_compare,
    }
    return render(request, 'cars/car_detail.html', context)


# ============== ИЗБРАННОЕ ==============

@login_required
def add_to_favorites(request, pk):
    car = get_object_or_404(Car, pk=pk)
    Favorite.objects.get_or_create(user=request.user, car=car)
    messages.success(request, 'Добавлено в избранное ❤️')
    return redirect(request.META.get('HTTP_REFERER', 'cars:car_list'))


@login_required
def remove_from_favorites(request, pk):
    Favorite.objects.filter(user=request.user, car_id=pk).delete()
    messages.info(request, 'Удалено из избранного')
    return redirect(request.META.get('HTTP_REFERER', 'cars:car_list'))


@login_required
def favorites_list(request):
    favorites = Favorite.objects.filter(user=request.user).select_related('car')
    cars = [f.car for f in favorites]
    return render(request, 'cars/favorites.html', {'cars': cars})

# ============== СРАВНЕНИЕ ==============

@login_required
def add_to_compare(request, pk):
    car = get_object_or_404(Car, pk=pk)
    existing = Compare.objects.filter(user=request.user, car=car)

    if existing.exists():
        existing.delete()
        messages.info(request, 'Удалено из сравнения')
    else:
        count = Compare.objects.filter(user=request.user).count()
        if count >= 3:
            messages.warning(request, 'Можно сравнивать не более 3 автомобилей')
        else:
            Compare.objects.create(user=request.user, car=car)
            messages.success(request, 'Добавлено к сравнению ⚖️')
    return redirect(request.META.get('HTTP_REFERER', 'cars:car_list'))


@login_required
def compare_view(request):
    car_ids = Compare.objects.filter(user=request.user).values_list('car_id', flat=True)
    cars = Car.objects.filter(pk__in=car_ids)
    return render(request, 'cars/compare.html', {'cars': cars})


@login_required
def clear_compare(request):
    Compare.objects.filter(user=request.user).delete()
    messages.info(request, 'Сравнение очищено')
    return redirect('cars:car_list')


# ============== ФОРМА СВЯЗИ С ПРОДАВЦОМ ==============
@login_required
def contact_seller(request, slug):
    car = get_object_or_404(Car, slug=slug)

    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            subject = f'Заявка по автомобилю {car.brand} {car.model}'
            message = (
                f"Автомобиль: {car.brand} {car.model} ({car.year})\n"
                f"Цена: {car.price} ₽\n"
                f"Ссылка: {request.build_absolute_uri(car.get_absolute_url())}\n\n"
                f"Имя: {cd['name']}\n"
                f"Телефон: {cd['phone']}\n"
                f"Email: {cd.get('email') or '—'}\n\n"
                f"Сообщение:\n{cd['message']}"
            )
            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@carshop.local')
            send_mail(
                subject,
                message,
                from_email,
                ['seller@carshop.local'],
                fail_silently=True,
            )
            messages.success(request, 'Заявка отправлена! Продавец свяжется с вами.')
            return redirect('cars:car_detail', slug=car.slug)
    else:
        form = ContactForm()

    return render(request, 'cars/contact.html', {'form': form, 'car': car})


# ============== АВТОРИЗАЦИЯ ==============

def register_view(request):
    if request.user.is_authenticated:
        return redirect('cars:car_list')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Добро пожаловать, {user.username}! 🎉')
            return redirect('cars:car_list')
    else:
        form = RegisterForm()

    return render(request, 'cars/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('cars:car_list')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'С возвращением, {user.username}!')
            next_url = request.GET.get('next') or 'cars:car_list'
            return redirect(next_url)
    else:
        form = AuthenticationForm()

    # Применяем стили
    for field in form.fields.values():
        field.widget.attrs[
            'style'] = 'width:100%; padding:12px; border:1px solid #ddd; border-radius:8px; font-size:14px; box-sizing:border-box;'

    return render(request, 'cars/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'Вы вышли из аккаунта')
    return redirect('cars:car_list')


@login_required
def profile_view(request):
    favorites_count = Favorite.objects.filter(user=request.user).count()
    compare_count = Compare.objects.filter(user=request.user).count()

    context = {
        'favorites_count': favorites_count,
        'compare_count': compare_count,
    }
    return render(request, 'cars/profile.html', context)


# ============== АНАЛИТИКА ==============

@login_required
def analytics_view(request):
    if not request.user.is_staff:
        messages.warning(request, 'Доступ только для администраторов')
        return redirect('cars:car_list')

    cars = Car.objects.all()

    # 1. Средняя цена по маркам (топ-10)
    brands_price = (
        Car.objects.values('brand')
        .annotate(avg_price=Avg('price'), count=Count('id'))
        .order_by('-count')[:10]
    )

    brand_labels = [item['brand'] for item in brands_price]
    brand_avg_prices = [float(item['avg_price']) for item in brands_price]
    brand_counts = [item['count'] for item in brands_price]

    # 2. Распределение цен по диапазонам
    price_ranges = [
        (0, 500000, 'до 500 тыс'),
        (500000, 1000000, '500 тыс – 1 млн'),
        (1000000, 2000000, '1 – 2 млн'),
        (2000000, 5000000, '2 – 5 млн'),
        (5000000, 999999999, '5+ млн'),
    ]
    price_distribution = []
    price_labels = []
    for low, high, label in price_ranges:
        count = cars.filter(price__gte=low, price__lt=high).count()
        price_distribution.append(count)
        price_labels.append(label)

    # 3. Распределение по КПП
    transmission_data = (
        Car.objects.values('transmission')
        .annotate(count=Count('id'))
    )
    transmission_map = dict(Car.TRANSMISSION_CHOICES)
    trans_labels = [transmission_map.get(item['transmission'], item['transmission']) for item in transmission_data]
    trans_counts = [item['count'] for item in transmission_data]

    # 4. Распределение по топливу
    fuel_data = (
        Car.objects.values('fuel')
        .annotate(count=Count('id'))
    )
    fuel_map = dict(Car.FUEL_CHOICES)
    fuel_labels = [fuel_map.get(item['fuel'], item['fuel']) for item in fuel_data]
    fuel_counts = [item['count'] for item in fuel_data]

    # 5. Динамика добавления машин по месяцам (за последние 12)
    year_ago = timezone.now() - timedelta(days=365)
    monthly_data = (
        Car.objects.filter(created_at__gte=year_ago)
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )
    month_labels = [item['month'].strftime('%b %Y') for item in monthly_data]
    month_counts = [item['count'] for item in monthly_data]

    # 6. Топ-5 по просмотрам
    top_viewed = Car.objects.order_by('-views_count')[:5]
    top_viewed_labels = [f"{c.brand} {c.model}" for c in top_viewed]
    top_viewed_counts = [c.views_count for c in top_viewed]

    # 7. Общая статистика
    total_cars = cars.count()
    available_cars = cars.filter(is_available=True).count()
    total_value = cars.aggregate(total=Sum('price'))['total'] or 0
    avg_price = cars.aggregate(avg=Avg('price'))['avg'] or 0
    max_price = cars.aggregate(max=Max('price'))['max'] or 0
    min_price = cars.aggregate(min=Min('price'))['min'] or 0
    total_views = cars.aggregate(total=Sum('views_count'))['total'] or 0

    context = {
        # Статистика
        'total_cars': total_cars,
        'available_cars': available_cars,
        'total_value': total_value,
        'avg_price': avg_price,
        'max_price': max_price,
        'min_price': min_price,
        'total_views': total_views,
        'total_users': User.objects.count(),
        'total_favorites': Favorite.objects.count(),
        'total_compares': Compare.objects.count(),

        # Данные для графиков (JSON)
        'brand_labels': json.dumps(brand_labels, ensure_ascii=False),
        'brand_avg_prices': json.dumps(brand_avg_prices),
        'brand_counts': json.dumps(brand_counts),

        'price_labels': json.dumps(price_labels, ensure_ascii=False),
        'price_distribution': json.dumps(price_distribution),

        'trans_labels': json.dumps(trans_labels, ensure_ascii=False),
        'trans_counts': json.dumps(trans_counts),

        'fuel_labels': json.dumps(fuel_labels, ensure_ascii=False),
        'fuel_counts': json.dumps(fuel_counts),

        'month_labels': json.dumps(month_labels, ensure_ascii=False),
        'month_counts': json.dumps(month_counts),

        'top_viewed_labels': json.dumps(top_viewed_labels, ensure_ascii=False),
        'top_viewed_counts': json.dumps(top_viewed_counts),
    }
    return render(request, 'cars/analytics.html', context)


