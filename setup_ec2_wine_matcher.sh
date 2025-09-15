#!/bin/bash
# setup_ec2_wine_matcher.sh - TEST MODE
# This version tests infrastructure without wine matching logic

set -e  # Exit on any error
set -o pipefail  # Exit on pipe failures

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log " Wine Matching System - TEST MODE Setup"
log "========================================"
info "This is a test run to validate infrastructure setup"

# Check if running as ec2-user
if [ "$USER" != "ec2-user" ]; then
    error "This script should be run as ec2-user, not $USER"
    exit 1
fi

# Get current directory
PROJECT_DIR=$(pwd)
log "Project directory: $PROJECT_DIR"

# Create logs directory
mkdir -p logs
log " Created logs directory"

# Setup Python virtual environment
log "Setting up Python virtual environment..."
if [ ! -d "wine_env" ]; then
    python3 -m venv wine_env
    log " Created virtual environment: wine_env"
else
    warn "Virtual environment already exists"
fi

# Activate virtual environment
source wine_env/bin/activate
log " Activated virtual environment"

# Check Python version
PYTHON_VERSION=$(python --version)
log "Using Python: $PYTHON_VERSION"

# Install basic packages first
log "Installing basic Python packages..."
pip install --upgrade pip
pip install pandas requests schedule psutil

# Create a minimal test requirements.txt
log "Creating test requirements.txt..."
cat > requirements_test.txt << 'EOF'
pandas==1.5.3
requests==2.28.2
schedule==1.2.0
psutil==5.9.5
streamlit==1.28.1
EOF

# Install test requirements
pip install -r requirements_test.txt
log " Test packages installed successfully"

# Create test config.json
log "Creating test config.json..."
cat > config_test.json << 'EOF'
{
  "api": {
    "base_url": "https://data.montgomerycountymd.gov/resource/v76h-r7br.json",
    "app_token": "",
    "chunk_size": 100,
    "rate_limit_delay": 1.0
  },
  "processing": {
    "matching_threshold": 0.6,
    "enable_parallel": false,
    "max_workers": 1,
    "cache_enabled": true,
    "database_path": "/home/ec2-user/Montgomery_County_Dashboard/test_wine_data.db"
  },
  "test_mode": {
    "enabled": true,
    "max_records": 100,
    "mock_data": true
  }
}
EOF
log " Created test config.json"

# Create a comprehensive test script
log "Creating infrastructure test script..."
cat > test_infrastructure.py << 'EOF'
#!/usr/bin/env python3
"""
Infrastructure Test Script - Validates setup without wine matching logic
"""
import sys
import json
import sqlite3
import requests
import os
import time
from datetime import datetime

def test_python_environment():
    """Test Python packages and environment"""
    print(" Testing Python Environment...")
    try:
        import pandas as pd
        import requests
        import schedule
        import psutil
        
        print(f"   Python version: {sys.version.split()[0]}")
        print(f"   Pandas: {pd.__version__}")
        print(f"   Requests: {requests.__version__}")
        print(f"   Schedule available")
        print(f"   Psutil: {psutil.__version__}")
        return True
    except ImportError as e:
        print(f"   Import failed: {e}")
        return False

def test_system_resources():
    """Test system resources"""
    print(" Testing System Resources...")
    try:
        import psutil
        
        # Memory
        memory = psutil.virtual_memory()
        print(f"   Memory: {memory.total / (1024**3):.1f} GB total, {memory.available / (1024**3):.1f} GB available")
        
        # CPU
        cpu_count = psutil.cpu_count()
        cpu_percent = psutil.cpu_percent(interval=1)
        print(f"   CPU: {cpu_count} cores, {cpu_percent}% usage")
        
        # Disk
        disk = psutil.disk_usage('/')
        print(f"   Disk: {disk.total / (1024**3):.1f} GB total, {disk.free / (1024**3):.1f} GB free")
        
        return True
    except Exception as e:
        print(f"   System test failed: {e}")
        return False

