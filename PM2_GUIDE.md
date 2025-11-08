# PM2 Process Manager - Quick Guide

PM2 ist ein Production Process Manager für Node.js und Python Anwendungen mit eingebautem Load Balancer.

## Installation

PM2 wird automatisch beim Setup angeboten. Zur manuellen Installation:

```bash
# Node.js muss installiert sein
npm install -g pm2
```

## Basis-Befehle

### Start
```bash
pm2 start ecosystem.config.js
pm2 save  # Speichert aktuelle Konfiguration
```

### Status & Monitoring
```bash
pm2 list         # Zeigt alle laufenden Prozesse
pm2 status       # Gleich wie list
pm2 show ki-smart-home  # Details zu einem Prozess
pm2 monit        # Live-Monitoring Dashboard
```

### Logs
```bash
pm2 logs                # Alle Logs
pm2 logs ki-smart-home  # Nur App-Logs
pm2 logs --lines 100    # Letzte 100 Zeilen
pm2 flush               # Logs leeren
```

### Neustart & Stop
```bash
pm2 restart ki-smart-home
pm2 reload ki-smart-home   # Zero-downtime reload
pm2 stop ki-smart-home
pm2 delete ki-smart-home   # Aus PM2 entfernen
```

### System Autostart
```bash
pm2 startup      # Zeigt Befehl für Autostart
# Führe den angezeigten Befehl aus (mit sudo)
pm2 save         # Speichert aktuelle Apps
```

Um Autostart zu deaktivieren:
```bash
pm2 unstartup
```

## Erweiterte Features

### Resource Limits
```bash
# Max Memory (bereits in ecosystem.config.js konfiguriert)
pm2 restart ki-smart-home --max-memory-restart 500M
```

### Cron Restart
Automatischer Neustart ist in `ecosystem.config.js` konfiguriert:
- Täglich um 04:00 Uhr
- Kann in der Config angepasst werden

### Environment Variables
```bash
pm2 start ecosystem.config.js --env production
```

## Troubleshooting

### App startet nicht
```bash
pm2 logs ki-smart-home --err  # Nur Fehler
pm2 describe ki-smart-home    # Detaillierte Infos
```

### PM2 Daemon Probleme
```bash
pm2 kill         # Stoppt PM2 Daemon
pm2 resurrect    # Startet gespeicherte Apps neu
```

### Logs zu groß
```bash
pm2 install pm2-logrotate
pm2 set pm2-logrotate:max_size 10M
```

## Konfigurationsdatei

Die `ecosystem.config.js` enthält alle App-Einstellungen:

```javascript
{
  name: 'ki-smart-home',
  script: 'main.py',
  interpreter: './venv/bin/python3',
  autorestart: true,
  max_memory_restart: '500M',
  cron_restart: '0 4 * * *'  // 04:00 Uhr
}
```

Änderungen aktivieren:
```bash
pm2 reload ecosystem.config.js
pm2 save
```

## Best Practices

1. **Immer speichern nach Änderungen:**
   ```bash
   pm2 save
   ```

2. **Logs regelmäßig prüfen:**
   ```bash
   pm2 logs --lines 50
   ```

3. **Monitoring nutzen:**
   ```bash
   pm2 monit
   ```

4. **Autostart einrichten:**
   ```bash
   pm2 startup
   pm2 save
   ```

## Nützliche Aliasse

Füge diese zu deiner `.bashrc` oder `.zshrc` hinzu:

```bash
alias pm2l='pm2 logs'
alias pm2m='pm2 monit'
alias pm2s='pm2 status'
alias pm2r='pm2 restart ki-smart-home'
```

## Integration mit KI Smart Home

### Start mit PM2
```bash
pm2 start ecosystem.config.js
```

### Manueller Start (ohne PM2)
```bash
python main.py web --host 0.0.0.0 --port 8080
```

### Update-Prozess
Das `update.sh` Script erkennt PM2 automatisch:
- Mit PM2: `pm2 restart ki-smart-home`
- Ohne PM2: Manueller Neustart

## Web-Interface

PM2 bietet auch ein optionales Web-Interface:

```bash
pm2 web  # Startet auf Port 9615
```

Zugriff: http://localhost:9615

## Weitere Informationen

- Offizielle Dokumentation: https://pm2.keymetrics.io/
- Quick Start: https://pm2.keymetrics.io/docs/usage/quick-start/
- PM2 on GitHub: https://github.com/Unitech/pm2
