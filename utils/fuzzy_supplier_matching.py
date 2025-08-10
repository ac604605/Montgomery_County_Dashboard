import pandas as pd
import time  # <- Add this line
from difflib import SequenceMatcher

    """
    Fuzzy Supplier Matching System
    Handles name variations, case differences, and business suffix inconsistencies
    """



    def clean_supplier_name(name):
        """
        Clean supplier names for better matching by removing common variations
        """
        if pd.isna(name):
            return ""
        
        name = str(name).upper().strip()
        
        # Remove common business suffixes and variations
        suffixes_to_remove = [
            ' INC', ' LLC', ' CO', ' CORP', ' CORPORATION', ' LTD', ' LIMITED', 
            ' COMPANY', ' LP', ' LLP', ' LLLP', ' DBA', ' USA', ' INC.', ' LLC.', 
            ' CO.', ' CORP.', ' LTD.', ' LP.', ' LLP.'
        ]
        
        for suffix in suffixes_to_remove:
            if name.endswith(suffix):
                name = name[:-len(suffix)].strip()
        
        # Remove extra spaces and punctuation
        name = ' '.join(name.split())  # Normalize whitespace
        name = name.replace('.', '').replace(',', '').replace('&', 'AND')
        
        return name

    def find_best_supplier_match(sales_supplier, suppliers_df, threshold=0.8):
        """
        Find the best matching supplier using fuzzy string matching
        
        Args:
            sales_supplier (str): Supplier name from sales data
            suppliers_df (pd.DataFrame): Suppliers reference table
            threshold (float): Minimum similarity score (0.8 = 80% similar)
        
        Returns:
            tuple: (best_match_name, similarity_score, report_type)
        """
        sales_clean = clean_supplier_name(sales_supplier)
        
        if not sales_clean:
            return None, 0, None
        
        best_match = None
        best_score = 0
        best_report_type = None
        
        for _, row in suppliers_df.iterrows():
            supplier_name = row['Trade Name']
            supplier_clean = clean_supplier_name(supplier_name)
            
            if not supplier_clean:
                continue
            
            # Calculate similarity score
            score = SequenceMatcher(None, sales_clean, supplier_clean).ratio()
            
            # Bonus points for exact word matches
            sales_words = set(sales_clean.split())
            supplier_words = set(supplier_clean.split())
            
            if sales_words and supplier_words:
                word_overlap = len(sales_words.intersection(supplier_words)) / len(sales_words.union(supplier_words))
                score = (score * 0.7) + (word_overlap * 0.3)  # Weighted combination
            
            if score > best_score and score >= threshold:
                best_score = score
                best_match = supplier_name
                best_report_type = row.get('Report_Type', None)
        
        return best_match, best_score, best_report_type

    def enrich_sales_with_supplier_data(sales_df, suppliers_df, threshold=0.8, 
                                       show_progress=True, max_test_rows=None):
        """
        Enrich sales data with supplier information using fuzzy matching
        
        Args:
            sales_df (pd.DataFrame): Sales data with 'SUPPLIER' column
            suppliers_df (pd.DataFrame): Suppliers data with 'Trade Name' and 'Report Type'
            threshold (float): Minimum similarity threshold for matching
            show_progress (bool): Whether to show progress updates
            max_test_rows (int): Limit rows for testing (None = process all)
        
        Returns:
            pd.DataFrame: Enriched sales data with new columns
        """
        print(f"Starting fuzzy supplier matching with threshold {threshold}")
        print(f"Sales data: {len(sales_df):,} rows")
        
        # Filter suppliers to only Wholesale Wine Distributors
        wine_distributors = suppliers_df[suppliers_df['Report_Type'] == 'Wholesale Wine Distributors']
        print(f"Wholesale Wine Distributors: {len(wine_distributors):,} (filtered from {len(suppliers_df):,} total suppliers)")
        
        # Create working copy
        df_enriched = sales_df.copy()
        
        # For testing, limit rows
        if max_test_rows:
            df_enriched = df_enriched.head(max_test_rows)
            print(f"Testing mode: Processing only {max_test_rows:,} rows")
        
        # Add new columns
        df_enriched['MATCHED_SUPPLIER_NAME'] = ""
        df_enriched['SUPPLIER_MATCH_SCORE'] = 0.0
        df_enriched['SUPPLIER_REPORT_TYPE'] = ""
        
        # Get unique suppliers to avoid duplicate work
        unique_suppliers = df_enriched['SUPPLIER'].unique()
        print(f"Unique suppliers to match: {len(unique_suppliers):,}")
        
        # Create supplier lookup cache
        supplier_cache = {}
        
        start_time = time.time()
        matched_count = 0
        
        # Process each unique supplier
        for i, supplier in enumerate(unique_suppliers):
            if pd.isna(supplier):
                continue
                
            # Find best match (only among wine distributors)
            match_name, match_score, report_type = find_best_supplier_match(
                supplier, wine_distributors, threshold
            )
            
            # Cache the result
            supplier_cache[supplier] = {
                'matched_name': match_name or "",
                'match_score': match_score,
                'report_type': 'Wholesale Wine Distributors' if match_name else ""
            }
            
            if match_name:
                matched_count += 1
            
            # Progress reporting
            if show_progress and (i + 1) % 50 == 0:
                elapsed = time.time() - start_time
                print(f"Processed {i+1:,}/{len(unique_suppliers):,} suppliers "
                      f"({matched_count} matches, {elapsed:.1f}s)")
        
        # Apply cached results to all rows
        print("Applying matches to all rows...")
        for supplier, cache_data in supplier_cache.items():
            mask = df_enriched['SUPPLIER'] == supplier
            df_enriched.loc[mask, 'MATCHED_SUPPLIER_NAME'] = cache_data['matched_name']
            df_enriched.loc[mask, 'SUPPLIER_MATCH_SCORE'] = cache_data['match_score']
            df_enriched.loc[mask, 'SUPPLIER_REPORT_TYPE'] = cache_data['report_type']
        
        # Final statistics
        total_time = time.time() - start_time
        total_matched_rows = (df_enriched['SUPPLIER_MATCH_SCORE'] >= threshold).sum()
        match_rate = (total_matched_rows / len(df_enriched)) * 100
        
        print(f"\n{'='*50}")
        print("FUZZY MATCHING RESULTS:")
        print(f"Unique suppliers matched: {matched_count:,}/{len(unique_suppliers):,}")
        print(f"Total rows matched: {total_matched_rows:,}/{len(df_enriched):,} ({match_rate:.1f}%)")
        print(f"Processing time: {total_time:.1f} seconds")
        print(f"Average time per supplier: {total_time/len(unique_suppliers):.3f}s")
        
        return df_enriched

    def test_supplier_matching(sales_df, suppliers_df, test_suppliers=None):
        """
        Test the matching function on specific suppliers
        """
        # Filter to only Wholesale Wine Distributors for testing
        wine_distributors = suppliers_df[suppliers_df['Report_Type'] == 'Wholesale Wine Distributors']
        print(f"Testing against {len(wine_distributors):,} Wholesale Wine Distributors")
        
        if test_suppliers is None:
            # Use some common suppliers for testing
            test_suppliers = [
                "REPUBLIC NATIONAL DISTRIBUTING CO",
                "SANTA MARGHERITA USA INC", 
                "SUTTER HOME WINERY INC",
                "JACKSON FAMILY ENTERPRISES INC"
            ]
        
        print("Testing supplier matching:")
        print("="*50)
        
        for supplier in test_suppliers:
            match_name, score, report_type = find_best_supplier_match(
                supplier, wine_distributors, threshold=0.7
            )
            
            print(f"Sales: '{supplier}'")
            print(f"Match: '{match_name}' (score: {score:.3f})")
            print(f"Type:  '{report_type}'")
            print("-" * 30)

    # Usage functions
    def run_supplier_enrichment(sales_df, suppliers_df, test_mode=False):
        """
        Main function to run supplier enrichment
        """
        if test_mode:
            print("Running in TEST MODE with 1000 rows...")
            result = enrich_sales_with_supplier_data(
                sales_df, suppliers_df, 
                threshold=0.8, 
                max_test_rows=1000
            )
        else:
            print("Running FULL enrichment...")
            result = enrich_sales_with_supplier_data(
                sales_df, suppliers_df, 
                threshold=0.8
            )
        
        return result

    def analyze_supplier_matches(enriched_df):
        """
        Analyze the results of supplier matching
        """
        print("SUPPLIER MATCHING ANALYSIS")
        print("="*40)
        
        # Match rate analysis
        matched = enriched_df[enriched_df['SUPPLIER_MATCH_SCORE'] >= 0.8]
        match_rate = len(matched) / len(enriched_df) * 100
        print(f"Overall match rate: {match_rate:.1f}%")
        
        # Score distribution
        print(f"\nMatch score distribution:")
        print(enriched_df['SUPPLIER_MATCH_SCORE'].describe())
        
        # Report types found
        print(f"\nSupplier Report Types found:")
        print(enriched_df['SUPPLIER_REPORT_TYPE'].value_counts())
        
        # Sample matches
        print(f"\nSample successful matches:")
        sample_matches = matched[['SUPPLIER', 'MATCHED_SUPPLIER_NAME', 
                                 'SUPPLIER_MATCH_SCORE', 'SUPPLIER_REPORT_TYPE']].head(10)
        print(sample_matches)
        
        return matched