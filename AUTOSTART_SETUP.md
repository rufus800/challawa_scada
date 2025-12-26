# IOT2050 Auto-Start Setup Guide

## Overview
This guide will help you set up the Challawa SCADA system to automatically start when the IOT2050 device boots up. Once configured, the dashboard will be immediately available at `http://challawaOP.akfotekengoineering.com:5000` without manual intervention.

## Prerequisites
- SSH access to the IOT2050 device
- The `challawa_scada` folder deployed to `/home/root/challawa_scada/`
- Python 3 and all dependencies installed (see requirements.txt)

## Installation Steps

### Option 1: Automated Setup (Recommended)

1. **SSH into the IOT2050 device:**
```bash
ssh root@challawaOP.akfotekengoineering.com
# or
ssh root@<IOT2050_IP_ADDRESS>
```

2. **Navigate to the project directory:**
```bash
cd /home/root/challawa_scada
```

3. **Run the automated setup script:**
```bash
chmod +x setup-autostart.sh
./setup-autostart.sh
```

The script will:
- Copy the systemd service file
- Reload the systemd daemon
- Enable auto-start on boot
- Start the service immediately

### Option 2: Manual Setup

1. **Copy the service file to systemd:**
```bash
sudo cp /home/root/challawa_scada/challawa-scada.service /etc/systemd/system/
```

2. **Reload systemd daemon:**
```bash
sudo systemctl daemon-reload
```

3. **Enable the service to start on boot:**
```bash
sudo systemctl enable challawa-scada.service
```

4. **Start the service immediately:**
```bash
sudo systemctl start challawa-scada.service
```

5. **Verify it's running:**
```bash
sudo systemctl status challawa-scada.service
```

## Verification

### Check Service Status
```bash
sudo systemctl status challawa-scada.service
```

Expected output:
```
● challawa-scada.service - Challawa SCADA System - Industrial Pump Monitoring Dashboard
   Loaded: loaded (/etc/systemd/system/challawa-scada.service; enabled; vendor preset: enabled)
   Active: active (running) since <date/time>
   Main PID: <PID> (python3)
```

### View Live Logs
```bash
journalctl -u challawa-scada -f
```

This shows real-time logs from the service.

### Test the Dashboard
Open your browser and visit:
```
http://challawaOP.akfotekengoineering.com:5000
```

## Service Management Commands

### Start the service
```bash
sudo systemctl start challawa-scada.service
```

### Stop the service
```bash
sudo systemctl stop challawa-scada.service
```

### Restart the service
```bash
sudo systemctl restart challawa-scada.service
```

### View service logs (last 50 lines)
```bash
journalctl -u challawa-scada -n 50
```

### View service logs (real-time)
```bash
journalctl -u challawa-scada -f
```

### Disable auto-start (service still runs, won't start on boot)
```bash
sudo systemctl disable challawa-scada.service
```

### Re-enable auto-start
```bash
sudo systemctl enable challawa-scada.service
```

## Troubleshooting

### Service won't start
1. Check the logs: `journalctl -u challawa-scada -n 100`
2. Verify the service file path: `cat /etc/systemd/system/challawa-scada.service`
3. Check Python installation: `python3 --version`
4. Verify project path exists: `ls -la /home/root/challawa_scada/`

### Dashboard not accessible at domain
1. Verify service is running: `sudo systemctl status challawa-scada.service`
2. Check if Flask is listening on port 5000: `sudo netstat -tlnp | grep 5000`
3. Verify DNS resolution: `nslookup challawaOP.akfotekengoineering.com`

### High memory or CPU usage
The service includes auto-restart on failure, but if experiencing issues:
```bash
sudo systemctl stop challawa-scada.service
# Then review logs and make necessary changes
sudo systemctl start challawa-scada.service
```

### Reboot Test
To verify auto-start on reboot:
```bash
sudo reboot
# After device comes back online, check:
sudo systemctl status challawa-scada.service
```

## Service File Explanation

The systemd service file (`challawa-scada.service`) includes:

- **After=network-online.target**: Waits for network to be ready before starting
- **Wants=network-online.target**: Explicitly requests network to be online
- **Type=simple**: Runs the Flask app directly (not daemonized)
- **Restart=always**: Automatically restarts if the app crashes
- **RestartSec=10**: Waits 10 seconds before restarting
- **StandardOutput=journal**: Logs to systemd journal
- **WantedBy=multi-user.target**: Starts in multi-user mode

## Additional Notes

- The service runs as `root` user (necessary for PLC access)
- Working directory is set to `/home/root/challawa_scada/`
- Flask app runs on `0.0.0.0:5000` (accessible from any interface)
- Logs are stored in systemd journal (accessible via `journalctl`)
- Service will survive system reboots automatically

## Accessing Remote Dashboard

Once configured, you can access the dashboard from any device on the network:

- **Local network**: `http://<IOT2050_IP>:5000`
- **Remote (if configured)**: `http://challawaOP.akfotekengoineering.com:5000`

## Uninstallation

If you need to remove auto-start:

```bash
# Stop the service
sudo systemctl stop challawa-scada.service

# Disable auto-start
sudo systemctl disable challawa-scada.service

# Remove the service file
sudo rm /etc/systemd/system/challawa-scada.service

# Reload systemd
sudo systemctl daemon-reload
```

To manually run the app again:
```bash
cd /home/root/challawa_scada
python3 app.py
```

## Support

For issues or questions:
1. Check the logs: `journalctl -u challawa-scada -f`
2. Verify Python dependencies: `pip3 install -r requirements.txt`
3. Test manual execution: `python3 /home/root/challawa_scada/app.py`
