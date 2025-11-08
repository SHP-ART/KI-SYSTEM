// KI Smart Home - Haupt JavaScript

// API Base URL
const API_BASE = window.location.origin;

// Utility: Fetch JSON
async function fetchJSON(endpoint) {
    try {
        const response = await fetch(`${API_BASE}${endpoint}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('Fetch error:', error);
        throw error;
    }
}

// Utility: POST JSON
async function postJSON(endpoint, data) {
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('POST error:', error);
        throw error;
    }
}

// Formatiere Temperatur
function formatTemperature(temp) {
    if (temp === null || temp === undefined) return '--';
    return `${temp.toFixed(1)}°C`;
}

// Formatiere Prozent
function formatPercent(value) {
    if (value === null || value === undefined) return '--';
    return `${Math.round(value)}%`;
}

// Zeige Benachrichtigung
function showNotification(message, type = 'info') {
    // Einfache Console-Benachrichtigung (kann später erweitert werden)
    console.log(`[${type.toUpperCase()}] ${message}`);
}
