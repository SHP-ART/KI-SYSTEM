// Devices Page JavaScript

let allDevices = [];
let allRooms = [];
let zoneNameMap = {};
let currentFilter = 'all';
let currentView = 'grid';
let searchTerm = '';

// Lade alle Geräte und Räume
async function loadDevices() {
    try {
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
        });

        updateStatistics();
        renderDevices();
    } catch (error) {
        console.error('Error loading devices:', error);
        document.getElementById('devices-container').innerHTML =
            '<div class="error">Fehler beim Laden der Geräte</div>';
    }
}

// Update Statistiken
function updateStatistics() {
    const stats = {
        total: allDevices.length,
        lights: allDevices.filter(d => d.domain === 'light').length,
        switches: allDevices.filter(d => d.domain === 'switch' || d.domain === 'socket').length,
        climate: allDevices.filter(d => d.domain === 'climate').length,
        sensors: allDevices.filter(d => d.domain === 'sensor').length
    };

    document.getElementById('total-devices').textContent = stats.total;
    document.getElementById('lights-count').textContent = stats.lights;
    document.getElementById('switches-count').textContent = stats.switches;
    document.getElementById('climate-count').textContent = stats.climate;
    document.getElementById('sensors-count').textContent = stats.sensors;
}

// Filtere Geräte
function getFilteredDevices() {
    let filtered = allDevices;

    // Filter nach Typ
    if (currentFilter !== 'all') {
        filtered = filtered.filter(d => {
            if (currentFilter === 'switch') {
                return d.domain === 'switch' || d.domain === 'socket';
            }
            return d.domain === currentFilter;
        });
    }

    // Filter nach Suchbegriff
    if (searchTerm) {
        const term = searchTerm.toLowerCase();
        filtered = filtered.filter(d =>
            d.name.toLowerCase().includes(term) ||
            (d.zoneName && d.zoneName.toLowerCase().includes(term)) ||
            getDomainName(d.domain).toLowerCase().includes(term)
        );
    }

    return filtered;
}

// Rendere Geräte
function renderDevices() {
    const container = document.getElementById('devices-container');
    const filtered = getFilteredDevices();

    // Update Titel
    const title = document.getElementById('devices-section-title');
    if (searchTerm) {
        title.textContent = `Suchergebnisse (${filtered.length})`;
    } else if (currentFilter !== 'all') {
        title.textContent = `${getDomainName(currentFilter)} (${filtered.length})`;
    } else {
        title.textContent = `Alle Geräte (${filtered.length})`;
    }

    if (filtered.length === 0) {
        container.innerHTML = '<div class="empty-state">Keine Geräte gefunden</div>';
        return;
    }

    // Setze View-Klasse
    container.className = `devices-display ${currentView}-view`;

    // Rendere basierend auf aktueller Ansicht
    if (currentView === 'grid') {
        renderGridView(container, filtered);
    } else if (currentView === 'list') {
        renderListView(container, filtered);
    } else if (currentView === 'rooms') {
        renderRoomsView(container, filtered);
    }
}

// Grid-Ansicht
function renderGridView(container, devices) {
    container.innerHTML = devices.map(device => {
        const isOn = device.state === 'on' || device.state === 'true';
        const icon = getDeviceIcon(device.domain);

        return `
            <div class="device-card ${isOn ? 'on' : ''}" data-id="${device.id}">
                <div class="device-card-header">
                    <div class="device-icon">${icon}</div>
                    <div class="device-status-indicator ${isOn ? 'on' : ''}"></div>
                </div>
                <div class="device-card-body">
                    <h4>${device.name}</h4>
                    <p class="device-zone">${device.zoneName || 'Kein Raum'}</p>
                    <div class="device-capabilities">
                        <span class="capability-badge">${getDomainName(device.domain)}</span>
                        ${isOn ? '<span class="capability-badge" style="background-color: #d1fae5; color: #065f46;">An</span>' : ''}
                    </div>
                </div>
            </div>
        `;
    }).join('');

    attachDeviceClickListeners();
}

