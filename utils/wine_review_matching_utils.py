"""
Wine Review Matching Utilities - External Module
File: utils/wine_review_matching_utils.py

Matches sales data item descriptions directly against wine review titles
with integrated column validation and progress tracking.

Usage in Jupyter:
    sys.path.append('./utils')
    import wine_review_matching_utils as wrmu
    
    # Test mode
    results, sales_map, review_map = wrmu.run_wine_review_matching(
        sales_df, review_df, threshold=0.6, test_mode=True
    )
    
    # Full run
    results, sales_map, review_map = wrmu.run_wine_review_matching(
        sales_df, review_df, threshold=0.6, test_mode=False
    )
"""

import pandas as pd
import time
from datetime import datetime, timedelta
import re
from difflib import SequenceMatcher
from typing import Dict, List, Optional, Tuple
import warnings


class ColumnValidator:
    """Handle column validation and mapping for wine matching system"""
    
    def __init__(self):
        # Define expected column mappings with alternatives
        self.sales_columns = {
            'item_type': ['ITEM TYPE', 'ITEM_TYPE', 'ItemType', 'item_type'],
            'item_description': ['ITEM DESCRIPTION', 'ITEM_DESCRIPTION', 'ItemDescription', 'item_description'],
            'supplier': ['SUPPLIER', 'supplier'],
            'item_code': ['ITEM CODE', 'ITEM_CODE', 'ItemCode', 'item_code'],
            'year': ['YEAR', 'year'],
            'month': ['MONTH', 'month'],
        }
        
        self.review_columns = {
            'title': ['title', 'Title', 'TITLE', 'wine_title'],
            'country': ['country', 'Country', 'COUNTRY'],
            'variety': ['variety', 'Variety', 'VARIETY'],
            'points': ['points', 'Points', 'POINTS', 'rating', 'score'],
            'price': ['price', 'Price', 'PRICE'],
            'description': ['description', 'Description', 'DESCRIPTION'],
            'province': ['province', 'Province', 'PROVINCE', 'region'],
            'region_1': ['region_1', 'Region_1', 'REGION_1', 'region1'],
            'region_2': ['region_2', 'Region_2', 'REGION_2', 'region2'],
            'winery': ['winery', 'Winery', 'WINERY'],
            'designation': ['designation', 'Designation', 'DESIGNATION'],
            'taster_name': ['taster_name', 'Taster_Name', 'TASTER_NAME', 'taster'],
        }
    
    def find_column(self, df: pd.DataFrame, column_key: str, column_dict: Dict) -> Optional[str]:
        """Find the actual column name in the DataFrame"""
        possible_names = column_dict.get(column_key, [])
        
        for name in possible_names:
            if name in df.columns:
                return name
        return None
    
    def validate_and_map_columns(self, sales_df: pd.DataFrame, 
                                review_df: pd.DataFrame) -> Tuple[Dict[str, str], Dict[str, str]]:
        """
        Validate required columns exist and create mapping dictionaries
        
        Returns:
            Tuple of (sales_column_map, review_column_map)
        """
        # Required columns for basic functionality
        required_sales = ['item_type', 'item_description']
        required_reviews = ['title']
        
        # Create column mappings
        sales_map = {}
        review_map = {}
        
        # Validate sales columns
        missing_sales = []
        for col_key in required_sales:
            actual_col = self.find_column(sales_df, col_key, self.sales_columns)
            if actual_col:
                sales_map[col_key] = actual_col
            else:
                missing_sales.append(col_key)
        
        # Validate review columns
        missing_reviews = []
        for col_key in required_reviews:
            actual_col = self.find_column(review_df, col_key, self.review_columns)
            if actual_col:
                review_map[col_key] = actual_col
            else:
                missing_reviews.append(col_key)
        
        # Add optional columns that exist
        optional_sales = ['supplier', 'item_code', 'year', 'month']
        for col_key in optional_sales:
            actual_col = self.find_column(sales_df, col_key, self.sales_columns)
            if actual_col:
                sales_map[col_key] = actual_col
        
        optional_reviews = ['country', 'variety', 'points', 'price', 'description', 
                          'province', 'region_1', 'region_2', 'winery', 'designation', 'taster_name']
        for col_key in optional_reviews:
            actual_col = self.find_column(review_df, col_key, self.review_columns)
            if actual_col:
                review_map[col_key] = actual_col
        
        # Report issues
        if missing_sales or missing_reviews:
            error_msg = "Missing required columns:\n"
            if missing_sales:
                available_sales = list(sales_df.columns)
                error_msg += f"Sales data missing: {missing_sales}\n"
                error_msg += f"Available sales columns: {available_sales}\n"
            if missing_reviews:
                available_reviews = list(review_df.columns)
                error_msg += f"Review data missing: {missing_reviews}\n"
                error_msg += f"Available review columns: {available_reviews}\n"
            raise ValueError(error_msg)
        
        return sales_map, review_map
    
    def print_column_mapping(self, sales_map: Dict[str, str], review_map: Dict[str, str]):
        """Print the column mapping for verification"""
        print("✅ Column Mapping Detected:")
        print("Sales Data:")
        for key, actual in sales_map.items():
            print(f"  {key} -> '{actual}'")
        
        print("Review Data:")
        for key, actual in review_map.items():
            print(f"  {key} -> '{actual}'")
        print()


