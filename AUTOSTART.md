# Autostart & Prozess-Management

Dieses Dokument erklärt verschiedene Methoden, um das KI Smart Home System automatisch zu starten und laufen zu halten.

## 🚀 Schnellstart-Scripts

### start.sh - Web-Interface starten/neu starten

Das einfachste und empfohlene Script für manuelles Starten:

```bash
# Mach das Script ausführbar (einmalig)
chmod +x start.sh stop.sh

# Starten
./start.sh

# Starten mit anderem Port
./start.sh 8080

# Starten mit anderem Host und Port
./start.sh 0.0.0.0 8080

# Neu starten (automatisch)
./start.sh --restart

# Stoppen
./stop.sh
```

**Features:**
- ✅ Prüft ob bereits läuft
- ✅ Stoppt alte Instanzen automatisch
- ✅ Startet im Hintergrund (nohup)
- ✅ Erstellt PID-Datei für Prozess-Tracking
- ✅ Zeigt Status und Logs
- ✅ Aktiviert Virtual Environment automatisch

**Logs ansehen:**
```bash
# Live-Logs
tail -f logs/webapp.log

# Letzte 50 Zeilen
tail -50 logs/webapp.log

# Mit Farben
tail -f logs/webapp.log | grep --color=auto -E 'ERROR|WARNING|INFO'
```

---

## 🔄 Methode 1: PM2 (Empfohlen für Produktion)

PM2 ist ein professioneller Prozess-Manager mit Auto-Restart, Monitoring und Load Balancing.

### Installation

```bash
# PM2 global installieren
npm install -g pm2

# Oder via Homebrew (macOS)
brew install pm2
```

### Nutzung

```bash
# Starten
pm2 start ecosystem.config.js

# Status prüfen
pm2 status
pm2 list

# Logs ansehen
pm2 logs ki-smart-home

# Monitoring
pm2 monit

# Neustart
pm2 restart ki-smart-home

# Stoppen
pm2 stop ki-smart-home

# Aus Liste entfernen
pm2 delete ki-smart-home
```

### Autostart bei System-Reboot

```bash
# PM2 als Startup-Service einrichten
pm2 startup

# Führe den angezeigten Befehl aus (je nach System)
# Beispiel: sudo env PATH=$PATH:/usr/bin pm2 startup systemd -u USERNAME --hp /home/USERNAME

# Aktuelle PM2-Prozesse speichern
pm2 save
```

**Vorteile:**
- ✅ Automatischer Neustart bei Crashes
- ✅ Load Balancing (mehrere Instanzen)
- ✅ Echtzeit-Monitoring
- ✅ Log-Rotation
- ✅ Cluster-Mode
- ✅ Web-Interface (Keymetrics)

**Konfiguration:** `ecosystem.config.js`

---

## 🐧 Methode 2: Systemd (Linux)

Für Linux-Systeme mit systemd (Ubuntu, Debian, CentOS, etc.)

### Installation

1. **Service-Datei anpassen:**

```bash
# Kopiere Template
cp systemd/ki-smart-home.service /tmp/ki-smart-home.service

# Bearbeite und ersetze Platzhalter
nano /tmp/ki-smart-home.service
```

**Ersetze:**
- `YOUR_USERNAME` → Dein Linux-Username
- `/path/to/KI-SYSTEM` → Vollständiger Pfad zum Projekt (z.B. `/home/user/KI-SYSTEM`)

2. **Service installieren:**

```bash
# Kopiere nach systemd
sudo cp /tmp/ki-smart-home.service /etc/systemd/system/

# Berechtigungen setzen
sudo chmod 644 /etc/systemd/system/ki-smart-home.service

# Systemd neu laden
sudo systemctl daemon-reload

# Service aktivieren (Autostart)
sudo systemctl enable ki-smart-home

# Service starten
sudo systemctl start ki-smart-home
```

### Nutzung

```bash
# Status prüfen
sudo systemctl status ki-smart-home

# Starten
sudo systemctl start ki-smart-home

# Stoppen
sudo systemctl stop ki-smart-home

# Neustart
sudo systemctl restart ki-smart-home

# Logs ansehen
sudo journalctl -u ki-smart-home -f

# Autostart deaktivieren
sudo systemctl disable ki-smart-home
```

**Vorteile:**
- ✅ Native Linux-Integration
- ✅ Automatischer Start beim Booten
- ✅ Automatischer Neustart bei Crashes (RestartSec=10)
- ✅ Zentrale Log-Verwaltung (journalctl)
- ✅ Keine zusätzlichen Dependencies

---

## 🍎 Methode 3: launchd (macOS)

Für macOS-Systeme mit launchd.

### Service-Datei erstellen

```bash
# Erstelle plist-Datei
nano ~/Library/LaunchAgents/com.smart-home.ki-system.plist
```

**Inhalt:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.smart-home.ki-system</string>

    <key>ProgramArguments</key>
    <array>
        <string>/path/to/KI-SYSTEM/venv/bin/python</string>
        <string>/path/to/KI-SYSTEM/main.py</string>
        <string>web</string>
        <string>--host</string>
        <string>0.0.0.0</string>
        <string>--port</string>
        <string>5000</string>
    </array>

    <key>WorkingDirectory</key>
    <string>/path/to/KI-SYSTEM</string>

    <key>StandardOutPath</key>
    <string>/path/to/KI-SYSTEM/logs/webapp.log</string>

    <key>StandardErrorPath</key>
    <string>/path/to/KI-SYSTEM/logs/webapp_error.log</string>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
```

**Ersetze** `/path/to/KI-SYSTEM` mit dem tatsächlichen Pfad!

### Nutzung

```bash
# Laden (starten)
launchctl load ~/Library/LaunchAgents/com.smart-home.ki-system.plist

