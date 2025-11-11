#!/usr/bin/env python3
"""
Debug-Script: Zeigt den vollständigen State der Heizung
"""

import sys
from pathlib import Path
import json

sys.path.insert(0, str(Path(__file__).parent))

from src.decision_engine.engine import DecisionEngine


def debug_heater():
    print("=" * 70)
    print("HEIZUNGS-STATE DEBUG")
    print("=" * 70)
    print()

    # Initialisiere Engine
    engine = DecisionEngine()

    # Heater ID
    heater_id = "78aba55b-98ed-4838-bbff-47527a46d69b"

    print(f"Heater ID: {heater_id}")
    print()

    # Hole State
    state = engine.platform.get_state(heater_id)

    if not state:
        print("❌ Kein State gefunden!")
        return

    # Zeige vollständigen State
    print("📋 Vollständiger State:")
    print("-" * 70)
    print(json.dumps(state, indent=2, ensure_ascii=False))
    print("-" * 70)
    print()

    # Capabilities analysieren
    print("🔍 Capabilities Analyse:")
    print("-" * 70)

    # Prüfe verschiedene mögliche Strukturen
    caps_obj = state.get('capabilitiesObj', {})
    if caps_obj:
        print("✅ capabilitiesObj gefunden:")
        for cap_name, cap_data in caps_obj.items():
            if isinstance(cap_data, dict):
                value = cap_data.get('value', 'N/A')
                print(f"   - {cap_name}: {value}")
            else:
                print(f"   - {cap_name}: {cap_data}")
    else:
        print("❌ Keine capabilitiesObj")

    # Alternative: capabilities
    caps = state.get('capabilities', {})
    if caps:
        print("\n✅ capabilities gefunden:")
        for cap_name, cap_value in caps.items():
            print(f"   - {cap_name}: {cap_value}")
    else:
        print("❌ Keine capabilities")

    # Alternative: attributes
    attrs = state.get('attributes', {})
    if attrs:
        print("\n✅ attributes gefunden:")
        caps = attrs.get('capabilities', {})
        if caps:
            for cap_name, cap_data in caps.items():
                if isinstance(cap_data, dict):
                    value = cap_data.get('value', 'N/A')
                    print(f"   - {cap_name}: {value}")
                else:
                    print(f"   - {cap_name}: {cap_data}")

    print("-" * 70)
    print()

    # Zeige empfohlene Extraktion
    print("💡 Empfohlene Werte-Extraktion:")
    print("-" * 70)

    # Versuche verschiedene Wege
    target_temp = None
    current_temp = None

    # Weg 1: capabilitiesObj
    if caps_obj:
        target_temp = caps_obj.get('target_temperature', {}).get('value')
        current_temp = caps_obj.get('measure_temperature', {}).get('value')

    # Weg 2: attributes.capabilities
    if target_temp is None and attrs:
        caps = attrs.get('capabilities', {})
        if caps:
            target_temp_cap = caps.get('target_temperature', {})
            current_temp_cap = caps.get('measure_temperature', {})
            if isinstance(target_temp_cap, dict):
                target_temp = target_temp_cap.get('value')
            if isinstance(current_temp_cap, dict):
                current_temp = current_temp_cap.get('value')

    print(f"IST-Temperatur (measure_temperature): {current_temp}")
    print(f"SOLL-Temperatur (target_temperature): {target_temp}")
    print("-" * 70)


if __name__ == '__main__':
    try:
        debug_heater()
    except Exception as e:
        print(f"\n❌ Fehler: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
