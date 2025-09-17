#!/usr/bin/env python3
"""
Corrected Wine Review Matching System
Works with the database structure from corrected_montgomery_api.py
Focuses ONLY on matching, not ingestion
"""

import pandas as pd
import sqlite3
import pickle
import os
import re
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Dict, List, Optional
import logging
from difflib import SequenceMatcher

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('wine_matching.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class WineMatcherFixed:
    def __init__(self, db_path: str = "wine_data.db", enable_parallel: bool = True, max_workers: int = 4):
        self.db_path = db_path
        self.enable_parallel = enable_parallel
        self.max_workers = max_workers
        self.cache = {}
        self.load_cache()
        self.init_matching_tables()
    
    def load_cache(self):
        """Load existing match cache"""
        if os.path.exists('match_cache.pkl'):
            try:
                with open('match_cache.pkl', 'rb') as f:
                    self.cache = pickle.load(f)
                logger.info(f"Loaded {len(self.cache)} cached matches")
            except Exception as e:
                logger.warning(f"Could not load cache: {e}")
                self.cache = {}
        else:
            logger.info("No existing cache found")
    
    def save_cache(self):
        """Save match cache"""
        try:
            with open('match_cache.pkl', 'wb') as f:
                pickle.dump(self.cache, f)
            logger.info(f"Saved {len(self.cache)} cached matches")
        except Exception as e:
            logger.error(f"Could not save cache: {e}")
    
    def init_matching_tables(self):
        """Ensure matching tables exist"""
        with sqlite3.connect(self.db_path) as conn:
            # Create matched_results table if it doesn't exist
            conn.execute('''
                CREATE TABLE IF NOT EXISTS matched_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sales_id INTEGER,
                    wine_name_extracted TEXT,
                    review_match_score REAL,
                    review_title TEXT,
                    review_country TEXT,
                    review_variety TEXT,
                    review_points INTEGER,
                    review_price REAL,
                    match_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (sales_id) REFERENCES sales_data (id)
                )
            ''')
            
            # Create index for faster lookups
            conn.execute('CREATE INDEX IF NOT EXISTS idx_matched_sales_id ON matched_results (sales_id)')
            conn.commit()
        logger.info("Matching tables initialized")
    
    def load_review_data(self) -> Optional[pd.DataFrame]:
        """Load wine review dataset"""
        try:
            df = pd.read_csv('data/winemag-data-130k-v2.csv')
            logger.info(f"Loaded {len(df):,} wine reviews")
            return df
        except Exception as e:
            logger.error(f"Error loading wine review data: {e}")
            return None
    
    def get_unmatched_wines(self, batch_size: int = 1000) -> pd.DataFrame:
        """Get wine records that haven't been matched yet"""
        query = """
            SELECT s.id, s.item_description, s.supplier, s.calendar_year, s.cal_month_num
            FROM sales_data s
            LEFT JOIN matched_results m ON s.id = m.sales_id
            WHERE s.item_type = 'WINE' AND m.sales_id IS NULL
            ORDER BY s.id
            LIMIT ?
        """
        
        with sqlite3.connect(self.db_path) as conn:
            df = pd.read_sql_query(query, conn, params=(batch_size,))
        
        logger.info(f"Found {len(df):,} unmatched wine records")
        return df
    
    def get_matching_stats(self) -> Dict:
        """Get current matching statistics"""
        with sqlite3.connect(self.db_path) as conn:
            # Total wine records
            cursor = conn.execute("SELECT COUNT(*) FROM sales_data WHERE item_type = 'WINE'")
            total_wines = cursor.fetchone()[0]
            
            # Matched records
            cursor = conn.execute("SELECT COUNT(*) FROM matched_results")
            matched_count = cursor.fetchone()[0]
            
            # Unmatched records
            cursor = conn.execute("""
                SELECT COUNT(*) FROM sales_data s
                LEFT JOIN matched_results m ON s.id = m.sales_id
                WHERE s.item_type = 'WINE' AND m.sales_id IS NULL
            """)
            unmatched_count = cursor.fetchone()[0]
            
            # Average match score
            cursor = conn.execute("SELECT AVG(review_match_score) FROM matched_results")
            avg_score = cursor.fetchone()[0] or 0
            
        return {
            'total_wines': total_wines,
            'matched_count': matched_count,
            'unmatched_count': unmatched_count,
            'match_percentage': (matched_count / total_wines * 100) if total_wines > 0 else 0,
            'average_score': avg_score
        }
    
    @staticmethod
    def clean_wine_name(text: str) -> str:
        """Clean wine name for matching"""
        if pd.isna(text) or not text:
            return ""
        
        text = str(text).upper().strip()
        
        # Remove volume indicators
        text = re.sub(r'\s*-?\s*(750ML|1\.5L|375ML|187ML|3L|500ML|1L|750|1500|375)\s*$', '', text)
        
        # Expand abbreviations
        abbreviations = {
            'CH ': 'CHATEAU ', 'CH.': 'CHATEAU', 'DOM ': 'DOMAINE ', 'DOM.': 'DOMAINE',
            'S/BLC': 'SAUVIGNON BLANC', 'SAUV BLANC': 'SAUVIGNON BLANC',
            'P/GRIG': 'PINOT GRIGIO', 'P/GRIS': 'PINOT GRIS', 'P/NOIR': 'PINOT NOIR',
            'CAB SAV': 'CABERNET SAUVIGNON', 'CAB': 'CABERNET', 'CHARD': 'CHARDONNAY',
            'MERLOT': 'MERLOT', 'SHIRAZ': 'SYRAH'
        }
        
        for abbrev, full in abbreviations.items():
            text = text.replace(abbrev, full)
        
        # Clean punctuation and normalize spaces
        text = re.sub(r'[^\w\s]', ' ', text)
        text = ' '.join(text.split())
        
        return text.strip()
    
    def find_wine_match(self, wine_name: str, review_data: pd.DataFrame) -> Dict:
        """Find best matching wine review"""
        if len(wine_name) < 3:
            return {'wine_name': wine_name, 'match_score': 0}
        
        # Check cache first
        if wine_name in self.cache:
            cached_match = self.cache[wine_name]
            if cached_match.get('match_score', 0) >= 0.6:
                return cached_match
        
        # Create search mask
        search_words = [word for word in wine_name.split() if len(word) > 2]
        if not search_words:
            return {'wine_name': wine_name, 'match_score': 0}
        
        # Find potential matches
        mask = pd.Series([False] * len(review_data))
        for word in search_words:
            mask |= review_data['title'].str.contains(word, case=False, na=False)
        
        potential_matches = review_data[mask].head(100)  # Increased for better matches
        
        if potential_matches.empty:
            return {'wine_name': wine_name, 'match_score': 0}
        
        # Find best match using sequence matching
        best_score = 0
        best_match = None
        
        for _, candidate in potential_matches.iterrows():
            candidate_clean = self.clean_wine_name(candidate['title'])
            score = SequenceMatcher(None, wine_name, candidate_clean).ratio()
            
            if score > best_score:
                best_score = score
                best_match = candidate
        
        if best_match is not None and best_score >= 0.6:
            result = {
                'wine_name': wine_name,
                'match_score': best_score,
                'title': best_match.get('title', ''),
                'country': best_match.get('country', ''),
                'variety': best_match.get('variety', ''),
                'points': best_match.get('points', 0),
                'price': best_match.get('price', 0.0)
            }
            
            # Cache the result
            self.cache[wine_name] = result
            return result
        
        return {'wine_name': wine_name, 'match_score': 0}
    
    def process_wine_batch(self, wine_batch: pd.DataFrame, review_data: pd.DataFrame) -> List[Dict]:
        """Process a batch of wine records"""
        matches = []
        
        for _, row in wine_batch.iterrows():
            wine_name = self.clean_wine_name(row.get('item_description', ''))
            
            if len(wine_name) < 3:
                continue
            
            match_result = self.find_wine_match(wine_name, review_data)
            
            if match_result['match_score'] >= 0.6:
                matches.append({
                    'sales_id': row['id'],
                    'wine_name_extracted': wine_name,
                    'review_match_score': match_result['match_score'],
                    'review_title': match_result.get('title', ''),
                    'review_country': match_result.get('country', ''),
                    'review_variety': match_result.get('variety', ''),
                    'review_points': match_result.get('points', 0),
                    'review_price': match_result.get('price', 0.0)
                })
        
        return matches
    
    def store_matches(self, matches: List[Dict]):
        """Store matches in database"""
        if not matches:
            return
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                for match in matches:
                    conn.execute("""
                        INSERT INTO matched_results 
                        (sales_id, wine_name_extracted, review_match_score, review_title,
                         review_country, review_variety, review_points, review_price)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        match['sales_id'], match['wine_name_extracted'], match['review_match_score'],
                        match['review_title'], match['review_country'], match['review_variety'],
                        match['review_points'], match['review_price']
                    ))
                conn.commit()
            logger.info(f"Stored {len(matches)} matches")
        except Exception as e:
            logger.error(f"Error storing matches: {e}")
    
    def run_matching(self, batch_size: int = 1000, max_batches: Optional[int] = None):
        """Run the complete matching process"""
        start_time = datetime.now()
        
        # Load review data
        review_data = self.load_review_data()
        if review_data is None:
            logger.error("Cannot proceed without wine review data")
            return
        
        # Get initial stats
        initial_stats = self.get_matching_stats()
        logger.info(f"Starting matching: {initial_stats['unmatched_count']:,} unmatched wines")
        
        if initial_stats['unmatched_count'] == 0:
            logger.info("No unmatched wines found - matching complete!")
            return
        
        total_processed = 0
        total_matches = 0
        batch_count = 0
        
        try:
            while True:
                # Check batch limit
                if max_batches and batch_count >= max_batches:
                    logger.info(f"Reached batch limit ({max_batches})")
                    break
                
                # Get next batch of unmatched wines
                wine_batch = self.get_unmatched_wines(batch_size)
                
                if wine_batch.empty:
                    logger.info("No more unmatched wines found")
                    break
                
                logger.info(f"Processing batch {batch_count + 1}: {len(wine_batch)} wines")
                
                # Process batch
                if self.enable_parallel and len(wine_batch) > 50:
                    # Split into chunks for parallel processing
                    chunk_size = max(10, len(wine_batch) // self.max_workers)
                    chunks = [wine_batch[i:i + chunk_size] for i in range(0, len(wine_batch), chunk_size)]
                    
                    all_matches = []
                    with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
                        futures = [executor.submit(self.process_wine_batch, chunk, review_data) for chunk in chunks]
                        for future in as_completed(futures):
                            all_matches.extend(future.result())
                else:
                    all_matches = self.process_wine_batch(wine_batch, review_data)
                
                # Store matches
                if all_matches:
                    self.store_matches(all_matches)
                    total_matches += len(all_matches)
                
                total_processed += len(wine_batch)
                batch_count += 1
                
                logger.info(f"Batch {batch_count} complete: {len(all_matches)} matches found")
                
                # Save cache periodically
                if batch_count % 5 == 0:
                    self.save_cache()
        
        finally:
            # Save cache
            self.save_cache()
        
        # Final statistics
        duration = datetime.now() - start_time
        final_stats = self.get_matching_stats()
        
        logger.info("=" * 60)
        logger.info("WINE MATCHING COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Duration: {duration}")
        logger.info(f"Wines processed: {total_processed:,}")
        logger.info(f"New matches found: {total_matches:,}")
        logger.info(f"Total wines: {final_stats['total_wines']:,}")
        logger.info(f"Total matched: {final_stats['matched_count']:,}")
        logger.info(f"Remaining unmatched: {final_stats['unmatched_count']:,}")
        logger.info(f"Match percentage: {final_stats['match_percentage']:.1f}%")
        logger.info(f"Average match score: {final_stats['average_score']:.3f}")

def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Wine Matching System")
        print("Usage:")
        print("  python corrected_wine_matcher.py match              # Run full matching")
        print("  python corrected_wine_matcher.py match 500          # Custom batch size")
        print("  python corrected_wine_matcher.py match 1000 10      # Batch size + max batches")
        print("  python corrected_wine_matcher.py status             # Show matching stats")
        print("  python corrected_wine_matcher.py test               # Test with small batch")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    matcher = WineMatcherFixed()
    
    if command == "match":
        batch_size = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
        max_batches = int(sys.argv[3]) if len(sys.argv) > 3 else None
        matcher.run_matching(batch_size, max_batches)
    
    elif command == "status":
        stats = matcher.get_matching_stats()
        print("=" * 50)
        print("WINE MATCHING STATUS")
        print("=" * 50)
        print(f"Total wine records:     {stats['total_wines']:,}")
        print(f"Matched records:        {stats['matched_count']:,}")
        print(f"Unmatched records:      {stats['unmatched_count']:,}")
        print(f"Match percentage:       {stats['match_percentage']:.1f}%")
        print(f"Average match score:    {stats['average_score']:.3f}")
        print(f"Cache size:             {len(matcher.cache):,} entries")
    
    elif command == "test":
        print("Running test with 100 wines...")
        matcher.run_matching(batch_size=100, max_batches=1)
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()