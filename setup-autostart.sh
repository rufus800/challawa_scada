#!/bin/bash
# Challawa SCADA System - Setup Auto-Start Service on IOT2050
# This script enables the Flask app to start automatically on boot

echo "=========================================="
echo "Challawa SCADA - Auto-Start Setup"
echo "=========================================="

# Copy the service file to systemd
echo "[1/4] Copying service file..."
sudo cp /home/root/challawa_scada/challawa-scada.service /etc/systemd/system/

# Reload systemd daemon to recognize new service
echo "[2/4] Reloading systemd daemon..."
sudo systemctl daemon-reload

# Enable the service to start on boot
echo "[3/4] Enabling service on boot..."
sudo systemctl enable challawa-scada.service

# Start the service immediately
echo "[4/4] Starting service..."
sudo systemctl start challawa-scada.service

# Check status
echo ""
echo "=========================================="
echo "Service Installation Complete!"
echo "=========================================="
echo ""
systemctl status challawa-scada.service

echo ""
echo "Useful Commands:"
echo "  View logs:              journalctl -u challawa-scada -f"
echo "  Start service:          sudo systemctl start challawa-scada"
echo "  Stop service:           sudo systemctl stop challawa-scada"
echo "  Restart service:        sudo systemctl restart challawa-scada"
echo "  Check status:           sudo systemctl status challawa-scada"
echo "  Disable auto-start:     sudo systemctl disable challawa-scada"
echo ""
echo "Dashboard URL: http://challawaOP.akfotekengoineering.com:5000"
echo ""
