# Contributing zu KI-System

Danke dass du zum Projekt beitragen möchtest! 🎉

## Code of Conduct

Dieses Projekt folgt einem Code of Conduct. Durch deine Teilnahme erklärst du dich damit einverstanden, respektvoll und konstruktiv zu sein.

## Wie kann ich beitragen?

### 🐛 Bug Reports

1. Prüfe ob der Bug schon gemeldet wurde (GitHub Issues)
2. Erstelle ein neues Issue mit dem "Bug Report" Template
3. Füge so viele Details wie möglich hinzu:
   - Schritte zur Reproduktion
   - Erwartetes vs. tatsächliches Verhalten
   - Logs (`logs/ki_system.log`)
   - System-Info (OS, Python Version)

### 💡 Feature Requests

1. Prüfe ob das Feature schon vorgeschlagen wurde
2. Erstelle ein Issue mit dem "Feature Request" Template
3. Beschreibe:
   - Welches Problem löst es?
   - Wie sollte es funktionieren?
   - Warum ist es nützlich?

### 📝 Dokumentation

Dokumentations-Verbesserungen sind immer willkommen:
- Typos beheben
- Beispiele hinzufügen
- Erklärungen verbessern
- Neue Guides schreiben

### 💻 Code Contributions

## Development Setup

### 1. Fork & Clone

```bash
# Fork das Repository auf GitHub

# Clone dein Fork
git clone https://github.com/DEIN-USERNAME/KI-SYSTEM.git
cd KI-SYSTEM

# Füge upstream hinzu
git remote add upstream https://github.com/ORIGINAL-OWNER/KI-SYSTEM.git
```

### 2. Environment Setup

```bash
# Virtual Environment
python3 -m venv venv
source venv/bin/activate

# Dependencies
pip install -r requirements.txt

# Development Dependencies (optional)
pip install black flake8 mypy pytest
```

### 3. Branch erstellen

```bash
# Update main
git checkout main
git pull upstream main

# Neuer Feature Branch
git checkout -b feature/dein-feature-name

# Oder Bug Fix Branch
git checkout -b fix/bug-beschreibung
```

## Coding Standards

### Code Style

- **Python**: PEP 8
- **Formatting**: Black (Line length: 100)
- **Imports**: Alphabetisch sortiert
- **Type Hints**: Wo sinnvoll

```python
# Gut
def process_data(sensor_id: str, value: float) -> Optional[Dict]:
    """Verarbeitet Sensordaten."""
    pass

# Nicht gut
def process_data(sensor_id,value):
    pass
```

### Formatting

```bash
# Auto-Format mit Black
black .

# Linting
flake8 .

# Type Checking (optional)
mypy src/
```

### Kommentare

- **Docstrings**: Für alle public Funktionen/Klassen
- **Inline Kommentare**: Nur wo Code nicht selbsterklärend ist
- **TODO Kommentare**: Mit Issue-Nummer

```python
def complex_calculation(data: List[float]) -> float:
    """
    Führt komplexe Berechnung durch.

    Args:
        data: Liste von Messwerten

    Returns:
        Berechnetes Ergebnis

    Raises:
        ValueError: Wenn data leer ist
    """
    # TODO(#123): Optimierung für große Datensätze
    pass
```

### Tests

Füge Tests für neue Features hinzu:

```python
# tests/test_dein_feature.py
def test_new_feature():
    """Testet das neue Feature."""
    result = your_function()
    assert result == expected
```

Führe Tests aus:
```bash
# Quick Test
./quick_test.sh

# Datenbank Test
python test_database.py

# Alle Tests
pytest tests/
```

## Pull Request Process

### 1. Vorbereitung

```bash
# Stelle sicher dein Branch ist aktuell
git checkout main
git pull upstream main
git checkout dein-branch
git rebase main

# Tests laufen
./quick_test.sh
```

### 2. Commit Messages

Gute Commit Messages:
- Erste Zeile: Kurze Zusammenfassung (max 50 Zeichen)
- Leerzeile
- Detaillierte Beschreibung (wenn nötig)

```bash
# Gut
git commit -m "Add Homey Pro zone support

- Implement get_zones() method
- Add zone filtering for devices
- Update documentation"

# Nicht gut
git commit -m "fix bug"
```

### 3. Push & PR

```bash
# Push zu deinem Fork
git push origin dein-branch

# Erstelle Pull Request auf GitHub
# - Gehe zu deinem Fork
# - Klicke "New Pull Request"
# - Fülle das PR Template aus
```

### 4. Review Process

- **CI Checks**: Müssen grün sein (GitHub Actions)
- **Code Review**: Mindestens 1 Approval
- **Änderungen**: Reagiere auf Feedback konstruktiv

```bash
# Nach Feedback Änderungen machen
git add .
git commit -m "Address review feedback"
git push origin dein-branch
```

### 5. Merge

Nach Approval wird dein PR gemerged! 🎉

## Projekt-Struktur

```
KI-SYSTEM/
├── src/
│   ├── data_collector/     # Smart Home Integrations
│   ├── models/             # ML Modelle
│   ├── decision_engine/    # Entscheidungslogik
│   └── utils/              # Hilfsfunktionen
├── config/                 # Konfigurationen
├── tests/                  # Tests
├── docs/                   # Dokumentation
└── .github/                # GitHub-spezifisch
```

### Neue Features hinzufügen

**Smart Home Platform:**
```python
# 1. Erstelle src/data_collector/neue_platform_collector.py
class NeuePlatformCollector(SmartHomeCollector):
    """Implementiert SmartHomeCollector Interface"""
    pass

# 2. Registriere in platform_factory.py
PLATFORMS = {
    'neue_platform': NeuePlatformCollector,
}
```

**ML Model:**
```python
# Erstelle src/models/neues_model.py
# Orientiere dich an lighting_model.py
```

## Branches

- **`main`**: Stabile Releases
- **`develop`**: Entwicklungs-Branch
- **`feature/*`**: Neue Features
- **`fix/*`**: Bug Fixes
- **`docs/*`**: Dokumentation

## Release Process

(Nur für Maintainer)

1. Update `CHANGELOG.md`
2. Update Version in `src/__init__.py`
3. Create Release Tag: `git tag v1.2.0`
4. Push Tag: `git push origin v1.2.0`
5. GitHub Release erstellen

## Fragen?

- **Issues**: Stelle Fragen als Issue (Template: "Frage / Hilfe")
- **Diskussionen**: GitHub Discussions (wenn aktiviert)
- **E-Mail**: (falls vorhanden)

## Lizenz

Durch deine Contribution stimmst du zu, dass dein Code unter der MIT Lizenz lizenziert wird.

---

**Danke für deine Hilfe! 🙏**

Jeder Beitrag zählt - ob Bug Report, Dokumentation oder Code!
