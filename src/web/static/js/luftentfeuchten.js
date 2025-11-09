// Bathroom Automation JavaScript

let allDevices = [];
let allRooms = [];
let zoneNameMap = {};
let selectedRoomId = '';
let devicesCache = null;
let devicesCacheTime = 0;
const CACHE_DURATION = 60000; // 60 Sekunden Cache

// Lade alle Geräte und Räume (mit Caching)
async function loadDevices() {
    try {
        const now = Date.now();

        // Verwende Cache wenn vorhanden und nicht älter als CACHE_DURATION
        if (devicesCache && (now - devicesCacheTime) < CACHE_DURATION) {
            allDevices = devicesCache;
            populateDeviceSelectors();
            return;
        }

        // Lade Geräte und Räume parallel
        const [devicesData, roomsData] = await Promise.all([
            fetchJSON('/api/devices'),
            fetchJSON('/api/rooms')
        ]);

        allDevices = devicesData.devices;
        allRooms = roomsData.rooms || [];

        // Erstelle Zone-ID zu Name Mapping
        zoneNameMap = {};
        allRooms.forEach(room => {
            zoneNameMap[room.id] = room.name;
        });

        // Füge Raumnamen zu Geräten hinzu
        allDevices.forEach(device => {
            const zoneId = device.attributes?.zone || device.zone;
            device.zoneName = zoneId ? zoneNameMap[zoneId] : 'Ohne Raum';
            device.zoneId = zoneId;
        });

        devicesCache = allDevices;
        devicesCacheTime = now;

        populateRoomFilter();
        populateDeviceSelectors();
    } catch (error) {
        console.error('Error loading devices:', error);
    }
}

// Fülle Raum-Filter
function populateRoomFilter() {
    const select = document.getElementById('room-filter');
    if (!select) return;

    // Keep the first "-- Alle Räume --" option
    const firstOption = select.options[0];
    select.innerHTML = '';
    select.appendChild(firstOption);

    // Sortiere Räume alphabetisch
    const sortedRooms = [...allRooms].sort((a, b) => a.name.localeCompare(b.name));

    let badRoomId = null;

    sortedRooms.forEach(room => {
        const option = document.createElement('option');
        option.value = room.id;
        option.textContent = `${room.icon || '🏠'} ${room.name}`;
        select.appendChild(option);

        // Merke Bad-Raum ID (suche nach "bad" im Namen, case-insensitive)
        if (room.name.toLowerCase().includes('bad')) {
            badRoomId = room.id;
        }
    });

    // Setze "Bad" als Standard-Auswahl wenn gefunden
    if (badRoomId) {
        select.value = badRoomId;
        selectedRoomId = badRoomId;
        // Aktualisiere Geräte-Auswahl mit Bad-Filter
        populateDeviceSelectors();
    }
}

// Fülle Device-Auswahl
function populateDeviceSelectors() {
    // Helper function to check if device has a capability
    const hasCap = (device, capName) => {
        const caps = device.attributes?.capabilities || {};
        return caps.hasOwnProperty(capName);
    };

    // Helper function to filter by room
    const filterByRoom = (devices) => {
        if (!selectedRoomId) return devices;
        return devices.filter(d => d.zoneId === selectedRoomId);
    };

    // Luftfeuchtigkeit-Sensoren (nur Sensoren mit humidity capability)
    const humiditySensors = filterByRoom(allDevices.filter(d => hasCap(d, 'measure_humidity')));
    populateSelect('humidity-sensor', humiditySensors);

    // Temperatur-Sensoren
    const tempSensors = filterByRoom(allDevices.filter(d => hasCap(d, 'measure_temperature')));
    populateSelect('temperature-sensor', tempSensors);

    // Luftentfeuchter (Nur einfache On/Off Geräte - keine Thermostate!)
    const dehumidifiers = filterByRoom(allDevices.filter(d => {
        // Muss onoff haben
        if (!hasCap(d, 'onoff')) return false;
        // Darf KEIN Thermostat sein (kein target_temperature)
        if (hasCap(d, 'target_temperature')) return false;
        // Sollte switch oder socket sein
        return d.domain === 'switch' || d.domain === 'socket';
    }));
    populateSelect('dehumidifier', dehumidifiers);

    // Heizungen/Thermostate (mit target_temperature capability)
    const heaters = filterByRoom(allDevices.filter(d => hasCap(d, 'target_temperature')));
    populateSelect('heater', heaters);

    // Bewegungssensoren
    const motionSensors = filterByRoom(allDevices.filter(d => hasCap(d, 'alarm_motion')));
    populateSelect('motion-sensor', motionSensors);

    // Tür-Sensoren
    const doorSensors = filterByRoom(allDevices.filter(d => hasCap(d, 'alarm_contact')));
    populateSelect('door-sensor', doorSensors);

    // Fenster-Sensoren
    const windowSensors = filterByRoom(allDevices.filter(d => hasCap(d, 'alarm_contact')));
    populateSelect('window-sensor', windowSensors);
}

