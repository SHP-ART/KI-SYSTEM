// Settings Page JavaScript

// === TAB SWITCHING ===

function initTabs() {
    const tabButtons = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const targetTab = button.dataset.tab;

            // Entferne active class von allen Buttons und Contents
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));

            // Setze active class für aktuellen Tab
            button.classList.add('active');
            document.getElementById(`tab-${targetTab}`).classList.add('active');

            // Speichere aktiven Tab in localStorage
            localStorage.setItem('settings-active-tab', targetTab);

            // Lade Daten für den Tab wenn nötig
            if (targetTab === 'database') {
                loadDatabaseStatus();
            } else if (targetTab === 'ml') {
                loadMLStatus();
            } else if (targetTab === 'system') {
                loadVersion();
            }
        });
    });

    // Stelle letzten aktiven Tab wieder her
    const savedTab = localStorage.getItem('settings-active-tab');
    if (savedTab) {
        const tabButton = document.querySelector(`[data-tab="${savedTab}"]`);
        if (tabButton) {
            tabButton.click();
        }
    }
}

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

// === HEIZUNGS-MODUS FUNKTIONEN ===

// Lade Heizungs-Modus
async function loadHeatingMode() {
    try {
        const data = await fetchJSON('/api/heating/mode');
        const mode = data.mode || 'control';

        const select = document.getElementById('heating-mode');
        if (select) {
            select.value = mode;
            updateHeatingModeDescription(mode);
        }
    } catch (error) {
        console.error('Error loading heating mode:', error);
    }
}

// Update Beschreibung basierend auf Modus
function updateHeatingModeDescription(mode) {
    const descriptionEl = document.getElementById('heating-mode-description');
    if (!descriptionEl) return;

    if (mode === 'control') {
        descriptionEl.innerHTML = `
            <strong>🎮 Steuerungs-Modus:</strong>
            <ul style="margin: 5px 0 0 0; padding-left: 20px;">
                <li>KI-System steuert die Heizung <strong>direkt und automatisch</strong></li>
                <li>Nutzt ML-Modelle für optimale Temperaturen</li>
                <li>Schnellaktionen und Zeitpläne verfügbar</li>
                <li>Für vollautomatische Smart-Home-Steuerung</li>
            </ul>
        `;
    } else {
        descriptionEl.innerHTML = `
            <strong>📊 Optimierungs-Modus:</strong>
            <ul style="margin: 5px 0 0 0; padding-left: 20px;">
                <li><strong>Perfekt für Tado X</strong> und andere externe Steuerungen</li>
                <li>System sammelt Daten über Heizverhalten</li>
                <li>Generiert KI-basierte Optimierungsvorschläge</li>
                <li>Zeigt Einsparpotenziale in € und %</li>
                <li><strong>Keine automatischen Eingriffe</strong> - Sie behalten die Kontrolle</li>
            </ul>
        `;
    }
}

// Heizungs-Modus ändern Event
const heatingModeSelect = document.getElementById('heating-mode');
if (heatingModeSelect) {
    heatingModeSelect.addEventListener('change', (e) => {
        updateHeatingModeDescription(e.target.value);
    });
}

// Heizungs-Modus speichern
const saveHeatingModeBtn = document.getElementById('save-heating-mode');
if (saveHeatingModeBtn) {
    saveHeatingModeBtn.addEventListener('click', async () => {
        const resultEl = document.getElementById('heating-mode-result');
        const mode = document.getElementById('heating-mode').value;

        resultEl.innerHTML = '<div class="loading">Speichere...</div>';
        resultEl.style.display = 'block';

        try {
            const response = await fetch('/api/heating/mode', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ mode })
            });

            if (!response.ok) throw new Error('Failed to save mode');

            const data = await response.json();

            resultEl.innerHTML = `
                <div class="success">
                    ✓ Heizungs-Modus gespeichert: <strong>${mode === 'control' ? '🎮 Steuerung' : '📊 Optimierung'}</strong>
                    <br><small>Die Änderung ist sofort auf der Heizungs-Seite sichtbar.</small>
                </div>
            `;

            setTimeout(() => {
                resultEl.style.display = 'none';
            }, 5000);

        } catch (error) {
            console.error('Error saving heating mode:', error);
            resultEl.innerHTML = '<div class="error">✗ Fehler beim Speichern</div>';
        }
    });
}

// === DATENBANK-WARTUNG FUNKTIONEN ===

