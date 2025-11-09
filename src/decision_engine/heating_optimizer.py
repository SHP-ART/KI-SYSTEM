"""
Heizungs-Optimierung - Analyse & Lern-Modul
Analysiert Heizverhalten und generiert Optimierungsvorschläge
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from loguru import logger
from src.utils.database import Database
import statistics


class HeatingOptimizer:
    """
    Analysiert Heizungsdaten und generiert Optimierungsvorschläge

    Modi:
    - Regelungsmodus: System steuert direkt
    - Optimierungsmodus: Nur Datensammlung + Vorschläge

    Features:
    - Zeitliche Muster-Erkennung (wann wird geheizt)
    - Optimierung von Temperaturen
    - Energiespar-Potenzial erkennen
    - Fenster-offen Warnungen
    """

    def __init__(self, db: Database = None):
        self.db = db or Database()

        # Standard-Annahmen für Berechnungen
        self.heating_cost_per_degree_per_day = 0.50  # EUR pro Grad pro Tag (grobe Schätzung)
        self.avg_room_count = 4  # Durchschnittliche Anzahl Räume

    def collect_current_state(self, platform, outdoor_temp: float = None) -> Dict:
        """
        Sammelt aktuellen Heizungszustand von allen Thermostaten
        Speichert Daten für spätere Analyse

        Args:
            platform: SmartHomeCollector (Homey oder HA)
            outdoor_temp: Außentemperatur (optional)
        """
        # Hole alle Climate-Entities (Thermostate)
        climate_entities = platform.get_all_entities(domain='climate')

        observations = []

        for entity_id in climate_entities:
            try:
                state = platform.get_state(entity_id)
                if not state:
                    continue

                # Extrahiere Daten
                current_temp = state.get('attributes', {}).get('current_temperature')
                target_temp = state.get('attributes', {}).get('temperature')
                room_name = self._extract_room_name(state)

                # Prüfe ob gerade geheizt wird
                is_heating = self._is_heating(state, current_temp, target_temp)

                # Fenster-Status (wenn verfügbar)
                window_open = False  # TODO: Fenster-Erkennung implementieren

                # Anwesenheit (wenn verfügbar)
                presence = True  # Default: anwesend

                if current_temp and target_temp:
                    # Speichere in DB
                    self.db.add_heating_observation(
                        device_id=entity_id,
                        room_name=room_name,
                        current_temp=current_temp,
                        target_temp=target_temp,
                        outdoor_temp=outdoor_temp or 10.0,
                        is_heating=is_heating,
                        presence=presence,
                        window_open=window_open,
                        energy_level=2  # Default: mittel
                    )

                    observations.append({
                        'device_id': entity_id,
                        'room_name': room_name,
                        'current_temp': current_temp,
                        'target_temp': target_temp,
                        'is_heating': is_heating
                    })

            except Exception as e:
                logger.error(f"Error collecting state for {entity_id}: {e}")

        logger.info(f"Collected {len(observations)} heating observations")
        return {
            'timestamp': datetime.now().isoformat(),
            'observations_count': len(observations),
            'observations': observations
        }

    def _extract_room_name(self, state: Dict) -> str:
        """Extrahiert Raumnamen aus Device-State"""
        # Versuche verschiedene Quellen
        if 'attributes' in state:
            # Homey: zoneName
            if 'zoneName' in state['attributes']:
                return state['attributes']['zoneName']

            # Home Assistant: friendly_name
            if 'friendly_name' in state['attributes']:
                name = state['attributes']['friendly_name']
                # Extrahiere Raum aus Namen (z.B. "Wohnzimmer Thermostat" -> "Wohnzimmer")
                for keyword in ['Thermostat', 'Heizung', 'Climate']:
                    name = name.replace(keyword, '').strip()
                return name

        return "Unbekannt"

    def _is_heating(self, state: Dict, current_temp: float, target_temp: float) -> bool:
        """Prüft ob gerade geheizt wird"""
        # Methode 1: State-Attribut
        hvac_state = state.get('state')
        if hvac_state in ['heat', 'heating']:
            return True

        # Methode 2: Temperatur-Differenz
        if current_temp and target_temp:
            return target_temp > current_temp + 0.5  # 0.5°C Hysterese

        return False

    def analyze_patterns(self, days_back: int = 14) -> Dict:
        """
        Analysiert Heizmuster der letzten X Tage

        Returns:
            Dict mit Analyse-Ergebnissen
        """
        observations = self.db.get_heating_observations(days_back=days_back)

        if not observations or len(observations) < 50:
            logger.warning(f"Nicht genug Daten für Analyse: {len(observations) if observations else 0} Beobachtungen")
            return {
                'observations_count': len(observations) if observations else 0,
                'sufficient_data': False,
                'message': f'Mindestens 50 Beobachtungen benötigt (aktuell: {len(observations) if observations else 0})'
            }

        # Zeitliche Muster
        hourly_pattern = self._analyze_hourly_heating_pattern(observations)
        weekly_pattern = self._analyze_weekly_heating_pattern(observations)

        # Temperatur-Statistiken
        temp_stats = self._analyze_temperature_patterns(observations)

        # Ineffizienzen erkennen
        inefficiencies = self._detect_inefficiencies(observations)

        return {
            'observations_count': len(observations),
            'sufficient_data': True,
            'period_days': days_back,
            'hourly_pattern': hourly_pattern,
            'weekly_pattern': weekly_pattern,
            'temperature_stats': temp_stats,
            'inefficiencies': inefficiencies,
            'analyzed_at': datetime.now().isoformat()
        }

    def _analyze_hourly_heating_pattern(self, observations: List[Dict]) -> Dict:
        """Analysiert Heizmuster nach Tageszeit"""
        hourly_heating = {}
        hourly_total = {}

        for obs in observations:
            hour = obs.get('hour_of_day')
            if hour is not None:
                hourly_total[hour] = hourly_total.get(hour, 0) + 1
                if obs.get('is_heating'):
                    hourly_heating[hour] = hourly_heating.get(hour, 0) + 1

        # Berechne Heiz-Prozentsatz pro Stunde
        hourly_percentages = {}
        for hour in range(24):
            total = hourly_total.get(hour, 0)
            heating = hourly_heating.get(hour, 0)
            hourly_percentages[hour] = round((heating / total * 100), 1) if total > 0 else 0

        # Finde Peak-Heizzeiten
        peak_hours = sorted(
            hourly_percentages.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]

        return {
            'hourly_percentages': hourly_percentages,
            'peak_heating_hours': [
                {
                    'hour': hour,
                    'heating_percentage': percentage
                }
                for hour, percentage in peak_hours
            ]
        }

    def _analyze_weekly_heating_pattern(self, observations: List[Dict]) -> Dict:
        """Analysiert Heizmuster nach Wochentag"""
        weekday_names = ['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag',
                        'Freitag', 'Samstag', 'Sonntag']

        weekday_heating = {}
        weekday_total = {}

        for obs in observations:
            day = obs.get('day_of_week')
            if day is not None:
                weekday_total[day] = weekday_total.get(day, 0) + 1
                if obs.get('is_heating'):
                    weekday_heating[day] = weekday_heating.get(day, 0) + 1

        # Berechne Heiz-Prozentsatz pro Wochentag
        distribution = []
        for day in range(7):
            total = weekday_total.get(day, 0)
            heating = weekday_heating.get(day, 0)
            percentage = round((heating / total * 100), 1) if total > 0 else 0

            distribution.append({
                'day': day,
                'name': weekday_names[day],
                'heating_percentage': percentage,
                'observations': total
            })

        return {
            'distribution': distribution
        }

    def _analyze_temperature_patterns(self, observations: List[Dict]) -> Dict:
        """Analysiert Temperatur-Muster"""
        target_temps = [obs['target_temperature'] for obs in observations if obs.get('target_temperature')]
        current_temps = [obs['current_temperature'] for obs in observations if obs.get('current_temperature')]
        outdoor_temps = [obs['outdoor_temperature'] for obs in observations if obs.get('outdoor_temperature')]

        if not target_temps or not current_temps:
            return {'available': False}

        return {
            'available': True,
            'target_temperature': {
                'avg': round(statistics.mean(target_temps), 1),
                'min': round(min(target_temps), 1),
                'max': round(max(target_temps), 1),
                'std_dev': round(statistics.stdev(target_temps), 1) if len(target_temps) > 1 else 0
            },
            'current_temperature': {
                'avg': round(statistics.mean(current_temps), 1),
                'min': round(min(current_temps), 1),
                'max': round(max(current_temps), 1)
            },
            'outdoor_temperature': {
                'avg': round(statistics.mean(outdoor_temps), 1) if outdoor_temps else None,
                'min': round(min(outdoor_temps), 1) if outdoor_temps else None,
                'max': round(max(outdoor_temps), 1) if outdoor_temps else None
            }
        }

    def _detect_inefficiencies(self, observations: List[Dict]) -> Dict:
        """Erkennt Ineffizienzen im Heizverhalten"""
        # Heizen bei offenem Fenster
        window_open_heating = sum(1 for obs in observations
                                  if obs.get('window_open') and obs.get('is_heating'))

        # Hohe Temperaturen ohne Anwesenheit
        high_temp_no_presence = sum(1 for obs in observations
                                   if not obs.get('presence_detected')
                                   and obs.get('target_temperature', 0) > 20.0)

        # Nächtliche Überheizung (22-06 Uhr, über 19°C)
        night_overheating = sum(1 for obs in observations
                               if 22 <= obs.get('hour_of_day', 12) or obs.get('hour_of_day', 12) < 6
                               and obs.get('target_temperature', 0) > 19.0)

        total_obs = len(observations)

        return {
            'window_open_heating': {
                'count': window_open_heating,
                'percentage': round((window_open_heating / total_obs * 100), 1) if total_obs > 0 else 0
            },
            'high_temp_no_presence': {
                'count': high_temp_no_presence,
                'percentage': round((high_temp_no_presence / total_obs * 100), 1) if total_obs > 0 else 0
            },
            'night_overheating': {
                'count': night_overheating,
                'percentage': round((night_overheating / total_obs * 100), 1) if total_obs > 0 else 0
            }
        }

    def generate_insights(self, days_back: int = 14) -> List[Dict]:
        """
        Generiert konkrete Optimierungsvorschläge

        Returns:
            Liste von Insights mit Einsparpotenzialen
        """
        patterns = self.analyze_patterns(days_back=days_back)

        if not patterns.get('sufficient_data'):
            logger.warning("Nicht genug Daten für Insights")
            return []

        insights = []

        # Insight 1: Nachtabsenkung
        night_insight = self._generate_night_reduction_insight(patterns)
        if night_insight:
            insights.append(night_insight)
            # Speichere in DB
            self.db.add_heating_insight(
                insight_type='night_reduction',
                recommendation=night_insight['recommendation'],
                saving_percent=night_insight.get('saving_percent'),
                saving_eur=night_insight.get('saving_eur'),
                confidence=night_insight.get('confidence', 0.7),
                samples=patterns.get('observations_count', 0),
                priority=night_insight.get('priority', 'medium')
            )

        # Insight 2: Fenster-offen Warnung
        window_insight = self._generate_window_warning_insight(patterns)
        if window_insight:
            insights.append(window_insight)
            self.db.add_heating_insight(
                insight_type='window_warning',
                recommendation=window_insight['recommendation'],
                saving_percent=window_insight.get('saving_percent'),
                saving_eur=window_insight.get('saving_eur'),
                confidence=window_insight.get('confidence', 0.8),
                samples=patterns.get('observations_count', 0),
                priority=window_insight.get('priority', 'high')
            )

        # Insight 3: Temperaturoptimierung
        temp_insight = self._generate_temperature_optimization_insight(patterns)
        if temp_insight:
            insights.append(temp_insight)
            self.db.add_heating_insight(
                insight_type='temperature_optimization',
                recommendation=temp_insight['recommendation'],
                saving_percent=temp_insight.get('saving_percent'),
                saving_eur=temp_insight.get('saving_eur'),
                confidence=temp_insight.get('confidence', 0.7),
                samples=patterns.get('observations_count', 0),
                priority=temp_insight.get('priority', 'medium')
            )

        # Insight 4: Wochenend-Optimierung
        weekend_insight = self._generate_weekend_optimization_insight(patterns)
        if weekend_insight:
            insights.append(weekend_insight)
            self.db.add_heating_insight(
                insight_type='weekend_optimization',
                recommendation=weekend_insight['recommendation'],
                saving_percent=weekend_insight.get('saving_percent'),
                saving_eur=weekend_insight.get('saving_eur'),
                confidence=weekend_insight.get('confidence', 0.6),
                samples=patterns.get('observations_count', 0),
                priority=weekend_insight.get('priority', 'low')
            )

        logger.info(f"Generated {len(insights)} heating insights")
        return insights

    def _generate_night_reduction_insight(self, patterns: Dict) -> Optional[Dict]:
        """Generiert Vorschlag für Nachtabsenkung"""
        inefficiencies = patterns.get('inefficiencies', {})
        night_overheating = inefficiencies.get('night_overheating', {})

        if night_overheating.get('percentage', 0) > 20:  # Mehr als 20% der Nacht-Beobachtungen über 19°C
            # Berechne Einsparpotenzial (grobe Schätzung)
            # 2°C Reduktion nachts (8h) = ca. 10-15% Ersparnis
            saving_percent = 12.0
            saving_eur = self.heating_cost_per_degree_per_day * 2 * 30  # Pro Monat

            return {
                'type': 'night_reduction',
                'icon': '🌙',
                'title': 'Nachtabsenkung',
                'recommendation': f'Reduziere Nachttemperatur (22-6 Uhr) um 2°C auf 17-18°C',
                'saving_percent': saving_percent,
                'saving_eur': round(saving_eur, 2),
                'confidence': 0.75,
                'priority': 'high',
                'details': f'In {night_overheating.get("percentage")}% der Nächte wird über 19°C geheizt'
            }

        return None

    def _generate_window_warning_insight(self, patterns: Dict) -> Optional[Dict]:
        """Generiert Warnung für Heizen bei offenem Fenster"""
        inefficiencies = patterns.get('inefficiencies', {})
        window_heating = inefficiencies.get('window_open_heating', {})

        if window_heating.get('count', 0) > 10:
            # Heizen bei offenem Fenster ist sehr ineffizient (30-50% Verlust)
            saving_percent = 30.0
            # Annahme: 5% der Zeit wird mit offenem Fenster geheizt
            saving_eur = self.heating_cost_per_degree_per_day * 5 * 30 * 0.05

            return {
                'type': 'window_warning',
                'icon': '⚠️',
                'title': 'Fenster-Heizung',
                'recommendation': 'Aktiviere Fenster-Erkennung: Heizung automatisch aus bei offenem Fenster',
                'saving_percent': saving_percent,
                'saving_eur': round(saving_eur, 2),
                'confidence': 0.85,
                'priority': 'high',
                'details': f'{window_heating.get("count")} Mal wurde bei offenem Fenster geheizt'
            }

        return None

    def _generate_temperature_optimization_insight(self, patterns: Dict) -> Optional[Dict]:
        """Generiert Vorschlag zur Temperaturoptimierung"""
        temp_stats = patterns.get('temperature_stats', {})

        if not temp_stats.get('available'):
            return None

        avg_target = temp_stats.get('target_temperature', {}).get('avg', 21.0)

        # Wenn durchschnittliche Zieltemperatur über 21°C
        if avg_target > 21.0:
            reduction = round(avg_target - 21.0, 1)
            # 1°C Reduktion = ca. 6% Ersparnis
            saving_percent = reduction * 6
            saving_eur = self.heating_cost_per_degree_per_day * reduction * 30

            return {
                'type': 'temperature_optimization',
                'icon': '🌡️',
                'title': 'Temperatur-Optimierung',
                'recommendation': f'Reduziere Durchschnittstemperatur um {reduction}°C auf 21°C',
                'saving_percent': round(saving_percent, 1),
                'saving_eur': round(saving_eur, 2),
                'confidence': 0.70,
                'priority': 'medium',
                'details': f'Aktuelle Durchschnittstemperatur: {avg_target}°C'
            }

        return None

    def _generate_weekend_optimization_insight(self, patterns: Dict) -> Optional[Dict]:
        """Generiert Vorschlag für Wochenend-Optimierung"""
        weekly = patterns.get('weekly_pattern', {})

        if not weekly:
            return None

        # Vergleiche Werktage vs. Wochenende
        weekday_avg = statistics.mean([
            day['heating_percentage']
            for day in weekly.get('distribution', [])[:5]
        ])

        weekend_avg = statistics.mean([
            day['heating_percentage']
            for day in weekly.get('distribution', [])[5:]
        ])

        # Wenn am Wochenende ähnlich viel geheizt wird wie unter der Woche
        if abs(weekend_avg - weekday_avg) < 5:  # Unterschied < 5%
            return {
                'type': 'weekend_optimization',
                'icon': '📅',
                'title': 'Wochenend-Heizplan',
                'recommendation': 'Erstelle separaten Heizplan für Wochenenden basierend auf Anwesenheit',
                'saving_percent': 5.0,
                'saving_eur': round(self.heating_cost_per_degree_per_day * 1 * 8, 2),  # 8 Wochenend-Tage/Monat
                'confidence': 0.60,
                'priority': 'low',
                'details': f'Werktag: {weekday_avg:.1f}% Heizzeit, Wochenende: {weekend_avg:.1f}%'
            }

        return None

    def get_recommended_schedule(self, device_id: str = None) -> List[Dict]:
        """
        Erstellt einen optimierten Heizplan basierend auf gelernten Mustern

        Returns:
            Liste von Zeitplan-Einträgen
        """
        patterns = self.analyze_patterns(days_back=14)

        if not patterns.get('sufficient_data'):
            logger.warning("Nicht genug Daten für Zeitplan-Erstellung")
            return []

        schedule = []
        hourly_pattern = patterns.get('hourly_pattern', {})

        # Standard-Temperaturen
        comfort_temp = 21.0
        eco_temp = 18.0
        night_temp = 17.0

        # Erstelle Wochenplan
        for day in range(7):
            for hour in range(24):
                # Bestimme optimale Temperatur basierend auf Heizmuster
                heating_percent = hourly_pattern.get('hourly_percentages', {}).get(hour, 0)

                if hour >= 22 or hour < 6:
                    # Nacht
                    recommended_temp = night_temp
                    reason = "Nachtabsenkung"
                elif heating_percent > 70:
                    # Häufig geheizt -> Komfort
                    recommended_temp = comfort_temp
                    reason = f"Häufige Nutzung ({heating_percent}%)"
                elif heating_percent > 30:
                    # Gelegentlich geheizt -> Öko
                    recommended_temp = eco_temp
                    reason = f"Gelegentliche Nutzung ({heating_percent}%)"
                else:
                    # Selten geheizt -> Absenkung
                    recommended_temp = eco_temp - 1
                    reason = f"Seltene Nutzung ({heating_percent}%)"

                schedule.append({
                    'day_of_week': day,
                    'hour': hour,
                    'recommended_temperature': recommended_temp,
                    'reason': reason,
                    'heating_percentage': heating_percent
                })

        # Speichere Zeitplan in DB (nur wenn device_id angegeben)
        if device_id and schedule:
            for entry in schedule:
                self.db.save_heating_schedule(
                    device_id=device_id,
                    room_name="Alle",  # TODO: Raumspezifisch
                    schedule_type='optimized',
                    day_of_week=entry['day_of_week'],
                    hour=entry['hour'],
                    recommended_temp=entry['recommended_temperature'],
                    reason=entry['reason'],
                    confidence=0.7,
                    samples=patterns.get('observations_count', 0)
                )

        return schedule
