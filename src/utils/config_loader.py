"""Konfiguration laden und verwalten"""

import yaml
import os
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv


class ConfigLoader:
    """Lädt und verwaltet Konfiguration aus YAML und .env Dateien"""

    def __init__(self, config_path: str = None):
        # Load environment variables
        load_dotenv()

        # Set config path
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "config" / "config.yaml"

        self.config_path = Path(config_path)
        self.config = self._load_config()
        self._merge_env_variables()

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
            self.config['external_data']['weather']['api_key'] = os.getenv('WEATHER_API_KEY')

        # Energy API
        if os.getenv('ENERGY_API_KEY'):
            self.config['external_data']['energy_prices']['api_key'] = os.getenv('ENERGY_API_KEY')
        if os.getenv('ENERGY_PROVIDER'):
            self.config['external_data']['energy_prices']['provider'] = os.getenv('ENERGY_PROVIDER')

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