function populateSelect(selectId, devices) {
    const select = document.getElementById(selectId);
    if (!select) return;

    // Keep the first "-- ... --" option
    const firstOption = select.options[0];
    select.innerHTML = '';
    select.appendChild(firstOption);

    devices.forEach(device => {
        const option = document.createElement('option');
        option.value = device.id;
        // Zone kann in attributes.zone sein
        const zoneName = device.attributes?.zone_name || device.zone || 'Kein Raum';
        option.textContent = `${device.name} (${zoneName})`;
        select.appendChild(option);
    });
}

// Lade Konfiguration
async function loadConfig() {
    try {
        const data = await fetchJSON('/api/luftentfeuchten/config');

        if (data.config) {
            const config = data.config;

            // Geräte
            setSelectValue('humidity-sensor', config.humidity_sensor_id);
            setSelectValue('temperature-sensor', config.temperature_sensor_id);
            setSelectValue('dehumidifier', config.dehumidifier_id);
            setSelectValue('heater', config.heater_id);
            setSelectValue('motion-sensor', config.motion_sensor_id);
            setSelectValue('door-sensor', config.door_sensor_id);
            setSelectValue('window-sensor', config.window_sensor_id);

            // Schwellwerte
            setSlider('humidity-high', config.humidity_threshold_high || 70);
            setSlider('humidity-low', config.humidity_threshold_low || 60);
            setSlider('dehumidifier-delay', config.dehumidifier_delay || 5);

            // Heizung
            setSlider('target-temperature', config.target_temperature || 22);
            setSlider('heating-boost-delta', config.heating_boost_delta || 1);
            const heatingBoostEnabled = document.getElementById('heating-boost-enabled');
            if (heatingBoostEnabled) {
                heatingBoostEnabled.checked = config.heating_boost_enabled !== false; // Default: true
                setupHeatingBoostToggle(); // Trigger toggle logic
            }

            // Energie-Werte (Tab: Erweitert)
            const dehumWattage = document.getElementById('dehumidifier-wattage');
            const energyPrice = document.getElementById('energy-price');

            if (dehumWattage) dehumWattage.value = config.dehumidifier_wattage || 400;
            if (energyPrice) energyPrice.value = config.energy_price_per_kwh || 0.30;

            // Enabled
            document.getElementById('bathroom-enabled').checked = config.enabled || false;
        }
    } catch (error) {
        console.error('Error loading bathroom config:', error);
    }
}

function setSelectValue(selectId, value) {
    const select = document.getElementById(selectId);
    if (select && value) {
        select.value = value;
    }
}

function setSlider(sliderId, value) {
    const slider = document.getElementById(sliderId);
    if (slider) {
        slider.value = value;
        updateSliderValue(sliderId);
    }
}

// Speichere Konfiguration
async function saveConfig() {
    try {
        const config = {
            enabled: document.getElementById('bathroom-enabled').checked,
            humidity_sensor_id: document.getElementById('humidity-sensor').value,
            temperature_sensor_id: document.getElementById('temperature-sensor').value,
            dehumidifier_id: document.getElementById('dehumidifier').value,
            heater_id: document.getElementById('heater').value || null,
            motion_sensor_id: document.getElementById('motion-sensor').value || null,
            door_sensor_id: document.getElementById('door-sensor').value || null,
            window_sensor_id: document.getElementById('window-sensor').value || null,
            humidity_threshold_high: parseFloat(document.getElementById('humidity-high').value),
            humidity_threshold_low: parseFloat(document.getElementById('humidity-low').value),
            dehumidifier_delay: parseInt(document.getElementById('dehumidifier-delay').value),
            // Heizung
            target_temperature: parseFloat(document.getElementById('target-temperature').value),
            heating_boost_enabled: document.getElementById('heating-boost-enabled').checked,
            heating_boost_delta: parseFloat(document.getElementById('heating-boost-delta').value),
            // Energie-Werte (nur Luftentfeuchter, keine Heizung bei Zentralheizung)
            dehumidifier_wattage: parseFloat(document.getElementById('dehumidifier-wattage').value),
            energy_price_per_kwh: parseFloat(document.getElementById('energy-price').value)
        };

        // Validierung
        if (!config.humidity_sensor_id || !config.temperature_sensor_id || !config.dehumidifier_id) {
            alert('Bitte wählen Sie mindestens Luftfeuchtigkeit-Sensor, Temperatur-Sensor und Luftentfeuchter aus!');
            return;
        }

        const result = await postJSON('/api/luftentfeuchten/config', { config });

        if (result.success) {
            showToast('✅ Konfiguration gespeichert!', 'success');
            loadStatus();
            // Energie-Stats neu laden
            loadEnergyStats();
        }
    } catch (error) {
        console.error('Error saving config:', error);
        showToast('❌ Fehler beim Speichern', 'error');
    }
}