// Listen-Ansicht
function renderListView(container, devices) {
    container.innerHTML = devices.map(device => {
        const isOn = device.state === 'on' || device.state === 'true';
        const icon = getDeviceIcon(device.domain);

        return `
            <div class="device-list-item ${isOn ? 'on' : ''}" data-id="${device.id}">
                <div class="device-list-icon">${icon}</div>
                <div class="device-list-info">
                    <h4>${device.name}</h4>
                    <p class="device-zone">${device.zoneName || 'Kein Raum'} · ${getDomainName(device.domain)}</p>
                </div>
                <div class="device-list-status ${isOn ? 'on' : 'off'}">
                    ${isOn ? '● An' : '○ Aus'}
                </div>
                <div class="device-list-actions">
                    <button class="btn btn-small btn-primary" onclick="quickToggleDevice('${device.id}', event)">
                        ${isOn ? 'Aus' : 'Ein'}
                    </button>
                </div>
            </div>
        `;
    }).join('');

    attachDeviceClickListeners();
}

// Raum-Ansicht
function renderRoomsView(container, devices) {
    // Gruppiere nach Raum
    const byRoom = {};

    devices.forEach(device => {
        const room = device.zoneName || 'Ohne Raum';
        if (!byRoom[room]) {
            byRoom[room] = [];
        }
        byRoom[room].push(device);
    });

    // Sortiere Räume alphabetisch, aber "Ohne Raum" kommt ans Ende
    const rooms = Object.keys(byRoom).sort((a, b) => {
        if (a === 'Ohne Raum') return 1;
        if (b === 'Ohne Raum') return -1;
        return a.localeCompare(b);
    });

    container.innerHTML = rooms.map(room => {
        const roomDevices = byRoom[room];

        // Finde Raum-Icon (falls verfügbar)
        const roomData = allRooms.find(r => r.name === room);
        const roomIcon = roomData?.icon || '🏠';

        return `
            <div class="room-group">
                <div class="room-group-header">
                    <h4>${roomIcon} ${room}</h4>
                    <span class="room-device-count">${roomDevices.length} ${roomDevices.length === 1 ? 'Gerät' : 'Geräte'}</span>
                </div>
                <div class="room-devices-grid">
                    ${roomDevices.map(device => {
                        const isOn = device.state === 'on' || device.state === 'true';
                        const icon = getDeviceIcon(device.domain);

                        return `
                            <div class="device-card ${isOn ? 'on' : ''}" data-id="${device.id}">
                                <div class="device-card-header">
                                    <div class="device-icon">${icon}</div>
                                    <div class="device-status-indicator ${isOn ? 'on' : ''}"></div>
                                </div>
                                <div class="device-card-body">
                                    <h4>${device.name}</h4>
                                    <div class="device-capabilities">
                                        <span class="capability-badge">${getDomainName(device.domain)}</span>
                                    </div>
                                </div>
                            </div>
                        `;
                    }).join('')}
                </div>
            </div>
        `;
    }).join('');

    attachDeviceClickListeners();
}

// Event Listener für Geräte-Karten
function attachDeviceClickListeners() {
    document.querySelectorAll('.device-card, .device-list-item').forEach(card => {
        card.addEventListener('click', (e) => {
            // Verhindere Modal-Öffnung wenn Button geklickt
            if (e.target.tagName === 'BUTTON') return;

            const deviceId = card.dataset.id;
            const device = allDevices.find(d => d.id === deviceId);
            if (device) {
                showDeviceModal(device);
            }
        });
    });
}

// Gerät-Icon
function getDeviceIcon(domain) {
    const icons = {
        'light': '💡',
        'climate': '🌡️',
        'thermostat': '🌡️',
        'heater': '🔥',
        'switch': '🔌',
        'socket': '🔌',
        'sensor': '📊'
    };
    return icons[domain] || '📱';
}

// Domain-Name
function getDomainName(domain) {
    const names = {
        'light': 'Beleuchtung',
        'climate': 'Klima',
        'thermostat': 'Thermostat',
        'heater': 'Heizung',
        'switch': 'Schalter',
        'socket': 'Steckdose',
        'sensor': 'Sensor'
    };
    return names[domain] || domain;
}

// Filter-Buttons
function setupFilters() {
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentFilter = btn.dataset.filter;
            renderDevices();
        });
    });
}

// View-Toggle
function setupViewToggle() {
    document.querySelectorAll('.view-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.view-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentView = btn.dataset.view;
            renderDevices();
        });
    });
}

