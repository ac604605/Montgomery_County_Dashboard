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