// Lade Datenbank-Status
async function loadDatabaseStatus() {
    try {
        const response = await fetch('/api/database/status');
        const data = await response.json();

        if (data.success) {
            const db = data.database;
            const settings = data.settings;

            // Dateigröße
            document.getElementById('db-size').textContent = db.file_size_mb + ' MB';
            document.getElementById('db-size-bytes').textContent = formatBytes(db.file_size_bytes);

            // Gesamt Zeilen
            document.getElementById('db-total-rows').textContent = formatNumber(db.total_rows);

            // Ältester Eintrag
            if (db.oldest_data) {
                const oldestDate = new Date(db.oldest_data);
                document.getElementById('db-oldest-data').textContent = formatDate(oldestDate);

                // Berechne Alter in Tagen
                const ageInDays = Math.floor((new Date() - oldestDate) / (1000 * 60 * 60 * 24));
                document.getElementById('db-data-age').textContent = ageInDays + ' Tage alt';
            } else {
                document.getElementById('db-oldest-data').textContent = 'Keine Daten';
                document.getElementById('db-data-age').textContent = '';
            }

            // Retention Days in Input setzen
            document.getElementById('retention-days').value = settings.retention_days || 90;

            // Letzte Wartung
            if (data.maintenance && data.maintenance.last_cleanup) {
                const lastMaintenance = new Date(data.maintenance.last_cleanup);
                const now = new Date();
                const hoursAgo = Math.floor((now - lastMaintenance) / (1000 * 60 * 60));

                if (hoursAgo < 24) {
                    document.getElementById('db-last-maintenance').textContent =
                        hoursAgo === 0 ? 'Gerade eben' : `Vor ${hoursAgo}h`;
                } else {
                    document.getElementById('db-last-maintenance').textContent = formatDate(lastMaintenance);
                }
            } else {
                document.getElementById('db-last-maintenance').textContent = 'Nie';
            }

            // Tabellen-Details
            renderTableDetails(db.table_counts);

        }
    } catch (error) {
        console.error('Error loading database status:', error);
    }
}

// Rendere Tabellen-Details
function renderTableDetails(tableCounts) {
    const container = document.getElementById('db-table-details');

    // Sortiere nach Anzahl (absteigend)
    const sorted = Object.entries(tableCounts)
        .filter(([_, count]) => count > 0)
        .sort((a, b) => b[1] - a[1]);

    if (sorted.length === 0) {
        container.innerHTML = '<div style="padding: 10px; color: #6b7280;">Keine Daten vorhanden</div>';
        return;
    }

    let html = '<table style="width: 100%; border-collapse: collapse;">';
    html += '<tr style="border-bottom: 1px solid #e5e7eb; font-weight: 600;"><th style="text-align: left; padding: 8px;">Tabelle</th><th style="text-align: right; padding: 8px;">Zeilen</th></tr>';

    for (const [table, count] of sorted) {
        html += `
            <tr style="border-bottom: 1px solid #f3f4f6;">
                <td style="padding: 8px;">${table}</td>
                <td style="padding: 8px; text-align: right; font-weight: 600;">${formatNumber(count)}</td>
            </tr>
        `;
    }

    html += '</table>';
    container.innerHTML = html;
}

// Cleanup durchführen
async function runCleanup() {
    const retentionDays = parseInt(document.getElementById('retention-days').value);
    const resultEl = document.getElementById('db-maintenance-result');
    const progressContainer = document.getElementById('db-progress-container');
    const progressBar = document.getElementById('db-progress-bar');
    const progressText = document.getElementById('db-progress-text');

    // Deaktiviere Buttons
    setButtonsDisabled(true);

    // Zeige Progress
    progressContainer.style.display = 'block';
    progressBar.style.width = '30%';
    progressText.textContent = 'Lösche alte Daten...';

    resultEl.innerHTML = '<div class="loading">Cleanup läuft...</div>';
    resultEl.style.display = 'block';

    try {
        const response = await fetch('/api/database/cleanup', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ retention_days: retentionDays })
        });

        const data = await response.json();

        progressBar.style.width = '100%';
        progressText.textContent = 'Abgeschlossen!';

        if (data.success) {
            resultEl.innerHTML = `
                <div class="success">
                    ✓ ${data.message}
                    <br><small>Gelöschte Zeilen: ${formatNumber(data.deleted_rows)}</small>
                </div>
            `;

            // Aktualisiere Status
            setTimeout(() => {
                loadDatabaseStatus();
            }, 1000);
        } else {
            throw new Error(data.error || 'Cleanup fehlgeschlagen');
        }

    } catch (error) {
        console.error('Error during cleanup:', error);
        resultEl.innerHTML = `<div class="error">✗ Fehler: ${error.message}</div>`;
    } finally {
        setButtonsDisabled(false);
        setTimeout(() => {
            progressContainer.style.display = 'none';
            progressBar.style.width = '0%';
            resultEl.style.display = 'none';
        }, 5000);
    }
}

