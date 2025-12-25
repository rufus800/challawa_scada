# 🚀 Challawa SCADA Dashboard - IoT2050 Deployment Guide

## Prerequisites
- **IoT2050 Device** with Debian Linux installed
- **Network Connection** to PLC (192.168.200.20)
- **Python 3.7+** (usually pre-installed on Debian)
- **pip** package manager

---

## Step 1: Transfer Files to IoT2050

### Option A: Using SCP (Secure Copy)
```bash
# From your local machine:
scp -r ~/challlawa_scada root@<IOT2050_IP>:/root/
# Example: scp -r ~/challlawa_scada root@192.168.1.100:/root/
```

### Option B: Using Git
```bash
# If you have a Git repository:
ssh root@<IOT2050_IP>
git clone <your-repo-url> /root/challlawa_scada
cd /root/challlawa_scada
```

### Option C: Manual USB/Network Drive
- Copy the `challlawa_scada` folder to the IoT2050

---

## Step 2: Connect to IoT2050

```bash
ssh root@<IOT2050_IP>
# or ssh <your-username>@<IOT2050_IP>

# Navigate to project directory
cd /root/challlawa_scada
# or cd ~/challlawa_scada if in home directory
```

---

## Step 3: Install Python Dependencies

```bash
# Update package lists
sudo apt-get update

# Install Python3 and pip (if not installed)
sudo apt-get install python3 python3-pip -y

# Navigate to project directory
cd ~/challlawa_scada

# Install requirements
pip3 install -r requirements.txt

# Or with sudo if needed:
sudo pip3 install -r requirements.txt
```

---

## Step 4: Configure PLC Connection

Edit `app.py` and verify the PLC configuration:

```python
PLC_CONFIG = {
    "ip": "192.168.200.20",      # ← Verify this matches your PLC IP
    "rack": 0,
    "slot": 1,
    "db": 39
}
```

**If PLC is on different IP/port**, update accordingly.

---

## Step 5: Run the Dashboard

### Option A: Direct Execution (Testing)
```bash
cd ~/challlawa_scada
python3 app.py
```

You should see:
```
WARNING: This is a development server. Do not use it in production.
Running on http://0.0.0.0:5000
```

### Option B: Run in Background (Production)
```bash
nohup python3 app.py > dashboard.log 2>&1 &
echo $! > dashboard.pid
```

### Option C: Run as a Service (Recommended)

Create a systemd service file:

```bash
sudo nano /etc/systemd/system/challawa-dashboard.service
```

Paste this content:

```ini
[Unit]
Description=Challawa SCADA Dashboard
After=network.target
StartLimitIntervalSec=0

[Service]
Type=simple
Restart=always
RestartSec=10
User=root
WorkingDirectory=/root/challlawa_scada
ExecStart=/usr/bin/python3 /root/challlawa_scada/app.py
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Then enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable challawa-dashboard
sudo systemctl start challawa-dashboard

# Check status:
sudo systemctl status challawa-dashboard

# View logs:
sudo journalctl -u challawa-dashboard -f
```

---

## Step 6: Access the Dashboard

Once running, access via:

- **Local Network**: `http://<IOT2050_IP>:5000`
  - Example: `http://192.168.1.100:5000`

- **From Your Computer**: `http://challawa-scada.your-domain.com` (if configured with domain/reverse proxy)

---

## Step 7: Configure Domain (Optional)

### Using Nginx as Reverse Proxy

```bash
# Install Nginx
sudo apt-get install nginx -y

# Create config
sudo nano /etc/nginx/sites-available/default
```

Replace content with:

```nginx
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    
    server_name _;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Then:

```bash
sudo systemctl restart nginx
```

### Using SSL with Let's Encrypt

```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx -y

# Get certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal should be enabled automatically
sudo systemctl enable certbot.timer
```

---

## Step 8: Monitor & Troubleshoot

### Check if app is running:
```bash
ps aux | grep python3
```

### View recent logs:
```bash
# If running as service:
sudo journalctl -u challawa-dashboard -n 50

# If running in background:
tail -f dashboard.log
```

### Test network connectivity to PLC:
```bash
ping 192.168.200.20
```

### Restart the service:
```bash
sudo systemctl restart challawa-dashboard
```

### Stop the service:
```bash
sudo systemctl stop challawa-dashboard
```

---

## Step 9: Auto-Start on Boot

If using systemd service (recommended):
```bash
sudo systemctl enable challawa-dashboard
```

The dashboard will automatically start when the IoT2050 boots up.

---

## Troubleshooting

### Port 5000 Already in Use
```bash
# Find process using port 5000
sudo lsof -i :5000

# Kill it and restart
sudo kill -9 <PID>
sudo systemctl restart challawa-dashboard
```

### Cannot Connect to PLC
- Verify PLC IP: `ping 192.168.200.20`
- Check network cable connections
- Verify firewall isn't blocking port 102 (SNAP7 uses port 102)
- Dashboard will show simulated data if PLC isn't connected (graceful fallback)

### Python Module Not Found
```bash
pip3 install -r requirements.txt --upgrade
```

### Permission Denied Errors
```bash
sudo chown -R root:root ~/challlawa_scada
chmod -R 755 ~/challlawa_scada
```

---

## Performance Notes

- **Memory Usage**: ~80-120 MB (minimal)
- **CPU Usage**: ~2-5% (when idle)
- **Network Bandwidth**: ~5-10 KB/s (per user)
- **Polling Interval**: 1 second (configurable in app.py)

---

## Security Recommendations

For production deployment:

1. **Change default credentials** if database is later added
2. **Use HTTPS** (SSL/TLS via Nginx reverse proxy)
3. **Enable firewall** and only allow necessary ports
4. **Use strong passwords** for system access
5. **Regular backups** of configuration files
6. **Monitor logs** for unusual activity

---

## Quick Start Summary

```bash
# 1. SSH to IoT2050
ssh root@<IOT2050_IP>

# 2. Install dependencies
cd ~/challlawa_scada
pip3 install -r requirements.txt

# 3. Run as service (recommended)
sudo nano /etc/systemd/system/challawa-dashboard.service
# (Copy content from Step 5 above)
sudo systemctl enable challawa-dashboard
sudo systemctl start challawa-dashboard

# 4. Access dashboard
# Visit: http://<IOT2050_IP>:5000
```

---

## Support

For issues or questions:
- Check logs: `sudo journalctl -u challawa-dashboard -f`
- Verify PLC connection: `ping 192.168.200.20`
- Ensure all dependencies installed: `pip3 list`
