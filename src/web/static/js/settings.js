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

// ===== System Update Functions =====

// Lade aktuelle Version
async function loadVersion() {
    try {
        const data = await fetchJSON('/api/system/version');

        if (data.success) {
            document.getElementById('current-version').textContent = data.version.message;
            document.getElementById('current-commit').textContent = data.version.commit + ' (' + data.version.time + ')';
        } else {
            document.getElementById('current-version').textContent = 'Nicht verfügbar';
            document.getElementById('current-commit').textContent = '--';
        }
    } catch (error) {
        console.error('Error loading version:', error);
        document.getElementById('current-version').textContent = 'Fehler';
    }
}

// Prüfe auf Updates
async function checkForUpdates() {
    const statusEl = document.getElementById('update-status');
    const installBtn = document.getElementById('install-update');
    const commitsList = document.getElementById('new-commits-list');
    const resultEl = document.getElementById('update-result');

    try {
        statusEl.textContent = 'Prüfe...';
        resultEl.textContent = '';
        resultEl.style.display = 'none';

        const data = await fetchJSON('/api/system/check-update');

        if (data.success) {
            if (data.update_available) {
                statusEl.textContent = `Ja (${data.commits_behind} neue${data.commits_behind > 1 ? '' : 's'} Update)`;
                statusEl.style.color = '#ff9800';
                installBtn.style.display = 'inline-block';

                // Zeige neue Commits
                if (data.new_commits && data.new_commits.length > 0) {
                    const list = document.getElementById('commits-list');
                    list.innerHTML = data.new_commits.map(commit =>
                        `<li><code>${commit.hash}</code> ${commit.message}</li>`
                    ).join('');
                    commitsList.style.display = 'block';
                }
            } else {
                statusEl.textContent = 'Nein - System ist aktuell';
                statusEl.style.color = '#4caf50';
                installBtn.style.display = 'none';
                commitsList.style.display = 'none';
            }
        } else {
            statusEl.textContent = 'Fehler: ' + (data.error || 'Unbekannt');
            statusEl.style.color = '#f44336';
        }
    } catch (error) {
        console.error('Error checking for updates:', error);
        statusEl.textContent = 'Fehler beim Prüfen';
        statusEl.style.color = '#f44336';
    }
}

