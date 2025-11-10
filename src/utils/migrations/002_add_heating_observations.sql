-- Migration 002: Heizungs-Beobachtungen für Analytics
-- Erstellt: 2025-11-10
-- Beschreibung: Fügt Tabelle für kontinuierliche Heizungsdaten-Sammlung hinzu

-- Haupttabelle für Heizungsbeobachtungen (alle 15 Minuten)
CREATE TABLE IF NOT EXISTS heating_observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL,
    device_id TEXT NOT NULL,
    room_name TEXT,
    current_temp REAL,
    target_temp REAL,
    is_heating BOOLEAN DEFAULT 0,
    outdoor_temp REAL,
    humidity REAL,
    hour_of_day INTEGER,
    day_of_week INTEGER,
    power_percentage REAL,
    FOREIGN KEY (device_id) REFERENCES devices(id)
);

-- Indizes für Performance
CREATE INDEX IF NOT EXISTS idx_heating_obs_timestamp
ON heating_observations(timestamp);

CREATE INDEX IF NOT EXISTS idx_heating_obs_device
ON heating_observations(device_id, timestamp);

CREATE INDEX IF NOT EXISTS idx_heating_obs_room
ON heating_observations(room_name, timestamp);

CREATE INDEX IF NOT EXISTS idx_heating_obs_heating
ON heating_observations(is_heating, timestamp);

-- Für Zeitanalysen
CREATE INDEX IF NOT EXISTS idx_heating_obs_time_patterns
ON heating_observations(hour_of_day, day_of_week);
