#!/bin/bash
# Stop-Script für KI Smart Home Web-Interface

# Farben
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

PID_FILE="data/webapp.pid"

echo "╔═══════════════════════════════════════════╗"
echo "║   KI Smart Home - Web-Interface Stop    ║"
echo "╚═══════════════════════════════════════════╝"
echo ""

echo "🛑 Stoppe Web-Interface..."

# Methode 1: Via PID-Datei
if [[ -f "$PID_FILE" ]]; then
    PID=$(cat "$PID_FILE")
    if ps -p $PID > /dev/null 2>&1; then
        echo "Stoppe Prozess (PID: $PID)..."
        kill $PID 2>/dev/null || true
        sleep 2

        # Force kill falls noch läuft
        if ps -p $PID > /dev/null 2>&1; then
            echo "Force-Kill (PID: $PID)..."
            kill -9 $PID 2>/dev/null || true
        fi

        echo -e "${GREEN}✓ Prozess gestoppt${NC}"
    else
        echo -e "${YELLOW}⚠️  Prozess läuft nicht mehr (alte PID-Datei)${NC}"
    fi
    rm -f "$PID_FILE"
fi

# Methode 2: Alle Python main.py web Prozesse
echo "Suche nach laufenden Web-Interface Prozessen..."
PIDS=$(pgrep -f "python.*main.py.*web" 2>/dev/null || true)

if [[ -n "$PIDS" ]]; then
    echo "Gefundene Prozesse: $PIDS"
    pkill -f "python.*main.py.*web" 2>/dev/null || true
    sleep 1

    # Force kill falls noch läuft
    pkill -9 -f "python.*main.py.*web" 2>/dev/null || true

    echo -e "${GREEN}✓ Alle Web-Interface Prozesse gestoppt${NC}"
else
    echo -e "${YELLOW}⚠️  Keine laufenden Prozesse gefunden${NC}"
fi

# Prüfe Ports
for PORT in 5000 8080; do
    if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        PID=$(lsof -ti :$PORT)
        echo -e "${YELLOW}⚠️  Port $PORT noch belegt durch PID $PID${NC}"
        echo "Stoppe Prozess..."
        kill -9 $PID 2>/dev/null || true
    fi
done

echo ""
echo -e "${GREEN}✅ Web-Interface vollständig gestoppt${NC}"
echo ""
echo "💡 Zum Neustarten:"
echo "   ./start.sh"
echo ""
