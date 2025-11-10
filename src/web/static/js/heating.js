// Heating Page JavaScript

let allHeaters = [];
let allWindows = [];
let allRooms = [];
let zoneNameMap = {};
let currentFilter = 'all';
let currentRoomFilter = 'all';
let currentMode = 'control'; // control oder optimization
let temperatureChart = null; // Chart.js Instanz für Temperaturverlauf

// Lade alle Heizgeräte beim Seitenaufruf
document.addEventListener('DOMContentLoaded', () => {
    loadHeaters();
    loadWindows();
    loadHeatingMode();
    setupEventListeners();
    setupSliders();
    loadOutdoorTemp();

    // Lade Fenster-Daten
    loadWindowData();

    // Lade Optimierungsdaten wenn im Monitoring-Modus
    if (currentMode === 'optimization') {
        loadOptimizationData();
        loadTemperatureHistory();
    }

    // Lade Heizungs-Analytics
    loadHeatingAnalytics();
});

// Event Listeners einrichten
function setupEventListeners() {
    // Refresh Button
    document.getElementById('refresh-heating')?.addEventListener('click', () => {
        loadHeaters();
        loadWindows();
        loadWindowData();
        if (currentMode === 'optimization') {
            loadOptimizationData();
        }
    });

    // Filter
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentFilter = btn.dataset.filter;
            renderHeaters();
        });
    });

    document.getElementById('room-filter')?.addEventListener('change', (e) => {
        currentRoomFilter = e.target.value;
        renderHeaters();
    });

    // Analytics Zeitraum Selector
    document.getElementById('analytics-timeframe')?.addEventListener('change', () => {
        loadHeatingAnalytics();
    });

    // Speichern

    // Zeitplan erstellen
    document.getElementById('add-schedule')?.addEventListener('click', () => {
        document.getElementById('schedule-modal').style.display = 'block';
    });

    // Modal schließen
    document.querySelectorAll('.close').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.modal').forEach(modal => {
                modal.style.display = 'none';
            });
        });
    });

    // Modal außerhalb klicken
    window.addEventListener('click', (e) => {
        if (e.target.classList.contains('modal')) {
            e.target.style.display = 'none';
        }
    });
}

// Slider mit Wert-Anzeige einrichten
function setupSliders() {
    const sliders = [
        { id: 'default-comfort-temp', valueId: 'default-comfort-temp-value' },
        { id: 'default-eco-temp', valueId: 'default-eco-temp-value' },
        { id: 'default-night-temp', valueId: 'default-night-temp-value' },
        { id: 'default-frost-temp', valueId: 'default-frost-temp-value' },
        { id: 'modal-temp-slider', valueId: 'modal-temp-value' },
        { id: 'schedule-temp', valueId: 'schedule-temp-value' }
    ];

    sliders.forEach(({ id, valueId }) => {
        const slider = document.getElementById(id);
        const valueDisplay = document.getElementById(valueId);
        if (slider && valueDisplay) {
            slider.addEventListener('input', () => {
                valueDisplay.textContent = slider.value + '°C';
            });
        }
    });
}

// Lade alle Heizgeräte
async function loadHeaters() {
    try {
        // Lade Geräte und Räume parallel
        const [devicesData, roomsData] = await Promise.all([
            fetchJSON('/api/devices'),
            fetchJSON('/api/rooms')
        ]);

        const allDevices = devicesData.devices || [];
        allRooms = roomsData.rooms || [];

        console.log('Loaded devices:', allDevices.length);
        console.log('Climate devices:', allDevices.filter(d => d.domain === 'climate'));

        // Filtere nur Heizgeräte (climate domain)
        allHeaters = allDevices.filter(d => {
            // Climate domain ist der Hauptindikator
            if (d.domain === 'climate') return true;

            // Thermostat class
            if (d.attributes?.device_class === 'thermostat') return true;
            if (d.class === 'thermostat') return true;

            // Hat target_temperature capability
            if (d.capabilitiesObj?.target_temperature) return true;
            if (d.capabilities?.target_temperature) return true;
            if (d.attributes?.capabilities?.target_temperature) return true;

            return false;
        });

        console.log('Filtered heaters:', allHeaters.length);
        if (allHeaters.length > 0) {
            console.log('First heater example:', allHeaters[0]);
        }

        // Erstelle Zone-ID zu Name Mapping
        zoneNameMap = {};
        allRooms.forEach(room => {
            zoneNameMap[room.id] = room.name;
        });

        // Füge Raumnamen zu Heizgeräten hinzu
        allHeaters.forEach(heater => {
            const zoneId = heater.attributes?.zone || heater.zone;
            heater.zoneName = zoneId ? zoneNameMap[zoneId] : 'Ohne Raum';
        });

        updateStatistics();
        populateRoomFilter();
        renderHeaters();
    } catch (error) {
        console.error('Error loading heaters:', error);
        document.getElementById('heaters-container').innerHTML =
            '<div class="error">Fehler beim Laden der Heizgeräte</div>';
    }
}

