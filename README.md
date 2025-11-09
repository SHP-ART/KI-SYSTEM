# KI-System für Smart Home Automatisierung

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/version-0.8-blue.svg)](https://github.com/dein-username/KI-SYSTEM/releases)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

Ein intelligentes Machine Learning-basiertes System zur automatischen Steuerung von Beleuchtung, Heizung und anderen Smart-Home-Geräten. Das System lernt aus deinem Verhalten und optimiert automatisch Energieverbrauch und Komfort.

**Version:** 0.8 | **Unterstützte Plattformen:** 🏠 Home Assistant · 🔷 Homey Pro

[Features](#features) · [Installation](#installation) · [Web-Dashboard](#web-dashboard) · [Dokumentation](#dokumentation) · [Contributing](CONTRIBUTING.md)

## 🆕 Was ist neu in Version 0.8?

- **🌐 Web-Dashboard**: Komplett neues Web-Interface mit modernem Design
- **🚿 Badezimmer-Automatisierung**: Selbstlernendes System für intelligente Luftentfeuchter-Steuerung
- **📊 Analytics-Dashboards**: Interaktive Charts für Temperatur und Luftfeuchtigkeit
- **🤖 Automatische Optimierung**: Tägliche Schwellwert-Optimierung basierend auf historischen Daten
- **📈 Trend-Analyse**: Visualisierung von Mustern und Vorhersagen
- **🔄 Hintergrund-Datensammlung**: Automatisches Sensor-Logging alle 5 Minuten
- **🏠 Raum-Management**: Verbesserte Raum- und Geräteverwaltung
- **📱 Responsive Design**: Optimiert für Desktop, Tablet und Smartphone

## Features

### 🎯 Core Features

- **Machine Learning Steuerung**
  - Intelligente Beleuchtungssteuerung basierend auf Tageszeit, Helligkeit, Bewegung
  - Adaptive Temperaturregelung mit Wettervorhersage
  - Lernt aus deinem Verhalten und passt sich an

- **Energieoptimierung**
  - Intelligente Heizungssteuerung
  - Optional: Dynamische Strompreise (aWATTar, Tibber)
  - Energiespar-Empfehlungen in Echtzeit

### 🌐 Web-Dashboard (NEU in v0.8)

- **Modernes Web-Interface**
  - Echtzeit-Übersicht über alle Geräte und Sensoren
  - Interaktive Analytics-Dashboards mit Trend-Charts
  - Responsive Design für Desktop, Tablet und Mobile
  - Dunkles Theme für bessere Lesbarkeit

- **Selbstlernendes Badezimmer-System**
  - Automatische Dusch-Erkennung
  - Intelligente Luftentfeuchter-Steuerung
  - Analytics & Statistiken (Events, Dauer, Luftfeuchtigkeit)
  - Vorhersage der nächsten Duschzeit
  - Automatische Schwellwert-Optimierung (täglich um 3:00 Uhr)
  - Trendanalyse und Muster-Erkennung

- **Hintergrund-Datensammlung**
  - Automatisches Sammeln von Sensor-Daten alle 5 Minuten
  - Langzeit-Analytics für Temperatur und Luftfeuchtigkeit
  - Persistente Speicherung in SQLite-Datenbank

### 🏠 Multi-Platform Support

- **Home Assistant**: Volle Integration mit Home Assistant
- **Homey Pro**: Native Unterstützung für Homey Pro
- Einfacher Wechsel zwischen Plattformen
- Einheitliche API für beide Systeme

### 🔌 Externe Datenquellen (optional)

- Wettervorhersage (OpenWeatherMap) - empfohlen
- Dynamische Strompreise (aWATTar, Tibber) - optional, standardmäßig deaktiviert
- Anwesenheitserkennung

## Systemanforderungen

- **Betriebssystem**: Linux (getestet auf Ubuntu 22.04, Debian 11, Raspberry Pi OS)
- **Python**: 3.8 oder höher
- **Smart Home Platform** (eine davon):
  - **Home Assistant**: Version 2023.1 oder höher, ODER
  - **Homey Pro**: 2023 oder neuer (auch ältere Homey-Versionen unterstützt)
- **Speicher**: Mindestens 2GB RAM
- **Speicherplatz**: 500MB für System + Logs

## Installation

### 1. Repository klonen

```bash
git clone https://github.com/dein-username/KI-SYSTEM.git
cd KI-SYSTEM
```

### 2. Python Virtual Environment erstellen

```bash
python3 -m venv venv
source venv/bin/activate  # Auf Linux/Mac
```

### 3. Dependencies installieren

```bash
pip install -r requirements.txt
```

### 4. Konfiguration einrichten

```bash
# .env Datei erstellen
cp .env.example .env

# Bearbeite .env mit deinen Zugangsdaten
nano .env
```

#### Option A: Home Assistant

Trage folgende Daten ein:
- `PLATFORM_TYPE=homeassistant`
- `HA_URL`: URL deiner Home Assistant Instanz (z.B. `http://192.168.1.100:8123`)
- `HA_TOKEN`: Long-lived Access Token von Home Assistant

**Home Assistant Token erstellen:**

1. Öffne Home Assistant
2. Gehe zu deinem Profil (unten links)
3. Scrolle zu "Long-lived access tokens"
4. Klicke "Create Token"
5. Kopiere den Token und trage ihn in `.env` ein

#### Option B: Homey Pro

Trage folgende Daten ein:
- `PLATFORM_TYPE=homey`
- `HOMEY_URL=https://api.athom.com` (oder lokale IP)
- `HOMEY_TOKEN`: Bearer Token von Homey

**Homey Token erstellen:** Siehe [HOMEY_SETUP.md](HOMEY_SETUP.md) für Details

```bash
# Via Homey CLI
npm install -g athom-cli
athom login
athom user --bearer
```

### 5. Konfiguration anpassen

Bearbeite `config/config.yaml`:

```bash
nano config/config.yaml
```

Wichtige Einstellungen:
- `home_assistant.url`: Deine Home Assistant URL
- `data_collection.sensors`: Deine Sensor-Entity-IDs
- `models.energy_optimizer`: Komfort vs. Energiesparen

## 🔄 Updates & Daten-Persistenz

### Updates installieren

```bash
# Hole neueste Version vom Repository
git pull origin main

# Aktualisiere Dependencies (falls nötig)
pip install -r requirements.txt --upgrade
```

### ✅ Deine Daten bleiben erhalten!

**Alle wichtigen Dateien sind automatisch vor Updates geschützt** und werden nicht von Git überschrieben:

| Was bleibt erhalten | Speicherort |
|---------------------|-------------|
| 🗄️ **Datenbank** | `data/ki_system.db` |
| ⚙️ **Einstellungen** | `data/*.json` |
| 🧠 **Trainierte ML-Modelle** | `models/*.pkl` |
| 🔑 **Credentials** | `.env` |
| 📝 **Logs** | `logs/` |

**Kein manuelles Backup vor Updates nötig!** Siehe [PERSISTENCE.md](PERSISTENCE.md) für Details.

### Nach einem Update

```bash
# Web-App neu starten
python3 main.py web

# Logs prüfen
tail -f logs/ki_system.log

# Einstellungen überprüfen
open http://localhost:5000/settings
```

## Web-Dashboard

### Web-Interface starten

```bash
python main.py web --host 0.0.0.0 --port 8080
```

Das Web-Dashboard ist dann erreichbar unter:
- **Lokal**: http://localhost:8080
- **Im Netzwerk**: http://DEINE-IP:8080

### Dashboard-Features

**📊 Hauptseiten:**

- **Dashboard** (`/`) - Übersicht über Status, Vorhersagen, Wetter
- **Analytics** (`/analytics`) - Temperatur- und Luftfeuchtigkeit-Trends
- **Badezimmer** (`/bathroom`) - Intelligente Badezimmer-Automatisierung
- **Geräte** (`/devices`) - Alle verbundenen Geräte verwalten
- **Räume** (`/rooms`) - Raum-Management
- **Automatisierungen** (`/automations`) - Automatisierungs-Regeln
- **Einstellungen** (`/settings`) - System-Konfiguration

**🚿 Badezimmer-Automatisierung:**

1. **Konfiguration** (`/bathroom`):
   - Sensoren auswählen (Luftfeuchtigkeit, Temperatur)
   - Luftentfeuchter konfigurieren
   - Schwellwerte anpassen (High/Low Luftfeuchtigkeit)
   - System aktivieren/deaktivieren

2. **Analytics Dashboard** (`/bathroom/analytics`):
   - Echtzeit-Statistiken (Events, Durchschnittswerte)
   - Trend-Charts (letzte 10 Events)
   - Häufigste Duschzeiten
   - Wochentags-Verteilung
   - Vorhersage der nächsten Duschzeit
   - Event-Historie

3. **Automatische Optimierung**:
   - Läuft täglich um 3:00 Uhr
   - Optimiert Schwellwerte basierend auf historischen Daten
   - Benötigt mindestens 3 Events für Optimierung

### API-Endpunkte

Das Web-Interface bietet auch eine REST-API:

```bash
# Status abrufen
curl http://localhost:8080/api/status

# Geräte auflisten
curl http://localhost:8080/api/devices

# Badezimmer-Analytics
curl http://localhost:8080/api/bathroom/analytics?days=30

# Badezimmer-Events
curl http://localhost:8080/api/bathroom/events?days=7&limit=50
```

## Verwendung

### Verbindung testen

```bash
python main.py test
```

Dies prüft:
- Home Assistant Verbindung
- Wetter-API
- Energiepreis-API
- Datenbank

### Aktuellen Status anzeigen

```bash
python main.py status
```

Zeigt:
- Aktuelle Temperaturen
- Wetterbedingungen
- Strompreise
- Empfehlungen

### Einmaligen Zyklus ausführen

```bash
python main.py run
```

Führt einen Entscheidungs-Zyklus aus:
1. Sammelt Sensordaten
2. Trifft Entscheidungen
3. Führt Aktionen aus (wenn im Auto-Modus)

### Daemon-Modus (dauerhaft laufen lassen)

```bash
python main.py daemon --interval 300
```

Läuft dauerhaft und führt alle 300 Sekunden (5 Minuten) einen Zyklus aus.

### Als Systemd Service einrichten

Für automatischen Start beim Booten:

```bash
# Service-Datei erstellen
sudo nano /etc/systemd/system/ki-system.service
```

Inhalt:

```ini
[Unit]
Description=KI Smart Home System
After=network.target home-assistant.service

[Service]
Type=simple
User=dein-username
WorkingDirectory=/pfad/zum/KI-SYSTEM
ExecStart=/pfad/zum/KI-SYSTEM/venv/bin/python main.py daemon
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Service aktivieren:

```bash
sudo systemctl daemon-reload
sudo systemctl enable ki-system
sudo systemctl start ki-system

# Status prüfen
sudo systemctl status ki-system
```

## Konfiguration

### Modi

Das System hat 3 Modi:

- **`auto`**: Entscheidungen werden automatisch ausgeführt
- **`learning`**: System lernt, führt aber keine Aktionen aus
- **`manual`**: System macht Vorschläge, wartet aber auf Bestätigung

Einstellen in `config/config.yaml`:

```yaml
decision_engine:
  mode: "auto"  # oder "learning" oder "manual"
```

### Machine Learning Modelle

#### Beleuchtung

```yaml
models:
  lighting:
    type: "random_forest"  # oder "gradient_boosting"
    retrain_interval_hours: 24
    min_training_samples: 100
```

#### Heizung

```yaml
models:
  heating:
    type: "gradient_boosting"  # oder "random_forest"
    retrain_interval_hours: 24
    min_training_samples: 200
```

### Energieoptimierung

```yaml
models:
  energy_optimizer:
    target: "minimize_cost"  # oder "minimize_consumption", "balance"
    constraints:
      min_temperature: 18
      max_temperature: 23
      comfort_priority: 0.7  # 0 = max Einsparung, 1 = max Komfort
```

### Sicherheitsregeln

Definiere Regeln, die immer gelten:

```yaml
decision_engine:
  rules:
    - name: "no_heating_when_windows_open"
      condition: "window_sensor == open"
      action: "heating == off"

    - name: "presence_override"
      condition: "away_mode == true"
      action: "eco_mode == true"
```

## Training der ML-Modelle

Das System sammelt automatisch Daten. Nach einigen Tagen Training:

```bash
python main.py train
```

Minimale Datenmengen:
- Beleuchtung: 100+ Samples (ca. 2-3 Tage)
- Heizung: 200+ Samples (ca. 4-5 Tage)

Das System trainiert auch automatisch neu, wenn genug neue Daten vorhanden sind.

## Externe APIs

### OpenWeatherMap (Wetter)

1. Registriere dich auf [openweathermap.org](https://openweathermap.org/)
2. Erstelle einen API Key (kostenlos für 60 calls/min)
3. Trage Key in `.env` ein: `WEATHER_API_KEY=dein_key`

### aWATTar (Strompreise)

- Keine Registrierung nötig
- Funktioniert automatisch für Deutschland und Österreich

### Tibber (Strompreise)

1. Tibber-Kunde werden
2. API Token holen: [developer.tibber.com](https://developer.tibber.com/)
3. In `.env` eintragen: `ENERGY_API_KEY=dein_token`

## Projektstruktur

```
KI-SYSTEM/
├── config/
│   └── config.yaml           # Hauptkonfiguration
├── src/
│   ├── data_collector/       # Datensammler
│   │   ├── ha_collector.py   # Home Assistant
│   │   ├── homey_collector.py # Homey Pro
│   │   ├── weather_collector.py
│   │   └── energy_price_collector.py
│   ├── models/               # ML-Modelle
│   │   ├── lighting_model.py
│   │   ├── temperature_model.py
│   │   └── energy_optimizer.py
│   ├── decision_engine/      # Entscheidungs-Engine
│   │   ├── engine.py
│   │   ├── bathroom_automation.py    # Badezimmer-Logik
│   │   └── bathroom_analyzer.py      # Analytics & Muster-Erkennung
│   ├── background/           # Hintergrund-Prozesse
│   │   ├── data_collector.py         # Auto. Datensammlung
│   │   └── bathroom_optimizer.py     # Tägliche Optimierung
│   ├── web/                  # Web-Interface (NEU in v0.8)
│   │   ├── app.py            # Flask Web-App
│   │   ├── templates/        # HTML Templates
│   │   │   ├── base.html
│   │   │   ├── dashboard.html
│   │   │   ├── bathroom.html
│   │   │   ├── bathroom_analytics.html
│   │   │   ├── analytics.html
│   │   │   └── ...
│   │   └── static/           # CSS/JS/Assets
│   │       ├── css/
│   │       │   └── style.css
│   │       └── js/
│   │           ├── main.js
│   │           ├── bathroom.js
│   │           ├── bathroom_analytics.js
│   │           └── ...
│   └── utils/                # Utilities
│       ├── config_loader.py
│       └── database.py       # SQLite mit Analytics-Support
├── data/
│   ├── ki_system.db          # SQLite Datenbank (erweitert)
│   ├── bathroom_config.json  # Badezimmer-Konfiguration
│   └── sensor_config.json    # Sensor-Whitelist
├── models/                   # Trainierte ML-Modelle
├── logs/                     # Log-Dateien
├── main.py                   # Hauptprogramm
├── requirements.txt          # Python Dependencies
└── README.md                 # Diese Datei
```

## Troubleshooting

### Home Assistant Verbindung fehlgeschlagen

```bash
# Prüfe Erreichbarkeit
curl -H "Authorization: Bearer DEIN_TOKEN" http://IP:8123/api/

# Prüfe Token in .env
cat .env | grep HA_TOKEN
```

### Keine Sensor-Daten

```bash
# Prüfe Entity-IDs in Home Assistant
# Öffne Home Assistant → Developer Tools → States
# Kopiere exakte Entity-IDs in config.yaml
```

### ML-Modell trainiert nicht

- Prüfe ob genug Daten vorhanden: `python main.py status`
- System muss mindestens 2-3 Tage Daten sammeln
- Prüfe Logs: `tail -f logs/ki_system.log`

### Hoher CPU/RAM Verbrauch

- Reduziere `data_collection.interval_seconds` in config.yaml
- Nutze `model_type: "random_forest"` statt "gradient_boosting"
- Aktiviere nicht tensorflow wenn nicht nötig

## FAQ

### Allgemein

**Q: Wie lange dauert es, bis das System lernt?**
A: Nach 2-3 Tagen hat das System genug Daten für erste Entscheidungen. Optimale Ergebnisse nach 1-2 Wochen.

**Q: Ist das System sicher?**
A: Ja, es gibt mehrere Safety-Checks:
- Temperatur-Grenzen (16-25°C)
- Keine extremen Änderungen
- Sicherheitsregeln (z.B. kein Heizen bei offenen Fenstern)

**Q: Kann ich das System auf Raspberry Pi laufen lassen?**
A: Ja! Raspberry Pi 3B+ oder höher empfohlen. Funktioniert auch auf Pi Zero 2W.

**Q: Werden meine Daten in die Cloud gesendet?**
A: Nein! Alle Daten bleiben lokal. Nur externe APIs (Wetter, Preise) werden abgerufen.

**Q: Kann ich eigene Regeln hinzufügen?**
A: Ja, in `config/config.yaml` unter `decision_engine.rules`

**Q: Funktioniert es ohne Home Assistant?**
A: Ja! Das System unterstützt auch Homey Pro. Du kannst zwischen beiden Plattformen wählen.

### Web-Dashboard

**Q: Wie greife ich auf das Web-Dashboard zu?**
A: Starte das Web-Interface mit `python main.py web --host 0.0.0.0 --port 8080` und öffne http://localhost:8080 im Browser.

**Q: Kann ich das Dashboard von meinem Smartphone aus nutzen?**
A: Ja! Das Dashboard ist responsive und funktioniert auf Desktop, Tablet und Smartphone.

**Q: Ist das Web-Dashboard passwortgeschützt?**
A: Aktuell noch nicht. Dies ist für zukünftige Versionen geplant. Nutze es nur in vertrauenswürdigen Netzwerken.

### Badezimmer-Automatisierung

**Q: Wann beginnt das System Daten zu sammeln?**
A: Sofort nach Aktivierung in `/bathroom`. Das System erkennt automatisch Duschen basierend auf Luftfeuchtigkeit-Anstiegen.

**Q: Warum zeigt Analytics "Fehler beim Laden der Daten"?**
A: Das System benötigt mindestens 1 Event (Dusch-Vorgang). Die Datensammlung startet automatisch nach der Konfiguration.

**Q: Wie oft optimiert das System die Schwellwerte?**
A: Täglich um 3:00 Uhr, sobald mindestens 3 Events erfasst wurden. Die Optimierung benötigt eine Konfidenz von mindestens 70%.

**Q: Kann ich die Optimierung manuell starten?**
A: Ja! Im Analytics-Dashboard (`/bathroom/analytics`) gibt es einen "Jetzt optimieren" Button.

**Q: Welche Sensoren werden benötigt?**
A: Mindestens:
- 1 Luftfeuchtigkeit-Sensor (für Dusch-Erkennung)
- 1 Temperatur-Sensor
- 1 Schaltbares Gerät (Luftentfeuchter)

Optional: Bewegungsmelder, Tür-Sensor für erweiterte Funktionen.

## Roadmap

### ✅ Implementiert (v0.8)

- [x] Home Assistant Support
- [x] Homey Pro Support
- [x] **Web-Dashboard für Visualisierung**
  - [x] Echtzeit-Status-Übersicht
  - [x] Interaktive Analytics-Charts
  - [x] Geräte-Verwaltung
  - [x] Raum-Management
  - [x] Automatisierungs-Konfiguration
- [x] **Selbstlernendes Badezimmer-System**
  - [x] Dusch-Erkennung
  - [x] Automatische Luftentfeuchter-Steuerung
  - [x] Analytics & Event-Tracking
  - [x] Vorhersage-System
  - [x] Automatische Optimierung
- [x] **Hintergrund-Datensammlung**
  - [x] Automatisches Sensor-Logging
  - [x] Langzeit-Analytics
  - [x] SQLite-Datenbank

### 🚀 Geplant

- [ ] Smartphone-App (iOS/Android)
- [ ] MQTT-Support für direkte Geräte-Steuerung
- [ ] Mehr ML-Modelle
  - [ ] Jalousien-Steuerung
  - [ ] Lüftungs-Optimierung
  - [ ] Waschmaschinen-Zeitplanung
- [ ] Voice-Control Integration (Alexa, Google Home)
- [ ] Multi-Home Support (mehrere Standorte)
- [ ] Zusätzliche Plattformen
  - [ ] OpenHAB Support
  - [ ] ioBroker Support
  - [ ] Node-RED Integration
- [ ] Erweiterte Features
  - [ ] Energieverbrauchs-Prognosen
  - [ ] Kostenoptimierung mit dynamischen Tarifen
  - [ ] Push-Benachrichtigungen
  - [ ] Backup & Restore-Funktion

## Beitragen

Contributions sind willkommen! Bitte:
1. Fork das Repository
2. Erstelle einen Feature-Branch (`git checkout -b feature/AmazingFeature`)
3. Commit deine Änderungen (`git commit -m 'Add AmazingFeature'`)
4. Push zum Branch (`git push origin feature/AmazingFeature`)
5. Öffne einen Pull Request

## Lizenz

MIT License - siehe [LICENSE](LICENSE) Datei

## Support

- GitHub Issues: [Issues](https://github.com/dein-username/KI-SYSTEM/issues)
- Dokumentation: [Wiki](https://github.com/dein-username/KI-SYSTEM/wiki)

## Credits

Erstellt mit:
- [Home Assistant](https://www.home-assistant.io/)
- [scikit-learn](https://scikit-learn.org/)
- [OpenWeatherMap](https://openweathermap.org/)

---

**Hinweis**: Dies ist ein experimentelles Projekt. Nutze es auf eigene Verantwortung und prüfe alle Automatisierungen gründlich, bevor du sie in Produktion einsetzt.

---

## 🤝 Contributing

Beiträge sind willkommen! Siehe [CONTRIBUTING.md](CONTRIBUTING.md) für Details.

- 🐛 [Bug melden](.github/ISSUE_TEMPLATE/bug_report.yml)
- 💡 [Feature vorschlagen](.github/ISSUE_TEMPLATE/feature_request.yml)
- ❓ [Frage stellen](.github/ISSUE_TEMPLATE/question.yml)

## 📄 Lizenz

Dieses Projekt ist lizenziert unter der MIT License - siehe [LICENSE](LICENSE) für Details.

## 🙏 Acknowledgments

- [Home Assistant](https://www.home-assistant.io/) - Open Source Smart Home Platform
- [Homey](https://homey.app/) - Homey Pro Integration
- [scikit-learn](https://scikit-learn.org/) - Machine Learning Library
- Alle [Contributors](../../graphs/contributors) die geholfen haben!

## 📬 Kontakt & Support

- 📫 GitHub Issues für Bugs und Features
- 💬 GitHub Discussions für Fragen (falls aktiviert)
- ⭐ Gib dem Projekt einen Star wenn es dir gefällt!

---

<p align="center">
  Made with ❤️ für die Smart Home Community
</p>
