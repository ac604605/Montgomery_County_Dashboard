#!/bin/bash
# start_services.sh - Configure and start Wine Matching System services

set -e  # Exit on any error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[$(date +'%H:%M:%S')]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log "🚀 Starting Wine Matching System Services"
log "========================================"

# Get current directory (should be project root)
PROJECT_DIR=$(pwd)
log "Project directory: $PROJECT_DIR"

# Ensure we're in the right place
if [ ! -f "config.json" ]; then
    echo "❌ Error: config.json not found. Are you in the project directory?"
    exit 1
fi

# Activate virtual environment
if [ -d "wine_env" ]; then
    source wine_env/bin/activate
    log "Activated virtual environment"
else
    echo "❌ Error: wine_env not found. Run setup_ec2_wine_matcher.sh first"
    exit 1
fi

# Create systemd service file for wine matcher
log "Creating wine-matcher systemd service..."
sudo tee /etc/systemd/system/wine-matcher.service > /dev/null << EOF
[Unit]
Description=Wine Review Matching Service
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$PROJECT_DIR/wine_env/bin
ExecStart=$PROJECT_DIR/wine_env/bin/python scheduler.py
Restart=always
RestartSec=10
StandardOutput=append:$PROJECT_DIR/logs/scheduler.log
StandardError=append:$PROJECT_DIR/logs/scheduler_error.log

[Install]
WantedBy=multi-user.target
EOF

# Create systemd service file for Streamlit dashboard (optional)
log "Creating streamlit-dashboard systemd service..."
sudo tee /etc/systemd/system/streamlit-dashboard.service > /dev/null << EOF
[Unit]
Description=Wine Matching Streamlit Dashboard
After=network.target wine-matcher.service

[Service]
Type=simple
User=ec2-user
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$PROJECT_DIR/wine_env/bin
ExecStart=$PROJECT_DIR/wine_env/bin/streamlit run dashboard.py --server.port 8501 --server.address 0.0.0.0
Restart=always
RestartSec=10
StandardOutput=append:$PROJECT_DIR/logs/dashboard.log
StandardError=append:$PROJECT_DIR/logs/dashboard_error.log

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd to recognize new services
log "Reloading systemd daemon..."
sudo systemctl daemon-reload

# Enable services to start on boot
log "Enabling services to start on boot..."
sudo systemctl enable wine-matcher.service

# Check if dashboard.py exists before enabling dashboard service
if [ -f "dashboard.py" ]; then
    sudo systemctl enable streamlit-dashboard.service
    log "Enabled streamlit-dashboard service"
else
    warn "dashboard.py not found - skipping dashboard service"
fi

# Start the wine matcher service
log "Starting wine-matcher service..."
sudo systemctl start wine-matcher.service

# Start dashboard service if it exists
if [ -f "dashboard.py" ]; then
    log "Starting streamlit-dashboard service..."
    sudo systemctl start streamlit-dashboard.service
fi

# Create a simple monitoring script
log "Creating monitoring script..."
cat > monitor_services.sh << 'EOF'
#!/bin/bash
# Simple service monitoring script

echo "🍷 Wine Matching System - Service Status"
echo "========================================"

echo "Wine Matcher Service:"
sudo systemctl status wine-matcher.service --no-pager -l

echo ""
echo "Dashboard Service:"
if systemctl is-active --quiet streamlit-dashboard.service; then
    sudo systemctl status streamlit-dashboard.service --no-pager -l
else
    echo "Dashboard service not running or not available"
fi

echo ""
echo "Recent Logs (last 10 lines):"
echo "Scheduler:"
tail -n 10 logs/scheduler.log 2>/dev/null || echo "No scheduler logs yet"

echo ""
echo "System Resources:"
echo "Memory: $(free -h | grep Mem | awk '{print $3 "/" $2}')"
echo "Disk: $(df -h / | tail -1 | awk '{print $3 "/" $2 " (" $5 " used)"}')"
echo "CPU Load: $(uptime | awk '{print $10 $11 $12}')"

echo ""
echo "Service URLs:"
echo "Health Check: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8080/health"
echo "Dashboard: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8501"
EOF

chmod +x monitor_services.sh
log "Created monitor_services.sh"

# Wait a moment for services to start
sleep 3

# Check service status
log "Checking service status..."
if sudo systemctl is-active --quiet wine-matcher.service; then
    log "✅ wine-matcher service is running"
else
    warn "⚠️  wine-matcher service may not be running properly"
    info "Check status with: sudo systemctl status wine-matcher"
fi

if [ -f "dashboard.py" ] && sudo systemctl is-active --quiet streamlit-dashboard.service; then
    log "✅ streamlit-dashboard service is running"
else
    warn "⚠️  Dashboard service not running (this is okay if dashboard.py doesn't exist)"
fi

# Display helpful information
log ""
log "🎉 Service setup complete!"
log ""
log "Useful commands:"
log "  Monitor services:     ./monitor_services.sh"
log "  Check wine matcher:   sudo systemctl status wine-matcher"
log "  Check dashboard:      sudo systemctl status streamlit-dashboard"
log "  View logs:           tail -f logs/scheduler.log"
log "  Restart service:     sudo systemctl restart wine-matcher"
log ""

# Get EC2 public IP for URLs
PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4 2>/dev/null || echo "localhost")

log "Access your system:"
log "  Health Check: http://$PUBLIC_IP:8080/health"
if [ -f "dashboard.py" ]; then
    log "  Dashboard:    http://$PUBLIC_IP:8501"
fi
log ""

log "Services are now running in the background!"
log "Use './monitor_services.sh' to check status anytime."