// Dashboard JavaScript

// Update Status-Karten
async function updateStatus() {
    try {
        const data = await fetchJSON('/api/status');

        // Temperatur
        document.getElementById('temp-indoor').textContent = formatTemperature(data.temperature.indoor);
        document.getElementById('temp-outdoor').textContent = formatTemperature(data.temperature.outdoor);
        document.getElementById('humidity').textContent = formatPercent(data.temperature.humidity);

        // Umgebung
        const brightness = data.environment.brightness;
        document.getElementById('brightness').textContent = brightness !== null ? `${brightness} lux` : '--';
        document.getElementById('motion').textContent = data.environment.motion_detected ? 'Erkannt' : 'Keine';

        // Wetter mit deutscher Beschreibung
        const weatherCondition = data.environment.weather || '--';
        const weatherDescription = data.environment.weather_description || '';
        document.getElementById('weather').textContent = weatherDescription || weatherCondition;

        // Wetter Details
        if (data.weather) {
            document.getElementById('feels-like').textContent = formatTemperature(data.weather.feels_like);
            document.getElementById('wind-speed').textContent = data.weather.wind_speed !== null ? `${data.weather.wind_speed} m/s` : '--';
            document.getElementById('pressure').textContent = data.weather.pressure !== null ? `${data.weather.pressure} hPa` : '--';
            document.getElementById('clouds').textContent = data.weather.clouds !== null ? `${data.weather.clouds}%` : '--';

            // Update Wettervorhersage
            updateWeatherForecast(data.weather.forecast);
        }

        // Energie
        const price = data.energy.price;
        document.getElementById('energy-price').textContent = price !== null ? `${price.toFixed(4)} EUR/kWh` : '--';

        const consumption = data.energy.consumption;
        document.getElementById('power-consumption').textContent = consumption !== null ? `${consumption} W` : '--';

        const priceLevel = data.energy.price_level;
        const levelNames = { 1: 'Niedrig', 2: 'Mittel', 3: 'Hoch' };
        document.getElementById('price-level').textContent = levelNames[priceLevel] || '--';

        // Schimmelprävention
        if (data.mold_prevention) {
            const mold = data.mold_prevention;
            const riskDisplay = mold.risk_icon ? `${mold.risk_icon} ${mold.risk_level}` : mold.risk_level;
            document.getElementById('mold-risk-level').textContent = riskDisplay;
            document.getElementById('mold-dewpoint').textContent = mold.dewpoint !== null && mold.dewpoint !== undefined ? 
                `${mold.dewpoint.toFixed(1)}°C` : '--';
            document.getElementById('mold-condensation').textContent = mold.condensation_possible ? 
                '⚠️ Möglich' : '✓ Keine Gefahr';
            document.getElementById('mold-dehumidifier').textContent = mold.dehumidifier_running ? 
                '✓ Aktiv' : '○ Aus';
            
            // Färbe Risiko-Level basierend auf Stufe
            const riskElement = document.getElementById('mold-risk-level');
            riskElement.classList.remove('risk-low', 'risk-medium', 'risk-high', 'risk-critical');
            if (mold.risk_level === 'NIEDRIG') {
                riskElement.classList.add('risk-low');
            } else if (mold.risk_level === 'MITTEL') {
                riskElement.classList.add('risk-medium');
            } else if (mold.risk_level === 'HOCH') {
                riskElement.classList.add('risk-high');
            } else if (mold.risk_level === 'KRITISCH') {
                riskElement.classList.add('risk-critical');
            }
        }

    } catch (error) {
        console.error('Error updating status:', error);
    }
}