// Lade Status
async function loadStatus() {
    try {
        const data = await fetchJSON('/api/luftentfeuchten/status');

        if (data.status) {
            const status = data.status;

            // Dusche erkannt
            if (status.shower_detected) {
                document.getElementById('shower-status').textContent = 'Ja - Dusche läuft!';
                document.getElementById('shower-status-icon').textContent = '🚿';
            } else {
                document.getElementById('shower-status').textContent = 'Nein';
                document.getElementById('shower-status-icon').textContent = '⏸️';
            }

            // Luftentfeuchter
            if (status.dehumidifier_running) {
                document.getElementById('dehumidifier-status').textContent = 'An';
                document.getElementById('dehumidifier-status-icon').textContent = '💨';
            } else {
                document.getElementById('dehumidifier-status').textContent = 'Aus';
                document.getElementById('dehumidifier-status-icon').textContent = '⏸️';
            }

            // Luftfeuchtigkeit
            if (status.current_humidity !== null) {
                document.getElementById('current-humidity').textContent = `${status.current_humidity.toFixed(1)}%`;
            }

            // Temperatur
            if (status.current_temperature !== null) {
                document.getElementById('current-temperature').textContent = `${status.current_temperature.toFixed(1)}°C`;
            }
        }
    } catch (error) {
        console.error('Error loading status:', error);
    }
}

// Test-Funktion
async function testAutomation() {
    try {
        const result = await postJSON('/api/luftentfeuchten/test', {});

        if (result.success) {
            alert(`Test erfolgreich!\n\nAktionen: ${result.actions.length}\n${result.message || ''}`);
            loadStatus();
        }
    } catch (error) {
        console.error('Error testing automation:', error);
        alert('Fehler beim Test');
    }
}

// Slider-Updates
function updateSliderValue(sliderId) {
    const slider = document.getElementById(sliderId);
    const valueSpan = document.getElementById(`${sliderId}-value`);

    if (!slider || !valueSpan) return;

    let value = slider.value;
    let suffix = '';

    if (sliderId.includes('humidity')) {
        suffix = '%';
    } else if (sliderId.includes('temperature')) {
        suffix = '°C';
    } else if (sliderId.includes('delay')) {
        suffix = ' Min';
    } else if (sliderId === 'heating-boost-delta') {
        suffix = '°C';
        value = '+' + value; // Plus-Zeichen für Erhöhung
    }

    valueSpan.textContent = value + suffix;
}

// Setup Slider-Listeners
function setupSliders() {
    const sliders = ['humidity-high', 'humidity-low', 'target-temperature', 'dehumidifier-delay', 'heating-boost-delta'];
    sliders.forEach(sliderId => {
        const slider = document.getElementById(sliderId);
        if (slider) {
            slider.addEventListener('input', () => updateSliderValue(sliderId));
            updateSliderValue(sliderId);
        }
    });
}

// Setup Heating Boost Toggle
function setupHeatingBoostToggle() {
    const toggle = document.getElementById('heating-boost-enabled');
    const boostGroup = document.getElementById('boost-temp-group');

    if (toggle && boostGroup) {
        toggle.addEventListener('change', () => {
            if (toggle.checked) {
                boostGroup.style.display = 'block';
            } else {
                boostGroup.style.display = 'none';
            }
        });

        // Initial state
        if (toggle.checked) {
            boostGroup.style.display = 'block';
        } else {
            boostGroup.style.display = 'none';
        }
    }
}

// Live Sensor Status laden
let liveSensorInterval = null;

