/* ============================== */
/* DASHBOARD PAGE JAVASCRIPT */
/* ============================== */

const socket = io();
let allData = {};
let updateInterval = null;

// ============================== 
// INITIALIZATION
// ============================== 
document.addEventListener('DOMContentLoaded', () => {
    initializeSocket();
    setupEventListeners();
    fetchAndUpdateData();
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
        console.log('Data update received:', data);
        handleDataUpdate(data);
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
        // Reset to empty
        pumpSelect.value = '';
        
        const handlePumpChange = function() {
            const selectedValue = this.value;
            if (selectedValue) {
                // Reset immediately
                this.value = '';
                
                // Visual feedback
                const dashboard = document.querySelector('.dashboard');
                if (dashboard) {
                    dashboard.style.opacity = '0.6';
                    dashboard.style.pointerEvents = 'none';
                }
                
                // Navigate
                window.location.href = '/pump/' + selectedValue;
            }
        };
        
        pumpSelect.addEventListener('change', handlePumpChange);
        pumpSelect.addEventListener('input', handlePumpChange);
    }

    const reportsLink = document.getElementById('reports-link');
    if (reportsLink) {
        reportsLink.addEventListener('click', (e) => {
            e.preventDefault();
            
            // Visual feedback
            const dashboard = document.querySelector('.dashboard');
            if (dashboard) {
                dashboard.style.opacity = '0.6';
                dashboard.style.pointerEvents = 'none';
            }
            
            window.location.href = '/reports';
        });
    }
}

// ============================== 
// DATA FETCHING
// ============================== 
function fetchAndUpdateData() {
    fetch('/api/data')
        .then(response => response.json())
        .then(data => {
            allData = data;
            renderDashboard();
        })
        .catch(error => console.error('Error fetching data:', error));

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
// DATA HANDLERS
// ============================== 
function handleDataUpdate(data) {
    console.log('Processing data update');
    updateTimestamp(data.timestamp);
    updateAlarmStatus(data.system_alarm);
    updatePressureSetpoints(data.pressure_setpoints);
}

function updateAlarmStatus(alarmActive) {
    const alarmCard = document.getElementById('alarm-card');
    const alarmMessage = document.getElementById('alarm-message');
    const indicator = alarmCard?.querySelector('.alarm-indicator');

    if (!alarmCard || !alarmMessage || !indicator) return;

    if (alarmActive) {
        alarmCard.classList.add('active');
        alarmMessage.textContent = 'SYSTEM ALARM ACTIVE - Immediate Action Required!';
        alarmMessage.style.color = '#ef4444';
        
        // Clear all previous styles and apply alarm animation
        indicator.style.removeProperty('background');
        indicator.style.removeProperty('box-shadow');
        indicator.style.animation = 'alarm-flash 0.4s ease-in-out infinite';
        indicator.style.background = '#ef4444';
    } else {
        alarmCard.classList.remove('active');
        alarmMessage.textContent = 'Normal Operation';
        alarmMessage.style.color = '';
        
        // Properly reset all styles when alarm is inactive
        indicator.style.animation = 'none';
        indicator.style.removeProperty('animation');
        indicator.style.background = '#10b981';
        indicator.style.boxShadow = '0 0 0 4px rgba(16, 185, 129, 0.2)';
    }
}

function updatePressureSetpoints(setpoints) {
    const container = document.getElementById('setpoints-container');
    if (!container) return;

    container.innerHTML = '';

    for (let pumpId = 1; pumpId <= 7; pumpId++) {
        const setpoint = setpoints[pumpId];
        if (!setpoint) continue;

        const card = document.createElement('div');
        card.className = 'setpoint-card';
        card.innerHTML = `
            <div class="setpoint-label">Pump ${pumpId} Pressure SP</div>
            <div class="setpoint-value">${setpoint.value.toFixed(2)}</div>
            <div class="setpoint-unit">${setpoint.unit}</div>
        `;

        container.appendChild(card);
    }
}

// ============================== 
// RENDERING
// ============================== 
function renderDashboard() {
    console.log('Rendering dashboard with data:', allData);
    
    if (allData.system_alarm !== undefined) {
        updateAlarmStatus(allData.system_alarm);
    }

    if (allData.pressure_setpoints) {
        updatePressureSetpoints(allData.pressure_setpoints);
    }
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
            
            // When PLC is disconnected, force alarm to inactive state (green)
            updateAlarmStatus(false);
        }
    }
}

// ============================== 
// PERIODIC UPDATES
// ============================== 
function startPeriodicUpdates() {
    // Update every 1 second for live data when PLC is connected
    updateInterval = setInterval(() => {
        fetchAndUpdateData();
    }, 1000);
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

// ============================== 
// UTILITY FUNCTIONS
// ============================== 
function formatValue(value, type) {
    if (type === 'bool') {
        return value ? 'ON' : 'OFF';
    }
    if (typeof value === 'number') {
        return value.toFixed(2);
    }
    return value;
}
