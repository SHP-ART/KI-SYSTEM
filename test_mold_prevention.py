#!/usr/bin/env python3
"""
Test-Skript für Schimmelprävention-Integration
Simuliert verschiedene Szenarien
"""

from src.decision_engine.mold_prevention import MoldPreventionSystem
from src.utils.database import Database
from loguru import logger

def test_mold_risk_scenarios():
    """Testet verschiedene Schimmelrisiko-Szenarien"""
    
    db = Database()
    mold_system = MoldPreventionSystem(db=db)
    
    print("="*70)
    print("SCHIMMELPRÄVENTION - TEST SZENARIEN")
    print("="*70)
    print()
    
    # Szenario 1: Normale Bedingungen
    print("📊 Szenario 1: Normale Bedingungen")
    print("-" * 70)
    result = mold_system.analyze_room_humidity(
        room_name="Bad",
        temperature=22.0,
        humidity=55.0
    )
    print(f"Temperatur: {result['temperature']}°C")
    print(f"Luftfeuchtigkeit: {result['humidity']}%")
    print(f"Taupunkt: {result['dewpoint']:.1f}°C")
    print(f"Status: {result['humidity_status']['level']} {result['humidity_status']['icon']}")
    print(f"Kondensationsrisiko: {result['condensation_risk']['risk_level']}")
    print(f"Empfehlungen: {len(result['recommendations'])}")
    for rec in result['recommendations']:
        print(f"  - {rec}")
    print()
    
    # Szenario 2: Erhöhte Luftfeuchtigkeit
    print("📊 Szenario 2: Erhöhte Luftfeuchtigkeit")
    print("-" * 70)
    result = mold_system.analyze_room_humidity(
        room_name="Bad",
        temperature=22.0,
        humidity=68.0
    )
    print(f"Temperatur: {result['temperature']}°C")
    print(f"Luftfeuchtigkeit: {result['humidity']}%")
    print(f"Taupunkt: {result['dewpoint']:.1f}°C")
    print(f"Status: {result['humidity_status']['level']} {result['humidity_status']['icon']}")
    print(f"Kondensationsrisiko: {result['condensation_risk']['risk_level']}")
    print(f"Risiko-Score: {result['condensation_risk']['risk_score']:.2f}")
    print(f"Empfehlungen: {len(result['recommendations'])}")
    for rec in result['recommendations']:
        print(f"  - {rec}")
    print()
    
    # Szenario 3: Kritische Bedingungen (hohe Feuchtigkeit + niedrige Temp)
    print("📊 Szenario 3: Kritische Bedingungen")
    print("-" * 70)
    result = mold_system.analyze_room_humidity(
        room_name="Bad",
        temperature=18.0,
        humidity=75.0
    )
    print(f"Temperatur: {result['temperature']}°C")
    print(f"Luftfeuchtigkeit: {result['humidity']}%")
    print(f"Taupunkt: {result['dewpoint']:.1f}°C")
    print(f"Temp-Delta: {result['temperature'] - result['dewpoint']:.1f}°C")
    print(f"Status: {result['humidity_status']['level']} {result['humidity_status']['icon']}")
    print(f"Kondensationsrisiko: {result['condensation_risk']['risk_level']}")
    print(f"Risiko-Score: {result['condensation_risk']['risk_score']:.2f}")
    print(f"⚠️ LUFTENTFEUCHTER SOLLTE EINSCHALTEN!")
    print(f"Empfehlungen: {len(result['recommendations'])}")
    for rec in result['recommendations']:
        print(f"  - {rec}")
    print()
    
    # Szenario 4: Sehr kritisch (Kondensation möglich)
    print("📊 Szenario 4: Sehr kritische Bedingungen")
    print("-" * 70)
    result = mold_system.analyze_room_humidity(
        room_name="Bad",
        temperature=16.0,
        humidity=80.0
    )
    print(f"Temperatur: {result['temperature']}°C")
    print(f"Luftfeuchtigkeit: {result['humidity']}%")
    print(f"Taupunkt: {result['dewpoint']:.1f}°C")
    print(f"Temp-Delta: {result['temperature'] - result['dewpoint']:.1f}°C")
    print(f"Status: {result['humidity_status']['level']} {result['humidity_status']['icon']}")
    print(f"Kondensationsrisiko: {result['condensation_risk']['risk_level']}")
    print(f"Risiko-Score: {result['condensation_risk']['risk_score']:.2f}")
    print(f"Kondensation möglich: {result['condensation_risk']['condensation_possible']}")
    print(f"🚨 KRITISCH - LUFTENTFEUCHTER MUSS EINSCHALTEN!")
    print(f"Empfehlungen: {len(result['recommendations'])}")
    for rec in result['recommendations']:
        print(f"  - {rec}")
    print()
    
    print("="*70)
    print("TEST ABGESCHLOSSEN")
    print("="*70)
    print()
    print("Integration in BathroomAutomation:")
    print("- Luftentfeuchter schaltet bei KRITISCH/HOCH Risiko ein")
    print("- Luftentfeuchter läuft weiter bis Risiko auf MITTEL/NIEDRIG sinkt")
    print("- Automatische Überwachung im 60s Intervall")
    print()

if __name__ == '__main__':
    test_mold_risk_scenarios()