async function loadLiveSensorStatus() {
    try {
        const data = await fetchJSON('/api/luftentfeuchten/live-status');

        if (!data.devices || Object.keys(data.devices).length === 0) {
            // Keine Geräte konfiguriert - verstecke Live-Card
            document.getElementById('live-sensors-card').style.display = 'none';
            return;
        }

        // Zeige Live-Card
        document.getElementById('live-sensors-card').style.display = 'block';

        const devices = data.devices;

        // Humidity Sensor
        if (devices.humidity_sensor) {
            const card = document.getElementById('live-humidity-card');
            card.style.display = 'block';
            document.getElementById('live-humidity-name').textContent = devices.humidity_sensor.name;
            const value = devices.humidity_sensor.value;
            if (value !== null && value !== undefined) {
                document.getElementById('live-humidity-value').textContent = `${value.toFixed(1)}%`;
                document.getElementById('live-humidity-meta').textContent = devices.humidity_sensor.available ? 'Online' : 'Offline';
            } else {
                document.getElementById('live-humidity-value').textContent = '--';
                document.getElementById('live-humidity-meta').textContent = 'Keine Daten';
            }
        } else {
            document.getElementById('live-humidity-card').style.display = 'none';
        }

        // Temperature Sensor
        if (devices.temperature_sensor) {
            const card = document.getElementById('live-temp-card');
            card.style.display = 'block';
            document.getElementById('live-temp-name').textContent = devices.temperature_sensor.name;
            const value = devices.temperature_sensor.value;
            if (value !== null && value !== undefined) {
                document.getElementById('live-temp-value').textContent = `${value.toFixed(1)}°C`;
                document.getElementById('live-temp-meta').textContent = devices.temperature_sensor.available ? 'Online' : 'Offline';
            } else {
                document.getElementById('live-temp-value').textContent = '--';
                document.getElementById('live-temp-meta').textContent = 'Keine Daten';
            }
        } else {
            document.getElementById('live-temp-card').style.display = 'none';
        }

        // Door Sensor
        if (devices.door_sensor) {
            const card = document.getElementById('live-door-card');
            card.style.display = 'block';
            document.getElementById('live-door-name').textContent = devices.door_sensor.name;
            const valueEl = document.getElementById('live-door-value');
            const iconEl = document.getElementById('live-door-icon');

            if (devices.door_sensor.is_open) {
                valueEl.textContent = 'Offen';
                valueEl.className = 'sensor-value door-open';
                iconEl.textContent = '🚪🔓';
            } else {
                valueEl.textContent = 'Geschlossen';
                valueEl.className = 'sensor-value door-closed';
                iconEl.textContent = '🚪🔒';
            }
            document.getElementById('live-door-meta').textContent = devices.door_sensor.available ? 'Online' : 'Offline';
        } else {
            document.getElementById('live-door-card').style.display = 'none';
        }

        // Window Sensor
        if (devices.window_sensor) {
            const card = document.getElementById('live-window-card');
            card.style.display = 'block';
            document.getElementById('live-window-name').textContent = devices.window_sensor.name;
            const valueEl = document.getElementById('live-window-value');
            const iconEl = document.getElementById('live-window-icon');

            if (devices.window_sensor.is_open) {
                valueEl.textContent = 'Offen';
                valueEl.className = 'sensor-value door-open';
                iconEl.textContent = '🪟🔓';
            } else {
                valueEl.textContent = 'Geschlossen';
                valueEl.className = 'sensor-value door-closed';
                iconEl.textContent = '🪟🔒';
            }
            document.getElementById('live-window-meta').textContent = devices.window_sensor.available ? 'Online' : 'Offline';
        } else {
            document.getElementById('live-window-card').style.display = 'none';
        }

        // Motion Sensor
        if (devices.motion_sensor) {
            const card = document.getElementById('live-motion-card');
            card.style.display = 'block';
            document.getElementById('live-motion-name').textContent = devices.motion_sensor.name;
            const valueEl = document.getElementById('live-motion-value');
            const iconEl = document.getElementById('live-motion-icon');

            if (devices.motion_sensor.motion_detected) {
                valueEl.textContent = 'Bewegung erkannt!';
                valueEl.className = 'sensor-value motion-detected';
                iconEl.textContent = '👤✨';
            } else {
                valueEl.textContent = 'Keine Bewegung';
                valueEl.className = 'sensor-value';
                iconEl.textContent = '👤';
            }
            document.getElementById('live-motion-meta').textContent = devices.motion_sensor.available ? 'Online' : 'Offline';
        } else {
            document.getElementById('live-motion-card').style.display = 'none';
        }

        // Dehumidifier
        if (devices.dehumidifier) {
            const card = document.getElementById('live-dehumidifier-card');
            card.style.display = 'block';
            document.getElementById('live-dehumidifier-name').textContent = devices.dehumidifier.name;
            const valueEl = document.getElementById('live-dehumidifier-value');
            const iconEl = document.getElementById('live-dehumidifier-icon');

            if (devices.dehumidifier.is_on) {
                valueEl.textContent = 'An';
                valueEl.style.color = '#10b981';
                iconEl.textContent = '💨';
            } else {
                valueEl.textContent = 'Aus';
                valueEl.style.color = '#6b7280';
                iconEl.textContent = '💨';
            }
            document.getElementById('live-dehumidifier-meta').textContent = devices.dehumidifier.available ? 'Online' : 'Offline';
        } else {
            document.getElementById('live-dehumidifier-card').style.display = 'none';
        }

        // Heater
        if (devices.heater) {
            const card = document.getElementById('live-heater-card');
            card.style.display = 'block';
            document.getElementById('live-heater-name').textContent = devices.heater.name;
            const value = devices.heater.value;
            if (value !== null && value !== undefined) {
                document.getElementById('live-heater-value').textContent = `${value.toFixed(1)}°C`;
            } else {
                document.getElementById('live-heater-value').textContent = '--';
            }
            document.getElementById('live-heater-meta').textContent = devices.heater.available ? 'Online' : 'Offline';
        } else {
            document.getElementById('live-heater-card').style.display = 'none';
        }

    } catch (error) {
        console.error('Error loading live sensor status:', error);
    }
}

