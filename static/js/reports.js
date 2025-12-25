/* ============================== */
/* REPORTS PAGE JAVASCRIPT */
/* ============================== */

const socket = io();
let tripEvents = [];
let statusEvents = [];
let updateInterval = null;
let currentTimeRange = 24;

// ============================== 
// INITIALIZATION
// ============================== 
document.addEventListener('DOMContentLoaded', () => {
    initializeSocket();
    setupEventListeners();
    fetchAllEvents();
    startPeriodicUpdates();
});

// ============================== 
// SOCKET.IO SETUP
// ============================== 
function initializeSocket() {
    socket.on('connect', () => {
        console.log('Connected to server');
        updatePLCStatus(true);
    });

    socket.on('disconnect', () => {
        console.log('Disconnected from server');
        updatePLCStatus(false);
    });

    socket.on('data_update', (data) => {
        console.log('Data update received');
        fetchAllEvents();
    });

    socket.on('connection_response', (data) => {
        console.log('Server response:', data);
        updatePLCStatus(data.plc_connected);
    });
}

// ============================== 
// EVENT LISTENERS
// ============================== 
function setupEventListeners() {
    const pumpSelect = document.getElementById('pump-select');
    if (pumpSelect) {
        pumpSelect.addEventListener('change', (e) => {
            if (e.target.value) {
                window.location.href = `/pump/${e.target.value}`;
            }
        });
    }

    const timeRangeFilter = document.getElementById('time-range-filter');
    if (timeRangeFilter) {
        timeRangeFilter.addEventListener('change', (e) => {
            currentTimeRange = parseInt(e.target.value);
            fetchAllEvents();
        });
    }

    const exportPdfBtn = document.getElementById('btn-export-pdf');
    if (exportPdfBtn) {
        exportPdfBtn.addEventListener('click', () => {
            exportToPDF();
        });
    }

    const refreshBtn = document.getElementById('btn-refresh');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => {
            fetchAllEvents();
        });
    }
}

// ============================== 
// DATA FETCHING
// ============================== 
function fetchAllEvents() {
    const hours = currentTimeRange;
    
    // Fetch trip events
    fetch(`/api/trip-events?hours=${hours}`)
        .then(response => response.json())
        .then(data => {
            tripEvents = data.events || [];
            renderTripEventsTable();
            updateStats();
        })
        .catch(error => console.error('Error fetching trip events:', error));

    // Fetch status events
    fetch(`/api/status-events?hours=${hours}`)
        .then(response => response.json())
        .then(data => {
            statusEvents = data.events || [];
            renderStatusEventsTable();
            updateStats();
        })
        .catch(error => console.error('Error fetching status events:', error));

    fetchStatusData();
}

function fetchStatusData() {
    fetch('/api/status')
        .then(response => response.json())
        .then(data => {
            updatePLCStatus(data.plc_connected);
            updateTimestamp(data.timestamp);
        })
        .catch(error => console.error('Error fetching status:', error));
}

// ============================== 
// TABLE RENDERING
// ============================== 
function renderTripEventsTable() {
    const tbody = document.getElementById('trip-events-tbody');
    const info = document.getElementById('trip-events-info');
    
    if (!tbody) return;

    if (tripEvents.length === 0) {
        tbody.innerHTML = '<tr class="empty-row"><td colspan="5" class="empty-text">✓ No trip events recorded in this period</td></tr>';
        if (info) info.innerHTML = '';
        return;
    }

    tbody.innerHTML = '';
    tripEvents.forEach(event => {
        const row = document.createElement('tr');
        const timestamp = new Date(event.timestamp).toLocaleString();
        const tripStatus = event.trip_state ? '<span class="badge badge-danger">TRIP ON</span>' : '<span class="badge badge-warning">TRIP OFF</span>';
        
        row.innerHTML = `
            <td class="timestamp-cell">${timestamp}</td>
            <td class="pump-id-cell">PUMP ${event.pump_id}</td>
            <td class="status-cell">${tripStatus}</td>
            <td class="metric-cell">${event.pressure?.toFixed(2) || '-'}</td>
            <td class="metric-cell">${event.speed?.toFixed(2) || '-'}</td>
        `;
        tbody.appendChild(row);
    });

    if (info) {
        info.innerHTML = `<span class="record-count">Total Events: <strong>${tripEvents.length}</strong></span>`;
    }
}

