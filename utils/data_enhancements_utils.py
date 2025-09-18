#!/usr/bin/env python3
"""
Data Enhancement Utilities (deu)
Standalone module for Montgomery County data cleaning pipeline
Works in both EC2 and Docker environments
"""
import sys
from pathlib import Path

# Determine project root (one level above 'utils')
project_root = Path(__file__).parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / 'data'))

import pandas as pd
import numpy as np
from typing import Optional, Dict, List, Union, Tuple, Any
import warnings


# ===============================
# DATA CLEANING UTILITIES WITH PROGRESS TRACKING
# ===============================

def clean_missing_supplier_data(df: pd.DataFrame, 
                               supplier_col: str = 'SUPPLIER',
                               verbose: bool = True) -> pd.DataFrame:
    """
    Remove rows with missing supplier data with detailed progress tracking.
    
    Args:
        df (pd.DataFrame): DataFrame to clean
        supplier_col (str): Name of supplier column (default: 'SUPPLIER')
        verbose (bool): Whether to show progress (default: True)
    
    Returns:
        pd.DataFrame: Cleaned DataFrame copy with missing suppliers removed
    """
    if verbose:
        print("="*60)
        print("STEP 1: REMOVING MISSING SUPPLIER DATA")
        print("="*60)
    
    # Store original info
    original_shape = df.shape
    
    if supplier_col not in df.columns:
        if verbose:
            print(f"Error: Column '{supplier_col}' not found in DataFrame")
            print(f"Available columns: {list(df.columns)}")
        return df.copy()
    
    original_nulls = df[supplier_col].isnull().sum()
    
    if verbose:
        print(f"Original dataset shape: {original_shape}")
        print(f"Rows with missing {supplier_col}: {original_nulls:,}")
        if len(df) > 0:
            print(f"Missing {supplier_col} percentage: {(original_nulls/len(df)*100):.2f}%")
    
    # Create clean copy and remove missing suppliers
    df_clean = df.copy()
    df_clean = df_clean.dropna(subset=[supplier_col])
    
    # Calculate results
    rows_removed = original_shape[0] - df_clean.shape[0]
    
    if verbose:
        print(f"\n✓ Cleaning complete!")
        print(f"New dataset shape: {df_clean.shape}")
        print(f"✓ Rows removed: {rows_removed:,}")
        print(f"✓ Null {supplier_col} remaining: {df_clean[supplier_col].isnull().sum()}")
        
        if rows_removed > 0:
            print(f"Data reduction: {(rows_removed/original_shape[0]*100):.2f}%")
    
    return df_clean