// Update Wettervorhersage
function updateWeatherForecast(forecast) {
    const container = document.getElementById('forecast-container');
    if (!forecast || forecast.length === 0) {
        container.innerHTML = '<p style="text-align: center; color: #888;">Keine Wettervorhersage verfügbar</p>';
        return;
    }

    // Wetter-Icons Mapping
    const weatherIcons = {
        'Clear': '☀️',
        'Clouds': '☁️',
        'Rain': '🌧️',
        'Drizzle': '🌦️',
        'Snow': '❄️',
        'Thunderstorm': '⛈️',
        'Mist': '🌫️',
        'Fog': '🌫️'
    };

    container.innerHTML = forecast.map(item => {
        const date = new Date(item.timestamp);
        const time = date.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' });
        const icon = weatherIcons[item.weather] || '🌡️';
        const rainProb = item.rain_probability || 0;

        return `
            <div class="forecast-item">
                <div class="forecast-time">${time}</div>
                <div class="forecast-icon">${icon}</div>
                <div class="forecast-temp">${formatTemperature(item.temperature)}</div>
                ${rainProb > 0 ? `<div class="forecast-rain">💧 ${Math.round(rainProb)}%</div>` : ''}
            </div>
        `;
    }).join('');
}

// Update Vorhersagen
async function updatePredictions() {
    try {
        const data = await fetchJSON('/api/predictions');

        // Beleuchtung
        updatePrediction('lighting', data.predictions.lighting);

        // Heizung
        updatePrediction('heating', data.predictions.heating);

        // Energie
        const energy = data.predictions.energy;
        const energyFill = document.getElementById('energy-confidence');
        energyFill.style.width = `${energy.confidence * 100}%`;
        document.getElementById('energy-conf-text').textContent = `${Math.round(energy.confidence * 100)}%`;
        document.getElementById('energy-optimization').textContent = energy.optimization;
        document.getElementById('savings-potential').textContent = energy.savings_potential;

        // Farbe basierend auf Status
        if (energy.status === 'savings_recommended') {
            energyFill.style.background = 'linear-gradient(90deg, #10b981, #059669)';
        } else if (energy.status === 'opportunity') {
            energyFill.style.background = 'linear-gradient(90deg, #3b82f6, #2563eb)';
        } else if (energy.status === 'optimal') {
            energyFill.style.background = 'linear-gradient(90deg, #3b82f6, #2563eb)';
        } else {
            energyFill.style.background = 'linear-gradient(90deg, #6b7280, #4b5563)';
        }

    } catch (error) {
        console.error('Error updating predictions:', error);
    }
}

// Hilfsfunktion: Update einzelne Vorhersage
function updatePrediction(type, prediction) {
    // Konfidenz-Balken mit Farbe basierend auf Status
    const confidenceFill = document.getElementById(`${type}-confidence`);
    confidenceFill.style.width = `${prediction.confidence * 100}%`;
    document.getElementById(`${type}-conf-text`).textContent = `${Math.round(prediction.confidence * 100)}%`;

    // Farbe basierend auf Status
    const status = prediction.status || 'optimal';
    if (status === 'action_recommended') {
        confidenceFill.style.background = 'linear-gradient(90deg, #f59e0b, #d97706)';
    } else if (status === 'savings_possible') {
        confidenceFill.style.background = 'linear-gradient(90deg, #10b981, #059669)';
    } else if (status === 'optimal') {
        confidenceFill.style.background = 'linear-gradient(90deg, #3b82f6, #2563eb)';
    } else {
        confidenceFill.style.background = 'linear-gradient(90deg, #6b7280, #4b5563)';
    }

    // Vorschläge
    const suggestionsEl = document.getElementById(`${type}-suggestions`);
    if (prediction.suggested_actions && prediction.suggested_actions.length > 0) {
        let html = '<ul>';
        prediction.suggested_actions.forEach(action => {
            // Icon basierend auf Inhalt
            let icon = '•';
            if (action.includes('💚') || action.includes('optimal') || action.includes('gut')) {
                icon = '✓';
            } else if (action.includes('💸') || action.includes('reduzieren') || action.includes('ausschalten')) {
                icon = '⚠';
            } else if (action.includes('🌙')) {
                icon = '🌙';
            } else if (action.includes('🏠')) {
                icon = '🏠';
            }

            html += `<li><span class="suggestion-icon">${icon}</span> ${action}</li>`;
        });
        html += '</ul>';
        suggestionsEl.innerHTML = html;
    } else {
        // Bessere Darstellung wenn keine Aktionen nötig
        if (status === 'optimal') {
            suggestionsEl.innerHTML = '<div class="no-action-needed">✓ Alles optimal - keine Aktionen erforderlich</div>';
        } else {
            suggestionsEl.innerHTML = '<div class="no-data">Keine Daten verfügbar</div>';
        }
    }

    // Begründung
    const reasoningEl = document.getElementById(`${type}-reasoning`);
    if (reasoningEl) {
        reasoningEl.textContent = prediction.reasoning;
    }
}

