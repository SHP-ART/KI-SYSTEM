"""
Debug Script: Simuliere hohe Luftfeuchtigkeit und teste ob Automation läuft
"""

import sys
from pathlib import Path
from datetime import datetime

# Füge src zum Python-Path hinzu
sys.path.insert(0, str(Path(__file__).parent))

from src.decision_engine.bathroom_automation import BathroomAutomation
from src.decision_engine.engine import DecisionEngine
import json

def main():
    print("=== Bathroom Automation Simulation ===\n")
    
    # Lade Config
    with open('data/luftentfeuchten_config.json', 'r') as f:
        config = json.load(f)
    
    print(f"Config loaded: {config.get('enabled')}")
    print(f"Humidity threshold high: {config.get('humidity_threshold_high')}%")
    print(f"Humidity threshold low: {config.get('humidity_threshold_low')}%\n")
    
    # Initialisiere Automation
    automation = BathroomAutomation(config, enable_learning=False)
    
    # Initialisiere Platform
    engine = DecisionEngine()
    platform = engine.platform
    
    print("=== Test 1: Normal humidity (65%) ===")
    current_state = {
        'humidity': 65.0,
        'temperature': 21.5,
        'motion_detected': False,
        'door_closed': True,
        'window_open': False
    }
    actions = automation.process(platform, current_state)
    print(f"Actions: {len(actions)}")
    for action in actions:
        print(f"  - {action}")
    print()
    
    print("=== Test 2: High humidity (75%) ===")
    current_state = {
        'humidity': 75.0,
        'temperature': 21.5,
        'motion_detected': True,
        'door_closed': True,
        'window_open': False
    }
    actions = automation.process(platform, current_state)
    print(f"Actions: {len(actions)}")
    for action in actions:
        print(f"  - {action}")
    print()
    
    print("=== Test 3: Very high humidity (80%) ===")
    current_state = {
        'humidity': 80.0,
        'temperature': 21.5,
        'motion_detected': True,
        'door_closed': True,
        'window_open': False
    }
    actions = automation.process(platform, current_state)
    print(f"Actions: {len(actions)}")
    for action in actions:
        print(f"  - {action}")
    print()
    
    print("=== Test 4: Humidity drops back to 58% ===")
    current_state = {
        'humidity': 58.0,
        'temperature': 21.5,
        'motion_detected': False,
        'door_closed': True,
        'window_open': False
    }
    actions = automation.process(platform, current_state)
    print(f"Actions: {len(actions)}")
    for action in actions:
        print(f"  - {action}")
    print()

if __name__ == "__main__":
    main()