// Update Statistiken
function updateStatistics() {
    const activeHeaters = allHeaters.filter(h => isHeaterActive(h)).length;
    const temps = allHeaters
        .map(h => getCurrentTemp(h))
        .filter(t => t !== null && !isNaN(t));

    const avgTemp = temps.length > 0
        ? (temps.reduce((a, b) => a + b, 0) / temps.length).toFixed(1)
        : '--';

    document.getElementById('total-heaters').textContent = allHeaters.length;
    document.getElementById('active-heaters').textContent = activeHeaters;
    document.getElementById('avg-temp').textContent = avgTemp + (avgTemp !== '--' ? '°C' : '');
}

// Lade Fenster-Sensoren
async function loadWindows() {
    try {
        const devicesData = await fetchJSON('/api/devices');
        const allDevices = devicesData.devices || [];

        // Filtere Fenster-Sensoren (contact sensors für Fenster/Türen)
        allWindows = allDevices.filter(d => {
            // Sensor domain mit contact class
            if (d.domain === 'sensor' && d.attributes?.device_class === 'window') return true;
            if (d.domain === 'binary_sensor' && d.attributes?.device_class === 'window') return true;
            if (d.domain === 'binary_sensor' && d.attributes?.device_class === 'door') return true;

            // Homey: contact alarm capability
            if (d.capabilitiesObj?.alarm_contact !== undefined) return true;

            // Name enthält "Fenster" oder "Window"
            const name = (d.name || '').toLowerCase();
            if (name.includes('fenster') || name.includes('window')) return true;

            return false;
        });

        // Füge Raumnamen hinzu
        allWindows.forEach(window => {
            const zoneId = window.attributes?.zone || window.zone;
            window.zoneName = zoneId ? zoneNameMap[zoneId] : 'Ohne Raum';
        });

        console.log('Filtered windows:', allWindows.length);
        if (allWindows.length > 0) {
            console.log('First window example:', allWindows[0]);
        }

        renderWindows();
    } catch (error) {
        console.error('Error loading windows:', error);
        document.getElementById('windows-container').innerHTML =
            '<div class="error">Fehler beim Laden der Fenster-Sensoren</div>';
    }
}

// Rendere Fenster-Sensoren
function renderWindows() {
    const container = document.getElementById('windows-container');

    if (allWindows.length === 0) {
        container.innerHTML = '<div class="info-box">Keine Fenster-Sensoren gefunden.</div>';
        return;
    }

    container.innerHTML = allWindows.map(window => createWindowCard(window)).join('');
}

// Erstelle Fenster-Karte
function createWindowCard(window) {
    const isOpen = isWindowOpen(window);
    const windowName = window.name || window.id;
    const zoneName = window.zoneName || 'Ohne Raum';

    return `
        <div class="window-card ${isOpen ? 'open' : 'closed'}">
            <div class="window-icon">
                ${isOpen ? '🪟' : '🟢'}
            </div>
            <div class="window-name">${windowName}</div>
            <div class="window-status ${isOpen ? 'open' : 'closed'}">
                ${isOpen ? '⚠️ Offen' : '✓ Geschlossen'}
            </div>
            <div class="window-room">🏠 ${zoneName}</div>
        </div>
    `;
}

// Prüfe ob Fenster offen ist
function isWindowOpen(window) {
    // State "on" bedeutet offen bei binary sensors
    if (window.state === 'on' || window.state === 'open') return true;

    // Homey: alarm_contact capability (true = offen)
    if (window.capabilitiesObj?.alarm_contact?.value === true) return true;

    // Home Assistant: state "on" oder "open"
    const state = window.state?.state || window.state;
    if (state === 'on' || state === 'open') return true;

    return false;
}

// Lade Außentemperatur
async function loadOutdoorTemp() {
    try {
        const status = await fetchJSON('/api/status');
        // API gibt Temperatur unter temperature.outdoor zurück
        const outdoorTemp = status.temperature?.outdoor;
        if (outdoorTemp !== undefined && outdoorTemp !== null) {
            document.getElementById('outdoor-temp').textContent = outdoorTemp.toFixed(1) + '°C';
        }
    } catch (error) {
        console.error('Error loading outdoor temp:', error);
    }
}

// Lade Temperaturverlauf für Chart (24 Stunden)
async function loadTemperatureHistory() {
    try {
        const response = await fetchJSON('/api/heating/temperature-history?hours=24');

        if (!response.success) {
            console.error('Error loading temperature history:', response.error);
            return;
        }

        // Wenn keine Daten vorhanden
        if (!response.data || response.data.timestamps.length === 0) {
            const chartContainer = document.getElementById('temperature-chart').parentElement;
            chartContainer.innerHTML = `
                <div style="text-align: center; padding: 40px; color: #6b7280;">
                    <p>${response.message || 'Noch keine Daten verfügbar'}</p>
                    <p style="font-size: 0.9em; margin-top: 10px;">
                        Das System sammelt alle 15 Minuten Heizungsdaten.
                    </p>
                </div>
            `;
            return;
        }

        renderTemperatureChart(response.data);

    } catch (error) {
        console.error('Error loading temperature history:', error);
    }
}

