# Testing Guide - So testest du das KI-System

Schritt-für-Schritt Anleitung zum Testen aller Funktionen.

## Voraussetzungen

Bevor du startest:

```bash
# 1. Zum Projekt-Verzeichnis wechseln
cd /Users/shp-art/Documents/Github/KI-SYSTEM

# 2. Virtual Environment erstellen (falls noch nicht vorhanden)
python3 -m venv venv

# 3. Aktivieren
source venv/bin/activate

# 4. Dependencies installieren
pip install -r requirements.txt
```

Erwartete Ausgabe:
```
Successfully installed loguru-0.7.2 numpy-1.26.2 pandas-2.1.4 ...
```

---

## Test 1: Basis-Imports testen ✅

Prüfe ob alle Python-Module korrekt installiert sind:

```bash
python3 << 'EOF'
print("=== Testing Imports ===\n")

try:
    import loguru
    print("✓ loguru")
except ImportError as e:
    print(f"✗ loguru: {e}")

try:
    import numpy
    print("✓ numpy")
except ImportError as e:
    print(f"✗ numpy: {e}")

try:
    import pandas
    print("✓ pandas")
except ImportError as e:
    print(f"✗ pandas: {e}")

try:
    import sklearn
    print("✓ scikit-learn")
except ImportError as e:
    print(f"✗ sklearn: {e}")

try:
    import sqlite3
    print("✓ sqlite3 (built-in)")
except ImportError as e:
    print(f"✗ sqlite3: {e}")

try:
    from src.utils.database import Database
    print("✓ src.utils.database")
except ImportError as e:
    print(f"✗ src.utils.database: {e}")

try:
    from src.data_collector.platform_factory import PlatformFactory
    print("✓ src.data_collector.platform_factory")
except ImportError as e:
    print(f"✗ platform_factory: {e}")

print("\n=== All imports successful! ===")
EOF
```

**Erwartete Ausgabe:**
```
=== Testing Imports ===

✓ loguru
✓ numpy
✓ pandas
✓ scikit-learn
✓ sqlite3 (built-in)
✓ src.utils.database
✓ src.data_collector.platform_factory

=== All imports successful! ===
```

---

## Test 2: Datenbank testen 🗄️

```bash
python3 test_database.py
```

**Erwartete Ausgabe:**
```
=== Database Test ===

1. Creating database...
   ✓ Database created

2. Inserting sensor data...
   ✓ Sensor data inserted

3. Inserting external data...
   ✓ External data inserted

4. Inserting decision...
   ✓ Decision inserted (ID: 1)

5. Updating decision result...
   ✓ Decision updated

6. Retrieving sensor data...
   ✓ Found 1 sensor records

7. Retrieving training data...
   ✓ Found 1 sensor types

8. Inserting training history...
   ✓ Training history inserted

9. Closing database connection...
   ✓ Connection closed

=== All tests passed! ✓ ===
```

**Falls Fehler:** Siehe "Troubleshooting" weiter unten

---

## Test 3: Konfiguration prüfen ⚙️

### A) Ohne Smart Home Platform (Minimal-Test)

Erstelle eine Test-Config:

```bash
cat > config/test_config.yaml << 'EOF'
platform:
  type: "homeassistant"

home_assistant:
  url: "http://localhost:8123"
  token: "test_token_123"

data_collection:
  interval_seconds: 300

external_data:
  weather:
    enabled: false
  energy_prices:
    enabled: false

models:
  lighting:
    type: "random_forest"
  heating:
    type: "gradient_boosting"

decision_engine:
  mode: "learning"
  confidence_threshold: 0.7

database:
  type: "sqlite"
  path: "data/test_ki_system.db"

logging:
  level: "INFO"
  path: "logs/test.log"
EOF
```

Test Config laden:

```bash
python3 << 'EOF'
from src.utils.config_loader import ConfigLoader

print("=== Testing Config Loader ===\n")

config = ConfigLoader("config/test_config.yaml")

print(f"Platform: {config.get('platform.type')}")
print(f"HA URL: {config.get('home_assistant.url')}")
print(f"Mode: {config.get('decision_engine.mode')}")
print(f"DB Path: {config.get('database.path')}")

print("\n✓ Config loaded successfully!")
EOF
```

---

## Test 4: Platform Factory testen 🏭

