#!/bin/bash
# Minimal User Data - under 16KB limit
# Logs to /var/log/user-data.log

exec > >(tee /var/log/user-data.log) 2>&1

echo "Starting Wine Matcher setup at $(date)"

# Update system and install essentials
dnf update -y
dnf install -y git python3 python3-pip

# Setup project as ec2-user
USER_HOME="/home/ec2-user"
PROJECT_DIR="$USER_HOME/Montgomery_County_Dashboard"

# Clone repository
cd $USER_HOME
git clone https://github.com/ac604605/Montgomery_County_Dashboard.git

# Fix ownership
chown -R ec2-user:ec2-user $PROJECT_DIR

# Run main setup as ec2-user
cd $PROJECT_DIR
sudo -u ec2-user bash -c "
  chmod +x setup_ec2_wine_matcher.sh
  ./setup_ec2_wine_matcher.sh
"

echo "User Data complete at $(date). Check project at $PROJECT_DIR"