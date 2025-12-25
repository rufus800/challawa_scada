# 🚀 Quick Reference - Challawa SCADA on IoT2050

## File Structure (After Cleanup)
```
challlawa_scada/
├── app.py                      # Main Flask application
├── requirements.txt            # Python dependencies
├── IOT2050_DEPLOYMENT.md      # Full deployment guide
├── setup-iot2050.sh           # Automated setup script
├── static/
│   ├── css/
│   │   ├── animations.css
│   │   └── style.css
│   └── js/
│       ├── dashboard.js
│       ├── pump-detail.js
│       └── reports.js
└── templates/
    ├── index.html
    ├── pump.html
    └── reports.html
```

## Fastest Setup (3 Steps)

### Step 1: Transfer to IoT2050
```bash
scp -r ~/challlawa_scada root@<IOT2050_IP>:/root/
# Example: scp -r ~/challlawa_scada root@192.168.1.50:/root/
```

### Step 2: Run Automated Setup
```bash
ssh root@<IOT2050_IP>
cd /root/challlawa_scada
chmod +x setup-iot2050.sh
sudo ./setup-iot2050.sh
```

### Step 3: Access Dashboard
```
Open browser: http://<IOT2050_IP>:5000
```

---

## Manual Setup (If Preferred)

```bash
# Connect to IoT2050
ssh root@<IOT2050_IP>

# Navigate to project
cd /root/challlawa_scada

# Install dependencies
pip3 install -r requirements.txt

# Create service
sudo nano /etc/systemd/system/challawa-dashboard.service
# Copy content from IOT2050_DEPLOYMENT.md step 5

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable challawa-dashboard
sudo systemctl start challawa-dashboard

# Check status
sudo systemctl status challawa-dashboard
```

---

## Important Configuration

Edit `app.py` line 40-45 if PLC IP is different:

```python
PLC_CONFIG = {
    "ip": "192.168.200.20",  # ← YOUR PLC IP HERE
    "rack": 0,
    "slot": 1,
    "db": 39
}
```

---

## Monitoring Commands

```bash
# Check if running
sudo systemctl status challawa-dashboard

# View real-time logs
sudo journalctl -u challawa-dashboard -f

# Last 50 lines
sudo journalctl -u challawa-dashboard -n 50

# Stop service
sudo systemctl stop challawa-dashboard

# Restart service
sudo systemctl restart challawa-dashboard

# View error logs
sudo journalctl -u challawa-dashboard -p err
```

---

## Network Access

| Access Type | URL |
|---|---|
| Local Network | `http://<IOT2050_IP>:5000` |
| With Domain | `http://your-domain.com` |
| Secure (HTTPS) | `https://your-domain.com` |

**Example:**
- IoT2050 IP: `192.168.1.50`
- Access: `http://192.168.1.50:5000`

---

## Troubleshooting

### Service won't start?
```bash
sudo journalctl -u challawa-dashboard -n 50
```

### Can't reach PLC?
```bash
ping 192.168.200.20
```

### Port 5000 in use?
```bash
sudo lsof -i :5000
sudo kill -9 <PID>
sudo systemctl restart challawa-dashboard
```

### Need to reinstall dependencies?
```bash
pip3 install -r requirements.txt --upgrade
```

---

## Auto-Start Verification

To verify the service auto-starts on boot:

```bash
sudo reboot  # Reboot IoT2050

# After reboot, check if running:
sudo systemctl status challawa-dashboard

# Should show "active (running)"
```

---

## System Requirements

- Python 3.7+
- 512 MB RAM (minimum)
- Network access to PLC (192.168.200.20)
- Port 5000 available (or change in app.py)

---

## Contact & Support

If issues arise:
1. Check logs: `sudo journalctl -u challawa-dashboard -f`
2. Verify PLC connectivity: `ping 192.168.200.20`
3. Ensure dependencies: `pip3 list | grep Flask`
4. Review IOT2050_DEPLOYMENT.md for detailed guide
