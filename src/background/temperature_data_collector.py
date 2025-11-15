"""
Background Service: Sammelt Temperaturdaten für ML-Training
Läuft kontinuierlich und sammelt alle Thermostat-Daten
"""

import time
from datetime import datetime
from threading import Thread
from loguru import logger
from typing import Dict, Optional

from src.utils.database import Database


class TemperatureDataCollector:
    """
    Sammelt Temperaturdaten für das TemperatureModel
    
    Erfasst:
    - Aktuelle und Zieltemperaturen aller Thermostate
    - Heizstatus (aktiv/inaktiv)
    - Außentemperatur
    - Fensterstatus
    - Anwesenheit
    - Energiepreis-Level
    """
    
    def __init__(self, db: Database | None = None, config: dict | None = None):
        self.db = db or Database()
        self.config = config or {}
        self.interval = self.config.get('data_collection', {}).get('temperature_interval', 300)  # 5 Minuten
        self.running = False
        self.thread = None
        
        # Platform-spezifische Collector
        self.collectors = []
        try:
            if self.config.get('homey', {}).get('enabled'):
                from src.data_collector.homey_collector import HomeyCollector
                homey_config = self.config.get('homey', {})
                homey = HomeyCollector(
                    url=homey_config.get('url'),
                    token=homey_config.get('token')
                )
                self.collectors.append(('homey', homey))
                logger.info("Homey collector initialized for temperature data")
        except Exception as e:
            logger.warning(f"Could not initialize Homey collector: {e}")
            
        try:
            if self.config.get('homeassistant', {}).get('enabled'):
                from src.data_collector.ha_collector import HomeAssistantCollector
                ha_config = self.config.get('homeassistant', {})
                ha = HomeAssistantCollector(
                    url=ha_config.get('url'),
                    token=ha_config.get('token')
                )
                self.collectors.append(('homeassistant', ha))
                logger.info("Home Assistant collector initialized for temperature data")
        except Exception as e:
            logger.warning(f"Could not initialize Home Assistant collector: {e}")
    
    def start(self):
        """Startet Background-Collection"""
        if self.running:
            logger.warning("TemperatureDataCollector already running")
            return
        
        if not self.collectors:
            logger.warning("No collectors available for temperature data collection")
            return
        
        self.running = True
        self.thread = Thread(target=self._collection_loop, daemon=True)
        self.thread.start()
        logger.info(f"TemperatureDataCollector started (interval: {self.interval}s)")
    
    def stop(self):
        """Stoppt Background-Collection"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("TemperatureDataCollector stopped")
    
    def _collection_loop(self):
        """Hauptloop für Datensammlung"""
        while self.running:
            try:
                self._collect_temperature_data()
            except Exception as e:
                logger.error(f"Error in temperature data collection: {e}")
            
            time.sleep(self.interval)
    
    def _collect_temperature_data(self):
        """Sammelt Daten von allen Thermostaten"""
        outdoor_temp = self._get_outdoor_temperature()
        energy_level = self._get_energy_price_level()
        
        for platform_name, collector in self.collectors:
            try:
                devices = collector.get_all_devices()
                
                for device in devices:
                    # Nur Thermostate
                    if not self._is_thermostat(device):
                        continue
                    
                    device_id = device.get('id')
                    device_name = device.get('name', 'Unknown')
                    room_name = device.get('zone', {}).get('name', 'Unknown')
                    
                    # Temperaturen
                    caps = device.get('capabilitiesObj', {})
                    current_temp = caps.get('measure_temperature', {}).get('value')
                    target_temp = caps.get('target_temperature', {}).get('value')
                    
                    if current_temp is None or target_temp is None:
                        continue
                    
                    # Heizstatus
                    heating_active = self._is_heating(device)
                    
                    # Fensterstatus für diesen Raum
                    window_open = self._check_window_status(room_name, devices)
                    
                    # Anwesenheit (TODO: Motion-Sensor)
                    presence = False
                    
                    # Humidity (falls verfügbar)
                    humidity = caps.get('measure_humidity', {}).get('value')
                    
                    # In DB speichern
                    self.db.add_continuous_measurement(
                        device_id=device_id,
                        device_name=device_name,
                        room_name=room_name,
                        current_temp=current_temp,
                        target_temp=target_temp,
                        outdoor_temp=outdoor_temp,
                        humidity=humidity,
                        heating_active=heating_active,
                        presence=presence,
                        window_open=window_open,
                        energy_price_level=energy_level
                    )
                    
                    logger.debug(f"Temperature data: {device_name} - {current_temp}°C / {target_temp}°C (heating: {heating_active})")
                    
            except Exception as e:
                logger.error(f"Error collecting from {platform_name}: {e}")
    
    def _is_thermostat(self, device: Dict) -> bool:
        """Prüft ob Gerät ein Thermostat ist"""
        device_class = device.get('class', '').lower()
        capabilities = device.get('capabilities', [])
        
        # Homey: class=thermostat
        if 'thermostat' in device_class or 'heater' in device_class:
            return True
        
        # Capability-basiert
        if 'target_temperature' in capabilities and 'measure_temperature' in capabilities:
            return True
        
        return False
    
    def _is_heating(self, device: Dict) -> bool:
        """Detektiert ob Gerät gerade heizt"""
        caps = device.get('capabilitiesObj', {})
        
        # Direkte Heizstatus-Capability
        heating_status = caps.get('heating', {}).get('value')
        if heating_status is not None:
            return bool(heating_status)
        
        # Indirekt: Wenn target > current + threshold
        current = caps.get('measure_temperature', {}).get('value')
        target = caps.get('target_temperature', {}).get('value')
        
        if current is not None and target is not None:
            return target > (current + 0.5)  # 0.5°C Hysterese
        
        return False
    
    def _check_window_status(self, room_name: str, all_devices: list) -> bool:
        """Prüft ob Fenster in diesem Raum offen ist"""
        for device in all_devices:
            device_room = device.get('zone', {}).get('name', '')
            if device_room != room_name:
                continue
            
            device_class = device.get('class', '').lower()
            if 'sensor' in device_class or 'contactsensor' in device_class:
                caps = device.get('capabilitiesObj', {})
                alarm_contact = caps.get('alarm_contact', {}).get('value')
                
                # Homey: alarm_contact=True bedeutet Fenster offen
                if alarm_contact is True:
                    return True
        
        return False
    
    def _get_outdoor_temperature(self) -> Optional[float]:
        """Holt Außentemperatur"""
        try:
            # TODO: Von Weather Collector holen
            # Für jetzt: Dummy-Wert
            from src.data_collector.weather_collector import WeatherCollector
            weather = WeatherCollector(config=self.config)
            data = weather.get_current_weather()
            return data.get('temperature')
        except Exception as e:
            logger.debug(f"Could not get outdoor temperature: {e}")
            return None
    
    def _get_energy_price_level(self) -> int:
        """Holt Energiepreis-Level (1=niedrig, 2=mittel, 3=hoch)"""
        try:
            # TODO: Von Energy Price Collector holen
            # Für jetzt: Default mittel
            return 2
        except Exception as e:
            logger.debug(f"Could not get energy price level: {e}")
            return 2
    
    def get_stats(self) -> Dict:
        """Gibt Statistiken zurück"""
        return {
            'running': self.running,
            'interval': self.interval,
            'collectors_count': len(self.collectors),
            'total_measurements': self.db.get_continuous_measurements_count()
        }


def start_temperature_collector(config: dict | None = None):
    """Convenience-Funktion zum Starten"""
    collector = TemperatureDataCollector(config=config)
    collector.start()
    return collector


if __name__ == '__main__':
    # Test
    from src.utils.config_loader import ConfigLoader
    
    config = ConfigLoader()
    collector = TemperatureDataCollector(config=config.config)
    
    print("Starting temperature data collector...")
    collector.start()
    
    try:
        while True:
            time.sleep(10)
            stats = collector.get_stats()
            print(f"Stats: {stats}")
    except KeyboardInterrupt:
        print("\nStopping...")
        collector.stop()
