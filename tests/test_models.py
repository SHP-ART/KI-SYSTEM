"""
Tests für Machine Learning Modelle
"""

import pytest
import numpy as np
from pathlib import Path
from src.models.lighting_model import LightingModel
from src.models.temperature_model import TemperatureModel


class TestLightingModel:
    """Tests für LightingModel"""

    def test_model_initialization(self):
        """Test: Model kann initialisiert werden"""
        model = LightingModel()
        assert model is not None
        assert model.model is None  # Noch nicht trainiert

    def test_prepare_training_data(self, sample_lighting_data):
        """Test: Daten werden korrekt vorbereitet"""
        model = LightingModel()
        X, y = model._prepare_training_data(sample_lighting_data)
        
        assert X is not None
        assert y is not None
        assert len(X) == len(sample_lighting_data)
        assert len(y) == len(sample_lighting_data)

    def test_train_with_sufficient_data(self, sample_lighting_data, tmp_path):
        """Test: Training mit ausreichend Daten"""
        # Generiere mehr Sample-Daten
        extended_data = sample_lighting_data * 40  # 120 Samples
        
        model = LightingModel()
        result = model.train(extended_data)
        
        assert result['success'] is True
        assert result['samples'] >= 100
        assert 'accuracy' in result
        assert model.model is not None

    def test_train_insufficient_data(self, sample_lighting_data):
        """Test: Training mit zu wenig Daten schlägt fehl"""
        model = LightingModel()
        result = model.train(sample_lighting_data)  # Nur 3 Samples
        
        assert result['success'] is False
        assert 'error' in result
        assert 'insufficient data' in result['error'].lower()

    def test_predict(self, sample_lighting_data):
        """Test: Vorhersage nach Training"""
        extended_data = sample_lighting_data * 40
        
        model = LightingModel()
        model.train(extended_data)
        
        prediction = model.predict(
            hour=20,
            outdoor_light=10.0,
            motion_detected=True,
            recent_activity=True
        )
        
        assert prediction in ['on', 'off']

    def test_save_and_load(self, sample_lighting_data, tmp_path):
        """Test: Model kann gespeichert und geladen werden"""
        extended_data = sample_lighting_data * 40
        
        # Trainiere Model
        model1 = LightingModel()
        model1.train(extended_data)
        
        # Speichere
        model_path = tmp_path / "test_lighting_model.pkl"
        model1.save(str(model_path))
        
        assert model_path.exists()
        
        # Lade
        model2 = LightingModel()
        model2.load(str(model_path))
        
        assert model2.model is not None
        
        # Prüfe dass beide gleiche Vorhersagen machen
        pred1 = model1.predict(hour=20, outdoor_light=10.0, motion_detected=True)
        pred2 = model2.predict(hour=20, outdoor_light=10.0, motion_detected=True)
        
        assert pred1 == pred2


class TestTemperatureModel:
    """Tests für TemperatureModel"""

    def test_model_initialization(self):
        """Test: Model kann initialisiert werden"""
        model = TemperatureModel()
        assert model is not None
        assert model.model is None

    def test_prepare_training_data(self, sample_temperature_data):
        """Test: Daten werden korrekt vorbereitet"""
        model = TemperatureModel()
        X, y = model._prepare_training_data(sample_temperature_data)
        
        assert X is not None
        assert y is not None
        assert len(X) == len(sample_temperature_data)
        assert len(y) == len(sample_temperature_data)

    def test_train_with_sufficient_data(self, sample_temperature_data):
        """Test: Training mit ausreichend Daten"""
        extended_data = sample_temperature_data * 70  # 210 Samples
        
        model = TemperatureModel()
        result = model.train(extended_data)
        
        assert result['success'] is True
        assert result['samples'] >= 200
        assert 'mae' in result
        assert 'rmse' in result
        assert model.model is not None

    def test_train_insufficient_data(self, sample_temperature_data):
        """Test: Training mit zu wenig Daten"""
        model = TemperatureModel()
        result = model.train(sample_temperature_data)  # Nur 3 Samples
        
        assert result['success'] is False
        assert 'error' in result

    def test_predict_temperature(self, sample_temperature_data):
        """Test: Temperatur-Vorhersage"""
        extended_data = sample_temperature_data * 70
        
        model = TemperatureModel()
        model.train(extended_data)
        
        temp, metadata = model.predict(
            current_temp=20.0,
            outdoor_temp=10.0,
            hour=8,
            presence=True,
            window_open=False
        )
        
        assert isinstance(temp, (int, float))
        assert 15.0 <= temp <= 25.0  # Reasonable range
        assert 'confidence' in metadata

    def test_predict_with_energy_optimization(self, sample_temperature_data):
        """Test: Vorhersage mit Energiepreis-Optimierung"""
        extended_data = sample_temperature_data * 70
        
        model = TemperatureModel()
        model.train(extended_data)
        
        # High energy price -> niedrigere Temperatur
        temp_high, _ = model.predict_with_energy_optimization(
            {'current_temp': 20.0, 'outdoor_temp': 10.0, 'hour': 8},
            energy_price_level=3  # Hoch
        )
        
        # Low energy price -> höhere Temperatur
        temp_low, _ = model.predict_with_energy_optimization(
            {'current_temp': 20.0, 'outdoor_temp': 10.0, 'hour': 8},
            energy_price_level=1  # Niedrig
        )
        
        assert temp_high <= temp_low  # Bei hohen Preisen wird gespart

    def test_save_and_load(self, sample_temperature_data, tmp_path):
        """Test: Model kann gespeichert und geladen werden"""
        extended_data = sample_temperature_data * 70
        
        model1 = TemperatureModel()
        model1.train(extended_data)
        
        model_path = tmp_path / "test_temperature_model.pkl"
        model1.save(str(model_path))
        
        assert model_path.exists()
        
        model2 = TemperatureModel()
        model2.load(str(model_path))
        
        assert model2.model is not None
        
        # Gleiche Vorhersagen
        pred1, _ = model1.predict(current_temp=20.0, outdoor_temp=10.0, hour=8)
        pred2, _ = model2.predict(current_temp=20.0, outdoor_temp=10.0, hour=8)
        
        assert abs(pred1 - pred2) < 0.1  # Fast identisch