// Installiere Update
async function installUpdate() {
    const resultEl = document.getElementById('update-result');
    const installBtn = document.getElementById('install-update');

    if (!confirm('System-Update wird durchgeführt.\n\nDas System wird neu gestartet.\nDatenbank und Einstellungen bleiben erhalten.\n\nFortfahren?')) {
        return;
    }

    try {
        installBtn.disabled = true;
        resultEl.textContent = 'Update wird durchgeführt... Bitte warten...';
        resultEl.className = 'action-result';
        resultEl.style.display = 'block';

        const response = await fetch('/api/system/update', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        const data = await response.json();

        if (data.success) {
            resultEl.textContent = '✓ ' + data.message + '\n\nSeite wird in 10 Sekunden neu geladen...';
            resultEl.className = 'action-result success';

            // Warte 10 Sekunden und reload
            setTimeout(() => {
                window.location.reload();
            }, 10000);
        } else {
            resultEl.textContent = '✗ Fehler: ' + (data.error || 'Unbekannter Fehler');
            resultEl.className = 'action-result error';
            installBtn.disabled = false;
        }

    } catch (error) {
        resultEl.textContent = '✗ Fehler beim Update: ' + error.message;
        resultEl.className = 'action-result error';
        installBtn.disabled = false;
    }
}

// Event Listeners für Update-Buttons
document.getElementById('check-update').addEventListener('click', checkForUpdates);
document.getElementById('install-update').addEventListener('click', installUpdate);

// ===== ML Training Status Functions =====

// Lade ML Status
async function loadMLStatus() {
    try {
        const data = await fetchJSON('/api/ml/status');

        if (data.success) {
            // Lighting Model Status
            const lightingStatus = data.lighting;
            updateModelStatus('lighting', lightingStatus);

            // Temperature Model Status
            const tempStatus = data.temperature;
            updateModelStatus('temp', tempStatus);

            // Auto-Trainer Status
            const trainerStatus = data.auto_trainer;
            const trainerEl = document.getElementById('autotrainer-status');
            if (trainerStatus.enabled) {
                trainerEl.innerHTML = `
                    <span class="status-dot" style="display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: #10b981; margin-right: 6px;"></span>
                    Aktiv
                `;
            } else {
                trainerEl.innerHTML = `
                    <span class="status-dot" style="display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: #ef4444; margin-right: 6px;"></span>
                    Deaktiviert
                `;
            }

            // Next run info
            const nextRunEl = document.getElementById('autotrainer-next-run');
            if (trainerStatus.last_run) {
                nextRunEl.textContent = `Letzter Run: ${trainerStatus.last_run}`;
            } else {
                nextRunEl.textContent = 'Noch nie gelaufen';
            }

            // Update settings
            document.getElementById('autotrainer-enabled').checked = trainerStatus.enabled;
            document.getElementById('training-hour').value = trainerStatus.run_hour;

        } else {
            console.error('Error loading ML status:', data.error);
        }
    } catch (error) {
        console.error('Error loading ML status:', error);
    }
}

function updateModelStatus(modelType, status) {
    const prefix = modelType === 'lighting' ? 'lighting' : 'temp';
    const statusEl = document.getElementById(`${prefix}-model-status`);
    const dataCountEl = document.getElementById(`${prefix}-data-count`);
    const lastTrainedEl = document.getElementById(`${prefix}-last-trained`);

    // Status Text und Farbe
    let statusText = 'Warte auf Daten';
    let statusColor = '#fbbf24'; // yellow

    if (status.trained) {
        statusText = 'Trainiert ✓';
        statusColor = '#10b981'; // green
    } else if (status.ready) {
        statusText = 'Bereit zum Training';
        statusColor = '#3b82f6'; // blue
    }

    statusEl.innerHTML = `
        <span class="status-dot" style="display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: ${statusColor}; margin-right: 6px;"></span>
        ${statusText}
    `;

    // Data Count
    const unit = modelType === 'lighting' ? 'Events' : 'Readings';
    dataCountEl.textContent = `${status.data_count} / ${status.required} ${unit}`;

    // Last Trained
    if (status.last_trained) {
        lastTrainedEl.textContent = `Trainiert: ${status.last_trained}`;
    } else {
        lastTrainedEl.textContent = 'Nie trainiert';
    }
}

// Lade Training History
async function loadTrainingHistory() {
    const historyEl = document.getElementById('training-history');

    try {
        historyEl.innerHTML = '<div class="loading">Lade Verlauf...</div>';
        const data = await fetchJSON('/api/ml/training-history');

        if (data.success && data.history.length > 0) {
            let historyHTML = '<table style="width: 100%; border-collapse: collapse;">';
            historyHTML += '<thead><tr style="border-bottom: 2px solid #e5e7eb;">';
            historyHTML += '<th style="text-align: left; padding: 8px;">Zeit</th>';
            historyHTML += '<th style="text-align: left; padding: 8px;">Modell</th>';
            historyHTML += '<th style="text-align: right; padding: 8px;">Genauigkeit</th>';
            historyHTML += '<th style="text-align: right; padding: 8px;">Samples</th>';
            historyHTML += '<th style="text-align: right; padding: 8px;">Dauer</th>';
            historyHTML += '</tr></thead><tbody>';

            data.history.forEach((record, index) => {
                const bgColor = index % 2 === 0 ? '#f9fafb' : 'white';
                const accuracy = (record.accuracy * 100).toFixed(1);
                const time = record.training_time ? record.training_time.toFixed(1) + 's' : '--';

                historyHTML += `<tr style="background: ${bgColor};">`;
                historyHTML += `<td style="padding: 8px;">${record.timestamp}</td>`;
                historyHTML += `<td style="padding: 8px;">${record.model_name}</td>`;
                historyHTML += `<td style="padding: 8px; text-align: right;">${accuracy}%</td>`;
                historyHTML += `<td style="padding: 8px; text-align: right;">${record.samples_used}</td>`;
                historyHTML += `<td style="padding: 8px; text-align: right;">${time}</td>`;
                historyHTML += '</tr>';
            });

            historyHTML += '</tbody></table>';
            historyEl.innerHTML = historyHTML;
        } else {
            historyEl.innerHTML = '<p class="empty-state">Noch keine Trainings durchgeführt</p>';
        }
    } catch (error) {
        console.error('Error loading training history:', error);
        historyEl.innerHTML = '<p class="error">Fehler beim Laden der Historie</p>';
    }
}

// Manual Training
document.getElementById('manual-train').addEventListener('click', async () => {
    const resultEl = document.getElementById('ml-training-result');
    const btn = document.getElementById('manual-train');

    if (!confirm('Manuelles Training starten?\n\nDies kann einige Minuten dauern.\nEs werden nur Modelle trainiert, für die genug Daten vorhanden sind.')) {
        return;
    }

    try {
        btn.disabled = true;
        resultEl.textContent = 'Training wird gestartet... Bitte warten...';
        resultEl.className = 'action-result';
        resultEl.style.display = 'block';

        const response = await fetch('/api/ml/train', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ model: 'all' })
        });

        const data = await response.json();

        if (data.success) {
            let resultText = '✓ Training abgeschlossen:\n\n';

            if (data.results.lighting) {
                if (data.results.lighting.success) {
                    resultText += `• Lighting Model: Erfolgreich (${(data.results.lighting.accuracy * 100).toFixed(1)}% Genauigkeit)\n`;
                } else {
                    resultText += `• Lighting Model: ${data.results.lighting.error || 'Nicht genug Daten'}\n`;
                }
            }

            if (data.results.temperature) {
                if (data.results.temperature.success) {
                    resultText += `• Temperature Model: Erfolgreich (R² = ${data.results.temperature.r2_score.toFixed(3)})\n`;
                } else {
                    resultText += `• Temperature Model: ${data.results.temperature.error || 'Nicht genug Daten'}\n`;
                }
            }

            resultEl.textContent = resultText;
            resultEl.className = 'action-result success';

            // Aktualisiere Status
            setTimeout(() => {
                loadMLStatus();
                loadTrainingHistory();
            }, 1000);

        } else {
            resultEl.textContent = '✗ Fehler: ' + (data.error || 'Unbekannter Fehler');
            resultEl.className = 'action-result error';
        }

    } catch (error) {
        resultEl.textContent = '✗ Fehler beim Training: ' + error.message;
        resultEl.className = 'action-result error';
    } finally {
        btn.disabled = false;
    }
});

// Refresh ML Status
document.getElementById('refresh-ml-status').addEventListener('click', () => {
    loadMLStatus();
});

// Training History Details Toggle
const historyDetails = document.querySelector('details');
if (historyDetails) {
    historyDetails.addEventListener('toggle', (e) => {
        if (e.target.open) {
            loadTrainingHistory();
        }
    });
}

// Init
document.addEventListener('DOMContentLoaded', () => {
    loadConfig();
    loadSensorConfig();
    loadVersion();
    checkForUpdates(); // Auto-check beim Laden
    loadMLStatus(); // Lade ML Status
});
