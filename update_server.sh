#!/bin/bash
# Update-Script für KI-SYSTEM Server
# Führt alle notwendigen Schritte aus, um den Server zu aktualisieren

set -e  # Bei Fehler abbrechen

echo "=========================================="
echo "KI-SYSTEM Server Update"
echo "=========================================="
echo ""

# 1. Aktuellen Status prüfen
echo "📋 Schritt 1: Prüfe Git Status..."
git status
echo ""

# 2. Änderungen vom Remote Repository holen
echo "📥 Schritt 2: Hole Änderungen von GitHub..."
git pull origin main
echo ""

# 3. Prüfe ob luftentfeuchten_config.json aktualisiert wurde
echo "🔍 Schritt 3: Prüfe Konfigurationsdatei..."
if grep -q "frost_protection_temperature" data/luftentfeuchten_config.json; then
    echo "✅ frost_protection_temperature gefunden in luftentfeuchten_config.json"
else
    echo "❌ frost_protection_temperature NICHT gefunden!"
    echo "   Bitte prüfe data/luftentfeuchten_config.json manuell"
    exit 1
fi
echo ""

# 4. Stoppe laufende Web-App
echo "🛑 Schritt 4: Stoppe laufende Web-App (Port 8080)..."
PID=$(lsof -ti:8080 2>/dev/null || echo "")
if [ -n "$PID" ]; then
    echo "   Stoppe Prozess $PID..."
    kill $PID
    sleep 3
    echo "✅ Web-App gestoppt"
else
    echo "   ℹ️  Keine laufende Web-App gefunden"
fi
echo ""

# 5. Aktiviere Virtual Environment und starte Web-App neu
echo "🚀 Schritt 5: Starte Web-App neu..."
source venv/bin/activate

# Starte Web-App im Hintergrund
nohup python3 main.py web --host 0.0.0.0 --port 8080 > logs/web_app.log 2>&1 &

# Warte kurz
sleep 5
echo ""

# 6. Prüfe ob Web-App läuft
echo "✅ Schritt 6: Prüfe ob Web-App läuft..."
if lsof -ti:8080 > /dev/null 2>&1; then
    echo "✅ Web-App läuft auf Port 8080"
else
    echo "❌ Web-App läuft NICHT!"
    echo "   Prüfe logs/web_app.log für Fehler"
    exit 1
fi
echo ""

# 7. Teste API-Endpunkt
echo "🧪 Schritt 7: Teste Bathroom API..."
sleep 3
RESPONSE=$(curl -s http://localhost:8080/api/luftentfeuchten/status)

if echo "$RESPONSE" | grep -q "enabled"; then
    echo "✅ API antwortet korrekt"

    # Prüfe ob neue Version läuft (mit frost_protection)
    if grep -q "Frost=" logs/web_app.log 2>/dev/null; then
        echo "✅ Neue Version mit Frostschutz-Funktion aktiv!"
    else
        echo "⚠️  API läuft, aber möglicherweise noch alte Version"
        echo "   Prüfe logs/web_app.log"
    fi
else
    echo "⚠️  API-Response ungewöhnlich:"
    echo "$RESPONSE" | head -5
fi
echo ""

echo "=========================================="
echo "✅ Update abgeschlossen!"
echo "=========================================="
echo ""
echo "Nächste Schritte:"
echo "1. Öffne http://192.168.12.198:8080/luftentfeuchten im Browser"
echo "2. Prüfe ob Sensordaten angezeigt werden"
echo "3. Bei Problemen: tail -f logs/web_app.log"
echo ""
