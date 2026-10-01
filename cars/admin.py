from django.contrib import admin
from .models import Car, CarImage, Favorite, Compare


class CarImageInline(admin.TabularInline):
    model = CarImage
    extra = 3


@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = ('brand', 'model', 'year', 'price', 'views_count', 'is_available', 'created_at')
    list_filter = ('brand', 'transmission', 'fuel', 'is_available', 'year')
    search_fields = ('brand', 'model', 'description')
    prepopulated_fields = {'slug': ('brand', 'model', 'year')}
    readonly_fields = ('views_count', 'created_at')
    inlines = [CarImageInline]
    list_editable = ('is_available',)


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'car', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'car__brand', 'car__model')


@admin.register(Compare)
class CompareAdmin(admin.ModelAdmin):
    list_display = ('user', 'car', 'created_at')