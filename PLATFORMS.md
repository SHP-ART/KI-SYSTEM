# Unterstützte Smart Home Plattformen

Das KI-System unterstützt mehrere Smart Home Plattformen. Hier ein Überblick:

## Aktuell unterstützt

### Home Assistant ✅

**Status:** Vollständig unterstützt

**Features:**
- ✅ Alle Devices (Lights, Climate, Sensors, Switches)
- ✅ Services und Automationen
- ✅ Historische Daten (History API)
- ✅ States und Attributes
- ✅ REST API

**Setup:** Siehe [README.md](README.md)

**Vorteile:**
- Sehr weit verbreitet
- Riesige Community
- Tausende Integrationen
- Open Source

---

### Homey Pro ✅

**Status:** Vollständig unterstützt

**Features:**
- ✅ Alle Devices (via Capabilities)
- ✅ Zones (Räume)
- ✅ Flows triggern
- ✅ Cloud API & Lokale API
- ✅ Apps-Integration

**Setup:** Siehe [HOMEY_SETUP.md](HOMEY_SETUP.md)

**Vorteile:**
- Einfache Einrichtung
- Native Zigbee/Z-Wave
- Schöne UI
- Advanced Flows
- Lokale Steuerung

---

## Vergleich

| Feature | Home Assistant | Homey Pro |
|---------|---------------|-----------|
| **Device-Steuerung** | ✅ | ✅ |
| **Sensoren** | ✅ | ✅ |
| **Historische Daten** | ✅ Vollständig | ⚠️ Eingeschränkt |
| **Automationen** | ✅ Automations | ✅ Flows |
| **Scenes** | ✅ | ⚠️ Via Flows |
| **Räume/Zonen** | ⚠️ Areas | ✅ Native Zones |
| **Lokal** | ✅ | ✅ |
| **Cloud** | Optional | ✅ |
| **Open Source** | ✅ | ❌ |
| **Kosten** | Kostenlos | Hardware-Kauf |
| **Setup-Schwierigkeit** | Mittel | Einfach |

## In Planung

### MQTT (Standalone) 🔄

**Status:** Geplant für v2.0

Direkter MQTT-Support ohne Home Assistant/Homey:
- Direkte Device-Steuerung via MQTT
- Für DIY-Projekte
- Custom Hardware
- Tasmota, ESPHome, Shelly

### OpenHAB 🔄

**Status:** Geplant

Ähnlich wie Home Assistant, aber Java-basiert.

### ioBroker 🔄

**Status:** Geplant

Beliebte Plattform in Deutschland.

### SmartThings 🔄

**Status:** Unter Evaluation

Samsung SmartThings Support.

## Welche Plattform ist die richtige für mich?

### Wähle Home Assistant wenn:

- ✅ Du maximale Flexibilität willst
- ✅ Du gerne bastelst und customized
- ✅ Du viele verschiedene Integrationen brauchst
- ✅ Du Open Source bevorzugst
- ✅ Du bereits einen Server/Raspberry Pi hast
- ✅ Du technisch versiert bist

### Wähle Homey Pro wenn:

- ✅ Du einfache Einrichtung willst
- ✅ Du "out of the box" Lösung bevorzugst
- ✅ Du native Zigbee/Z-Wave ohne USB-Stick willst
- ✅ Du eine schöne App-Erfahrung willst
- ✅ Du Advanced Flows nutzen willst
- ✅ Du lokale Steuerung ohne Basteln willst

## Platform-Switch

Du kannst jederzeit zwischen Plattformen wechseln:

```bash
# In .env ändern
PLATFORM_TYPE=homeassistant  # oder "homey"

# System neu starten
sudo systemctl restart ki-system
```

Die ML-Modelle und historischen Daten bleiben erhalten!

## Community

### Home Assistant
- Forum: [https://community.home-assistant.io/](https://community.home-assistant.io/)
- Discord: [https://discord.gg/home-assistant](https://discord.gg/home-assistant)
- Reddit: [r/homeassistant](https://reddit.com/r/homeassistant)

### Homey
- Community: [https://community.homey.app/](https://community.homey.app/)
- Facebook: Homey Users Group
- Discord: Homey Community

## Contributions

Du nutzt eine andere Plattform und möchtest sie unterstützen?

1. Erstelle einen Collector der `SmartHomeCollector` implementiert
2. Füge ihn zur `PlatformFactory` hinzu
3. Erstelle einen Pull Request

Siehe [src/data_collector/base_collector.py](src/data_collector/base_collector.py) für das Interface.

## Support Matrix

| Feature | Home Assistant | Homey Pro | MQTT (geplant) |
|---------|---------------|-----------|----------------|
| Licht steuern | ✅ | ✅ | 🔄 |
| Temperatur | ✅ | ✅ | 🔄 |
| Sensoren | ✅ | ✅ | 🔄 |
| Historie | ✅ | ⚠️ | ❌ |
| Scenes | ✅ | ⚠️ | 🔄 |
| Räume | ⚠️ | ✅ | 🔄 |
| Flows/Auto | ✅ | ✅ | ❌ |
| Benachrichtigungen | ✅ | ✅ | ❌ |

Legend:
- ✅ Vollständig unterstützt
- ⚠️ Teilweise unterstützt
- 🔄 In Arbeit
- ❌ Nicht verfügbar
