"""
Debug Script: Prüfe ob BathroomDataCollector läuft und Automation initialisiert ist
"""

import sys
from pathlib import Path

# Füge src zum Python-Path hinzu
sys.path.insert(0, str(Path(__file__).parent))

from src.decision_engine.engine import DecisionEngine
from src.background.bathroom_data_collector import BathroomDataCollector

def main():
    print("=== Bathroom Data Collector Debug ===\n")
    
    # Initialisiere Engine
    print("1. Initializing DecisionEngine...")
    engine = DecisionEngine()
    print(f"   Engine initialized: {engine is not None}")
    print(f"   Platform available: {engine.platform is not None}\n")
    
    # Initialisiere Collector
    print("2. Initializing BathroomDataCollector...")
    collector = BathroomDataCollector(engine=engine, interval_seconds=60)
    print(f"   Collector initialized: {collector is not None}")
    print(f"   Config loaded: {collector.config is not None}")
    print(f"   Automation initialized: {collector.automation is not None}")
    
    if collector.config:
        print(f"   Config enabled: {collector.config.get('enabled', False)}")
        print(f"   Humidity sensor: {collector.config.get('humidity_sensor_id')}")
        print(f"   Temperature sensor: {collector.config.get('temperature_sensor_id')}")
        print(f"   Dehumidifier: {collector.config.get('dehumidifier_id')}")
    
    if collector.automation:
        print(f"\n3. Automation Status:")
        print(f"   Shower detected: {collector.automation.shower_detected}")
        print(f"   Dehumidifier running: {collector.automation.dehumidifier_running}")
        print(f"   Humidity high threshold: {collector.automation.humidity_high}%")
        print(f"   Humidity low threshold: {collector.automation.humidity_low}%")
    else:
        print("\n3. ❌ Automation NOT initialized!")
        print("   This is the problem - no automation running!")
    
    # Teste Datensammlung
    print("\n4. Testing data collection...")
    try:
        collector._collect_data()
        print("   ✅ Data collection successful")
    except Exception as e:
        print(f"   ❌ Data collection failed: {e}")
    
    # Prüfe Status
    status = collector.get_status()
    print(f"\n5. Collector Status:")
    print(f"   Running: {status['running']}")
    print(f"   Last collection: {status['last_collection']}")
    print(f"   Config loaded: {status['config_loaded']}")
    print(f"   Automation active: {status['automation_active']}")

if __name__ == "__main__":
    main()
