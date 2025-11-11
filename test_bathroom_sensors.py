#!/usr/bin/env python3
"""
Test-Script für Badezimmer-Sensoren
Überprüft, ob die konfigurierten Sensoren erreichbar sind und Daten liefern
"""

import sys
from pathlib import Path
import json
from loguru import logger

# Füge src zum Path hinzu
sys.path.insert(0, str(Path(__file__).parent))

from src.decision_engine.engine import DecisionEngine


def test_bathroom_sensors():
    """Testet die Badezimmer-Sensoren"""

    print("=" * 60)
    print("BADEZIMMER-SENSOR TEST")
    print("=" * 60)

    # Lade Konfiguration
    config_file = Path('data/luftentfeuchten_config.json')
    if not config_file.exists():
        print("❌ Konfigurationsdatei nicht gefunden!")
        return False

    with open(config_file, 'r') as f:
        config = json.load(f)

    print(f"\n📋 Konfiguration:")
    print(f"   Aktiviert: {config.get('enabled', False)}")
    print(f"   Luftfeuchtigkeit-Sensor: {config.get('humidity_sensor_id', 'nicht konfiguriert')}")
    print(f"   Temperatur-Sensor: {config.get('temperature_sensor_id', 'nicht konfiguriert')}")
    print(f"   Luftentfeuchter: {config.get('dehumidifier_id', 'nicht konfiguriert')}")
    print(f"   Bewegungssensor: {config.get('motion_sensor_id', 'nicht konfiguriert')}")
    print(f"   Türsensor: {config.get('door_sensor_id', 'nicht konfiguriert')}")

    if not config.get('enabled', False):
        print("\n⚠️  Warnung: Badezimmer-Automation ist deaktiviert!")
        print("   Bitte setze 'enabled' auf 'true' in der Konfigurationsdatei.")
        return False

    # Initialisiere Decision Engine
    print("\n🔧 Initialisiere Decision Engine...")
    try:
        engine = DecisionEngine()
        print("✅ Decision Engine initialisiert")
    except Exception as e:
        print(f"❌ Fehler beim Initialisieren: {e}")
        return False

    # Teste Sensoren
    print("\n🔍 Teste Sensoren:")
    print("-" * 60)

    sensors_ok = True

    # Luftfeuchtigkeit
    humidity_id = config.get('humidity_sensor_id')
    if humidity_id:
        try:
            state = engine.platform.get_state(humidity_id)
            if state:
                caps = state.get('attributes', {}).get('capabilities', {})
                if 'measure_humidity' in caps:
                    humidity = caps['measure_humidity'].get('value')
                    print(f"✅ Luftfeuchtigkeit: {humidity}%")
                else:
                    print(f"❌ Luftfeuchtigkeit: Capability 'measure_humidity' nicht gefunden")
                    print(f"   Verfügbare Capabilities: {list(caps.keys())}")
                    sensors_ok = False
            else:
                print(f"❌ Luftfeuchtigkeit: Sensor liefert keinen Status")
                sensors_ok = False
        except Exception as e:
            print(f"❌ Luftfeuchtigkeit: Fehler beim Abrufen - {e}")
            sensors_ok = False
    else:
        print("⚠️  Luftfeuchtigkeit: Nicht konfiguriert")

    # Temperatur
    temp_id = config.get('temperature_sensor_id')
    if temp_id:
        try:
            state = engine.platform.get_state(temp_id)
            if state:
                caps = state.get('attributes', {}).get('capabilities', {})
                if 'measure_temperature' in caps:
                    temperature = caps['measure_temperature'].get('value')
                    print(f"✅ Temperatur: {temperature}°C")
                else:
                    print(f"❌ Temperatur: Capability 'measure_temperature' nicht gefunden")
                    print(f"   Verfügbare Capabilities: {list(caps.keys())}")
                    sensors_ok = False
            else:
                print(f"❌ Temperatur: Sensor liefert keinen Status")
                sensors_ok = False
        except Exception as e:
            print(f"❌ Temperatur: Fehler beim Abrufen - {e}")
            sensors_ok = False
    else:
        print("⚠️  Temperatur: Nicht konfiguriert")

    # Bewegungssensor
    motion_id = config.get('motion_sensor_id')
    if motion_id:
        try:
            state = engine.platform.get_state(motion_id)
            if state:
                caps = state.get('attributes', {}).get('capabilities', {})
                if 'alarm_motion' in caps:
                    motion = caps['alarm_motion'].get('value', False)
                    print(f"✅ Bewegung: {'Ja' if motion else 'Nein'}")
                else:
                    print(f"❌ Bewegung: Capability 'alarm_motion' nicht gefunden")
                    print(f"   Verfügbare Capabilities: {list(caps.keys())}")
            else:
                print(f"⚠️  Bewegung: Sensor liefert keinen Status")
        except Exception as e:
            print(f"⚠️  Bewegung: Fehler beim Abrufen - {e}")
    else:
        print("⚠️  Bewegung: Nicht konfiguriert")

    # Türsensor
    door_id = config.get('door_sensor_id')
    if door_id:
        try:
            state = engine.platform.get_state(door_id)
            if state:
                caps = state.get('attributes', {}).get('capabilities', {})
                if 'alarm_contact' in caps:
                    is_open = caps['alarm_contact'].get('value', False)
                    print(f"✅ Tür: {'Offen' if is_open else 'Geschlossen'}")
                else:
                    print(f"❌ Tür: Capability 'alarm_contact' nicht gefunden")
                    print(f"   Verfügbare Capabilities: {list(caps.keys())}")
            else:
                print(f"⚠️  Tür: Sensor liefert keinen Status")
        except Exception as e:
            print(f"⚠️  Tür: Fehler beim Abrufen - {e}")
    else:
        print("⚠️  Tür: Nicht konfiguriert")

    print("-" * 60)

    # Zusammenfassung
    print("\n📊 Zusammenfassung:")
    if sensors_ok:
        print("✅ Alle kritischen Sensoren funktionieren!")
        print("   Die Badezimmer-Automation sollte jetzt funktionieren.")
        return True
    else:
        print("❌ Einige Sensoren funktionieren nicht korrekt")
        print("   Bitte überprüfe die Sensor-IDs in der Konfiguration")
        return False


if __name__ == '__main__':
    try:
        success = test_bathroom_sensors()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Test fehlgeschlagen: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