// Aktoren-Steuerung
async function controlActuator(deviceType, action) {
    try {
        const result = await postJSON('/api/luftentfeuchten/control', {
            device_type: deviceType,
            action: action
        });

        if (result.success) {
            // Zeige kurze Bestätigung
            const message = result.message || 'Befehl gesendet';
            showToast(message, 'success');

            // Lade sofort den neuen Status
            setTimeout(loadLiveSensorStatus, 500);
        } else {
            showToast(result.error || 'Fehler beim Steuern', 'error');
        }
    } catch (error) {
        console.error('Error controlling actuator:', error);
        showToast('Fehler beim Steuern des Geräts', 'error');
    }
}

// Toast-Nachricht anzeigen
function showToast(message, type = 'info') {
    // Erstelle Toast Element wenn nicht vorhanden
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 9999;';
        document.body.appendChild(toastContainer);
    }

    const toast = document.createElement('div');
    const bgColor = type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#3b82f6';
    toast.style.cssText = `
        background: ${bgColor};
        color: white;
        padding: 12px 20px;
        border-radius: 6px;
        margin-bottom: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        animation: slideIn 0.3s ease;
    `;
    toast.textContent = message;

    toastContainer.appendChild(toast);

    // Entferne nach 3 Sekunden
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Lade gelernte Parameter-Informationen
async function loadLearnedParams() {
    try {
        const data = await fetchJSON('/api/luftentfeuchten/learned-params');

        const learnedParams = data.learned_params || {};
        const eventsCount = data.events_last_30_days || 0;
        const readyForOptimization = data.ready_for_optimization || false;

        // Prüfe ob irgendein Parameter gelernt wurde
        const hasLearnedParams = Object.values(learnedParams).some(p => p.is_learned);

        if (hasLearnedParams) {
            // Zeige Info-Box
            const infoBox = document.getElementById('learning-info-box');
            const infoText = document.getElementById('learning-info-text');
            const statusBadge = document.getElementById('learning-status-badge');

            if (infoBox && infoText) {
                let learnedCount = Object.values(learnedParams).filter(p => p.is_learned).length;

                infoText.innerHTML = `
                    Das System hat <strong>${learnedCount} Parameter</strong> aus <strong>${eventsCount} Events</strong> gelernt.
                    Die Werte werden automatisch verwendet und überschreiben die manuellen Einstellungen.
                `;
                infoBox.style.display = 'block';
            }

            if (statusBadge) {
                statusBadge.textContent = '🧠 Gelernte Werte aktiv';
                statusBadge.className = 'active';
                statusBadge.style.display = 'block';
            }

            // Zeige Parameter-Infos
            displayParamInfo('humidity_threshold_high', learnedParams.humidity_threshold_high);
            displayParamInfo('humidity_threshold_low', learnedParams.humidity_threshold_low);
            displayParamInfo('dehumidifier_delay', learnedParams.dehumidifier_delay);
        } else if (eventsCount > 0) {
            // Es gibt Events, aber noch keine gelernten Parameter
            const statusBadge = document.getElementById('learning-status-badge');
            if (statusBadge) {
                statusBadge.textContent = `📊 ${eventsCount} Events gesammelt`;
                statusBadge.className = 'inactive';
                statusBadge.style.display = 'block';
            }
        }

    } catch (error) {
        console.error('Error loading learned params:', error);
    }
}

// Zeige Info für einen einzelnen Parameter
function displayParamInfo(paramName, paramData) {
    if (!paramData || !paramData.is_learned) {
        return; // Kein gelernter Wert
    }

    // Map param name to UI element IDs
    const idMap = {
        'humidity_threshold_high': { source: 'humidity-high-source', info: 'humidity-high-learned-info' },
        'humidity_threshold_low': { source: 'humidity-low-source', info: 'humidity-low-learned-info' },
        'dehumidifier_delay': { source: 'delay-source', info: 'delay-learned-info' }
    };

    const ids = idMap[paramName];
    if (!ids) return;

    // Source Badge
    const sourceBadge = document.getElementById(ids.source);
    if (sourceBadge) {
        sourceBadge.textContent = '🧠 Gelernt';
        sourceBadge.className = 'param-source-badge learned';
        sourceBadge.style.display = 'inline-block';
    }

    // Detail Info
    const learnedInfo = document.getElementById(ids.info);
    if (learnedInfo) {
        const confidencePercent = Math.round(paramData.confidence * 100);
        const date = new Date(paramData.timestamp).toLocaleDateString('de-DE');

        learnedInfo.innerHTML = `
            ℹ️ Optimiert aus ${paramData.samples_used} Events
            (Konfidenz: ${confidencePercent}%, ${date})
        `;
        learnedInfo.style.display = 'block';
    }
}

