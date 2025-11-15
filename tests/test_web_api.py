"""
Tests für Web-API Endpoints
"""

import pytest
import json
from unittest.mock import Mock, patch
from src.web.app import WebInterface
from src.utils.database import Database


@pytest.fixture
def test_app(test_config, test_db):
    """Flask Test Client"""
    web = WebInterface(test_config, test_db)
    web.app.config['TESTING'] = True
    with web.app.test_client() as client:
        yield client


class TestHealthEndpoints:
    """Tests für Health & Status Endpoints"""

    def test_health_check(self, test_app):
        """Test: /health endpoint"""
        response = test_app.get('/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'ok'

    def test_status(self, test_app):
        """Test: /api/status endpoint"""
        response = test_app.get('/api/status')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'system' in data
        assert 'database' in data


class TestMLEndpoints:
    """Tests für Machine Learning Endpoints"""

    def test_ml_status(self, test_app):
        """Test: /api/ml/status endpoint"""
        response = test_app.get('/api/ml/status')
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert 'lighting' in data
        assert 'temperature' in data
        assert 'data_count' in data['lighting']
        assert 'data_count' in data['temperature']

    @patch('src.models.lighting_model.LightingModel.predict')
    def test_lighting_prediction(self, mock_predict, test_app):
        """Test: /api/ml/lighting/predict endpoint"""
        mock_predict.return_value = (True, 0.8)  # (should_turn_on, brightness)
        
        payload = {
            'hour_of_day': 18,
            'outdoor_light': 100,
            'presence': True,
            'motion_detected': True
        }
        
        response = test_app.post('/api/ml/lighting/predict',
                                json=payload,
                                content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'should_turn_on' in data
        assert 'brightness' in data

    @patch('src.models.temperature_model.TemperatureModel.predict')
    def test_temperature_prediction(self, mock_predict, test_app):
        """Test: /api/ml/temperature/predict endpoint"""
        mock_predict.return_value = 21.5
        
        payload = {
            'current_temperature': 20.0,
            'outdoor_temperature': 5.0,
            'presence': True,
            'time_of_day': '18:00'
        }
        
        response = test_app.post('/api/ml/temperature/predict',
                                json=payload,
                                content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'predicted_temperature' in data


class TestHeatingEndpoints:
    """Tests für Heizungs-Endpoints"""

    def test_heating_status(self, test_app):
        """Test: /api/heating/status endpoint"""
        response = test_app.get('/api/heating/status')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, dict)

    def test_heating_analytics(self, test_app):
        """Test: /api/heating/analytics endpoint"""
        response = test_app.get('/api/heating/analytics')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, dict)

    def test_frost_protection_status(self, test_app):
        """Test: /api/heating/frost-protection endpoint"""
        response = test_app.get('/api/heating/frost-protection')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'enabled' in data or 'status' in data


class TestBathroomEndpoints:
    """Tests für Badezimmer-Endpoints"""

    def test_bathroom_status(self, test_app):
        """Test: /api/bathroom/status endpoint"""
        response = test_app.get('/api/bathroom/status')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, dict)

    def test_bathroom_analytics(self, test_app):
        """Test: /api/bathroom/analytics endpoint"""
        response = test_app.get('/api/bathroom/analytics')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, dict)

    def test_mold_prevention_recommendation(self, test_app):
        """Test: /api/bathroom/mold-prevention endpoint"""
        response = test_app.get('/api/bathroom/mold-prevention')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'recommendation' in data or 'status' in data


class TestDeviceEndpoints:
    """Tests für Geräte-Endpoints"""

    @patch('src.data_collector.homey_collector.HomeyCollector.get_all_devices')
    def test_devices_list(self, mock_devices, test_app):
        """Test: /api/devices endpoint"""
        mock_devices.return_value = [
            {'id': 'device-1', 'name': 'Test Device', 'class': 'light'}
        ]
        
        response = test_app.get('/api/devices')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)

    @patch('src.data_collector.homey_collector.HomeyCollector.get_device')
    def test_device_detail(self, mock_device, test_app):
        """Test: /api/devices/<id> endpoint"""
        mock_device.return_value = {
            'id': 'device-1',
            'name': 'Test Device',
            'class': 'light',
            'capabilities': ['onoff', 'dim']
        }
        
        response = test_app.get('/api/devices/device-1')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['id'] == 'device-1'


class TestAutomationEndpoints:
    """Tests für Automatisierungs-Endpoints"""

    def test_automations_list(self, test_app):
        """Test: /api/automations endpoint"""
        response = test_app.get('/api/automations')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, (list, dict))

    def test_automation_toggle(self, test_app):
        """Test: /api/automations/<id>/toggle endpoint"""
        payload = {'enabled': True}
        
        response = test_app.post('/api/automations/test-automation/toggle',
                                json=payload,
                                content_type='application/json')
        
        # Kann 200 oder 404 sein je nach Existenz
        assert response.status_code in [200, 404]


class TestErrorHandling:
    """Tests für Fehlerbehandlung"""

    def test_404_not_found(self, test_app):
        """Test: 404 für nicht existierende Route"""
        response = test_app.get('/api/does-not-exist')
        assert response.status_code == 404

    def test_method_not_allowed(self, test_app):
        """Test: 405 für falsche HTTP-Methode"""
        response = test_app.post('/health')
        assert response.status_code == 405

    def test_invalid_json(self, test_app):
        """Test: 400 für ungültiges JSON"""
        response = test_app.post('/api/ml/lighting/predict',
                                data='invalid json',
                                content_type='application/json')
        assert response.status_code in [400, 422]


class TestHTMLPages:
    """Tests für HTML-Seiten"""

    def test_dashboard(self, test_app):
        """Test: Dashboard-Seite"""
        response = test_app.get('/')
        assert response.status_code == 200
        assert b'<!DOCTYPE html>' in response.data or b'<html' in response.data

    def test_analytics_page(self, test_app):
        """Test: Analytics-Seite"""
        response = test_app.get('/analytics')
        assert response.status_code == 200

    def test_automations_page(self, test_app):
        """Test: Automations-Seite"""
        response = test_app.get('/automations')
        assert response.status_code == 200

    def test_heating_page(self, test_app):
        """Test: Heating-Seite"""
        response = test_app.get('/heating')
        assert response.status_code == 200
