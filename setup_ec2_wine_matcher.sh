#!/bin/bash
# setup_ec2_wine_matcher.sh - Initial setup for Montgomery County Pipeline
# Gets you to the GitHub data loading checkpoint

set -e

echo " Montgomery County Wine Matcher - Initial Setup"
echo "================================================="

# Detect environment
if [ -f /.dockerenv ]; then
    ENVIRONMENT="docker"
    USER_HOME="/app"
    echo " Docker container environment detected"
else
    ENVIRONMENT="ec2"
    USER_HOME="/home/ec2-user"
    echo "️  EC2 native environment detected"
fi

PROJECT_DIR="$USER_HOME/montgomery_wine_pipeline"

# EC2-specific setup
setup_ec2() {
    echo " Setting up EC2 environment..."
    
    # Update system
    echo "Updating system packages..."
    sudo dnf update -y
    
    # Install Python 3.11 and development tools
    echo "Installing Python 3.11 and tools..."
    sudo dnf install -y python3.11 python3.11-pip python3.11-venv git htop sqlite wget curl
    
    # Create project directory
    echo "Creating project directory: $PROJECT_DIR"
    mkdir -p $PROJECT_DIR
    cd $PROJECT_DIR
    
    # Create virtual environment
    echo "Creating Python virtual environment..."
    python3.11 -m venv venv
    source venv/bin/activate
    
    # Install required packages for initial data loading
    echo "Installing Python packages..."
    pip install --upgrade pip
    pip install pandas requests psutil numpy
    
    echo " EC2 environment ready"
}

# Docker-specific setup (simplified for now)
setup_docker() {
    echo " Setting up Docker environment..."
    cd $PROJECT_DIR
    pip install pandas requests psutil numpy
    echo " Docker environment ready"
}

# Create basic project structure
create_project_structure() {
    echo " Creating project structure..."
    mkdir -p {data/{raw,processed,logs},scripts,src}
    
    # Create the initial data loader script
    cat > scripts/load_github_data.py << 'EOF'
#!/usr/bin/env python3
"""
Initial GitHub Data Loader - Phase 1
Gets you to the checkpoint with all datasets loaded and summarized
"""

import pandas as pd
import requests
import os
from pathlib import Path
import gc

def main():
    # GitHub raw URL
    base_url = "https://raw.githubusercontent.com/ac604605/Montgomery_County_Dashboard/main/"
    
    print("Loading datasets from GitHub repository...")
    print("=" * 60)
    
    try:
        # Load standard datasets
        print("Loading standard datasets...")
        Distributors_Virginia_Three_Main = pd.read_csv(base_url + "data/Distributors_Virginia_Three_Main.csv")
        wine_producers = pd.read_csv(base_url + "data/wine_producers.csv")
        Warehouse_and_Retail_Sales = pd.read_csv(base_url + "data/Warehouse_and_Retail_Sales.csv")
        Wine_Review_Data = pd.read_csv(base_url + "data/winemag-data-130k-v2.csv/winemag-data-130k-v2.csv")
        
        # Load suppliers with data quality fix
        print("Loading and fixing supplier data structure...")
        correct_columns = ['License_ID', 'Trade Name', 'Address', 'City', 'State', 'Zip_Code', 'Report_Type']
        Suppliers_Fixed = pd.read_csv(
            base_url + "data/Suppliers_Importers_Retailers.csv",
            header=0,
            names=correct_columns,
            usecols=range(7),
            dtype={'License_ID': str, 'Zip_Code': str}
        )
        
        # Professional summaries
        datasets = [
            (Distributors_Virginia_Three_Main, "Virginia Distributors"),
            (wine_producers, "Wine Producers"),
            (Warehouse_and_Retail_Sales, "Sales Transactions"),
            (Wine_Review_Data, "Wine Reviews"),
            (Suppliers_Fixed, "Supplier Directory (Fixed)")
        ]
        
        for df, name in datasets:
            memory_mb = df.memory_usage(deep=True).sum() / 1024**2
            print(f"{name:<25} │ {df.shape[0]:>8,} rows × {df.shape[1]:>2} cols │ {memory_mb:>6.1f} MB")
        
        # Quick validation for suppliers
        report_types = Suppliers_Fixed['Report_Type'].nunique()
        print(f"Supplier validation: {report_types} unique report types identified")
        
        print("=" * 60)
        print(f"Successfully loaded {len(datasets)} datasets with data quality fixes applied")
        
        # Cache the datasets for next steps
        data_dir = Path("data/raw")
        data_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"\nCaching datasets to {data_dir}...")
        Distributors_Virginia_Three_Main.to_csv(data_dir / "distributors.csv", index=False)
        wine_producers.to_csv(data_dir / "wine_producers.csv", index=False) 
        Warehouse_and_Retail_Sales.to_csv(data_dir / "sales_transactions.csv", index=False)
        Wine_Review_Data.to_csv(data_dir / "wine_reviews.csv", index=False)
        Suppliers_Fixed.to_csv(data_dir / "suppliers_fixed.csv", index=False)
        
        print(" All datasets cached locally")
        print()
        print(" CHECKPOINT REACHED!")
        print("Now with everything loaded, you can begin data cleaning and refinement.")
        print("After investigating the sales data, there are a few cleaning steps that need to take place:")
        print("- First will be removing all values that are not wine and beer items")
        print("- Second will be ensuring item codes are numeric for easier processing") 
        print("- Finally, some individual values will be changed and anything that isn't wine or beer will be removed")
        print("- Also removing keg versions of wines and beer for simpler scope")
        
        # Return datasets for potential immediate use
        return {
            'distributors': Distributors_Virginia_Three_Main,
            'producers': wine_producers,
            'sales': Warehouse_and_Retail_Sales,
            'reviews': Wine_Review_Data,
            'suppliers': Suppliers_Fixed
        }
        
    except Exception as e:
        print(f" Error loading data: {e}")
        raise

