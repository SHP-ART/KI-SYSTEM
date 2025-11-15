"""
Pytest Configuration & Shared Fixtures
"""

import pytest
import sys
from pathlib import Path

# Füge src zum Python-Path hinzu
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.database import Database
from src.utils.config_loader import ConfigLoader


@pytest.fixture
def test_db():
    """Temporäre Test-Datenbank"""
    db = Database(db_path=":memory:")  # In-Memory-DB für Tests
    yield db
    db.close()


@pytest.fixture
def test_config():
    """Test-Konfiguration"""
    return {
        'platform': 'homey',
        'homey': {
            'url': 'http://test-homey.local',
            'token': 'test-token-12345',
            'enabled': True
        },
        'homeassistant': {
            'url': 'http://test-ha.local:8123',
            'token': 'test-ha-token',
            'enabled': False
        },
        'decision_engine': {
            'mode': 'learning',
            'confidence_threshold': 0.7
        },
        'models': {
            'lighting': {
                'type': 'random_forest',
                'min_training_samples': 50
            },
            'temperature': {
                'type': 'gradient_boosting',
                'min_training_samples': 100
            }
        },
        'data_collection': {
            'interval_seconds': 300,
            'sensors': {
                'temperature': ['sensor.temperature_bedroom'],
                'humidity': ['sensor.humidity_bathroom']
            }
        }
    }


@pytest.fixture
def sample_lighting_data():
    """Sample-Daten für Lighting Model Tests"""
    return [
        {
            'timestamp': '2025-11-15 08:00:00',
            'device_id': 'light-1',
            'state': 'on',
            'brightness': 80,
            'hour_of_day': 8,
            'outdoor_light': 20.0,
            'presence': True
        },
        {
            'timestamp': '2025-11-15 12:00:00',
            'device_id': 'light-1',
            'state': 'off',
            'brightness': 0,
            'hour_of_day': 12,
            'outdoor_light': 80.0,
            'presence': False
        },
        {
            'timestamp': '2025-11-15 20:00:00',
            'device_id': 'light-1',
            'state': 'on',
            'brightness': 100,
            'hour_of_day': 20,
            'outdoor_light': 5.0,
            'presence': True
        }
    ]


@pytest.fixture
def sample_temperature_data():
    """Sample-Daten für Temperature Model Tests"""
    return [
        {
            'timestamp': '2025-11-15 08:00:00',
            'device_id': 'thermo-1',
            'current_temperature': 20.5,
            'target_temperature': 21.0,
            'outdoor_temperature': 10.0,
            'heating_active': True,
            'presence': True,
            'window_open': False
        },
        {
            'timestamp': '2025-11-15 12:00:00',
            'device_id': 'thermo-1',
            'current_temperature': 21.0,
            'target_temperature': 21.0,
            'outdoor_temperature': 12.0,
            'heating_active': False,
            'presence': False,
            'window_open': False
        },
        {
            'timestamp': '2025-11-15 18:00:00',
            'device_id': 'thermo-1',
            'current_temperature': 19.5,
            'target_temperature': 21.0,
            'outdoor_temperature': 8.0,
            'heating_active': True,
            'presence': True,
            'window_open': False
        }
    ]
