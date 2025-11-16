"""
Unit Tests für Database
"""

import pytest
import tempfile
import os
from datetime import datetime
from src.utils.database import Database


@pytest.fixture
def temp_db():
    """Erstelle temporäre Datenbank für Tests"""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_file.close()

    db = Database(temp_file.name)
    yield db

    db.close()
    os.unlink(temp_file.name)


def test_database_initialization(temp_db):
    """Test: Datenbank wird korrekt initialisiert"""
    assert temp_db.connection is not None


def test_execute_query(temp_db):
    """Test: Query kann ausgeführt werden"""
    result = temp_db.execute("SELECT 1 as value")

    assert result is not None
    assert len(result) == 1
    assert result[0]['value'] == 1


def test_add_sensor_data(temp_db):
    """Test: Sensor-Daten können hinzugefügt werden"""
    sensor_id = temp_db.add_sensor_data(
        sensor_id='test_sensor',
        value=21.5,
        sensor_type='temperature'
    )

    assert sensor_id > 0

    # Überprüfe ob Daten gespeichert wurden
    result = temp_db.execute(
        "SELECT * FROM sensor_data WHERE sensor_id = ?",
        ('test_sensor',)
    )

    assert len(result) == 1
    assert result[0]['value'] == 21.5


def test_add_decision(temp_db):
    """Test: Entscheidung kann gespeichert werden"""
    decision_id = temp_db.add_decision(
        device_id='light.kitchen',
        action='turn_on',
        confidence=0.85,
        executed=True
    )

    assert decision_id > 0

    # Überprüfe Speicherung
    result = temp_db.execute(
        "SELECT * FROM decisions WHERE id = ?",
        (decision_id,)
    )

    assert len(result) == 1
    assert result[0]['device_id'] == 'light.kitchen'
    assert result[0]['executed'] == 1


def test_save_training_metrics(temp_db):
    """Test: Training Metriken können gespeichert werden"""
    metrics = {
        'accuracy': 0.87,
        'precision': 0.85,
        'recall': 0.89
    }

    training_id = temp_db.save_training_metrics(
        model_name='test_model',
        model_type='random_forest',
        metrics=metrics
    )

    assert training_id > 0

    # Überprüfe Speicherung
    result = temp_db.execute(
        "SELECT * FROM training_history WHERE id = ?",
        (training_id,)
    )

    assert len(result) == 1
    assert result[0]['model_name'] == 'test_model'


def test_get_recent_sensor_data(temp_db):
    """Test: Neueste Sensor-Daten können abgerufen werden"""
    # Füge mehrere Datensätze hinzu
    for i in range(5):
        temp_db.add_sensor_data(
            sensor_id=f'sensor_{i}',
            value=20.0 + i,
            sensor_type='temperature'
        )

    # Hole neueste 3
    recent = temp_db.get_recent_sensor_data(limit=3)

    assert len(recent) <= 3


def test_close_connection(temp_db):
    """Test: Verbindung kann geschlossen werden"""
    temp_db.close()

    assert temp_db.connection is None