// Suche
function setupSearch() {
    const searchInput = document.getElementById('device-search');
    searchInput.addEventListener('input', (e) => {
        searchTerm = e.target.value;
        renderDevices();
    });
}

// Quick Toggle Device
async function quickToggleDevice(deviceId, event) {
    event.stopPropagation();
    const device = allDevices.find(d => d.id === deviceId);
    const isOn = device.state === 'on' || device.state === 'true';
    const action = isOn ? 'turn_off' : 'turn_on';

    try {
        const result = await postJSON(`/api/devices/${deviceId}/control`, { action });
        if (result.success) {
            setTimeout(loadDevices, 500);
        }
    } catch (error) {
        console.error('Error toggling device:', error);
    }
}

// Zeige Device Modal
function showDeviceModal(device) {
    const modal = document.getElementById('device-modal');
    const isOn = device.state === 'on' || device.state === 'true';

    document.getElementById('modal-device-name').textContent = device.name;
    document.getElementById('modal-device-type').textContent = getDomainName(device.domain);
    document.getElementById('modal-device-zone').textContent = device.zone || 'Kein Raum';

    // Status
    const stateHTML = `
        <div class="device-state-info">
            <div class="state-item">
                <span class="state-label">Status:</span>
                <span class="state-value ${isOn ? 'on' : 'off'}">${isOn ? '● An' : '○ Aus'}</span>
            </div>
            ${device.attributes && device.attributes.current_temperature ? `
                <div class="state-item">
                    <span class="state-label">Temperatur:</span>
                    <span class="state-value">${device.attributes.current_temperature}°C</span>
                </div>
            ` : ''}
            ${device.attributes && device.attributes.brightness ? `
                <div class="state-item">
                    <span class="state-label">Helligkeit:</span>
                    <span class="state-value">${Math.round((device.attributes.brightness / 255) * 100)}%</span>
                </div>
            ` : ''}
        </div>
    `;
    document.getElementById('modal-device-state').innerHTML = stateHTML;

    // Controls
    let controlsHTML = '';
    if (device.domain === 'light' || device.domain === 'switch' || device.domain === 'socket') {
        controlsHTML = `
            <div class="modal-controls">
                <button class="btn btn-primary" onclick="controlDevice('${device.id}', 'turn_on')">
                    💡 Einschalten
                </button>
                <button class="btn btn-secondary" onclick="controlDevice('${device.id}', 'turn_off')">
                    Ausschalten
                </button>
                ${device.domain === 'light' ? `
                    <div class="form-group" style="margin-top: 1rem;">
                        <label>Helligkeit: <span id="brightness-display">100%</span></label>
                        <input type="range" id="brightness-slider" min="0" max="255" value="255" class="slider">
                    </div>
                    <button class="btn btn-primary" onclick="setBrightness('${device.id}')">
                        Helligkeit setzen
                    </button>
                ` : ''}
            </div>
        `;
    } else if (device.domain === 'climate' || device.domain === 'thermostat') {
        const currentTemp = device.attributes.target_temperature || 20;
        controlsHTML = `
            <div class="modal-controls">
                <div class="form-group">
                    <label>Zieltemperatur: <span id="temp-display">${currentTemp}°C</span></label>
                    <input type="range" id="temp-slider" min="15" max="30" step="0.5" value="${currentTemp}" class="slider">
                </div>
                <button class="btn btn-primary" onclick="setTemperature('${device.id}')">
                    🌡️ Temperatur setzen
                </button>
            </div>
        `;
    } else {
        controlsHTML = '<p class="empty-state">Dieses Gerät kann nicht gesteuert werden.</p>';
    }

    document.getElementById('modal-device-controls').innerHTML = controlsHTML;

    // Event Listener für Slider
    setupSliders();

    modal.style.display = 'block';
}

// Setup Sliders
function setupSliders() {
    const tempSlider = document.getElementById('temp-slider');
    if (tempSlider) {
        tempSlider.addEventListener('input', (e) => {
            document.getElementById('temp-display').textContent = `${e.target.value}°C`;
        });
    }

    const brightnessSlider = document.getElementById('brightness-slider');
    if (brightnessSlider) {
        brightnessSlider.addEventListener('input', (e) => {
            const percent = Math.round((e.target.value / 255) * 100);
            document.getElementById('brightness-display').textContent = `${percent}%`;
        });
    }
}

