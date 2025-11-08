#!/bin/bash
# Setup-Script für KI-System v0.8
# Erweitert mit: Dependency-Check, Port-Check, Interaktive Config, PM2 Auto-Start

set -e

echo "╔═══════════════════════════════════════════╗"
echo "║   KI Smart Home System v0.8 - Setup      ║"
echo "╚═══════════════════════════════════════════╝"
echo ""

# ===== SYSTEM REQUIREMENTS CHECK =====
echo "🔍 Prüfe System-Voraussetzungen..."
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 nicht gefunden!"
    echo "Bitte installiere Python 3.8 oder höher: https://www.python.org/downloads/"
    exit 1
fi

python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python Version: $python_version"

required_version="3.8"
if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python 3.8 oder höher erforderlich!"
    exit 1
fi

# Check Git
if ! command -v git &> /dev/null; then
    echo "❌ Git nicht gefunden!"
    echo "Bitte installiere Git: https://git-scm.com/downloads"
    exit 1
fi
echo "✓ Git Version: $(git --version | awk '{print $3}')"

# Check pip
if ! python3 -m pip --version &> /dev/null; then
    echo "❌ pip nicht gefunden!"
    echo "Bitte installiere pip: python3 -m ensurepip --upgrade"
    exit 1
fi
echo "✓ pip installiert"

# Check lsof (für Port-Check)
if ! command -v lsof &> /dev/null; then
    echo "⚠️  lsof nicht gefunden - Port-Check wird übersprungen"
    HAS_LSOF=false
else
    echo "✓ lsof verfügbar"
    HAS_LSOF=true
fi

# Optional: curl
if command -v curl &> /dev/null; then
    echo "✓ curl verfügbar"
else
    echo "ℹ️  curl nicht gefunden (optional)"
fi

echo ""
echo "✓ Alle erforderlichen System-Voraussetzungen erfüllt!"
echo ""

# ===== PORT CHECK =====
if [ "$HAS_LSOF" = true ]; then
    echo "🔍 Prüfe Port 8080..."

    if lsof -i :8080 &> /dev/null; then
        echo "⚠️  Port 8080 ist bereits belegt!"
        echo ""
        echo "Laufende Prozesse auf Port 8080:"
        lsof -i :8080 | grep LISTEN || true
        echo ""

        read -p "Möchtest du die Prozesse auf Port 8080 beenden? (j/n) [Standard: n]: " kill_port
        kill_port=${kill_port:-n}

        if [[ "$kill_port" =~ ^[Jj]$ ]]; then
            echo "Stoppe Prozesse auf Port 8080..."
            lsof -ti :8080 | xargs kill -9 2>/dev/null || true
            sleep 2

            if lsof -i :8080 &> /dev/null; then
                echo "⚠️  Port konnte nicht freigegeben werden"
            else
                echo "✓ Port 8080 ist jetzt frei"
            fi
        fi
    else
        echo "✓ Port 8080 ist frei"
    fi
    echo ""
fi

# ===== VIRTUAL ENVIRONMENT =====
if [ ! -d "venv" ]; then
    echo ""
    echo "📦 Erstelle Virtual Environment..."
    python3 -m venv venv
    echo "✓ Virtual Environment erstellt"
else
    echo "✓ Virtual Environment existiert bereits"
fi

# Aktiviere Virtual Environment
echo ""
echo "🔧 Aktiviere Virtual Environment..."
source venv/bin/activate

# ===== DEPENDENCIES =====
echo ""
echo "📦 Installiere Python-Pakete..."
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo "✓ Dependencies installiert"

# ===== VERZEICHNISSE =====
echo ""
echo "📁 Erstelle Verzeichnisse..."
mkdir -p data models logs
echo "✓ Verzeichnisse erstellt"

# Mache main.py ausführbar
chmod +x main.py

