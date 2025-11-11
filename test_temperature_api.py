#!/usr/bin/env python3
"""Test-Script für temperature-history API"""

import sqlite3
from datetime import datetime, timedelta
from collections import defaultdict
import statistics
import json

db_path = "data/ki_system.db"

# Zeitfenster
hours_back = 24
now = datetime.now()
start_time = now - timedelta(hours=hours_back)

print(f"Testing temperature-history API logic...")
print(f"Time window: {start_time} to {now}")
print(f"Hours back: {hours_back}")
print()

# Verbinde zur DB
conn = sqlite3.connect(db_path)

# Hole Temperaturdaten
query = """
    SELECT timestamp, value, metadata
    FROM sensor_data
    WHERE sensor_type = 'temperature'
    AND timestamp >= ?
    ORDER BY timestamp ASC
"""
cursor = conn.execute(query, (start_time.isoformat(),))
temp_data = cursor.fetchall()

print(f"Found {len(temp_data)} temperature readings")

# Hole Außentemperaturen
query = """
    SELECT timestamp, data
    FROM external_data
    WHERE data_type = 'weather'
    AND timestamp >= ?
    ORDER BY timestamp ASC
"""
cursor = conn.execute(query, (start_time.isoformat(),))
weather_data = cursor.fetchall()

print(f"Found {len(weather_data)} weather readings")
print()

if not temp_data and not weather_data:
    print("❌ No data available")
    exit(1)

# Gruppiere nach Stunde
hourly_data = defaultdict(lambda: {
    'indoor_temps': [],
    'outdoor_temps': [],
    'target_temps': []
})

# Verarbeite Temperaturen
for row in temp_data:
    timestamp = datetime.fromisoformat(row[0]) if isinstance(row[0], str) else row[0]
    hour_key = timestamp.replace(minute=0, second=0, microsecond=0)

    value = float(row[1])
    if 5 < value < 30:  # Filter
        hourly_data[hour_key]['indoor_temps'].append(value)

# Verarbeite Wetter
for row in weather_data:
    timestamp = datetime.fromisoformat(row[0]) if isinstance(row[0], str) else row[0]
    hour_key = timestamp.replace(minute=0, second=0, microsecond=0)

    data_json = json.loads(row[1]) if isinstance(row[1], str) else row[1]
    outdoor_temp = data_json.get('temperature')

    if outdoor_temp is not None:
        hourly_data[hour_key]['outdoor_temps'].append(float(outdoor_temp))

# Erstelle Arrays
timestamps = []
indoor_temps = []
outdoor_temps = []

for hour in sorted(hourly_data.keys()):
    data = hourly_data[hour]
    timestamps.append(hour.isoformat())

    indoor_temps.append(
        round(statistics.mean(data['indoor_temps']), 1)
        if data['indoor_temps'] else None
    )
    outdoor_temps.append(
        round(statistics.mean(data['outdoor_temps']), 1)
        if data['outdoor_temps'] else None
    )

print(f"Generated {len(timestamps)} hourly data points")
print()
print("Sample data (first 5):")
for i in range(min(5, len(timestamps))):
    print(f"  {timestamps[i]}: Indoor={indoor_temps[i]}°C, Outdoor={outdoor_temps[i]}°C")

print()
print("Result:")
print(f"  Timestamps: {len(timestamps)}")
print(f"  Indoor temps (non-null): {sum(1 for t in indoor_temps if t is not None)}")
print(f"  Outdoor temps (non-null): {sum(1 for t in outdoor_temps if t is not None)}")

if len(timestamps) > 0:
    print("\n✅ API would return data")
else:
    print("\n❌ API would return empty data")

conn.close()
