// Settings Page JavaScript

// Lade Konfiguration
async function loadConfig() {
    try {
        const data = await fetchJSON('/api/config');

        // Platform Type
        document.getElementById('platform-type').value = data.platform_type || 'homeassistant';

        // Data Collection Interval
        document.getElementById('collection-interval').value = data.data_collection_interval || 300;

        // Decision Mode
        document.getElementById('decision-mode').value = data.decision_mode || 'auto';

        // Confidence Threshold
        const threshold = data.confidence_threshold || 0.7;
        document.getElementById('confidence-threshold').value = threshold;
        document.getElementById('confidence-value').textContent = threshold.toFixed(2);

    } catch (error) {
        console.error('Error loading config:', error);
    }
}

// Confidence Slider
document.getElementById('confidence-threshold').addEventListener('input', (e) => {
    document.getElementById('confidence-value').textContent = parseFloat(e.target.value).toFixed(2);
});

// Verbindung testen
document.getElementById('test-connection').addEventListener('click', async () => {
    const resultEl = document.getElementById('action-result');
    resultEl.textContent = 'Teste Verbindungen...';
    resultEl.className = 'action-result';
    resultEl.style.display = 'block';

    try {
        const data = await fetchJSON('/api/connection-test');

        let resultHTML = '<h4>Testergebnisse:</h4><ul>';
        for (const [service, status] of Object.entries(data.results)) {
            const icon = status ? '✓' : '✗';
            const statusText = status ? 'OK' : 'FEHLER';
            resultHTML += `<li>${icon} ${service}: ${statusText}</li>`;
        }
        resultHTML += '</ul>';

        resultEl.innerHTML = resultHTML;
        resultEl.className = 'action-result ' + (data.all_ok ? 'success' : 'error');

    } catch (error) {
        resultEl.textContent = 'Fehler beim Testen der Verbindungen: ' + error.message;
        resultEl.className = 'action-result error';
    }
});

// Modelle neu trainieren
document.getElementById('retrain-models').addEventListener('click', async () => {
    const resultEl = document.getElementById('action-result');

    if (!confirm('Möchten Sie die ML-Modelle wirklich neu trainieren? Dies kann einige Minuten dauern.')) {
        return;
    }

    resultEl.textContent = 'Training wird gestartet... (Diese Funktion ist in Entwicklung)';
    resultEl.className = 'action-result';
    resultEl.style.display = 'block';

    // TODO: Implementiere Modell-Training API
    setTimeout(() => {
        resultEl.textContent = 'Modell-Training ist noch nicht implementiert.';
        resultEl.className = 'action-result error';
    }, 1000);
});

// Daten löschen
document.getElementById('clear-data').addEventListener('click', async () => {
    const resultEl = document.getElementById('action-result');

    if (!confirm('Möchten Sie wirklich ALLE historischen Daten löschen? Diese Aktion kann nicht rückgängig gemacht werden!')) {
        return;
    }

    if (!confirm('Sind Sie ABSOLUT SICHER? Alle Trainingsdaten gehen verloren!')) {
        return;
    }

    resultEl.textContent = 'Daten werden gelöscht... (Diese Funktion ist in Entwicklung)';
    resultEl.className = 'action-result';
    resultEl.style.display = 'block';

    // TODO: Implementiere Daten-Lösch API
    setTimeout(() => {
        resultEl.textContent = 'Daten-Löschung ist noch nicht implementiert.';
        resultEl.className = 'action-result error';
    }, 1000);
});

// Sensor Configuration
let availableSensors = { temperature_sensors: [], humidity_sensors: [] };
let selectedSensors = { temperature_sensors: [], humidity_sensors: [] };

