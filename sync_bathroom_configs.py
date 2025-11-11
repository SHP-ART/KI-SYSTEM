#!/usr/bin/env python3
"""
Synchronisiert bathroom_config.json und luftentfeuchten_config.json

Problem: Es gibt zwei Config-Dateien für die Badezimmer-Automation:
- bathroom_config.json (wird von bathroom_optimizer.py verwendet)
- luftentfeuchten_config.json (wird von Web-UI verwendet)

Dieses Script stellt sicher, dass beide identisch sind.
"""

import json
from pathlib import Path
import sys


def sync_configs():
    """Synchronisiert beide Config-Dateien"""

    bathroom_config = Path('data/bathroom_config.json')
    luftentfeuchten_config = Path('data/luftentfeuchten_config.json')

    print("=" * 70)
    print("BADEZIMMER CONFIG SYNC")
    print("=" * 70)
    print()

    # Prüfe ob beide existieren
    if not bathroom_config.exists():
        print(f"❌ {bathroom_config} existiert nicht!")
        return False

    if not luftentfeuchten_config.exists():
        print(f"❌ {luftentfeuchten_config} existiert nicht!")
        return False

    # Lade beide
    with open(bathroom_config, 'r') as f:
        bathroom_data = json.load(f)

    with open(luftentfeuchten_config, 'r') as f:
        luftentfeuchten_data = json.load(f)

    # Zeige Status
    print("📋 Aktuelle Config-Werte:")
    print("-" * 70)
    print(f"bathroom_config.json:")
    print(f"  enabled: {bathroom_data.get('enabled', 'NICHT GESETZT')}")
    print(f"  frost_protection_temperature: {bathroom_data.get('frost_protection_temperature', 'NICHT GESETZT')}")
    print()
    print(f"luftentfeuchten_config.json:")
    print(f"  enabled: {luftentfeuchten_data.get('enabled', 'NICHT GESETZT')}")
    print(f"  frost_protection_temperature: {luftentfeuchten_data.get('frost_protection_temperature', 'NICHT GESETZT')}")
    print()

    # Vergleiche
    if bathroom_data == luftentfeuchten_data:
        print("✅ Beide Config-Dateien sind identisch!")
        print()
        if bathroom_data.get('enabled'):
            print("✅ Automation ist AKTIVIERT")
        else:
            print("⚠️  Automation ist DEAKTIVIERT")
        return True
    else:
        print("⚠️  Config-Dateien sind UNTERSCHIEDLICH!")
        print()

        # Finde Unterschiede
        all_keys = set(bathroom_data.keys()) | set(luftentfeuchten_data.keys())
        differences = []

        for key in sorted(all_keys):
            val1 = bathroom_data.get(key)
            val2 = luftentfeuchten_data.get(key)
            if val1 != val2:
                differences.append(f"  {key}: {val1} != {val2}")

        if differences:
            print("Unterschiede:")
            for diff in differences:
                print(diff)
            print()

        # Frage welche als Master verwendet werden soll
        print("Welche Config soll als Master verwendet werden?")
        print("1. bathroom_config.json")
        print("2. luftentfeuchten_config.json")

        choice = input("\nEingabe (1 oder 2): ").strip()

        if choice == '1':
            master = bathroom_data
            target = luftentfeuchten_config
            print(f"\n✅ Kopiere bathroom_config.json → luftentfeuchten_config.json")
        elif choice == '2':
            master = luftentfeuchten_data
            target = bathroom_config
            print(f"\n✅ Kopiere luftentfeuchten_config.json → bathroom_config.json")
        else:
            print("\n❌ Ungültige Eingabe!")
            return False

        # Backup erstellen
        backup = Path(f"{target}.backup")
        with open(target, 'r') as f:
            backup_data = f.read()
        with open(backup, 'w') as f:
            f.write(backup_data)
        print(f"💾 Backup erstellt: {backup}")

        # Schreibe Master-Config
        with open(target, 'w') as f:
            json.dump(master, f, indent=2)

        print(f"✅ Config synchronisiert!")
        print()

        if master.get('enabled'):
            print("✅ Automation ist jetzt AKTIVIERT in beiden Dateien")
        else:
            print("⚠️  Automation ist DEAKTIVIERT in beiden Dateien")

        return True


if __name__ == '__main__':
    try:
        success = sync_configs()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Fehler: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