def clean_text_for_matching(text):
    """Clean text for better matching"""
    if pd.isna(text):
        return ""
    
    text = str(text).upper()
    
    # Remove common wine suffixes and volume indicators
    text = re.sub(r'\s*-\s*(750ML|1\.5L|375ML|187ML|3L|500ML|1L)\s*$', '', text)
    text = re.sub(r'\s*-\s*$', '', text)  # Remove trailing dashes
    
    # Remove common business suffixes
    suffixes_to_remove = [
        'INC', 'LLC', 'CO', 'CORP', 'CORPORATION', 'LTD', 'LIMITED',
        'COMPANY', 'WINERY', 'VINEYARDS', 'VINEYARD', 'WINES', 'WINE'
    ]
    
    for suffix in suffixes_to_remove:
        text = re.sub(rf'\b{suffix}\b', '', text)
    
    # Clean up extra spaces and punctuation
    text = re.sub(r'[^\w\s]', ' ', text)
    text = ' '.join(text.split())
    
    return text.strip()


def extract_wine_name_from_description(item_description):
    """Extract searchable wine name from item description"""
    desc = item_description.upper().strip()
    
    # Remove volume first
    desc = re.sub(r'\s*-\s*(750ML|1\.5L|375ML|187ML|3L|500ML|1L)\s*$', '', desc)
    
    # Handle common abbreviations
    abbreviation_map = {
        'CH ': 'CHATEAU ',
        'DOM ': 'DOMAINE ',
        'S/BLC': 'SAUVIGNON BLANC',
        'P/GRIG': 'PINOT GRIGIO', 
        'P/GRIS': 'PINOT GRIS',
        'S/BLANC': 'SAUVIGNON BLANC',
        'P/NOIR': 'PINOT NOIR',
        'CAB SAV': 'CABERNET SAUVIGNON',
        'CAB': 'CABERNET',
        'CHARD': 'CHARDONNAY'
    }
    
    for abbrev, full_name in abbreviation_map.items():
        desc = desc.replace(abbrev, full_name)
    
    return desc.strip()


