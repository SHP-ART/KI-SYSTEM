"""
Background Task: Kontinuierliche Badezimmer-Datensammlung
- Sammelt alle 60 Sekunden Temperatur und Luftfeuchtigkeit
- Unabhängig von Dusch-Events
- Ermöglicht detaillierte Langzeit-Analyse
"""

import threading
import time
import json
from pathlib import Path
from datetime import datetime
from loguru import logger
from src.utils.database import Database


class BathroomDataCollector:
    """
    Background-Prozess für kontinuierliche Badezimmer-Datensammlung

    - Sammelt alle 60 Sekunden Temperatur & Luftfeuchtigkeit
    - Speichert in separater Tabelle für Langzeit-Analyse
    - Läuft unabhängig von Event-Erkennung
    """

    def __init__(self, engine=None, interval_seconds: int = 60):
        """
        Args:
            engine: DecisionEngine Instanz (optional)
            interval_seconds: Intervall für Datensammlung in Sekunden (default: 60)
        """
        self.engine = engine
        self.interval_seconds = interval_seconds
        self.running = False
        self.thread = None
        self.last_collection = None
        self.db = Database()
        self.config = None

        # Lade Badezimmer-Konfiguration
        self._load_config()

    def _load_config(self):
        """Lädt die Badezimmer-Konfiguration"""
        try:
            config_file = Path('data/luftentfeuchten_config.json')
            if config_file.exists():
                with open(config_file, 'r') as f:
                    self.config = json.load(f)
                logger.debug("Bathroom config loaded for data collector")
            else:
                logger.warning("No bathroom config found - data collector will wait for configuration")
        except Exception as e:
            logger.error(f"Error loading bathroom config: {e}")

    def start(self):
        """Startet den Background-Prozess"""
        if self.running:
            logger.warning("BathroomDataCollector is already running")
            return

        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        logger.info(f"BathroomDataCollector started (collects every {self.interval_seconds}s)")

    def stop(self):
        """Stoppt den Background-Prozess"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("BathroomDataCollector stopped")

    def _run_loop(self):
        """Haupt-Loop des Background-Prozesses"""
        while self.running:
            try:
                # Reload config alle 5 Minuten (falls geändert)
                if self._should_reload_config():
                    self._load_config()

                # Datensammlung
                if self._should_collect_now():
                    self._collect_data()
                    self.last_collection = datetime.now()

                # Warte interval_seconds Sekunden
                time.sleep(self.interval_seconds)

            except Exception as e:
                logger.error(f"Error in BathroomDataCollector loop: {e}")
                time.sleep(self.interval_seconds)

    def _should_collect_now(self) -> bool:
        """Prüft ob jetzt Daten gesammelt werden sollen"""
        if not self.last_collection:
            return True

        seconds_since_last = (datetime.now() - self.last_collection).seconds
        return seconds_since_last >= self.interval_seconds

    def _should_reload_config(self) -> bool:
        """Prüft ob Config neu geladen werden soll (alle 5 Minuten)"""
        if not self.last_collection:
            return False

        minutes_since_last = (datetime.now() - self.last_collection).seconds / 60
        return minutes_since_last >= 5

    def _collect_data(self):
        """Sammelt aktuelle Badezimmer-Daten"""
        try:
            # Prüfe ob Konfiguration vorhanden
            if not self.config:
                logger.debug("No bathroom config - skipping data collection")
                return

            if not self.engine or not self.engine.platform:
                logger.debug("No engine/platform available for data collection")
                return

            # Hole Sensor-Werte
            humidity_sensor_id = self.config.get('humidity_sensor_id')
            temp_sensor_id = self.config.get('temperature_sensor_id')

            if not humidity_sensor_id and not temp_sensor_id:
                logger.debug("No sensors configured - skipping data collection")
                return

            humidity = None
            temperature = None

            # Luftfeuchtigkeit
            if humidity_sensor_id:
                state = self.engine.platform.get_state(humidity_sensor_id)
                if state:
                    humidity = self.engine._extract_humidity_value(state)

            # Temperatur
            if temp_sensor_id:
                state = self.engine.platform.get_state(temp_sensor_id)
                if state:
                    temperature = self.engine._extract_temperature_value(state)

            # Speichere nur wenn mindestens ein Wert vorhanden
            if humidity is not None or temperature is not None:
                self.db.add_bathroom_continuous_measurement(
                    humidity=humidity,
                    temperature=temperature
                )
                logger.debug(f"Collected bathroom data: Humidity={humidity}%, Temp={temperature}°C")
            else:
                logger.debug("No sensor values available")

        except Exception as e:
            logger.error(f"Error collecting bathroom data: {e}")

    def get_status(self) -> dict:
        """Gibt den aktuellen Status zurück"""
        return {
            'running': self.running,
            'last_collection': self.last_collection.isoformat() if self.last_collection else None,
            'interval_seconds': self.interval_seconds,
            'config_loaded': self.config is not None,
            'humidity_sensor': self.config.get('humidity_sensor_id') if self.config else None,
            'temperature_sensor': self.config.get('temperature_sensor_id') if self.config else None
        }
