"""
Tests für Platform-Collectors
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.data_collector.homey_collector import HomeyCollector
from src.data_collector.ha_collector import HomeAssistantCollector


class TestHomeyCollector:
    """Tests für HomeyCollector"""

    @pytest.fixture
    def mock_homey_response(self):
        """Mock-Response von Homey API"""
        return [
            {
                'id': 'device-1',
                'name': 'Living Room Light',
                'class': 'light',
                'zone': {'id': 'zone-1', 'name': 'Living Room'},
                'capabilitiesObj': {
                    'onoff': {'value': True},
                    'dim': {'value': 0.8}
                },
                'capabilities': ['onoff', 'dim']
            },
            {
                'id': 'device-2',
                'name': 'Bedroom Thermostat',
                'class': 'thermostat',
                'zone': {'id': 'zone-2', 'name': 'Bedroom'},
                'capabilitiesObj': {
                    'target_temperature': {'value': 21.0},
                    'measure_temperature': {'value': 20.5}
                },
                'capabilities': ['target_temperature', 'measure_temperature']
            }
        ]

    @patch('src.data_collector.homey_collector.requests.get')
    def test_get_all_devices(self, mock_get, mock_homey_response):
        """Test: Alle Geräte können abgerufen werden"""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_homey_response
        
        collector = HomeyCollector(url='http://test.local', token='test-token')
        devices = collector.get_all_devices()
        
        assert len(devices) == 2
        assert devices[0]['name'] == 'Living Room Light'
        assert devices[1]['class'] == 'thermostat'

    @patch('src.data_collector.homey_collector.requests.get')
    def test_get_device_by_id(self, mock_get, mock_homey_response):
        """Test: Einzelnes Gerät abrufen"""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_homey_response[0]
        
        collector = HomeyCollector(url='http://test.local', token='test-token')
        device = collector.get_device('device-1')
        
        assert device['id'] == 'device-1'
        assert device['class'] == 'light'

    @patch('src.data_collector.homey_collector.requests.get')
    def test_connection_error_handling(self, mock_get):
        """Test: Fehlerbehandlung bei Verbindungsproblemen"""
        mock_get.side_effect = Exception("Connection failed")
        
        collector = HomeyCollector(url='http://test.local', token='test-token')
        devices = collector.get_all_devices()
        
        assert devices == []  # Sollte leere Liste zurückgeben

    @patch('src.data_collector.homey_collector.requests.post')
    def test_control_device(self, mock_post):
        """Test: Gerät steuern"""
        mock_post.return_value.status_code = 200
        
        collector = HomeyCollector(url='http://test.local', token='test-token')
        result = collector.set_capability('device-1', 'onoff', True)
        
        assert result is True
        mock_post.assert_called_once()

    @patch('src.data_collector.homey_collector.requests.get')
    def test_get_zones(self, mock_get):
        """Test: Zonen abrufen"""
        mock_zones = [
            {'id': 'zone-1', 'name': 'Living Room'},
            {'id': 'zone-2', 'name': 'Bedroom'}
        ]
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_zones
        
        collector = HomeyCollector(url='http://test.local', token='test-token')
        zones = collector.get_zones()
        
        assert len(zones) == 2
        assert zones[0]['name'] == 'Living Room'


class TestHomeAssistantCollector:
    """Tests für HomeAssistantCollector"""

    @pytest.fixture
    def mock_ha_response(self):
        """Mock-Response von Home Assistant API"""
        return [
            {
                'entity_id': 'light.living_room',
                'state': 'on',
                'attributes': {
                    'friendly_name': 'Living Room Light',
                    'brightness': 200
                }
            },
            {
                'entity_id': 'climate.bedroom',
                'state': 'heat',
                'attributes': {
                    'friendly_name': 'Bedroom Thermostat',
                    'current_temperature': 20.5,
                    'temperature': 21.0
                }
            }
        ]

    @patch('src.data_collector.ha_collector.requests.get')
    def test_get_states(self, mock_get, mock_ha_response):
        """Test: States abrufen"""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_ha_response
        
        collector = HomeAssistantCollector(url='http://test-ha.local:8123', token='test-token')
        states = collector.get_states()
        
        assert len(states) == 2
        assert states[0]['entity_id'] == 'light.living_room'

    @patch('src.data_collector.ha_collector.requests.get')
    def test_get_entity_state(self, mock_get, mock_ha_response):
        """Test: Einzelner Entity-State"""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_ha_response[0]
        
        collector = HomeAssistantCollector(url='http://test-ha.local:8123', token='test-token')
        state = collector.get_state('light.living_room')
        
        assert state['state'] == 'on'
        assert state['attributes']['brightness'] == 200

    @patch('src.data_collector.ha_collector.requests.post')
    def test_call_service(self, mock_post):
        """Test: Service aufrufen"""
        mock_post.return_value.status_code = 200
        
        collector = HomeAssistantCollector(url='http://test-ha.local:8123', token='test-token')
        result = collector.call_service('light', 'turn_on', {'entity_id': 'light.living_room'})
        
        assert result is True
        mock_post.assert_called_once()

    @patch('src.data_collector.ha_collector.requests.get')
    def test_authentication_header(self, mock_get, mock_ha_response):
        """Test: Authorization Header wird korrekt gesetzt"""
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_ha_response
        
        collector = HomeAssistantCollector(url='http://test-ha.local:8123', token='my-secret-token')
        collector.get_states()
        
        # Prüfe dass Authorization Header gesetzt wurde
        call_headers = mock_get.call_args[1]['headers']
        assert 'Authorization' in call_headers
        assert call_headers['Authorization'] == 'Bearer my-secret-token'

    @patch('src.data_collector.ha_collector.requests.get')
    def test_connection_error(self, mock_get):
        """Test: Fehlerbehandlung"""
        mock_get.side_effect = Exception("Connection failed")
        
        collector = HomeAssistantCollector(url='http://test-ha.local:8123', token='test-token')
        states = collector.get_states()
        
        assert states == []