// Rendere Temperaturverlauf Chart
function renderTemperatureChart(data) {
    const ctx = document.getElementById('temperature-chart');
    if (!ctx) return;

    // Zerstöre existierenden Chart
    if (temperatureChart) {
        temperatureChart.destroy();
    }

    // Formatiere Timestamps für X-Achse
    const labels = data.timestamps.map(ts => {
        const date = new Date(ts);
        return date.toLocaleTimeString('de-DE', {
            hour: '2-digit',
            minute: '2-digit'
        });
    });

    // Erstelle Chart
    temperatureChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Außentemperatur',
                    data: data.outdoor_temp,
                    borderColor: '#ef4444',
                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                    borderWidth: 2,
                    tension: 0.4,
                    fill: false,
                    spanGaps: true
                },
                {
                    label: 'Durchschnitt Innen',
                    data: data.indoor_temp,
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    borderWidth: 2,
                    tension: 0.4,
                    fill: true,
                    spanGaps: true
                },
                {
                    label: 'Zieltemperatur',
                    data: data.target_temp,
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    borderWidth: 2,
                    borderDash: [5, 5],
                    tension: 0.4,
                    fill: false,
                    spanGaps: true
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            if (context.parsed.y !== null) {
                                label += context.parsed.y.toFixed(1) + '°C';
                            }
                            return label;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    ticks: {
                        callback: function(value) {
                            return value + '°C';
                        }
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                },
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        maxRotation: 45,
                        minRotation: 45
                    }
                }
            }
        }
    });
}

// Fülle Raum-Filter aus
function populateRoomFilter() {
    const roomFilter = document.getElementById('room-filter');
    if (!roomFilter) return;

    const rooms = [...new Set(allHeaters.map(h => h.zoneName))].sort();

    roomFilter.innerHTML = '<option value="all">Alle Räume</option>';
    rooms.forEach(room => {
        const option = document.createElement('option');
        option.value = room;
        option.textContent = room;
        roomFilter.appendChild(option);
    });
}

// Filtere Heizgeräte
function getFilteredHeaters() {
    let filtered = allHeaters;

    // Filter nach Status
    if (currentFilter === 'active') {
        filtered = filtered.filter(h => isHeaterActive(h));
    } else if (currentFilter === 'inactive') {
        filtered = filtered.filter(h => !isHeaterActive(h));
    }

    // Filter nach Raum
    if (currentRoomFilter !== 'all') {
        filtered = filtered.filter(h => h.zoneName === currentRoomFilter);
    }

    return filtered;
}

// Rendere Heizgeräte
function renderHeaters() {
    const container = document.getElementById('heaters-container');
    const filtered = getFilteredHeaters();

    if (filtered.length === 0) {
        container.innerHTML = '<div class="info-box">Keine Heizgeräte gefunden.</div>';
        return;
    }

    container.innerHTML = filtered.map(heater => createHeaterCard(heater)).join('');

    // Event Listener für Karten
    container.querySelectorAll('.heater-card').forEach(card => {
        card.addEventListener('click', () => {
            const heaterId = card.dataset.heaterId;
            const heater = allHeaters.find(h => getHeaterId(h) === heaterId);
            if (heater) {
                openHeaterModal(heater);
            }
        });
    });
}

// Erstelle Heizgeräte-Karte
function createHeaterCard(heater) {
    const isActive = isHeaterActive(heater);
    const currentTemp = getCurrentTemp(heater);
    const targetTemp = getTargetTemp(heater);
    const heaterId = getHeaterId(heater);

    return `
        <div class="heater-card ${isActive ? 'active' : ''}" data-heater-id="${heaterId}">
            <div class="heater-header">
                <div class="heater-name">${heater.name || heater.id}</div>
                <div class="heater-status">
                    ${isActive ? '🔥 Aktiv' : '⏸️ Inaktiv'}
                </div>
            </div>

            <div class="heater-temps">
                <div class="temp-display">
                    <div class="temp-label">Aktuell</div>
                    <div class="temp-value">${currentTemp !== null ? currentTemp.toFixed(1) : '--'}°C</div>
                </div>
                <div class="temp-display">
                    <div class="temp-label">Ziel</div>
                    <div class="temp-value">${targetTemp !== null ? targetTemp.toFixed(1) : '--'}°C</div>
                </div>
            </div>

            <div class="heater-room">
                <span>🏠</span>
                <span>${heater.zoneName}</span>
            </div>
        </div>
    `;
}

// Öffne Heizgeräte-Info-Modal (nur Anzeige, keine Steuerung)
function openHeaterModal(heater) {
    const modal = document.getElementById('heater-modal');
    const currentTemp = getCurrentTemp(heater);
    const targetTemp = getTargetTemp(heater);
    const isActive = isHeaterActive(heater);

    document.getElementById('modal-heater-name').textContent = heater.name || heater.id;
    document.getElementById('modal-heater-room').textContent = '🏠 ' + heater.zoneName;
    document.getElementById('modal-current-temp').textContent =
        currentTemp !== null ? currentTemp.toFixed(1) + '°C' : '--';
    document.getElementById('modal-target-temp').textContent =
        targetTemp !== null ? targetTemp.toFixed(1) + '°C' : '--';
    document.getElementById('modal-heater-status').textContent = isActive ? '🔥 Aktiv' : '⏸️ Inaktiv';

    modal.style.display = 'block';
}

// Hilfsfunktionen für Heizgeräte-Daten
function getHeaterId(heater) {
    return heater.entity_id || heater.id;
}

