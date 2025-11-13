"""
Debug: Teste ob BathroomDataCollector wirklich Aktionen ausführt
"""

import sys
from pathlib import Path
import time

# Füge src zum Python-Path hinzu
sys.path.insert(0, str(Path(__file__).parent))

from src.decision_engine.engine import DecisionEngine
from src.background.bathroom_data_collector import BathroomDataCollector

def main():
    print("=== Testing Bathroom Automation Action Execution ===\n")
    
    # Initialisiere Engine
    engine = DecisionEngine()
    print(f"Engine: {engine is not None}")
    print(f"Platform: {engine.platform is not None}")
    
    # Initialisiere Collector
    collector = BathroomDataCollector(engine=engine, interval_seconds=60)
    print(f"Collector initialized: {collector is not None}")
    print(f"Automation: {collector.automation is not None}")
    print(f"Config enabled: {collector.config.get('enabled') if collector.config else False}")
    
    # Prüfe ob engine in collector gesetzt ist
    print(f"\nCollector.engine: {collector.engine is not None}")
    print(f"Collector.engine.platform: {collector.engine.platform is not None if collector.engine else 'No engine'}")
    
    # Test mit hoher Luftfeuchtigkeit
    print("\n=== Simulating high humidity (75%) ===")
    print("This should trigger dehumidifier to turn on...")
    
    # Rufe _run_automation direkt auf
    collector._run_automation(humidity=75.0, temperature=21.5)
    
    print("\n=== Checking automation state ===")
    if collector.automation:
        print(f"Shower detected: {collector.automation.shower_detected}")
        print(f"Dehumidifier running: {collector.automation.dehumidifier_running}")
    
    # Warte und teste nochmal
    print("\n=== Simulating normal humidity (60%) ===")
    time.sleep(2)
    collector._run_automation(humidity=60.0, temperature=21.5)
    
    if collector.automation:
        print(f"Shower detected: {collector.automation.shower_detected}")
        print(f"Dehumidifier running: {collector.automation.dehumidifier_running}")

if __name__ == "__main__":
    main()