async function loadSensorConfig() {
    try {
        // Lade verfügbare Sensoren
        const available = await fetchJSON('/api/sensors/available');
        availableSensors = available;

        // Lade gespeicherte Konfiguration
        const config = await fetchJSON('/api/sensors/config');
        selectedSensors = config;

        // Rendere Sensor-Listen
        renderSensorList('temp', available.temperature_sensors, config.temperature_sensors);
        renderSensorList('humidity', available.humidity_sensors, config.humidity_sensors);

    } catch (error) {
        console.error('Error loading sensor config:', error);
        document.getElementById('temp-sensors-list').innerHTML =
            '<p class="error">Fehler beim Laden der Sensoren</p>';
        document.getElementById('humidity-sensors-list').innerHTML =
            '<p class="error">Fehler beim Laden der Sensoren</p>';
    }
}

function renderSensorList(type, sensors, selectedIds) {
    const containerId = type === 'temp' ? 'temp-sensors-list' : 'humidity-sensors-list';
    const container = document.getElementById(containerId);

    if (sensors.length === 0) {
        container.innerHTML = '<p class="empty-state">Keine Sensoren gefunden</p>';
        return;
    }

    container.innerHTML = sensors.map(sensor => {
        const isSelected = selectedIds.length === 0 || selectedIds.includes(sensor.id);
        const zoneName = sensor.zone ? ` (${sensor.zone})` : '';
        const currentValue = sensor.current_value !== null ?
            (type === 'temp' ? `${sensor.current_value}°C` : `${sensor.current_value}%`) : '';

        return `
            <div class="sensor-item">
                <label>
                    <input type="checkbox"
                           class="sensor-checkbox ${type}-sensor"
                           data-sensor-id="${sensor.id}"
                           ${isSelected ? 'checked' : ''}>
                    <span class="sensor-name">${sensor.name}${zoneName}</span>
                    <span class="sensor-value">${currentValue}</span>
                </label>
            </div>
        `;
    }).join('');
}

// Select/Deselect All
document.getElementById('select-all-temp').addEventListener('click', () => {
    document.querySelectorAll('.temp-sensor').forEach(cb => cb.checked = true);
});

document.getElementById('deselect-all-temp').addEventListener('click', () => {
    document.querySelectorAll('.temp-sensor').forEach(cb => cb.checked = false);
});

document.getElementById('select-all-humidity').addEventListener('click', () => {
    document.querySelectorAll('.humidity-sensor').forEach(cb => cb.checked = true);
});

document.getElementById('deselect-all-humidity').addEventListener('click', () => {
    document.querySelectorAll('.humidity-sensor').forEach(cb => cb.checked = false);
});

// Speichere Sensor-Konfiguration
document.getElementById('save-sensor-config').addEventListener('click', async () => {
    const resultEl = document.getElementById('sensor-save-result');

    // Sammle ausgewählte Sensoren
    const tempSensors = Array.from(document.querySelectorAll('.temp-sensor:checked'))
        .map(cb => cb.dataset.sensorId);
    const humiditySensors = Array.from(document.querySelectorAll('.humidity-sensor:checked'))
        .map(cb => cb.dataset.sensorId);

    try {
        resultEl.textContent = 'Speichere Konfiguration...';
        resultEl.className = 'action-result';
        resultEl.style.display = 'block';

        const response = await fetch('/api/sensors/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                temperature_sensors: tempSensors,
                humidity_sensors: humiditySensors
            })
        });

        const data = await response.json();

        if (data.success) {
            resultEl.textContent = '✓ ' + data.message;
            resultEl.className = 'action-result success';

            // Automatisch nach 3 Sekunden ausblenden
            setTimeout(() => {
                resultEl.style.display = 'none';
            }, 3000);
        } else {
            resultEl.textContent = '✗ Fehler: ' + (data.error || 'Unbekannter Fehler');
            resultEl.className = 'action-result error';
        }

    } catch (error) {
        resultEl.textContent = '✗ Fehler beim Speichern: ' + error.message;
        resultEl.className = 'action-result error';
    }
});

// Init
document.addEventListener('DOMContentLoaded', () => {
    loadConfig();
    loadSensorConfig();
});