def analyze_non_numeric_item_codes(df: pd.DataFrame, 
                                 item_code_col: str = 'ITEM CODE',
                                 max_examples: int = 10,
                                 verbose: bool = True) -> Dict[str, Any]:
    """
    Analyze non-numeric patterns in item codes with detailed reporting.
    
    Args:
        df (pd.DataFrame): DataFrame to analyze
        item_code_col (str): Name of item code column (default: 'ITEM CODE')
        max_examples (int): Maximum examples to show (default: 10)
        verbose (bool): Whether to show progress (default: True)
    
    Returns:
        dict: Analysis results including patterns found and recommendations
    """
    if verbose:
        print("="*60)
        print("STEP 2: ANALYZING NON-NUMERIC ITEM CODE PATTERNS")
        print("="*60)
    
    if item_code_col not in df.columns:
        if verbose:
            print(f"Error: Column '{item_code_col}' not found in DataFrame")
        return {'error': f"Column '{item_code_col}' not found"}
    
    # Convert to string to ensure consistent analysis
    item_codes = df[item_code_col].astype(str)
    
    # Find non-numeric codes
    non_numeric = df[~item_codes.str.isdigit()].copy()
    
    results = {
        'total_items': len(df),
        'non_numeric_count': len(non_numeric),
        'non_numeric_percentage': (len(non_numeric) / len(df) * 100) if len(df) > 0 else 0,
        'patterns': {},
        'recommendations': []
    }
    
    if verbose:
        print(f"Total items analyzed: {len(df):,}")
        print(f"Non-numeric item codes found: {len(non_numeric):,}")
        print(f"Non-numeric percentage: {results['non_numeric_percentage']:.2f}%")
    
    if len(non_numeric) > 0:
        if verbose:
            print(f"\n⚙ Analyzing patterns in non-numeric codes...")
        
        # Extract patterns using regex
        try:
            patterns = non_numeric[item_code_col].astype(str).str.extract(r'(\d+)([A-Za-z]+)')
            if not patterns.empty and patterns.shape[1] >= 2:
                # Count suffixes
                suffixes = patterns[1].value_counts()
                results['patterns']['suffixes'] = suffixes.to_dict()
                
                if verbose:
                    print(f"Pattern analysis:")
                    print(f"Most common format: [numbers][letters]")
                    print(f"Suffixes found:")
                    for suffix, count in suffixes.head(5).items():
                        print(f"  '{suffix}': {count} occurrences")
                
                # Show examples
                if verbose and len(non_numeric) > 0:
                    print(f"\nSample non-numeric codes (showing up to {max_examples}):")
                    sample = non_numeric.head(max_examples)
                    for idx, row in sample.iterrows():
                        if 'ITEM DESCRIPTION' in df.columns:
                            print(f"{row[item_code_col]} - {row['ITEM DESCRIPTION'][:50]}...")
                        else:
                            print(f"{row[item_code_col]}")
        
        except Exception as e:
            if verbose:
                print(f"⚠ Could not analyze patterns: {str(e)}")
            results['pattern_error'] = str(e)
        
        # Generate recommendations
        if 'A' in results.get('patterns', {}).get('suffixes', {}):
            results['recommendations'].append("Consider consolidating 'A' suffix items with base versions")
        
        if len(non_numeric) < len(df) * 0.1:  # Less than 10%
            results['recommendations'].append("Small number of non-numeric codes - investigate individually")
        else:
            results['recommendations'].append("High number of non-numeric codes - systematic review needed")
    
    else:
        if verbose:
            print("✓ All item codes are numeric - no patterns to analyze")
        results['recommendations'].append("All codes are numeric - ready for type conversion")
    
    if verbose and results['recommendations']:
        print(f"\n📋 Recommendations:")
        for i, rec in enumerate(results['recommendations'], 1):
            print(f"{i}. {rec}")
    
    return results


