# Changelog

Alle wichtigen Änderungen am Projekt werden hier dokumentiert.

## [1.1.0] - 2025-11-07

### Hinzugefügt
- **Multi-Platform Support**: Homey Pro Integration
- `HomeyCollector`: Native Homey Pro API Integration
- `PlatformFactory`: Factory Pattern für Plattform-Auswahl
- `SmartHomeCollector`: Abstraktes Interface für alle Plattformen
- Neue Dokumentation: `HOMEY_SETUP.md`, `PLATFORMS.md`, `FEATURES.md`

### Geändert
- **Energiepreis-Integration ist jetzt optional** (standardmäßig deaktiviert)
- Config: `platform.type` zur Auswahl zwischen Home Assistant und Homey
- Decision Engine: Nutzt jetzt Platform Factory statt direkte HA-Integration
- `test_connection()`: Zeigt jetzt "smart_home_platform" statt "home_assistant"
- Requirements: Optionale Dependencies klar markiert

### Entfernt
- Keine Breaking Changes

### Migration von v1.0.0

1. Update `config.yaml`:
```yaml
# Alt:
home_assistant:
  url: "..."
  token: "..."

# Neu (optional):
platform:
  type: "homeassistant"  # oder "homey"
home_assistant:
  url: "..."
  token: "..."
```

2. Energiepreise sind jetzt standardmäßig deaktiviert:
```yaml
external_data:
  energy_prices:
    enabled: false  # Auf true setzen wenn gewünscht
```

3. Keine Code-Änderungen nötig - voll abwärtskompatibel!

---

## [1.0.0] - 2025-11-07

### Erste Release

#### Features
- Machine Learning Beleuchtungssteuerung
- ML-basierte Temperaturregelung
- Home Assistant Integration
- Wetter-Integration (OpenWeatherMap)
- Energiepreis-Integration (aWATTar, Tibber)
- SQLite Datenbank für Historie
- Entscheidungs-Engine mit Safety-Checks
- CLI mit test, run, daemon, status, train Modi
- Systemd Service Support
- Logging mit loguru

#### Modelle
- Random Forest für Beleuchtung
- Gradient Boosting für Temperatur
- Energy Optimizer

#### Dokumentation
- README.md
- QUICK_START.md
- Setup-Script

---

## Versionsschema

Wir folgen [Semantic Versioning](https://semver.org/):
- MAJOR: Breaking Changes
- MINOR: Neue Features (abwärtskompatibel)
- PATCH: Bug Fixes
