import os
import requests
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import SearchHistory

OPENWEATHER_KEY = os.getenv('OPENWEATHER_API_KEY', '')
BASE_URL = 'https://api.openweathermap.org/data/2.5'


def index(request):
    return render(request, 'weather/index.html')


def get_weather(request):
    city = request.GET.get('city', '')
    lat = request.GET.get('lat', '')
    lon = request.GET.get('lon', '')

    if lat and lon:
        params = {'lat': lat, 'lon': lon, 'appid': OPENWEATHER_KEY, 'units': 'metric', 'lang': 'ua'}
    elif city:
        params = {'q': city, 'appid': OPENWEATHER_KEY, 'units': 'metric', 'lang': 'ua'}
    else:
        return JsonResponse({'error': 'Місто не вказано'}, status=400)

    try:
        weather = requests.get(f'{BASE_URL}/weather', params=params, timeout=10)
        if weather.status_code == 404:
            return JsonResponse({'error': 'Місто не знайдено'}, status=404)
        weather.raise_for_status()

        forecast = requests.get(f'{BASE_URL}/forecast', params=params, timeout=10)
        forecast.raise_for_status()

        # Зберігаємо в історію
        city_name = weather.json().get('name', city)
        last = SearchHistory.objects.first()
        if not last or last.city.lower() != city_name.lower():
            SearchHistory.objects.create(city=city_name)

        return JsonResponse({'weather': weather.json(), 'forecast': forecast.json()})

    except requests.RequestException as e:
        return JsonResponse({'error': str(e)}, status=500)


def get_history(request):
    cities = SearchHistory.objects.values_list('city', flat=True)[:10]
    seen = set()
    unique = []
    for c in cities:
        if c.lower() not in seen:
            seen.add(c.lower())
            unique.append(c)
    return JsonResponse({'history': unique})


@csrf_exempt
def clear_history(request):
    if request.method == 'POST':
        SearchHistory.objects.all().delete()
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'error': 'Тільки POST'}, status=405)


def city_autocomplete(request):
    query = request.GET.get('q', '')
    if len(query) < 2:
        return JsonResponse({'cities': []})

    try:
        resp = requests.get(
            'https://api.openweathermap.org/geo/1.0/direct',
            params={'q': query, 'limit': 5, 'appid': OPENWEATHER_KEY},
            timeout=10
        )
        resp.raise_for_status()
        cities = [
            {
                'name': item.get('local_names', {}).get('uk', item['name']),
                'country': item.get('country', ''),
            }
            for item in resp.json()
        ]
        return JsonResponse({'cities': cities})
    except requests.RequestException as e:
        return JsonResponse({'error': str(e)}, status=500)