function renderStatusEventsTable() {
    const tbody = document.getElementById('status-events-tbody');
    const info = document.getElementById('status-events-info');
    
    if (!tbody) return;

    if (statusEvents.length === 0) {
        tbody.innerHTML = '<tr class="empty-row"><td colspan="6" class="empty-text">✓ No status events recorded in this period</td></tr>';
        if (info) info.innerHTML = '';
        return;
    }

    tbody.innerHTML = '';
    statusEvents.forEach(event => {
        const row = document.createElement('tr');
        const timestamp = new Date(event.timestamp).toLocaleString();
        const statusBadge = getStatusBadge(event.status);
        
        row.innerHTML = `
            <td class="timestamp-cell">${timestamp}</td>
            <td class="pump-id-cell">PUMP ${event.pump_id}</td>
            <td class="status-cell">${statusBadge}</td>
            <td class="description-cell">${event.description || '-'}</td>
            <td class="metric-cell">${event.pressure?.toFixed(2) || '-'}</td>
            <td class="metric-cell">${event.speed?.toFixed(2) || '-'}</td>
        `;
        tbody.appendChild(row);
    });

    if (info) {
        info.innerHTML = `<span class="record-count">Total Events: <strong>${statusEvents.length}</strong></span>`;
    }
}

function getStatusBadge(status) {
    const statusLower = (status || '').toLowerCase();
    if (statusLower.includes('critical') || statusLower.includes('trip')) {
        return `<span class="badge badge-danger">${status}</span>`;
    } else if (statusLower.includes('running') || statusLower.includes('active')) {
        return `<span class="badge badge-success">${status}</span>`;
    } else if (statusLower.includes('warning')) {
        return `<span class="badge badge-warning">${status}</span>`;
    } else if (statusLower.includes('idle') || statusLower.includes('ready')) {
        return `<span class="badge badge-info">${status}</span>`;
    }
    return `<span class="badge badge-secondary">${status}</span>`;
}

// ============================== 
// STATISTICS UPDATES
// ============================== 
function updateStats() {
    const tripCount = tripEvents.length;
    const statusCount = statusEvents.length;
    const totalCount = tripCount + statusCount;

    const statTripCount = document.getElementById('stat-trip-count');
    const statStatusCount = document.getElementById('stat-status-count');
    const statTotalEvents = document.getElementById('stat-total-events');

    if (statTripCount) statTripCount.textContent = tripCount;
    if (statStatusCount) statStatusCount.textContent = statusCount;
    if (statTotalEvents) statTotalEvents.textContent = totalCount;
}

// ============================== 
// PDF EXPORT
// ============================== 
function exportToPDF() {
    const hours = currentTimeRange;
    window.open(`/api/export/pdf?hours=${hours}`, '_blank');
}

// ============================== 
// UI UPDATES
// ============================== 
function updateTimestamp(timestamp) {
    const timestampEl = document.getElementById('timestamp');
    if (timestampEl && timestamp) {
        const date = new Date(timestamp);
        const formatted = date.toLocaleString('en-US', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: false
        });
        timestampEl.textContent = formatted;
    }
}

function updatePLCStatus(connected) {
    const statusDot = document.getElementById('plc-status');
    const statusText = document.getElementById('plc-status-text');

    if (statusDot && statusText) {
        if (connected) {
            statusDot.textContent = '●';
            statusDot.style.color = '#10b981';
            statusDot.classList.add('active');
            statusText.textContent = 'Connected';
        } else {
            statusDot.textContent = '●';
            statusDot.style.color = '#ef4444';
            statusDot.classList.remove('active');
            statusText.textContent = 'Disconnected';
        }
    }
}

// ============================== 
// PERIODIC UPDATES
// ============================== 
function startPeriodicUpdates() {
    updateInterval = setInterval(() => {
        fetchAllEvents();
    }, 5000); // Update every 5 seconds
}

function stopPeriodicUpdates() {
    if (updateInterval) {
        clearInterval(updateInterval);
        updateInterval = null;
    }
}