def standardize_item_codes_with_suffix(df: pd.DataFrame, 
                                     item_code_col: str = 'ITEM CODE',
                                     description_col: str = 'ITEM DESCRIPTION',
                                     suffix: str = 'A',
                                     columns_to_standardize: List[str] = None,
                                     verbose: bool = True) -> pd.DataFrame:
    """
    Consolidate items with suffix (like 'A') with their base versions.
    FIXED VERSION - addresses the logic issue from your original code.
    
    Args:
        df (pd.DataFrame): DataFrame to standardize
        item_code_col (str): Name of item code column (default: 'ITEM CODE')
        description_col (str): Name of description column (default: 'ITEM DESCRIPTION')
        suffix (str): Suffix to consolidate (default: 'A')
        columns_to_standardize (list): Columns to standardize (default: auto-detect)
        verbose (bool): Whether to show progress (default: True)
    
    Returns:
        pd.DataFrame: Cleaned DataFrame copy with standardized item codes
    """
    if verbose:
        print("="*60)
        print(f"STEP 3: STANDARDIZING ITEM CODES ('{suffix}' SUFFIX CONSOLIDATION)")
        print("="*60)
    
    # Create clean copy
    df_clean = df.copy()
    
    if item_code_col not in df_clean.columns:
        if verbose:
            print(f"Error: Column '{item_code_col}' not found in DataFrame")
        return df_clean
    
    # Auto-detect columns to standardize if not provided
    if columns_to_standardize is None:
        potential_cols = ['SUPPLIER', 'ITEM DESCRIPTION', 'ITEM TYPE', 'CATEGORY']
        columns_to_standardize = [col for col in potential_cols if col in df_clean.columns]
    
    # Find items with suffix
    suffix_mask = df_clean[item_code_col].astype(str).str.endswith(suffix)
    suffix_items = df_clean[suffix_mask].copy()
    
    if len(suffix_items) == 0:
        if verbose:
            print(f"No items found with '{suffix}' suffix - nothing to standardize")
        return df_clean
    
    # Create base codes
    suffix_items['BASE_CODE'] = suffix_items[item_code_col].astype(str).str[:-len(suffix)]
    
    if verbose:
        print(f"Found {len(suffix_items)} items with '{suffix}' suffix")
    
    # Check which have corresponding base versions
    base_codes_exist = suffix_items['BASE_CODE'].isin(df_clean[item_code_col].astype(str))
    consolidatable = suffix_items[base_codes_exist].copy()
    
    if len(consolidatable) == 0:
        if verbose:
            print(f"⚠ No base versions found for '{suffix}' suffix items")
        return df_clean
    
    if verbose:
        print(f"Can consolidate {len(consolidatable)} items (have matching base codes)")
        print(f"Standardizing columns: {columns_to_standardize}")
    
    # FIXED CONSOLIDATION LOGIC
    standardized_count = 0
    for idx, row in consolidatable.iterrows():
        base_code = row['BASE_CODE']
        
        try:
            # Find the base version
            base_mask = df_clean[item_code_col].astype(str) == base_code
            if not base_mask.any():
                continue
                
            base_row = df_clean[base_mask].iloc[0]
            
            # Get the current suffix item's index (BEFORE changing anything)
            suffix_item_idx = df_clean.index[df_clean.index == idx]
            
            if len(suffix_item_idx) > 0:
                # Update all columns at once using the stored index
                update_dict = {item_code_col: base_row[item_code_col]}
                for col in columns_to_standardize:
                    if col in df_clean.columns and col in base_row.index:
                        update_dict[col] = base_row[col]
                
                # Apply all updates at once
                for col, value in update_dict.items():
                    df_clean.loc[suffix_item_idx, col] = value
                
                standardized_count += 1
                
        except Exception as e:
            if verbose:
                print(f"⚠ Error processing {row[item_code_col]}: {str(e)}")
            continue
    
    if verbose:
        print(f"✓ Successfully standardized {standardized_count} items")
        
        # Verification
        if standardized_count > 0:
            sample_base = consolidatable['BASE_CODE'].iloc[0]
            consolidated_items = df_clean[df_clean[item_code_col].astype(str) == sample_base]
            print(f"Verification - Items with code {sample_base}: {len(consolidated_items)}")
            if len(consolidated_items) > 1:
                print(f"✓ Successfully created duplicates for consolidation")
    
    return df_clean


