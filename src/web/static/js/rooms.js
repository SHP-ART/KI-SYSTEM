// Rooms Page JavaScript

let rooms = [];
let allDevices = [];
let deviceRoomAssignments = {}; // { device_id: room_id }
let selectedRoomId = null;

// Lade Räume
async function loadRooms() {
    try {
        const data = await fetchJSON('/api/rooms');
        rooms = data.rooms || [];
        deviceRoomAssignments = data.assignments || {};
        renderRooms();
        populateRoomSelector();
    } catch (error) {
        console.error('Error loading rooms:', error);
    }
}

// Rendere Räume
function renderRooms() {
    const container = document.getElementById('rooms-grid');

    if (rooms.length === 0) {
        container.innerHTML = '<div class="empty-state">Noch keine Räume vorhanden. Synchronisieren Sie Homey-Zonen oder fügen Sie manuell Räume hinzu.</div>';
        return;
    }

    container.innerHTML = rooms.map(room => {
        const deviceCount = Object.values(deviceRoomAssignments).filter(rid => rid === room.id).length;

        return `
            <div class="room-card" data-room-id="${room.id}" onclick="showRoomDetails('${room.id}')">
                <div class="room-icon">${room.icon || '🏠'}</div>
                <div class="room-info">
                    <h4>${room.name}</h4>
                    <p class="room-device-count">${deviceCount} Geräte</p>
                </div>
            </div>
        `;
    }).join('');
}

// Sync Homey Zones
document.getElementById('sync-zones').addEventListener('click', async () => {
    const statusEl = document.getElementById('sync-status');
    statusEl.innerHTML = '<p class="info">Synchronisiere Zonen...</p>';

    try {
        const result = await postJSON('/api/rooms/sync-homey-zones', {});

        if (result.success) {
            statusEl.innerHTML = `<p class="success">✓ ${result.zones_imported} Zonen importiert!</p>`;
            await loadRooms();
            setTimeout(() => statusEl.innerHTML = '', 3000);
        }
    } catch (error) {
        console.error('Error syncing zones:', error);
        statusEl.innerHTML = '<p class="error">✗ Fehler beim Synchronisieren</p>';
    }
});

// Sync Device Assignments from Homey
document.getElementById('sync-device-assignments').addEventListener('click', async () => {
    const statusEl = document.getElementById('sync-status');
    statusEl.innerHTML = '<p class="info">Importiere Geräte-Zuordnungen aus Homey...</p>';

    try {
        const result = await postJSON('/api/rooms/sync-device-assignments', {});

        if (result.success) {
            statusEl.innerHTML = `<p class="success">✓ ${result.assignments_imported} Geräte-Zuordnungen importiert!</p>`;
            await loadRooms();
            setTimeout(() => statusEl.innerHTML = '', 3000);
        }
    } catch (error) {
        console.error('Error syncing device assignments:', error);
        statusEl.innerHTML = '<p class="error">✗ Fehler beim Importieren</p>';
    }
});

// Neuen Raum hinzufügen
document.getElementById('add-room-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const name = document.getElementById('new-room-name').value;
    const icon = document.getElementById('new-room-icon').value;

    try {
        const result = await postJSON('/api/rooms', {
            name,
            icon
        });

        if (result.success) {
            alert('Raum hinzugefügt!');
            document.getElementById('add-room-form').reset();
            await loadRooms();
        }
    } catch (error) {
        console.error('Error adding room:', error);
        alert('Fehler beim Hinzufügen des Raums');
    }
});

// Populiere Raum-Selector
function populateRoomSelector() {
    const select = document.getElementById('room-select');
    select.innerHTML = '<option value="">Raum wählen...</option>' +
        rooms.map(room => `<option value="${room.id}">${room.icon || '🏠'} ${room.name}</option>`).join('');
}

// Raum-Auswahl geändert
document.getElementById('room-select').addEventListener('change', async (e) => {
    selectedRoomId = e.target.value;

    if (!selectedRoomId) {
        document.getElementById('room-devices-container').classList.add('hidden');
        return;
    }

    const room = rooms.find(r => r.id === selectedRoomId);
    document.getElementById('selected-room-name').textContent = room.name;
    document.getElementById('room-devices-container').classList.remove('hidden');

    // Lade Geräte falls noch nicht geladen
    if (allDevices.length === 0) {
        await loadAllDevices();
    }

    renderDeviceLists();
    updateDeviceCountBadge();
});

