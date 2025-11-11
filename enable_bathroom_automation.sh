#!/bin/bash
# Aktiviert die Badezimmer-Automation
# Setzt 'enabled: true' in luftentfeuchten_config.json

set -e

echo "=========================================="
echo "Aktiviere Badezimmer-Automation"
echo "=========================================="
echo ""

CONFIG_FILE="data/luftentfeuchten_config.json"

# Prüfe ob Config existiert
if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ $CONFIG_FILE nicht gefunden!"
    echo ""
    echo "Bitte führe zuerst aus:"
    echo "  git pull origin main"
    exit 1
fi

# Zeige aktuellen Status
CURRENT_STATUS=$(grep -oP '"enabled":\s*\K(true|false)' "$CONFIG_FILE" || echo "unknown")
echo "📋 Aktueller Status: enabled=$CURRENT_STATUS"
echo ""

# Wenn bereits aktiviert, nichts zu tun
if [ "$CURRENT_STATUS" = "true" ]; then
    echo "✅ Badezimmer-Automation ist bereits aktiviert!"
    exit 0
fi

# Backup erstellen
BACKUP_FILE="${CONFIG_FILE}.backup"
cp "$CONFIG_FILE" "$BACKUP_FILE"
echo "💾 Backup erstellt: $BACKUP_FILE"

# Aktiviere Automation
sed -i.tmp 's/"enabled":\s*false/"enabled": true/g' "$CONFIG_FILE"
rm -f "${CONFIG_FILE}.tmp"

# Prüfe neuen Status
NEW_STATUS=$(grep -oP '"enabled":\s*\K(true|false)' "$CONFIG_FILE")
echo "✅ Neuer Status: enabled=$NEW_STATUS"
echo ""

# Starte Web-App neu (wenn läuft)
echo "🔄 Starte Web-App neu..."

# Standard-Port ist 8080
PORT=${1:-8080}

PID=$(lsof -ti:$PORT 2>/dev/null || echo "")
if [ -n "$PID" ]; then
    echo "   Stoppe laufende Web-App (Port $PORT, PID: $PID)..."
    kill $PID
    sleep 3
fi

# Starte neu
if [ -d "venv" ]; then
    echo "   Starte Web-App auf Port $PORT..."
    source venv/bin/activate
    nohup python3 main.py web --host 0.0.0.0 --port $PORT > logs/web_app.log 2>&1 &
    sleep 5

    # Prüfe ob gestartet
    if lsof -ti:$PORT > /dev/null 2>&1; then
        echo "   ✅ Web-App läuft"
    else
        echo "   ❌ Web-App konnte nicht gestartet werden!"
        echo "   Prüfe: tail -f logs/web_app.log"
        exit 1
    fi
fi

echo ""
echo "=========================================="
echo "✅ Badezimmer-Automation aktiviert!"
echo "=========================================="
echo ""
echo "Nächste Schritte:"
echo "1. Öffne die Web-UI: http://localhost:$PORT/luftentfeuchten"
echo "2. Aktualisiere die Seite (Strg+F5 / Cmd+Shift+R)"
echo "3. Die Warnung sollte verschwunden sein"
echo ""
