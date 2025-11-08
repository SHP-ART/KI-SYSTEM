"""Wetter-Daten Sammler"""

import requests
from typing import Dict, Optional
from loguru import logger
from datetime import datetime


class WeatherCollector:
    """Sammelt Wetterdaten von verschiedenen APIs"""

    def __init__(self, api_key: str = None, location: str = "Berlin, DE"):
        self.api_key = api_key
        self.location = location

    def get_openweathermap_data(self) -> Optional[Dict]:
        """
        Holt Wetterdaten von OpenWeatherMap
        Kostenlos bis 60 calls/minute
        API Key: https://openweathermap.org/api
        """
        if not self.api_key:
            logger.warning("No weather API key provided")
            return None

        try:
            url = "https://api.openweathermap.org/data/2.5/weather"
            params = {
                'q': self.location,
                'appid': self.api_key,
                'units': 'metric',
                'lang': 'de'
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            # Strukturiere die relevanten Daten
            return {
                'timestamp': datetime.now().isoformat(),
                'temperature': data['main']['temp'],
                'feels_like': data['main']['feels_like'],
                'humidity': data['main']['humidity'],
                'pressure': data['main']['pressure'],
                'weather_condition': data['weather'][0]['main'],
                'weather_description': data['weather'][0]['description'],
                'clouds': data['clouds']['all'],
                'wind_speed': data['wind']['speed'],
                'sunrise': datetime.fromtimestamp(data['sys']['sunrise']).isoformat(),
                'sunset': datetime.fromtimestamp(data['sys']['sunset']).isoformat(),
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"Weather API error: {e}")
            return None

    def get_forecast(self) -> Optional[Dict]:
        """
        Holt 5-Tage Wettervorhersage
        """
        if not self.api_key:
            return None

        try:
            url = "https://api.openweathermap.org/data/2.5/forecast"
            params = {
                'q': self.location,
                'appid': self.api_key,
                'units': 'metric',
                'lang': 'de'
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            # Parse nur die relevanten Vorhersagen (nächste 24h)
            forecasts = []
            for item in data['list'][:8]:  # 8 * 3h = 24h
                forecasts.append({
                    'timestamp': item['dt_txt'],
                    'temperature': item['main']['temp'],
                    'weather': item['weather'][0]['main'],
                    'rain_probability': item.get('pop', 0) * 100  # Probability of precipitation
                })

            return {
                'timestamp': datetime.now().isoformat(),
                'forecasts': forecasts
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"Forecast API error: {e}")
            return None

    def get_homey_weather(self, homey_collector) -> Optional[Dict]:
        """
        Nutzt Wetterdaten direkt von Homey
        Sammelt Temperatur/Luftfeuchtigkeit von Sensoren + DWD Warnungen
        """
        try:
            if hasattr(homey_collector, 'get_weather_data'):
                weather = homey_collector.get_weather_data()
                if weather:
                    logger.info("Weather data from Homey sensors")
                    return weather

        except Exception as e:
            logger.error(f"Error getting weather from Homey: {e}")

        return None

    def get_home_assistant_weather(self, ha_collector) -> Optional[Dict]:
        """
        Alternative: Nutzt Wetterdaten direkt von Home Assistant
        (falls dort bereits eine Wetterintegration konfiguriert ist)
        """
        try:
            # Home Assistant hat oft eine weather.* Entity
            weather_entities = ha_collector.get_all_entities(domain='weather')

            if not weather_entities:
                logger.warning("No weather entities found in Home Assistant")
                return None

            # Nimm die erste Weather-Entity
            weather_entity = weather_entities[0]
            state = ha_collector.get_state(weather_entity)

            if state:
                attrs = state['attributes']
                return {
                    'timestamp': datetime.now().isoformat(),
                    'temperature': attrs.get('temperature'),
                    'humidity': attrs.get('humidity'),
                    'pressure': attrs.get('pressure'),
                    'wind_speed': attrs.get('wind_speed'),
                    'weather_condition': state['state'],
                    'forecast': attrs.get('forecast', [])
                }

        except Exception as e:
            logger.error(f"Error getting weather from Home Assistant: {e}")

        return None

    def get_weather_data(self, platform_collector=None) -> Optional[Dict]:
        """
        Hauptmethode - holt OUTDOOR-Wetterdaten

        WICHTIG: Für Outdoor-Temperatur nutzen wir IMMER externe Wetter-APIs,
        da Homey/Home Assistant Sensoren sind meist INDOOR-Sensoren!

        Priorität:
        1. OpenWeatherMap API (empfohlen für genaue Outdoor-Daten)
        2. Home Assistant Weather-Integration (falls konfiguriert)
        3. Fallback: Homey Sensoren (nur wenn keine API verfügbar)
        """
        # Bevorzuge externe Wetter-API für genaue Outdoor-Daten
        if self.api_key:
            weather = self.get_openweathermap_data()
            if weather:
                logger.info("Weather data from OpenWeatherMap (Outdoor)")
                return weather

        # Fallback: Versuche Home Assistant Weather-Integration
        if platform_collector and hasattr(platform_collector, 'get_all_entities'):
            weather = self.get_home_assistant_weather(platform_collector)
            if weather:
                logger.info("Weather data from Home Assistant (Outdoor)")
                return weather

        # Letzter Fallback: Homey Sensoren (meist Indoor!)
        if platform_collector and hasattr(platform_collector, 'get_weather_data'):
            weather = self.get_homey_weather(platform_collector)
            if weather:
                logger.warning("Using Homey sensors for outdoor weather - may be inaccurate!")
                return weather

        logger.warning("No weather data available")
        return None
