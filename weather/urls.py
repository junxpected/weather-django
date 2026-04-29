from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('api/weather/', views.get_weather, name='get_weather'),
    path('api/history/', views.get_history, name='get_history'),
    path('api/history/clear/', views.clear_history, name='clear_history'),
    path('api/autocomplete/', views.city_autocomplete, name='autocomplete'),
]