```bash
python3 << 'EOF'
from src.data_collector.platform_factory import PlatformFactory

print("=== Testing Platform Factory ===\n")

# Test 1: Verfügbare Plattformen
platforms = PlatformFactory.get_platform_names()
print(f"Available platforms: {', '.join(platforms)}")

# Test 2: Ungültige Plattform
collector = PlatformFactory.create_collector("invalid", "http://test", "token")
if collector is None:
    print("✓ Correctly returns None for invalid platform")
else:
    print("✗ Should return None for invalid platform")

# Test 3: Fehlende URL/Token
collector = PlatformFactory.create_collector("homeassistant", None, None)
if collector is None:
    print("✓ Correctly validates URL and token")
else:
    print("✗ Should validate URL and token")

print("\n=== Platform Factory tests passed! ===")
EOF
```

---

## Test 5: Mit echtem Home Assistant/Homey 🏠

### Voraussetzungen:
- ✅ Home Assistant oder Homey läuft
- ✅ Token erstellt
- ✅ `.env` konfiguriert

### A) .env erstellen

```bash
# Kopiere Beispiel
cp .env.example .env

# Bearbeite mit deinen echten Daten
nano .env
```

Trage ein:
```bash
PLATFORM_TYPE=homeassistant
HA_URL=http://192.168.1.100:8123  # Deine IP!
HA_TOKEN=eyJ0eXAiOi...  # Dein echter Token!
```

### B) Verbindung testen

```bash
python3 main.py test
```

**Erwartete Ausgabe bei Erfolg:**
```
=== Connection Test Results ===
✓ smart_home_platform: OK
✓ weather_api: OK
✓ energy_prices: disabled
✓ database: OK

Overall: ✓ All systems operational
```

**Bei Fehler:**
```
✗ smart_home_platform: FAILED
```
→ Siehe "Troubleshooting Verbindung" unten

### C) Status abrufen

```bash
python3 main.py status
```

**Erwartete Ausgabe:**
```
=== Current System Status ===
Timestamp: 2025-11-07T20:30:00

Temperature:
  Indoor: 21.5°C
  Outdoor: 12.3°C
  Humidity: 65%

Environment:
  Brightness: 150 lux
  Motion: None
  Weather: Clouds

=== Recommendations ===
  🌡️ Außentemperatur ist 12.3°C. Heizung kann reduziert werden.
```

---

## Test 6: Einmaligen Zyklus ausführen 🔄

**WICHTIG:** Stelle sicher, dass `mode: "learning"` in config.yaml ist!

```bash
python3 main.py run
```

**Erwartete Ausgabe:**
```
=== Cycle Results ===
Timestamp: 2025-11-07T20:30:00
Lighting actions: 0
Heating actions: 0
Total actions: 0
```

Im Learning-Modus führt das System **keine Aktionen** aus, sondern sammelt nur Daten!

---

## Test 7: ML-Modelle testen (mit Dummy-Daten) 🤖

```bash
python3 << 'EOF'
import pandas as pd
from datetime import datetime, timedelta
from src.models.lighting_model import LightingModel

print("=== Testing Lighting Model ===\n")

# Erstelle Dummy-Daten
sensor_data = []
light_states = []

for i in range(100):
    time = datetime.now() - timedelta(hours=100-i)

    sensor_data.append({
        'timestamp': time,
        'brightness': 200 if time.hour < 12 else 50,
        'motion_detected': 1 if i % 3 == 0 else 0,
        'presence_home': 1,
        'weather_condition': 'clear'
    })

    light_states.append({
        'timestamp': time,
        'light_state': 1 if time.hour >= 18 or time.hour < 7 else 0
    })

# Trainiere Modell
model = LightingModel()
X, y = model.prepare_training_data(sensor_data, light_states)

print(f"Training data: {len(X)} samples")

if len(X) >= 50:
    metrics = model.train(X, y)
    print(f"✓ Model trained with {metrics['accuracy']:.2%} accuracy")

    # Test Vorhersage
    test_condition = {
        'timestamp': datetime.now().replace(hour=20),
        'brightness': 30,
        'motion_detected': 1,
        'presence_home': 1,
        'weather_condition': 'clear'
    }

    prediction, confidence = model.predict(test_condition)
    print(f"✓ Prediction: {'ON' if prediction == 1 else 'OFF'} (confidence: {confidence:.2%})")

    # Speichern
    model.save("models/test_lighting_model.pkl")
    print("✓ Model saved")

    # Laden
    model2 = LightingModel()
    model2.load("models/test_lighting_model.pkl")
    print("✓ Model loaded")
else:
    print("✗ Not enough data for training")

print("\n=== Lighting Model test passed! ===")
EOF
```