// ============================== 
// CLEANUP
// ============================== 
window.addEventListener('beforeunload', () => {
    stopPeriodicUpdates();
    socket.disconnect();
});
            if (e.target.value === 'reports') {
                // Stay on reports page
            } else if (e.target.value) {
                window.location.href = `/pump/${e.target.value}`;
            }
        });
    }

    const statusFilter = document.getElementById('status-filter');
    if (statusFilter) {
        statusFilter.addEventListener('change', () => {
            renderReportsTable();
        });
    }

    const refreshBtn = document.getElementById('btn-refresh');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', () => {
            refreshBtn.style.animation = 'spin 0.6s ease-in-out';
            fetchAndRenderReports();
            setTimeout(() => {
                refreshBtn.style.animation = '';
            }, 600);
        });
    }

    const exportBtn = document.getElementById('btn-export-csv');
    if (exportBtn) {
        exportBtn.addEventListener('click', exportToPDF);
    }
}

// ============================== 
// DATA FETCHING
// ============================== 
function fetchAndRenderReports() {
    fetch('/api/reports')
        .then(response => response.json())
        .then(data => {
            allReportsData = data.pumps;
            updateTimestamp(data.timestamp);
            renderReportsTable();
            renderSummaryStats();
            renderDetailedCards();
        })
        .catch(error => console.error('Error fetching reports:', error));

    fetchStatusData();
}

function fetchStatusData() {
    fetch('/api/status')
        .then(response => response.json())
        .then(data => {
            updatePLCStatus(data.plc_connected);
            updateTimestamp(data.timestamp);
        })
        .catch(error => console.error('Error fetching status:', error));
}

// ============================== 
// RENDERING
// ============================== 
function renderReportsTable() {
    const tbody = document.getElementById('table-body');
    if (!tbody) return;

    const statusFilter = document.getElementById('status-filter').value;
    
    let filteredData = allReportsData;
    
    if (statusFilter) {
        filteredData = allReportsData.filter(pump => {
            const status = pump.status;
            if (statusFilter === 'ready') return status.ready && !status.running && !status.trip;
            if (statusFilter === 'running') return status.running && !status.trip;
            if (statusFilter === 'trip') return status.trip;
            return true;
        });
    }

    tbody.innerHTML = '';

    if (filteredData.length === 0) {
        tbody.innerHTML = '<tr class="empty-row"><td colspan="7" class="empty-text">No pumps match the selected filter</td></tr>';
        return;
    }

    filteredData.forEach((pump, index) => {
        const row = document.createElement('tr');
        row.className = 'report-row';
        if (index % 2 === 0) row.classList.add('alt-row');

        const statusBadges = getStatusBadges(pump.status);
        const healthStatus = getHealthStatus(pump);

        row.innerHTML = `
            <td class="pump-cell"><strong>Pump ${pump.pump_id}</strong></td>
            <td class="status-cell">${statusBadges}</td>
            <td class="metric-cell">${pump.metrics.pressure.value.toFixed(2)}</td>
            <td class="setpoint-cell">${pump.metrics.pressure.setpoint.toFixed(2)}</td>
            <td class="metric-cell">${pump.metrics.speed.value.toFixed(2)}</td>
            <td class="health-cell">${healthStatus}</td>
            <td class="timestamp-cell"><span class="live-indicator"></span> Live</td>
        `;

        tbody.appendChild(row);
    });
}

function renderSummaryStats() {
    if (allReportsData.length === 0) return;

    let running = 0;
    let ready = 0;
    let faulted = 0;
    let totalPressure = 0;
    let totalSpeed = 0;

    allReportsData.forEach(pump => {
        if (pump.status.trip) {
            faulted++;
        } else if (pump.status.running) {
            running++;
        } else if (pump.status.ready) {
            ready++;
        }

        totalPressure += pump.metrics.pressure.value;
        totalSpeed += pump.metrics.speed.value;
    });

    document.getElementById('stat-running').textContent = running;
    document.getElementById('stat-ready').textContent = ready;
    document.getElementById('stat-faulted').textContent = faulted;
    document.getElementById('stat-avg-pressure').textContent = (totalPressure / allReportsData.length).toFixed(2);
    document.getElementById('stat-avg-speed').textContent = (totalSpeed / allReportsData.length).toFixed(2);
}

