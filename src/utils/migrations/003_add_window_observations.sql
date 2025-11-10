-- Migration 003: Fenster-Beobachtungen für Heizungsoptimierung
-- Erstellt: 2025-11-10
-- Beschreibung: Fügt Tabelle für kontinuierliche Fenster-Status-Sammlung hinzu (alle 60s)

-- Haupttabelle für Fenster-Beobachtungen (alle 60 Sekunden)
CREATE TABLE IF NOT EXISTS window_observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL,
    device_id TEXT NOT NULL,
    device_name TEXT,
    room_name TEXT,
    is_open BOOLEAN DEFAULT 0,
    contact_alarm BOOLEAN DEFAULT 0,
    FOREIGN KEY (device_id) REFERENCES devices(id)
);

-- Indizes für Performance
CREATE INDEX IF NOT EXISTS idx_window_obs_timestamp
ON window_observations(timestamp);

CREATE INDEX IF NOT EXISTS idx_window_obs_device
ON window_observations(device_id, timestamp);

CREATE INDEX IF NOT EXISTS idx_window_obs_room
ON window_observations(room_name, timestamp);

CREATE INDEX IF NOT EXISTS idx_window_obs_open_status
ON window_observations(is_open, timestamp);

-- View für offene Fenster-Dauer (praktisch für Abfragen)
CREATE VIEW IF NOT EXISTS v_current_open_windows AS
SELECT
    device_id,
    device_name,
    room_name,
    MIN(timestamp) as opened_at,
    MAX(timestamp) as last_seen,
    CAST((julianday('now') - julianday(MIN(timestamp))) * 24 * 60 AS INTEGER) as minutes_open
FROM window_observations
WHERE is_open = 1
GROUP BY device_id, device_name, room_name
HAVING MAX(timestamp) >= datetime('now', '-2 minutes');
