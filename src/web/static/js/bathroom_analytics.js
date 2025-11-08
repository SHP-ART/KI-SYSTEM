// Bathroom Analytics Dashboard JavaScript

let analyticsData = null;
let eventsData = null;

// Lade alle Daten
async function loadAllData() {
    try {
        // Lade Analytics parallel
        const [analytics, events] = await Promise.all([
            fetchJSON('/api/bathroom/analytics?days=30'),
            fetchJSON('/api/bathroom/events?days=30&limit=50')
        ]);

        analyticsData = analytics;
        eventsData = events;

        renderDashboard();
    } catch (error) {
        console.error('Error loading analytics data:', error);
        alert('Fehler beim Laden der Analytics-Daten');
    }
}

function renderDashboard() {
    if (!analyticsData || !analyticsData.available) {
        showNoData();
        return;
    }

    renderLearningStatus();
    renderStatistics();
    renderPrediction();
    renderTrendChart();
    renderPeakHours();
    renderWeekdayDistribution();
    renderEventHistory();
}

function renderLearningStatus() {
    const container = document.getElementById('learning-status');

    if (!analyticsData.learning_enabled) {
        container.innerHTML = `
            <div class="learning-warning">
                <strong>⚠️ Lernsystem deaktiviert</strong>
                <p>Das selbstlernende System ist aktuell deaktiviert.</p>
            </div>
        `;
        return;
    }

    const patterns = analyticsData.patterns;

    if (!patterns.sufficient_data) {
        container.innerHTML = `
            <div class="learning-warning">
                <strong>📊 Sammle Daten...</strong>
                <p>${patterns.message}</p>
                <p style="margin-top: 10px;">Events: <strong>${patterns.events_count}</strong> / 3 benötigt</p>
            </div>
        `;
        return;
    }

    container.innerHTML = `
        <div class="learning-info">
            <strong>✅ Lernsystem aktiv</strong>
            <p>Basierend auf <strong>${patterns.events_count} Events</strong> der letzten ${patterns.period_days} Tage</p>
            <p style="margin-top: 10px; color: #059669;">
                Das System lernt kontinuierlich und optimiert Schwellwerte automatisch.
            </p>
        </div>
    `;
}

function renderStatistics() {
    const stats = analyticsData.statistics.event_stats;

    document.getElementById('stat-events').textContent = stats.event_count || 0;

    if (stats.avg_duration) {
        document.getElementById('stat-avg-duration').textContent =
            `${stats.avg_duration.toFixed(1)} Min`;
    }

    if (stats.avg_peak_humidity) {
        document.getElementById('stat-avg-humidity').textContent =
            `${stats.avg_peak_humidity.toFixed(1)}%`;
    }

    if (stats.avg_dehumidifier_runtime) {
        document.getElementById('stat-dehumidifier').textContent =
            `${stats.avg_dehumidifier_runtime.toFixed(1)} Min`;
    }
}

function renderPrediction() {
    const prediction = analyticsData.prediction;

    if (!prediction || !prediction.most_likely) {
        document.getElementById('prediction-card').style.display = 'none';
        return;
    }

    const most_likely = prediction.most_likely;
    const predTime = new Date(most_likely.time);

    const content = document.getElementById('prediction-content');
    content.innerHTML = `
        <div class="prediction-box">
            <div style="color: #6b7280; font-size: 0.9em;">Nächste wahrscheinliche Duschzeit:</div>
            <div class="prediction-time">${predTime.toLocaleString('de-DE', {
                weekday: 'short',
                day: '2-digit',
                month: '2-digit',
                hour: '2-digit',
                minute: '2-digit'
            })}</div>
            <div class="prediction-probability">
                Wahrscheinlichkeit: ${(most_likely.probability * 100).toFixed(0)}%
                (in ca. ${most_likely.hours_until.toFixed(1)} Stunden)
            </div>
        </div>
    `;

    document.getElementById('prediction-card').style.display = 'block';
}

