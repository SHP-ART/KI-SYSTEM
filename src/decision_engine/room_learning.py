"""
Raumspezifisches Lernen für Heizungssteuerung
Lernt individuelle Eigenschaften jedes Raums (Aufheizzeit, Wärmeverlust, etc.)
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from loguru import logger
from src.utils.database import Database
import statistics


class RoomLearningSystem:
    """
    Lernt raumspezifische Heizungs-Charakteristiken

    Gelernte Parameter:
    - heating_rate: Wie schnell heizt der Raum auf (°C pro Stunde)
    - cooling_rate: Wie schnell kühlt der Raum ab (°C pro Stunde)
    - thermal_mass: Thermische Masse (wie lange hält Wärme)
    - optimal_temp_comfort: Gelernte Komfort-Temperatur
    - optimal_temp_night: Gelernte Nacht-Temperatur
    - heat_loss_coefficient: Wärmeverlust-Koeffizient
    """

    def __init__(self, db: Database = None):
        self.db = db or Database()
        self.min_samples = 10  # Mindestens 10 Messungen für Lernen

    def learn_heating_rate(self, room_name: str, days_back: int = 14) -> Optional[float]:
        """
        Lernt wie schnell ein Raum aufheizt (°C pro Stunde)

        Returns:
            Aufheizrate in °C/h oder None wenn zu wenig Daten
        """
        observations = self.db.get_heating_observations(
            room_name=room_name,
            days_back=days_back
        )

        if not observations or len(observations) < self.min_samples:
            logger.warning(f"Not enough data to learn heating rate for {room_name}")
            return None

        # Finde Perioden wo geheizt wird
        heating_periods = self._find_heating_periods(observations)

        if not heating_periods or len(heating_periods) < 3:
            logger.warning(f"Not enough heating periods found for {room_name}")
            return None

        # Berechne Aufheizrate für jede Periode
        heating_rates = []

        for period in heating_periods:
            start_temp = period['start_temp']
            end_temp = period['end_temp']
            duration_hours = period['duration_hours']

            if duration_hours > 0.1:  # Mindestens 6 Minuten
                temp_increase = end_temp - start_temp
                if temp_increase > 0.2:  # Mindestens 0.2°C Anstieg
                    rate = temp_increase / duration_hours
                    heating_rates.append(rate)

        if not heating_rates:
            return None

        # Median ist robuster gegen Ausreißer als Mean
        heating_rate = statistics.median(heating_rates)

        # Plausibilitätsprüfung (0.5 - 5°C pro Stunde sind realistisch)
        if 0.5 <= heating_rate <= 5.0:
            # Speichere gelernten Parameter
            confidence = min(1.0, len(heating_rates) / 20.0)  # 20 Samples = volle Confidence
            self.db.save_room_learning_parameter(
                room_name=room_name,
                parameter_name='heating_rate',
                value=heating_rate,
                confidence=confidence,
                samples=len(heating_rates),
                notes=f'Learned from {len(heating_rates)} heating periods'
            )

            logger.info(f"Learned heating rate for {room_name}: {heating_rate:.2f}°C/h (confidence: {confidence:.0%})")
            return round(heating_rate, 2)

        return None

    def learn_cooling_rate(self, room_name: str, days_back: int = 14) -> Optional[float]:
        """
        Lernt wie schnell ein Raum abkühlt (°C pro Stunde)

        Returns:
            Abkühlrate in °C/h oder None
        """
        observations = self.db.get_heating_observations(
            room_name=room_name,
            days_back=days_back
        )

        if not observations or len(observations) < self.min_samples:
            return None

        # Finde Perioden wo NICHT geheizt wird
        cooling_periods = self._find_cooling_periods(observations)

        if not cooling_periods or len(cooling_periods) < 3:
            return None

        cooling_rates = []

        for period in cooling_periods:
            start_temp = period['start_temp']
            end_temp = period['end_temp']
            duration_hours = period['duration_hours']

            if duration_hours > 0.5:  # Mindestens 30 Minuten
                temp_decrease = start_temp - end_temp
                if temp_decrease > 0.1:  # Mindestens 0.1°C Abfall
                    rate = temp_decrease / duration_hours
                    cooling_rates.append(rate)

        if not cooling_rates:
            return None

        cooling_rate = statistics.median(cooling_rates)

        # Plausibilitätsprüfung (0.1 - 2°C pro Stunde)
        if 0.1 <= cooling_rate <= 2.0:
            confidence = min(1.0, len(cooling_rates) / 20.0)
            self.db.save_room_learning_parameter(
                room_name=room_name,
                parameter_name='cooling_rate',
                value=cooling_rate,
                confidence=confidence,
                samples=len(cooling_rates)
            )

            logger.info(f"Learned cooling rate for {room_name}: {cooling_rate:.2f}°C/h")
            return round(cooling_rate, 2)

        return None

    def calculate_thermal_mass(self, heating_rate: float, cooling_rate: float) -> float:
        """
        Berechnet thermische Masse des Raums

        Räume mit hoher thermischer Masse:
        - Heizen langsam auf
        - Kühlen langsam ab
        - Halten Temperatur gut

        Returns:
            Thermische Masse Score (0-100)
        """
        if heating_rate <= 0 or cooling_rate <= 0:
            return 50.0  # Neutral

        # Verhältnis von Aufheiz- zu Abkühlrate
        # Gute thermische Masse: langsames Aufheizen, langsames Abkühlen
        thermal_score = (1 / heating_rate) * 50 + (1 / cooling_rate) * 50

        # Normalisiere auf 0-100
        normalized = min(100, max(0, thermal_score))

        return round(normalized, 1)

    def learn_optimal_temperatures(self, room_name: str, days_back: int = 30) -> Dict:
        """
        Lernt die vom Nutzer bevorzugten Temperaturen für verschiedene Zeiten

        Returns:
            Dict mit gelernten Temperaturen
        """
        observations = self.db.get_heating_observations(
            room_name=room_name,
            days_back=days_back
        )

        if not observations or len(observations) < self.min_samples:
            return {}

        # Gruppiere nach Tageszeit
        morning_temps = []  # 6-9 Uhr
        day_temps = []      # 9-22 Uhr
        night_temps = []    # 22-6 Uhr

        for obs in observations:
            hour = obs.get('hour_of_day', 12)
            target_temp = obs.get('target_temp') or obs.get('target_temperature')

            if target_temp and target_temp > 10:  # Plausibilität
                if 6 <= hour < 9:
                    morning_temps.append(target_temp)
                elif 9 <= hour < 22:
                    day_temps.append(target_temp)
                else:
                    night_temps.append(target_temp)

        learned_temps = {}

        if morning_temps and len(morning_temps) >= 5:
            optimal_morning = statistics.median(morning_temps)
            learned_temps['optimal_temp_morning'] = round(optimal_morning, 1)
            self.db.save_room_learning_parameter(
                room_name, 'optimal_temp_morning', optimal_morning,
                confidence=min(1.0, len(morning_temps) / 20.0),
                samples=len(morning_temps)
            )

        if day_temps and len(day_temps) >= 5:
            optimal_day = statistics.median(day_temps)
            learned_temps['optimal_temp_day'] = round(optimal_day, 1)
            self.db.save_room_learning_parameter(
                room_name, 'optimal_temp_day', optimal_day,
                confidence=min(1.0, len(day_temps) / 30.0),
                samples=len(day_temps)
            )

        if night_temps and len(night_temps) >= 5:
            optimal_night = statistics.median(night_temps)
            learned_temps['optimal_temp_night'] = round(optimal_night, 1)
            self.db.save_room_learning_parameter(
                room_name, 'optimal_temp_night', optimal_night,
                confidence=min(1.0, len(night_temps) / 20.0),
                samples=len(night_temps)
            )

        return learned_temps

    def calculate_preheat_time(self, room_name: str, current_temp: float,
                              target_temp: float) -> Optional[int]:
        """
        Berechnet wie lange vorher geheizt werden muss

        Args:
            room_name: Raumname
            current_temp: Aktuelle Temperatur
            target_temp: Zieltemperatur

        Returns:
            Benötigte Zeit in Minuten
        """
        # Hole gelernte Aufheizrate
        heating_rate = self.db.get_room_learning_parameter(room_name, 'heating_rate')

        if not heating_rate or heating_rate <= 0:
            # Fallback: Standardwert 1°C pro Stunde
            heating_rate = 1.0
            logger.warning(f"No learned heating rate for {room_name}, using default {heating_rate}°C/h")

        temp_diff = target_temp - current_temp

        if temp_diff <= 0:
            return 0  # Schon warm genug

        # Berechne benötigte Zeit
        hours_needed = temp_diff / heating_rate
        minutes_needed = int(hours_needed * 60)

        # Sicherheitspuffer von 10%
        minutes_with_buffer = int(minutes_needed * 1.1)

        logger.info(
            f"Preheat calculation for {room_name}: "
            f"{temp_diff:.1f}°C / {heating_rate:.1f}°C/h = {minutes_needed} min "
            f"(+10% = {minutes_with_buffer} min)"
        )

        return minutes_with_buffer

    def _find_heating_periods(self, observations: List[Dict]) -> List[Dict]:
        """Findet Perioden wo aktiv geheizt wurde"""
        periods = []
        current_period = None

        sorted_obs = sorted(observations, key=lambda x: x.get('timestamp', ''))

        for obs in sorted_obs:
            is_heating = obs.get('is_heating', False)
            current_temp = obs.get('current_temp') or obs.get('current_temperature')
            timestamp = obs.get('timestamp')

            if not current_temp or not timestamp:
                continue

            if is_heating:
                if current_period is None:
                    # Neue Heizperiode starten
                    current_period = {
                        'start_time': datetime.fromisoformat(timestamp),
                        'start_temp': current_temp,
                        'end_time': datetime.fromisoformat(timestamp),
                        'end_temp': current_temp
                    }
                else:
                    # Heizperiode fortsetzen
                    current_period['end_time'] = datetime.fromisoformat(timestamp)
                    current_period['end_temp'] = current_temp
            else:
                if current_period is not None:
                    # Heizperiode beenden
                    duration = (current_period['end_time'] - current_period['start_time']).total_seconds() / 3600
                    if duration >= 0.1:  # Mindestens 6 Minuten
                        current_period['duration_hours'] = duration
                        periods.append(current_period)
                    current_period = None

        # Letzte Periode abschließen
        if current_period is not None:
            duration = (current_period['end_time'] - current_period['start_time']).total_seconds() / 3600
            if duration >= 0.1:
                current_period['duration_hours'] = duration
                periods.append(current_period)

        return periods

    def _find_cooling_periods(self, observations: List[Dict]) -> List[Dict]:
        """Findet Perioden wo Raum abkühlt (nicht geheizt wird)"""
        periods = []
        current_period = None

        sorted_obs = sorted(observations, key=lambda x: x.get('timestamp', ''))

        for obs in sorted_obs:
            is_heating = obs.get('is_heating', False)
            current_temp = obs.get('current_temp') or obs.get('current_temperature')
            timestamp = obs.get('timestamp')

            if not current_temp or not timestamp:
                continue

            if not is_heating:
                if current_period is None:
                    current_period = {
                        'start_time': datetime.fromisoformat(timestamp),
                        'start_temp': current_temp,
                        'end_time': datetime.fromisoformat(timestamp),
                        'end_temp': current_temp
                    }
                else:
                    current_period['end_time'] = datetime.fromisoformat(timestamp)
                    current_period['end_temp'] = current_temp
            else:
                if current_period is not None:
                    duration = (current_period['end_time'] - current_period['start_time']).total_seconds() / 3600
                    if duration >= 0.5:  # Mindestens 30 Minuten
                        current_period['duration_hours'] = duration
                        periods.append(current_period)
                    current_period = None

        if current_period is not None:
            duration = (current_period['end_time'] - current_period['start_time']).total_seconds() / 3600
            if duration >= 0.5:
                current_period['duration_hours'] = duration
                periods.append(current_period)

        return periods

    def get_room_profile(self, room_name: str) -> Dict:
        """
        Holt vollständiges gelerntes Profil eines Raums

        Returns:
            Dict mit allen gelernten Parametern
        """
        heating_rate = self.db.get_room_learning_parameter(room_name, 'heating_rate')
        cooling_rate = self.db.get_room_learning_parameter(room_name, 'cooling_rate')
        optimal_morning = self.db.get_room_learning_parameter(room_name, 'optimal_temp_morning')
        optimal_day = self.db.get_room_learning_parameter(room_name, 'optimal_temp_day')
        optimal_night = self.db.get_room_learning_parameter(room_name, 'optimal_temp_night')

        thermal_mass = None
        if heating_rate and cooling_rate:
            thermal_mass = self.calculate_thermal_mass(heating_rate, cooling_rate)

        return {
            'room_name': room_name,
            'heating_rate_celsius_per_hour': heating_rate,
            'cooling_rate_celsius_per_hour': cooling_rate,
            'thermal_mass_score': thermal_mass,
            'optimal_temp_morning': optimal_morning,
            'optimal_temp_day': optimal_day,
            'optimal_temp_night': optimal_night,
            'profile_complete': all([heating_rate, cooling_rate, optimal_day])
        }
