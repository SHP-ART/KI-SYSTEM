-- Migration 001: Kontinuierliche Badezimmer-Messungen (alle 60s)
-- Erstellt: 2025-11-09
-- Beschreibung: Fügt Tabelle für kontinuierliche Temp/Luftfeuchtigkeits-Messungen hinzu

CREATE TABLE IF NOT EXISTS bathroom_continuous_measurements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL,
    humidity REAL,
    temperature REAL
);

-- Index für schnellere Zeitbereichs-Abfragen
CREATE INDEX IF NOT EXISTS idx_bathroom_continuous_timestamp
ON bathroom_continuous_measurements(timestamp);