def convert_item_codes_to_numeric(df: pd.DataFrame,
                                item_code_col: str = 'ITEM CODE',
                                verbose: bool = True) -> pd.DataFrame:
    """
    Convert item codes to numeric type with validation and progress tracking.
    
    Args:
        df (pd.DataFrame): DataFrame to convert
        item_code_col (str): Name of item code column (default: 'ITEM CODE')
        verbose (bool): Whether to show progress (default: True)
    
    Returns:
        pd.DataFrame: DataFrame copy with numeric item codes
    """
    if verbose:
        print("="*60)
        print("STEP 4: CONVERTING ITEM CODES TO NUMERIC TYPE")
        print("="*60)
    
    # Create clean copy
    df_clean = df.copy()
    
    if item_code_col not in df_clean.columns:
        if verbose:
            print(f"Error: Column '{item_code_col}' not found in DataFrame")
        return df_clean
    
    # Check current state
    current_dtype = df_clean[item_code_col].dtype
    
    if verbose:
        print(f"Current {item_code_col} dtype: {current_dtype}")
        print(f"Sample values: {df_clean[item_code_col].head().tolist()}")
    
    # Check for non-numeric values before conversion
    if current_dtype == 'object':
        non_numeric = df_clean[~df_clean[item_code_col].astype(str).str.isdigit()]
        if len(non_numeric) > 0:
            if verbose:
                print(f"⚠ Warning: {len(non_numeric)} non-numeric values found")
                print(f"These will become NaN during conversion")
                print(f"Sample: {non_numeric[item_code_col].head().tolist()}")
    
    try:
        # Convert to numeric
        df_clean[item_code_col] = pd.to_numeric(df_clean[item_code_col], errors='coerce')
        
        # Check results
        new_dtype = df_clean[item_code_col].dtype
        nan_count = df_clean[item_code_col].isnull().sum()
        
        if verbose:
            print(f"\n✓ Conversion complete!")
            print(f"New {item_code_col} dtype: {new_dtype}")
            print(f"Sample numeric codes: {df_clean[item_code_col].head().tolist()}")
            print(f"NaN values created: {nan_count}")
            
            if nan_count == 0:
                print(f"✓ Perfect conversion - all values are now numeric!")
            else:
                print(f"⚠ {nan_count} values could not be converted to numeric")
        
        return df_clean
        
    except Exception as e:
        if verbose:
            print(f"Error during conversion: {str(e)}")
        return df_clean


def filter_item_types(df: pd.DataFrame,
                     item_types_to_keep: List[str],
                     item_type_col: str = 'ITEM TYPE',
                     verbose: bool = True) -> pd.DataFrame:
    """
    Filter dataset to keep only specified item types with detailed reporting.
    
    Args:
        df (pd.DataFrame): DataFrame to filter
        item_types_to_keep (list): List of item types to keep (e.g., ['WINE', 'BEER'])
        item_type_col (str): Name of item type column (default: 'ITEM TYPE')
        verbose (bool): Whether to show progress (default: True)
    
    Returns:
        pd.DataFrame: Filtered DataFrame copy
    """
    if verbose:
        print("="*60)
        print("STEP 5: FILTERING TO BUSINESS-RELEVANT ITEM TYPES")
        print("="*60)
    
    # Create clean copy
    df_clean = df.copy()
    
    if item_type_col not in df_clean.columns:
        if verbose:
            print(f"Error: Column '{item_type_col}' not found in DataFrame")
        return df_clean
    
    # Show current distribution
    if verbose:
        print(f"Current item type distribution:")
        current_counts = df_clean[item_type_col].value_counts()
        for item_type, count in current_counts.items():
            status = "✓ KEEPING" if item_type in item_types_to_keep else "✗ REMOVING"
            print(f"{item_type}: {count:,} ({status})")
        
        print(f"\n⚙ Filtering to keep: {item_types_to_keep}")
    
    # Filter the data
    original_count = len(df_clean)
    df_clean = df_clean[df_clean[item_type_col].isin(item_types_to_keep)]
    final_count = len(df_clean)
    
    # Calculate results
    rows_kept = final_count
    rows_removed = original_count - final_count
    
    if verbose:
        print(f"\n✓ Filtering complete!")
        print(f"Final item type distribution:")
        final_counts = df_clean[item_type_col].value_counts()
        for item_type, count in final_counts.items():
            print(f"{item_type}: {count:,}")
        
        print(f"\nSummary:")
        print(f"Original rows: {original_count:,}")
        print(f"Rows kept: {rows_kept:,}")
        print(f"Rows removed: {rows_removed:,}")
        print(f"Data retention: {(rows_kept/original_count*100):.1f}%")
        
        if rows_removed > 0:
            removed_categories = set(df[item_type_col].unique()) - set(item_types_to_keep)
            print(f"⚠ Removed categories: {removed_categories}")
    
    return df_clean


