#!/bin/bash
# Test version of start_services.sh

echo " Starting Test Services..."

PROJECT_DIR=$(pwd)

# Create systemd service for test scheduler
sudo tee /etc/systemd/system/wine-matcher-test.service > /dev/null << SVCEOF
[Unit]
Description=Wine Matcher Test Service
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$PROJECT_DIR/wine_env/bin
ExecStart=$PROJECT_DIR/wine_env/bin/python test_scheduler.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SVCEOF

# Reload and enable
sudo systemctl daemon-reload
sudo systemctl enable wine-matcher-test.service
sudo systemctl start wine-matcher-test.service

echo " Test services started!"
echo "Check status: sudo systemctl status wine-matcher-test"
echo "Test dashboard: streamlit run test_dashboard.py --server.port 8501 --server.address 0.0.0.0"