def test_config_loading():
    """Test configuration loading"""
    print("️  Testing Configuration...")
    try:
        with open('config_test.json', 'r') as f:
            config = json.load(f)
        
        print(f"   Config loaded successfully")
        print(f"   API endpoint: {config['api']['base_url']}")
        print(f"   Test mode: {config.get('test_mode', {}).get('enabled', False)}")
        return True
    except Exception as e:
        print(f"   Config test failed: {e}")
        return False

def test_database():
    """Test database functionality"""
    print("️  Testing Database...")
    try:
        # Create test database
        conn = sqlite3.connect('test_database.db')
        
        # Create test table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS test_wines (
                id INTEGER PRIMARY KEY,
                name TEXT,
                type TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insert test data
        test_data = [
            ('Test Wine 1', 'RED'),
            ('Test Wine 2', 'WHITE'),
            ('Test Wine 3', 'SPARKLING')
        ]
        
        conn.executemany(
            "INSERT INTO test_wines (name, type) VALUES (?, ?)",
            test_data
        )
        conn.commit()
        
        # Query test data
        cursor = conn.execute("SELECT COUNT(*) FROM test_wines")
        count = cursor.fetchone()[0]
        
        conn.close()
        
        # Clean up
        os.remove('test_database.db')
        
        print(f"   Database operations successful ({count} test records)")
        return True
    except Exception as e:
        print(f"   Database test failed: {e}")
        return False

def test_api_connectivity():
    """Test API connectivity"""
    print(" Testing API Connectivity...")
    try:
        # Test with minimal request
        response = requests.get(
            'https://data.montgomerycountymd.gov/resource/v76h-r7br.json',
            params={'$limit': 1},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"   API accessible (status: {response.status_code})")
            print(f"   Received {len(data)} sample record(s)")
            
            # Show sample data structure
            if data:
                sample = data[0]
                print(f"   Sample fields: {list(sample.keys())[:5]}...")
            
            return True
        else:
            print(f"   API returned status: {response.status_code}")
            return False
            
    except requests.RequestException as e:
        print(f"   API test failed: {e}")
        return False

def test_file_permissions():
    """Test file permissions and directory access"""
    print(" Testing File Permissions...")
    try:
        # Test write permissions
        test_file = 'permission_test.txt'
        with open(test_file, 'w') as f:
            f.write("Permission test")
        
        # Test read permissions
        with open(test_file, 'r') as f:
            content = f.read()
        
        # Clean up
        os.remove(test_file)
        
        print(f"   File read/write permissions working")
        
        # Test directory creation
        test_dir = 'test_directory'
        os.makedirs(test_dir, exist_ok=True)
        os.rmdir(test_dir)
        
        print(f"   Directory creation permissions working")
        return True
        
    except Exception as e:
        print(f"   Permission test failed: {e}")
        return False

