"""Abstraktes Interface für Smart Home Plattformen"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any


class SmartHomeCollector(ABC):
    """
    Abstraktes Base-Interface für Smart Home Plattformen
    Implementierungen: Home Assistant, Homey Pro, etc.
    """

    @abstractmethod
    def test_connection(self) -> bool:
        """
        Testet die Verbindung zur Plattform

        Returns:
            True wenn Verbindung erfolgreich, sonst False
        """
        pass

    @abstractmethod
    def get_state(self, entity_id: str) -> Optional[Dict]:
        """
        Holt den Status einer Entity/Device

        Args:
            entity_id: ID des Devices

        Returns:
            Dictionary mit state, attributes, etc. oder None
        """
        pass

    @abstractmethod
    def get_states(self, entity_ids: List[str] = None) -> Dict[str, Dict]:
        """
        Holt Status mehrerer Entities

        Args:
            entity_ids: Liste von Entity-IDs (None = alle)

        Returns:
            Dictionary: entity_id -> state_data
        """
        pass

    @abstractmethod
    def turn_on(self, entity_id: str, **kwargs) -> bool:
        """
        Schaltet ein Device ein

        Args:
            entity_id: ID des Devices
            **kwargs: Zusätzliche Parameter (brightness, etc.)

        Returns:
            True wenn erfolgreich
        """
        pass

    @abstractmethod
    def turn_off(self, entity_id: str) -> bool:
        """
        Schaltet ein Device aus

        Args:
            entity_id: ID des Devices

        Returns:
            True wenn erfolgreich
        """
        pass

    @abstractmethod
    def set_temperature(self, entity_id: str, temperature: float) -> bool:
        """
        Setzt Zieltemperatur für Thermostat

        Args:
            entity_id: ID des Thermostats
            temperature: Zieltemperatur in °C

        Returns:
            True wenn erfolgreich
        """
        pass

    @abstractmethod
    def set_hvac_mode(self, entity_id: str, hvac_mode: str) -> bool:
        """
        Setzt HVAC-Modus (heat, cool, auto, off)

        Args:
            entity_id: ID des Thermostats
            hvac_mode: Gewünschter Modus

        Returns:
            True wenn erfolgreich
        """
        pass

    @abstractmethod
    def get_all_entities(self, domain: str = None) -> List[str]:
        """
        Holt alle verfügbaren Entity-IDs

        Args:
            domain: Optional Domain-Filter (light, sensor, climate, etc.)

        Returns:
            Liste von Entity-IDs
        """
        pass

    @abstractmethod
    def call_service(self, domain: str, service: str, entity_id: str, **kwargs) -> bool:
        """
        Ruft einen Service auf (generisch)

        Args:
            domain: Domain (z.B. 'light', 'climate')
            service: Service-Name (z.B. 'turn_on')
            entity_id: Ziel-Entity
            **kwargs: Service-Parameter

        Returns:
            True wenn erfolgreich
        """
        pass

    def get_platform_name(self) -> str:
        """Gibt den Namen der Plattform zurück"""
        return self.__class__.__name__.replace('Collector', '')

    def normalize_entity_id(self, entity_id: str, domain: str = None) -> str:
        """
        Normalisiert Entity-IDs plattformübergreifend

        Überschreibe diese Methode wenn die Plattform ein anderes Format nutzt
        """
        return entity_id

    def supports_capability(self, capability: str) -> bool:
        """
        Prüft ob die Plattform eine Fähigkeit unterstützt

        Args:
            capability: z.B. 'scenes', 'automations', 'history', etc.

        Returns:
            True wenn unterstützt
        """
        # Default-Implementierung
        supported = ['basic_control', 'state_query']
        return capability in supported