// Reset gelernte Parameter
async function resetLearnedParams() {
    if (!confirm('Möchten Sie wirklich alle gelernten Parameter zurücksetzen?\n\nDas System wird dann wieder die manuell konfigurierten Werte verwenden.')) {
        return;
    }

    try {
        const response = await fetch('/api/luftentfeuchten/reset-learned', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        const data = await response.json();

        if (data.success) {
            showToast(`✅ ${data.message}`, 'success');

            // Verstecke Info-Box und Badges
            document.getElementById('learning-info-box').style.display = 'none';
            document.getElementById('learning-status-badge').style.display = 'none';

            // Verstecke alle Parameter-Infos
            document.querySelectorAll('.param-source-badge').forEach(el => el.style.display = 'none');
            document.querySelectorAll('.learned-param-info').forEach(el => el.style.display = 'none');

            // Neu laden nach kurzer Verzögerung
            setTimeout(() => {
                window.location.reload();
            }, 1500);
        } else {
            showToast('❌ Fehler beim Zurücksetzen', 'error');
        }
    } catch (error) {
        console.error('Error resetting learned params:', error);
        showToast('❌ Netzwerkfehler', 'error');
    }
}

// Lade Energie-Statistiken
async function loadEnergyStats() {
    try {
        const data = await fetchJSON('/api/luftentfeuchten/energy-stats?days=30');

        document.getElementById('energy-stats-loading').style.display = 'none';
        document.getElementById('energy-stats-content').style.display = 'block';

        // Update UI
        document.getElementById('energy-runtime').textContent = data.dehumidifier.runtime_hours + ' h';
        document.getElementById('energy-kwh').textContent = data.total.kwh + ' kWh';
        document.getElementById('energy-cost').textContent = data.total.cost_eur.toFixed(2) + ' €';
        document.getElementById('energy-savings').textContent = data.comparison_always_on.savings_percent + '%';
        document.getElementById('energy-events-count').textContent = data.event_count;
        document.getElementById('energy-avg-runtime').textContent = data.per_event.avg_runtime_minutes.toFixed(1);
        document.getElementById('energy-avg-cost').textContent = data.per_event.avg_cost_eur.toFixed(3);

    } catch (error) {
        console.error('Error loading energy stats:', error);
        document.getElementById('energy-stats-loading').textContent = 'Fehler beim Laden der Statistiken';
    }
}

// Lade Alerts
async function loadAlerts() {
    try {
        const data = await fetchJSON('/api/luftentfeuchten/alerts?days=7');

        if (data.alerts && data.alerts.length > 0) {
            const alertsCard = document.getElementById('alerts-card');
            const alertsContent = document.getElementById('alerts-content');

            let html = '';
            data.alerts.forEach(alert => {
                html += `
                    <div class="alert-item severity-${alert.severity}">
                        <div class="alert-title">${alert.title}</div>
                        <div class="alert-message">${alert.message}</div>
                    </div>
                `;
            });

            alertsContent.innerHTML = html;
            alertsCard.style.display = 'block';
        }

    } catch (error) {
        console.error('Error loading alerts:', error);
    }
}

// Live-Preview
async function showPreview() {
    try {
        const modal = document.getElementById('preview-modal');
        const content = document.getElementById('preview-content');

        content.innerHTML = '<div style="text-align: center; padding: 20px;">Lade Preview...</div>';
        modal.style.display = 'flex';

        const response = await fetch('/api/luftentfeuchten/preview', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        const data = await response.json();

        if (data.error) {
            content.innerHTML = `<div class="alert-item severity-high">Fehler: ${data.error}</div>`;
            return;
        }

        // Build Preview HTML
        let html = '';

        // Current State
        html += `
            <div class="preview-section">
                <h4>📊 Aktueller Zustand</h4>
                <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px;">
                    <div><strong>Luftfeuchtigkeit:</strong> ${data.current_state.humidity || '--'}%</div>
                    <div><strong>Temperatur:</strong> ${data.current_state.temperature || '--'}°C</div>
                    <div><strong>Bewegung:</strong> ${data.current_state.motion_detected ? 'Ja' : 'Nein'}</div>
                    <div><strong>Tür:</strong> ${data.current_state.door_closed ? 'Geschlossen' : 'Offen'}</div>
                </div>
                ${data.current_state.shower_would_be_detected ? '<div style="margin-top: 10px; color: #3b82f6; font-weight: 600;">🚿 Dusche würde erkannt werden!</div>' : ''}
            </div>
        `;

        // Thresholds
        html += `
            <div class="preview-section">
                <h4>📏 Schwellwerte</h4>
                <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px;">
                    <div><strong>High:</strong> ${data.thresholds.humidity_high}%</div>
                    <div><strong>Low:</strong> ${data.thresholds.humidity_low}%</div>
                    <div><strong>Ziel-Temp:</strong> ${data.thresholds.target_temperature}°C</div>
                </div>
            </div>
        `;

        // Actions
        html += '<div class="preview-section"><h4>🎯 Was würde passieren?</h4>';

        // Dehumidifier Action
        const dehum = data.actions.dehumidifier;
        const dehumClass = dehum.action === 'turn_on' ? 'turn-on' : dehum.action === 'turn_off' ? 'turn-off' : 'no-change';
        html += `
            <div class="preview-action ${dehumClass}">
                <div>
                    <strong>💨 Luftentfeuchter:</strong><br>
                    <span style="font-size: 0.9em; color: #6b7280;">${dehum.reason}</span>
                </div>
                <div>
                    ${dehum.action === 'turn_on' ? '✅ EIN' : dehum.action === 'turn_off' ? '⏸️ AUS' : '➖ Keine Änderung'}
                </div>
            </div>
        `;

        // Heater Action
        if (data.actions.heater) {
            const heater = data.actions.heater;
            const heaterClass = heater.action === 'set_temperature' ? 'turn-on' : 'no-change';
            html += `
                <div class="preview-action ${heaterClass}">
                    <div>
                        <strong>🔥 Heizung:</strong><br>
                        <span style="font-size: 0.9em; color: #6b7280;">${heater.reason}</span>
                    </div>
                    <div>
                        ${heater.action === 'set_temperature' ? '🌡️ ' + heater.target_temperature + '°C' : '➖ Keine Änderung'}
                    </div>
                </div>
            `;
        }

        html += '</div>';

        // Execution Note
        if (!data.automation_enabled) {
            html += `
                <div style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 12px; border-radius: 6px; margin-top: 15px;">
                    <strong>⚠️ Hinweis:</strong> Automation ist deaktiviert. Aktionen werden nicht ausgeführt.
                </div>
            `;
        }

        content.innerHTML = html;

    } catch (error) {
        console.error('Error loading preview:', error);
        document.getElementById('preview-content').innerHTML = '<div class="alert-item severity-high">Fehler beim Laden der Preview</div>';
    }
}

// Setup Tab System
function setupTabs() {
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const targetTab = button.getAttribute('data-tab');

            // Deaktiviere alle Tabs
            tabButtons.forEach(btn => btn.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));

            // Aktiviere gewählten Tab
            button.classList.add('active');
            document.getElementById(`tab-${targetTab}`).classList.add('active');
        });
    });
}

