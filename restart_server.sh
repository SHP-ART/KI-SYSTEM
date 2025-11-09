#!/bin/bash

# KI-System Server Neustart-Skript
# Stoppt alte Instanzen und startet den Server neu mit aktuellen Änderungen

echo "🔄 Starte KI-System Server neu..."

# Farben für Ausgabe
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Prüfe ob im richtigen Verzeichnis
if [ ! -f "main.py" ]; then
    echo -e "${RED}❌ Fehler: main.py nicht gefunden. Bitte im KI-SYSTEM Verzeichnis ausführen.${NC}"
    exit 1
fi

# Stoppe alte Server-Instanzen
echo "🛑 Stoppe alte Server-Instanzen..."
for port in 8080 5000 8000; do
    pid=$(lsof -ti:$port 2>/dev/null)
    if [ ! -z "$pid" ]; then
        echo -e "${YELLOW}  Stoppe Server auf Port $port (PID: $pid)${NC}"
        kill -9 $pid 2>/dev/null
        sleep 1
    fi
done

# Prüfe Python-Umgebung
if [ -d "venv" ]; then
    echo "🐍 Aktiviere Virtual Environment..."
    source venv/bin/activate
else
    echo -e "${YELLOW}⚠️  Kein venv gefunden - verwende System-Python${NC}"
fi

# Prüfe Dependencies
echo "📦 Prüfe Dependencies..."
python3 -c "import loguru" 2>/dev/null || {
    echo -e "${RED}❌ Fehler: loguru nicht installiert${NC}"
    echo "Installiere Dependencies..."
    pip install -r requirements.txt
}

# Führe Datenbank-Migrationen aus (wird automatisch beim Start gemacht)
echo "🗄️  Datenbank-Migrationen werden beim Start automatisch ausgeführt..."

# Starte Server
echo -e "${GREEN}🚀 Starte Server auf Port 8080...${NC}"
echo ""
echo "Server-URL: http://0.0.0.0:8080"
echo "Drücke Ctrl+C zum Beenden"
echo ""

# Starte Server im Vordergrund
python3 main.py web --host 0.0.0.0 --port 8080

# Wenn Server beendet wird
echo -e "\n${YELLOW}Server wurde beendet${NC}"