function renderDetailedCards() {
    const container = document.getElementById('detailed-cards');
    if (!container) return;

    container.innerHTML = '';

    allReportsData.forEach(pump => {
        const card = document.createElement('div');
        card.className = 'detailed-report-card';

        const statusBadges = getStatusBadges(pump.status);
        const healthStatus = getHealthStatus(pump);

        card.innerHTML = `
            <div class="card-header">
                <h3>Pump ${pump.pump_id}</h3>
                <span class="card-health ${getHealthClass(pump)}">${healthStatus}</span>
            </div>
            <div class="card-status">
                <strong>Status:</strong> ${statusBadges}
            </div>
            <div class="card-metrics">
                <div class="metric-item">
                    <span class="metric-name">Pressure:</span>
                    <span class="metric-value">${pump.metrics.pressure.value.toFixed(2)} ${pump.metrics.pressure.unit}</span>
                </div>
                <div class="metric-item">
                    <span class="metric-name">Setpoint:</span>
                    <span class="metric-value">${pump.metrics.pressure.setpoint.toFixed(2)} ${pump.metrics.pressure.unit}</span>
                </div>
                <div class="metric-item">
                    <span class="metric-name">Speed:</span>
                    <span class="metric-value">${pump.metrics.speed.value.toFixed(2)} ${pump.metrics.speed.unit}</span>
                </div>
            </div>
            <div class="card-footer">
                <a href="/pump/${pump.pump_id}" class="card-link">View Details →</a>
            </div>
        `;

        container.appendChild(card);
    });
}

// ============================== 
// HELPER FUNCTIONS
// ============================== 
function getStatusBadges(status) {
    let badges = '';
    
    if (status.trip) {
        badges += '<span class="badge badge-trip">TRIP</span>';
    } else {
        if (status.ready) {
            badges += '<span class="badge badge-ready">READY</span>';
        }
        if (status.running) {
            badges += '<span class="badge badge-running">RUNNING</span>';
        }
    }

    if (!status.ready && !status.running && !status.trip) {
        badges = '<span class="badge badge-off">OFF</span>';
    }

    return badges;
}

function getHealthStatus(pump) {
    if (pump.status.trip) {
        return '🔴 Critical';
    }
    if (pump.status.running) {
        const pressure = pump.metrics.pressure.value;
        if (pressure > 8) {
            return '🟡 High Load';
        }
        return '🟢 Healthy';
    }
    if (pump.status.ready) {
        return '🟢 Standby';
    }
    return '⚪ Idle';
}

function getHealthClass(pump) {
    if (pump.status.trip) return 'critical';
    if (pump.metrics.pressure.value > 8) return 'warning';
    return 'healthy';
}

function updateTimestamp(timestamp) {
    const timestampEl = document.getElementById('timestamp');
    if (timestampEl && timestamp) {
        const date = new Date(timestamp);
        const formatted = date.toLocaleString('en-US', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: false
        });
        timestampEl.textContent = formatted;
    }
}

function updatePLCStatus(connected) {
    const statusDot = document.getElementById('plc-status');
    const statusText = document.getElementById('plc-status-text');

    if (statusDot && statusText) {
        if (connected) {
            statusDot.textContent = '●';
            statusDot.style.color = '#10b981';
            statusDot.classList.add('active');
            statusText.textContent = 'Connected';
        } else {
            statusDot.textContent = '●';
            statusDot.style.color = '#ef4444';
            statusDot.classList.remove('active');
            statusText.textContent = 'Disconnected';
        }
    }
}

