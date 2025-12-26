# Quick Start: Auto-Run SCADA on IOT2050 Boot

## One-Command Setup

SSH into your IOT2050 and run:

```bash
cd /home/root/challawa_scada && chmod +x setup-autostart.sh && ./setup-autostart.sh
```

## What This Does
✅ Copies service configuration to systemd  
✅ Enables Flask app to start on boot  
✅ Starts the dashboard immediately  
✅ Auto-restarts if the app crashes  

## Result
Your dashboard will be available at:
```
http://challawaOP.akfotekengoineering.com:5000
```

Even after device reboots!

## View Logs
```bash
journalctl -u challawa-scada -f
```

## Useful Commands
```bash
sudo systemctl status challawa-scada      # Check if running
sudo systemctl restart challawa-scada     # Restart service
sudo systemctl stop challawa-scada        # Stop service
```

That's it! 🎉