// Gerät steuern
async function controlDevice(deviceId, action) {
    try {
        const result = await postJSON(`/api/devices/${deviceId}/control`, { action });

        if (result.success) {
            showNotification('✓ Gerät erfolgreich gesteuert', 'success');
            closeModal();
            setTimeout(loadDevices, 1000);
        } else {
            showNotification('✗ Fehler beim Steuern des Geräts', 'error');
        }
    } catch (error) {
        console.error('Error controlling device:', error);
        showNotification('✗ Fehler beim Steuern des Geräts', 'error');
    }
}

// Helligkeit setzen
async function setBrightness(deviceId) {
    try {
        const brightnessSlider = document.getElementById('brightness-slider');
        const brightness = parseInt(brightnessSlider.value);

        const result = await postJSON(`/api/devices/${deviceId}/control`, {
            action: 'turn_on',
            brightness
        });

        if (result.success) {
            showNotification('✓ Helligkeit erfolgreich gesetzt', 'success');
            closeModal();
            setTimeout(loadDevices, 1000);
        } else {
            showNotification('✗ Fehler beim Setzen der Helligkeit', 'error');
        }
    } catch (error) {
        console.error('Error setting brightness:', error);
        showNotification('✗ Fehler beim Setzen der Helligkeit', 'error');
    }
}

// Temperatur setzen
async function setTemperature(deviceId) {
    try {
        const tempSlider = document.getElementById('temp-slider');
        const temperature = parseFloat(tempSlider.value);

        const result = await postJSON(`/api/devices/${deviceId}/control`, {
            action: 'set_temperature',
            temperature
        });

        if (result.success) {
            showNotification('✓ Temperatur erfolgreich gesetzt', 'success');
            closeModal();
            setTimeout(loadDevices, 1000);
        } else {
            showNotification('✗ Fehler beim Setzen der Temperatur', 'error');
        }
    } catch (error) {
        console.error('Error setting temperature:', error);
        showNotification('✗ Fehler beim Setzen der Temperatur', 'error');
    }
}

// Schnellaktionen
function setupQuickActions() {
    document.getElementById('all-lights-on').addEventListener('click', async () => {
        await bulkAction('light', 'turn_on');
    });

    document.getElementById('all-lights-off').addEventListener('click', async () => {
        await bulkAction('light', 'turn_off');
    });

    document.getElementById('all-switches-off').addEventListener('click', async () => {
        await bulkAction('switch', 'turn_off');
    });

    document.getElementById('refresh-devices').addEventListener('click', loadDevices);
}

// Bulk Action
async function bulkAction(domain, action) {
    const resultEl = document.getElementById('quick-action-result');
    const devices = allDevices.filter(d => d.domain === domain || (domain === 'switch' && d.domain === 'socket'));

    if (devices.length === 0) {
        resultEl.textContent = `Keine ${getDomainName(domain)} gefunden`;
        resultEl.className = 'action-result error';
        resultEl.style.display = 'block';
        setTimeout(() => resultEl.style.display = 'none', 3000);
        return;
    }

    resultEl.textContent = `Führe Aktion für ${devices.length} Geräte aus...`;
    resultEl.className = 'action-result';
    resultEl.style.display = 'block';

    let success = 0;
    for (const device of devices) {
        try {
            const result = await postJSON(`/api/devices/${device.id}/control`, { action });
            if (result.success) success++;
        } catch (error) {
            console.error('Error:', error);
        }
    }

    resultEl.textContent = `✓ ${success} von ${devices.length} Geräten erfolgreich gesteuert`;
    resultEl.className = 'action-result success';
    setTimeout(() => {
        resultEl.style.display = 'none';
        loadDevices();
    }, 3000);
}

// Schließe Modal
function closeModal() {
    document.getElementById('device-modal').style.display = 'none';
}

// Modal Schließen-Button
document.querySelector('.close').addEventListener('click', closeModal);

// Klick außerhalb des Modals schließt es
window.addEventListener('click', (e) => {
    const modal = document.getElementById('device-modal');
    if (e.target === modal) {
        closeModal();
    }
});

// Init
document.addEventListener('DOMContentLoaded', () => {
    loadDevices();
    setupFilters();
    setupViewToggle();
    setupSearch();
    setupQuickActions();

    // Auto-refresh alle 15 Sekunden
    setInterval(loadDevices, 15000);
});