// Init
document.addEventListener('DOMContentLoaded', async () => {
    setupSliders();
    setupTabs();
    setupHeatingBoostToggle();

    // Zeige Lade-Indikator
    const statusSection = document.querySelector('.status-grid');
    if (statusSection) {
        statusSection.style.opacity = '0.6';
    }

    // Lade Devices, Config und gelernte Parameter parallel
    await Promise.all([
        loadDevices(),
        loadConfig(),
        loadLearnedParams(),
        loadEnergyStats(),
        loadAlerts()
    ]);

    // Lade Status nach Config (braucht Config-Daten)
    await loadStatus();

    // Entferne Lade-Indikator
    if (statusSection) {
        statusSection.style.opacity = '1';
    }

    // Event Listeners
    document.getElementById('save-bathroom-config').addEventListener('click', saveConfig);
    document.getElementById('test-bathroom').addEventListener('click', testAutomation);

    // Reset Button
    const resetBtn = document.getElementById('reset-learned-btn');
    if (resetBtn) {
        resetBtn.addEventListener('click', resetLearnedParams);
    }

    // Preview Button
    const previewBtn = document.getElementById('preview-btn');
    if (previewBtn) {
        previewBtn.addEventListener('click', showPreview);
    }

    // Close Preview Modal
    const closePreviewBtn = document.getElementById('close-preview-btn');
    if (closePreviewBtn) {
        closePreviewBtn.addEventListener('click', () => {
            document.getElementById('preview-modal').style.display = 'none';
        });
    }

    // Dismiss Alerts
    const dismissAlertsBtn = document.getElementById('dismiss-alerts-btn');
    if (dismissAlertsBtn) {
        dismissAlertsBtn.addEventListener('click', () => {
            document.getElementById('alerts-card').style.display = 'none';
        });
    }

    // Event Listener für Raum-Filter
    const roomFilter = document.getElementById('room-filter');
    if (roomFilter) {
        roomFilter.addEventListener('change', (e) => {
            selectedRoomId = e.target.value;
            populateDeviceSelectors();
        });
    }

    // Aktoren-Test Event Listeners
    const dehumidifierOn = document.getElementById('test-dehumidifier-on');
    const dehumidifierOff = document.getElementById('test-dehumidifier-off');
    const heaterUp = document.getElementById('test-heater-up');
    const heaterDown = document.getElementById('test-heater-down');

    if (dehumidifierOn) {
        dehumidifierOn.addEventListener('click', () => controlActuator('dehumidifier', 'on'));
    }
    if (dehumidifierOff) {
        dehumidifierOff.addEventListener('click', () => controlActuator('dehumidifier', 'off'));
    }
    if (heaterUp) {
        heaterUp.addEventListener('click', () => controlActuator('heater', 'temp_up'));
    }
    if (heaterDown) {
        heaterDown.addEventListener('click', () => controlActuator('heater', 'temp_down'));
    }

    // Auto-refresh Status alle 10 Sekunden
    setInterval(loadStatus, 10000);

    // Lade Live-Sensor-Status initial
    await loadLiveSensorStatus();

    // Auto-refresh Live-Sensoren alle 5 Sekunden
    liveSensorInterval = setInterval(loadLiveSensorStatus, 5000);

    // === MANUELLES EVENT-FORMULAR ===

    // Submit Manual Event
    const submitManualEventBtn = document.getElementById('submit-manual-event');
    if (submitManualEventBtn) {
        submitManualEventBtn.addEventListener('click', submitManualEvent);
    }

    // Clear Manual Form
    const clearManualFormBtn = document.getElementById('clear-manual-form');
    if (clearManualFormBtn) {
        clearManualFormBtn.addEventListener('click', () => {
            document.getElementById('manual-start-time').value = '';
            document.getElementById('manual-end-time').value = '';
            document.getElementById('manual-peak-humidity').value = '75';
            document.getElementById('manual-notes').value = '';

            const resultEl = document.getElementById('manual-event-result');
            resultEl.style.display = 'none';
        });
    }

    // Set default times (jetzt - 30 Minuten bis jetzt)
    setDefaultManualEventTimes();
});