if __name__ == "__main__":
    datasets = main()
EOF

    chmod +x scripts/load_github_data.py
}

# Test git accessibility
test_git_access() {
    echo " Testing GitHub repository access..."
    
    # Test direct access to one of your files
    test_url="https://raw.githubusercontent.com/ac604605/Montgomery_County_Dashboard/main/data/wine_producers.csv"
    
    if command -v curl &> /dev/null; then
        echo "Testing access to: $test_url"
        if curl -s --head "$test_url" | head -n 1 | grep -q "200 OK"; then
            echo " GitHub repository is accessible"
            # Show first few lines to verify content
            echo "Sample data preview:"
            curl -s "$test_url" | head -3
        else
            echo " Cannot access GitHub repository"
            exit 1
        fi
    else
        echo "️  curl not available, skipping connectivity test"
    fi
}

# Create simple health check
create_health_check() {
    cat > scripts/health_check.py << 'EOF'
#!/usr/bin/env python3
"""Simple health check for the pipeline environment"""

import sys
import os
from pathlib import Path

def check_environment():
    print(" Environment Health Check")
    print("=" * 30)
    
    # Check Python version
    print(f"Python version: {sys.version}")
    
    # Check required packages
    required_packages = ['pandas', 'requests', 'numpy']
    for package in required_packages:
        try:
            __import__(package)
            print(f" {package} available")
        except ImportError:
            print(f" {package} missing")
            return False
    
    # Check directory structure
    expected_dirs = ['data/raw', 'data/processed', 'data/logs', 'scripts']
    for dir_path in expected_dirs:
        if Path(dir_path).exists():
            print(f" {dir_path} exists")
        else:
            print(f"️  {dir_path} missing (will be created)")
    
    print("=" * 30)
    print(" Environment check complete")
    return True

if __name__ == "__main__":
    healthy = check_environment()
    sys.exit(0 if healthy else 1)
EOF

    chmod +x scripts/health_check.py
}

# Main setup function
main() {
    echo "Starting setup for environment: $ENVIRONMENT"
    
    # Environment-specific setup
    if [ "$ENVIRONMENT" = "ec2" ]; then
        setup_ec2
    else
        setup_docker
    fi
    
    # Common setup
    create_project_structure
    create_health_check
    test_git_access
    
    # Set proper permissions
    if [ "$ENVIRONMENT" = "ec2" ]; then
        chown -R ec2-user:ec2-user $PROJECT_DIR
        chmod -R 755 $PROJECT_DIR
    fi
    
    echo ""
    echo " SETUP COMPLETE!"
    echo "=================="
    echo ""
    echo "Ready to run checkpoint test:"
    if [ "$ENVIRONMENT" = "ec2" ]; then
        echo "  cd $PROJECT_DIR"
        echo "  source venv/bin/activate"
    fi
    echo "  python scripts/health_check.py"
    echo "  python scripts/load_github_data.py"
    echo ""

}

# Run setup
main "$@"