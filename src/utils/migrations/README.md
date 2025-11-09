# Datenbank-Migrationen

Dieses System verwaltet automatische Schema-Updates für die SQLite-Datenbank.

## Wie es funktioniert

- Beim Start wird `Database.__init__()` aufgerufen
- `_run_migrations()` prüft auf neue Migrations-Dateien
- Jede Migration wird nur einmal ausgeführt (getrackt in `schema_migrations` Tabelle)
- Migrationen laufen in Transaktionen (atomare Operationen)

## Neue Migration erstellen

### 1. Migrations-Datei anlegen

Erstelle eine neue `.sql` Datei mit dem Format:
```
<VERSION>_<NAME>.sql
```

Beispiel: `002_add_heating_predictions.sql`

**Wichtig:**
- VERSION muss eine 3-stellige Zahl sein (001, 002, 003, ...)
- NAME sollte beschreibend sein (snake_case)
- Dateien werden in aufsteigender Reihenfolge ausgeführt

### 2. SQL-Code schreiben

Die Migrations-Datei enthält normales SQL:

```sql
-- Migration 002: Heizungs-Vorhersagen
-- Erstellt: 2025-11-10
-- Beschreibung: Fügt Tabelle für ML-basierte Heizungsvorhersagen hinzu

CREATE TABLE IF NOT EXISTS heating_predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL,
    device_id TEXT NOT NULL,
    predicted_temperature REAL,
    confidence REAL
);

-- Index für Performance
CREATE INDEX IF NOT EXISTS idx_heating_predictions_time
ON heating_predictions(timestamp, device_id);
```

**Best Practices:**
- Verwende immer `IF NOT EXISTS` (idempotent!)
- Füge Kommentare mit Version, Datum und Beschreibung hinzu
- Erstelle Indizes für häufig abgefragte Spalten
- Teste die Migration lokal vor dem Commit

### 3. Migration testen

```bash
# Starte die Anwendung - Migration läuft automatisch
python3 main.py web

# Oder teste direkt in Python:
from src.utils.database import Database
db = Database()
```

Logs sollten zeigen:
```
✅ Applied migration 002: add_heating_predictions
✅ Successfully applied 1 database migration(s)
```

### 4. Migration verifizieren

```bash
# Prüfe ob Tabelle existiert
sqlite3 data/ki_system.db ".tables"

# Prüfe Schema
sqlite3 data/ki_system.db ".schema heating_predictions"

# Prüfe Migrations-Status
sqlite3 data/ki_system.db "SELECT * FROM schema_migrations"
```

## Beispiele

### Neue Tabelle hinzufügen

```sql
-- 003_add_user_preferences.sql
CREATE TABLE IF NOT EXISTS user_preferences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    preference_key TEXT NOT NULL,
    preference_value TEXT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_user_pref_key
ON user_preferences(user_id, preference_key);
```

### Spalte zu bestehender Tabelle hinzufügen

```sql
-- 004_add_priority_to_decisions.sql
ALTER TABLE decisions ADD COLUMN priority INTEGER DEFAULT 5;

CREATE INDEX IF NOT EXISTS idx_decisions_priority
ON decisions(priority, timestamp);
```

### Daten migrieren

```sql
-- 005_normalize_temperature_units.sql
-- Konvertiere alle Fahrenheit zu Celsius
UPDATE sensor_data
SET value = (value - 32) * 5/9
WHERE sensor_type = 'temperature' AND unit = 'F';

UPDATE sensor_data
SET unit = 'C'
WHERE sensor_type = 'temperature' AND unit = 'F';
```

## Troubleshooting

### Migration schlägt fehl

```
❌ Failed to apply migration 002 (add_heating_predictions): ...
```

**Lösung:**
1. Prüfe SQL-Syntax
2. Teste SQL manuell: `sqlite3 data/ki_system.db < migrations/002_add_heating_predictions.sql`
3. Prüfe ob Tabelle/Spalte bereits existiert
4. Verwende `IF NOT EXISTS` und `IF EXISTS`

### Migration wurde nicht erkannt

**Prüfe:**
- Dateiname-Format korrekt? `001_name.sql`
- Datei im richtigen Verzeichnis? `src/utils/migrations/`
- Version nicht bereits verwendet?

### Migration zurücksetzen (Development only!)

```bash
# WARNUNG: Löscht Daten!
sqlite3 data/ki_system.db "DELETE FROM schema_migrations WHERE version = 002"

# Dann neu starten
python3 main.py web
```

**Für Production:** Erstelle eine Reverse-Migration statt zu löschen!

## Migration-Status abfragen

```python
from src.utils.migrations import MigrationManager

migrator = MigrationManager('data/ki_system.db')

# Aktuell version
print(f"Current version: {migrator.get_current_version()}")

# Alle angewendeten Migrationen
for migration in migrator.get_migration_history():
    print(f"{migration['version']:03d}: {migration['name']} ({migration['applied_at']})")

# Ausstehende Migrationen
pending = migrator.get_pending_migrations()
print(f"{len(pending)} pending migrations")
```

## Wichtige Regeln

✅ **DO:**
- Verwende `IF NOT EXISTS` / `IF EXISTS`
- Teste Migrationen lokal
- Schreibe klare Kommentare
- Behalte Migrations-Dateien im Git
- Verwende aufsteigende Versionsnummern

❌ **DON'T:**
- Migrations-Dateien nach dem Merge ändern
- Versionsnummern wiederverwenden
- SQL ohne `IF NOT EXISTS` (außer bei ALTER)
- Migrationen in Production manuell löschen
- Migrations-Dateien aus Git entfernen
