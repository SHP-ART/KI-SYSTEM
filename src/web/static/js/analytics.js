// Analytics JavaScript mit Chart.js

let temperatureChart = null;
let humidityChart = null;

// Update Collector Status
async function updateCollectorStatus() {
    try {
        const data = await fetchJSON('/api/collector/status');

        const statusEl = document.getElementById('collector-status');
        if (data.running) {
            statusEl.textContent = '✅ Aktiv';
            statusEl.style.color = 'var(--secondary-color)';
        } else {
            statusEl.textContent = '⏸️ Gestoppt';
            statusEl.style.color = 'var(--warning-color)';
        }

        document.getElementById('total-readings').textContent =
            (data.total_sensor_readings || 0).toLocaleString('de-DE');

        if (data.last_collection) {
            const lastDate = new Date(data.last_collection);
            document.getElementById('last-collection').textContent =
                lastDate.toLocaleString('de-DE');
        } else {
            document.getElementById('last-collection').textContent = 'Noch keine';
        }

        if (data.interval) {
            const minutes = Math.floor(data.interval / 60);
            document.getElementById('collection-interval').textContent =
                `${minutes} Minuten`;
        }

    } catch (error) {
        console.error('Error updating collector status:', error);
    }
}

// Lade und aktualisiere Temperatur-Daten
async function updateTemperatureChart(hoursBack = 168) {
    try {
        const response = await fetchJSON(`/api/analytics/temperature?hours=${hoursBack}`);

        if (!response.data || response.data.length === 0) {
            showNoDataMessage();
            return;
        }

        hideNoDataMessage();

        const data = response.data;

        // Berechne Statistiken
        const values = data.map(d => d.avg_value);
        const avg = values.reduce((a, b) => a + b, 0) / values.length;
        const min = Math.min(...values);
        const max = Math.max(...values);

        document.getElementById('temp-avg').textContent = `${avg.toFixed(1)}°C`;
        document.getElementById('temp-min').textContent = `${min.toFixed(1)}°C`;
        document.getElementById('temp-max').textContent = `${max.toFixed(1)}°C`;

        // Erstelle Chart-Daten
        const labels = data.map(d => {
            const date = new Date(d.interval_time);
            return date.toLocaleDateString('de-DE', {
                month: 'short',
                day: 'numeric',
                hour: '2-digit'
            });
        });

        const chartData = {
            labels: labels,
            datasets: [
                {
                    label: 'Durchschnitt',
                    data: data.map(d => d.avg_value),
                    borderColor: 'rgba(75, 192, 192, 1)',
                    backgroundColor: 'rgba(75, 192, 192, 0.1)',
                    fill: true,
                    tension: 0.4
                },
                {
                    label: 'Min/Max Bereich',
                    data: data.map(d => [d.min_value, d.max_value]),
                    borderColor: 'rgba(255, 159, 64, 0.3)',
                    backgroundColor: 'rgba(255, 159, 64, 0.05)',
                    fill: true,
                    pointRadius: 0,
                    borderWidth: 1
                }
            ]
        };

        // Zerstöre alten Chart
        if (temperatureChart) {
            temperatureChart.destroy();
        }

        // Erstelle neuen Chart
        const ctx = document.getElementById('temperature-chart').getContext('2d');
        temperatureChart = new Chart(ctx, {
            type: 'line',
            data: chartData,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'bottom'
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        callbacks: {
                            label: function(context) {
                                let label = context.dataset.label || '';
                                if (label) {
                                    label += ': ';
                                }
                                if (Array.isArray(context.parsed.y)) {
                                    label += `${context.parsed.y[0].toFixed(1)}°C - ${context.parsed.y[1].toFixed(1)}°C`;
                                } else {
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
                        title: {
                            display: true,
                            text: 'Temperatur (°C)'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Zeit'
                        }
                    }
                }
            }
        });

    } catch (error) {
        console.error('Error updating temperature chart:', error);
        showNoDataMessage();
    }
}

// Lade und aktualisiere Luftfeuchtigkeit-Daten
async function updateHumidityChart(hoursBack = 168) {
    try {
        const response = await fetchJSON(`/api/analytics/humidity?hours=${hoursBack}`);

        if (!response.data || response.data.length === 0) {
            showNoDataMessage();
            return;
        }

        const data = response.data;

        // Berechne Statistiken
        const values = data.map(d => d.avg_value);
        const avg = values.reduce((a, b) => a + b, 0) / values.length;
        const min = Math.min(...values);
        const max = Math.max(...values);

        document.getElementById('humid-avg').textContent = `${avg.toFixed(1)}%`;
        document.getElementById('humid-min').textContent = `${min.toFixed(1)}%`;
        document.getElementById('humid-max').textContent = `${max.toFixed(1)}%`;

        // Erstelle Chart-Daten
        const labels = data.map(d => {
            const date = new Date(d.interval_time);
            return date.toLocaleDateString('de-DE', {
                month: 'short',
                day: 'numeric',
                hour: '2-digit'
            });
        });

        const chartData = {
            labels: labels,
            datasets: [{
                label: 'Luftfeuchtigkeit',
                data: data.map(d => d.avg_value),
                borderColor: 'rgba(54, 162, 235, 1)',
                backgroundColor: 'rgba(54, 162, 235, 0.1)',
                fill: true,
                tension: 0.4
            }]
        };

        // Zerstöre alten Chart
        if (humidityChart) {
            humidityChart.destroy();
        }

        // Erstelle neuen Chart
        const ctx = document.getElementById('humidity-chart').getContext('2d');
        humidityChart = new Chart(ctx, {
            type: 'line',
            data: chartData,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'bottom'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `Luftfeuchtigkeit: ${context.parsed.y.toFixed(1)}%`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        min: 0,
                        max: 100,
                        title: {
                            display: true,
                            text: 'Luftfeuchtigkeit (%)'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Zeit'
                        }
                    }
                }
            }
        });

    } catch (error) {
        console.error('Error updating humidity chart:', error);
    }
}

// Zeige "Keine Daten" Nachricht
function showNoDataMessage() {
    document.getElementById('no-data-message').classList.remove('hidden');
    document.querySelectorAll('.chart-card').forEach(card => {
        card.style.opacity = '0.5';
    });
}

// Verstecke "Keine Daten" Nachricht
function hideNoDataMessage() {
    document.getElementById('no-data-message').classList.add('hidden');
    document.querySelectorAll('.chart-card').forEach(card => {
        card.style.opacity = '1';
    });
}

// Aktualisiere alle Charts
function updateAllCharts() {
    const hoursBack = parseInt(document.getElementById('time-range').value);
    updateTemperatureChart(hoursBack);
    updateHumidityChart(hoursBack);
}

// Init
document.addEventListener('DOMContentLoaded', () => {
    // Initiales Laden
    updateCollectorStatus();
    updateAllCharts();

    // Event Listeners
    document.getElementById('refresh-charts').addEventListener('click', updateAllCharts);
    document.getElementById('time-range').addEventListener('change', updateAllCharts);

    // Auto-refresh alle 30 Sekunden
    setInterval(() => {
        updateCollectorStatus();
        updateAllCharts();
    }, 30000);
});