def run_complete_item_code_standardization(df: pd.DataFrame,
                                         item_types_to_keep: List[str] = ['WINE', 'BEER'],
                                         supplier_col: str = 'SUPPLIER',
                                         item_code_col: str = 'ITEM CODE',
                                         item_type_col: str = 'ITEM TYPE',
                                         suffix_to_consolidate: str = 'A',
                                         verbose: bool = True) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Run the complete item code standardization pipeline with progress tracking.
    
    Args:
        df (pd.DataFrame): Raw DataFrame to process
        item_types_to_keep (list): Item types to keep (default: ['WINE', 'BEER'])
        supplier_col (str): Supplier column name (default: 'SUPPLIER')
        item_code_col (str): Item code column name (default: 'ITEM CODE')
        item_type_col (str): Item type column name (default: 'ITEM TYPE')
        suffix_to_consolidate (str): Suffix to consolidate (default: 'A')
        verbose (bool): Whether to show progress (default: True)
    
    Returns:
        tuple: (cleaned_dataframe, processing_report)
    """
    if verbose:
        print("="*70)
        print("COMPLETE ITEM CODE STANDARDIZATION PIPELINE")
        print("="*70)
        print(f"Processing dataset with {len(df):,} rows and {len(df.columns)} columns")
    
    # Track progress
    report = {
        'original_shape': df.shape,
        'steps_completed': [],
        'data_quality_improvements': []
    }
    
    try:
        # Step 1: Remove missing suppliers
        df_step1 = clean_missing_supplier_data(df, supplier_col, verbose)
        report['steps_completed'].append('Missing supplier removal')
        report['after_step1_shape'] = df_step1.shape
        
        # Step 2: Analyze non-numeric patterns
        analysis = analyze_non_numeric_item_codes(df_step1, item_code_col, verbose=verbose)
        report['pattern_analysis'] = analysis
        report['steps_completed'].append('Pattern analysis')
        
        # Step 3: Standardize item codes (if needed)
        if analysis.get('non_numeric_count', 0) > 0:
            df_step3 = standardize_item_codes_with_suffix(df_step1, item_code_col, 
                                                        suffix=suffix_to_consolidate, verbose=verbose)
            report['steps_completed'].append('Item code standardization')
        else:
            df_step3 = df_step1.copy()
            if verbose:
                print("⚠ Skipping standardization - no non-numeric codes found")
        
        report['after_step3_shape'] = df_step3.shape
        
        # Step 4: Convert to numeric
        df_step4 = convert_item_codes_to_numeric(df_step3, item_code_col, verbose)
        report['steps_completed'].append('Numeric conversion')
        report['after_step4_shape'] = df_step4.shape
        
        # Step 5: Filter item types
        df_final = filter_item_types(df_step4, item_types_to_keep, item_type_col, verbose)
        report['steps_completed'].append('Item type filtering')
        report['final_shape'] = df_final.shape
        
        # Final summary
        original_rows = df.shape[0]
        final_rows = df_final.shape[0]
        total_removed = original_rows - final_rows
        
        report['summary'] = {
            'original_rows': original_rows,
            'final_rows': final_rows,
            'total_rows_removed': total_removed,
            'data_retention_pct': (final_rows / original_rows * 100) if original_rows > 0 else 0
        }
        
        if verbose:
            print("="*60)
            print("PIPELINE COMPLETE - FINAL SUMMARY")
            print("="*60)
            print(f"Original dataset: {original_rows:,} rows")
            print(f"Final dataset: {final_rows:,} rows")
            print(f"✓ Total rows removed: {total_removed:,}")
            print(f"✓ Data retention: {report['summary']['data_retention_pct']:.1f}%")
            print(f"✓ Steps completed: {', '.join(report['steps_completed'])}")
            
            # Data quality improvements
            improvements = []
            if analysis.get('non_numeric_count', 0) > 0:
                improvements.append("✓ Standardized non-numeric item codes")
            improvements.append("✓ Converted item codes to numeric type")
            improvements.append("✓ Removed missing supplier data")
            improvements.append(f"✓ Filtered to business-relevant categories: {item_types_to_keep}")
            
            print(f"\nData quality improvements:")
            for improvement in improvements:
                print(f"{improvement}")
            
            report['data_quality_improvements'] = improvements
        
        return df_final, report
        
    except Exception as e:
        error_msg = f"Pipeline failed at step {len(report['steps_completed']) + 1}: {str(e)}"
        if verbose:
            print(f"\n❌ {error_msg}")
        report['error'] = error_msg
        return df, report

def run_supplier_enrichment(sales_df: pd.DataFrame, 
                           suppliers_df: pd.DataFrame, 
                           test_mode: bool = False,
                           match_threshold: float = 0.8,
                           verbose: bool = True) -> pd.DataFrame:
    """
    Enrich sales data with supplier information using fuzzy matching.
    
    Matches SUPPLIER column from sales data to Trade Name in suppliers data,
    then adds Report Type information for better brand ownership classification.
    
    Args:
        sales_df (pd.DataFrame): Sales data with SUPPLIER column
        suppliers_df (pd.DataFrame): Suppliers data with Trade Name and Report Type
        test_mode (bool): If True, only process first 1000 rows for testing
        match_threshold (float): Minimum similarity score for matches (0.0-1.0)
        verbose (bool): Whether to show progress
        
    Returns:
        pd.DataFrame: Sales data enriched with supplier information
    """
    from difflib import SequenceMatcher
    
    if verbose:
        print("="*60)
        print("SUPPLIER ENRICHMENT - FUZZY MATCHING")
        print("="*60)
    
    # Create copy of sales data
    enriched_df = sales_df.copy()
    
    if test_mode:
        enriched_df = enriched_df.head(1000)
        if verbose:
            print(f"TEST MODE: Processing only {len(enriched_df)} rows")
    
    # Prepare supplier lookup data
    suppliers_lookup = suppliers_df.copy()
    suppliers_lookup['Trade Name'] = suppliers_lookup['Trade Name'].astype(str).str.strip().str.upper()
    suppliers_lookup = suppliers_lookup.dropna(subset=['Trade Name'])
    
    if verbose:
        print(f"Sales data: {len(enriched_df):,} rows")
        print(f"Suppliers data: {len(suppliers_lookup):,} entries")
        print(f"Unique suppliers in sales: {enriched_df['SUPPLIER'].nunique():,}")
    
    # Initialize new columns
    enriched_df['MATCHED_SUPPLIER_NAME'] = ''
    enriched_df['SUPPLIER_MATCH_SCORE'] = 0.0
    enriched_df['SUPPLIER_REPORT_TYPE'] = ''
    enriched_df['SUPPLIER_LICENSE_ID'] = ''
    
    # Get unique suppliers to avoid redundant matching
    unique_suppliers = enriched_df['SUPPLIER'].dropna().unique()
    supplier_matches = {}
    
    if verbose:
        print(f"\nMatching {len(unique_suppliers):,} unique suppliers...")
    
    # Process each unique supplier
    for i, supplier in enumerate(unique_suppliers):
        if pd.isna(supplier) or supplier == '':
            continue
            
        supplier_clean = str(supplier).strip().upper()
        best_match = None
        best_score = 0.0
        
        # Compare against all trade names
        for _, supplier_row in suppliers_lookup.iterrows():
            trade_name = supplier_row['Trade Name']
            
            # Calculate similarity score
            score = SequenceMatcher(None, supplier_clean, trade_name).ratio()
            
            if score > best_score:
                best_score = score
                best_match = supplier_row
        
        # Store the best match if it meets threshold
        if best_match is not None and best_score >= match_threshold:
            supplier_matches[supplier] = {
                'matched_name': best_match['Trade Name'],
                'score': best_score,
                'report_type': best_match['Report Type'],
                'license_id': best_match['License_ID']
            }
        
        # Progress indicator
        if verbose and (i + 1) % 100 == 0:
            matched_so_far = len([m for m in supplier_matches.values() if m['score'] >= match_threshold])
            print(f"Processed {i + 1:,}/{len(unique_suppliers):,} suppliers, {matched_so_far} matches found")
    
    # Apply matches to the dataframe
    if verbose:
        print(f"\nApplying matches to dataset...")
    
    for supplier, match_info in supplier_matches.items():
        mask = enriched_df['SUPPLIER'] == supplier
        enriched_df.loc[mask, 'MATCHED_SUPPLIER_NAME'] = match_info['matched_name']
        enriched_df.loc[mask, 'SUPPLIER_MATCH_SCORE'] = match_info['score']
        enriched_df.loc[mask, 'SUPPLIER_REPORT_TYPE'] = match_info['report_type']
        enriched_df.loc[mask, 'SUPPLIER_LICENSE_ID'] = match_info['license_id']
    
    # Results summary
    total_matches = len(supplier_matches)
    high_confidence_matches = len([m for m in supplier_matches.values() if m['score'] >= 0.8])
    
    if verbose:
        print(f"\nENRICHMENT COMPLETE:")
        print(f"✓ Total supplier matches found: {total_matches}")
        print(f"✓ High confidence matches (≥0.8): {high_confidence_matches}")
        print(f"✓ Match rate: {(total_matches/len(unique_suppliers)*100):.1f}%")
        
        # Show report type distribution
        if high_confidence_matches > 0:
            print(f"\nReport Type Distribution (high confidence matches):")
            high_conf_mask = enriched_df['SUPPLIER_MATCH_SCORE'] >= 0.8
            report_types = enriched_df[high_conf_mask]['SUPPLIER_REPORT_TYPE'].value_counts()
            for report_type, count in report_types.items():
                print(f"  {report_type}: {count:,}")
    
    return enriched_df


# Example usage and testing
def test_supplier_enrichment():
    """Test function to verify supplier enrichment works"""
    
    # Sample sales data
    sales_sample = pd.DataFrame({
        'SUPPLIER': [
            'REPUBLIC NATIONAL DISTRIBUTING CO',
            'PWSWN INC', 
            'RELIABLE CHURCHILL LLLP',
            'LANTERNA DISTRIBUTORS INC',
            'KYSELA PERE ET FILS LTD'
        ],
        'ITEM_CODE': [100009, 100024, 1001, 100145, 100641],
        'ITEM_TYPE': ['WINE', 'WINE', 'BEER', 'WINE', 'WINE']
    })
    
    # Sample suppliers data  
    suppliers_sample = pd.DataFrame({
        'License_ID': ['085631', '123456', '789012'],
        'Trade Name': [
            'REPUBLIC NATIONAL DISTRIBUTING CO LLC',
            'PWSWN INCORPORATED', 
            'KYSELA PERE ET FILS LTD'
        ],
        'Report Type': [
            'Virginia Importers and Breweries',
            'Wholesale Wine Distributors',
            'Wholesale Wine Distributors'
        ]
    })
    
    # Run enrichment
    result = run_supplier_enrichment(sales_sample, suppliers_sample, test_mode=True)
    
    print(f"\nTEST RESULTS:")
    print(result[['SUPPLIER', 'MATCHED_SUPPLIER_NAME', 'SUPPLIER_MATCH_SCORE', 'SUPPLIER_REPORT_TYPE']].head())
    
    return result

# ================================
# USAGE EXAMPLES AND TESTING
# ================================

if __name__ == "__main__":
    print("Enhanced Data Utilities with Progress Tracking - Loaded Successfully!")
    print("Example usage:")
    print("""
    # Individual functions:
    df_clean = clean_missing_supplier_data(df)
    analysis = analyze_non_numeric_item_codes(df_clean)
    df_standardized = standardize_item_codes_with_suffix(df_clean)
    df_numeric = convert_item_codes_to_numeric(df_standardized)
    df_filtered = filter_item_types(df_numeric, ['WINE', 'BEER'])
    
    # Complete pipeline:
    df_final, report = run_complete_item_code_standardization(df)
    print(f"Processing complete! Final dataset: {df_final.shape}")
    """)