// ============================== 
// EXPORT FUNCTIONALITY
// ============================== 
function exportToPDF() {
    if (allReportsData.length === 0) {
        alert('No data to export');
        return;
    }

    // Create a new window with HTML content
    const timestamp = new Date().toLocaleString();
    let htmlContent = `
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                h1 { text-align: center; color: #0f172a; }
                .header { text-align: center; margin-bottom: 20px; }
                .timestamp { text-align: right; margin-bottom: 20px; font-size: 12px; color: #666; }
                table { width: 100%; border-collapse: collapse; margin: 20px 0; }
                table th { background-color: #0f172a; color: white; padding: 10px; text-align: left; }
                table td { padding: 8px; border-bottom: 1px solid #ddd; }
                table tr:nth-child(even) { background-color: #f9fafb; }
                .page-break { page-break-after: always; }
                .summary { margin: 20px 0; }
                .summary-item { display: inline-block; margin-right: 30px; }
                .summary-label { font-weight: bold; }
                .badge { display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 12px; margin-right: 5px; }
                .badge-running { background-color: #10b981; color: white; }
                .badge-ready { background-color: #f59e0b; color: white; }
                .badge-trip { background-color: #ef4444; color: white; }
                .badge-off { background-color: #9ca3af; color: white; }
                .metric { margin: 10px 0; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Challawa SCADA System - Reports</h1>
                <div class="timestamp">Generated: ${timestamp}</div>
            </div>
            
            <div class="summary">
                <h2>System Summary</h2>
    `;

    // Add summary stats
    let running = 0, ready = 0, faulted = 0, totalPressure = 0, totalSpeed = 0;
    allReportsData.forEach(pump => {
        if (pump.status.trip) faulted++;
        else if (pump.status.running) running++;
        else if (pump.status.ready) ready++;
        totalPressure += pump.metrics.pressure.value;
        totalSpeed += pump.metrics.speed.value;
    });

    htmlContent += `
                <div class="summary-item">
                    <span class="summary-label">Running:</span> ${running}
                </div>
                <div class="summary-item">
                    <span class="summary-label">Ready:</span> ${ready}
                </div>
                <div class="summary-item">
                    <span class="summary-label">Faulted:</span> ${faulted}
                </div>
                <div class="summary-item">
                    <span class="summary-label">Avg Pressure:</span> ${(totalPressure / allReportsData.length).toFixed(2)} bar
                </div>
                <div class="summary-item">
                    <span class="summary-label">Avg Speed:</span> ${(totalSpeed / allReportsData.length).toFixed(2)} Hz
                </div>
            </div>

            <h2>Pump Status Report</h2>
            <table>
                <thead>
                    <tr>
                        <th>Pump ID</th>
                        <th>Status</th>
                        <th>Pressure (bar)</th>
                        <th>Setpoint (bar)</th>
                        <th>Speed (Hz)</th>
                        <th>Timestamp</th>
                    </tr>
                </thead>
                <tbody>
    `;

    // Add pump data
    allReportsData.forEach(pump => {
        const statusBadges = getStatusBadges(pump.status);
        const pumpTimestamp = new Date().toLocaleString();
        
        htmlContent += `
            <tr>
                <td>Pump ${pump.pump_id}</td>
                <td>${statusBadges}</td>
                <td>${pump.metrics.pressure.value.toFixed(2)}</td>
                <td>${pump.metrics.pressure.setpoint.toFixed(2)}</td>
                <td>${pump.metrics.speed.value.toFixed(2)}</td>
                <td>${pumpTimestamp}</td>
            </tr>
        `;
    });

    htmlContent += `
                </tbody>
            </table>
            
            <div class="page-break"></div>
            <h2>Detailed Pump Analysis</h2>
    `;

    // Add detailed analysis
    allReportsData.forEach(pump => {
        const statusBadges = getStatusBadges(pump.status);
        const healthStatus = getHealthStatus(pump);
        const pumpTimestamp = new Date().toLocaleString();
        
        htmlContent += `
            <div class="metric">
                <h3>Pump ${pump.pump_id}</h3>
                <p><strong>Status:</strong> ${statusBadges}</p>
                <p><strong>Health:</strong> ${healthStatus}</p>
                <p><strong>Pressure:</strong> ${pump.metrics.pressure.value.toFixed(2)} ${pump.metrics.pressure.unit}</p>
                <p><strong>Setpoint:</strong> ${pump.metrics.pressure.setpoint.toFixed(2)} ${pump.metrics.pressure.unit}</p>
                <p><strong>Speed:</strong> ${pump.metrics.speed.value.toFixed(2)} ${pump.metrics.speed.unit}</p>
                <p><strong>Last Updated:</strong> ${pumpTimestamp}</p>
                <hr>
            </div>
        `;
    });

    htmlContent += `
        </body>
        </html>
    `;

    // Create a new window and print to PDF
    const printWindow = window.open('', '', 'width=800,height=600');
    printWindow.document.write(htmlContent);
    printWindow.document.close();

    // Trigger print dialog (user can save as PDF)
    setTimeout(() => {
        printWindow.print();
    }, 500);
}

// ============================== 
// PERIODIC UPDATES
// ============================== 
function startPeriodicUpdates() {
    updateInterval = setInterval(() => {
        fetchAndRenderReports();
    }, 3000);
}

function stopPeriodicUpdates() {
    if (updateInterval) {
        clearInterval(updateInterval);
        updateInterval = null;
    }
}

// ============================== 
// CLEANUP
// ============================== 
window.addEventListener('beforeunload', () => {
    stopPeriodicUpdates();
    socket.disconnect();
});
