"""Konfiguration laden und verwalten"""

import yaml
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from loguru import logger

try:
    from pydantic import ValidationError
    from .config_schema import KISystemConfig
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    logger.warning("Pydantic not available - config validation disabled. Install with: pip install pydantic")


class ConfigValidationError(Exception):
    """Custom exception for configuration validation errors"""
    pass


class ConfigLoader:
    """Lädt und verwaltet Konfiguration aus YAML und .env Dateien"""

    def __init__(self, config_path: str = None, validate: bool = True):
        """
        Initialize ConfigLoader

        Args:
            config_path: Path to config.yaml file
            validate: Whether to validate config with Pydantic (default: True)
        """
        # Load environment variables
        load_dotenv()

        # Set config path
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "config" / "config.yaml"

        self.config_path = Path(config_path)
        self.config = self._load_config()
        self._merge_env_variables()

        # Validate configuration if requested and Pydantic is available
        if validate and PYDANTIC_AVAILABLE:
            self._validate_config()

    def _load_config(self) -> Dict[str, Any]:
        """Lädt die YAML-Konfiguration"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(self.config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def _merge_env_variables(self):
        """Überschreibt Config-Werte mit Umgebungsvariablen"""
        # Platform Type
        if os.getenv('PLATFORM_TYPE'):
            if 'platform' not in self.config:
                self.config['platform'] = {}
            self.config['platform']['type'] = os.getenv('PLATFORM_TYPE')

        # Home Assistant
        if os.getenv('HA_URL'):
            if 'home_assistant' not in self.config:
                self.config['home_assistant'] = {}
            self.config['home_assistant']['url'] = os.getenv('HA_URL')
        if os.getenv('HA_TOKEN'):
            if 'home_assistant' not in self.config:
                self.config['home_assistant'] = {}
            self.config['home_assistant']['token'] = os.getenv('HA_TOKEN')

        # Homey
        if os.getenv('HOMEY_URL'):
            if 'homey' not in self.config:
                self.config['homey'] = {}
            self.config['homey']['url'] = os.getenv('HOMEY_URL')
        if os.getenv('HOMEY_TOKEN'):
            if 'homey' not in self.config:
                self.config['homey'] = {}
            self.config['homey']['token'] = os.getenv('HOMEY_TOKEN')

        # Weather API
        if os.getenv('WEATHER_API_KEY'):
            if 'external_data' not in self.config:
                self.config['external_data'] = {}
            if 'weather' not in self.config['external_data']:
                self.config['external_data']['weather'] = {}
            self.config['external_data']['weather']['api_key'] = os.getenv('WEATHER_API_KEY')

        # Energy API
        if os.getenv('ENERGY_API_KEY'):
            if 'external_data' not in self.config:
                self.config['external_data'] = {}
            if 'energy_prices' not in self.config['external_data']:
                self.config['external_data']['energy_prices'] = {}
            self.config['external_data']['energy_prices']['api_key'] = os.getenv('ENERGY_API_KEY')
        if os.getenv('ENERGY_PROVIDER'):
            if 'external_data' not in self.config:
                self.config['external_data'] = {}
            if 'energy_prices' not in self.config['external_data']:
                self.config['external_data']['energy_prices'] = {}
            self.config['external_data']['energy_prices']['provider'] = os.getenv('ENERGY_PROVIDER')

    def _validate_config(self):
        """
        Validates configuration using Pydantic schema

        Raises:
            ConfigValidationError: If configuration is invalid
        """
        try:
            # Validate config against Pydantic schema
            validated_config = KISystemConfig(**self.config)
            logger.info("Configuration validated successfully")

            # Update config with validated data (ensures all defaults are set)
            self.config = validated_config.model_dump(mode='python')

        except ValidationError as e:
            # Format validation errors nicely
            error_messages = []
            for error in e.errors():
                location = " -> ".join(str(loc) for loc in error['loc'])
                message = error['msg']
                error_messages.append(f"  • {location}: {message}")

            error_text = "\n".join([
                "Configuration validation failed:",
                *error_messages,
                "",
                "Please check your config/config.yaml file and .env variables."
            ])

            logger.error(error_text)
            raise ConfigValidationError(error_text) from e

        except Exception as e:
            logger.error(f"Unexpected error during config validation: {e}")
            raise ConfigValidationError(f"Config validation error: {e}") from e

    def get(self, key: str, default: Any = None) -> Any:
        """
        Holt einen Config-Wert mit Dot-Notation
        Beispiel: config.get('home_assistant.url')
        """
        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default

        return value

    def __getitem__(self, key: str) -> Any:
        """Ermöglicht dict-ähnlichen Zugriff"""
        return self.config[key]

    def get_all(self) -> Dict[str, Any]:
        """Gibt die gesamte Konfiguration zurück"""
        return self.config

    def update(self, key: str, value: Any) -> bool:
        """
        Aktualisiert einen Config-Wert mit Dot-Notation und speichert in YAML
        Beispiel: config.update('decision_engine.mode', 'learning')

        Returns:
            bool: True wenn erfolgreich, False bei Fehler
        """
        keys = key.split('.')
        config_ref = self.config

        # Navigate to parent
        for k in keys[:-1]:
            if k not in config_ref:
                config_ref[k] = {}
            config_ref = config_ref[k]

        # Set value
        config_ref[keys[-1]] = value

        # Save to YAML
        return self._save_config()

    def _save_config(self) -> bool:
        """Speichert die aktuelle Konfiguration in die YAML-Datei"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
            return True
        except Exception as e:
            print(f"Fehler beim Speichern der Config: {e}")
            return False
