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