function getCurrentTemp(heater) {
    // Direkt auf oberster Ebene (von verbesserter API)
    if (heater.current_temperature !== undefined && heater.current_temperature !== null) {
        return heater.current_temperature;
    }
    // In attributes (Home Assistant Format)
    if (heater.attributes?.current_temperature !== undefined) {
        return heater.attributes.current_temperature;
    }
    // In state Objekt
    if (heater.state?.current_temperature !== undefined) {
        return heater.state.current_temperature;
    }
    // Direkt in capabilitiesObj (Homey Format)
    if (heater.capabilitiesObj?.measure_temperature?.value !== undefined) {
        return heater.capabilitiesObj.measure_temperature.value;
    }
    // Als Fallback: state Wert wenn es eine Zahl ist
    const stateValue = parseFloat(heater.state);
    if (!isNaN(stateValue)) {
        return stateValue;
    }
    return null;
}

function getTargetTemp(heater) {
    // Direkt auf oberster Ebene (von verbesserter API)
    if (heater.target_temperature !== undefined && heater.target_temperature !== null) {
        return heater.target_temperature;
    }
    // In attributes.temperature (Home Assistant Format)
    if (heater.attributes?.temperature !== undefined) {
        return heater.attributes.temperature;
    }
    // In state.target_temperature
    if (heater.state?.target_temperature !== undefined) {
        return heater.state.target_temperature;
    }
    // Direkt in capabilitiesObj (Homey Format)
    if (heater.capabilitiesObj?.target_temperature?.value !== undefined) {
        return heater.capabilitiesObj.target_temperature.value;
    }
    return null;
}

function isHeaterActive(heater) {
    const state = heater.state?.state || heater.state;
    if (state === 'heat' || state === 'heating') return true;

    const targetTemp = getTargetTemp(heater);
    const currentTemp = getCurrentTemp(heater);

    if (targetTemp !== null && currentTemp !== null) {
        return targetTemp > currentTemp + 0.5; // 0.5°C Hysterese
    }

    return false;
}

// Setze Temperatur für alle Heizgeräte
async function setAllHeaters(temperature) {
    const resultDiv = document.getElementById('quick-action-result');
    resultDiv.innerHTML = '<div class="loading">Setze Temperatur für alle Heizgeräte...</div>';

    let success = 0;
    let failed = 0;

    for (const heater of allHeaters) {
        try {
            await setHeaterTemperature(heater, temperature);
            success++;
        } catch (error) {
            console.error('Failed to set temperature for', heater.name, error);
            failed++;
        }
    }

    resultDiv.innerHTML = `
        <div class="success">
            ✓ ${success} Heizgeräte auf ${temperature}°C gesetzt
            ${failed > 0 ? `<br>⚠ ${failed} fehlgeschlagen` : ''}
        </div>
    `;

    setTimeout(() => {
        resultDiv.innerHTML = '';
        loadHeaters();
    }, 3000);
}

// Schalte alle Heizgeräte aus
async function turnAllHeatersOff() {
    if (!confirm('Wirklich alle Heizgeräte ausschalten?')) return;

    const resultDiv = document.getElementById('quick-action-result');
    resultDiv.innerHTML = '<div class="loading">Schalte alle Heizgeräte aus...</div>';

    let success = 0;
    let failed = 0;

    for (const heater of allHeaters) {
        try {
            await turnHeaterOff(heater);
            success++;
        } catch (error) {
            console.error('Failed to turn off', heater.name, error);
            failed++;
        }
    }

    resultDiv.innerHTML = `
        <div class="success">
            ✓ ${success} Heizgeräte ausgeschaltet
            ${failed > 0 ? `<br>⚠ ${failed} fehlgeschlagen` : ''}
        </div>
    `;

    setTimeout(() => {
        resultDiv.innerHTML = '';
        loadHeaters();
    }, 3000);
}

// Setze Temperatur für ein Heizgerät
async function setHeaterTemperature(heater, temperature) {
    const heaterId = getHeaterId(heater);

    try {
        const response = await fetch('/api/devices/control', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                entity_id: heaterId,
                action: 'set_temperature',
                temperature: temperature
            })
        });

        if (!response.ok) throw new Error('Failed to set temperature');

        const result = document.getElementById('modal-action-result');
        if (result) {
            result.innerHTML = `<div class="success">✓ Temperatur auf ${temperature}°C gesetzt</div>`;
            setTimeout(() => {
                result.innerHTML = '';
                document.getElementById('heater-modal').style.display = 'none';
                loadHeaters();
            }, 2000);
        }
    } catch (error) {
        console.error('Error setting temperature:', error);
        const result = document.getElementById('modal-action-result');
        if (result) {
            result.innerHTML = '<div class="error">✗ Fehler beim Setzen der Temperatur</div>';
        }
        throw error;
    }
}

// Schalte Heizgerät aus
async function turnHeaterOff(heater) {
    const heaterId = getHeaterId(heater);

    try {
        const response = await fetch('/api/devices/control', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                entity_id: heaterId,
                action: 'turn_off'
            })
        });

        if (!response.ok) throw new Error('Failed to turn off heater');

        const result = document.getElementById('modal-action-result');
        if (result) {
            result.innerHTML = '<div class="success">✓ Heizgerät ausgeschaltet</div>';
            setTimeout(() => {
                result.innerHTML = '';
                document.getElementById('heater-modal').style.display = 'none';
                loadHeaters();
            }, 2000);
        }
    } catch (error) {
        console.error('Error turning off heater:', error);
        const result = document.getElementById('modal-action-result');
        if (result) {
            result.innerHTML = '<div class="error">✗ Fehler beim Ausschalten</div>';
        }
        throw error;
    }
}

