#!/usr/bin/env python3
"""
Phase 2: Data Cleaning, Standardization, and Supplier Enrichment
Loads cached GitHub data, runs cleaning pipeline, enriches supplier info, saves results
Works in both EC2 and Docker environments
"""
import sys
from pathlib import Path

# Determine project root (one level above 'utils')
project_root = Path(__file__).parent.parent

import pandas as pd
import sys
from pathlib import Path
import os
import importlib


# Import the data enhancement utilities
try:
    import data_enhancement_utils as deu
    importlib.reload(deu)  # Reload if module has changed
    print("✓ Successfully imported data_enhancement_utils")
except ImportError as e:
    print(f"Error importing data_enhancement_utils: {e}")
    print("Make sure data_enhancement_utils.py is in the utils directory")
    sys.exit(1)

# Debug: List all available functions in the module
print("Available functions in deu module:")
print([attr for attr in dir(deu) if not attr.startswith('_')])

def load_cached_data(data_dir: Path):
    """Load the cached datasets from Phase 1"""
    print("Loading cached datasets from Phase 1...")

    required_files = {
        'Warehouse_and_Retail_Sales.csv': 'Warehouse_and_Retail_Sales',
        'Distributors_Virginia_Three_Main.csv': 'Distributors_Virginia_Three_Main', 
        'wine_producers.csv': 'wine_producers',
        'winemag-data-130k-v2.csv': 'Wine_Review_Data',
        'Suppliers_Importers_Retailers.csv': 'Suppliers_Fixed'
    }

    datasets = {}
    for filename, dataset_name in required_files.items():
        file_path = data_dir / filename
        if not file_path.exists():
            print(f"Required file not found: {file_path}")
            print("Please run scripts/load_github_data.py first")
            return None

        try:
            df = pd.read_csv(file_path)
            datasets[dataset_name] = df
            print(f"Loaded {dataset_name}: {df.shape[0]:,} rows × {df.shape[1]} cols")
        except Exception as e:
            print(f"Error loading {filename}: {e}")
            return None

    return datasets

def run_phase2():
    """Run Phase 2: Cleaning + Supplier Enrichment"""
    
    print("\nPHASE 2: DATA CLEANING AND STANDARDIZATION")
    print("=" * 60)

    # Paths
    data_dir = project_root / 'data'
    processed_dir = data_dir / 'processed'
    processed_dir.mkdir(parents=True, exist_ok=True)

    # Load cached datasets
    datasets = load_cached_data(data_dir)
    if datasets is None:
        return None

    # Phase 2A: Cleaning
    sales_data = datasets['Warehouse_and_Retail_Sales']
    print(f"\nStarting with sales dataset: {sales_data.shape[0]:,} rows × {sales_data.shape[1]} cols")
    df_working = sales_data.copy()

    print("\nRunning data cleaning pipeline...")
    try:
        df_clean, cleaning_report = deu.run_complete_item_code_standardization(
            df_working, 
            item_types_to_keep=['WINE', 'BEER']
        )

        # Show cleaning results
        print(f"\nCLEANING RESULTS:")
        print(f"Original: {cleaning_report['original_shape']}")
        print(f"Cleaned:  {cleaning_report['final_shape']}")
        print(f"Retention: {cleaning_report['summary']['data_retention_pct']:.1f}%")

        # Save cleaned dataset
        cleaned_file = processed_dir / 'cleaned_sales_data.csv'
        df_clean.to_csv(cleaned_file, index=False)
        print(f"Cleaned dataset saved to: {cleaned_file}")

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
        print(f"Cleaning report saved to: {report_file}")

    except Exception as e:
        print(f"\nERROR during cleaning pipeline: {e}")
        return None

    # Phase 2B: Supplier Enrichment
    print("\nPHASE 2B: SUPPLIER ENRICHMENT")
    print("=" * 60)
    print("Enhancing sales data with supplier information...")

  # Paths
    data_dir = project_root / 'utils'
    processed_dir = data_dir / 'processed'
    processed_dir.mkdir(parents=True, exist_ok=True)

    try:
        df_enhanced = deu.run_supplier_enrichment(
            df_clean,
            datasets['Suppliers_Fixed'],
            test_mode=False
        )

        matched_suppliers = df_enhanced[
            (df_enhanced['SUPPLIER_MATCH_SCORE'] >= 0.8) &
            (df_enhanced['SUPPLIER_REPORT_TYPE'] == 'Wholesale Wine Distributors')
        ]

        print(f"\nWholesale Wine Distributors found:")
        print(matched_suppliers['SUPPLIER'].value_counts())

        print(f"\nSample matched data:")
        print(matched_suppliers[['SUPPLIER', 'MATCHED_SUPPLIER_NAME', 'SUPPLIER_MATCH_SCORE']].head(10))

        # Save enhanced dataset
        enhanced_file = processed_dir / 'enhanced_sales_data.csv'
        df_enhanced.to_csv(enhanced_file, index=False)
        print(f"\nEnhanced dataset saved to: {enhanced_file}")

    except Exception as e:
        print(f"\nERROR during supplier enrichment: {e}")
        return None

    print("\nPHASE 2 COMPLETE!")
    return df_clean, df_enhanced, datasets

def main():
    """Main execution function"""
    
    if Path('/.dockerenv').exists():
        print("Running in Docker environment")
    else:
        print("Running in EC2 environment")
    
    results = run_phase2()
    if results is None:
        print("\nPhase 2 failed - check error messages above")
        return 1

    df_clean, df_enhanced, datasets = results
    print("\nPhase 2 completed successfully!")
    print(f"- Cleaned dataset ready: {Path('data/processed/cleaned_sales_data.csv')}")
    print(f"- Enhanced dataset ready: {Path('data/processed/enhanced_sales_data.csv')}")
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
