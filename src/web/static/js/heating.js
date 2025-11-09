// Heating Page JavaScript

let allHeaters = [];
let allWindows = [];
let allRooms = [];
let zoneNameMap = {};
let currentFilter = 'all';
let currentRoomFilter = 'all';

// Lade alle Heizgeräte beim Seitenaufruf
document.addEventListener('DOMContentLoaded', () => {
    loadHeaters();
    loadWindows();
    setupEventListeners();
    setupSliders();
    loadOutdoorTemp();
});

// Event Listeners einrichten
function setupEventListeners() {
    // Refresh Button
    document.getElementById('refresh-heating')?.addEventListener('click', () => {
        loadHeaters();
        loadWindows();
    });

    // Schnellaktionen
    document.getElementById('comfort-mode')?.addEventListener('click', () => setAllHeaters(21));
    document.getElementById('eco-mode')?.addEventListener('click', () => setAllHeaters(18));
    document.getElementById('night-mode')?.addEventListener('click', () => setAllHeaters(17));
    document.getElementById('frost-protection')?.addEventListener('click', () => setAllHeaters(12));
    document.getElementById('all-heaters-off')?.addEventListener('click', turnAllHeatersOff);

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

    // Speichern
    document.getElementById('save-heating-settings')?.addEventListener('click', saveSettings);

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
        const outdoorTemp = status.outdoor_temperature;
        if (outdoorTemp !== undefined && outdoorTemp !== null) {
            document.getElementById('outdoor-temp').textContent = outdoorTemp.toFixed(1) + '°C';
        }
    } catch (error) {
        console.error('Error loading outdoor temp:', error);
    }
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

// Öffne Heizgeräte-Modal
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

    // Setze Slider-Wert
    const slider = document.getElementById('modal-temp-slider');
    if (targetTemp !== null) {
        slider.value = targetTemp;
        document.getElementById('modal-temp-value').textContent = targetTemp.toFixed(1) + '°C';
    }

    // Event Listener für Buttons
    document.getElementById('modal-set-temp').onclick = async () => {
        const newTemp = parseFloat(slider.value);
        await setHeaterTemperature(heater, newTemp);
    };

    document.getElementById('modal-turn-off').onclick = async () => {
        await turnHeaterOff(heater);
    };

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

// Hilfsfunktion für API-Aufrufe
async function fetchJSON(url) {
    const response = await fetch(url);
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    return await response.json();
}