// Speichere Einstellungen
async function saveSettings() {
    const resultDiv = document.getElementById('save-result');
    resultDiv.innerHTML = '<div class="loading">Speichere Einstellungen...</div>';

    const settings = {
        default_comfort_temp: parseFloat(document.getElementById('default-comfort-temp').value),
        default_eco_temp: parseFloat(document.getElementById('default-eco-temp').value),
        default_night_temp: parseFloat(document.getElementById('default-night-temp').value),
        default_frost_temp: parseFloat(document.getElementById('default-frost-temp').value),
        auto_heating: document.getElementById('auto-heating').checked,
        window_detection: document.getElementById('window-detection').checked,
        presence_based: document.getElementById('presence-based').checked,
        energy_price_optimization: document.getElementById('energy-price-optimization').checked
    };

    try {
        const response = await fetch('/api/heating/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(settings)
        });

        if (!response.ok) throw new Error('Failed to save settings');

        resultDiv.innerHTML = '<div class="success">✓ Einstellungen gespeichert</div>';
        setTimeout(() => resultDiv.innerHTML = '', 3000);
    } catch (error) {
        console.error('Error saving settings:', error);
        resultDiv.innerHTML = '<div class="error">✗ Fehler beim Speichern der Einstellungen</div>';
    }
}

// === HEIZUNGS-OPTIMIERUNG FUNKTIONEN ===

// Lade aktuellen Heizungs-Modus
async function loadHeatingMode() {
    try {
        const data = await fetchJSON('/api/heating/mode');
        currentMode = data.mode || 'control';
        updateModeUI(currentMode);
    } catch (error) {
        console.error('Error loading heating mode:', error);
        currentMode = 'control';
        updateModeUI(currentMode);
    }
}

// Wechsle zwischen Control und Optimization Modus
async function switchMode(newMode) {
    try {
        const response = await fetch('/api/heating/mode', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mode: newMode })
        });

        if (!response.ok) throw new Error('Failed to switch mode');

        const data = await response.json();
        currentMode = data.mode;
        updateModeUI(currentMode);

        // Lade relevante Daten für den neuen Modus
        if (currentMode === 'optimization') {
            loadOptimizationData();
        }

        console.log('Switched to mode:', currentMode);
    } catch (error) {
        console.error('Error switching mode:', error);
        alert('Fehler beim Wechseln des Modus');
    }
}

// Update UI basierend auf Modus
function updateModeUI(mode) {
    // Zeige/verstecke Modi-spezifische Elemente
    if (mode === 'control') {
        // Steuerungs-Elemente zeigen
        document.querySelectorAll('.mode-control-only').forEach(el => {
            el.style.display = 'block';
        });
        document.querySelectorAll('.mode-monitoring-only').forEach(el => {
            el.style.display = 'none';
        });
        document.getElementById('mode-subtitle').textContent = 'Zentrale Steuerung aller Heizgeräte und Thermostate';
    } else {
        // Monitoring-Elemente zeigen
        document.querySelectorAll('.mode-control-only').forEach(el => {
            el.style.display = 'none';
        });
        document.querySelectorAll('.mode-monitoring-only').forEach(el => {
            el.style.display = 'block';
        });
        document.getElementById('mode-subtitle').textContent = 'KI-Analyse und Optimierungsvorschläge für Tado X';
    }
}

// Lade Optimierungsdaten (Insights, Muster, etc.)
async function loadOptimizationData() {
    try {
        // Lade Insights
        const insights = await fetchJSON('/api/heating/insights');
        renderInsights(insights.insights || []);

        // Lade Statistiken
        const stats = await fetchJSON('/api/heating/statistics');
        renderStatistics(stats);

        console.log('Optimization data loaded');
    } catch (error) {
        console.error('Error loading optimization data:', error);
    }
}

// Rendere KI-Insights
function renderInsights(insights) {
    const container = document.querySelector('.recommendations-grid');
    if (!container) return;

    // Update Insights-Zähler
    const insightsCount = insights.length;
    const insightsCountEl = document.getElementById('monitoring-insights-count');
    if (insightsCountEl) {
        insightsCountEl.textContent = insightsCount;
    }

    if (insights.length === 0) {
        container.innerHTML = `
            <div class="info-box" style="grid-column: 1 / -1;">
                <strong>ℹ️ Hinweis:</strong> Noch nicht genug Daten für Optimierungsvorschläge.
                <br>Das System sammelt aktuell Daten über dein Heizverhalten.
                <br>Komme in ein paar Tagen wieder, um personalisierte Vorschläge zu erhalten.
            </div>
        `;
        return;
    }

    container.innerHTML = insights.map(insight => createInsightCard(insight)).join('');
}

// Erstelle Insight-Karte
function createInsightCard(insight) {
    const typeClasses = {
        'night_reduction': 'energy',
        'window_warning': 'comfort',
        'temperature_optimization': 'weather',
        'weekend_optimization': 'timing'
    };

    const cardClass = typeClasses[insight.insight_type] || 'energy';

    return `
        <div class="recommendation-card ${cardClass}">
            <div class="recommendation-icon">${insight.icon || '💡'}</div>
            <div class="recommendation-content">
                <h4>${insight.title || insight.insight_type}</h4>
                <p class="recommendation-value">
                    ${insight.potential_saving_percent ? `~${insight.potential_saving_percent}%` : 'Optimierung'}
                </p>
                <p class="recommendation-text">${insight.recommendation}</p>
                ${insight.potential_saving_eur ?
                    `<small style="color: #10b981; font-weight: 600;">Sparpotenzial: ~${insight.potential_saving_eur}€/Monat</small>` :
                    ''}
            </div>
        </div>
    `;
}

