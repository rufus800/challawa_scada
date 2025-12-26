/* ============================== */
/* PUMP DETAIL PAGE JAVASCRIPT */
/* ============================== */

// Socket.IO connection for real-time updates
const socket = io();

// Extract pump ID from URL
const PUMP_ID = parseInt(window.location.pathname.split('/').pop());

// Global state
let updateInterval = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initializeSocket();
    initSpeedometer();
    fetchPumpData();
    updateTimestamp();
    setupEventListeners();
    
    // Start periodic updates
    setInterval(fetchPumpData, 2000);
    setInterval(updateTimestamp, 1000);
});

// Setup event listeners
function setupEventListeners() {
    const pumpSelect = document.getElementById('pump-select');
    if (pumpSelect) {
        // Set current pump as selected
        pumpSelect.value = PUMP_ID.toString();
        
        pumpSelect.addEventListener('change', (e) => {
            const selectedValue = e.target.value;
            if (selectedValue && selectedValue !== PUMP_ID.toString()) {
                // Visual feedback
                const dashboard = document.querySelector('.dashboard');
                if (dashboard) {
                    dashboard.style.opacity = '0.6';
                    dashboard.style.pointerEvents = 'none';
                }
                
                window.location.href = '/pump/' + selectedValue;
            }
        });
        
        pumpSelect.addEventListener('input', (e) => {
            const selectedValue = e.target.value;
            if (selectedValue && selectedValue !== PUMP_ID.toString()) {
                // Visual feedback
                const dashboard = document.querySelector('.dashboard');
                if (dashboard) {
                    dashboard.style.opacity = '0.6';
                    dashboard.style.pointerEvents = 'none';
                }
                
                window.location.href = '/pump/' + selectedValue;
            }
        });
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

// Socket.IO connection handlers
function initializeSocket() {
    socket.on('connect', () => {
        updatePLCStatus(true);
    });

    socket.on('disconnect', () => {
        updatePLCStatus(false);
    });

    socket.on('data_update', () => {
        fetchPumpData();
    });
}

// Update PLC status indicator
function updatePLCStatus(connected) {
    const statusDot = document.getElementById('plc-status');
    const statusText = document.getElementById('plc-status-text');
    
    if (statusDot && statusText) {
        if (connected) {
            statusDot.style.backgroundColor = '#10b981';
            statusText.textContent = 'Connected';
        } else {
            statusDot.style.backgroundColor = '#ef4444';
            statusText.textContent = 'Disconnected';
        }
    }
}

// Initialize speedometer scale (car-style gauge)
function initSpeedometer() {
    const scaleContainer = document.getElementById('speedometer-scale');
    if (!scaleContainer) return;
    
    const maxSpeed = 50;
    const tickCount = 11;
    
    for (let i = 0; i < tickCount; i++) {
        const angle = (i / (tickCount - 1)) * 180 - 90;
        const value = (i / (tickCount - 1)) * maxSpeed;
        
        // Create tick
        const tick = document.createElement('div');
        tick.className = 'scale-tick';
        tick.style.transform = `rotate(${angle}deg)`;
        scaleContainer.appendChild(tick);
        
        // Create number label
        if (i % 2 === 0) {
            const label = document.createElement('div');
            label.className = 'scale-number';
            label.textContent = Math.round(value);
            
            const radius = 90;
            const radian = (angle + 90) * Math.PI / 180;
            const x = 90 + radius * Math.cos(radian);
            const y = 90 + radius * Math.sin(radian);
            
            label.style.left = x + 'px';
            label.style.top = y + 'px';
            scaleContainer.appendChild(label);
        }
    }
}

// Update gauges with pressure and speed values
function updateGauges(pressure, speed) {
    // Pressure gauge (0-180 degrees)
    const pressureAngle = (pressure / 10) * 180 - 90;
    const pressureNeedle = document.getElementById('pressure-needle');
    if (pressureNeedle) {
        pressureNeedle.setAttribute('transform', `rotate(${pressureAngle} 100 100)`);
    }
    
    const pressureValue = document.getElementById('pressure-value');
    if (pressureValue) {
        pressureValue.textContent = pressure.toFixed(1);
    }
    
    // Speed gauge (0-180 degrees)
    const speedAngle = (speed / 50) * 180 - 90;
    const speedNeedle = document.getElementById('speed-needle');
    if (speedNeedle) {
        speedNeedle.style.transform = `translateX(-50%) rotate(${speedAngle + 90}deg)`;
    }
    
    const speedValue = document.getElementById('speed-value');
    if (speedValue) {
        speedValue.textContent = speed.toFixed(1);
    }
}

// Update status indicators
function updateStatus(ready, running, trip) {
    const readyEl = document.getElementById('status-ready');
    const runningEl = document.getElementById('status-running');
    const tripEl = document.getElementById('status-trip');
    
    if (readyEl) {
        readyEl.className = 'status-value ' + (ready ? 'active' : 'inactive');
    }
    
    if (runningEl) {
        runningEl.className = 'status-value ' + (running ? 'active' : 'inactive');
    }
    
    if (tripEl) {
        tripEl.className = 'status-value ' + (trip ? 'trip' : 'inactive');
    }
}

// Update timestamp display
function updateTimestamp() {
    const now = new Date();
    const time = now.toLocaleTimeString();
    const timestampEl = document.getElementById('timestamp');
    if (timestampEl) {
        timestampEl.textContent = time;
    }
}

// Fetch pump data from API
async function fetchPumpData() {
    try {
        const response = await fetch(`/api/pump/${PUMP_ID}`);
        if (!response.ok) throw new Error('Failed to fetch pump data');
        
        const data = await response.json();
        
        // Update UI with data
        updateGauges(data.pressure || 0, data.speed || 0);
        updateStatus(data.ready || false, data.running || false, data.trip || false);
    } catch (error) {
        console.error('Error fetching pump data:', error);
    }
}

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (updateInterval) {
        clearInterval(updateInterval);
    }
    socket.disconnect();
});