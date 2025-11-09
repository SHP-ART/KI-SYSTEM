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

    // Luftentfeuchter (Switches/Sockets mit onoff)
    const dehumidifiers = filterByRoom(allDevices.filter(d => {
        return hasCap(d, 'onoff') && (d.domain === 'switch' || d.domain === 'socket');
    }));
    populateSelect('dehumidifier', dehumidifiers);

    // Heizungen/Thermostate
    const heaters = filterByRoom(allDevices.filter(d => d.domain === 'climate' || d.domain === 'thermostat'));
    populateSelect('heater', heaters);

    // Bewegungssensoren
    const motionSensors = filterByRoom(allDevices.filter(d => hasCap(d, 'alarm_motion')));
    populateSelect('motion-sensor', motionSensors);

    // Tür-Sensoren
    const doorSensors = filterByRoom(allDevices.filter(d => hasCap(d, 'alarm_contact')));
    populateSelect('door-sensor', doorSensors);
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

            // Schwellwerte
            setSlider('humidity-high', config.humidity_threshold_high || 70);
            setSlider('humidity-low', config.humidity_threshold_low || 60);
            setSlider('target-temperature', config.target_temperature || 22);
            setSlider('dehumidifier-delay', config.dehumidifier_delay || 5);

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
            humidity_threshold_high: parseFloat(document.getElementById('humidity-high').value),
            humidity_threshold_low: parseFloat(document.getElementById('humidity-low').value),
            target_temperature: parseFloat(document.getElementById('target-temperature').value),
            dehumidifier_delay: parseInt(document.getElementById('dehumidifier-delay').value)
        };

        // Validierung
        if (!config.humidity_sensor_id || !config.temperature_sensor_id || !config.dehumidifier_id) {
            alert('Bitte wählen Sie mindestens Luftfeuchtigkeit-Sensor, Temperatur-Sensor und Luftentfeuchter aus!');
            return;
        }

        const result = await postJSON('/api/luftentfeuchten/config', { config });

        if (result.success) {
            alert('✅ Konfiguration gespeichert!');
            loadStatus();
        }
    } catch (error) {
        console.error('Error saving config:', error);
        alert('Fehler beim Speichern der Konfiguration');
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
    }

    valueSpan.textContent = value + suffix;
}

// Setup Slider-Listeners
function setupSliders() {
    const sliders = ['humidity-high', 'humidity-low', 'target-temperature', 'dehumidifier-delay'];
    sliders.forEach(sliderId => {
        const slider = document.getElementById(sliderId);
        if (slider) {
            slider.addEventListener('input', () => updateSliderValue(sliderId));
            updateSliderValue(sliderId);
        }
    });
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

// Init
document.addEventListener('DOMContentLoaded', async () => {
    setupSliders();

    // Zeige Lade-Indikator
    const statusSection = document.querySelector('.status-grid');
    if (statusSection) {
        statusSection.style.opacity = '0.6';
    }

    // Lade Devices und Config parallel
    await Promise.all([
        loadDevices(),
        loadConfig()
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
});