// VACUUM durchführen
async function runVacuum() {
    const resultEl = document.getElementById('db-maintenance-result');
    const progressContainer = document.getElementById('db-progress-container');
    const progressBar = document.getElementById('db-progress-bar');
    const progressText = document.getElementById('db-progress-text');

    setButtonsDisabled(true);

    progressContainer.style.display = 'block';
    progressBar.style.width = '50%';
    progressText.textContent = 'Optimiere Datenbank...';

    resultEl.innerHTML = '<div class="loading">VACUUM läuft (kann einige Sekunden dauern)...</div>';
    resultEl.style.display = 'block';

    try {
        const response = await fetch('/api/database/vacuum', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        const data = await response.json();

        progressBar.style.width = '100%';
        progressText.textContent = 'Abgeschlossen!';

        if (data.success) {
            resultEl.innerHTML = `
                <div class="success">
                    ✓ ${data.message}
                    <br><small>Größe vorher: ${data.before_size_mb} MB → nachher: ${data.after_size_mb} MB</small>
                </div>
            `;

            // Aktualisiere Status
            setTimeout(() => {
                loadDatabaseStatus();
            }, 1000);
        } else {
            throw new Error(data.error || 'VACUUM fehlgeschlagen');
        }

    } catch (error) {
        console.error('Error during vacuum:', error);
        resultEl.innerHTML = `<div class="error">✗ Fehler: ${error.message}</div>`;
    } finally {
        setButtonsDisabled(false);
        setTimeout(() => {
            progressContainer.style.display = 'none';
            progressBar.style.width = '0%';
            resultEl.style.display = 'none';
        }, 5000);
    }
}

// Vollständige Wartung (Cleanup + Vacuum)
async function runFullMaintenance() {
    const resultEl = document.getElementById('db-maintenance-result');
    const progressContainer = document.getElementById('db-progress-container');
    const progressBar = document.getElementById('db-progress-bar');
    const progressText = document.getElementById('db-progress-text');

    setButtonsDisabled(true);

    progressContainer.style.display = 'block';
    progressBar.style.width = '0%';
    progressText.textContent = 'Starte Wartung...';

    resultEl.innerHTML = '<div class="loading">Führe vollständige Wartung durch...</div>';
    resultEl.style.display = 'block';

    try {
        // 1. Cleanup
        progressBar.style.width = '25%';
        progressText.textContent = '1/2: Lösche alte Daten...';

        const retentionDays = parseInt(document.getElementById('retention-days').value);
        const cleanupResponse = await fetch('/api/database/cleanup', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ retention_days: retentionDays })
        });

        const cleanupData = await cleanupResponse.json();
        if (!cleanupData.success) throw new Error(cleanupData.error);

        // 2. VACUUM
        progressBar.style.width = '60%';
        progressText.textContent = '2/2: Optimiere Datenbank...';

        const vacuumResponse = await fetch('/api/database/vacuum', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        const vacuumData = await vacuumResponse.json();
        if (!vacuumData.success) throw new Error(vacuumData.error);

        // Fertig!
        progressBar.style.width = '100%';
        progressText.textContent = 'Abgeschlossen!';

        resultEl.innerHTML = `
            <div class="success">
                ✓ Vollständige Wartung abgeschlossen!
                <br><small>Gelöschte Zeilen: ${formatNumber(cleanupData.deleted_rows)} | Freigegeben: ${vacuumData.freed_mb} MB</small>
            </div>
        `;

        // Aktualisiere Status
        setTimeout(() => {
            loadDatabaseStatus();
        }, 1000);

    } catch (error) {
        console.error('Error during full maintenance:', error);
        resultEl.innerHTML = `<div class="error">✗ Fehler: ${error.message}</div>`;
    } finally {
        setButtonsDisabled(false);
        setTimeout(() => {
            progressContainer.style.display = 'none';
            progressBar.style.width = '0%';
            resultEl.style.display = 'none';
        }, 5000);
    }
}

// Deaktiviere/Aktiviere Buttons während Wartung
function setButtonsDisabled(disabled) {
    document.getElementById('db-cleanup').disabled = disabled;
    document.getElementById('db-vacuum').disabled = disabled;
    document.getElementById('db-full-maintenance').disabled = disabled;
    document.getElementById('db-refresh-status').disabled = disabled;
}

// Event Listeners für Datenbank-Wartung
if (document.getElementById('db-cleanup')) {
    document.getElementById('db-cleanup').addEventListener('click', runCleanup);
    document.getElementById('db-vacuum').addEventListener('click', runVacuum);
    document.getElementById('db-full-maintenance').addEventListener('click', runFullMaintenance);
    document.getElementById('db-refresh-status').addEventListener('click', loadDatabaseStatus);
}

// Hilfsfunktionen
function formatNumber(num) {
    return num.toLocaleString('de-DE');
}

function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

function formatDate(date) {
    const options = { year: 'numeric', month: '2-digit', day: '2-digit' };
    return date.toLocaleDateString('de-DE', options);
}

// Init
document.addEventListener('DOMContentLoaded', () => {
    // Initialisiere Tab-System
    initTabs();

    // Lade initiale Daten
    loadConfig();
    loadSensorConfig();
    loadHeatingMode();

    // Die anderen Daten werden nur geladen wenn der entsprechende Tab aktiv ist
    // oder beim ersten Laden wenn kein Tab gespeichert ist
    const savedTab = localStorage.getItem('settings-active-tab');
    if (!savedTab || savedTab === 'general') {
        // Allgemein-Tab ist aktiv - keine Extra-Daten nötig
    } else if (savedTab === 'database') {
        loadDatabaseStatus();
    } else if (savedTab === 'ml') {
        loadMLStatus();
    } else if (savedTab === 'system') {
        loadVersion();
        checkForUpdates();
    }
});