function renderTrendChart() {
    if (!eventsData || !eventsData.events || eventsData.events.length < 2) {
        document.getElementById('trend-chart').innerHTML =
            '<p style="color: #6b7280;">Nicht genug Daten für Trend-Chart (mindestens 2 Events benötigt)</p>';
        return;
    }

    // Nimm die letzten 10 Events
    const events = eventsData.events.slice(0, 10).reverse();

    const canvas = document.getElementById('trend-canvas');
    const ctx = canvas.getContext('2d');

    // Setze Canvas-Größe
    canvas.width = canvas.parentElement.clientWidth;
    canvas.height = 300;

    const padding = 40;
    const chartWidth = canvas.width - 2 * padding;
    const chartHeight = canvas.height - 2 * padding;

    // Extrahiere Daten
    const peakValues = events.map(e => e.peak_humidity || 0);
    const avgValues = events.map(e => e.avg_humidity || 0);
    const labels = events.map((e, i) => `Event ${events.length - i}`);

    // Finde Min/Max für Skalierung
    const allValues = [...peakValues, ...avgValues];
    const maxValue = Math.max(...allValues);
    const minValue = Math.min(...allValues.filter(v => v > 0));
    const range = maxValue - minValue;
    const yMin = Math.max(0, minValue - range * 0.1);
    const yMax = maxValue + range * 0.1;

    // Zeichne Achsen
    ctx.strokeStyle = '#e5e7eb';
    ctx.lineWidth = 1;

    // Y-Achse
    ctx.beginPath();
    ctx.moveTo(padding, padding);
    ctx.lineTo(padding, canvas.height - padding);
    ctx.stroke();

    // X-Achse
    ctx.beginPath();
    ctx.moveTo(padding, canvas.height - padding);
    ctx.lineTo(canvas.width - padding, canvas.height - padding);
    ctx.stroke();

    // Zeichne Gitterlinien
    ctx.strokeStyle = '#f3f4f6';
    for (let i = 0; i <= 5; i++) {
        const y = padding + (chartHeight / 5) * i;
        ctx.beginPath();
        ctx.moveTo(padding, y);
        ctx.lineTo(canvas.width - padding, y);
        ctx.stroke();

        // Y-Achsen-Labels
        const value = yMax - (yMax - yMin) / 5 * i;
        ctx.fillStyle = '#6b7280';
        ctx.font = '12px Arial';
        ctx.textAlign = 'right';
        ctx.fillText(value.toFixed(0) + '%', padding - 10, y + 4);
    }

    // Hilfsfunktion für Y-Koordinate
    const getY = (value) => {
        return canvas.height - padding - ((value - yMin) / (yMax - yMin)) * chartHeight;
    };

    // Hilfsfunktion für X-Koordinate
    const getX = (index) => {
        return padding + (chartWidth / (events.length - 1)) * index;
    };

    // Zeichne Peak-Linie (Blau)
    ctx.strokeStyle = '#3b82f6';
    ctx.lineWidth = 2;
    ctx.beginPath();
    peakValues.forEach((value, i) => {
        const x = getX(i);
        const y = getY(value);
        if (i === 0) {
            ctx.moveTo(x, y);
        } else {
            ctx.lineTo(x, y);
        }
    });
    ctx.stroke();

    // Zeichne Average-Linie (Grün)
    ctx.strokeStyle = '#10b981';
    ctx.lineWidth = 2;
    ctx.setLineDash([5, 5]);
    ctx.beginPath();
    avgValues.forEach((value, i) => {
        const x = getX(i);
        const y = getY(value);
        if (i === 0) {
            ctx.moveTo(x, y);
        } else {
            ctx.lineTo(x, y);
        }
    });
    ctx.stroke();
    ctx.setLineDash([]);

    // Zeichne Datenpunkte
    peakValues.forEach((value, i) => {
        const x = getX(i);
        const y = getY(value);

        // Peak Punkt (Blau)
        ctx.fillStyle = '#3b82f6';
        ctx.beginPath();
        ctx.arc(x, y, 4, 0, 2 * Math.PI);
        ctx.fill();

        // Average Punkt (Grün)
        const avgY = getY(avgValues[i]);
        ctx.fillStyle = '#10b981';
        ctx.beginPath();
        ctx.arc(x, avgY, 4, 0, 2 * Math.PI);
        ctx.fill();
    });

    // Legende
    const legendX = padding + 20;
    const legendY = padding + 20;

    ctx.fillStyle = '#3b82f6';
    ctx.fillRect(legendX, legendY, 15, 3);
    ctx.fillStyle = '#1f2937';
    ctx.font = '12px Arial';
    ctx.textAlign = 'left';
    ctx.fillText('Peak Luftfeuchtigkeit', legendX + 20, legendY + 4);

    ctx.fillStyle = '#10b981';
    ctx.fillRect(legendX, legendY + 20, 15, 3);
    ctx.fillStyle = '#1f2937';
    ctx.fillText('Durchschnitt', legendX + 20, legendY + 24);
}

