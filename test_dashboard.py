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
