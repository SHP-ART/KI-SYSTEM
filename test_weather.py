#!/usr/bin/env python3
"""
Test-Script für Wetter-API
"""

import sys
from pathlib import Path

# Füge src zum Python-Path hinzu
sys.path.insert(0, str(Path(__file__).parent))

from src.data_collector.weather_collector import WeatherCollector
from src.utils.config_loader import ConfigLoader
import json

print("=== Wetter-API Test ===\n")

# Lade Config
config = ConfigLoader()

# Hole Weather API Key
weather_key = config.get('external_data.weather.api_key')
weather_location = config.get('external_data.weather.location', 'Berlin, DE')

print(f"Weather API Key: {'✓ Vorhanden' if weather_key else '✗ Fehlt'}")
print(f"Location: {weather_location}\n")

if not weather_key:
    print("❌ Kein Weather API Key konfiguriert!")
    print("Bitte WEATHER_API_KEY in .env eintragen")
    sys.exit(1)

# Erstelle WeatherCollector
weather = WeatherCollector(weather_key, weather_location)

# Test 1: Aktuelle Wetterdaten
print("--- Test 1: Aktuelle Wetterdaten ---")
current_weather = weather.get_openweathermap_data()

if current_weather:
    print("✓ Wetterdaten erfolgreich abgerufen!")
    print(f"\nTemperatur: {current_weather.get('temperature')}°C")
    print(f"Gefühlt: {current_weather.get('feels_like')}°C")
    print(f"Luftfeuchtigkeit: {current_weather.get('humidity')}%")
    print(f"Wetter: {current_weather.get('weather_condition')} - {current_weather.get('weather_description')}")
    print(f"Wind: {current_weather.get('wind_speed')} m/s")
    print(f"Luftdruck: {current_weather.get('pressure')} hPa")
    print(f"Bewölkung: {current_weather.get('clouds')}%")
    print(f"\nRohdaten:")
    print(json.dumps(current_weather, indent=2, ensure_ascii=False))
else:
    print("✗ Keine Wetterdaten erhalten!")
    print("\nMögliche Probleme:")
    print("1. Ungültiger API Key")
    print("2. Ungültige Location")
    print("3. API-Limit erreicht")
    print("4. Netzwerkproblem")

print("\n--- Test 2: Wettervorhersage ---")
forecast = weather.get_forecast()

if forecast:
    print("✓ Wettervorhersage erfolgreich abgerufen!")
    print(f"\nAnzahl Zeitpunkte: {len(forecast.get('forecasts', []))}")
    for item in forecast.get('forecasts', [])[:3]:
        print(f"  {item['timestamp']}: {item['temperature']}°C, {item['weather']}, Regen: {item['rain_probability']}%")
else:
    print("✗ Keine Wettervorhersage erhalten!")

print("\n=== Test abgeschlossen ===")