def main():
    """Run all infrastructure tests"""
    print(" Infrastructure Test Suite")
    print("=" * 50)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    tests = [
        ("Python Environment", test_python_environment),
        ("System Resources", test_system_resources),
        ("Configuration", test_config_loading),
        ("Database", test_database),
        ("API Connectivity", test_api_connectivity),
        ("File Permissions", test_file_permissions)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"   {test_name} failed with exception: {e}")
            failed += 1
        print()
    
    print("=" * 50)
    print(f" Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print(" All infrastructure tests passed!")
        print(" System ready for wine matching application code")
        return 0
    else:
        print("️  Some tests failed - check the output above")
        return 1

if __name__ == "__main__":
    sys.exit(main())
EOF

chmod +x test_infrastructure.py
log " Created infrastructure test script"

# Create a mock scheduler for testing
log "Creating test scheduler..."
cat > test_scheduler.py << 'EOF'
#!/usr/bin/env python3
"""
Test Scheduler - Validates scheduling without wine matching
"""
import schedule
import time
import json
import subprocess
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/test_scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def run_infrastructure_test():
    """Run infrastructure test periodically"""
    logger.info("Running scheduled infrastructure test...")
    try:
        result = subprocess.run([
            'python', 'test_infrastructure.py'
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            logger.info(" Infrastructure test passed")
        else:
            logger.error(f" Infrastructure test failed: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        logger.error("Test timed out")
    except Exception as e:
        logger.error(f"Test error: {e}")

def log_system_status():
    """Log basic system status"""
    logger.info("System status check...")
    try:
        import psutil
        
        memory = psutil.virtual_memory()
        cpu = psutil.cpu_percent(interval=1)
        
        logger.info(f"Memory usage: {memory.percent}%")
        logger.info(f"CPU usage: {cpu}%")
        
    except Exception as e:
        logger.error(f"Status check failed: {e}")

def main():
    logger.info(" Test Scheduler Started")
    logger.info("Running in test mode - no wine matching")
    
    # Schedule tests
    schedule.every(10).minutes.do(run_infrastructure_test)
    schedule.every(5).minutes.do(log_system_status)
    
    # Run initial test
    run_infrastructure_test()
    
    logger.info("Scheduler running - will test every 10 minutes")
    
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main()
EOF

chmod +x test_scheduler.py
log " Created test scheduler"

# Create simple test dashboard
log "Creating test dashboard..."
cat > test_dashboard.py << 'EOF'
#!/usr/bin/env python3
"""
Test Dashboard - Simple Streamlit app to verify dashboard functionality
"""
import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime

st.title(" Wine Matching System - Test Dashboard")
st.write("Infrastructure validation dashboard")

# System Info
st.header("System Information")
col1, col2 = st.columns(2)

with col1:
    st.metric("Status", " Online")
    st.metric("Mode", " Test")

with col2:
    st.metric("Project Dir", os.getcwd().split('/')[-1])
    st.metric("Time", datetime.now().strftime("%H:%M:%S"))

# Config Display
st.header("Configuration")
try:
    with open('config_test.json', 'r') as f:
        config = json.load(f)
    st.json(config)
except FileNotFoundError:
    st.error("Config file not found")

# Test Data
st.header("Test Data")
test_data = pd.DataFrame({
    'Wine Name': ['Test Wine 1', 'Test Wine 2', 'Test Wine 3'],
    'Type': ['Red', 'White', 'Sparkling'],
    'Status': [' Ready', ' Ready', ' Ready']
})
st.dataframe(test_data)

# Logs
st.header("Recent Logs")
try:
    with open('logs/test_scheduler.log', 'r') as f:
        logs = f.readlines()[-10:]  # Last 10 lines
    st.text('\n'.join(logs))
except FileNotFoundError:
    st.info("No logs yet - run the scheduler first")

st.success("Dashboard is working! Ready for real wine matching code.")
EOF

log " Created test dashboard"

# Run infrastructure test
log "Running infrastructure validation test..."
python test_infrastructure.py
TEST_RESULT=$?

if [ $TEST_RESULT -eq 0 ]; then
    log " Infrastructure test passed!"
else
    warn "️  Some infrastructure tests failed, but continuing..."
fi

# Setup memory optimization for t2.micro
MEMORY_GB=$(free -g | awk '/^Mem:/{print $2}')
if [ "$MEMORY_GB" -le 1 ]; then
    log "Detected low memory (${MEMORY_GB}GB) - setting up swap..."
    if [ ! -f /swapfile ]; then
        sudo dd if=/dev/zero of=/swapfile bs=128M count=8
        sudo chmod 600 /swapfile
        sudo mkswap /swapfile
        sudo swapon /swapfile
        echo '/swapfile swap swap defaults 0 0' | sudo tee -a /etc/fstab
        log " 1GB swap file created"
    fi
fi

# Create test version of start_services.sh
log "Creating test start_services script..."
cat > start_test_services.sh << 'EOF'
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
EOF

chmod +x start_test_services.sh

# Final completion message
log ""
log " TEST MODE setup completed successfully!"
log ""
log "What was tested:"
log "   Python virtual environment"
log "   Package installation"
log "   Database functionality"
log "   API connectivity"
log "   File permissions"
log "   System resources"
log ""
log "Next steps:"
log "  1. Start test services: ./start_test_services.sh"
log "  2. Check service: sudo systemctl status wine-matcher-test"
log "  3. Test dashboard: streamlit run test_dashboard.py --server.port 8501 --server.address 0.0.0.0"
log "  4. Monitor logs: tail -f logs/test_scheduler.log"
log ""
log "Once infrastructure is validated, replace with real wine matching code!"
log " Infrastructure ready for wine matching application!"