// === MANUELLE EVENT FUNKTIONEN ===

function setDefaultManualEventTimes() {
    const now = new Date();
    const thirtyMinutesAgo = new Date(now.getTime() - 30 * 60 * 1000);

    const startInput = document.getElementById('manual-start-time');
    const endInput = document.getElementById('manual-end-time');

    if (startInput && endInput) {
        // Format: YYYY-MM-DDTHH:MM
        startInput.value = formatDateTimeLocal(thirtyMinutesAgo);
        endInput.value = formatDateTimeLocal(now);
    }
}

function formatDateTimeLocal(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');

    return `${year}-${month}-${day}T${hours}:${minutes}`;
}

async function submitManualEvent() {
    const resultEl = document.getElementById('manual-event-result');
    const submitBtn = document.getElementById('submit-manual-event');

    // Validierung
    const startTime = document.getElementById('manual-start-time').value;
    const endTime = document.getElementById('manual-end-time').value;
    const peakHumidity = document.getElementById('manual-peak-humidity').value;
    const notes = document.getElementById('manual-notes').value;

    if (!startTime || !endTime) {
        resultEl.innerHTML = '<div class="error">❌ Bitte Start- und Endzeit angeben!</div>';
        resultEl.style.display = 'block';
        return;
    }

    // Parse Zeiten
    const start = new Date(startTime);
    const end = new Date(endTime);

    // Validiere Zeitspanne
    if (end <= start) {
        resultEl.innerHTML = '<div class="error">❌ Endzeit muss nach Startzeit liegen!</div>';
        resultEl.style.display = 'block';
        return;
    }

    const durationMinutes = (end - start) / 1000 / 60;
    if (durationMinutes > 120) {
        resultEl.innerHTML = '<div class="error">❌ Dauer zu lang! Maximal 2 Stunden erlaubt.</div>';
        resultEl.style.display = 'block';
        return;
    }

    try {
        submitBtn.disabled = true;
        resultEl.innerHTML = '<div class="loading">📤 Trage Event ein...</div>';
        resultEl.style.display = 'block';

        const response = await fetch('/api/luftentfeuchten/manual-event', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                start_time: start.toISOString(),
                end_time: end.toISOString(),
                peak_humidity: parseFloat(peakHumidity),
                notes: notes || null
            })
        });

        const data = await response.json();

        if (data.success) {
            resultEl.innerHTML = `
                <div class="success">
                    ✅ ${data.message}
                    <br><small>Event ID: ${data.event_id} | Dauer: ${Math.round(durationMinutes)} Minuten</small>
                </div>
            `;

            // Clear form nach Erfolg
            setTimeout(() => {
                document.getElementById('clear-manual-form').click();
                // Reload Status und Energie-Stats
                loadStatus();
                loadEnergyStats();
            }, 2000);

        } else {
            throw new Error(data.error || 'Unbekannter Fehler');
        }

    } catch (error) {
        console.error('Error submitting manual event:', error);
        resultEl.innerHTML = `<div class="error">❌ Fehler: ${error.message}</div>`;
    } finally {
        submitBtn.disabled = false;
    }
}
