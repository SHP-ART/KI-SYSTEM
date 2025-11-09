# Server Neustart nach Updates

## Problem

Nach Git-Pull oder Code-Änderungen zeigt die Weboberfläche Fehler wie:
- HTTP 500: INTERNAL SERVER ERROR
- "Tabelle nicht gefunden" Fehler
- Alte Funktionen fehlen

## Ursache

Der laufende Server verwendet noch die alte Code-Version. Python lädt Module nur beim Start.

## Lösung: Server neu starten

### Option 1: Automatisches Restart-Skript (empfohlen)

```bash
./restart_server.sh
```

Das Skript:
- ✅ Stoppt automatisch alte Server-Instanzen (Ports 8080, 5000, 8000)
- ✅ Aktiviert venv (falls vorhanden)
- ✅ Prüft Dependencies
- ✅ Führt Datenbank-Migrationen automatisch aus
- ✅ Startet Server auf Port 8080

### Option 2: Manueller Neustart

**Schritt 1: Alte Instanzen stoppen**
```bash
# Finde und stoppe Server auf Port 8080
lsof -ti:8080 | xargs kill -9

# Oder für alle üblichen Ports:
lsof -ti:8080 | xargs kill -9 2>/dev/null
lsof -ti:5000 | xargs kill -9 2>/dev/null
lsof -ti:8000 | xargs kill -9 2>/dev/null
```

**Schritt 2: Virtual Environment aktivieren** (falls vorhanden)
```bash
source venv/bin/activate
```

**Schritt 3: Server starten**
```bash
python3 main.py web --host 0.0.0.0 --port 8080
```

### Option 3: Mit systemd (Production)

```bash
sudo systemctl restart ki-system
```

## Nach dem Neustart

Der Server sollte nun zeigen:
```
Database initialized at data/ki_system.db
✅ Applied migration 001: add_continuous_measurements  ← Nur bei ersten Mal
Bathroom Data Collector initialized (60s interval)
Heating Data Collector initialized
...
Starting web interface on http://0.0.0.0:8080
```

**Wichtig:** Die Migration `001_add_continuous_measurements` wird nur **einmal** ausgeführt, auch wenn du den Server mehrfach neu startest.

## Prüfen ob Server läuft

```bash
# Prüfe ob Port 8080 verwendet wird
lsof -i:8080

# Oder teste HTTP-Request
curl http://localhost:8080/api/database/status
```

## Logs prüfen

```bash
# Live-Logs ansehen
tail -f logs/ki_system.log

# Letzte 100 Zeilen
tail -100 logs/ki_system.log

# Fehler suchen
tail -200 logs/ki_system.log | grep -i error
```

## Häufige Probleme

### "Address already in use"
```
OSError: [Errno 48] Address already in use
```
**Lösung:** Ein alter Server läuft noch. Stoppe ihn mit:
```bash
lsof -ti:8080 | xargs kill -9
```

### "ModuleNotFoundError"
```
ModuleNotFoundError: No module named 'loguru'
```
**Lösung:** Dependencies installieren:
```bash
pip install -r requirements.txt
```

### "Permission denied"
```
PermissionError: [Errno 13] Permission denied
```
**Lösung:** Restart-Skript ausführbar machen:
```bash
chmod +x restart_server.sh
```

### Migration wird nicht ausgeführt
```
Database initialized at data/ki_system.db
(keine Migration-Meldung)
```
**Erklärung:** Das ist normal! Migrationen werden nur einmal ausgeführt. Wenn die Migration bereits angewendet wurde, wird sie übersprungen.

**Prüfen welche Migrationen angewendet wurden:**
```bash
sqlite3 data/ki_system.db "SELECT * FROM schema_migrations"
```

## Production Deployment

Für Production-Umgebungen empfehlen wir:
- systemd Service
- Supervisor
- Docker Container

Siehe `docs/deployment.md` für Details.

## Support

Bei weiteren Problemen:
1. Logs prüfen: `tail -100 logs/ki_system.log`
2. GitHub Issues: https://github.com/SHP-ART/KI-SYSTEM/issues
3. Server im Debug-Modus starten: `python3 main.py web --debug`
