function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        for (const cookie of document.cookie.split(';')) {
            const c = cookie.trim();
            if (c.startsWith(name + '=')) {
                cookieValue = decodeURIComponent(c.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

const weatherVideos = {
    'clear':        'https://assets.mixkit.co/videos/preview/mixkit-sunny-clear-sky-4438-large.mp4',
    'clouds':       'https://assets.mixkit.co/videos/preview/mixkit-clouds-and-blue-sky-2408-large.mp4',
    'rain':         'https://assets.mixkit.co/videos/preview/mixkit-rain-falling-on-the-water-of-a-lake-seen-up-close-18312-large.mp4',
    'drizzle':      'https://assets.mixkit.co/videos/preview/mixkit-rain-falling-on-the-water-of-a-lake-seen-up-close-18312-large.mp4',
    'thunderstorm': 'https://assets.mixkit.co/videos/preview/mixkit-lightning-storm-in-the-city-4398-large.mp4',
    'snow':         'https://assets.mixkit.co/videos/preview/mixkit-snowflakes-in-the-air-in-winter-4382-large.mp4',
    'mist':         'https://assets.mixkit.co/videos/preview/mixkit-misty-forest-in-the-morning-327-large.mp4',
    'default':      'https://assets.mixkit.co/videos/preview/mixkit-clouds-and-blue-sky-2408-large.mp4',
};

let map = null;
let marker = null;

function setWeatherVideo(weatherMain) {
    const video = document.getElementById('bg-video');
    const src = weatherVideos[weatherMain.toLowerCase()] || weatherVideos['default'];
    if (video.src !== src) {
        video.style.opacity = '0';
        video.src = src;
        video.load();
        video.play().catch(() => {});
        setTimeout(() => { video.style.opacity = '1'; }, 500);
    }
}

function getDayName(dateStr) {
    const days = ['Нд', 'Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб'];
    return days[new Date(dateStr).getDay()];
}

function updateMap(lat, lon) {
    document.querySelector('.map-container').style.display = 'block';
    if (!map) {
        map = L.map('map').setView([lat, lon], 11);
        L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
            attribution: '© OpenStreetMap © CARTO'
        }).addTo(map);
        marker = L.marker([lat, lon]).addTo(map);
    } else {
        map.setView([lat, lon], 11);
        marker.setLatLng([lat, lon]);
    }
}

function renderWeather(data) {
    const { weather, forecast } = data;

    document.querySelector('.weather-main').style.display = 'block';
    document.getElementById('city-name').textContent = `${weather.name}, ${weather.sys.country}`;
    document.getElementById('temperature').textContent = `${Math.round(weather.main.temp)}°C`;
    document.getElementById('description').textContent = weather.weather[0].description;
    document.getElementById('weather-icon').src = `https://openweathermap.org/img/wn/${weather.weather[0].icon}@2x.png`;
    document.getElementById('feels-like').textContent = `${Math.round(weather.main.feels_like)}°C`;
    document.getElementById('humidity').textContent = `${weather.main.humidity}%`;
    document.getElementById('wind').textContent = `${Math.round(weather.wind.speed)} м/с`;

    setWeatherVideo(weather.weather[0].main);
    updateMap(weather.coord.lat, weather.coord.lon);

    const forecastContainer = document.querySelector('.forecast-container');
    forecastContainer.style.display = 'block';

    const daily = forecast.list.filter(i => i.dt_txt.includes('12:00:00')).slice(0, 5);
    const forecastDays = document.getElementById('forecast-days');
    forecastDays.innerHTML = '';
    daily.forEach(item => {
        const div = document.createElement('div');
        div.className = 'forecast-day';
        div.innerHTML = `
            <div class="day-name">${getDayName(item.dt_txt)}</div>
            <img src="https://openweathermap.org/img/wn/${item.weather[0].icon}.png" alt="">
            <div class="temp">${Math.round(item.main.temp)}°</div>
        `;
        forecastDays.appendChild(div);
    });

    loadHistory();
}

async function searchWeather(city) {
    if (!city.trim()) return;
    hideError();
    try {
        const resp = await fetch(`/api/weather/?city=${encodeURIComponent(city)}`);
        const data = await resp.json();
        if (!resp.ok) { showError(data.error || 'Помилка'); return; }
        renderWeather(data);
    } catch (e) {
        showError('Помилка з\'єднання');
    }
}

async function loadHistory() {
    try {
        const resp = await fetch('/api/history/');
        const data = await resp.json();
        renderHistory(data.history);
    } catch (e) {}
}

function renderHistory(cities) {
    const container = document.querySelector('.history-container');
    const tagsDiv = document.getElementById('history-tags');
    if (!cities || cities.length === 0) { container.style.display = 'none'; return; }
    container.style.display = 'block';
    tagsDiv.innerHTML = '';
    cities.forEach(city => {
        const tag = document.createElement('span');
        tag.className = 'history-tag';
        tag.textContent = city;
        tag.onclick = () => {
            document.getElementById('city-input').value = city;
            searchWeather(city);
        };
        tagsDiv.appendChild(tag);
    });
}

let autocompleteTimeout = null;

async function fetchAutocomplete(query) {
    try {
        const resp = await fetch(`/api/autocomplete/?q=${encodeURIComponent(query)}`);
        const data = await resp.json();
        const list = document.getElementById('autocomplete-list');
        list.innerHTML = '';
        if (!data.cities || data.cities.length === 0) { list.style.display = 'none'; return; }
        data.cities.forEach(city => {
            const div = document.createElement('div');
            div.textContent = `${city.name}${city.country ? ', ' + city.country : ''}`;
            div.onclick = () => {
                document.getElementById('city-input').value = city.name;
                list.style.display = 'none';
                searchWeather(city.name);
            };
            list.appendChild(div);
        });
        list.style.display = 'block';
    } catch (e) {}
}

function showError(msg) {
    const el = document.getElementById('error-msg');
    el.textContent = msg;
    el.style.display = 'block';
}

function hideError() {
    document.getElementById('error-msg').style.display = 'none';
}

document.addEventListener('DOMContentLoaded', () => {
    document.addEventListener('click', () => {
        const video = document.getElementById('bg-video');
        if (video.paused) video.play().catch(() => {});
    }, { once: true });

    document.getElementById('city-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            document.getElementById('autocomplete-list').style.display = 'none';
            searchWeather(e.target.value);
        }
    });

    document.getElementById('city-input').addEventListener('input', (e) => {
        clearTimeout(autocompleteTimeout);
        if (e.target.value.length < 2) { document.getElementById('autocomplete-list').style.display = 'none'; return; }
        autocompleteTimeout = setTimeout(() => fetchAutocomplete(e.target.value), 300);
    });

    document.addEventListener('click', (e) => {
        if (!e.target.closest('.search-wrap')) {
            document.getElementById('autocomplete-list').style.display = 'none';
        }
    });

    document.getElementById('clear-history-btn').addEventListener('click', async () => {
        await fetch('/api/history/clear/', {
            method: 'POST',
            headers: { 'X-CSRFToken': getCookie('csrftoken') }
        });
        loadHistory();
    });

    // Геолокація при старті
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            async (pos) => {
                try {
                    const resp = await fetch(`/api/weather/?lat=${pos.coords.latitude}&lon=${pos.coords.longitude}`);
                    const data = await resp.json();
                    if (resp.ok) renderWeather(data);
                } catch (e) {}
            },
            () => {}
        );
    }

    loadHistory();
});