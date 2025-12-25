#!/bin/bash

# Challawa SCADA Dashboard - IoT2050 Auto-Setup Script
# This script automates the entire setup process

set -e  # Exit on error

echo "================================"
echo "Challawa SCADA Dashboard Setup"
echo "================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -ne 0 ]; then
   echo -e "${RED}Please run as root (sudo)${NC}"
   exit 1
fi

echo -e "${YELLOW}[1/6]${NC} Updating system packages..."
apt-get update
apt-get install -y python3 python3-pip

echo -e "${YELLOW}[2/6]${NC} Installing Python dependencies..."
cd $(dirname "$0")
pip3 install -r requirements.txt

echo -e "${YELLOW}[3/6]${NC} Creating systemd service..."
cat > /etc/systemd/system/challawa-dashboard.service << EOF
[Unit]
Description=Challawa SCADA Dashboard
After=network.target
StartLimitIntervalSec=0

[Service]
Type=simple
Restart=always
RestartSec=10
User=root
WorkingDirectory=$(pwd)
ExecStart=/usr/bin/python3 $(pwd)/app.py
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

echo -e "${YELLOW}[4/6]${NC} Enabling systemd service..."
systemctl daemon-reload
systemctl enable challawa-dashboard

echo -e "${YELLOW}[5/6]${NC} Configuring Nginx reverse proxy (optional)..."
read -p "Install Nginx for reverse proxy? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    apt-get install -y nginx
    
    cat > /etc/nginx/sites-available/default << EOF
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    
    server_name _;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF
    
    systemctl enable nginx
    systemctl restart nginx
    echo -e "${GREEN}✓ Nginx configured${NC}"
fi

echo -e "${YELLOW}[6/6]${NC} Starting dashboard service..."
systemctl start challawa-dashboard

# Wait a moment for service to start
sleep 2

# Check if service is running
if systemctl is-active --quiet challawa-dashboard; then
    echo ""
    echo -e "${GREEN}================================${NC}"
    echo -e "${GREEN}✓ Setup Complete!${NC}"
    echo -e "${GREEN}================================${NC}"
    echo ""
    echo -e "Dashboard is running at: ${YELLOW}http://$(hostname -I | awk '{print $1}'):5000${NC}"
    echo ""
    echo "Useful commands:"
    echo "  View status:     sudo systemctl status challawa-dashboard"
    echo "  View logs:       sudo journalctl -u challawa-dashboard -f"
    echo "  Stop service:    sudo systemctl stop challawa-dashboard"
    echo "  Restart service: sudo systemctl restart challawa-dashboard"
    echo ""
else
    echo -e "${RED}✗ Service failed to start. Check logs:${NC}"
    journalctl -u challawa-dashboard -n 20
    exit 1
fi
