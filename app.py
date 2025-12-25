"""
Challawa Industrial SCADA System - Web Application
Professional Pump Monitoring & Control Dashboard (7 Pumps)

Features:
- Real-time PLC data acquisition via SNAP7
- Beautiful responsive web UI with real-time updates
- Home page with pressure setpoints & system alarm
- Detailed pump monitoring pages with live metrics
- Real-time WebSocket updates
- Professional ISA-101 compliant design

Author: Industrial Automation Team
Date: 2025
"""

# ===============================
# IMPORTS
# ===============================
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit, join_room, leave_room
import threading
import time
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, Optional, List
from enum import Enum
import json
import sqlite3
import os
from pathlib import Path

try:
    import snap7
    HAS_SNAP7 = True
except ImportError:
    HAS_SNAP7 = False
    print("WARNING: snap7 not installed. Install with: pip install python-snap7")

# ===============================
# CONFIGURATION
# ===============================
PLC_CONFIG = {
    "ip": "192.168.200.20",
    "rack": 0,
    "slot": 1,
    "db": 39
}

# Pump Parameters (Offsets and Data Types)
# Format: {pump_id: {parameter: {offset: int, type: str, min: float, max: float}}}
PUMP_PARAMETERS = {
    1: {
        "ready": {"offset": 1, "type": "bool", "label": "PUMP 1 READY", "color": "yellow"},
        "running": {"offset": 2, "type": "bool", "label": "PUMP 1 RUNNING", "color": "green"},
        "trip": {"offset": 3, "type": "bool", "label": "PUMP 1 TRIP", "color": "red"},
        "pressure": {"offset": 4, "type": "real", "label": "PUMP 1 PRESSURE", "min": 0.0, "max": 10.0, "unit": "bar"},
        "speed": {"offset": 8, "type": "real", "label": "PUMP 1 SPEED", "min": 0.0, "max": 50.0, "unit": "Hz"},
        "pressure_setpoint": {"offset": 12, "type": "real", "label": "PUMP 1 PRESSURE SETPOINT", "min": 0.0, "max": 10.0, "unit": "bar"},
    },
    2: {
        "ready": {"offset": 16, "type": "bool", "label": "PUMP 2 READY", "color": "yellow"},
        "running": {"offset": 17, "type": "bool", "label": "PUMP 2 RUNNING", "color": "green"},
        "trip": {"offset": 18, "type": "bool", "label": "PUMP 2 TRIP", "color": "red"},
        "pressure": {"offset": 20, "type": "real", "label": "PUMP 2 PRESSURE", "min": 0.0, "max": 10.0, "unit": "bar"},
        "speed": {"offset": 24, "type": "real", "label": "PUMP 2 SPEED", "min": 0.0, "max": 50.0, "unit": "Hz"},
        "pressure_setpoint": {"offset": 28, "type": "real", "label": "PUMP 2 PRESSURE SETPOINT", "min": 0.0, "max": 10.0, "unit": "bar"},
    },
    3: {
        "ready": {"offset": 32, "type": "bool", "label": "PUMP 3 READY", "color": "yellow"},
        "running": {"offset": 33, "type": "bool", "label": "PUMP 3 RUNNING", "color": "green"},
        "trip": {"offset": 34, "type": "bool", "label": "PUMP 3 TRIP", "color": "red"},
        "pressure": {"offset": 36, "type": "real", "label": "PUMP 3 PRESSURE", "min": 0.0, "max": 10.0, "unit": "bar"},
        "speed": {"offset": 40, "type": "real", "label": "PUMP 3 SPEED", "min": 0.0, "max": 50.0, "unit": "Hz"},
        "pressure_setpoint": {"offset": 44, "type": "real", "label": "PUMP 3 PRESSURE SETPOINT", "min": 0.0, "max": 10.0, "unit": "bar"},
    },
    4: {
        "ready": {"offset": 48, "type": "bool", "label": "PUMP 4 READY", "color": "yellow"},
        "running": {"offset": 49, "type": "bool", "label": "PUMP 4 RUNNING", "color": "green"},
        "trip": {"offset": 50, "type": "bool", "label": "PUMP 4 TRIP", "color": "red"},
        "pressure": {"offset": 52, "type": "real", "label": "PUMP 4 PRESSURE", "min": 0.0, "max": 10.0, "unit": "bar"},
        "speed": {"offset": 56, "type": "real", "label": "PUMP 4 SPEED", "min": 0.0, "max": 50.0, "unit": "Hz"},
        "pressure_setpoint": {"offset": 60, "type": "real", "label": "PUMP 4 PRESSURE SETPOINT", "min": 0.0, "max": 10.0, "unit": "bar"},
    },
    5: {
        "ready": {"offset": 64, "type": "bool", "label": "PUMP 5 READY", "color": "yellow"},
        "running": {"offset": 65, "type": "bool", "label": "PUMP 5 RUNNING", "color": "green"},
        "trip": {"offset": 66, "type": "bool", "label": "PUMP 5 TRIP", "color": "red"},
        "pressure": {"offset": 68, "type": "real", "label": "PUMP 5 PRESSURE", "min": 0.0, "max": 10.0, "unit": "bar"},
        "speed": {"offset": 72, "type": "real", "label": "PUMP 5 SPEED", "min": 0.0, "max": 50.0, "unit": "Hz"},
        "pressure_setpoint": {"offset": 76, "type": "real", "label": "PUMP 5 PRESSURE SETPOINT", "min": 0.0, "max": 10.0, "unit": "bar"},
    },
    6: {
        "ready": {"offset": 80, "type": "bool", "label": "PUMP 6 READY", "color": "yellow"},
        "running": {"offset": 81, "type": "bool", "label": "PUMP 6 RUNNING", "color": "green"},
        "trip": {"offset": 82, "type": "bool", "label": "PUMP 6 TRIP", "color": "red"},
        "pressure": {"offset": 84, "type": "real", "label": "PUMP 6 PRESSURE", "min": 0.0, "max": 10.0, "unit": "bar"},
        "speed": {"offset": 88, "type": "real", "label": "PUMP 6 SPEED", "min": 0.0, "max": 50.0, "unit": "Hz"},
        "pressure_setpoint": {"offset": 92, "type": "real", "label": "PUMP 6 PRESSURE SETPOINT", "min": 0.0, "max": 10.0, "unit": "bar"},
    },
    7: {
        "ready": {"offset": 96, "type": "bool", "label": "PUMP 7 READY", "color": "yellow"},
        "running": {"offset": 97, "type": "bool", "label": "PUMP 7 RUNNING", "color": "green"},
        "trip": {"offset": 98, "type": "bool", "label": "PUMP 7 TRIP", "color": "red"},
        "pressure": {"offset": 100, "type": "real", "label": "PUMP 7 PRESSURE", "min": 0.0, "max": 10.0, "unit": "bar"},
        "speed": {"offset": 104, "type": "real", "label": "PUMP 7 SPEED", "min": 0.0, "max": 50.0, "unit": "Hz"},
        "pressure_setpoint": {"offset": 108, "type": "real", "label": "PUMP 7 PRESSURE SETPOINT", "min": 0.0, "max": 10.0, "unit": "bar"},
    },
}

