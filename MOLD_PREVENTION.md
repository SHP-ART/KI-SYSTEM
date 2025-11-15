# Automatische Schimmelprävention

## Übersicht

Das System überwacht kontinuierlich die Raumfeuchtigkeit und erkennt automatisch Schimmelrisiken. Bei erhöhtem Risiko wird der Luftentfeuchter automatisch eingeschaltet.

## Funktionsweise

### 1. Risiko-Erkennung

Die Schimmelprävention berechnet mehrere Parameter:

- **Taupunkt**: Temperatur bei der Kondensation auftritt (Magnus-Formel)
- **Absolute Luftfeuchtigkeit**: Wasserdampfgehalt in g/m³
- **Kondensationsrisiko**: Wahrscheinlichkeit von Schimmelbildung

### 2. Risiko-Stufen

| Stufe | Beschreibung | Luftentfeuchter |
|-------|--------------|-----------------|
| **NIEDRIG** | Optimal (< 65% Luftfeuchtigkeit) | Aus |
| **MITTEL** | Erhöht (65-70%) | Aus |
| **HOCH** | Warnung (70-75%) | **Einschalten** |
| **KRITISCH** | Gefahr (> 75%) | **Einschalten** |

### 3. Automatische Steuerung

**Einschalt-Bedingungen:**
- Luftfeuchtigkeit > 70% (Standard-Schwellwert)
- **ODER** Dusche erkannt
- **ODER** Schimmelrisiko HOCH/KRITISCH

**Ausschalt-Bedingungen:**
- Luftfeuchtigkeit < 60% (Standard-Schwellwert)
- **UND** Schimmelrisiko nicht mehr HOCH/KRITISCH
- **UND** 5 Minuten Verzögerung abgelaufen

## Beispiel-Szenarien

### Szenario 1: Normale Bedingungen ✅
```
Temperatur: 22°C
Luftfeuchtigkeit: 55%
Taupunkt: 12.5°C
→ Risiko: NIEDRIG
→ Aktion: Keine
```

### Szenario 2: Erhöhte Feuchtigkeit ⚠️
```
Temperatur: 22°C
Luftfeuchtigkeit: 68%
Taupunkt: 15.8°C
→ Risiko: HOCH
→ Aktion: Luftentfeuchter EIN
→ Grund: "Mold risk detected: HOCH"
```

### Szenario 3: Kritische Bedingungen 🚨
```
Temperatur: 18°C
Luftfeuchtigkeit: 75%
Taupunkt: 13.5°C
→ Risiko: KRITISCH
→ Aktion: Luftentfeuchter EIN (sofort)
→ Grund: "Mold risk detected: KRITISCH"
```

### Szenario 4: Kondensationsgefahr 🚨🚨
```
Temperatur: 16°C
Luftfeuchtigkeit: 80%
Taupunkt: 12.6°C
Temp-Delta: 3.4°C (sehr gering!)
→ Risiko: KRITISCH + Kondensation möglich
→ Aktion: Luftentfeuchter EIN + Heizung hoch
→ Grund: "Mold risk detected: KRITISCH"
```

## Konfiguration

In `data/luftentfeuchten_config.json`:

```json
{
  "room_name": "Bad",
  "humidity_threshold_high": 70,
  "humidity_threshold_low": 60,
  "dehumidifier_delay": 5
}
```

### Parameter

- `room_name`: Name des Raums für Logging und Tracking
- `humidity_threshold_high`: Obergrenze für Luftfeuchtigkeit (%)
- `humidity_threshold_low`: Untergrenze für Ausschalten (%)
- `dehumidifier_delay`: Verzögerung vor Ausschalten (Minuten)

## Integration

### BathroomAutomation

```python
# Initialisierung
self.mold_prevention = MoldPreventionSystem(db=self.db)

# In _control_dehumidifier()
analysis = self.mold_prevention.analyze_room_humidity(
    room_name=room_name,
    temperature=temperature,
    humidity=humidity
)

risk_level = analysis['condensation_risk']['risk_level']
if risk_level in ['KRITISCH', 'HOCH']:
    # Luftentfeuchter einschalten
    mold_risk_detected = True
```

### Logging

Das System protokolliert alle Aktionen:

```
⚠️ Mold risk detected: HOCH (humidity: 68%, dewpoint: 15.8°C)
💨 Turning ON dehumidifier (humidity: 68%)
🛡️ Keeping dehumidifier running due to KRITISCH mold risk
```

## API-Endpoints

### Humidity Alerts
```bash
GET /api/humidity/alerts
```

Gibt aktuelle Schimmelrisiko-Warnungen zurück:
```json
{
  "alerts": [
    {
      "room_name": "Bad",
      "alert_type": "high_humidity",
      "humidity": 75.0,
      "temperature": 18.0,
      "dewpoint": 13.5,
      "severity": "critical",
      "timestamp": "2025-01-15T08:48:43"
    }
  ],
  "count": 1,
  "success": true
}
```

## Testing

Test-Skript ausführen:
```bash
python3 test_mold_prevention.py
```

Output zeigt alle 4 Szenarien mit Risiko-Bewertung und Empfehlungen.

## Vorteile

1. **Proaktiv**: Erkennt Risiken bevor Schimmel entsteht
2. **Automatisch**: Keine manuelle Steuerung nötig
3. **Intelligent**: Berücksichtigt Temperatur und Taupunkt
4. **Energieeffizient**: Läuft nur bei tatsächlichem Bedarf
5. **Transparent**: Alle Aktionen werden geloggt und protokolliert

## Zusammenarbeit mit anderen Features

Die Schimmelprävention arbeitet zusammen mit:

- **Duscherkennung**: Beide können Luftentfeuchter aktivieren
- **Fenstererkennung**: Bei offenem Fenster wird nicht entfeuchtet
- **Heizungssteuerung**: Bei niedrigen Temperaturen wird geheizt
- **Ventilation Optimizer**: Empfiehlt optimale Lüftungszeiten

## Nächste Schritte

Mögliche Erweiterungen:

1. Push-Benachrichtigungen bei kritischem Risiko
2. Historische Trend-Analyse
3. Raumübergreifende Koordination
4. Wettervorhersage-Integration
5. Adaptive Schwellwerte basierend auf Jahreszeit