# ===== INTERAKTIVE .ENV KONFIGURATION =====
if [ ! -f ".env" ]; then
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo "           Interaktive Konfiguration                          "
    echo "═══════════════════════════════════════════════════════════════"
    echo ""

    # Kopiere .env.example
    cp .env.example .env

    # Platform Type
    echo "🏠 Smart Home Platform auswählen:"
    echo "   1) Home Assistant"
    echo "   2) Homey Pro"
    echo ""
    read -p "Deine Auswahl (1/2) [Standard: 1]: " platform_choice
    platform_choice=${platform_choice:-1}

    if [ "$platform_choice" = "1" ]; then
        PLATFORM_TYPE="homeassistant"
        echo ""
        echo "📡 Home Assistant Konfiguration:"
        echo ""

        # Home Assistant URL
        read -p "Home Assistant URL [Standard: http://homeassistant.local:8123]: " ha_url
        ha_url=${ha_url:-http://homeassistant.local:8123}

        # Home Assistant Token
        echo ""
        echo "So erhältst du ein Long-Lived Access Token:"
        echo "  1. Öffne Home Assistant"
        echo "  2. Gehe zu deinem Profil (unten links)"
        echo "  3. Scrolle zu 'Long-Lived Access Tokens'"
        echo "  4. Klicke 'Create Token'"
        echo ""
        read -p "Home Assistant Token: " ha_token

        # In .env schreiben
        sed -i.bak "s|PLATFORM_TYPE=homeassistant|PLATFORM_TYPE=homeassistant|g" .env
        sed -i.bak "s|HA_URL=.*|HA_URL=$ha_url|g" .env
        sed -i.bak "s|HA_TOKEN=.*|HA_TOKEN=$ha_token|g" .env

    elif [ "$platform_choice" = "2" ]; then
        PLATFORM_TYPE="homey"
        echo ""
        echo "📡 Homey Pro Konfiguration:"
        echo ""

        # Homey URL
        read -p "Homey URL [Standard: https://api.athom.com]: " homey_url
        homey_url=${homey_url:-https://api.athom.com}

        # Homey Token
        echo ""
        echo "So erhältst du einen Homey Bearer Token:"
        echo "  1. Öffne https://developer.athom.com/tools/api"
        echo "  2. Logge dich ein"
        echo "  3. Wähle dein Homey aus"
        echo "  4. Kopiere den Bearer Token"
        echo ""
        read -p "Homey Bearer Token: " homey_token

        # In .env schreiben
        sed -i.bak "s|PLATFORM_TYPE=homeassistant|PLATFORM_TYPE=homey|g" .env
        sed -i.bak "s|HOMEY_URL=.*|HOMEY_URL=$homey_url|g" .env
        sed -i.bak "s|HOMEY_TOKEN=.*|HOMEY_TOKEN=$homey_token|g" .env
    fi

    # Optional: Weather API
    echo ""
    read -p "Möchtest du einen Weather API Key hinzufügen? (j/n) [Standard: n]: " add_weather
    add_weather=${add_weather:-n}

    if [[ "$add_weather" =~ ^[Jj]$ ]]; then
        echo ""
        echo "Weather API Services:"
        echo "  - OpenWeatherMap: https://openweathermap.org/api"
        echo "  - WeatherAPI: https://www.weatherapi.com/"
        echo ""
        read -p "Weather API Key: " weather_key
        sed -i.bak "s|WEATHER_API_KEY=.*|WEATHER_API_KEY=$weather_key|g" .env
    fi

    # Optional: Telegram Notifications
    echo ""
    read -p "Möchtest du Telegram-Benachrichtigungen einrichten? (j/n) [Standard: n]: " add_telegram
    add_telegram=${add_telegram:-n}

    if [[ "$add_telegram" =~ ^[Jj]$ ]]; then
        echo ""
        echo "Telegram Bot einrichten:"
        echo "  1. Öffne Telegram und suche @BotFather"
        echo "  2. Sende /newbot und folge den Anweisungen"
        echo "  3. Kopiere den Bot Token"
        echo ""
        read -p "Telegram Bot Token: " telegram_token

        echo ""
        echo "Chat ID finden:"
        echo "  1. Starte deinen Bot in Telegram"
        echo "  2. Sende eine Nachricht an den Bot"
        echo "  3. Öffne: https://api.telegram.org/bot<TOKEN>/getUpdates"
        echo "  4. Kopiere die 'chat id'"
        echo ""
        read -p "Telegram Chat ID: " telegram_chat

        sed -i.bak "s|TELEGRAM_BOT_TOKEN=.*|TELEGRAM_BOT_TOKEN=$telegram_token|g" .env
        sed -i.bak "s|TELEGRAM_CHAT_ID=.*|TELEGRAM_CHAT_ID=$telegram_chat|g" .env
    fi

    # Cleanup backup
    rm -f .env.bak

    echo ""
    echo "✓ .env Konfiguration abgeschlossen!"

else
    echo ""
    echo "✓ .env existiert bereits"

    # Frage ob neu konfigurieren
    read -p "Möchtest du die .env neu konfigurieren? (j/n) [Standard: n]: " reconfig
    reconfig=${reconfig:-n}

    if [[ "$reconfig" =~ ^[Jj]$ ]]; then
        mv .env .env.backup.$(date +%Y%m%d_%H%M%S)
        echo "Alte .env wurde gesichert"

        # Restart configuration process
        exec "$0"
    fi
fi

# ===== PM2 INSTALLATION =====
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "Möchtest du PM2 für Prozess-Management installieren? (empfohlen)"
echo "PM2 bietet: Auto-Restart, Log-Management, Monitoring"
echo "═══════════════════════════════════════════════════════════════"
read -p "PM2 installieren? (j/n) [Standard: j]: " install_pm2
install_pm2=${install_pm2:-j}

PM2_INSTALLED=false

if [[ "$install_pm2" =~ ^[Jj]$ ]]; then
    echo ""
    echo "📦 Installiere PM2..."

    # Prüfe ob Node.js/npm installiert ist
    if ! command -v npm &> /dev/null; then
        echo "⚠️  Node.js/npm nicht gefunden. Installiere Node.js..."

        # macOS
        if [[ "$OSTYPE" == "darwin"* ]]; then
            if command -v brew &> /dev/null; then
                echo "Installiere Node.js via Homebrew..."
                brew install node
            else
                echo "❌ Homebrew nicht gefunden."
                echo ""
                echo "Bitte installiere Node.js manuell:"
                echo "  1. Via Homebrew: brew install node"
                echo "  2. Oder Download: https://nodejs.org/"
                install_pm2="n"
            fi
        # Linux
        elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
            if command -v apt-get &> /dev/null; then
                echo "Installiere Node.js via apt..."
                sudo apt-get update
                sudo apt-get install -y nodejs npm
            elif command -v yum &> /dev/null; then
                echo "Installiere Node.js via yum..."
                sudo yum install -y nodejs npm
            else
                echo "❌ Paketmanager nicht gefunden."
                echo "Bitte installiere Node.js manuell: https://nodejs.org/"
                install_pm2="n"
            fi
        fi
    fi

    # Installiere PM2 wenn Node.js verfügbar
    if [[ "$install_pm2" =~ ^[Jj]$ ]] && command -v npm &> /dev/null; then
        npm install -g pm2
        echo "✓ PM2 installiert"
        PM2_INSTALLED=true

        # PM2 Startup konfigurieren
        echo ""
        read -p "PM2 beim System-Start automatisch starten? (j/n) [Standard: j]: " pm2_startup
        pm2_startup=${pm2_startup:-j}

        if [[ "$pm2_startup" =~ ^[Jj]$ ]]; then
            echo ""
            echo "Konfiguriere PM2 Autostart..."
            pm2 startup
            echo ""
            echo "⚠️  WICHTIG: Führe den oben angezeigten Befehl aus, um PM2 Autostart zu aktivieren"
        fi

        # PM2 direkt starten (NEU!)
        echo ""
        read -p "System jetzt mit PM2 starten? (j/n) [Standard: j]: " start_pm2
        start_pm2=${start_pm2:-j}

        if [[ "$start_pm2" =~ ^[Jj]$ ]]; then
            echo ""
            echo "🚀 Starte KI Smart Home System mit PM2..."

            # Stoppe eventuell laufende Instanzen
            pm2 delete ki-smart-home 2>/dev/null || true

            # Starte mit PM2
            pm2 start ecosystem.config.js
            pm2 save

            echo ""
            echo "✓ System gestartet!"
            echo ""
            echo "📊 PM2 Status:"
            pm2 list
        fi
    fi
fi

# ===== ABSCHLUSS =====
echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║            Setup erfolgreich abgeschlossen! ✓                ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

if [ "$PM2_INSTALLED" = true ] && [[ "$start_pm2" =~ ^[Jj]$ ]]; then
    echo "✨ Das System läuft bereits mit PM2!"
    echo ""
    echo "🌐 Web-Dashboard: http://localhost:8080"
    echo ""
    echo "📋 Nützliche PM2 Befehle:"
    echo "   pm2 list           # Status anzeigen"
    echo "   pm2 logs           # Logs anzeigen"
    echo "   pm2 monit          # Live-Monitoring"
    echo "   pm2 restart all    # Neustart"
    echo "   pm2 stop all       # Stoppen"
    echo ""
    echo "📚 Weitere Infos: PM2_GUIDE.md"
else
    echo "📋 Nächste Schritte:"
    echo ""

    if [ "$PM2_INSTALLED" = false ]; then
        echo "1️⃣  Teste die Verbindung:"
        echo "   source venv/bin/activate"
        echo "   python main.py test"
        echo ""
    fi

    echo "2️⃣  Starte das Web-Dashboard:"
    echo ""
    if command -v pm2 &> /dev/null; then
        echo "   Mit PM2 (empfohlen):"
        echo "   pm2 start ecosystem.config.js"
        echo "   pm2 save"
        echo ""
        echo "   Oder manuell:"
    fi
    echo "   source venv/bin/activate"
    echo "   python main.py web --host 0.0.0.0 --port 8080"
    echo ""
    echo "🌐 Zugriff: http://localhost:8080"
    echo ""
fi

echo "🚿 Features in v0.8:"
echo "   • Modernes Web-Dashboard"
echo "   • Selbstlernendes Badezimmer-System"
echo "   • Analytics & Trend-Charts"
echo "   • Automatische Optimierung (täglich 3:00 Uhr)"
echo "   • Web-basiertes System-Update"
echo ""
echo "📚 Dokumentation:"
echo "   • README.md - Hauptdokumentation"
echo "   • PM2_GUIDE.md - PM2 Prozess-Management"
echo ""
echo "🔗 GitHub: https://github.com/SHP-ART/KI-SYSTEM"
echo ""
echo "Viel Erfolg! 🚀"
