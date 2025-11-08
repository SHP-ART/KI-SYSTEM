#!/bin/bash
# Setup-Script für KI-System v0.8

set -e

echo "╔═══════════════════════════════════════════╗"
echo "║   KI Smart Home System v0.8 - Setup      ║"
echo "╚═══════════════════════════════════════════╝"
echo ""

# Prüfe Python-Version
echo "Prüfe Python-Version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python Version: $python_version"

required_version="3.8"
if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "FEHLER: Python 3.8 oder höher erforderlich!"
    exit 1
fi

# Virtual Environment erstellen
if [ ! -d "venv" ]; then
    echo ""
    echo "Erstelle Virtual Environment..."
    python3 -m venv venv
    echo "✓ Virtual Environment erstellt"
else
    echo "✓ Virtual Environment existiert bereits"
fi

# Aktiviere Virtual Environment
echo ""
echo "Aktiviere Virtual Environment..."
source venv/bin/activate

# Installiere Dependencies
echo ""
echo "Installiere Python-Pakete..."
pip install --upgrade pip
pip install -r requirements.txt
echo "✓ Dependencies installiert"

# Erstelle .env falls nicht vorhanden
if [ ! -f ".env" ]; then
    echo ""
    echo "Erstelle .env Datei..."
    cp .env.example .env
    echo "✓ .env erstellt - bitte mit deinen Daten ausfüllen!"
    echo ""
    echo "WICHTIG: Bearbeite .env und trage folgendes ein:"
    echo "  - PLATFORM_TYPE (homeassistant oder homey)"
    echo "  - HA_URL / HOMEY_URL (je nach Platform)"
    echo "  - HA_TOKEN / HOMEY_TOKEN (API-Token)"
    echo "  - Optional: WEATHER_API_KEY, ENERGY_API_KEY"
else
    echo "✓ .env existiert bereits"
fi

# Erstelle Verzeichnisse
echo ""
echo "Erstelle Verzeichnisse..."
mkdir -p data models logs
echo "✓ Verzeichnisse erstellt"

# Mache main.py ausführbar
chmod +x main.py

echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║            Setup erfolgreich abgeschlossen! ✓                ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "📋 Nächste Schritte:"
echo ""
echo "1️⃣  Bearbeite .env mit deinen Zugangsdaten:"
echo "   nano .env"
echo ""
echo "2️⃣  Passe config/config.yaml an deine Sensoren an:"
echo "   nano config/config.yaml"
echo ""
echo "3️⃣  Teste die Verbindung:"
echo "   source venv/bin/activate"
echo "   python main.py test"
echo ""
echo "4️⃣  Starte das Web-Dashboard (NEU in v0.8):"
echo "   python main.py web --host 0.0.0.0 --port 8080"
echo "   Zugriff: http://localhost:8080"
echo ""
echo "   ODER starte im Daemon-Modus:"
echo "   python main.py daemon"
echo ""
echo "🚿 Features in v0.8:"
echo "   • Modernes Web-Dashboard"
echo "   • Selbstlernendes Badezimmer-System"
echo "   • Analytics & Trend-Charts"
echo "   • Automatische Optimierung (täglich 3:00 Uhr)"
echo ""
echo "📚 Dokumentation: README.md"
echo "🐛 Issues: https://github.com/dein-username/KI-SYSTEM/issues"
echo ""
echo "Viel Erfolg! 🚀"