def find_best_wine_review_match(wine_name, wine_review_data, review_map, threshold=0.6):
    """Find the best matching wine review using two-stage approach"""
    wine_clean = clean_text_for_matching(wine_name)
    if not wine_clean or len(wine_clean) < 3:
        return None, 0
    
    # Stage 1: Fast pre-filtering using substring search
    search_words = wine_clean.split()
    if not search_words:
        return None, 0
    
    # Create search pattern - look for wines containing any key words
    search_pattern = '|'.join([word for word in search_words if len(word) > 2])
    
    if not search_pattern:
        return None, 0
    
    # Use the mapped column name for title
    title_col = review_map['title']
    
    try:
        potential_matches = wine_review_data[
            wine_review_data[title_col].str.contains(search_pattern, case=False, na=False, regex=True)
        ]
    except (re.error, ValueError) as e:
        # Fallback to simple contains if regex fails
        potential_matches = wine_review_data[
            wine_review_data[title_col].str.contains(search_words[0], case=False, na=False, regex=False)
        ]
    
    if len(potential_matches) == 0:
        return None, 0
    
    # Stage 2: Fuzzy matching on filtered candidates
    best_match = None
    best_score = 0
    
    # Limit candidates for performance (top 50 pre-filtered results)
    candidates = potential_matches.head(50)
    
    for _, wine_row in candidates.iterrows():
        candidate_title = clean_text_for_matching(wine_row[title_col])
        if not candidate_title:
            continue
        
        # Calculate similarity score
        similarity = SequenceMatcher(None, wine_clean, candidate_title).ratio()
        
        # Bonus for word matches
        wine_words = set(wine_clean.split())
        candidate_words = set(candidate_title.split())
        
        if wine_words and candidate_words:
            word_overlap = len(wine_words.intersection(candidate_words)) / len(wine_words)
            similarity += word_overlap * 0.3  # 30% bonus for word matches
        
        if similarity > best_score and similarity >= threshold:
            best_score = similarity
            best_match = wine_row
    
    return best_match, best_score


def print_progress_update(processed, total, matched_count, cache_hits, start_time, interval=5000):
    """Print detailed progress update every N wines"""
    if processed % interval == 0 or processed == total:
        elapsed = time.time() - start_time
        avg_time = elapsed / processed
        remaining = total - processed
        eta_seconds = remaining * avg_time
        eta = str(timedelta(seconds=int(eta_seconds)))
        
        match_rate = (matched_count / processed) * 100
        cache_rate = (cache_hits / processed) * 100
        wines_per_minute = (processed / elapsed) * 60
        
        print(f"\n{'='*60}")
        print(f"🍷 PROGRESS UPDATE - {processed:,}/{total:,} wines ({processed/total*100:.1f}%)")
        print(f"{'='*60}")
        print(f"✅ Matches found: {matched_count:,} ({match_rate:.1f}%)")
        print(f"🚀 Cache efficiency: {cache_rate:.1f}%")
        print(f"⚡ Processing speed: {wines_per_minute:.0f} wines/minute")
        print(f"⏱️  Elapsed time: {str(timedelta(seconds=int(elapsed)))}")
        print(f"🎯 ETA to completion: {eta}")
        
        if remaining > 0:
            print(f"📊 Estimated total time: {str(timedelta(seconds=int(elapsed + eta_seconds)))}")
        print(f"{'='*60}\n")


