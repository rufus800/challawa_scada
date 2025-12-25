# Challawa SCADA Dashboard

A professional, responsive web-based SCADA (Supervisory Control and Data Acquisition) system for monitoring 7 industrial pumps in real-time.

## Features

✨ **Modern Web Interface**
- Fully responsive design (mobile, tablet, desktop)
- Beautiful dark-themed UI with professional styling
- Real-time data updates via WebSocket
- Smooth animations and transitions

📊 **Home Dashboard**
- System alarm status with bright red flashing animation
- Pressure setpoints for all 7 pumps
- Real-time connection status indicator
- System timestamp

🔧 **Pump Monitoring**
- Individual pump detail pages
- Status indicators (Ready/Running/Trip)
- Real-time metrics (Pressure, Speed)
- Progress bars showing current values vs. range
- Pump selector dropdown for quick navigation

🔌 **PLC Integration**
- SNAP7 library for Siemens S7-1200 PLC connection
- Configurable IP, Rack, Slot, and DB addresses
- Real-time polling with configurable intervals
- Simulated data mode for testing/demo

🎯 **Professional Design**
- ISA-101 compliance principles
- Color-coded status indicators
- Responsive grid layouts
- Accessibility-focused
- Mobile-first approach

## System Requirements

- **Python**: 3.8 or higher
- **PLC**: Siemens S7-1200 (or compatible)
- **Network**: Direct connection to PLC via Ethernet
- **Browser**: Modern browser (Chrome, Firefox, Safari, Edge)

## Installation

### 1. Clone or Download the Project

```bash
cd challawa_scada
```

### 2. Create Virtual Environment (Optional but Recommended)

```bash
python -m venv venv

# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

**Note**: If `python-snap7` installation fails, you may need to install it via conda:
```bash
conda install -c conda-forge python-snap7
```

## Configuration

Edit `app.py` and modify the `PLC_CONFIG` dictionary:

```python
PLC_CONFIG = {
    "ip": "192.168.200.20",      # PLC IP address
    "rack": 0,                     # PLC Rack number
    "slot": 1,                     # PLC Slot number
    "db": 39                       # Data block number
}
```

### Pump Parameters

Each pump's parameters are defined in the `PUMP_PARAMETERS` dictionary with their offsets and data types:

```python
PUMP_PARAMETERS = {
    1: {
        "ready": {"offset": 0.1, "type": "bool", ...},
        "running": {"offset": 0.2, "type": "bool", ...},
        "trip": {"offset": 0.3, "type": "bool", ...},
        "pressure": {"offset": 2.0, "type": "real", ...},
        "speed": {"offset": 10.0, "type": "real", ...},
        "pressure_setpoint": {"offset": 6.0, "type": "real", ...},
    },
    # ... pumps 2-7 ...
}
```

Adjust offsets according to your PLC program layout.

## Running the Application

### Development Mode

```bash
python app.py
```

The application will:
1. Attempt to connect to the PLC
2. Start the Flask development server
3. Be accessible at `http://localhost:5000`

### Production Deployment

For production, use a WSGI server like Gunicorn:

```bash
pip install gunicorn python-socketio[client]
gunicorn --worker-class eventlet -w 1 -b 0.0.0.0:5000 app:app
```

## Accessing the Dashboard

- **Home Dashboard**: `http://localhost:5000` (or your domain)
- **Pump Detail Pages**: `http://localhost:5000/pump/1` (for Pump 1, etc.)
- **API Endpoints**:
  - `/api/data` - All pump data
  - `/api/pump/<id>` - Specific pump data
  - `/api/status` - System status

## API Documentation

### GET /api/data
Returns all pump data with system alarm status and timestamp.

**Response**:
```json
{
  "system_alarm": false,
  "pressure_setpoints": {
    "1": {"value": 5.5, "unit": "bar"},
    "2": {"value": 5.8, "unit": "bar"},
    ...
  },
  "pump_1": {
    "values": {
      "ready": true,
      "running": true,
      "trip": false,
      "pressure": 5.42,
      "speed": 35.2,
      "pressure_setpoint": 5.5
    },
    "parameters": { ... }
  },
  ...
  "timestamp": "2025-12-25T10:30:45.123456"
}
```

### GET /api/pump/<id>
Returns data for a specific pump.

### GET /api/status
Returns PLC connection status and timestamp.

## Real-Time Updates (WebSocket)

The dashboard uses Socket.IO for real-time updates. Events:

- **data_update**: Sent periodically with latest sensor values
- **connection_response**: Sent on client connection
- **request_update**: Client can request immediate update

## Simulated Mode

If the PLC is not available or python-snap7 is not installed, the application automatically falls back to simulated data:

```python
if not HAS_SNAP7:
    print("WARNING: snap7 not installed. Install with: pip install python-snap7")
    # Falls back to simulated data with random values
```

## File Structure

```
challawa_scada/
├── app.py                      # Flask application & PLC manager
├── requirements.txt            # Python dependencies
├── static/
│   ├── css/
│   │   ├── style.css          # Main stylesheet
│   │   └── animations.css     # Animation definitions
│   └── js/
│       ├── dashboard.js       # Home page logic
│       └── pump-detail.js     # Pump detail page logic
├── templates/
│   ├── index.html             # Home page
│   └── pump.html              # Pump detail page template
└── README.md                  # This file
```

## Customization

### Styling

Edit `static/css/style.css` to customize:
- Colors (see `:root` CSS variables)
- Typography
- Layout and spacing
- Responsive breakpoints

### Adding More Pumps

To support more than 7 pumps:

1. Add pump configuration to `PUMP_PARAMETERS` in `app.py`
2. Add `<option>` tags to pump selectors in HTML templates
3. Adjust grid layouts in CSS if needed

### Changing Update Frequency

In `app.py`:
```python
# Change this value (in seconds)
plc_manager.start_polling(interval=1.0)  # 1 second polling
```

In JavaScript files (`static/js/dashboard.js` and `pump-detail.js`):
```javascript
// Change this value (in milliseconds)
updateInterval = setInterval(() => {
    fetchAndUpdateData();
}, 2000);  // 2 second update interval
```

## Troubleshooting

### Connection Issues

1. **PLC Not Found**
   - Verify PLC IP address in `PLC_CONFIG`
   - Check network connectivity: `ping 192.168.200.20`
   - Verify PLC is powered on and has network connection

2. **snap7 Installation Fails**
   - Use conda: `conda install -c conda-forge python-snap7`
   - Or install from alternative source

### No Data Displayed

1. Check browser console for errors (F12)
2. Verify Flask server is running
3. Check that simulated data is working (fallback mode)
4. Review PLC parameter offsets match your program

### Slow Updates

1. Increase polling interval in `app.py`
2. Reduce client-side update frequency in JavaScript
3. Check network latency to PLC

## Security Considerations

⚠️ **This is a development version. For production use:**

1. Enable HTTPS/SSL
2. Implement authentication (Flask-Login)
3. Add authorization (role-based access)
4. Use environment variables for configuration
5. Implement input validation
6. Add rate limiting
7. Use a production WSGI server (Gunicorn, uWSGI)

## License

© 2025 Challawa Industrial Systems. All rights reserved.

## Support

For issues, questions, or feature requests, please contact the development team.

---

**Version**: 1.0.0
**Last Updated**: December 25, 2025