# Entladen (stoppen)
launchctl unload ~/Library/LaunchAgents/com.smart-home.ki-system.plist

# Status prüfen
launchctl list | grep ki-system

# Logs ansehen
tail -f logs/webapp.log
```

---

## 🪟 Methode 4: Windows Task Scheduler

Für Windows-Systeme.

### Via GUI

1. **Task Scheduler öffnen:** `Win + R` → `taskschd.msc`
2. **Task erstellen:**
   - Name: `KI Smart Home`
   - Trigger: Bei Anmeldung
   - Aktion: Programm starten
   - Programm: `C:\path\to\KI-SYSTEM\venv\Scripts\python.exe`
   - Argumente: `main.py web --host 0.0.0.0 --port 5000`
   - Starten in: `C:\path\to\KI-SYSTEM`

### Via PowerShell Script

```powershell
# start.ps1
$env:VIRTUAL_ENV = "C:\path\to\KI-SYSTEM\venv"
$env:PATH = "$env:VIRTUAL_ENV\Scripts;$env:PATH"

cd C:\path\to\KI-SYSTEM

# Prüfe ob bereits läuft
$running = Get-Process python -ErrorAction SilentlyContinue | Where-Object {$_.Path -like "*KI-SYSTEM*"}

if ($running) {
    Write-Host "Web-Interface läuft bereits!"
    Write-Host "PID: $($running.Id)"
} else {
    Write-Host "Starte Web-Interface..."
    Start-Process python -ArgumentList "main.py","web","--host","0.0.0.0","--port","5000" -WindowStyle Hidden
    Start-Sleep 3
    Write-Host "✓ Gestartet!"
}
```

---

## 🔧 Methode 5: Cron Job (Linux/macOS)

Einfache Methode für regelmäßige Prüfung ob Service läuft.

### Cron-Job erstellen

```bash
# Öffne Crontab
crontab -e

# Füge hinzu (prüft alle 5 Minuten)
*/5 * * * * /path/to/KI-SYSTEM/start.sh > /dev/null 2>&1

# Oder: Bei Reboot starten
@reboot /path/to/KI-SYSTEM/start.sh
```

**Nachteile:**
- ⚠️ Kein sofortiger Restart bei Crash (nur alle 5 Min)
- ⚠️ Keine Logs/Monitoring
- ⚠️ Kann mehrere Instanzen starten wenn Script nicht korrekt

**Besser:** Nutze PM2 oder Systemd!

---

## 📊 Vergleich der Methoden

| Methode | Auto-Start | Auto-Restart | Monitoring | Logs | Komplexität | Empfohlen für |
|---------|-----------|--------------|------------|------|-------------|---------------|
| **start.sh** | ❌ | ❌ | ⚠️ Basic | ✅ | 🟢 Einfach | Entwicklung, Tests |
| **PM2** | ✅ | ✅ | ✅ Exzellent | ✅ | 🟡 Mittel | Produktion, Heimserver |
| **Systemd** | ✅ | ✅ | ⚠️ Basic | ✅ | 🟡 Mittel | Linux-Server |
| **launchd** | ✅ | ✅ | ⚠️ Basic | ✅ | 🟡 Mittel | macOS |
| **Task Scheduler** | ✅ | ❌ | ❌ | ⚠️ | 🟢 Einfach | Windows |
| **Cron** | ✅ | ⚠️ Verzögert | ❌ | ❌ | 🟢 Einfach | Nicht empfohlen |

---

## 🎯 Empfehlungen

### Für Entwicklung
```bash
./start.sh
```
Schnell, einfach, flexibel.

### Für Heimserver / Raspberry Pi
```bash
npm install -g pm2
pm2 start ecosystem.config.js
pm2 startup
pm2 save
```
Professionell, zuverlässig, mit Monitoring.

### Für Linux-Server (ohne Node.js)
```bash
sudo systemctl enable ki-smart-home
sudo systemctl start ki-smart-home
```
Native Integration, keine Extra-Dependencies.

### Für macOS (Autostart bei Login)
```bash
launchctl load ~/Library/LaunchAgents/com.smart-home.ki-system.plist
```
Native macOS-Integration.

---

## 🐛 Troubleshooting

### Web-Interface startet nicht

1. **Prüfe Logs:**
   ```bash
   tail -50 logs/webapp.log
   ```

2. **Prüfe Python-Fehler:**
   ```bash
   python main.py web
   ```

3. **Prüfe Port:**
   ```bash
   lsof -i :5000
   ```

4. **Prüfe Virtual Environment:**
   ```bash
   which python
   # Sollte: /path/to/KI-SYSTEM/venv/bin/python
   ```

### PM2 funktioniert nicht

```bash
# PM2 zurücksetzen
pm2 kill
pm2 flush

# Neu starten
pm2 start ecosystem.config.js
```

### Systemd Service startet nicht

```bash
# Detaillierte Fehler ansehen
sudo journalctl -u ki-smart-home -n 50 --no-pager

# Service-Status
sudo systemctl status ki-smart-home
```

### Mehrere Instanzen laufen

```bash
# Alle stoppen
./stop.sh

# Oder manuell
pkill -9 -f "python.*main.py.*web"

# Neu starten
./start.sh
```

---

## 📝 Best Practices

1. **Immer Virtual Environment nutzen**
2. **Logs regelmäßig prüfen**
3. **PM2 oder Systemd für Produktion**
4. **start.sh für Entwicklung**
5. **Updates über Web-Interface machen** (automatischer Neustart)
6. **Firewall-Regeln setzen** falls öffentlich erreichbar

---

**Letzte Aktualisierung**: 2025-01-09
**Getestet auf**: Linux (Ubuntu 22.04), macOS (Sonoma), Raspberry Pi OS
