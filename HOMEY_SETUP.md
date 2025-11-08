# Homey Pro Setup Guide

## Homey Pro mit dem KI-System verbinden

Dieses System unterstützt sowohl **Home Assistant** als auch **Homey Pro**. Hier erfährst du, wie du Homey Pro einrichtest.

## Voraussetzungen

- Homey Pro (2023 oder neuer) oder Homey (Bridge/Frühe Versionen)
- Internetzugang
- Homey Mobile App

## 1. Homey Bearer Token erstellen

### Option A: Homey Cloud API (empfohlen)

1. Gehe zu [https://developer.athom.com/](https://developer.athom.com/)
2. Melde dich mit deinem Athom Account an
3. Gehe zu "Apps" → "Create new app"
4. Alternativ: Nutze das OAuth2 Flow

**Einfacher Weg:**

```bash
# Installiere Homey CLI
npm install -g athom-cli

# Login
athom login

# Hole Token
athom user --bearer
```

Das gibt dir deinen Bearer Token aus.

### Option B: Lokale API

Wenn du Homey Pro lokal nutzen möchtest (ohne Cloud):

1. Finde die IP-Adresse deines Homey Pro
   - Homey App → Einstellungen → System → Netzwerk

2. Erstelle einen API Token:
   - Öffne `http://[HOMEY-IP]` im Browser
   - Gehe zu "Einstellungen" → "Benutzer" → "API Token"
   - Erstelle einen neuen Token

## 2. Konfiguration einrichten

### .env Datei

Bearbeite `.env`:

```bash
# Platform auf Homey setzen
PLATFORM_TYPE=homey

# Homey Cloud API
HOMEY_URL=https://api.athom.com
HOMEY_TOKEN=dein_bearer_token_hier

# Oder: Lokale API
# HOMEY_URL=http://192.168.1.100
# HOMEY_TOKEN=dein_lokaler_token
```

### config.yaml

Bearbeite `config/config.yaml`:

```yaml
# Smart Home Platform Auswahl
platform:
  type: "homey"  # Auf homey setzen!

# Homey Pro Verbindung
homey:
  url: "https://api.athom.com"  # oder lokale IP
  token: "YOUR_HOMEY_BEARER_TOKEN"
```

## 3. Device-IDs herausfinden

Homey nutzt andere IDs als Home Assistant.

### Via Homey Web App

1. Öffne `https://my.homey.app` (Cloud) oder `http://[HOMEY-IP]` (lokal)
2. Gehe zu "Geräte"
3. Klicke auf ein Gerät
4. Die URL zeigt die Device-ID: `/device/[DEVICE-ID]`

### Via CLI

```bash
# Alle Devices auflisten
athom homey devices list

# Bestimmtes Gerät suchen
athom homey devices list | grep "Wohnzimmer"
```

### Via Python (mit unserem System)

```python
python main.py test
# Zeigt alle verfügbaren Devices
```

## 4. Sensor-Konfiguration anpassen

Bearbeite `config/config.yaml` und trage deine Homey Device-IDs ein:

```yaml
data_collection:
  sensors:
    temperature:
      - "abc123-def456-ghi789"  # Homey Device-IDs
      - "xyz987-uvw654-rst321"
    light:
      - "light-device-id-123"
    motion:
      - "motion-sensor-id-456"
```

**Wichtig:** Bei Homey sind die IDs UUID-Format, nicht wie bei Home Assistant `sensor.name`.

## 5. Testen

```bash
# Verbindung testen
python main.py test

# Status anzeigen
python main.py status
```

Erwartete Ausgabe:

```
=== Connection Test Results ===
✓ homey: OK
✓ weather_api: OK
✓ energy_prices: OK
✓ database: OK

Overall: ✓ All systems operational
```

## Unterschiede zu Home Assistant

### Device-IDs

- **Home Assistant**: `sensor.wohnzimmer_temperatur`
- **Homey**: `abc123-def456-ghi789` (UUID-Format)

### Capabilities

Homey nutzt "Capabilities" statt "Domains":

| Home Assistant | Homey Capability |
|---------------|------------------|
| `light.turn_on` | `onoff: true` + `dim` |
| `climate.set_temperature` | `target_temperature` |
| `sensor.temperature` | `measure_temperature` |
| `binary_sensor.motion` | `alarm_motion` |

Das System konvertiert automatisch zwischen beiden Formaten!

### Zonen

Homey hat ein Zonen-Konzept (Räume). Das System unterstützt dies:

```python
# Hole alle Zonen
zones = platform.get_zones()

# Filter Devices nach Zone
devices_in_living_room = [d for d in devices if d['zone'] == 'living_room_id']
```

### Flows

Homey-spezifisch: Du kannst Flows triggern:

```python
# Trigger einen Homey Flow (Advanced)
platform.trigger_flow('flow-id-123')
```

## Homey vs Home Assistant - Was funktioniert?

| Feature | Home Assistant | Homey Pro |
|---------|---------------|-----------|
| Licht steuern | ✅ | ✅ |
| Temperatur setzen | ✅ | ✅ |
| Sensoren auslesen | ✅ | ✅ |
| Historische Daten | ✅ | ⚠️ Eingeschränkt |
| Automationen | ✅ | ✅ (Flows) |
| Scenes | ✅ | ⚠️ Via Flows |
| Zonen/Räume | ⚠️ Via Areas | ✅ Native |

## API-Endpunkte (Technische Details)

Das System nutzt die offiziellen Homey REST API-Endpunkte:

**Basis-URL:** `https://api.athom.com/api/manager/` (Cloud) oder `http://[HOMEY-IP]/api/manager/` (Lokal)

**Wichtige Endpunkte:**
- Devices auflisten: `GET /devices/device/`
- Device abrufen: `GET /devices/device/{id}/`
- Device steuern: `PUT /devices/device/{id}/capability/{capability}/` (z.B. `onoff`, `dim`, `target_temperature`)
- Zonen auflisten: `GET /zones/zone/`
- System-Info: `GET /system/`

**Authentifizierung:**
```
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json
```

## Troubleshooting

### "Connection refused"

**Cloud API:**
```bash
# Prüfe Token und API-Zugriff
curl -H "Authorization: Bearer YOUR_TOKEN" https://api.athom.com/api/manager/system/
```

**Lokale API:**
```bash
# Prüfe Erreichbarkeit
ping 192.168.1.100

# Prüfe API-Zugriff
curl -H "Authorization: Bearer YOUR_TOKEN" http://192.168.1.100/api/manager/system/
```

### "Device not found"

- Prüfe Device-ID Format (UUID, nicht Name)
- Stelle sicher, dass Device online ist
- Cache refresh: `platform._refresh_device_cache()`

### "Capability not supported"

Manche alte Homey-Geräte haben limitierte Capabilities:

```python
# Prüfe verfügbare Capabilities
device = platform.get_state('device-id')
print(device['attributes']['capabilities'])
```

## Weitere Informationen

- **Homey Web API Docs:** [https://api.developer.homey.app/](https://api.developer.homey.app/)
- **node-homey-api Referenz:** [https://athombv.github.io/node-homey-api/](https://athombv.github.io/node-homey-api/)
- **REST API Endpunkte:** [Homey-Endpoints GitHub](https://github.com/JohanBendz/Homey-Endpoints)
- **Homey Community Forum:** [https://community.homey.app/](https://community.homey.app/)
- **Homey CLI Tool:** [https://www.npmjs.com/package/athom-cli](https://www.npmjs.com/package/athom-cli)

### API-Versionen

Homey unterstützt verschiedene API-Versionen:
- **Web API v3** (empfohlen): Moderne REST + WebSocket API
- **REST API v2**: Legacy HTTP-only API

Dieses System nutzt die **REST API** für maximale Kompatibilität.

## Wechsel zwischen Plattformen

Du kannst jederzeit zwischen Home Assistant und Homey wechseln:

### Zu Homey wechseln:

```bash
# In .env
PLATFORM_TYPE=homey

# System neu starten
sudo systemctl restart ki-system
```

### Zu Home Assistant wechseln:

```bash
# In .env
PLATFORM_TYPE=homeassistant

# System neu starten
sudo systemctl restart ki-system
```

Die ML-Modelle und Datenbank bleiben erhalten!

## Support

Bei Problemen mit Homey-Integration:
- Prüfe die Logs: `tail -f logs/ki_system.log`
- Erstelle ein Issue auf GitHub
- Homey Forum: [community.homey.app](https://community.homey.app)