def match_wines_to_reviews(sales_df, wine_review_data, threshold=0.6, 
                          max_test_rows=None, show_progress=True, progress_interval=5000):
    """
    Match wine sales data to wine review data with integrated column validation
    
    Args:
        sales_df: DataFrame with wine sales data
        wine_review_data: DataFrame with wine review data
        threshold: Minimum similarity score for matching (0.6 = 60%)
        max_test_rows: Limit for testing (None = process all)
        show_progress: Whether to show progress updates
        progress_interval: Show progress every N wines (default: 5000)
    
    Returns:
        Tuple of (DataFrame with wine review data added, sales_map, review_map)
    """
    print(f"🍷 Starting Wine Review Matching with Validation...")
    
    # Step 1: Validate and map columns
    validator = ColumnValidator()
    try:
        sales_map, review_map = validator.validate_and_map_columns(sales_df, wine_review_data)
        validator.print_column_mapping(sales_map, review_map)
    except ValueError as e:
        print(f"❌ Column validation failed: {e}")
        return None, None, None
    
    print(f"📊 Dataset Info:")
    print(f"  Sales data: {len(sales_df):,} total rows")
    print(f"  Wine reviews: {len(wine_review_data):,} rows")
    print(f"  Matching threshold: {threshold}")
    
    # Step 2: Filter to wines using the mapped column name
    wine_mask = sales_df[sales_map['item_type']] == 'WINE'
    wine_sales = sales_df[wine_mask].copy()
    
    print(f"  Wine records found: {len(wine_sales):,}")
    
    if max_test_rows:
        wine_sales = wine_sales.head(max_test_rows)
        print(f"🧪 TEST MODE: Processing {len(wine_sales):,} wines")
    else:
        print(f"🚀 FULL MODE: Processing {len(wine_sales):,} wines")
    
    # Step 3: Initialize new columns for wine review data
    for col_key, actual_col in review_map.items():
        if actual_col in ['Unnamed: 0']:  # Skip index columns
            continue
        new_col_name = f'review_{col_key}'
        if new_col_name not in wine_sales.columns:
            wine_sales[new_col_name] = ""
    
    # Add metadata columns
    wine_sales['WINE_NAME_EXTRACTED'] = ""
    wine_sales['REVIEW_MATCH_SCORE'] = 0.0
    wine_sales['REVIEW_MATCH_STATUS'] = 'NO_MATCH'
    
    # Step 4: Initialize tracking variables
    match_cache = {}
    matched_count = 0
    cache_hits = 0
    start_time = time.time()
    total_wines = len(wine_sales)
    
    print(f"\n🏁 Starting matching process...")
    print(f"📈 Progress updates every {progress_interval:,} wines")
    
    # Step 5: Process each wine
    item_desc_col = sales_map['item_description']
    
    for i, (idx, row) in enumerate(wine_sales.iterrows()):
        processed = i + 1
        item_desc = row[item_desc_col]
        
        # Check cache first
        if item_desc in match_cache:
            result = match_cache[item_desc]
            cache_hits += 1
        else:
            # Extract wine name and find match
            wine_name = extract_wine_name_from_description(item_desc)
            wine_match, match_score = find_best_wine_review_match(
                wine_name, wine_review_data, review_map, threshold
            )
            
            result = {
                'wine_name': wine_name,
                'match_data': wine_match,
                'score': match_score
            }
            match_cache[item_desc] = result
        
        # Apply results
        wine_sales.at[idx, 'WINE_NAME_EXTRACTED'] = result['wine_name']
        wine_sales.at[idx, 'REVIEW_MATCH_SCORE'] = result['score']
        
        if result['match_data'] is not None:
            wine_sales.at[idx, 'REVIEW_MATCH_STATUS'] = 'MATCHED'
            matched_count += 1
            
            # Add all review columns using the mapped names
            for col_key, actual_col in review_map.items():
                if actual_col in ['Unnamed: 0']:
                    continue
                review_col_name = f'review_{col_key}'
                if review_col_name in wine_sales.columns:
                    wine_sales.at[idx, review_col_name] = result['match_data'][actual_col]
        
        # Progress reporting every N wines
        if show_progress:
            print_progress_update(processed, total_wines, matched_count, cache_hits, 
                                start_time, progress_interval)
    
    # Final statistics
    total_time = time.time() - start_time
    final_match_rate = (matched_count / len(wine_sales)) * 100
    
    print(f"\n{'='*60}")
    print("🏆 WINE REVIEW MATCHING COMPLETE!")
    print(f"{'='*60}")
    print(f"📊 Final Statistics:")
    print(f"  Wines processed: {len(wine_sales):,}")
    print(f"  Matches found: {matched_count:,} ({final_match_rate:.1f}%)")
    print(f"  Cache efficiency: {(cache_hits/len(wine_sales)*100):.1f}%")
    print(f"  Total processing time: {str(timedelta(seconds=int(total_time)))}")
    print(f"  Average speed: {(len(wine_sales) / total_time * 60):.0f} wines/minute")
    print(f"{'='*60}")
    
    return wine_sales, sales_map, review_map