// Lade alle Geräte
async function loadAllDevices() {
    try {
        const data = await fetchJSON('/api/devices');
        allDevices = data.devices || [];
    } catch (error) {
        console.error('Error loading devices:', error);
    }
}

// Rendere Geräte-Listen
function renderDeviceLists() {
    if (!selectedRoomId) return;

    // Zugeordnete Geräte
    const assignedDevices = allDevices.filter(d => deviceRoomAssignments[d.id] === selectedRoomId);
    const assignedContainer = document.getElementById('assigned-devices-list');

    if (assignedDevices.length === 0) {
        assignedContainer.innerHTML = '<p class="empty-state">Noch keine Geräte zugeordnet</p>';
    } else {
        assignedContainer.innerHTML = assignedDevices.map(device => `
            <div class="device-item">
                ${getDeviceIcon(device.domain)} ${device.name}
                <button class="btn-small btn-danger" onclick="removeDeviceFromRoom('${device.id}')">
                    Entfernen
                </button>
            </div>
        `).join('');
    }

    // Verfügbare Geräte (nicht zugeordnet oder in anderem Raum)
    const availableDevices = allDevices.filter(d => !deviceRoomAssignments[d.id] || deviceRoomAssignments[d.id] !== selectedRoomId);
    const availableContainer = document.getElementById('available-devices-list');

    if (availableDevices.length === 0) {
        availableContainer.innerHTML = '<p class="empty-state">Alle Geräte zugeordnet</p>';
    } else {
        availableContainer.innerHTML = availableDevices.map(device => `
            <div class="device-item">
                ${getDeviceIcon(device.domain)} ${device.name}
                <button class="btn-small btn-primary" onclick="addDeviceToRoom('${device.id}')">
                    Hinzufügen
                </button>
            </div>
        `).join('');
    }
}

// Geräte-Suche
document.getElementById('device-search').addEventListener('input', (e) => {
    const searchTerm = e.target.value.toLowerCase();
    const availableContainer = document.getElementById('available-devices-list');
    const items = availableContainer.querySelectorAll('.device-item');

    items.forEach(item => {
        const text = item.textContent.toLowerCase();
        item.style.display = text.includes(searchTerm) ? 'flex' : 'none';
    });
});

// Gerät zu Raum hinzufügen
async function addDeviceToRoom(deviceId) {
    if (!selectedRoomId) return;

    try {
        const result = await postJSON('/api/rooms/assign-device', {
            device_id: deviceId,
            room_id: selectedRoomId
        });

        if (result.success) {
            deviceRoomAssignments[deviceId] = selectedRoomId;
            renderDeviceLists();
            updateDeviceCountBadge();
            renderRooms(); // Update room cards
        }
    } catch (error) {
        console.error('Error assigning device:', error);
    }
}

// Gerät aus Raum entfernen
async function removeDeviceFromRoom(deviceId) {
    try {
        const result = await postJSON('/api/rooms/unassign-device', {
            device_id: deviceId
        });

        if (result.success) {
            delete deviceRoomAssignments[deviceId];
            renderDeviceLists();
            updateDeviceCountBadge();
            renderRooms();
        }
    } catch (error) {
        console.error('Error unassigning device:', error);
    }
}

// Update Device Count Badge
function updateDeviceCountBadge() {
    if (!selectedRoomId) return;

    const count = Object.values(deviceRoomAssignments).filter(rid => rid === selectedRoomId).length;
    const badge = document.getElementById('device-count-badge');
    badge.textContent = `${count} Geräte`;
    badge.style.display = count > 0 ? 'inline-block' : 'none';
}

// Zeige Raum-Details Modal
async function showRoomDetails(roomId) {
    const room = rooms.find(r => r.id === roomId);
    if (!room) return;

    const modal = document.getElementById('room-modal');
    document.getElementById('modal-room-title').textContent = room.name;
    document.getElementById('modal-room-icon').textContent = room.icon || '🏠';
    document.getElementById('modal-room-id').textContent = room.id;

    // Count devices by type
    const roomDevices = allDevices.filter(d => deviceRoomAssignments[d.id] === roomId);
    document.getElementById('modal-room-device-count').textContent = roomDevices.length;

    const lightCount = roomDevices.filter(d => d.domain === 'light').length;
    const sensorCount = roomDevices.filter(d => d.domain === 'sensor').length;
    const switchCount = roomDevices.filter(d => d.domain === 'switch').length;
    const climateCount = roomDevices.filter(d => d.domain === 'climate').length;

    document.getElementById('room-lights-count').textContent = lightCount;
    document.getElementById('room-sensors-count').textContent = sensorCount;
    document.getElementById('room-switches-count').textContent = switchCount;
    document.getElementById('room-climate-count').textContent = climateCount;

    // Room actions
    document.getElementById('room-all-lights-on').onclick = () => controlRoomLights(roomId, 'on');
    document.getElementById('room-all-lights-off').onclick = () => controlRoomLights(roomId, 'off');
    document.getElementById('edit-room').onclick = () => showEditRoomForm(roomId, room.name, room.icon);
    document.getElementById('delete-room').onclick = () => deleteRoom(roomId);

    // Hide edit form initially
    document.getElementById('edit-room-form').style.display = 'none';

    modal.style.display = 'block';
}