function renderPeakHours() {
    const peakHours = analyticsData.patterns.hourly_pattern.peak_hours;

    if (!peakHours || peakHours.length === 0) {
        document.getElementById('peak-hours-chart').innerHTML =
            '<p style="color: #6b7280;">Nicht genug Daten für Analyse</p>';
        return;
    }

    // Finde Maximum für Skalierung
    const maxCount = Math.max(...peakHours.map(h => h.count));

    const html = `
        <div class="bar-chart">
            ${peakHours.map(hour => `
                <div class="bar-item">
                    <div class="bar-label">${hour.hour}:00 Uhr</div>
                    <div class="bar-container">
                        <div class="bar-fill" style="width: ${(hour.count / maxCount * 100)}%">
                            ${hour.count} (${hour.percentage}%)
                        </div>
                    </div>
                </div>
            `).join('')}
        </div>
    `;

    document.getElementById('peak-hours-chart').innerHTML = html;
}

function renderWeekdayDistribution() {
    const weekdayDist = analyticsData.patterns.weekly_pattern.distribution;

    if (!weekdayDist || weekdayDist.length === 0) {
        document.getElementById('weekday-chart').innerHTML =
            '<p style="color: #6b7280;">Nicht genug Daten für Analyse</p>';
        return;
    }

    // Finde Maximum für Skalierung
    const maxCount = Math.max(...weekdayDist.map(d => d.count));

    const html = `
        <div class="bar-chart">
            ${weekdayDist.map(day => `
                <div class="bar-item">
                    <div class="bar-label">${day.name}</div>
                    <div class="bar-container">
                        <div class="bar-fill" style="width: ${maxCount > 0 ? (day.count / maxCount * 100) : 0}%">
                            ${day.count > 0 ? `${day.count} (${day.percentage}%)` : '0'}
                        </div>
                    </div>
                </div>
            `).join('')}
        </div>
    `;

    document.getElementById('weekday-chart').innerHTML = html;
}

function renderEventHistory() {
    if (!eventsData || !eventsData.events || eventsData.events.length === 0) {
        document.querySelector('#events-table tbody').innerHTML = `
            <tr>
                <td colspan="4" style="text-align: center; color: #6b7280;">
                    Keine Events gefunden
                </td>
            </tr>
        `;
        return;
    }

    const tbody = document.querySelector('#events-table tbody');
    tbody.innerHTML = eventsData.events.map(event => {
        const startTime = new Date(event.start_time);
        return `
            <tr>
                <td>${startTime.toLocaleString('de-DE')}</td>
                <td>${event.duration_minutes ? event.duration_minutes.toFixed(1) + ' Min' : '-'}</td>
                <td>${event.peak_humidity ? event.peak_humidity.toFixed(1) + '%' : '-'}</td>
                <td>${event.dehumidifier_runtime_minutes ? event.dehumidifier_runtime_minutes.toFixed(1) + ' Min' : '-'}</td>
            </tr>
        `;
    }).join('');
}

function showNoData() {
    document.getElementById('learning-status').innerHTML = `
        <div class="learning-warning">
            <strong>⚠️ Keine Daten verfügbar</strong>
            <p>Das Analytics-System konnte nicht geladen werden.</p>
        </div>
    `;
}

// Optimierungs-Funktion
async function optimizeNow() {
    const btn = document.getElementById('optimize-now');
    const resultSpan = document.getElementById('optimize-result');

    btn.disabled = true;
    btn.textContent = 'Optimiere...';
    resultSpan.textContent = '';

    try {
        const result = await postJSON('/api/bathroom/optimize', {
            days_back: 30,
            min_confidence: 0.7
        });

        if (result.success) {
            resultSpan.textContent = `✅ Erfolgreich optimiert! High: ${result.old_values.humidity_high}% → ${result.new_values.humidity_high}%, Low: ${result.old_values.humidity_low}% → ${result.new_values.humidity_low}%`;
            resultSpan.style.color = '#10b981';

            // Reload nach 2 Sekunden
            setTimeout(() => {
                location.reload();
            }, 2000);
        } else {
            resultSpan.textContent = `⚠️ ${result.reason || 'Optimierung fehlgeschlagen'}`;
            resultSpan.style.color = '#f59e0b';
        }
    } catch (error) {
        console.error('Error optimizing:', error);
        resultSpan.textContent = '❌ Fehler bei der Optimierung';
        resultSpan.style.color = '#ef4444';
    } finally {
        btn.disabled = false;
        btn.textContent = 'Jetzt optimieren';
    }
}

// Init
document.addEventListener('DOMContentLoaded', () => {
    loadAllData();

    // Event Listener für Optimierungs-Button
    document.getElementById('optimize-now').addEventListener('click', optimizeNow);

    // Auto-Refresh alle 30 Sekunden
    setInterval(loadAllData, 30000);
});