# ===============================
# SETUP LOGGING
# ===============================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ===============================
# DATABASE MANAGER
# ===============================
class DatabaseManager:
    """Manages SQLite database for pump data history"""
    
    def __init__(self, db_path: str = "pump_data.db"):
        self.db_path = db_path
        self.lock = threading.Lock()
        self.init_db()
    
    def init_db(self):
        """Initialize database and create tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create pump data table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS pump_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        pump_id INTEGER NOT NULL,
                        pressure REAL,
                        speed REAL,
                        pressure_setpoint REAL,
                        ready BOOLEAN,
                        running BOOLEAN,
                        trip BOOLEAN,
                        FOREIGN KEY (pump_id) REFERENCES pumps(id)
                    )
                ''')
                
                # Create trip events table - for tracking trip events
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS trip_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        pump_id INTEGER NOT NULL,
                        trip_state BOOLEAN,
                        pressure REAL,
                        speed REAL,
                        FOREIGN KEY (pump_id) REFERENCES pumps(id)
                    )
                ''')
                
                # Create status events table - for tracking status changes
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS status_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        pump_id INTEGER NOT NULL,
                        status TEXT,
                        description TEXT,
                        pressure REAL,
                        speed REAL,
                        FOREIGN KEY (pump_id) REFERENCES pumps(id)
                    )
                ''')
                
                # Create pumps reference table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS pumps (
                        id INTEGER PRIMARY KEY,
                        name TEXT UNIQUE
                    )
                ''')
                
                # Insert pump names
                for pump_id in range(1, 8):
                    cursor.execute(
                        'INSERT OR IGNORE INTO pumps (id, name) VALUES (?, ?)',
                        (pump_id, f'PUMP {pump_id}')
                    )
                
                # Create indexes for faster queries
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_pump_timestamp 
                    ON pump_data(pump_id, timestamp)
                ''')
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_trip_events 
                    ON trip_events(pump_id, timestamp)
                ''')
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_status_events 
                    ON status_events(pump_id, timestamp)
                ''')
                
                conn.commit()
                logger.info(f"Database initialized: {self.db_path}")
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
    
    def save_data(self, pump_id: int, values: dict):
        """Save pump data to database"""
        try:
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO pump_data 
                        (pump_id, pressure, speed, pressure_setpoint, ready, running, trip)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        pump_id,
                        values.get('pressure', 0),
                        values.get('speed', 0),
                        values.get('pressure_setpoint', 0),
                        values.get('ready', False),
                        values.get('running', False),
                        values.get('trip', False)
                    ))
                    conn.commit()
        except Exception as e:
            logger.error(f"Error saving pump data: {e}")
    
    def get_historical_data(self, pump_id: int = None, hours: int = 24) -> List[dict]:
        """Get historical pump data"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                since = datetime.now() - timedelta(hours=hours)
                
                if pump_id:
                    cursor.execute('''
                        SELECT * FROM pump_data 
                        WHERE pump_id = ? AND timestamp > ?
                        ORDER BY timestamp DESC
                        LIMIT 1000
                    ''', (pump_id, since.isoformat()))
                else:
                    cursor.execute('''
                        SELECT * FROM pump_data 
                        WHERE timestamp > ?
                        ORDER BY timestamp DESC
                        LIMIT 5000
                    ''', (since.isoformat(),))
                
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error retrieving historical data: {e}")
            return []
    
    def get_stats(self, pump_id: int = None, hours: int = 24) -> dict:
        """Get statistics for pump data"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                since = datetime.now() - timedelta(hours=hours)
                
                if pump_id:
                    cursor.execute('''
                        SELECT 
                            AVG(pressure) as avg_pressure,
                            MAX(pressure) as max_pressure,
                            MIN(pressure) as min_pressure,
                            AVG(speed) as avg_speed,
                            MAX(speed) as max_speed,
                            COUNT(*) as record_count,
                            SUM(CASE WHEN trip = 1 THEN 1 ELSE 0 END) as trip_count
                        FROM pump_data 
                        WHERE pump_id = ? AND timestamp > ?
                    ''', (pump_id, since.isoformat()))
                else:
                    cursor.execute('''
                        SELECT 
                            AVG(pressure) as avg_pressure,
                            MAX(pressure) as max_pressure,
                            MIN(pressure) as min_pressure,
                            AVG(speed) as avg_speed,
                            MAX(speed) as max_speed,
                            COUNT(*) as record_count,
                            SUM(CASE WHEN trip = 1 THEN 1 ELSE 0 END) as trip_count
                        FROM pump_data 
                        WHERE timestamp > ?
                    ''', (since.isoformat(),))
                
                row = cursor.fetchone()
                return {
                    'avg_pressure': round(row[0] or 0, 2),
                    'max_pressure': round(row[1] or 0, 2),
                    'min_pressure': round(row[2] or 0, 2),
                    'avg_speed': round(row[3] or 0, 2),
                    'max_speed': round(row[4] or 0, 2),
                    'record_count': int(row[5] or 0),
                    'trip_count': int(row[6] or 0)
                }
        except Exception as e:
            logger.error(f"Error calculating stats: {e}")
            return {}
    
    def get_trip_events(self, pump_id: int = None, hours: int = 24) -> List[dict]:
        """Get trip events"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                since = datetime.now() - timedelta(hours=hours)
                
                if pump_id:
                    cursor.execute('''
                        SELECT * FROM trip_events 
                        WHERE pump_id = ? AND timestamp > ?
                        ORDER BY timestamp DESC
                        LIMIT 500
                    ''', (pump_id, since.isoformat()))
                else:
                    cursor.execute('''
                        SELECT * FROM trip_events 
                        WHERE timestamp > ?
                        ORDER BY timestamp DESC
                        LIMIT 1000
                    ''', (since.isoformat(),))
                
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error retrieving trip events: {e}")
            return []
    
    def get_status_events(self, pump_id: int = None, hours: int = 24) -> List[dict]:
        """Get status change events"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                since = datetime.now() - timedelta(hours=hours)
                
                if pump_id:
                    cursor.execute('''
                        SELECT * FROM status_events 
                        WHERE pump_id = ? AND timestamp > ?
                        ORDER BY timestamp DESC
                        LIMIT 500
                    ''', (pump_id, since.isoformat()))
                else:
                    cursor.execute('''
                        SELECT * FROM status_events 
                        WHERE timestamp > ?
                        ORDER BY timestamp DESC
                        LIMIT 1000
                    ''', (since.isoformat(),))
                
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error retrieving status events: {e}")
            return []
    
    def record_trip_event(self, pump_id: int, trip_state: str, pressure: float, speed: float):
        """Record a trip event"""
        try:
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO trip_events (pump_id, trip_state, pressure, speed)
                        VALUES (?, ?, ?, ?)
                    ''', (pump_id, trip_state, pressure, speed))
                    conn.commit()
        except Exception as e:
            logger.error(f"Error recording trip event: {e}")
    
    def record_status_event(self, pump_id: int, status: str, description: str, pressure: float, speed: float):
        """Record a status change event"""
        try:
            with self.lock:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO status_events (pump_id, status, description, pressure, speed)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (pump_id, status, description, pressure, speed))
                    conn.commit()
        except Exception as e:
            logger.error(f"Error recording status event: {e}")

# ===============================
# PLC MANAGER
# ===============================
class PLCManager:
    """Manages PLC connection and data acquisition"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.client = None
        self.connected = False
        self.data = {}
        self._lock = threading.Lock()
        self._running = False
        self._thread = None
        # Track previous state for event detection
        self._previous_state = {}
        for pump_id in range(1, 8):
            self._previous_state[pump_id] = {
                'trip': False,
                'running': False,
                'ready': False
            }
        
    def connect(self) -> bool:
        """Connect to PLC"""
        if not HAS_SNAP7:
            logger.warning("snap7 not available - using simulated data")
            self.connected = True
            return True
            
        try:
            self.client = snap7.client.Client()
            self.client.connect(
                self.config["ip"],
                self.config["rack"],
                self.config["slot"]
            )
            self.connected = True
            logger.info(f"Connected to PLC at {self.config['ip']}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to PLC: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Disconnect from PLC"""
        try:
            if self.client:
                self.client.disconnect()
            self.connected = False
            logger.info("Disconnected from PLC")
        except Exception as e:
            logger.error(f"Error disconnecting: {e}")
    
    def read_data(self) -> Dict:
        """Read all pump data from PLC"""
        if not self.connected:
            return self._get_simulated_data()
        
        try:
            with self._lock:
                data = {}
                db_number = self.config["db"]
                
                # Read from PLC
                for pump_id, params in PUMP_PARAMETERS.items():
                    pump_data = {}
                    
                    for param_name, param_info in params.items():
                        try:
                            offset = param_info["offset"]
                            
                            if param_info["type"] == "bool":
                                # Read 1 byte for bool
                                val = self.client.db_read(db_number, offset, 1)
                                pump_data[param_name] = bool(val[0])
                            else:  # real (float)
                                # Read 4 bytes for real
                                val = self.client.db_read(db_number, offset, 4)
                                pump_data[param_name] = float(snap7.util.get_real(val, 0))
                        except Exception as e:
                            logger.debug(f"Error reading {param_name}: {e}")
                            pump_data[param_name] = 0.0 if param_info["type"] == "real" else False
                    
                    data[f"pump_{pump_id}"] = pump_data
                
                self.data = data
                return data
        except Exception as e:
            logger.error(f"Error reading PLC data: {e}")
            return self._get_simulated_data()
    
    def _get_simulated_data(self) -> Dict:
        """Return simulated data for testing"""
        import random
        import math
        
        data = {}
        for pump_id in range(1, 8):
            pump_data = {}
            
            # Simulate some pumps running and some not
            pump_data["ready"] = random.random() > 0.3
            pump_data["running"] = pump_data["ready"] and random.random() > 0.5
            pump_data["trip"] = random.random() > 0.95
            
            # Simulate pressure and speed with some variation
            if pump_data["running"]:
                pump_data["pressure"] = round(5 + random.uniform(-1, 2), 2)
                pump_data["speed"] = round(30 + random.uniform(-5, 10), 2)
            else:
                pump_data["pressure"] = round(random.uniform(0, 2), 2)
                pump_data["speed"] = round(random.uniform(0, 5), 2)
            
            pump_data["pressure_setpoint"] = round(5.5 + (pump_id - 1) * 0.3, 2)
            
            data[f"pump_{pump_id}"] = pump_data
        
        self.data = data
        return data
    
    def start_polling(self, interval: float = 1.0):
        """Start polling PLC in background thread"""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._poll_loop, args=(interval,), daemon=True)
        self._thread.start()
        logger.info("Started PLC polling")
    
    def stop_polling(self):
        """Stop polling"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Stopped PLC polling")
    
    def _poll_loop(self, interval: float):
        """Polling loop - reads data and saves to database"""
        global db_manager
        while self._running:
            self.read_data()
            
            # Save each pump's data to database and detect state changes
            for pump_id in range(1, 8):
                pump_key = f"pump_{pump_id}"
                if pump_key in self.data:
                    pump_data = self.data[pump_key]
                    db_manager.save_data(pump_id, pump_data)
                    
                    # Check for trip state changes
                    current_trip = pump_data.get('trip', False)
                    previous_trip = self._previous_state[pump_id]['trip']
                    
                    if current_trip != previous_trip:
                        # Trip state changed
                        trip_state = "TRIP ON" if current_trip else "TRIP OFF"
                        db_manager.record_trip_event(
                            pump_id=pump_id,
                            trip_state=trip_state,
                            pressure=pump_data.get('pressure', 0),
                            speed=pump_data.get('speed', 0)
                        )
                        self._previous_state[pump_id]['trip'] = current_trip
                    
                    # Check for running state changes
                    current_running = pump_data.get('running', False)
                    previous_running = self._previous_state[pump_id]['running']
                    
                    if current_running != previous_running:
                        # Running state changed
                        if current_running:
                            status = "Running"
                            description = "Pump started"
                        else:
                            status = "Stopped"
                            description = "Pump stopped"
                        
                        db_manager.record_status_event(
                            pump_id=pump_id,
                            status=status,
                            description=description,
                            pressure=pump_data.get('pressure', 0),
                            speed=pump_data.get('speed', 0)
                        )
                        self._previous_state[pump_id]['running'] = current_running
                    
                    # Check for ready state changes
                    current_ready = pump_data.get('ready', False)
                    previous_ready = self._previous_state[pump_id]['ready']
                    
                    if current_ready != previous_ready:
                        # Ready state changed
                        if current_ready:
                            status = "Ready"
                            description = "Pump ready for operation"
                        else:
                            status = "Not Ready"
                            description = "Pump not ready"
                        
                        db_manager.record_status_event(
                            pump_id=pump_id,
                            status=status,
                            description=description,
                            pressure=pump_data.get('pressure', 0),
                            speed=pump_data.get('speed', 0)
                        )
                        self._previous_state[pump_id]['ready'] = current_ready
            
            time.sleep(interval)
    
    def get_data(self) -> Dict:
        """Get latest data"""
        return self.data.copy()


# ===============================
# FLASK APP SETUP
# ===============================
app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['SECRET_KEY'] = 'challawa_scada_secret_key_2025'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Initialize Database Manager and PLC Manager
db_manager = DatabaseManager('pump_data.db')
plc_manager = PLCManager(PLC_CONFIG)

# ===============================
# HELPER FUNCTIONS
# ===============================
def format_value(value, param_type: str, unit: str = ""):
    """Format value for display"""
    if param_type == "bool":
        return "ON" if value else "OFF"
    else:
        return f"{float(value):.2f} {unit}".strip()

def get_status_class(param_name: str, value) -> str:
    """Get CSS class for status indicator"""
    if param_name == "ready":
        return "status-yellow" if value else "status-off"
    elif param_name == "running":
        return "status-green" if value else "status-off"
    elif param_name == "trip":
        return "status-red" if value else "status-off"
    return "status-off"

# ===============================
# ROUTES
# ===============================
@app.route('/')
def index():
    """Home page - Dashboard overview"""
    return render_template('index.html')

@app.route('/pump/<int:pump_id>')
def pump_detail(pump_id):
    """Pump detail page"""
    if pump_id < 1 or pump_id > 7:
        return "Invalid pump ID", 404
    return render_template('pump.html', pump_id=pump_id)

@app.route('/reports')
def reports():
    """Reports page"""
    return render_template('reports.html')

@app.route('/api/data')
def get_data():
    """API endpoint for all PLC data"""
    data = plc_manager.get_data()
    
    # Prepare response with parameter info
    response = {}
    for pump_id in range(1, 8):
        pump_key = f"pump_{pump_id}"
        if pump_key in data:
            response[pump_key] = {
                "values": data[pump_key],
                "parameters": PUMP_PARAMETERS[pump_id]
            }
    
    # Calculate alarm state (any pump trip)
    alarm_active = any(data.get(f"pump_{i}", {}).get("trip", False) for i in range(1, 8))
    response["system_alarm"] = alarm_active
    
    # Add pressure setpoints for dashboard
    response["pressure_setpoints"] = {}
    for pump_id in range(1, 8):
        pump_key = f"pump_{pump_id}"
        if pump_key in data and "pressure_setpoint" in data[pump_key]:
            response["pressure_setpoints"][pump_id] = {
                "value": data[pump_key]["pressure_setpoint"],
                "unit": "bar"
            }
    
    response["timestamp"] = datetime.now().isoformat()
    
    return jsonify(response)

@app.route('/api/pump/<int:pump_id>')
def get_pump_data(pump_id):
    """API endpoint for specific pump data"""
    if pump_id < 1 or pump_id > 7:
        return {"error": "Invalid pump ID"}, 404
    
    data = plc_manager.get_data()
    pump_key = f"pump_{pump_id}"
    
    if pump_key not in data:
        return {"error": "Pump data not available"}, 404
    
    response = {
        "pump_id": pump_id,
        "values": data[pump_key],
        "parameters": PUMP_PARAMETERS[pump_id],
        "timestamp": datetime.now().isoformat()
    }
    
    return jsonify(response)

@app.route('/api/status')
def get_status():
    """Get connection status"""
    return jsonify({
        "plc_connected": plc_manager.connected,
        "plc_ip": PLC_CONFIG["ip"],
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/reports')
def get_reports():
    """Get all pump status for reports"""
    data = plc_manager.get_data()
    
    report_data = []
    for pump_id in range(1, 8):
        pump_key = f"pump_{pump_id}"
        if pump_key not in data:
            continue
        
        pump_values = data[pump_key]
        pump_params = PUMP_PARAMETERS[pump_id]
        
        report_data.append({
            "pump_id": pump_id,
            "status": {
                "ready": pump_values.get("ready", False),
                "running": pump_values.get("running", False),
                "trip": pump_values.get("trip", False),
            },
            "metrics": {
                "pressure": {
                    "value": pump_values.get("pressure", 0),
                    "unit": pump_params["pressure"].get("unit", "bar"),
                    "setpoint": pump_values.get("pressure_setpoint", 0)
                },
                "speed": {
                    "value": pump_values.get("speed", 0),
                    "unit": pump_params["speed"].get("unit", "Hz")
                }
            }
        })
    
    return jsonify({
        "timestamp": datetime.now().isoformat(),
        "pumps": report_data
    })

@app.route('/api/historical/<int:pump_id>')
def get_historical(pump_id: int):
    """Get historical data for specific pump"""
    hours = request.args.get('hours', 24, type=int)
    data = db_manager.get_historical_data(pump_id=pump_id, hours=hours)
    return jsonify({
        "pump_id": pump_id,
        "hours": hours,
        "data": data,
        "count": len(data)
    })

@app.route('/api/historical')
def get_all_historical():
    """Get all historical data"""
    hours = request.args.get('hours', 24, type=int)
    data = db_manager.get_historical_data(hours=hours)
    return jsonify({
        "hours": hours,
        "data": data,
        "count": len(data)
    })

@app.route('/api/stats/<int:pump_id>')
def get_pump_stats(pump_id: int):
    """Get statistics for specific pump"""
    hours = request.args.get('hours', 24, type=int)
    stats = db_manager.get_stats(pump_id=pump_id, hours=hours)
    return jsonify({
        "pump_id": pump_id,
        "hours": hours,
        "stats": stats
    })

@app.route('/api/stats')
def get_all_stats():
    """Get statistics for all pumps"""
    hours = request.args.get('hours', 24, type=int)
    all_stats = {}
    for pump_id in range(1, 8):
        all_stats[f"pump_{pump_id}"] = db_manager.get_stats(pump_id=pump_id, hours=hours)
    return jsonify({
        "hours": hours,
        "stats": all_stats
    })

@app.route('/api/trip-events/<int:pump_id>')
def get_trip_events_api(pump_id: int):
    """Get trip events for specific pump"""
    hours = request.args.get('hours', 24, type=int)
    events = db_manager.get_trip_events(pump_id=pump_id, hours=hours)
    return jsonify({
        "pump_id": pump_id,
        "hours": hours,
        "events": events,
        "count": len(events)
    })

@app.route('/api/trip-events')
def get_all_trip_events():
    """Get all trip events"""
    hours = request.args.get('hours', 24, type=int)
    events = db_manager.get_trip_events(hours=hours)
    return jsonify({
        "hours": hours,
        "events": events,
        "count": len(events)
    })

@app.route('/api/status-events/<int:pump_id>')
def get_status_events_api(pump_id: int):
    """Get status change events for specific pump"""
    hours = request.args.get('hours', 24, type=int)
    events = db_manager.get_status_events(pump_id=pump_id, hours=hours)
    return jsonify({
        "pump_id": pump_id,
        "hours": hours,
        "events": events,
        "count": len(events)
    })

@app.route('/api/status-events')
def get_all_status_events():
    """Get all status change events"""
    hours = request.args.get('hours', 24, type=int)
    events = db_manager.get_status_events(hours=hours)
    return jsonify({
        "hours": hours,
        "events": events,
        "count": len(events)
    })

@app.route('/api/export/csv')
def export_csv():
    """Export historical data as CSV"""
    from io import StringIO
    hours = request.args.get('hours', 24, type=int)
    data = db_manager.get_historical_data(hours=hours)
    
    if not data:
        return jsonify({"error": "No data to export"}), 404
    
    output = StringIO()
    output.write("timestamp,pump_id,pressure,speed,pressure_setpoint,ready,running,trip\n")
    
    for row in data:
        output.write(f"{row.get('timestamp','')},{row.get('pump_id','')},{row.get('pressure','')},")
        output.write(f"{row.get('speed','')},{row.get('pressure_setpoint','')},")
        output.write(f"{row.get('ready','')},{row.get('running','')},{row.get('trip','')}\n")
    
    response_str = output.getvalue()
    return response_str, 200, {'Content-Disposition': 'attachment; filename="pump_data.csv"'}

@app.route('/api/export/pdf')
def export_pdf():
    """Export trip and status events as PDF"""
    try:
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
        from reportlab.lib.units import inch
        from io import BytesIO
        
        hours = request.args.get('hours', 720, type=int)  # Default 30 days
        trip_events = db_manager.get_trip_events(hours=hours)
        status_events = db_manager.get_status_events(hours=hours)
        
        # Create PDF
        pdf_buffer = BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a3a52'),
            spaceAfter=30
        )
        story.append(Paragraph("Challawa SCADA System Report", title_style))
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
        story.append(Spacer(1, 0.3*inch))
        
        # Trip Events Section
        story.append(Paragraph("Pump Trip Events", styles['Heading2']))
        if trip_events:
            trip_data = [['Timestamp', 'Pump ID', 'Trip State', 'Pressure (bar)', 'Speed (Hz)']]
            for event in trip_events[-100:]:  # Last 100 events
                trip_data.append([
                    event.get('timestamp', ''),
                    str(event.get('pump_id', '')),
                    'TRIP ON' if event.get('trip_state') else 'TRIP OFF',
                    f"{event.get('pressure', 0):.2f}",
                    f"{event.get('speed', 0):.2f}"
                ])
            
            trip_table = Table(trip_data, colWidths=[1.8*inch, 0.8*inch, 1.2*inch, 1.2*inch, 1.2*inch])
            trip_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5aa0')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(trip_table)
        else:
            story.append(Paragraph("No trip events recorded.", styles['Normal']))
        
        story.append(Spacer(1, 0.5*inch))
        story.append(PageBreak())
        
        # Status Events Section
        story.append(Paragraph("Pump Status Events", styles['Heading2']))
        if status_events:
            status_data = [['Timestamp', 'Pump ID', 'Status', 'Description', 'Pressure (bar)', 'Speed (Hz)']]
            for event in status_events[-100:]:  # Last 100 events
                status_data.append([
                    event.get('timestamp', ''),
                    str(event.get('pump_id', '')),
                    event.get('status', ''),
                    event.get('description', ''),
                    f"{event.get('pressure', 0):.2f}",
                    f"{event.get('speed', 0):.2f}"
                ])
            
            status_table = Table(status_data, colWidths=[1.5*inch, 0.8*inch, 1.0*inch, 1.5*inch, 1.0*inch, 0.9*inch])
            status_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5aa0')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(status_table)
        else:
            story.append(Paragraph("No status events recorded.", styles['Normal']))
        
        doc.build(story)
        pdf_buffer.seek(0)
        
        return pdf_buffer.getvalue(), 200, {
            'Content-Disposition': f'attachment; filename="SCADA_Report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf"',
            'Content-Type': 'application/pdf'
        }
    except ImportError:
        return jsonify({"error": "reportlab not installed. Install with: pip install reportlab"}), 500
    except Exception as e:
        logger.error(f"Error generating PDF: {e}")
        return jsonify({"error": str(e)}), 500

# ===============================
# WEBSOCKET EVENTS
# ===============================
@socketio.on('connect')
def handle_connect():
    """Client connected"""
    logger.info(f"Client connected: {request.sid}")
    emit('connection_response', {
        'data': 'Connected to SCADA Dashboard',
        'plc_connected': plc_manager.connected
    })
    
    # Start sending updates
    emit_data_updates()

@socketio.on('disconnect')
def handle_disconnect():
    """Client disconnected"""
    logger.info(f"Client disconnected: {request.sid}")

@socketio.on('request_update')
def handle_update_request():
    """Client requested data update"""
    emit_data_updates()

def emit_data_updates():
    """Emit data updates to all connected clients"""
    data = plc_manager.get_data()
    
    # Calculate alarm state
    alarm_active = any(data.get(f"pump_{i}", {}).get("trip", False) for i in range(1, 8))
    
    # Prepare home page data (pressure setpoints only)
    home_data = {
        "timestamp": datetime.now().isoformat(),
        "system_alarm": alarm_active,
        "pressure_setpoints": {}
    }
    
    for pump_id in range(1, 8):
        pump_key = f"pump_{pump_id}"
        if pump_key in data and "pressure_setpoint" in data[pump_key]:
            home_data["pressure_setpoints"][pump_id] = {
                "value": data[pump_key]["pressure_setpoint"],
                "unit": "bar"
            }
    
    socketio.emit('data_update', home_data)

# ===============================
# SHUTDOWN HANDLER
# ===============================
def cleanup():
    """Cleanup resources on shutdown"""
    try:
        logger.info("Performing cleanup...")
        plc_manager.stop_polling()
        plc_manager.disconnect()
        logger.info("Cleanup complete")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")

import atexit
atexit.register(cleanup)

# ===============================
# MAIN
# ===============================
if __name__ == '__main__':
    try:
        # Connect to PLC
        logger.info("Initializing Challawa SCADA System...")
        plc_manager.connect()
        plc_manager.start_polling(interval=1.0)
        
        # Start Flask server
        logger.info("Starting Flask server on 0.0.0.0:5000")
        logger.info("Press Ctrl+C to shutdown gracefully...")
        socketio.run(app, host='0.0.0.0', port=5000, debug=False)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        cleanup()
