"""
Schimmel-Prävention & Luftfeuchtigkeit-Management
Berechnet Taupunkt, erkennt Kondensationsrisiken und gibt Lüftungsempfehlungen
"""

import math
from typing import Dict, Optional, List
from datetime import datetime
from loguru import logger
from src.utils.database import Database


class MoldPreventionSystem:
    """
    Intelligentes Schimmel-Präventions-System

    Features:
    - Taupunkt-Berechnung nach Magnus-Formel
    - Kondensationsrisiko-Erkennung
    - Kritische Feuchtigkeitswerte
    - Automatische Warnungen
    """

    def __init__(self, db: Database = None):
        self.db = db or Database()

        # Schwellwerte für Warnungen
        self.CRITICAL_HUMIDITY = 75.0  # %RH - kritisch für Schimmel
        self.WARNING_HUMIDITY = 65.0   # %RH - Warnstufe
        self.CONDENSATION_MARGIN = 2.0  # °C Sicherheitsabstand zum Taupunkt

    def calculate_dewpoint(self, temperature: float, humidity: float) -> float:
        """
        Berechnet Taupunkt nach Magnus-Formel

        Args:
            temperature: Temperatur in °C
            humidity: Relative Luftfeuchtigkeit in %

        Returns:
            Taupunkt in °C
        """
        # Magnus-Formel Konstanten
        a = 17.27
        b = 237.7

        # Sättigungsdampfdruck
        alpha = ((a * temperature) / (b + temperature)) + math.log(humidity / 100.0)

        # Taupunkt
        dewpoint = (b * alpha) / (a - alpha)

        return round(dewpoint, 2)

    def calculate_absolute_humidity(self, temperature: float, rel_humidity: float) -> float:
        """
        Berechnet absolute Luftfeuchtigkeit in g/m³

        Args:
            temperature: Temperatur in °C
            rel_humidity: Relative Luftfeuchtigkeit in %

        Returns:
            Absolute Feuchtigkeit in g/m³
        """
        # Sättigungsdampfdruck nach Magnus
        sat_vapor_pressure = 6.112 * math.exp((17.62 * temperature) / (243.12 + temperature))

        # Aktueller Dampfdruck
        vapor_pressure = (rel_humidity / 100.0) * sat_vapor_pressure

        # Absolute Feuchtigkeit
        # Formel: AH = (2.16679 * vapor_pressure) / (273.15 + temperature)
        abs_humidity = (2.16679 * vapor_pressure) / (273.15 + temperature)

        return round(abs_humidity, 2)

    def check_condensation_risk(self, room_temp: float, humidity: float,
                                surface_temp: float = None) -> Dict:
        """
        Prüft Kondensationsrisiko an kalten Oberflächen

        Args:
            room_temp: Raumtemperatur in °C
            humidity: Relative Luftfeuchtigkeit in %
            surface_temp: Oberflächentemperatur (z.B. Fenster, Wand)
                         Falls None, wird geschätzt (Außenwand ca. 5°C kälter)

        Returns:
            Dict mit Risikobewertung
        """
        dewpoint = self.calculate_dewpoint(room_temp, humidity)

        # Wenn keine Oberflächentemperatur gegeben, schätze sie
        if surface_temp is None:
            # Annahme: Außenwände sind ca. 5°C kälter als Raumtemperatur
            surface_temp = room_temp - 5.0

        # Risiko-Berechnung
        temp_diff = surface_temp - dewpoint

        if temp_diff <= 0:
            risk_level = "KRITISCH"
            risk_score = 1.0
            message = "⚠️ AKUTE KONDENSATIONSGEFAHR! Wasser kann sich bilden."
        elif temp_diff <= self.CONDENSATION_MARGIN:
            risk_level = "HOCH"
            risk_score = 0.8
            message = "⚠️ Hohes Kondensationsrisiko! Dringend lüften empfohlen."
        elif temp_diff <= self.CONDENSATION_MARGIN * 2:
            risk_level = "MITTEL"
            risk_score = 0.5
            message = "⚡ Erhöhtes Risiko. Regelmäßiges Lüften empfohlen."
        else:
            risk_level = "NIEDRIG"
            risk_score = 0.2
            message = "✓ Kondensationsrisiko gering."

        return {
            'risk_level': risk_level,
            'risk_score': risk_score,
            'message': message,
            'dewpoint': dewpoint,
            'surface_temp': surface_temp,
            'temp_difference': round(temp_diff, 2),
            'condensation_possible': temp_diff <= 0
        }

    def analyze_room_humidity(self, room_name: str, temperature: float,
                             humidity: float, outdoor_temp: float = None) -> Dict:
        """
        Vollständige Analyse der Raumfeuchtigkeit

        Returns:
            Dict mit Analyse, Warnungen und Empfehlungen
        """
        dewpoint = self.calculate_dewpoint(temperature, humidity)
        abs_humidity = self.calculate_absolute_humidity(temperature, humidity)
        condensation_risk = self.check_condensation_risk(temperature, humidity)

        # Bewertung der Feuchtigkeit
        humidity_status = self._evaluate_humidity_level(humidity)

        # Empfehlungen generieren
        recommendations = self._generate_recommendations(
            temperature, humidity, dewpoint, condensation_risk, outdoor_temp
        )

        # Prüfe ob Warnung nötig ist
        if humidity >= self.CRITICAL_HUMIDITY or condensation_risk['risk_level'] in ['KRITISCH', 'HOCH']:
            severity = 'critical' if humidity >= self.CRITICAL_HUMIDITY else 'warning'

            # Speichere Warnung in DB
            self.db.add_humidity_alert(
                room_name=room_name,
                alert_type='high_humidity' if humidity >= self.CRITICAL_HUMIDITY else 'condensation_risk',
                humidity=humidity,
                temperature=temperature,
                dewpoint=dewpoint,
                condensation_risk=condensation_risk['condensation_possible'],
                severity=severity,
                recommendation='; '.join(recommendations)
            )

        return {
            'room_name': room_name,
            'timestamp': datetime.now().isoformat(),
            'temperature': temperature,
            'humidity': humidity,
            'dewpoint': dewpoint,
            'absolute_humidity': abs_humidity,
            'humidity_status': humidity_status,
            'condensation_risk': condensation_risk,
            'recommendations': recommendations,
            'alert_required': humidity >= self.WARNING_HUMIDITY or condensation_risk['risk_score'] >= 0.5
        }

    def _evaluate_humidity_level(self, humidity: float) -> Dict:
        """Bewertet Luftfeuchtigkeitswert"""
        if humidity >= self.CRITICAL_HUMIDITY:
            return {
                'level': 'KRITISCH',
                'icon': '🔴',
                'color': 'red',
                'message': 'Schimmelgefahr! Sofortiges Handeln erforderlich.'
            }
        elif humidity >= self.WARNING_HUMIDITY:
            return {
                'level': 'WARNUNG',
                'icon': '🟠',
                'color': 'orange',
                'message': 'Erhöhte Luftfeuchtigkeit. Lüften empfohlen.'
            }
        elif humidity >= 50:
            return {
                'level': 'OPTIMAL',
                'icon': '🟢',
                'color': 'green',
                'message': 'Luftfeuchtigkeit im optimalen Bereich (50-65%).'
            }
        elif humidity >= 30:
            return {
                'level': 'NIEDRIG',
                'icon': '🟡',
                'color': 'yellow',
                'message': 'Etwas niedrige Luftfeuchtigkeit. Luftbefeuchter erwägen.'
            }
        else:
            return {
                'level': 'ZU TROCKEN',
                'icon': '🔵',
                'color': 'blue',
                'message': 'Sehr trockene Luft. Luftbefeuchter empfohlen.'
            }

    def _generate_recommendations(self, temperature: float, humidity: float,
                                 dewpoint: float, condensation_risk: Dict,
                                 outdoor_temp: float = None) -> List[str]:
        """Generiert konkrete Handlungsempfehlungen"""
        recommendations = []

        # Kritische Feuchtigkeit
        if humidity >= self.CRITICAL_HUMIDITY:
            recommendations.append("⚠️ DRINGEND: Sofort für 10-15 Minuten stoßlüften!")
            recommendations.append("🌡️ Heizung aufdrehen um Feuchtigkeit zu reduzieren")
            recommendations.append("💨 Luftentfeuchter einschalten")

        # Kondensationsrisiko
        elif condensation_risk['risk_level'] in ['KRITISCH', 'HOCH']:
            recommendations.append(f"🪟 Fenster/Wände zeigen Kondensation (Taupunkt: {dewpoint}°C)")
            recommendations.append("💨 Regelmäßiges Stoßlüften (3-4x täglich je 5-10 Min)")
            recommendations.append("🌡️ Raumtemperatur leicht erhöhen")

        # Erhöhte Feuchtigkeit
        elif humidity >= self.WARNING_HUMIDITY:
            recommendations.append("🪟 Stoßlüften für 5-10 Minuten")
            recommendations.append("🔍 Feuchtigkeitsquellen prüfen (Wäsche, Pflanzen, Kochen)")

        # Optimaler Bereich
        elif 50 <= humidity < self.WARNING_HUMIDITY:
            recommendations.append("✓ Luftfeuchtigkeit optimal - weiter so!")

        # Zu trocken
        elif humidity < 30:
            recommendations.append("💧 Luft zu trocken - Luftbefeuchter oder Pflanzen aufstellen")
            recommendations.append("🚿 Nach dem Duschen Tür offen lassen")

        # Temperatur-spezifische Tipps
        if temperature < 18:
            recommendations.append("🌡️ Raumtemperatur zu niedrig - mindestens 18-20°C empfohlen")

        return recommendations

    def get_mold_risk_assessment(self, room_name: str, days_back: int = 7) -> Dict:
        """
        Bewertet Schimmelrisiko basierend auf historischen Daten

        Args:
            room_name: Name des Raums
            days_back: Wie viele Tage zurückblicken

        Returns:
            Risikobewertung mit Score und Empfehlungen
        """
        # Hole historische Warnungen
        alerts = self.db.get_active_humidity_alerts(room_name=room_name, hours_back=days_back * 24)

        critical_count = sum(1 for a in alerts if a['severity'] == 'critical')
        warning_count = sum(1 for a in alerts if a['severity'] == 'warning')

        # Berechne Risiko-Score (0-100)
        risk_score = min(100, (critical_count * 20) + (warning_count * 10))

        if risk_score >= 80:
            risk_level = "SEHR HOCH"
            icon = "🔴"
            action = "Professionelle Begutachtung empfohlen"
        elif risk_score >= 60:
            risk_level = "HOCH"
            icon = "🟠"
            action = "Dringend Maßnahmen ergreifen"
        elif risk_score >= 40:
            risk_level = "MITTEL"
            icon = "🟡"
            action = "Lüftungsverhalten verbessern"
        elif risk_score >= 20:
            risk_level = "NIEDRIG"
            icon = "🟢"
            action = "Aktuelle Maßnahmen beibehalten"
        else:
            risk_level = "SEHR NIEDRIG"
            icon = "✅"
            action = "Keine Maßnahmen erforderlich"

        return {
            'room_name': room_name,
            'risk_score': risk_score,
            'risk_level': risk_level,
            'icon': icon,
            'action': action,
            'critical_events': critical_count,
            'warning_events': warning_count,
            'total_alerts': len(alerts),
            'period_days': days_back
        }
