"""
Heating Data Collector - Kontinuierliche Heizungsdaten-Sammlung

Sammelt alle 15 Minuten Daten von allen Heizgeräten für Analytics:
- Aktuelle/Zieltemperatur
- Heizstatus
- Außentemperatur
- Luftfeuchtigkeit
"""

import threading
import time
from datetime import datetime
from typing import Optional
from loguru import logger
from src.utils.database import Database


class HeatingDataCollector:
    """Sammelt kontinuierlich Heizungsdaten für Analytics"""

    def __init__(self, engine=None, interval_seconds: int = 900):  # 15 Minuten = 900 Sekunden
        """
        Args:
            engine: DecisionEngine Instanz für Zugriff auf Platform
            interval_seconds: Sammel-Intervall in Sekunden (default: 900 = 15 Min)
        """
        self.engine = engine
        self.interval_seconds = interval_seconds
        self.running = False
        self.thread = None
        self.last_collection = None
        self.db = Database()

        logger.info(f"Heating Data Collector initialized ({interval_seconds}s interval)")

    def start(self):
        """Startet die kontinuierliche Datensammlung"""
        if self.running:
            logger.warning("Heating Data Collector is already running")
            return

        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        logger.info(f"Heating Data Collector started (collects every {self.interval_seconds}s)")

    def stop(self):
        """Stoppt die kontinuierliche Datensammlung"""
        if not self.running:
            return

        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Heating Data Collector stopped")

    def _run(self):
        """Haupt-Loop für kontinuierliche Datensammlung"""
        while self.running:
            try:
                self._collect_data()
                self.last_collection = datetime.now()
            except Exception as e:
                logger.error(f"Error in heating data collection: {e}")

            # Warte bis zum nächsten Intervall
            time.sleep(self.interval_seconds)

    def _collect_data(self):
        """Sammelt aktuelle Heizungsdaten von allen Geräten"""
        if not self.engine or not self.engine.platform:
            logger.debug("No engine/platform available for heating data collection")
            return

        try:
            # Hole alle Heizgeräte
            all_states = self.engine.platform.get_states()
            heating_devices = []

            # Filtere nach Thermostaten und Heizgeräten
            for device in all_states:
                device_type = device.get('class', '').lower()
                capabilities = device.get('capabilitiesObj', {})

                # Prüfe ob es ein Thermostat oder Heizgerät ist
                if ('thermostat' in device_type or
                    'heater' in device_type or
                    'target_temperature' in capabilities or
                    'measure_temperature' in capabilities):
                    heating_devices.append(device)

            if not heating_devices:
                logger.debug("No heating devices found for data collection")
                return

            # Hole Außentemperatur einmal für alle Geräte
            outdoor_temp = self._get_outdoor_temperature()

            # Sammle Daten von jedem Heizgerät
            collected_count = 0
            for device in heating_devices:
                try:
                    observation_id = self._collect_device_data(device, outdoor_temp)
                    if observation_id:
                        collected_count += 1
                except Exception as e:
                    logger.error(f"Error collecting data from device {device.get('id')}: {e}")

            logger.debug(f"Collected heating data from {collected_count}/{len(heating_devices)} devices")

        except Exception as e:
            logger.error(f"Error in heating data collection: {e}")

    def _collect_device_data(self, device: dict, outdoor_temp: Optional[float]) -> Optional[int]:
        """Sammelt Daten von einem einzelnen Heizgerät"""
        device_id = device.get('id')
        if not device_id:
            return None

        # Extrahiere Daten
        capabilities = device.get('capabilitiesObj', {})

        # Aktuelle Temperatur
        current_temp = None
        if 'measure_temperature' in capabilities:
            temp_cap = capabilities['measure_temperature']
            current_temp = temp_cap.get('value')

        # Zieltemperatur
        target_temp = None
        if 'target_temperature' in capabilities:
            target_cap = capabilities['target_temperature']
            target_temp = target_cap.get('value')

        # Heizstatus (ist das Gerät gerade am Heizen?)
        is_heating = False
        if 'onoff' in capabilities:
            is_heating = capabilities['onoff'].get('value', False)

        # Alternativ: prüfe ob target > current (typisch für Thermostate)
        if not is_heating and current_temp and target_temp:
            # Wenn Zieltemp > aktuelle Temp + 0.5°C => vermutlich am Heizen
            is_heating = target_temp > (current_temp + 0.5)

        # Luftfeuchtigkeit (optional)
        humidity = None
        if 'measure_humidity' in capabilities:
            humidity = capabilities['measure_humidity'].get('value')

        # Raum-Name aus Zone
        room_name = None
        zone_id = device.get('zone')
        if zone_id and hasattr(self.engine, 'platform'):
            # Versuche Raum-Name zu holen
            try:
                zones = self.engine.platform.get_zones()
                for zone in zones:
                    if zone.get('id') == zone_id:
                        room_name = zone.get('name')
                        break
            except:
                pass

        # Speichere in Datenbank
        observation_id = self.db.add_heating_observation(
            device_id=device_id,
            room_name=room_name,
            current_temp=current_temp,
            target_temp=target_temp,
            is_heating=is_heating,
            outdoor_temp=outdoor_temp,
            humidity=humidity,
            power_percentage=None  # Könnte später von capable_dim oder measure_power kommen
        )

        return observation_id

    def _get_outdoor_temperature(self) -> Optional[float]:
        """Holt die aktuelle Außentemperatur"""
        try:
            # Versuche aus external_data (Weather-Collector)
            weather_data = self.db.get_latest_external_data('weather')
            if weather_data:
                data = weather_data.get('data', {})
                outdoor_temp = data.get('temperature') or data.get('temp')
                if outdoor_temp is not None:
                    return float(outdoor_temp)

            # Fallback: Suche nach Outdoor-Sensor in Geräten
            if self.engine and self.engine.platform:
                all_states = self.engine.platform.get_states()
                for device in all_states:
                    device_name = device.get('name', '').lower()
                    if 'outdoor' in device_name or 'außen' in device_name or 'outside' in device_name:
                        caps = device.get('capabilitiesObj', {})
                        if 'measure_temperature' in caps:
                            temp = caps['measure_temperature'].get('value')
                            if temp is not None:
                                return float(temp)

        except Exception as e:
            logger.debug(f"Could not get outdoor temperature: {e}")

        return None

    def get_status(self) -> dict:
        """Gibt den aktuellen Status des Collectors zurück"""
        return {
            'running': self.running,
            'interval_seconds': self.interval_seconds,
            'last_collection': self.last_collection.isoformat() if self.last_collection else None
        }