// Zeige Edit-Formular
function showEditRoomForm(roomId, currentName, currentIcon) {
    const editForm = document.getElementById('edit-room-form');
    const nameInput = document.getElementById('edit-room-name');
    const iconSelect = document.getElementById('edit-room-icon');

    // Fülle Formular mit aktuellen Werten
    nameInput.value = currentName;
    iconSelect.value = currentIcon;

    // Zeige Formular
    editForm.style.display = 'block';

    // Event Handlers
    document.getElementById('save-room-edit').onclick = () => saveRoomEdit(roomId);
    document.getElementById('cancel-room-edit').onclick = () => {
        editForm.style.display = 'none';
    };
}

// Speichere Raum-Änderungen
async function saveRoomEdit(roomId) {
    const newName = document.getElementById('edit-room-name').value;
    const newIcon = document.getElementById('edit-room-icon').value;

    if (!newName.trim()) {
        alert('Bitte geben Sie einen Namen ein');
        return;
    }

    try {
        const result = await postJSON('/api/rooms/update', {
            room_id: roomId,
            name: newName,
            icon: newIcon
        });

        if (result.success) {
            alert('Raum aktualisiert!');
            document.getElementById('edit-room-form').style.display = 'none';
            await loadRooms();
            closeModal();
        }
    } catch (error) {
        console.error('Error updating room:', error);
        alert('Fehler beim Aktualisieren des Raums');
    }
}

// Raum-Lichter steuern
async function controlRoomLights(roomId, action) {
    try {
        const result = await postJSON('/api/rooms/control-lights', {
            room_id: roomId,
            action
        });

        if (result.success) {
            alert(`${result.devices_controlled} Lichter ${action === 'on' ? 'eingeschaltet' : 'ausgeschaltet'}`);
        }
    } catch (error) {
        console.error('Error controlling lights:', error);
    }
}

// Raum löschen
async function deleteRoom(roomId) {
    if (!confirm('Möchten Sie diesen Raum wirklich löschen? Geräte-Zuordnungen bleiben erhalten.')) {
        return;
    }

    try {
        const result = await postJSON('/api/rooms/delete', {
            room_id: roomId
        });

        if (result.success) {
            alert('Raum gelöscht');
            closeModal();
            await loadRooms();
        }
    } catch (error) {
        console.error('Error deleting room:', error);
    }
}

// Modal schließen
function closeModal() {
    document.getElementById('room-modal').style.display = 'none';
}

document.querySelector('.close').addEventListener('click', closeModal);

window.addEventListener('click', (e) => {
    const modal = document.getElementById('room-modal');
    if (e.target === modal) {
        closeModal();
    }
});

// Hilfsfunktionen
function getDeviceIcon(domain) {
    const icons = {
        'light': '💡',
        'climate': '🌡️',
        'switch': '🔌',
        'sensor': '📊'
    };
    return icons[domain] || '📱';
}

// ===== FENSTER-ZUORDNUNG =====

