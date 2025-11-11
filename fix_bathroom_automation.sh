#!/bin/bash
# Quick-Fix: Aktiviert die Badezimmer-Automation
# Setzt 'enabled: true' in beiden Config-Dateien und startet Web-App neu

set -e

echo "=========================================="
echo "BADEZIMMER-AUTOMATION QUICK-FIX"
echo "=========================================="
echo ""

# 1. Prüfe aktuelle Config
echo "📋 Schritt 1: Prüfe aktuelle Konfiguration..."
echo ""

if [ -f "data/bathroom_config.json" ]; then
    BATHROOM_ENABLED=$(grep -oP '"enabled":\s*\K(true|false)' data/bathroom_config.json || echo "unknown")
    echo "   bathroom_config.json: enabled=$BATHROOM_ENABLED"
else
    echo "   ❌ bathroom_config.json nicht gefunden!"
fi

if [ -f "data/luftentfeuchten_config.json" ]; then
    LUFTENTFEUCHTEN_ENABLED=$(grep -oP '"enabled":\s*\K(true|false)' data/luftentfeuchten_config.json || echo "unknown")
    echo "   luftentfeuchten_config.json: enabled=$LUFTENTFEUCHTEN_ENABLED"
else
    echo "   ❌ luftentfeuchten_config.json nicht gefunden!"
fi

echo ""

# 2. Setze enabled: true in beiden Dateien
echo "🔧 Schritt 2: Aktiviere Automation in beiden Config-Dateien..."

if [ -f "data/bathroom_config.json" ]; then
    # Backup
    cp data/bathroom_config.json data/bathroom_config.json.backup
    # Setze enabled: true
    sed -i.tmp 's/"enabled":\s*false/"enabled": true/g' data/bathroom_config.json
    rm -f data/bathroom_config.json.tmp
    echo "   ✅ bathroom_config.json aktualisiert"
fi

if [ -f "data/luftentfeuchten_config.json" ]; then
    # Backup
    cp data/luftentfeuchten_config.json data/luftentfeuchten_config.json.backup
    # Setze enabled: true
    sed -i.tmp 's/"enabled":\s*false/"enabled": true/g' data/luftentfeuchten_config.json
    rm -f data/luftentfeuchten_config.json.tmp
    echo "   ✅ luftentfeuchten_config.json aktualisiert"
fi

echo ""

# 3. Prüfe neue Config
echo "✅ Schritt 3: Neue Konfiguration:"
echo ""

if [ -f "data/bathroom_config.json" ]; then
    BATHROOM_ENABLED=$(grep -oP '"enabled":\s*\K(true|false)' data/bathroom_config.json)
    echo "   bathroom_config.json: enabled=$BATHROOM_ENABLED"
fi

if [ -f "data/luftentfeuchten_config.json" ]; then
    LUFTENTFEUCHTEN_ENABLED=$(grep -oP '"enabled":\s*\K(true|false)' data/luftentfeuchten_config.json)
    echo "   luftentfeuchten_config.json: enabled=$LUFTENTFEUCHTEN_ENABLED"
fi

echo ""

# 4. Starte Web-App neu (wenn läuft)
echo "🔄 Schritt 4: Starte Web-App neu..."

# Prüfe Port 8080
PID=$(lsof -ti:8080 2>/dev/null || echo "")
if [ -n "$PID" ]; then
    echo "   Stoppe laufende Web-App (PID: $PID)..."
    kill $PID
    sleep 3
    echo "   ✅ Web-App gestoppt"
else
    echo "   ℹ️  Keine Web-App auf Port 8080 gefunden"
fi

# Starte Web-App neu
if [ -d "venv" ]; then
    echo "   Starte Web-App neu..."
    source venv/bin/activate
    nohup python3 main.py web --host 0.0.0.0 --port 8080 > logs/web_app.log 2>&1 &
    sleep 5

    # Prüfe ob gestartet
    if lsof -ti:8080 > /dev/null 2>&1; then
        echo "   ✅ Web-App läuft auf Port 8080"
    else
        echo "   ❌ Web-App konnte nicht gestartet werden!"
        echo "   Prüfe logs/web_app.log"
        exit 1
    fi
else
    echo "   ⚠️  venv nicht gefunden - Web-App muss manuell gestartet werden"
fi

echo ""
echo "=========================================="
echo "✅ Badezimmer-Automation aktiviert!"
echo "=========================================="
echo ""
echo "Nächste Schritte:"
echo "1. Öffne die Web-UI im Browser"
echo "2. Aktualisiere die Seite (Strg+F5 / Cmd+Shift+R)"
echo "3. Die Warnung 'Automation ist deaktiviert' sollte verschwunden sein"
echo "4. Backups: data/*_config.json.backup"
echo ""