// Rendere Statistiken
function renderStatistics(stats) {
    // Update Temperatur-Stats wenn vorhanden
    if (stats.temperatures) {
        const avgIndoor = stats.temperatures.avg_indoor;
        if (avgIndoor) {
            document.getElementById('avg-temp').textContent = avgIndoor + '°C';
        }
    }

    // Update Heiz-Stats
    if (stats.heating) {
        const heatingPercent = stats.heating.heating_percent;
        console.log('Heating active:', heatingPercent + '%');
    }

    // Update Monitoring-Status (nur im Monitoring-Modus sichtbar)
    if (currentMode === 'optimization') {
        // Beobachtungen
        const observationsCount = stats.heating?.total_observations || 0;
        document.getElementById('monitoring-observations-count').textContent = observationsCount;

        // Daten-Zeitraum
        const dataDays = stats.period_days || 0;
        document.getElementById('monitoring-data-days').textContent = dataDays > 0 ? dataDays + ' Tage' : 'Keine Daten';
    }
}

// === HEIZUNGS-ANALYTICS FUNKTIONEN ===

let heatingTimesChart = null;
let roomComparisonChart = null;
let weatherCorrelationChart = null;

// Lade Heizungs-Analytics
async function loadHeatingAnalytics() {
    const timeframeSelect = document.getElementById('analytics-timeframe');
    if (!timeframeSelect) return;

    const days = parseInt(timeframeSelect.value) || 14;

    try {
        const data = await fetchJSON(`/api/heating/analytics?days=${days}`);

        if (data.sufficient_data) {
            // Rendere alle Analytics
            renderCostEstimates(data.cost_estimates);
            renderHeatingTimes(data.heating_times);
            renderTemperatureEfficiency(data.temperature_efficiency);
            renderRoomComparison(data.room_comparison);
            renderWeatherCorrelation(data.weather_correlation);

            // Zeige Analytics-Section
            document.querySelector('.heating-analytics-card')?.classList.remove('hidden');
        } else {
            // Zeige Info-Nachricht
            console.log('Nicht genug Daten für Analytics');
        }
    } catch (error) {
        console.error('Error loading heating analytics:', error);
    }
}

// Rendere Kosten-Schätzungen
function renderCostEstimates(costData) {
    if (!costData) return;

    document.getElementById('cost-daily').textContent =
        (costData.daily_cost || 0).toFixed(2) + '€';
    document.getElementById('cost-monthly').textContent =
        (costData.monthly_cost || 0).toFixed(2) + '€';
    document.getElementById('cost-yearly').textContent =
        (costData.yearly_cost || 0).toFixed(0) + '€';
    document.getElementById('heating-hours').textContent =
        (costData.total_heating_hours || 0).toFixed(1) + 'h';
}

// Rendere Heizzeiten-Chart
function renderHeatingTimes(heatingTimesData) {
    if (!heatingTimesData || !heatingTimesData.hourly_breakdown) return;

    const ctx = document.getElementById('heating-times-chart');
    if (!ctx) return;

    // Zerstöre existierenden Chart
    if (heatingTimesChart) {
        heatingTimesChart.destroy();
    }

    const hours = Array.from({ length: 24 }, (_, i) => i);
    const percentages = hours.map(h => heatingTimesData.hourly_breakdown[h] || 0);

    heatingTimesChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: hours.map(h => h + ':00'),
            datasets: [{
                label: 'Heizaktivität (%)',
                data: percentages,
                backgroundColor: percentages.map(p => {
                    if (p > 70) return '#ef4444'; // Hoch - Rot
                    if (p > 40) return '#f59e0b'; // Mittel - Orange
                    return '#10b981'; // Niedrig - Grün
                }),
                borderColor: '#1f2937',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: (context) => `${context.parsed.y.toFixed(1)}% der Zeit aktiv`
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    title: { display: true, text: 'Heizaktivität (%)' }
                },
                x: {
                    title: { display: true, text: 'Uhrzeit' }
                }
            }
        }
    });

    // Zeige Peak-Zeiten
    if (heatingTimesData.peak_hours && heatingTimesData.peak_hours.length > 0) {
        const peakHoursText = heatingTimesData.peak_hours.join(', ');
        console.log('Peak Heizzeiten:', peakHoursText);
    }
}

