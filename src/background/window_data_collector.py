"""
Window Data Collector - Kontinuierliche Fenster-Status-Sammlung

Sammelt alle 60 Sekunden Daten von allen Fenstern/Türen für Heizungsoptimierung:
- Fenster offen/geschlossen
- Raum-Zuordnung
- Alarme
"""

import threading
import time
from datetime import datetime
from typing import Optional
from loguru import logger
from src.utils.database import Database


class WindowDataCollector:
    """Sammelt kontinuierlich Fenster-Status für Heizungsoptimierung"""

    def __init__(self, engine=None, interval_seconds: int = 60):  # 60 Sekunden = 1 Minute
        """
        Args:
            engine: DecisionEngine Instanz für Zugriff auf Platform
            interval_seconds: Sammel-Intervall in Sekunden (default: 60)
        """
        self.engine = engine
        self.interval_seconds = interval_seconds
        self.running = False
        self.thread = None
        self.last_collection = None
        self.db = Database()

        logger.info(f"Window Data Collector initialized ({interval_seconds}s interval)")

    def start(self):
        """Startet die kontinuierliche Datensammlung"""
        if self.running:
            logger.warning("Window Data Collector is already running")
            return

        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        logger.info(f"Window Data Collector started (collects every {self.interval_seconds}s)")

    def stop(self):
        """Stoppt die kontinuierliche Datensammlung"""
        if not self.running:
            return

        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Window Data Collector stopped")

    def _run(self):
        """Haupt-Loop für kontinuierliche Datensammlung"""
        while self.running:
            try:
                self._collect_data()
                self.last_collection = datetime.now()
            except Exception as e:
                logger.error(f"Error in window data collection: {e}")

            # Warte bis zum nächsten Intervall
            time.sleep(self.interval_seconds)

    def _collect_data(self):
        """Sammelt aktuellen Status von allen Fenstern/Türen"""
        if not self.engine or not self.engine.platform:
            logger.debug("No engine/platform available for window data collection")
            return

        try:
            # Hole alle Geräte
            all_states = self.engine.platform.get_states()
            window_devices = []

            # Filtere nach Fenster-Kontakten und Türen
            for device in all_states:
                # Skip wenn device kein Dictionary ist
                if not isinstance(device, dict):
                    continue

                device_class = device.get('class', '').lower()
                device_name = device.get('name', '').lower()
                capabilities = device.get('capabilitiesObj', {})

                # Prüfe ob es ein Fenster/Tür-Sensor ist
                if ('sensor' in device_class and
                    ('alarm_contact' in capabilities or 'windowcoverings_state' in capabilities)) or \
                   ('window' in device_name or 'fenster' in device_name or
                    'door' in device_name or 'tür' in device_name or 'tur' in device_name):
                    window_devices.append(device)

            if not window_devices:
                logger.debug("No window devices found for data collection")
                return

            # Sammle Daten von jedem Fenster/Tür
            collected_count = 0
            for device in window_devices:
                try:
                    observation_id = self._collect_device_data(device)
                    if observation_id:
                        collected_count += 1
                except Exception as e:
                    logger.error(f"Error collecting data from device {device.get('id')}: {e}")

            logger.debug(f"Collected window data from {collected_count}/{len(window_devices)} devices")

        except Exception as e:
            logger.error(f"Error in window data collection: {e}")

    def _collect_device_data(self, device: dict) -> Optional[int]:
        """Sammelt Daten von einem einzelnen Fenster/Tür"""
        device_id = device.get('id')
        if not device_id:
            return None

        device_name = device.get('name', 'Unbekannt')
        capabilities = device.get('capabilitiesObj', {})

        # Status: offen oder geschlossen
        is_open = False
        contact_alarm = False

        # Prüfe alarm_contact capability (typisch für Fenster/Tür-Sensoren)
        if 'alarm_contact' in capabilities:
            # alarm_contact: true = offen, false = geschlossen
            alarm_value = capabilities['alarm_contact'].get('value')
            if alarm_value is not None:
                is_open = bool(alarm_value)
                contact_alarm = is_open

        # Alternative: windowcoverings_state (für Rollläden/Jalousien)
        elif 'windowcoverings_state' in capabilities:
            state = capabilities['windowcoverings_state'].get('value', 'idle')
            is_open = (state == 'up')  # up = offen

        # Alternative: onoff (für manche Sensoren)
        elif 'onoff' in capabilities:
            is_open = capabilities['onoff'].get('value', False)

        # Raum-Name aus Zone
        room_name = None
        zone_id = device.get('zone')
        if zone_id and hasattr(self.engine, 'platform'):
            try:
                zones = self.engine.platform.get_zones()
                for zone in zones:
                    if zone.get('id') == zone_id:
                        room_name = zone.get('name')
                        break
            except:
                pass

        # Speichere in Datenbank
        observation_id = self.db.add_window_observation(
            device_id=device_id,
            device_name=device_name,
            room_name=room_name,
            is_open=is_open,
            contact_alarm=contact_alarm
        )

        return observation_id

    def get_status(self) -> dict:
        """Gibt den aktuellen Status des Collectors zurück"""
        return {
            'running': self.running,
            'interval_seconds': self.interval_seconds,
            'last_collection': self.last_collection.isoformat() if self.last_collection else None
        }
