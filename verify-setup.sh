#!/bin/bash
# Challenger SCADA Dashboard - IoT2050 Setup Verification
# Run this after setup to verify everything is working

echo "🔍 Verifying Challawa SCADA Dashboard Setup..."
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

checks_passed=0
checks_failed=0

# Function to run checks
check() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $1"
        ((checks_passed++))
    else
        echo -e "${RED}✗${NC} $1"
        ((checks_failed++))
    fi
}

# Check Python
echo "📦 Checking Python..."
python3 --version > /dev/null 2>&1
check "Python 3 installed"

# Check pip
pip3 --version > /dev/null 2>&1
check "pip3 installed"

# Check Flask
python3 -c "import flask" > /dev/null 2>&1
check "Flask installed"

# Check Flask-SocketIO
python3 -c "from flask_socketio import SocketIO" > /dev/null 2>&1
check "Flask-SocketIO installed"

# Check snap7
python3 -c "import snap7" > /dev/null 2>&1
check "python-snap7 installed"

# Check app.py exists
echo ""
echo "📁 Checking files..."
[ -f "app.py" ] && check "app.py found" || echo -e "${RED}✗${NC} app.py not found"

[ -d "templates" ] && check "templates folder found" || echo -e "${RED}✗${NC} templates folder not found"
[ -d "static" ] && check "static folder found" || echo -e "${RED}✗${NC} static folder not found"

# Check systemd service
echo ""
echo "⚙️  Checking system service..."
systemctl is-enabled challawa-dashboard > /dev/null 2>&1
check "Service enabled for auto-start"

systemctl is-active --quiet challawa-dashboard
check "Service is currently running"

# Check port
echo ""
echo "🔌 Checking network..."
netstat -tuln 2>/dev/null | grep -q ":5000" || ss -tuln 2>/dev/null | grep -q ":5000"
check "Port 5000 is listening"

# Get IP
IPADDY="$(hostname -I | awk '{print $1}')"
echo -e "   Access dashboard at: ${YELLOW}http://${IPADDY}:5000${NC}"

# Check PLC connectivity
echo ""
echo "🔗 Checking PLC connectivity..."
ping -c 1 192.168.200.20 > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓${NC} PLC is reachable (192.168.200.20)"
    ((checks_passed++))
else
    echo -e "${YELLOW}⚠${NC}  PLC not reachable (192.168.200.20) - will use simulated data"
fi

# Summary
echo ""
echo "================================"
if [ $checks_failed -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed!${NC}"
    echo "Dashboard is ready to use."
else
    echo -e "${RED}✗ Some checks failed${NC}"
    echo "Run: sudo systemctl status challawa-dashboard"
    echo "Or:  sudo journalctl -u challawa-dashboard -n 50"
fi
echo "================================"
echo ""
echo "📊 Dashboard URL: http://${IPADDY}:5000"
echo ""
echo "📋 Useful commands:"
echo "  Status:        sudo systemctl status challawa-dashboard"
echo "  View logs:     sudo journalctl -u challawa-dashboard -f"
echo "  Restart:       sudo systemctl restart challawa-dashboard"
echo "  Stop:          sudo systemctl stop challawa-dashboard"
echo ""
