"""
Intelligente Lüftungssteuerung
Berechnet optimale Lüftungszeiten basierend auf Innen- und Außenklima
"""

from typing import Dict, Optional, List
from datetime import datetime, timedelta
from loguru import logger
from src.utils.database import Database
from src.decision_engine.mold_prevention import MoldPreventionSystem


class VentilationOptimizer:
    """
    Optimiert Lüftungsstrategien für verschiedene Räume

    Features:
    - Berechnung ob Außenluft Feuchtigkeit reduzieren kann
    - Erkennung von Stoßlüftung (offenes Fenster)
    - Optimale Lüftungsdauer
    - Koordination mit Luftentfeuchtern
    """

    def __init__(self, db: Database = None):
        self.db = db or Database()
        self.mold_prevention = MoldPreventionSystem(db=self.db)

    def is_outdoor_air_beneficial(self, indoor_temp: float, indoor_humidity: float,
                                  outdoor_temp: float, outdoor_humidity: float) -> Dict:
        """
        Prüft ob Außenluft hilft Feuchtigkeit zu reduzieren

        Die Entscheidung basiert auf absoluter Feuchtigkeit,
        nicht relativer (% Luftfeuchtigkeit ist temperaturabhängig!)

        Args:
            indoor_temp: Innentemperatur °C
            indoor_humidity: Innen-Luftfeuchtigkeit %
            outdoor_temp: Außentemperatur °C
            outdoor_humidity: Außen-Luftfeuchtigkeit %

        Returns:
            Dict mit Empfehlung und Details
        """
        # Berechne absolute Feuchtigkeit (g/m³)
        indoor_abs_hum = self.mold_prevention.calculate_absolute_humidity(indoor_temp, indoor_humidity)
        outdoor_abs_hum = self.mold_prevention.calculate_absolute_humidity(outdoor_temp, outdoor_humidity)

        # Differenz berechnen
        abs_diff = indoor_abs_hum - outdoor_abs_hum

        # Bewertung
        if abs_diff <= 0:
            is_beneficial = False
            reason = "Außenluft ist feuchter als Innenluft - NICHT lüften!"
            icon = "❌"
            recommended_duration = 0
        elif abs_diff < 2.0:
            is_beneficial = False
            reason = "Zu geringer Unterschied - Lüften bringt wenig"
            icon = "⚠️"
            recommended_duration = 0
        elif abs_diff < 4.0:
            is_beneficial = True
            reason = "Leichter Vorteil - kurz lüften möglich"
            icon = "🟡"
            recommended_duration = 3  # Minuten
        elif abs_diff < 6.0:
            is_beneficial = True
            reason = "Gute Bedingungen - lüften empfohlen"
            icon = "🟢"
            recommended_duration = 5
        else:
            is_beneficial = True
            reason = "Optimale Bedingungen - jetzt lüften!"
            icon = "✅"
            recommended_duration = 10

        # Zusätzliche Bedingungen prüfen
        warnings = []

        # Warnung bei extremer Kälte
        if outdoor_temp < 0 and is_beneficial:
            warnings.append("⚠️ Sehr kalt draußen - nur kurz lüften (max 3 Min)")
            recommended_duration = min(3, recommended_duration)

        # Warnung bei hoher Außenfeuchtigkeit
        if outdoor_humidity > 80:
            warnings.append("💧 Sehr hohe Außenfeuchtigkeit - besser warten")
            is_beneficial = False

        return {
            'is_beneficial': is_beneficial,
            'icon': icon,
            'reason': reason,
            'indoor_abs_humidity': round(indoor_abs_hum, 2),
            'outdoor_abs_humidity': round(outdoor_abs_hum, 2),
            'abs_humidity_diff': round(abs_diff, 2),
            'recommended_duration_minutes': recommended_duration,
            'warnings': warnings,
            'outdoor_temp': outdoor_temp,
            'outdoor_humidity': outdoor_humidity
        }

    def detect_airing(self, room_name: str, temperature_drop: float,
                     humidity_drop: float, time_window_minutes: int = 10) -> Dict:
        """
        Erkennt Stoßlüftung anhand von Temperatur- und Feuchtigkeitsabfall

        Args:
            room_name: Raumname
            temperature_drop: Temperaturabfall in °C
            humidity_drop: Feuchtigkeitsabfall in %
            time_window_minutes: Zeitfenster für Erkennung

        Returns:
            Dict mit Erkennungsergebnis
        """
        # Schwellwerte für Stoßlüftungs-Erkennung
        MIN_TEMP_DROP = 1.5  # °C
        MIN_HUMIDITY_DROP = 5.0  # %

        is_airing = (abs(temperature_drop) >= MIN_TEMP_DROP or
                    abs(humidity_drop) >= MIN_HUMIDITY_DROP)

        if is_airing:
            # Schätze Lüftungsdauer anhand der Änderungsrate
            if abs(temperature_drop) >= 3.0:
                estimated_duration = "Lang (>10 Min)"
                quality = "Sehr gut"
            elif abs(temperature_drop) >= MIN_TEMP_DROP:
                estimated_duration = "Mittel (5-10 Min)"
                quality = "Gut"
            else:
                estimated_duration = "Kurz (<5 Min)"
                quality = "Ausreichend"

            return {
                'is_airing': True,
                'detected_at': datetime.now().isoformat(),
                'temperature_drop': round(temperature_drop, 2),
                'humidity_drop': round(humidity_drop, 2),
                'estimated_duration': estimated_duration,
                'quality': quality,
                'message': f"✅ Stoßlüftung erkannt ({quality})"
            }
        else:
            return {
                'is_airing': False,
                'temperature_drop': round(temperature_drop, 2),
                'humidity_drop': round(humidity_drop, 2),
                'message': "Keine Lüftung erkannt"
            }

    def generate_ventilation_recommendation(self, room_name: str,
                                           indoor_temp: float, indoor_humidity: float,
                                           outdoor_temp: float, outdoor_humidity: float) -> Dict:
        """
        Generiert umfassende Lüftungsempfehlung für einen Raum

        Returns:
            Dict mit Empfehlung, Timing und Dauer
        """
        # Prüfe ob Lüften sinnvoll ist
        outdoor_analysis = self.is_outdoor_air_beneficial(
            indoor_temp, indoor_humidity,
            outdoor_temp, outdoor_humidity
        )

        # Prüfe Schimmelrisiko
        mold_analysis = self.mold_prevention.analyze_room_humidity(
            room_name, indoor_temp, indoor_humidity, outdoor_temp
        )

        # Generiere Empfehlung
        if outdoor_analysis['is_beneficial']:
            if mold_analysis['alert_required']:
                priority = "HOCH"
                action = f"🚨 JETZT LÜFTEN! {outdoor_analysis['recommended_duration_minutes']} Minuten"
                reason = "Hohe Luftfeuchtigkeit + gute Außenbedingungen"
            else:
                priority = "MITTEL"
                action = f"🪟 Lüften empfohlen ({outdoor_analysis['recommended_duration_minutes']} Min)"
                reason = "Gute Bedingungen zum Lüften"
        else:
            if mold_analysis['alert_required']:
                priority = "HOCH"
                action = "💨 Luftentfeuchter einschalten (Außenluft zu feucht)"
                reason = "Hohe Innen-Feuchtigkeit aber Außenluft hilft nicht"
            else:
                priority = "NIEDRIG"
                action = "✓ Aktuell nicht lüften (Außenluft ungeeignet)"
                reason = outdoor_analysis['reason']

        # Berechne nächste optimale Lüftungszeit (vereinfacht)
        next_optimal_time = self._calculate_next_optimal_time(outdoor_analysis)

        recommendation_text = self._build_recommendation_text(
            outdoor_analysis, mold_analysis, priority, action
        )

        # Speichere in Datenbank
        self.db.add_ventilation_recommendation(
            room_name=room_name,
            indoor_temp=indoor_temp,
            indoor_humidity=indoor_humidity,
            outdoor_temp=outdoor_temp,
            outdoor_humidity=outdoor_humidity,
            is_beneficial=outdoor_analysis['is_beneficial'],
            abs_humidity_diff=outdoor_analysis['abs_humidity_diff'],
            duration_minutes=outdoor_analysis['recommended_duration_minutes'],
            recommendation=recommendation_text
        )

        return {
            'room_name': room_name,
            'timestamp': datetime.now().isoformat(),
            'priority': priority,
            'action': action,
            'reason': reason,
            'outdoor_analysis': outdoor_analysis,
            'mold_risk': mold_analysis.get('humidity_status'),
            'recommended_duration': outdoor_analysis['recommended_duration_minutes'],
            'next_optimal_time': next_optimal_time,
            'full_recommendation': recommendation_text
        }

    def _calculate_next_optimal_time(self, outdoor_analysis: Dict) -> Optional[str]:
        """Berechnet die nächste optimale Lüftungszeit (vereinfacht)"""
        if outdoor_analysis['is_beneficial']:
            return "Jetzt"

        # Wenn aktuell nicht optimal, empfehle Standard-Zeiten
        current_hour = datetime.now().hour

        # Typische gute Zeiten: morgens 7-9 Uhr, mittags 13-14 Uhr, abends 19-20 Uhr
        good_hours = [7, 8, 13, 19]

        # Finde nächste gute Zeit
        for hour in good_hours:
            if hour > current_hour:
                return f"Heute um {hour:02d}:00 Uhr"

        # Sonst morgen früh
        return f"Morgen um {good_hours[0]:02d}:00 Uhr"

    def _build_recommendation_text(self, outdoor_analysis: Dict,
                                   mold_analysis: Dict, priority: str, action: str) -> str:
        """Baut detaillierten Empfehlungstext"""
        parts = []

        parts.append(f"**{action}**")
        parts.append(f"\nPriorität: {priority}")

        if outdoor_analysis['is_beneficial']:
            parts.append(f"\n✓ Außenluft ist trockener ({outdoor_analysis['outdoor_abs_humidity']} g/m³ vs. {outdoor_analysis['indoor_abs_humidity']} g/m³)")
            parts.append(f"→ Empfohlene Dauer: {outdoor_analysis['recommended_duration_minutes']} Minuten")
        else:
            parts.append(f"\n✗ {outdoor_analysis['reason']}")

        if outdoor_analysis['warnings']:
            parts.append("\n⚠️ Hinweise:")
            for warning in outdoor_analysis['warnings']:
                parts.append(f"  • {warning}")

        parts.append(f"\nLuftfeuchtigkeit Status: {mold_analysis['humidity_status']['icon']} {mold_analysis['humidity_status']['level']}")

        return "\n".join(parts)

    def should_stop_dehumidifier_for_airing(self, is_window_open: bool,
                                           outdoor_beneficial: bool) -> Dict:
        """
        Entscheidet ob Luftentfeuchter bei Lüftung ausgeschaltet werden soll

        Args:
            is_window_open: Fenster offen?
            outdoor_beneficial: Ist Außenluft trocken genug?

        Returns:
            Dict mit Entscheidung und Grund
        """
        if not is_window_open:
            return {
                'should_stop': False,
                'reason': "Fenster geschlossen - Luftentfeuchter kann laufen",
                'action': None
            }

        if outdoor_beneficial:
            return {
                'should_stop': True,
                'reason': "Fenster offen + trockene Außenluft - Luftentfeuchter nicht nötig",
                'action': "Luftentfeuchter ausschalten und Energie sparen"
            }
        else:
            return {
                'should_stop': True,
                'reason': "Fenster offen - Luftentfeuchter verschwendet Energie",
                'action': "Fenster schließen oder Luftentfeuchter ausschalten"
            }

    def get_daily_ventilation_schedule(self, room_name: str = None) -> List[Dict]:
        """
        Erstellt einen optimalen Tages-Lüftungsplan

        Returns:
            Liste von empfohlenen Lüftungszeiten
        """
        # Standardzeiten für Stoßlüftung
        schedule = [
            {
                'time': '07:00-07:10',
                'hour': 7,
                'reason': 'Morgenlüftung - Frische Luft für den Tag',
                'duration_minutes': 10,
                'priority': 'hoch'
            },
            {
                'time': '13:00-13:05',
                'hour': 13,
                'reason': 'Mittagslüftung - Temperaturhoch draußen',
                'duration_minutes': 5,
                'priority': 'mittel'
            },
            {
                'time': '19:00-19:10',
                'hour': 19,
                'reason': 'Abendlüftung - Feuchtigkeit vom Tag raus',
                'duration_minutes': 10,
                'priority': 'hoch'
            }
        ]

        logger.info(f"Generated daily ventilation schedule with {len(schedule)} time slots")
        return schedule
