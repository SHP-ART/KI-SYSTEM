# Database Schema

Diagramm der Datenbankstruktur für das KI Smart Home System.

## Entity Relationship Diagram

```mermaid
erDiagram
    %% Continuous Measurements Table (ML Training Data)
    CONTINUOUS_MEASUREMENTS {
        integer id PK
        text timestamp
        text device_id
        real current_temperature
        real target_temperature
        real outdoor_temperature
        integer heating_active
        integer presence
        integer window_open
        integer hour_of_day
        integer day_of_week
        text weather_condition
        real energy_price
        integer hvac_mode
        real humidity
    }

    %% Lighting Events Table (ML Training Data)
    LIGHTING_EVENTS {
        integer id PK
        text timestamp
        text device_id
        text state
        real brightness
        integer hour_of_day
        real outdoor_light
        integer presence
        integer motion_detected
    }

    %% Heating Observations Table (Analytics)
    HEATING_OBSERVATIONS {
        integer id PK
        text timestamp
        text room_name
        real current_temperature
        real target_temperature
        real outdoor_temperature
        integer heating_active
        integer window_open
        integer presence_detected
        text weather_condition
        real energy_price_level
        text hvac_mode
    }

    %% Bathroom Observations Table
    BATHROOM_OBSERVATIONS {
        integer id PK
        text timestamp
        real temperature
        real humidity
        real dew_point
        integer shower_active
        integer ventilation_on
        text recommendation
    }

    %% Window Observations Table
    WINDOW_OBSERVATIONS {
        integer id PK
        text timestamp
        text room_name
        integer window_open
        real indoor_temperature
        real outdoor_temperature
        integer heating_active
        text recommendation
    }

    %% Devices Table
    DEVICES {
        text device_id PK
        text name
        text device_class
        text zone_id
        text zone_name
        text platform
        text last_seen
    }

    %% Zones Table
    ZONES {
        text zone_id PK
        text name
        text platform
    }

    %% Automations Table
    AUTOMATIONS {
        text automation_id PK
        text name
        integer enabled
        text trigger_type
        text conditions
        text actions
        text last_executed
    }

    %% ML Models Metadata Table
    ML_MODELS {
        text model_type PK
        text last_trained
        integer training_samples
        real accuracy
        text model_path
        text metrics
    }

    %% Energy Prices Table
    ENERGY_PRICES {
        integer id PK
        text timestamp
        real price_per_kwh
        text price_level
        text source
    }

    %% Weather Data Table
    WEATHER_DATA {
        integer id PK
        text timestamp
        real temperature
        real humidity
        real pressure
        text description
        text icon
    }

    %% System Logs Table
    SYSTEM_LOGS {
        integer id PK
        text timestamp
        text level
        text component
        text message
        text details
    }

    %% Relationships
    CONTINUOUS_MEASUREMENTS ||--o| DEVICES : "device_id"
    LIGHTING_EVENTS ||--o| DEVICES : "device_id"
    HEATING_OBSERVATIONS ||--o{ ZONES : "room_name"
    BATHROOM_OBSERVATIONS ||--o{ ZONES : "bathroom"
    WINDOW_OBSERVATIONS ||--o{ ZONES : "room_name"
    DEVICES ||--o{ ZONES : "zone_id"
    AUTOMATIONS ||--o{ DEVICES : "controls"
```

## Tabellen-Details

### 1. continuous_measurements
**Zweck:** ML-Trainingsdaten für Temperaturmodell  
**Sammlung:** Alle 5 Minuten (TemperatureDataCollector)  
**Größe:** ~100k Einträge/Jahr  
**Indizes:** `idx_continuous_timestamp`, `idx_continuous_device`

### 2. lighting_events
**Zweck:** ML-Trainingsdaten für Beleuchtungsmodell  
**Sammlung:** Bei Zustandsänderungen (LightingDataCollector, 60s Intervall)  
**Größe:** ~50k Einträge/Jahr  
**Indizes:** `idx_lighting_timestamp`, `idx_lighting_device`

### 3. heating_observations
**Zweck:** Heizungs-Analytics und historische Daten  
**Sammlung:** Alle 15 Minuten (HeatingDataCollector)  
**Größe:** ~35k Einträge/Jahr  
**Indizes:** `idx_heating_timestamp`, `idx_heating_room`