// Rendere Temperatur-Effizienz
function renderTemperatureEfficiency(efficiencyData) {
    if (!efficiencyData) return;

    const score = efficiencyData.efficiency_score || 0;
    const scoreText = document.getElementById('efficiency-score-text');
    const scoreCircle = document.getElementById('efficiency-score-circle');

    if (scoreText) {
        scoreText.textContent = score.toFixed(0);
    }

    if (scoreCircle) {
        // Animiere den Kreis (314 = Umfang bei r=50)
        const circumference = 314;
        const offset = circumference - (score / 100) * circumference;
        scoreCircle.style.strokeDashoffset = offset;

        // Farbe basierend auf Score
        let color = '#10b981'; // Grün
        if (score < 60) color = '#f59e0b'; // Orange
        if (score < 40) color = '#ef4444'; // Rot
        scoreCircle.setAttribute('stroke', color);
    }

    // Zeige Details
    const avgDiff = efficiencyData.avg_temp_difference || 0;
    const efficiencyDetails = document.getElementById('efficiency-details');
    if (efficiencyDetails) {
        efficiencyDetails.innerHTML = `
            <div class="efficiency-detail">
                <span class="label">Ø Zieltemperatur:</span>
                <span class="value">${(efficiencyData.avg_target_temp || 0).toFixed(1)}°C</span>
            </div>
            <div class="efficiency-detail">
                <span class="label">Ø Ist-Temperatur:</span>
                <span class="value">${(efficiencyData.avg_actual_temp || 0).toFixed(1)}°C</span>
            </div>
            <div class="efficiency-detail">
                <span class="label">Ø Differenz:</span>
                <span class="value">${avgDiff.toFixed(1)}°C</span>
            </div>
        `;
    }
}

// Rendere Raum-Vergleich
function renderRoomComparison(roomData) {
    if (!roomData || roomData.length === 0) return;

    const ctx = document.getElementById('room-comparison-chart');
    if (!ctx) return;

    // Zerstöre existierenden Chart
    if (roomComparisonChart) {
        roomComparisonChart.destroy();
    }

    const rooms = roomData.map(r => r.room_name);
    const heatingPercent = roomData.map(r => r.heating_percent);
    const avgTemp = roomData.map(r => r.avg_temp);

    roomComparisonChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: rooms,
            datasets: [
                {
                    label: 'Heizaktivität (%)',
                    data: heatingPercent,
                    backgroundColor: 'rgba(239, 68, 68, 0.6)',
                    borderColor: '#ef4444',
                    borderWidth: 1,
                    yAxisID: 'y-percent'
                },
                {
                    label: 'Ø Temperatur (°C)',
                    data: avgTemp,
                    backgroundColor: 'rgba(59, 130, 246, 0.6)',
                    borderColor: '#3b82f6',
                    borderWidth: 1,
                    yAxisID: 'y-temp'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: true, position: 'top' }
            },
            scales: {
                'y-percent': {
                    type: 'linear',
                    position: 'left',
                    beginAtZero: true,
                    max: 100,
                    title: { display: true, text: 'Heizaktivität (%)' }
                },
                'y-temp': {
                    type: 'linear',
                    position: 'right',
                    beginAtZero: false,
                    title: { display: true, text: 'Temperatur (°C)' },
                    grid: { drawOnChartArea: false }
                }
            }
        }
    });
}

// Rendere Wetter-Korrelation
function renderWeatherCorrelation(weatherData) {
    if (!weatherData || weatherData.length === 0) return;

    const ctx = document.getElementById('weather-correlation-chart');
    if (!ctx) return;

    // Zerstöre existierenden Chart
    if (weatherCorrelationChart) {
        weatherCorrelationChart.destroy();
    }

    const labels = weatherData.map(w => w.temp_range);
    const heatingPercent = weatherData.map(w => w.heating_percent);

    // Farben basierend auf Temperatur-Bereich
    const colors = weatherData.map(w => {
        const temp = parseFloat(w.temp_range.split('-')[0]); // Nimm untere Grenze
        if (temp < 0) return '#3b82f6'; // Blau (kalt)
        if (temp < 10) return '#10b981'; // Grün (kühl)
        if (temp < 15) return '#f59e0b'; // Orange (mild)
        return '#ef4444'; // Rot (warm)
    });

    weatherCorrelationChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Heizaktivität (%)',
                data: heatingPercent,
                backgroundColor: colors,
                borderColor: '#1f2937',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: (context) => {
                            const dataPoint = weatherData[context.dataIndex];
                            return [
                                `Heizaktivität: ${context.parsed.y.toFixed(1)}%`,
                                `Ø Außentemp: ${dataPoint.avg_outdoor_temp.toFixed(1)}°C`
                            ];
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    title: { display: true, text: 'Heizaktivität (%)' }
                },
                x: {
                    title: { display: true, text: 'Außentemperatur-Bereich (°C)' }
                }
            }
        }
    });
}

// Hilfsfunktion für API-Aufrufe
async function fetchJSON(url) {
    const response = await fetch(url);
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    return await response.json();
}

// ===== FENSTER-STATUS FUNKTIONEN =====

/**
 * Lädt und zeigt aktuell geöffnete Fenster
 */
