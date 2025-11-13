#!/usr/bin/env python3
"""
Test: Prüfe ob Countdown über API-Calls persistent bleibt
Simuliert einen laufenden Countdown und prüft mehrfache API-Calls
"""

import sys
import time
from pathlib import Path
import requests

sys.path.insert(0, str(Path(__file__).parent))

def test_countdown_persistence():
    print("=== Testing Countdown Persistence ===\n")
    
    # Simuliere mehrere API-Calls (wie beim Neuladen der Webseite)
    for i in range(5):
        print(f"API Call {i+1}:")
        
        response = requests.get('http://localhost:8080/api/luftentfeuchten/status')
        data = response.json()
        
        status = data['status']
        print(f"  Humidity: {status['current_humidity']}%")
        print(f"  Dehumidifier: {status['dehumidifier_running']}")
        
        shutdown = status.get('dehumidifier_shutdown_in_seconds')
        if shutdown:
            minutes = shutdown // 60
            seconds = shutdown % 60
            print(f"  Shutdown in: {minutes}:{seconds:02d} ({shutdown} seconds)")
        else:
            print(f"  Shutdown in: N/A")
        
        print()
        
        # Warte 2 Sekunden zwischen Calls
        if i < 4:
            time.sleep(2)
    
    print("\n✅ Wenn der Countdown bei jedem Call vorhanden ist und runterzählt,")
    print("   dann ist die Persistenz korrekt!")
    print("❌ Wenn der Countdown fehlt oder immer bei 5:00 startet,")
    print("   dann gibt es ein Problem mit dem State-Sharing.")

if __name__ == '__main__':
    test_countdown_persistence()
