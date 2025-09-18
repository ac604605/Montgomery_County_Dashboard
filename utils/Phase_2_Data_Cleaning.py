#!/usr/bin/env python3
"""
Phase 2: Data Cleaning and Standardization
Loads cached GitHub data, runs cleaning pipeline, saves cleaned result
Works in both EC2 and Docker environments
"""

import pandas as pd
import sys
from pathlib import Path
import os

# Add utils directory to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / 'utils'))
sys.path.append(str(project_root / 'data'))

# Import the data enhancement utilities
try:
    import data_enhancement_utils as deu
    print(" Successfully imported data_enhancement_utils")
except ImportError as e:
    print(f" Error importing data_enhancement_utils: {e}")
    print(f"Make sure data_enhancement_utils.py is in the utils directory")
    sys.exit(1)

def load_cached_data(data_dir: Path):
    """Load the cached datasets from Phase 1"""
    print("Loading cached datasets from Phase 1...")
    
    # Check if cached files exist
    required_files = {
        'Warehouse_and_Retail_Sales': 'Warehouse_and_Retail_Sales',  # Excel file
        'Distributors_Virginia_Three_Main': 'Distributors_Virginia_Three_Main', 
        'wine_producers': 'wine_producers',
        'winemag-data-130k-v2': 'Wine_Review_Data',
        'Suppliers_Importers_Retailers': 'Suppliers_Fixed'
    }
    
    datasets = {}
    
    for filename, dataset_name in required_files.items():
        file_path = data_dir / filename
        if not file_path.exists():
            print(f" Required file not found: {file_path}")
            print("Please run scripts/load_github_data.py first")
            return None
        
        try:
            df = pd.read_excel(file_path)
            datasets[dataset_name] = df
            print(f" Loaded {dataset_name}: {df.shape[0]:,} rows × {df.shape[1]} cols")
        except Exception as e:
            print(f" Error loading {filename}: {e}")
            return None
    
    return datasets

def run_phase2_cleaning():
    """Run Phase 2 data cleaning pipeline"""
    
    print(" PHASE 2: DATA CLEANING AND STANDARDIZATION")
    print("=" * 60)
    
    # Set up paths
    project_root = Path(__file__).parent.parent
    data_dir = project_root / 'data' / 'raw'
    processed_dir = project_root / 'data' / 'processed'
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Load cached datasets
    datasets = load_cached_data(data_dir)
    if datasets is None:
        return False
    
    # Get the sales data (main dataset for cleaning)
    sales_data = datasets['Warehouse_and_Retail_Sales']
    
    print(f"\n Starting with sales dataset:")
    print(f"Shape: {sales_data.shape}")
    print(f"Columns: {list(sales_data.columns)}")
    
    # Create working copy for processing
    print("\nCreating working copy of sales data...")
    df_working = sales_data.copy()
    print(f"Working dataset: {df_working.shape[0]:,} rows × {df_working.shape[1]} columns")
    
    # Run enhanced data cleaning utilities
    print("\nStarting data cleaning pipeline...")
    try:
        df_clean, cleaning_report = deu.run_complete_item_code_standardization(
            df_working, 
            item_types_to_keep=['WINE', 'BEER']
        )
        
        # Show cleaning results  
        print(f"\n CLEANING RESULTS:")
        print(f"   Original: {cleaning_report['original_shape']}")
        print(f"   Cleaned:  {cleaning_report['final_shape']}")
        print(f"   Retention: {cleaning_report['summary']['data_retention_pct']:.1f}%")
        
        # Save cleaned dataset
        output_file = processed_dir / 'cleaned_sales_data.csv'
        df_clean.to_csv(output_file, index=False)
        print(f"\n Cleaned dataset saved to: {output_file}")
        print(f"   File size: {output_file.stat().st_size / 1024**2:.1f} MB")
        
        # Save cleaning report
        report_file = processed_dir / 'cleaning_report.txt'
        with open(report_file, 'w') as f:
            f.write("DATA CLEANING REPORT\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Original shape: {cleaning_report['original_shape']}\n")
            f.write(f"Final shape: {cleaning_report['final_shape']}\n")
            f.write(f"Data retention: {cleaning_report['summary']['data_retention_pct']:.1f}%\n")
            f.write(f"Steps completed: {', '.join(cleaning_report['steps_completed'])}\n\n")
            
            f.write("Data Quality Improvements:\n")
            for improvement in cleaning_report.get('data_quality_improvements', []):
                f.write(f"- {improvement}\n")
        
        print(f" Cleaning report saved to: {report_file}")
        
        # Quick validation of cleaned data
        print(f"\n VALIDATION:")
        print(f" Final dataset shape: {df_clean.shape}")
        print(f" Item types: {df_clean['ITEM TYPE'].value_counts().to_dict()}")
        print(f" Missing suppliers: {df_clean['SUPPLIER'].isnull().sum()}")
        print(f" Numeric item codes: {pd.api.types.is_numeric_dtype(df_clean['ITEM CODE'])}")
        
        print(f"\n PHASE 2 COMPLETE!")
        print(f"Cleaned dataset ready for next steps at: {output_file}")
        
        return True
        
    except Exception as e:
        print(f"\n ERROR during cleaning pipeline: {e}")
        print(f"Check that your data has the expected columns:")
        print(f"Required: SUPPLIER, ITEM CODE, ITEM TYPE, ITEM DESCRIPTION")
        return False

def main():
    """Main execution function"""
    
    # Check environment
    if Path('/.dockerenv').exists():
        print("Running in Docker environment")
    else:
        print("Running in EC2 environment")
    
    success = run_phase2_cleaning()
    
    if success:
        print("\n Phase 2 completed successfully!")
        print("Next steps:")
        print("- Cleaned dataset is ready for further processing")
        print("- You can now add fuzzy matching, column additions, etc.")
        print("- Data is cached for future incremental updates")
    else:
        print("\n Phase 2 failed - check error messages above")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()