def run_wine_review_matching(sales_df, wine_review_data, threshold=0.6, test_mode=False, 
                           progress_interval=5000):
    """
    Main function to run wine review matching with validation
    
    Args:
        sales_df: DataFrame with wine sales data
        wine_review_data: DataFrame with wine review data  
        threshold: Minimum similarity score for matching (0.6 = 60%)
        test_mode: If True, process only 1000 wines for testing
        progress_interval: Show progress every N wines (default: 5000)
    
    Returns:
        Tuple of (results_df, sales_column_map, review_column_map)
    """
    if test_mode:
        print("🧪 Running in TEST MODE with 1,000 wines...")
        return match_wines_to_reviews(
            sales_df, wine_review_data, 
            threshold=threshold,
            max_test_rows=1000,
            progress_interval=progress_interval
        )
    else:
        print("🚀 Running FULL wine review matching...")
        return match_wines_to_reviews(
            sales_df, wine_review_data,
            threshold=threshold,
            progress_interval=progress_interval
        )


def safe_column_access(df, column_map, key):
    """
    Safe way to access columns using the mapping
    
    Usage: 
        item_desc = safe_column_access(sales_df, sales_map, 'item_description')
    """
    if key not in column_map:
        raise KeyError(f"Column key '{key}' not found in mapping")
    
    actual_column = column_map[key]
    if actual_column not in df.columns:
        raise KeyError(f"Mapped column '{actual_column}' not found in DataFrame")
    
    return df[actual_column]


def display_sample_matches(results_df, num_samples=5):
    """
    Display sample matches for verification
    
    Args:
        results_df: Results from wine matching process
        num_samples: Number of samples to display
    """
    if results_df is None:
        print("❌ No results to display - matching may have failed")
        return
    
    matched = results_df[results_df['REVIEW_MATCH_STATUS'] == 'MATCHED']
    
    if len(matched) == 0:
        print("❌ No matches found in results")
        return
    
    print(f"\n📋 Sample Matches ({min(num_samples, len(matched))} of {len(matched):,} total):")
    print("="*80)
    
    # Define columns to display (only if they exist)
    display_cols = [
        'ITEM DESCRIPTION', 'WINE_NAME_EXTRACTED', 'REVIEW_MATCH_SCORE',
        'review_title', 'review_country', 'review_variety', 'review_points'
    ]
    
    available_cols = [col for col in display_cols if col in matched.columns]
    
    sample = matched[available_cols].head(num_samples)
    
    for i, (_, row) in enumerate(sample.iterrows(), 1):
        print(f"\n{i}. Original: {row.get('ITEM DESCRIPTION', 'N/A')}")
        print(f"   Extracted: {row.get('WINE_NAME_EXTRACTED', 'N/A')}")
        print(f"   Score: {row.get('REVIEW_MATCH_SCORE', 0):.3f}")
        if 'review_title' in row:
            print(f"   Matched: {row['review_title']}")
        if 'review_country' in row and 'review_variety' in row:
            print(f"   Details: {row.get('review_country', 'N/A')} | {row.get('review_variety', 'N/A')} | {row.get('review_points', 'N/A')} pts")


# Quick test function for development
def quick_test(sales_df, review_df, num_wines=100):
    """Quick test function for development/debugging"""
    print(f"🔧 Quick Test Mode - Processing {num_wines} wines...")
    return match_wines_to_reviews(
        sales_df, review_df,
        threshold=0.6,
        max_test_rows=num_wines,
        show_progress=True,
        progress_interval=50  # More frequent updates for small tests
    )