from django.urls import path
from . import views

app_name = 'cars'

urlpatterns = [
    path('', views.car_list, name='car_list'),
    path('car/<slug:slug>/', views.car_detail, name='car_detail'),
    path('car/<slug:slug>/contact/', views.contact_seller, name='contact_seller'),

    # Избранное
    path('favorites/', views.favorites_list, name='favorites'),
    path('favorites/add/<int:pk>/', views.add_to_favorites, name='add_favorite'),
    path('favorites/remove/<int:pk>/', views.remove_from_favorites, name='remove_favorite'),

    # Сравнение
    path('compare/', views.compare_view, name='compare'),
    path('compare/add/<int:pk>/', views.add_to_compare, name='add_compare'),
    path('compare/clear/', views.clear_compare, name='clear_compare'),

    # Авторизация
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),

    path('analytics/', views.analytics_view, name='analytics'),
]