### 4. bathroom_observations
**Zweck:** Schimmelprävention und Luftfeuchtigkeit-Monitoring  
**Sammlung:** Alle 5 Minuten (BathroomDataCollector)  
**Größe:** ~100k Einträge/Jahr  
**Indizes:** `idx_bathroom_timestamp`

### 5. window_observations
**Zweck:** Fenster-offen-Erkennung und Heizungsoptimierung  
**Sammlung:** Bei Zustandsänderungen (WindowDataCollector)  
**Größe:** ~10k Einträge/Jahr  
**Indizes:** `idx_window_timestamp`

### 6. devices
**Zweck:** Geräte-Registry (Homey & Home Assistant)  
**Aktualisierung:** Bei jedem API-Call  
**Größe:** ~100 Einträge

### 7. zones
**Zweck:** Raum-/Zonen-Verwaltung  
**Aktualisierung:** Selten  
**Größe:** ~10 Einträge

### 8. automations
**Zweck:** Automatisierungs-Verwaltung  
**Aktualisierung:** Bei Änderungen durch UI  
**Größe:** ~20 Einträge

### 9. ml_models
**Zweck:** Metadaten zu trainierten ML-Modellen  
**Aktualisierung:** Bei Training  
**Größe:** 2 Einträge (Lighting, Temperature)

### 10. energy_prices
**Zweck:** Energiepreis-Historie (aWATTar)  
**Sammlung:** Stündlich (EnergyPriceCollector)  
**Größe:** ~8k Einträge/Jahr  
**Indizes:** `idx_energy_timestamp`

### 11. weather_data
**Zweck:** Wetterdaten (OpenWeatherMap)  
**Sammlung:** Alle 30 Minuten (WeatherCollector)  
**Größe:** ~17k Einträge/Jahr  
**Indizes:** `idx_weather_timestamp`

### 12. system_logs
**Zweck:** System-Logging (optional)  
**Sammlung:** Bei Events  
**Größe:** Variable

## Datenfluss

```mermaid
graph TD
    A[Homey/HA APIs] -->|Collectors| B[Raw Data]
    B --> C{Data Type}
    C -->|Temperatures| D[continuous_measurements]
    C -->|Lighting| E[lighting_events]
    C -->|Heating Status| F[heating_observations]
    C -->|Bathroom| G[bathroom_observations]
    C -->|Windows| H[window_observations]
    
    D --> I[ML Temperature Model]
    E --> J[ML Lighting Model]
    
    I --> K[Predictions]
    J --> K
    
    K --> L[Decision Engine]
    L --> M[Automations]
    M --> N[Device Control]
    N --> A
    
    F --> O[Analytics Dashboard]
    G --> O
    H --> O
```

## Speicherplatz-Schätzungen

| Zeitraum | Geschätzte DB-Größe |
|----------|---------------------|
| 1 Woche  | ~5 MB               |
| 1 Monat  | ~20 MB              |
| 3 Monate | ~60 MB              |
| 1 Jahr   | ~250 MB             |
| 2 Jahre  | ~500 MB             |

## Wartung

### Automatisches Cleanup
```python
# In database_maintenance.py
db.cleanup_old_data(days=365)  # Läuft täglich
```

### Manuelle Wartung
```bash
# VACUUM (Defragmentierung)
sqlite3 data/ki_system.db "VACUUM;"

# Größe prüfen
du -h data/ki_system.db

# Tabellengrößen
sqlite3 data/ki_system.db "SELECT name, SUM(pgsize) FROM dbstat GROUP BY name;"
```

## Performance-Optimierungen

### WAL-Modus (Write-Ahead Logging)
```sql
PRAGMA journal_mode=WAL;
```
Bessere Concurrency für Read/Write-Zugriffe.

### Indizes
Alle kritischen Tabellen haben Timestamp- und Device-ID-Indizes.

### Prepared Statements
Alle Queries verwenden Parameterized Statements (SQL-Injection-Schutz).

## Migrationen

Siehe `src/utils/migrations/` für Schema-Änderungen:
- `001_add_continuous_measurements.sql`
- `002_add_heating_observations.sql`
- `003_add_window_observations.sql`

Neue Migrationen werden automatisch bei Start erkannt und ausgeführt.
