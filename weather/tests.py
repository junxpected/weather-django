from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch, MagicMock
from .models import SearchHistory
from django.utils import timezone
from datetime import timedelta


class SearchHistoryModelTest(TestCase):
    """Тести моделі SearchHistory"""

    def test_create_history(self):
        """Перевірка створення запису в історії"""
        entry = SearchHistory.objects.create(city='Lviv')
        self.assertEqual(entry.city, 'Lviv')
        self.assertIsNotNone(entry.searched_at)

    def test_str_method(self):
        """Перевірка __str__ методу"""
        entry = SearchHistory.objects.create(city='Kyiv')
        self.assertEqual(str(entry), 'Kyiv')

    def test_ordering(self):
        """Перевірка сортування — нові записи першими"""
        first_entry = SearchHistory.objects.create(city='Lviv')
        first_entry.searched_at = timezone.now() - timedelta(seconds=10)
        first_entry.save()
        second_entry = SearchHistory.objects.create(city='Kyiv')
        latest = SearchHistory.objects.first()
        self.assertEqual(latest.pk, second_entry.pk)


class IndexViewTest(TestCase):
    """Тести головної сторінки"""

    def setUp(self):
        self.client = Client()

    def test_index_returns_200(self):
        """Головна сторінка повертає статус 200"""
        response = self.client.get(reverse('index'))
        self.assertEqual(response.status_code, 200)

    def test_index_uses_correct_template(self):
        """Перевірка що використовується правильний шаблон"""
        response = self.client.get(reverse('index'))
        self.assertTemplateUsed(response, 'weather/index.html')


class HistoryViewTest(TestCase):
    """Тести API історії"""

    def setUp(self):
        self.client = Client()

    def test_get_history_empty(self):
        """Порожня історія повертає пустий список"""
        response = self.client.get(reverse('get_history'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['history'], [])

    def test_get_history_with_data(self):
        """Історія повертає збережені міста"""
        SearchHistory.objects.create(city='Lviv')
        SearchHistory.objects.create(city='Kyiv')
        response = self.client.get(reverse('get_history'))
        data = response.json()
        self.assertIn('Kyiv', data['history'])
        self.assertIn('Lviv', data['history'])

    def test_clear_history(self):
        """Очищення історії видаляє всі записи"""
        SearchHistory.objects.create(city='Lviv')
        response = self.client.post(reverse('clear_history'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(SearchHistory.objects.count(), 0)

    def test_clear_history_get_not_allowed(self):
        """GET запит на clear_history повертає 405"""
        response = self.client.get(reverse('clear_history'))
        self.assertEqual(response.status_code, 405)


class WeatherViewTest(TestCase):
    """Тести API погоди"""

    def setUp(self):
        self.client = Client()

    def test_weather_no_city(self):
        """Запит без міста повертає 400"""
        response = self.client.get(reverse('get_weather'))
        self.assertEqual(response.status_code, 400)

    @patch('weather.views.requests.get')
    def test_weather_city_not_found(self, mock_get):
        """Неіснуюче місто повертає 404"""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        response = self.client.get(reverse('get_weather'), {'city': 'НеіснуєМісто'})
        self.assertEqual(response.status_code, 404)

    @patch('weather.views.requests.get')
    def test_weather_success(self, mock_get):
        """Успішний запит повертає дані погоди"""
        mock_weather = MagicMock()
        mock_weather.status_code = 200
        mock_weather.json.return_value = {
            'name': 'Lviv',
            'sys': {'country': 'UA'},
            'main': {'temp': 10, 'feels_like': 8, 'humidity': 70},
            'weather': [{'description': 'clear', 'icon': '01d', 'main': 'Clear'}],
            'wind': {'speed': 3},
            'coord': {'lat': 49.8, 'lon': 24.0},
        }
        mock_forecast = MagicMock()
        mock_forecast.status_code = 200
        mock_forecast.json.return_value = {'list': []}
        mock_get.side_effect = [mock_weather, mock_forecast]

        response = self.client.get(reverse('get_weather'), {'city': 'Lviv'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('weather', data)
        self.assertIn('forecast', data)


class AutocompleteViewTest(TestCase):
    """Тести автодоповнення"""

    def setUp(self):
        self.client = Client()

    def test_autocomplete_short_query(self):
        """Запит менше 2 символів повертає пустий список"""
        response = self.client.get(reverse('autocomplete'), {'q': 'L'})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['cities'], [])