async function loadCurrentOpenWindows() {
    try {
        const response = await fetchJSON('/api/heating/windows/current');

        const container = document.getElementById('open-windows-container');

        if (!response.data || response.data.length === 0) {
            container.innerHTML = `
                <div style="text-align: center; padding: 20px; background: #f0fdf4; border-radius: 8px; border: 1px solid #d1fae5;">
                    <div style="font-size: 2em; margin-bottom: 10px;">✅</div>
                    <p style="margin: 0; color: #065f46; font-weight: 600;">Alle Fenster geschlossen</p>
                    <p style="margin: 5px 0 0 0; color: #6b7280; font-size: 0.9em;">Optimale Bedingungen für Heizung</p>
                </div>
            `;
            return;
        }

        // Zeige geöffnete Fenster
        const openWindowsHTML = response.data.map(window => {
            const minutesOpen = window.minutes_open;
            const hoursOpen = Math.floor(minutesOpen / 60);
            const remainingMinutes = minutesOpen % 60;

            let durationText = '';
            if (hoursOpen > 0) {
                durationText = `${hoursOpen}h ${remainingMinutes}min`;
            } else {
                durationText = `${remainingMinutes} min`;
            }

            // Warnung bei langer Öffnung
            const isLongOpen = minutesOpen > 15;
            const bgColor = isLongOpen ? '#fef3c7' : '#fef9c3';
            const borderColor = isLongOpen ? '#f59e0b' : '#eab308';
            const iconColor = isLongOpen ? '#92400e' : '#854d0e';

            return `
                <div style="display: flex; align-items: center; gap: 15px; padding: 15px; background: ${bgColor}; border-radius: 8px; border: 1px solid ${borderColor}; margin-bottom: 10px;">
                    <div style="font-size: 2em;">🪟</div>
                    <div style="flex: 1;">
                        <div style="font-weight: 700; color: ${iconColor};">${window.device_name}</div>
                        <div style="font-size: 0.85em; color: #6b7280;">${window.room_name || 'Unbekannter Raum'}</div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 1.5em; font-weight: 700; color: ${iconColor};">${durationText}</div>
                        <div style="font-size: 0.75em; color: #6b7280;">offen seit</div>
                    </div>
                </div>
            `;
        }).join('');

        container.innerHTML = `
            <div style="margin-bottom: 10px; padding: 12px; background: #fef3c7; border-radius: 8px; border-left: 4px solid #f59e0b;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 1.5em;">⚠️</span>
                    <div>
                        <strong style="color: #92400e;">${response.data.length} Fenster offen</strong>
                        <div style="font-size: 0.85em; color: #6b7280; margin-top: 3px;">
                            Heizleistung kann beeinträchtigt sein
                        </div>
                    </div>
                </div>
            </div>
            ${openWindowsHTML}
        `;

    } catch (error) {
        console.error('Error loading open windows:', error);
        document.getElementById('open-windows-container').innerHTML = `
            <div class="error" style="padding: 15px; background: #fee2e2; border-radius: 8px; color: #991b1b;">
                ❌ Fehler beim Laden der Fensterdaten: ${error.message}
            </div>
        `;
    }
}

/**
 * Lädt und zeigt Fenster-Öffnungsstatistik
 */
async function loadWindowStatistics() {
    try {
        const response = await fetchJSON('/api/heating/windows/statistics?days=7');

        const container = document.getElementById('window-stats-content');

        if (!response.data || !response.data.by_room || response.data.by_room.length === 0) {
            container.innerHTML = `
                <div class="info" style="text-align: center; padding: 15px; color: #6b7280;">
                    Noch keine Statistiken verfügbar. Daten werden gesammelt...
                </div>
            `;
            return;
        }

        const statsHTML = response.data.by_room.map(stat => {
            const avgDurationHours = Math.floor(stat.avg_duration_minutes / 60);
            const avgDurationMinutes = Math.round(stat.avg_duration_minutes % 60);
            const maxDurationHours = Math.floor(stat.max_duration_minutes / 60);
            const maxDurationMinutes = Math.round(stat.max_duration_minutes % 60);
            const totalHours = Math.floor(stat.total_minutes_open / 60);

            return `
                <div style="padding: 15px; background: #f9fafb; border-radius: 8px; border: 1px solid #e5e7eb; margin-bottom: 10px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                        <div>
                            <div style="font-weight: 700; color: #1f2937;">${stat.device_name}</div>
                            <div style="font-size: 0.85em; color: #6b7280;">${stat.room_name || 'Unbekannter Raum'}</div>
                        </div>
                        <div style="background: #dbeafe; padding: 5px 12px; border-radius: 6px;">
                            <strong style="color: #1e40af;">${stat.open_count}x</strong>
                            <span style="font-size: 0.85em; color: #6b7280;"> geöffnet</span>
                        </div>
                    </div>
                    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; font-size: 0.85em;">
                        <div>
                            <div style="color: #6b7280;">Ø Dauer</div>
                            <div style="font-weight: 600; color: #1f2937;">${avgDurationHours}h ${avgDurationMinutes}min</div>
                        </div>
                        <div>
                            <div style="color: #6b7280;">Max. Dauer</div>
                            <div style="font-weight: 600; color: #1f2937;">${maxDurationHours}h ${maxDurationMinutes}min</div>
                        </div>
                        <div>
                            <div style="color: #6b7280;">Gesamt</div>
                            <div style="font-weight: 600; color: #1f2937;">${totalHours}h offen</div>
                        </div>
                    </div>
                </div>
            `;
        }).join('');

        container.innerHTML = statsHTML;

    } catch (error) {
        console.error('Error loading window statistics:', error);
        document.getElementById('window-stats-content').innerHTML = `
            <div class="error" style="padding: 15px; background: #fee2e2; border-radius: 8px; color: #991b1b;">
                ❌ Fehler beim Laden der Statistiken: ${error.message}
            </div>
        `;
    }
}

/**
 * Lädt alle Fenster-Daten
 */
function loadWindowData() {
    loadCurrentOpenWindows();
    loadWindowStatistics();
}
