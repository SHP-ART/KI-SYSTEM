"""Factory für Smart Home Platform Selection"""

from typing import Optional
from loguru import logger

from .base_collector import SmartHomeCollector
from .ha_collector import HomeAssistantCollector
from .homey_collector import HomeyCollector


class PlatformFactory:
    """
    Factory zum Erstellen der richtigen Smart Home Platform-Instanz
    basierend auf Konfiguration
    """

    PLATFORMS = {
        'homeassistant': HomeAssistantCollector,
        'home_assistant': HomeAssistantCollector,
        'ha': HomeAssistantCollector,
        'homey': HomeyCollector,
        'homey_pro': HomeyCollector,
    }

    @staticmethod
    def create_collector(platform: str, url: Optional[str], token: Optional[str]) -> Optional[SmartHomeCollector]:
        """
        Erstellt den passenden Collector für die gewählte Plattform

        Args:
            platform: Platform-Name ('homeassistant', 'homey', etc.)
            url: URL der Platform (kann None sein)
            token: Access Token (kann None sein)

        Returns:
            SmartHomeCollector Instanz oder None bei Fehler
        """
        # Validierung
        if not url or not token:
            logger.error(f"Missing URL or token for platform: {platform}")
            logger.error(f"URL: {'✓' if url else '✗'}, Token: {'✓' if token else '✗'}")
            return None

        platform_lower = platform.lower().replace(' ', '_')

        collector_class = PlatformFactory.PLATFORMS.get(platform_lower)

        if not collector_class:
            logger.error(f"Unknown platform: {platform}")
            logger.info(f"Available platforms: {', '.join(PlatformFactory.PLATFORMS.keys())}")
            return None

        try:
            collector = collector_class(url, token)
            logger.info(f"Created {collector.get_platform_name()} collector")
            return collector

        except Exception as e:
            logger.error(f"Failed to create collector for {platform}: {e}")
            return None

    @staticmethod
    def get_available_platforms() -> list:
        """Gibt Liste der verfügbaren Plattformen zurück"""
        return list(set(PlatformFactory.PLATFORMS.values()))

    @staticmethod
    def get_platform_names() -> list:
        """Gibt Liste der Platform-Namen zurück"""
        return sorted(set([
            'Home Assistant',
            'Homey Pro'
        ]))
