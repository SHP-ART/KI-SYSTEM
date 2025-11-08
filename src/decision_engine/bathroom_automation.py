"""
Intelligente Badezimmer-Automatisierung
Steuert Luftentfeuchter und Heizung basierend auf Sensoren
Mit selbstlernendem Optimierungs-System
"""

from typing import Dict, Optional, List
from datetime import datetime, timedelta
from loguru import logger
from src.utils.database import Database
from src.decision_engine.bathroom_analyzer import BathroomAnalyzer


class BathroomAutomation:
    """
    Intelligente Steuerung für Badezimmer:
    - Erkennt Duschen automatisch
    - Steuert Luftentfeuchter
    - Regelt Heizung
    """

    def __init__(self, config: Dict, enable_learning: bool = True):
        """
        Args:
            config: {
                'humidity_sensor_id': str,
                'temperature_sensor_id': str,
                'dehumidifier_id': str,
                'heater_id': str,
                'door_sensor_id': str (optional),
                'motion_sensor_id': str (optional),
                'humidity_threshold_high': float (default: 70),
                'humidity_threshold_low': float (default: 60),
                'target_temperature': float (default: 22)
            }
            enable_learning: Aktiviert selbstlernendes System (default: True)
        """
        self.config = config
        self.last_motion_time = None
        self.shower_detected = False
        self.dehumidifier_running = False
        self.enable_learning = enable_learning

        # Schwellwerte (können durch Lernen überschrieben werden)
        self.humidity_high = config.get('humidity_threshold_high', 70.0)
        self.humidity_low = config.get('humidity_threshold_low', 60.0)
        self.target_temp = config.get('target_temperature', 22.0)

        # Verzögerung bevor Luftentfeuchter ausschaltet
        self.dehumidifier_delay_minutes = config.get('dehumidifier_delay', 5)

        # Event-Tracking
        self.current_event_id = None
        self.event_start_time = None
        self.dehumidifier_start_time = None

        # Datenbank für Lernsystem
        self.db = Database() if enable_learning else None

        # Lade gelernte Parameter
        if self.db and enable_learning:
            self._load_learned_parameters()

        logger.info(f"Bathroom automation initialized: High={self.humidity_high}%, Low={self.humidity_low}%, Learning={enable_learning}")

    def process(self, platform, current_state: Dict) -> List[Dict]:
        """
        Hauptlogik - wird regelmäßig aufgerufen

        Returns:
            Liste von Aktionen die ausgeführt werden sollen
        """
        actions = []

        # Hole Sensor-Werte
        humidity = self._get_humidity(platform)
        temperature = self._get_temperature(platform)
        motion_detected = self._check_motion(platform)
        door_closed = self._check_door(platform)

        if humidity is None:
            logger.warning("No humidity sensor data available")
            return actions

        # Update Motion-Tracking
        if motion_detected:
            self.last_motion_time = datetime.now()

        # === DUSCHEN ERKENNUNG ===
        shower_active = self._detect_shower(humidity, motion_detected, door_closed)

        if shower_active and not self.shower_detected:
            logger.info("🚿 Shower detected! Starting dehumidifier...")
            self.shower_detected = True
            # Starte Event-Tracking
            self._start_event(platform)

        # Speichere Messung während des Events
        if self.current_event_id:
            self._record_measurement(platform)

        # === LUFTENTFEUCHTER STEUERUNG ===
        dehumidifier_action = self._control_dehumidifier(
            humidity,
            shower_active,
            motion_detected,
            platform  # Für Logging
        )
        if dehumidifier_action:
            actions.append(dehumidifier_action)

        # === HEIZUNG STEUERUNG ===
        heating_action = self._control_heating(
            temperature,
            humidity,
            self.dehumidifier_running,
            platform  # Für Logging
        )
        if heating_action:
            actions.append(heating_action)

        # Reset shower detection wenn Luftfeuchtigkeit wieder normal
        if self.shower_detected and humidity < self.humidity_low:
            logger.info("Shower finished, humidity back to normal")
            self.shower_detected = False
            # Beende Event-Tracking
            self._end_event(platform)

        return actions

    def _get_humidity(self, platform) -> Optional[float]:
        """Liest Luftfeuchtigkeit-Sensor"""
        sensor_id = self.config.get('humidity_sensor_id')
        if not sensor_id:
            return None

        try:
            state = platform.get_state(sensor_id)
            if state:
                caps = state.get('attributes', {}).get('capabilities', {})
                if 'measure_humidity' in caps:
                    return caps['measure_humidity'].get('value')
        except Exception as e:
            logger.error(f"Error reading humidity sensor: {e}")

        return None

    def _get_temperature(self, platform) -> Optional[float]:
        """Liest Temperatur-Sensor"""
        sensor_id = self.config.get('temperature_sensor_id')
        if not sensor_id:
            return None

        try:
            state = platform.get_state(sensor_id)
            if state:
                caps = state.get('attributes', {}).get('capabilities', {})
                if 'measure_temperature' in caps:
                    return caps['measure_temperature'].get('value')
        except Exception as e:
            logger.error(f"Error reading temperature sensor: {e}")

        return None

    def _check_motion(self, platform) -> bool:
        """Prüft Bewegungs-Sensor"""
        sensor_id = self.config.get('motion_sensor_id')
        if not sensor_id:
            return False

        try:
            state = platform.get_state(sensor_id)
            if state:
                caps = state.get('attributes', {}).get('capabilities', {})
                if 'alarm_motion' in caps:
                    return caps['alarm_motion'].get('value', False)
        except Exception as e:
            logger.debug(f"Error reading motion sensor: {e}")

        return False

    def _check_door(self, platform) -> bool:
        """Prüft Tür-Sensor (geschlossen = True)"""
        sensor_id = self.config.get('door_sensor_id')
        if not sensor_id:
            return False  # Kein Sensor = ignorieren

        try:
            state = platform.get_state(sensor_id)
            if state:
                caps = state.get('attributes', {}).get('capabilities', {})
                # alarm_contact: true = offen, false = geschlossen
                if 'alarm_contact' in caps:
                    is_open = caps['alarm_contact'].get('value', False)
                    return not is_open  # Umkehren: wir wollen wissen ob ZU
        except Exception as e:
            logger.debug(f"Error reading door sensor: {e}")

        return False

    def _detect_shower(self, humidity: float, motion: bool, door_closed: bool) -> bool:
        """
        Erkennt ob gerade geduscht wird

        Kriterien:
        - Luftfeuchtigkeit über Schwellwert
        - Optional: Bewegung erkannt
        - Optional: Tür geschlossen
        """
        if humidity > self.humidity_high:
            # Hohe Luftfeuchtigkeit ist Hauptindikator

            # Wenn wir einen Bewegungssensor haben, prüfe ob kürzlich Bewegung war
            if self.config.get('motion_sensor_id'):
                if self.last_motion_time:
                    time_since_motion = (datetime.now() - self.last_motion_time).seconds / 60
                    if time_since_motion > 30:  # Keine Bewegung seit 30 Min
                        return False

            return True

        return False

    def _control_dehumidifier(self, humidity: float, shower_active: bool,
                             motion: bool, platform) -> Optional[Dict]:
        """
        Steuert Luftentfeuchter intelligent

        Returns:
            Action-Dict oder None
        """
        dehumidifier_id = self.config.get('dehumidifier_id')
        if not dehumidifier_id:
            return None

        # EINSCHALTEN wenn:
        # - Luftfeuchtigkeit zu hoch
        # - Oder Dusche aktiv erkannt
        should_turn_on = (humidity > self.humidity_high) or shower_active

        if should_turn_on and not self.dehumidifier_running:
            reason = f'High humidity ({humidity}%) or shower detected'
            logger.info(f"💨 Turning ON dehumidifier (humidity: {humidity}%)")
            self.dehumidifier_running = True
            self.dehumidifier_start_time = datetime.now()

            # Protokolliere Aktion
            self._log_device_action('dehumidifier', dehumidifier_id, 'turn_on', reason, platform)

            return {
                'device_id': dehumidifier_id,
                'action': 'turn_on',
                'reason': reason
            }

        # AUSSCHALTEN wenn:
        # - Luftfeuchtigkeit wieder niedrig
        # - UND keine kürzliche Bewegung (Verzögerung)
        should_turn_off = humidity < self.humidity_low

        if should_turn_off and self.dehumidifier_running:
            # Prüfe Verzögerung
            if self.last_motion_time:
                minutes_since_motion = (datetime.now() - self.last_motion_time).seconds / 60
                if minutes_since_motion < self.dehumidifier_delay_minutes:
                    logger.debug(f"Delaying dehumidifier shutdown (motion detected {minutes_since_motion:.1f} min ago)")
                    return None

            reason = f'Humidity normalized ({humidity}%)'
            logger.info(f"💨 Turning OFF dehumidifier (humidity: {humidity}%)")
            self.dehumidifier_running = False

            # Protokolliere Aktion
            self._log_device_action('dehumidifier', dehumidifier_id, 'turn_off', reason, platform)

            return {
                'device_id': dehumidifier_id,
                'action': 'turn_off',
                'reason': reason
            }

        return None

    def _control_heating(self, temperature: Optional[float], humidity: float,
                        dehumidifier_running: bool, platform) -> Optional[Dict]:
        """
        Steuert Heizung intelligent

        Während Entfeuchtung: Temperatur leicht erhöhen (beschleunigt Trocknung)
        Normal: Ziel-Temperatur halten
        """
        heater_id = self.config.get('heater_id')
        if not heater_id or temperature is None:
            return None

        # Ziel-Temperatur anpassen
        if dehumidifier_running:
            # Während Entfeuchtung: +1°C für bessere Trocknung
            target = self.target_temp + 1.0
        else:
            target = self.target_temp

        # Nur anpassen wenn Abweichung > 0.5°C
        if abs(temperature - target) > 0.5:
            reason = f'Target temperature adjustment (dehumidifier: {dehumidifier_running})'
            logger.info(f"🌡️ Adjusting heating to {target}°C (current: {temperature}°C)")

            # Protokolliere Aktion
            self._log_device_action('heater', heater_id, 'set_temperature', reason, platform)

            return {
                'device_id': heater_id,
                'action': 'set_temperature',
                'temperature': target,
                'reason': reason
            }

        return None

    def get_status(self, platform) -> Dict:
        """Gibt aktuellen Status zurück"""
        status = {
            'enabled': True,
            'shower_detected': self.shower_detected,
            'dehumidifier_running': self.dehumidifier_running,
            'current_humidity': self._get_humidity(platform),
            'current_temperature': self._get_temperature(platform),
            'thresholds': {
                'humidity_high': self.humidity_high,
                'humidity_low': self.humidity_low,
                'target_temperature': self.target_temp
            },
            'last_motion': self.last_motion_time.isoformat() if self.last_motion_time else None,
            'learning_enabled': self.enable_learning
        }

        # Füge Event-Info hinzu wenn aktiv
        if self.current_event_id and self.event_start_time:
            duration = (datetime.now() - self.event_start_time).seconds / 60
            status['current_event'] = {
                'id': self.current_event_id,
                'duration_minutes': duration
            }

        return status

    # === LERN-FUNKTIONEN ===

    def _load_learned_parameters(self):
        """Lädt gelernte Parameter aus der Datenbank"""
        if not self.db:
            return

        try:
            # Lade optimierte Schwellwerte
            learned_high = self.db.get_learned_parameter('humidity_threshold_high')
            learned_low = self.db.get_learned_parameter('humidity_threshold_low')
            learned_delay = self.db.get_learned_parameter('dehumidifier_delay')

            if learned_high:
                self.humidity_high = learned_high
                logger.info(f"Loaded learned humidity_high: {learned_high}%")

            if learned_low:
                self.humidity_low = learned_low
                logger.info(f"Loaded learned humidity_low: {learned_low}%")

            if learned_delay:
                self.dehumidifier_delay_minutes = learned_delay
                logger.info(f"Loaded learned delay: {learned_delay} min")

        except Exception as e:
            logger.error(f"Error loading learned parameters: {e}")

    def _record_measurement(self, platform):
        """Speichert aktuelle Messung während eines Events"""
        if not self.db or not self.current_event_id:
            return

        try:
            humidity = self._get_humidity(platform)
            temperature = self._get_temperature(platform)
            motion = self._check_motion(platform)

            if humidity is not None and temperature is not None:
                self.db.add_bathroom_measurement(
                    event_id=self.current_event_id,
                    humidity=humidity,
                    temperature=temperature,
                    motion=motion,
                    dehumidifier_on=self.dehumidifier_running
                )
        except Exception as e:
            logger.error(f"Error recording measurement: {e}")

    def _log_device_action(self, device_type: str, device_id: str,
                          action: str, reason: str, platform):
        """Protokolliert eine Geräte-Aktion"""
        if not self.db:
            return

        try:
            humidity = self._get_humidity(platform) or 0
            temperature = self._get_temperature(platform) or 0

            self.db.add_bathroom_device_action(
                device_type=device_type,
                device_id=device_id,
                action=action,
                reason=reason,
                humidity=humidity,
                temperature=temperature,
                event_id=self.current_event_id
            )
        except Exception as e:
            logger.error(f"Error logging device action: {e}")

    def _start_event(self, platform):
        """Startet ein neues Badezimmer-Event"""
        if not self.db or self.current_event_id:
            return  # Event läuft bereits

        try:
            humidity = self._get_humidity(platform) or 0
            temperature = self._get_temperature(platform) or 0
            motion = self._check_motion(platform)
            door_closed = self._check_door(platform)

            self.current_event_id = self.db.start_bathroom_event(
                humidity=humidity,
                temperature=temperature,
                motion=motion,
                door_closed=door_closed
            )

            self.event_start_time = datetime.now()
            logger.info(f"Started bathroom event {self.current_event_id}")

        except Exception as e:
            logger.error(f"Error starting event: {e}")

    def _end_event(self, platform):
        """Beendet das aktuelle Badezimmer-Event"""
        if not self.db or not self.current_event_id:
            return

        try:
            humidity = self._get_humidity(platform) or 0

            # Berechne Luftentfeuchter-Laufzeit
            dehumidifier_runtime = None
            if self.dehumidifier_start_time:
                dehumidifier_runtime = (datetime.now() - self.dehumidifier_start_time).seconds / 60

            self.db.end_bathroom_event(
                event_id=self.current_event_id,
                humidity=humidity,
                dehumidifier_runtime=dehumidifier_runtime
            )

            logger.info(f"Ended bathroom event {self.current_event_id}")

            self.current_event_id = None
            self.event_start_time = None
            self.dehumidifier_start_time = None

        except Exception as e:
            logger.error(f"Error ending event: {e}")

    def optimize_parameters(self, days_back: int = 30, min_confidence: float = 0.7) -> Optional[Dict]:
        """
        Optimiert die Schwellwerte basierend auf historischen Daten

        Returns:
            Dict mit Optimierungs-Ergebnissen oder None
        """
        if not self.db or not self.enable_learning:
            logger.warning("Learning disabled, skipping optimization")
            return None

        try:
            analyzer = BathroomAnalyzer(self.db)

            # Hole optimale Schwellwerte
            suggestions = analyzer.suggest_optimal_thresholds(days_back=days_back)

            if not suggestions:
                logger.warning("Not enough data for optimization")
                return None

            if suggestions['confidence'] < min_confidence:
                logger.warning(f"Confidence too low ({suggestions['confidence']} < {min_confidence}), skipping optimization")
                return {
                    'success': False,
                    'reason': 'Confidence too low',
                    'suggestions': suggestions
                }

            # Speichere gelernte Parameter
            self.db.save_learned_parameter(
                parameter_name='humidity_threshold_high',
                value=suggestions['humidity_threshold_high'],
                confidence=suggestions['confidence'],
                samples_used=suggestions['based_on_events'],
                reason=suggestions['reason']
            )

            self.db.save_learned_parameter(
                parameter_name='humidity_threshold_low',
                value=suggestions['humidity_threshold_low'],
                confidence=suggestions['confidence'],
                samples_used=suggestions['based_on_events'],
                reason=suggestions['reason']
            )

            # Aktualisiere aktuelle Werte
            old_values = {
                'humidity_high': self.humidity_high,
                'humidity_low': self.humidity_low
            }

            self.humidity_high = suggestions['humidity_threshold_high']
            self.humidity_low = suggestions['humidity_threshold_low']

            logger.info(f"✨ Parameters optimized! High: {old_values['humidity_high']}% -> {self.humidity_high}%, Low: {old_values['humidity_low']}% -> {self.humidity_low}%")

            return {
                'success': True,
                'old_values': old_values,
                'new_values': {
                    'humidity_high': self.humidity_high,
                    'humidity_low': self.humidity_low
                },
                'confidence': suggestions['confidence'],
                'based_on_events': suggestions['based_on_events'],
                'statistics': suggestions['statistics']
            }

        except Exception as e:
            logger.error(f"Error during optimization: {e}")
            return None

    def get_analytics(self, days_back: int = 30) -> Dict:
        """
        Holt Analytics und Statistiken

        Returns:
            Dict mit Analytics-Daten
        """
        if not self.db:
            return {'available': False, 'reason': 'Database not available'}

        try:
            analyzer = BathroomAnalyzer(self.db)

            # Hole Muster-Analyse
            patterns = analyzer.analyze_patterns(days_back=days_back)

            # Hole Statistiken
            stats = self.db.get_bathroom_statistics(days_back=days_back)

            # Hole Vorhersage
            prediction = analyzer.predict_next_shower()

            return {
                'available': True,
                'patterns': patterns,
                'statistics': stats,
                'prediction': prediction,
                'learning_enabled': self.enable_learning
            }

        except Exception as e:
            logger.error(f"Error getting analytics: {e}")
            return {'available': False, 'reason': str(e)}