---

## Test 8: Debug Mode in VS Code 🐛

Falls du VS Code nutzt:

1. **Öffne VS Code** im Projekt-Verzeichnis:
   ```bash
   code .
   ```

2. **Wähle Python Interpreter:**
   - `Cmd+Shift+P` → "Python: Select Interpreter"
   - Wähle `./venv/bin/python`

3. **Gehe zum Debug Panel:**
   - Klicke auf Debug Icon (links)
   - Oder drücke `Cmd+Shift+D`

4. **Wähle Test Configuration:**
   - Dropdown oben: "KI-System: Test"
   - Drücke grünen Play-Button (oder F5)

5. **Breakpoints setzen:**
   - Klicke links neben Zeilennummern
   - Debugger stoppt dort

---

## Troubleshooting 🔧

### Problem: "ModuleNotFoundError: No module named 'loguru'"

```bash
# Prüfe ob venv aktiv
which python3
# Sollte zeigen: .../venv/bin/python

# Falls nicht:
source venv/bin/activate

# Dependencies neu installieren
pip install -r requirements.txt
```

### Problem: "Connection refused" zu Home Assistant

```bash
# Test 1: Ist HA erreichbar?
curl http://192.168.1.100:8123
# Sollte HTML zurückgeben

# Test 2: API erreichbar?
curl -H "Authorization: Bearer DEIN_TOKEN" http://192.168.1.100:8123/api/
# Sollte: {"message": "API running."}

# Test 3: Token gültig?
# In Home Assistant prüfen: Profil → Long-lived access tokens
```

### Problem: "Permission denied" auf Datenbank

```bash
# Rechte prüfen
ls -la data/

# Falls nötig:
chmod 755 data/
chmod 644 data/*.db
```

### Problem: Type-Checking Errors in VS Code

```bash
# Reload VS Code Window
# Cmd+Shift+P → "Developer: Reload Window"

# Oder Type Checking deaktivieren:
# .vscode/settings.json
# "python.analysis.typeCheckingMode": "off"
```

---

## Performance Tests 📊

### Test: Wie lange dauert ein Zyklus?

```bash
time python3 main.py run
```

**Erwartete Zeit:**
- Ohne ML-Modelle: 1-3 Sekunden
- Mit ML-Modellen: 3-5 Sekunden
- Mit externen APIs: 5-10 Sekunden

### Test: Speicherverbrauch

```bash
# Installation von memory_profiler
pip install memory_profiler

# Profiling
python3 -m memory_profiler main.py test
```

---

## Automatisierte Tests (Zukunft) 🧪

Für später kannst du pytest nutzen:

```bash
# Installation
pip install pytest

# Test-Struktur erstellen
mkdir tests
touch tests/__init__.py
touch tests/test_database.py
touch tests/test_models.py
touch tests/test_collectors.py

# Tests ausführen
pytest tests/
```

---

## Zusammenfassung - Schnelltest Checklist ✅

```bash
# 1. Setup
cd KI-SYSTEM
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Basis-Tests
python3 -c "import loguru; print('✓ Imports OK')"
python3 test_database.py

# 3. Config erstellen
cp .env.example .env
nano .env  # Deine Daten eintragen

# 4. System testen
python3 main.py test
python3 main.py status

# 5. Learning Mode (sammelt nur Daten)
python3 main.py run

# 6. Logs prüfen
tail -f logs/ki_system.log
```

**Wenn alle Tests grün sind (✓), funktioniert alles!** 🎉

---

## Hilfe bekommen

Bei Problemen:
1. Prüfe `logs/ki_system.log`
2. Prüfe diese Test-Anleitung
3. Siehe `TROUBLESHOOTING.md`
4. Erstelle Issue auf GitHub mit:
   - Output von `python3 main.py test`
   - Relevante Logs
   - Dein Setup (OS, Python Version)
