# Features und Module

Übersicht über alle Features des KI-Systems und welche davon optional sind.

## Kern-Features (immer aktiv)

### ✅ Machine Learning Steuerung
- **Beleuchtung**: Lernt wann Licht an/aus sein sollte
- **Temperatur**: Optimiert Heizungssteuerung
- **Verhaltensanalyse**: Lernt aus deinen Gewohnheiten

### ✅ Smart Home Integration
- **Home Assistant**: Volle Integration
- **Homey Pro**: Native Unterstützung
- Geräte-Steuerung (Lights, Climate, Sensors)

### ✅ Datensammlung & Historie
- SQLite Datenbank
- Sensor-Daten speichern
- Training-Historie
- Entscheidungs-Logs

### ✅ Automatisierung
- Regelbasierte Entscheidungen
- ML-basierte Vorhersagen
- Sicherheits-Checks
- Learning/Auto/Manual Modus

---

## Optionale Features

### ⚙️ Wetter-Integration

**Status:** Optional (standardmäßig aktiviert)

**Was es macht:**
- Wettervorhersage abrufen
- Außentemperatur für Heizoptimierung
- Wetter-basierte Entscheidungen

**Aktivieren:**
```yaml
# config/config.yaml
external_data:
  weather:
    enabled: true  # oder false zum deaktivieren
    location: "Berlin, DE"
    api_key: "YOUR_API_KEY"  # Optional
```

**Ohne Wetter:**
- System nutzt geschätzte Außentemperatur
- Keine wetterabhängigen Optimierungen

---

### ⚙️ Energiepreis-Integration (aWATTar, Tibber)

**Status:** Optional (standardmäßig DEAKTIVIERT)

**Was es macht:**
- Dynamische Strompreise abrufen
- Optimiert Heizen bei günstigen Preisen
- Vorheizen wenn Strom günstig ist
- Reduziert Verbrauch bei teuren Preisen

**Aktivieren:**
```yaml
# config/config.yaml
external_data:
  energy_prices:
    enabled: true  # Auf true setzen
    provider: "awattar"  # oder "tibber"
    api_key: ""  # Optional für aWATTar, Pflicht für Tibber
```

**Anbieter:**
- **aWATTar**: Kostenlos, kein API Key nötig (Deutschland & Österreich)
- **Tibber**: Benötigt API Token (siehe Tibber Developer Portal)

**Ohne Energiepreise:**
- System nutzt Standard-Optimierung
- Keine preisbasierte Anpassung
- Fokus nur auf Komfort und Anwesenheit

---

### ⚙️ Erweiterte ML-Modelle

**Status:** Optional

**TensorFlow/Keras:**
- Für sehr große Datensätze
- Deep Learning Modelle
- Komplexe Muster-Erkennung

**Standardmäßig:**
- System nutzt scikit-learn (Random Forest, Gradient Boosting)
- Ausreichend für 99% der Anwendungsfälle
- Viel schneller und weniger Ressourcen

**TensorFlow installieren:**
```bash
pip install tensorflow==2.15.0
```

---

## Feature-Matrix

| Feature | Standard | Optional | Benötigt |
|---------|----------|----------|----------|
| ML Beleuchtung | ✅ | - | - |
| ML Temperatur | ✅ | - | - |
| Home Assistant | ✅ | - | Token |
| Homey Pro | ✅ | - | Token |
| Datenbank | ✅ | - | - |
| Wetter | ✅ (kann deaktiviert werden) | ⚙️ | API Key (optional) |
| Energiepreise | ❌ | ⚙️ | Config aktivieren |
| TensorFlow | ❌ | ⚙️ | Manuell installieren |
| Benachrichtigungen | Geplant | 🔄 | Telegram Bot |

---

## Minimalinstallation

Für minimale Installation ohne optionale Features:

### 1. Minimal requirements.txt

```txt
# Core nur
python-dotenv==1.0.0
pyyaml==6.0.1
requests==2.31.0
scikit-learn==1.3.2
numpy==1.26.2
pandas==2.1.4
joblib==1.3.2
sqlalchemy==2.0.23
schedule==1.2.0
loguru==0.7.2
```

### 2. Minimal config.yaml

```yaml
platform:
  type: "homeassistant"

home_assistant:
  url: "http://homeassistant.local:8123"
  token: "YOUR_TOKEN"

data_collection:
  interval_seconds: 300
  sensors:
    temperature:
      - sensor.your_temp_sensor
    light:
      - sensor.your_light_sensor

external_data:
  weather:
    enabled: false  # Deaktiviert
  energy_prices:
    enabled: false  # Deaktiviert

models:
  lighting:
    type: "random_forest"
  heating:
    type: "gradient_boosting"

decision_engine:
  mode: "auto"
```

Dies läuft mit:
- ✅ Nur Smart Home Integration
- ✅ ML-Modelle
- ✅ Basis-Optimierung
- ❌ Keine externen APIs
- ❌ Keine Energiepreis-Optimierung

---

## Empfohlene Konfiguration

Für beste Ergebnisse:

```yaml
external_data:
  weather:
    enabled: true  # ✅ Empfohlen für Heizoptimierung
  energy_prices:
    enabled: false  # ⚙️ Optional, nur wenn du willst
```

**Warum Wetter empfohlen ist:**
- Heizung kann Außentemperatur berücksichtigen
- Bessere Vorhersagen
- Kostenlos (auch ohne API Key über Home Assistant)

**Warum Energiepreise optional:**
- Nur sinnvoll mit dynamischem Tarif
- Nicht jeder hat aWATTar/Tibber
- System funktioniert auch ohne sehr gut

---

## Zukünftige Features

### 🔄 In Planung

- **Benachrichtigungen**: Telegram/Push-Benachrichtigungen
- **Web-Dashboard**: Visualisierung & Kontrolle
- **Szenen**: Automatische Szenen erstellen
- **Präsenz-Erkennung**: Erweiterte Anwesenheits-Logik
- **Multi-Home**: Mehrere Standorte verwalten

### 💡 Ideen

- Solaranlagen-Integration
- Batteriespeicher-Optimierung
- E-Auto Lade-Optimierung
- Jalousien/Rolladen-Steuerung
- Luftqualität-Monitoring

---

## Feature-Anfragen

Du hast eine Idee für ein neues Feature?

1. Erstelle ein Issue auf GitHub
2. Beschreibe den Use-Case
3. Community diskutiert

Oder implementiere es selbst und erstelle einen Pull Request!

---

## Performance-Hinweise

### Ressourcen-Verbrauch

**Minimal-Setup:**
- RAM: ~200MB
- CPU: Sehr wenig (nur bei Entscheidungen)
- Speicher: ~50MB

**Mit allen Features:**
- RAM: ~500MB
- CPU: Niedrig (externe API-Calls)
- Speicher: ~200MB (Datenbank wächst)

**Mit TensorFlow:**
- RAM: ~1GB+
- CPU: Mittel-Hoch
- Speicher: ~500MB

### Optimierungs-Tipps

1. **Interval erhöhen**: `interval_seconds: 600` statt 300
2. **TensorFlow weglassen**: scikit-learn ist ausreichend
3. **Cache nutzen**: Externe APIs cachen
4. **Alte Daten löschen**: `retention_days: 30` statt 90

---

## Zusammenfassung

**Du brauchst minimal:**
- Smart Home Platform (Home Assistant oder Homey)
- Python Dependencies (Kern)
- Config-Datei

**Alles andere ist optional!**

Das System ist modular aufgebaut. Du kannst Features nach Bedarf aktivieren oder deaktivieren, ohne den Code ändern zu müssen.
