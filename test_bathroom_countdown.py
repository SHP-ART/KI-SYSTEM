#!/usr/bin/env python3
"""Test des Countdown-Timers für Luftentfeuchter"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.utils.config_loader import ConfigLoader
from src.data_collector.platform_factory import PlatformFactory
from src.decision_engine.bathroom_automation import BathroomAutomation
from datetime import datetime

def main():
    print("=== Bathroom Countdown Timer Test ===\n")
    
    # Lade Config
    config = ConfigLoader()
    bathroom_config = config.get_bathroom_config()
    
    print(f"Config geladen:")
    print(f"  Enabled: {bathroom_config.get('enabled')}")
    print(f"  Humidity High: {bathroom_config.get('humidity_threshold_high')}%")
    print(f"  Humidity Low: {bathroom_config.get('humidity_threshold_low')}%")
    print(f"  Delay: {bathroom_config.get('dehumidifier_delay')} min\n")
    
    # Erstelle Platform
    platform = PlatformFactory.create_platform(config)
    
    # Erstelle Automation
    automation = BathroomAutomation(bathroom_config, enable_learning=False)
    
    # Hole aktuellen Status
    status = automation.get_status(platform)
    
    print(f"Aktueller Status:")
    print(f"  Humidity: {status['current_humidity']}%")
    print(f"  Temperature: {status['current_temperature']}°C")
    print(f"  Dehumidifier Running: {status['dehumidifier_running']}")
    print(f"  Humidity Below Threshold Since: {automation.humidity_below_threshold_since}")
    print(f"  Shutdown in: {status.get('dehumidifier_shutdown_in_seconds', 'N/A')} seconds\n")
    
    # Simuliere mehrere Zyklen
    print("Simuliere 3 Automation-Zyklen...\n")
    for i in range(3):
        print(f"--- Zyklus {i+1} ---")
        
        current_state = {
            'humidity': status['current_humidity'],
            'temperature': status['current_temperature']
        }
        
        actions = automation.process(platform, current_state)
        
        print(f"  Actions generiert: {len(actions) if actions else 0}")
        if actions:
            for action in actions:
                print(f"    - {action['action']} on {action['device_id']}: {action['reason']}")
        
        print(f"  Humidity Below Threshold Since: {automation.humidity_below_threshold_since}")
        
        # Hole Status nach Verarbeitung
        status = automation.get_status(platform)
        print(f"  Shutdown in: {status.get('dehumidifier_shutdown_in_seconds', 'N/A')} seconds\n")

if __name__ == '__main__':
    main()
