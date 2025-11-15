# Deployment Guide

Produktionsreife Deployment-Anleitung für das KI Smart Home System.

## Inhaltsverzeichnis

- [Systemanforderungen](#systemanforderungen)
- [Deployment-Optionen](#deployment-optionen)
- [Docker Deployment](#docker-deployment)
- [systemd Service](#systemd-service)
- [Produktions-Best-Practices](#produktions-best-practices)
- [Monitoring & Logging](#monitoring--logging)
- [Backup & Recovery](#backup--recovery)
- [Security](#security)

---

## Systemanforderungen

### Minimum
- **CPU:** 2 Cores
- **RAM:** 2 GB
- **Disk:** 10 GB freier Speicher
- **OS:** Linux (Ubuntu 20.04+, Debian 11+) oder macOS
- **Python:** 3.9+
- **Netzwerk:** Zugriff auf Homey/Home Assistant APIs

### Empfohlen
- **CPU:** 4 Cores
- **RAM:** 4 GB
- **Disk:** 20 GB SSD
- **Python:** 3.11+

---

## Deployment-Optionen

### 1. Systemd Service (Empfohlen für Linux)
Am besten für dedizierte Server oder Raspberry Pi.

### 2. Docker
Isolierte Container-Umgebung, einfaches Deployment.

### 3. PM2 (Node.js Process Manager)
Bereits konfiguriert in `ecosystem.config.js`.

---

## Docker Deployment

### Dockerfile erstellen

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# System-Dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Python Dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application Code
COPY . .

# Data Directory
VOLUME /app/data
VOLUME /app/models
VOLUME /app/logs

# Port
EXPOSE 8080

# Health Check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health')"

# Start
CMD ["python", "main.py", "web", "--host", "0.0.0.0", "--port", "8080"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  ki-smart-home:
    build: .
    container_name: ki-smart-home
    restart: unless-stopped
    ports:
      - "8080:8080"
    volumes:
      - ./data:/app/data
      - ./models:/app/models
      - ./logs:/app/logs
      - ./config:/app/config
    environment:
      - PYTHONUNBUFFERED=1
      - TZ=Europe/Berlin
    env_file:
      - .env
    healthcheck:
      test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8080/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### .env Datei

```bash
# .env
HOMEY_URL=http://192.168.1.100
HOMEY_TOKEN=your-homey-token
HA_URL=http://192.168.1.101:8123
HA_TOKEN=your-ha-token
OPENWEATHER_API_KEY=your-api-key
AWATTAR_API_URL=https://api.awattar.de/v1/marketdata
```

### Deployment Commands

```bash
# Build
docker-compose build

# Start
docker-compose up -d

# Logs
docker-compose logs -f

# Stop
docker-compose down

# Update
docker-compose pull
docker-compose up -d
```

---

## systemd Service

### Service-Datei

Bereits vorhanden in `systemd/ki-smart-home.service`:

```ini
[Unit]
Description=KI Smart Home System
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/ki-smart-home
ExecStart=/home/pi/ki-smart-home/venv/bin/python main.py web --host 0.0.0.0 --port 8080
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### Installation

```bash
# Service kopieren
sudo cp systemd/ki-smart-home.service /etc/systemd/system/

# User anpassen (falls nicht 'pi')
sudo nano /etc/systemd/system/ki-smart-home.service

# Service aktivieren
sudo systemctl daemon-reload
sudo systemctl enable ki-smart-home.service

# Service starten
sudo systemctl start ki-smart-home.service

# Status prüfen
sudo systemctl status ki-smart-home.service

# Logs ansehen
sudo journalctl -u ki-smart-home.service -f
```

### Verwaltung

```bash
# Stoppen
sudo systemctl stop ki-smart-home.service

# Neustarten
sudo systemctl restart ki-smart-home.service

# Deaktivieren
sudo systemctl disable ki-smart-home.service
```

---

## Produktions-Best-Practices

### 1. Reverse Proxy (nginx)

```nginx
server {
    listen 80;
    server_name smart-home.example.com;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket Support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # SSL (nach Let's Encrypt Setup)
    # listen 443 ssl;
    # ssl_certificate /etc/letsencrypt/live/smart-home.example.com/fullchain.pem;
    # ssl_certificate_key /etc/letsencrypt/live/smart-home.example.com/privkey.pem;
}
```

### 2. Umgebungsvariablen

Sensible Daten NICHT in `config.yaml`:

```bash
export HOMEY_TOKEN="your-secret-token"
export HA_TOKEN="your-secret-token"
export OPENWEATHER_API_KEY="your-api-key"
```

### 3. Datenbank-Optimierung

```bash
# Regelmäßige Vakuumierung
sqlite3 data/ki_system.db "VACUUM;"

# In crontab:
0 3 * * * sqlite3 /path/to/data/ki_system.db "VACUUM;"
```

### 4. Log-Rotation

```bash
# /etc/logrotate.d/ki-smart-home
/home/pi/ki-smart-home/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    missingok
    copytruncate
}
```

---

## Monitoring & Logging

### Health Check Endpoint

```bash
curl http://localhost:8080/health
# {"status": "ok"}
```

### Prometheus Metrics (Optional)

```python
# In app.py hinzufügen:
from prometheus_client import make_wsgi_app, Counter, Gauge
from werkzeug.middleware.dispatcher import DispatcherMiddleware

# Metrics
request_count = Counter('http_requests_total', 'Total HTTP Requests')
temperature_gauge = Gauge('room_temperature', 'Room Temperature', ['room'])

# Middleware
app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {
    '/metrics': make_wsgi_app()
})
```

### Grafana Dashboard

Verbinde Prometheus mit Grafana für visualisierte Metriken:
- Raumtemperaturen
- Heizungsaktivität
- ML-Predictions
- API-Requests

---

## Backup & Recovery

### Backup-Script

```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/ki-smart-home"

mkdir -p $BACKUP_DIR

# Database
sqlite3 data/ki_system.db ".backup '$BACKUP_DIR/ki_system_$DATE.db'"

# ML Models
tar -czf $BACKUP_DIR/models_$DATE.tar.gz models/

# Config
cp config/config.yaml $BACKUP_DIR/config_$DATE.yaml

# Delete old backups (älter als 30 Tage)
find $BACKUP_DIR -name "*.db" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
```

### Cron Job

```bash
# Täglich um 2 Uhr
0 2 * * * /home/pi/ki-smart-home/backup.sh >> /var/log/ki-backup.log 2>&1
```

### Recovery

```bash
# Database wiederherstellen
cp /backups/ki-smart-home/ki_system_20240115_020000.db data/ki_system.db

# Models wiederherstellen
tar -xzf /backups/ki-smart-home/models_20240115_020000.tar.gz

# Service neustarten
sudo systemctl restart ki-smart-home.service
```

---

## Security

### 1. Firewall

```bash
# UFW (Ubuntu)
sudo ufw allow 8080/tcp
sudo ufw enable
```

### 2. API Authentication (TODO)

Zukünftig JWT-basierte Authentifizierung:

```python
from flask_jwt_extended import JWTManager, jwt_required

app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY')
jwt = JWTManager(app)

@app.route('/api/protected')
@jwt_required()
def protected():
    return {"msg": "Authenticated"}
```

### 3. HTTPS

```bash
# Let's Encrypt
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d smart-home.example.com
```

### 4. Secret Management

Verwende Vault oder AWS Secrets Manager für Produktionsumgebungen.

---

## Update-Prozess

```bash
# 1. Backup erstellen
./backup.sh

# 2. Code aktualisieren
git pull origin main

# 3. Dependencies aktualisieren
pip install -r requirements.txt

# 4. Migrationen ausführen
python -c "from src.utils.database import Database; db = Database(); db.run_migrations()"

# 5. Service neustarten
sudo systemctl restart ki-smart-home.service

# 6. Logs prüfen
sudo journalctl -u ki-smart-home.service -n 50
```

---

## Troubleshooting

### Service startet nicht

```bash
# Logs prüfen
sudo journalctl -u ki-smart-home.service -n 100

# Manuell starten für Debug
cd /home/pi/ki-smart-home
source venv/bin/activate
python main.py web
```

### Hoher Memory-Verbrauch

```bash
# Memory-Profiling
pip install memory_profiler
python -m memory_profiler main.py web
```

### Datenbank locked

```bash
# Connections prüfen
lsof data/ki_system.db

# WAL-Modus aktivieren (bessere Concurrency)
sqlite3 data/ki_system.db "PRAGMA journal_mode=WAL;"
```

---

## Support

Bei Problemen:
1. Logs prüfen: `logs/app.log` oder `journalctl`
2. Health Check: `curl http://localhost:8080/health`
3. GitHub Issues: https://github.com/your-repo/ki-system/issues