// Update Präsenz-Status
async function updatePresenceStatus() {
    try {
        const data = await fetchJSON('/api/automations/presence');

        const presenceDot = document.getElementById('presence-dot-dash');
        const presenceText = document.getElementById('presence-text-dash');
        const presenceCount = document.getElementById('presence-count-dash');

        // Status-Anzeige
        if (data.present) {
            presenceDot.className = 'presence-dot present';

            // Zeige wer zuhause ist (Homey User Tracking)
            if (data.mode === 'homey_users' && data.users) {
                const usersHome = data.users.filter(u => u.present).map(u => u.name);
                if (usersHome.length > 0) {
                    presenceText.textContent = `Anwesend: ${usersHome.join(', ')}`;
                } else {
                    presenceText.textContent = 'Anwesend';
                }

                // Zeige Personen-Anzahl
                presenceCount.textContent = `${data.users_home} von ${data.total_users} Person(en) zuhause`;
            } else {
                // Fallback: Motion-Sensor Modus
                presenceText.textContent = 'Anwesend';
                presenceCount.textContent = data.last_motion ?
                    new Date(data.last_motion).toLocaleString('de-DE') : '--';
            }
        } else {
            presenceDot.className = 'presence-dot away';
            presenceText.textContent = 'Abwesend';

            if (data.mode === 'homey_users') {
                presenceCount.textContent = 'Alle Nutzer sind unterwegs';
            } else {
                presenceCount.textContent = data.last_motion ?
                    `Letzte Bewegung: ${new Date(data.last_motion).toLocaleString('de-DE')}` : '--';
            }
        }

    } catch (error) {
        console.error('Error updating presence:', error);
        document.getElementById('presence-text-dash').textContent = 'Fehler beim Laden';
        document.getElementById('presence-count-dash').textContent = '--';
    }
}

// Update Verbindungsstatus
async function updateConnectionStatus() {
    try {
        const data = await fetchJSON('/api/connection-test');

        // Update Status-Dots
        const statusMap = {
            'smart_home_platform': 'platform',
            'weather_api': 'weather',
            'database': 'db',
            'energy_prices': 'energy'
        };

        for (const [key, shortKey] of Object.entries(statusMap)) {
            const dot = document.getElementById(`status-${shortKey}`);
            if (dot) {
                dot.className = 'status-dot ' + (data.results[key] ? 'ok' : 'error');
            }
        }

    } catch (error) {
        console.error('Error updating connection status:', error);
    }
}

// Auto-Refresh alle 10 Sekunden
function startAutoRefresh() {
    updateStatus();
    updatePredictions();
    updatePresenceStatus();
    updateConnectionStatus();

    setInterval(() => {
        updateStatus();
        updatePredictions();
        updatePresenceStatus();
    }, 10000); // 10 Sekunden

    // Verbindungsstatus alle 30 Sekunden
    setInterval(updateConnectionStatus, 30000);
}

// Start beim Laden der Seite
document.addEventListener('DOMContentLoaded', startAutoRefresh);
