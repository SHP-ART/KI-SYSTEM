"""
Unit Tests für ModelVersionManager
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from src.models.model_version_manager import ModelVersionManager


@pytest.fixture
def temp_models_dir():
    """Erstelle temporäres Models-Verzeichnis für Tests"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def version_manager(temp_models_dir):
    """Erstelle ModelVersionManager mit temp directory"""
    return ModelVersionManager(models_dir=temp_models_dir)


def test_initialization(version_manager, temp_models_dir):
    """Test: ModelVersionManager wird korrekt initialisiert"""
    assert version_manager.models_dir == Path(temp_models_dir)
    assert version_manager.models_dir.exists()
    assert version_manager.versions_dir.exists()
    assert version_manager.registry_file.exists()


def test_register_model(version_manager):
    """Test: Model kann registriert werden"""
    metrics = {'accuracy': 0.85, 'precision': 0.82}

    success = version_manager.register_model(
        model_name='test_model',
        metrics=metrics,
        notes='Test model'
    )

    assert success
    assert 'test_model' in version_manager.registry
    assert version_manager.registry['test_model']['versions'][-1]['metrics'] == metrics


def test_compare_with_previous_no_previous(version_manager):
    """Test: Vergleich ohne vorherige Version"""
    new_metrics = {'accuracy': 0.90}

    comparison = version_manager.compare_with_previous('new_model', new_metrics)

    assert comparison['improved'] == True
    assert comparison['previous_metrics'] is None


def test_compare_with_previous_improvement(version_manager):
    """Test: Vergleich zeigt Verbesserung"""
    # Registriere erste Version
    version_manager.register_model('test_model', {'accuracy': 0.80})

    # Vergleiche mit besserer Version
    comparison = version_manager.compare_with_previous('test_model', {'accuracy': 0.90})

    assert comparison['improved'] == True
    assert comparison['differences']['accuracy'] > 0


def test_compare_with_previous_degradation(version_manager):
    """Test: Vergleich zeigt Verschlechterung"""
    version_manager.register_model('test_model', {'accuracy': 0.90})

    comparison = version_manager.compare_with_previous('test_model', {'accuracy': 0.75})

    assert comparison['improved'] == False
    assert comparison['differences']['accuracy'] < 0


def test_get_version_history(version_manager):
    """Test: Version History kann abgerufen werden"""
    version_manager.register_model('test_model', {'accuracy': 0.80}, version='v1')
    version_manager.register_model('test_model', {'accuracy': 0.85}, version='v2')
    version_manager.register_model('test_model', {'accuracy': 0.90}, version='v3')

    history = version_manager.get_version_history('test_model', limit=10)

    assert len(history) == 3
    assert history[-1]['version'] == 'v3'


def test_get_summary(version_manager):
    """Test: Summary kann abgerufen werden"""
    version_manager.register_model('model1', {'accuracy': 0.85})
    version_manager.register_model('model2', {'mae': 1.2})

    summary = version_manager.get_summary()

    assert 'model1' in summary
    assert 'model2' in summary
    assert summary['model1']['versions_count'] > 0
    assert summary['model2']['versions_count'] > 0


def test_get_current_metrics(version_manager):
    """Test: Aktuelle Metriken können abgerufen werden"""
    metrics = {'accuracy': 0.90, 'precision': 0.88}
    version_manager.register_model('test_model', metrics)

    current = version_manager.get_current_metrics('test_model')

    assert current == metrics


def test_get_current_metrics_no_model(version_manager):
    """Test: Gibt None für nicht existierendes Model"""
    current = version_manager.get_current_metrics('nonexistent')

    assert current is None
