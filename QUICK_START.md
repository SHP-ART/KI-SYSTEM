# Quick Start Guide

## In 5 Minuten zum laufenden System

### 1. Setup ausführen

```bash
chmod +x setup.sh
./setup.sh
```

### 2. Home Assistant Token erstellen

1. Öffne Home Assistant in deinem Browser
2. Klicke auf dein Profil (unten links)
3. Scrolle runter zu "Long-lived access tokens"
4. Klicke "Create Token"
5. Gib einen Namen ein (z.B. "KI-System")
6. Kopiere den Token (nur einmal sichtbar!)

### 3. Konfiguration einrichten

Bearbeite `.env`:

```bash
nano .env
```

Mindest-Konfiguration:

```bash
PLATFORM_TYPE=homeassistant  # oder "homey"
HA_URL=http://192.168.1.100:8123  # Deine Home Assistant IP
HA_TOKEN=dein_super_langer_token_hier

# Optional - Wetter & Strompreise
# WEATHER_API_KEY=dein_key  # Optional, empfohlen
# ENERGY_API_KEY=dein_key   # Optional, nur wenn du dynamische Tarife hast
```

**Hinweis:** Energiepreis-Integration ist standardmäßig deaktiviert und nur sinnvoll, wenn du einen dynamischen Stromtarif (aWATTar/Tibber) hast.

### 4. Sensor-IDs finden

In Home Assistant:
1. Gehe zu "Developer Tools" → "States"
2. Suche deine Sensoren (z.B. `sensor.wohnzimmer_temperature`)
3. Kopiere die Entity-IDs

Bearbeite `config/config.yaml`:

```bash
nano config/config.yaml
```

Trage deine Sensor-IDs ein:

```yaml
data_collection:
  sensors:
    temperature:
      - sensor.wohnzimmer_temperature
      - sensor.schlafzimmer_temperature
    light:
      - sensor.wohnzimmer_helligkeit
    motion:
      - binary_sensor.wohnzimmer_bewegung
```

### 5. Verbindung testen

```bash
python main.py test
```

Erwartete Ausgabe:

```
=== Connection Test Results ===
✓ home_assistant: OK
✓ weather_api: OK
✓ energy_prices: OK
✓ database: OK

Overall: ✓ All systems operational
```

### 6. System starten

#### Option A: Einmal ausführen (zum Testen)

```bash
python main.py run
```

#### Option B: Daemon-Modus (dauerhaft)

```bash
python main.py daemon
```

#### Option C: Als Systemd Service (empfohlen)

```bash
# Service-Datei erstellen
sudo nano /etc/systemd/system/ki-system.service
```

Inhalt (passe Pfade an):

```ini
[Unit]
Description=KI Smart Home System
After=network.target

[Service]
Type=simple
User=dein-username
WorkingDirectory=/pfad/zum/KI-SYSTEM
ExecStart=/pfad/zum/KI-SYSTEM/venv/bin/python main.py daemon
Restart=always

[Install]
WantedBy=multi-user.target
```

Service starten:

```bash
sudo systemctl enable ki-system
sudo systemctl start ki-system
sudo systemctl status ki-system
```

## Erste Schritte nach Installation

### Status prüfen

```bash
python main.py status
```

### Learning-Modus (empfohlen für erste Tage)

Bearbeite `config/config.yaml`:

```yaml
decision_engine:
  mode: "learning"  # System sammelt Daten, aber führt keine Aktionen aus
```

Nach 3-5 Tagen auf Auto-Modus umstellen:

```yaml
decision_engine:
  mode: "auto"  # System trifft automatisch Entscheidungen
```

### Logs überwachen

```bash
tail -f logs/ki_system.log
```

## Häufige Probleme

### "Connection refused" bei Home Assistant

```bash
# Prüfe ob Home Assistant läuft
curl http://192.168.1.100:8123

# Prüfe Firewall
sudo ufw status
```

### "Invalid token"

- Token neu erstellen in Home Assistant
- Achte auf Leerzeichen beim Kopieren
- Token in `.env` ohne Anführungszeichen

### Keine Sensor-Daten

- Prüfe Entity-IDs in Home Assistant Developer Tools
- Entity-IDs sind case-sensitive!
- Format: `domain.name` (z.B. `sensor.temperatur`, nicht `Sensor.Temperatur`)

### Service startet nicht

```bash
# Logs prüfen
sudo journalctl -u ki-system -f

# Permissions prüfen
ls -la /pfad/zum/KI-SYSTEM
```

## Nächste Schritte

1. **Lass das System 3-5 Tage Daten sammeln** im Learning-Modus
2. **Trainiere die Modelle**: `python main.py train`
3. **Wechsle zu Auto-Modus** in config.yaml
4. **Überwache die ersten Aktionen** via Logs
5. **Optimiere die Einstellungen** basierend auf Ergebnissen

## Support

- README.md für detaillierte Dokumentation
- GitHub Issues für Probleme
- Logs in `logs/ki_system.log` für Debugging

Viel Erfolg! 🚀
