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

    // Auto-refresh Status alle 10 Sekunden
    setInterval(loadStatus, 10000);
});
