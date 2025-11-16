# KI-SYSTEM Deployment

Anleitung für das Deployment des KI-SYSTEM als Hintergrund-Service.

## Systemd Service (Empfohlen für Linux)

### Installation

1. **Service-Datei kopieren:**
   ```bash
   sudo cp deployment/systemd/ki-collector-manager.service /etc/systemd/system/
   ```

2. **Pfade anpassen (falls nötig):**
   Editiere `/etc/systemd/system/ki-collector-manager.service` und passe an:
   - `User=` (dein Benutzername)
   - `Group=` (deine Gruppe)
   - `WorkingDirectory=` (Pfad zu KI-SYSTEM)
   - `ExecStart=` (Pfad zu Python venv)

3. **Service aktivieren:**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable ki-collector-manager
   sudo systemctl start ki-collector-manager
   ```

### Verwaltung

```bash
# Status prüfen
sudo systemctl status ki-collector-manager

# Logs anzeigen
sudo journalctl -u ki-collector-manager -f

# Service stoppen
sudo systemctl stop ki-collector-manager

# Service neustarten
sudo systemctl restart ki-collector-manager

# Service deaktivieren
sudo systemctl disable ki-collector-manager
```

## Supervisor (Alternative)

Falls systemd nicht verfügbar ist, kann Supervisor verwendet werden:

1. **Supervisor installieren:**
   ```bash
   sudo apt-get install supervisor
   ```

2. **Config erstellen:**
   ```bash
   sudo nano /etc/supervisor/conf.d/ki-collector-manager.conf
   ```

   Inhalt:
   ```ini
   [program:ki-collector-manager]
   command=/home/pi/KI-SYSTEM/venv/bin/python3 -m src.background.collector_manager --config config/config.yaml
   directory=/home/pi/KI-SYSTEM
   user=pi
   autostart=true
   autorestart=true
   stderr_logfile=/var/log/ki-collector-manager.err.log
   stdout_logfile=/var/log/ki-collector-manager.out.log
   ```

3. **Supervisor neuladen:**
   ```bash
   sudo supervisorctl reread
   sudo supervisorctl update
   sudo supervisorctl start ki-collector-manager
   ```

## Manueller Start (für Tests)

```bash
# Im Vordergrund
python3 -m src.background.collector_manager --config config/config.yaml

# Im Hintergrund (Screen)
screen -dmS ki-collector python3 -m src.background.collector_manager --config config/config.yaml

# Im Hintergrund (Tmux)
tmux new-session -d -s ki-collector 'python3 -m src.background.collector_manager --config config/config.yaml'
```

## Konfiguration

Die Collector werden über `config/config.yaml` konfiguriert:

```yaml
# Collector-Einstellungen
collectors:
  heating:
    enabled: true
    interval: 60  # Sekunden

  lighting:
    enabled: true
    interval: 60

  windows:
    enabled: true
    interval: 60

  temperature:
    enabled: true
    interval: 60

  bathroom:
    enabled: false  # Optional
    interval: 60

# ML Auto-Trainer
ml_auto_trainer:
  enabled: true
  training_time: "03:00"  # Täglich um 3:00 Uhr

# Badezimmer-Optimizer
bathroom_optimizer:
  enabled: false
  optimization_time: "03:30"

# Database Maintenance
database_maintenance:
  enabled: true
  cleanup_time: "04:00"
  retention_days: 90
```

## Monitoring

### Logs

- **Systemd:** `sudo journalctl -u ki-collector-manager -f`
- **Supervisor:** `tail -f /var/log/ki-collector-manager.out.log`
- **Datei:** `tail -f logs/ki_system.log`

### Status-Check

```python
from src.background.collector_manager import CollectorManager

manager = CollectorManager()
status = manager.get_status()
print(status)
```

## Troubleshooting

### Service startet nicht

1. Prüfe Logs: `sudo journalctl -u ki-collector-manager -n 50`
2. Prüfe Pfade in Service-Datei
3. Prüfe Berechtigungen: `ls -la /home/pi/KI-SYSTEM`
4. Teste manuell: `python3 -m src.background.collector_manager`

### Collector stoppt unerwartet

- Prüfe Datenbank-Verbindung
- Prüfe Platform-API (Homey/Home Assistant)
- Prüfe verfügbaren Speicherplatz: `df -h`
- Prüfe RAM: `free -h`

### Performance-Probleme

- Erhöhe Intervalle in config.yaml
- Deaktiviere nicht benötigte Collectors
- Prüfe Datenbank-Größe: `du -sh data/ki_system.db`
- Führe Database Maintenance aus

## Best Practices

1. **Backup:** Regelmäßige Backups von `data/ki_system.db`
2. **Monitoring:** Überwache Logs regelmäßig
3. **Updates:** Stoppe Service vor Updates
4. **Testing:** Teste Änderungen erst manuell
5. **Retention:** Passe `retention_days` an verfügbaren Speicher an
