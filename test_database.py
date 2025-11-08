#!/usr/bin/env python3
"""Test-Script für Datenbank"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.database import Database

def test_database():
    """Testet alle Datenbank-Funktionen"""
    print("=== Database Test ===\n")

    # Test 1: Datenbank erstellen
    print("1. Creating database...")
    db = Database("data/test_ki_system.db")
    print("   ✓ Database created\n")

    # Test 2: Sensor-Daten einfügen
    print("2. Inserting sensor data...")
    db.insert_sensor_data(
        sensor_id="sensor.test_temp",
        sensor_type="temperature",
        value=21.5,
        unit="°C",
        metadata={"room": "living_room"}
    )
    print("   ✓ Sensor data inserted\n")

    # Test 3: Externe Daten einfügen
    print("3. Inserting external data...")
    db.insert_external_data(
        data_type="weather",
        data={"temperature": 15.0, "condition": "cloudy"}
    )
    print("   ✓ External data inserted\n")

    # Test 4: Entscheidung speichern
    print("4. Inserting decision...")
    decision_id = db.insert_decision(
        device_id="light.living_room",
        decision_type="lighting",
        action="turn_on",
        confidence=0.85,
        model_version="1.0.0"
    )
    print(f"   ✓ Decision inserted (ID: {decision_id})\n")

    # Test 5: Entscheidung updaten
    print("5. Updating decision result...")
    db.update_decision_result(decision_id, executed=True, result="success")
    print("   ✓ Decision updated\n")

    # Test 6: Daten abrufen
    print("6. Retrieving sensor data...")
    sensor_data = db.get_sensor_data(hours_back=1)
    print(f"   ✓ Found {len(sensor_data)} sensor records\n")

    # Test 7: Trainingsdaten abrufen
    print("7. Retrieving training data...")
    training_data = db.get_training_data(hours_back=1)
    print(f"   ✓ Found {len(training_data)} sensor types\n")

    # Test 8: Trainings-Historie speichern
    print("8. Inserting training history...")
    db.insert_training_history(
        model_name="lighting_model",
        model_type="random_forest",
        metrics={"accuracy": 0.92, "samples": 100},
        model_path="models/lighting_model.pkl"
    )
    print("   ✓ Training history inserted\n")

    # Test 9: Verbindung schließen
    print("9. Closing database connection...")
    db.close()
    print("   ✓ Connection closed\n")

    print("=== All tests passed! ✓ ===")
    return True

if __name__ == "__main__":
    try:
        test_database()
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