// Lade und zeige Fenster-Zuordnung
async function loadWindowAssignments() {
    const loadingEl = document.getElementById('window-assignment-loading');
    const containerEl = document.getElementById('window-assignment-container');
    const emptyEl = document.getElementById('window-assignment-empty');

    if (loadingEl) loadingEl.style.display = 'block';
    if (containerEl) containerEl.innerHTML = '';
    if (emptyEl) emptyEl.style.display = 'none';

    try {
        // Lade alle Geräte falls noch nicht geladen
        if (allDevices.length === 0) {
            await loadAllDevices();
        }

        // Filtere Fenster-Sensoren (binary_sensor mit window/door class)
        const windows = allDevices.filter(d =>
            (d.domain === 'binary_sensor' || d.domain === 'sensor') &&
            (d.attributes?.device_class === 'window' ||
             d.attributes?.device_class === 'door' ||
             d.name.toLowerCase().includes('fenster') ||
             d.name.toLowerCase().includes('window'))
        );

        if (loadingEl) loadingEl.style.display = 'none';

        if (windows.length === 0) {
            if (emptyEl) emptyEl.style.display = 'block';
            return;
        }

        // Rendere Fenster-Liste
        renderWindowAssignments(windows);

    } catch (error) {
        console.error('Error loading window assignments:', error);
        if (loadingEl) loadingEl.style.display = 'none';
    }
}

// Rendere Fenster-Zuordnungsliste
function renderWindowAssignments(windows) {
    const container = document.getElementById('window-assignment-container');
    if (!container) return;

    const html = `
        <div style="overflow-x: auto;">
            <table class="window-assignment-table" style="width: 100%; border-collapse: collapse;">
                <thead>
                    <tr style="background: #f9fafb; border-bottom: 2px solid #e5e7eb;">
                        <th style="padding: 12px; text-align: left; font-weight: 600; color: #374151;">Fenster/Tür</th>
                        <th style="padding: 12px; text-align: left; font-weight: 600; color: #374151;">Aktueller Raum</th>
                        <th style="padding: 12px; text-align: left; font-weight: 600; color: #374151;">Zuordnen zu</th>
                    </tr>
                </thead>
                <tbody>
                    ${windows.map(window => {
                        const currentRoom = deviceRoomAssignments[window.id];
                        const currentRoomObj = rooms.find(r => r.id === currentRoom);

                        return `
                            <tr style="border-bottom: 1px solid #e5e7eb;">
                                <td style="padding: 12px;">
                                    <div style="display: flex; align-items: center; gap: 8px;">
                                        <span style="font-size: 1.2em;">🪟</span>
                                        <span style="font-weight: 500;">${window.name}</span>
                                    </div>
                                </td>
                                <td style="padding: 12px;">
                                    ${currentRoomObj ?
                                        `<span style="background: #dbeafe; color: #1e40af; padding: 4px 10px; border-radius: 6px; font-size: 0.9em;">
                                            ${currentRoomObj.icon || '🏠'} ${currentRoomObj.name}
                                        </span>` :
                                        `<span style="color: #9ca3af; font-style: italic;">Nicht zugeordnet</span>`
                                    }
                                </td>
                                <td style="padding: 12px;">
                                    <select
                                        class="window-room-select"
                                        data-window-id="${window.id}"
                                        style="padding: 6px 10px; border: 1px solid #d1d5db; border-radius: 6px; background: white; min-width: 150px;"
                                        onchange="assignWindowToRoom('${window.id}', this.value)"
                                    >
                                        <option value="">-- Raum wählen --</option>
                                        ${rooms.map(room => `
                                            <option value="${room.id}" ${currentRoom === room.id ? 'selected' : ''}>
                                                ${room.icon || '🏠'} ${room.name}
                                            </option>
                                        `).join('')}
                                    </select>
                                </td>
                            </tr>
                        `;
                    }).join('')}
                </tbody>
            </table>
        </div>
    `;

    container.innerHTML = html;
}

// Ordne Fenster einem Raum zu
async function assignWindowToRoom(windowId, roomId) {
    try {
        if (!roomId) {
            // Entferne Zuordnung
            const result = await postJSON('/api/rooms/unassign-device', {
                device_id: windowId
            });

            if (result.success) {
                delete deviceRoomAssignments[windowId];
                loadWindowAssignments(); // Neu laden
                renderRooms(); // Update room cards
            }
        } else {
            // Setze neue Zuordnung
            const result = await postJSON('/api/rooms/assign-device', {
                device_id: windowId,
                room_id: roomId
            });

            if (result.success) {
                deviceRoomAssignments[windowId] = roomId;
                loadWindowAssignments(); // Neu laden
                renderRooms(); // Update room cards
            }
        }
    } catch (error) {
        console.error('Error assigning window to room:', error);
        alert('Fehler beim Zuordnen des Fensters');
    }
}

// Init
document.addEventListener('DOMContentLoaded', () => {
    loadRooms();
    loadAllDevices();

    // Warte kurz bis Räume geladen sind, dann lade Fenster
    setTimeout(() => {
        loadWindowAssignments();
    }, 500);
});
