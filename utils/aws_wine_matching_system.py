#!/usr/bin/env python3
"""
Clean Wine Review Matching System
Simple, reliable approach that works first time
"""

import pandas as pd
import sqlite3
import pickle
import os
import re
import time
from datetime import datetime
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

class CleanWineMatcher:
    def __init__(self, db_path: str = "wine_data.db"):
        self.db_path = db_path
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
            self.cache = {}
    
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
            conn.execute('CREATE INDEX IF NOT EXISTS idx_matched_sales_id ON matched_results (sales_id)')
            conn.commit()
        logger.info("Matching tables initialized")
    
    def load_review_data(self) -> Optional[pd.DataFrame]:
        """Load wine review dataset"""
        try:
            df = pd.read_csv('data/winemag-data-130k-v2.csv')
            # Pre-clean all wine titles for faster matching
            df['title_clean'] = df['title'].apply(self.clean_wine_name)
            logger.info(f"Loaded {len(df):,} wine reviews")
            return df
        except Exception as e:
            logger.error(f"Error loading wine review data: {e}")
            return None
    
    def clean_wine_name(self, name: str) -> str:
        """Clean wine name for better matching"""
        if pd.isna(name) or not name:
            return ""
        
        name = str(name).upper().strip()
        
        # Remove volume indicators
        name = re.sub(r'\s*-?\s*(750ML|1\.5L|375ML|187ML|3L|500ML|1L|750|1500|375)\s*$', '', name)
        name = re.sub(r'\s*-?\s*(ML|L)\s*$', '', name)
        
        # Remove common descriptors
        descriptors = [' WINE', ' RED', ' WHITE', ' ROSE', ' SPARKLING', ' BOTTLE', ' BTL']
        for desc in descriptors:
            if name.endswith(desc):
                name = name[:-len(desc)].strip()
        
        # Expand abbreviations
        abbreviations = {
            'CH ': 'CHATEAU ', 'CH.': 'CHATEAU',
            'DOM ': 'DOMAINE ', 'DOM.': 'DOMAINE',
            'S/BLC': 'SAUVIGNON BLANC', 'SAUV BLANC': 'SAUVIGNON BLANC',
            'P/GRIG': 'PINOT GRIGIO', 'P/NOIR': 'PINOT NOIR',
            'CAB SAV': 'CABERNET SAUVIGNON', 'CAB': 'CABERNET',
            'CHARD': 'CHARDONNAY'
        }
        
        for abbrev, full in abbreviations.items():
            name = name.replace(abbrev, full)
        
        # Clean punctuation and normalize whitespace
        name = re.sub(r'[^\w\s]', ' ', name)
        name = ' '.join(name.split())
        
        return name.strip()
    
    def find_best_match(self, wine_name: str, review_data: pd.DataFrame, threshold: float = 0.6) -> Dict:
        """Find best wine match using simple, reliable approach"""
        if len(wine_name) < 3:
            return {'wine_name': wine_name, 'match_score': 0}
        
        # Check cache first
        if wine_name in self.cache:
            return self.cache[wine_name]
        
        # Clean the wine name
        wine_clean = self.clean_wine_name(wine_name)
        if len(wine_clean) < 3:
            return {'wine_name': wine_name, 'match_score': 0}
        
        # Find potential matches by looking for wines that share words
        wine_words = set(wine_clean.split())
        if not wine_words:
            return {'wine_name': wine_name, 'match_score': 0}
        
        # Filter to wines that have at least one word in common
        mask = pd.Series([False] * len(review_data))
        for word in wine_words:
            if len(word) > 2:  # Only use words longer than 2 characters
                mask |= review_data['title_clean'].str.contains(word, case=False, na=False)
        
        candidates = review_data[mask].head(200)  # Limit candidates for speed
        
        if candidates.empty:
            result = {'wine_name': wine_name, 'match_score': 0}
            self.cache[wine_name] = result
            return result
        
        # Score each candidate
        best_score = 0
        best_match = None
        
        for _, candidate in candidates.iterrows():
            candidate_clean = candidate['title_clean']
            if not candidate_clean:
                continue
            
            # Calculate similarity score
            score = SequenceMatcher(None, wine_clean, candidate_clean).ratio()
            
            if score > best_score and score >= threshold:
                best_score = score
                best_match = candidate
        
        # Create result
        if best_match is not None and best_score >= threshold:
            result = {
                'wine_name': wine_name,
                'match_score': best_score,
                'title': best_match.get('title', ''),
                'country': best_match.get('country', ''),
                'variety': best_match.get('variety', ''),
                'points': best_match.get('points', 0),
                'price': best_match.get('price', 0.0)
            }
        else:
            result = {'wine_name': wine_name, 'match_score': 0}
        
        # Cache and return
        self.cache[wine_name] = result
        return result
    
    def get_unmatched_wines(self, batch_size: int, offset: int = 0) -> pd.DataFrame:
        """Get unmatched wines using simple offset-based pagination"""
        with sqlite3.connect(self.db_path) as conn:
            query = """
                SELECT s.id, s.item_description, s.supplier, s.calendar_year, s.cal_month_num
                FROM sales_data s
                LEFT JOIN matched_results m ON s.id = m.sales_id
                WHERE s.item_type = 'WINE'
                  AND m.sales_id IS NULL
                ORDER BY s.id
                LIMIT ? OFFSET ?
            """
            return pd.read_sql_query(query, conn, params=[batch_size, offset])
    
    def process_batch(self, wine_batch: pd.DataFrame, review_data: pd.DataFrame, 
                     threshold: float = 0.6) -> List[Dict]:
        """Process a batch of wines"""
        matches = []
        
        for _, row in wine_batch.iterrows():
            wine_name = row.get('item_description', '')
            if pd.isna(wine_name) or len(str(wine_name).strip()) < 3:
                continue
            
            wine_name = str(wine_name).strip()
            match_result = self.find_best_match(wine_name, review_data, threshold)
            
            if match_result['match_score'] >= threshold:
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
    
    def get_stats(self) -> Dict:
        """Get matching statistics"""
        with sqlite3.connect(self.db_path) as conn:
            # Total wines
            total = conn.execute("SELECT COUNT(*) FROM sales_data WHERE item_type = 'WINE'").fetchone()[0]
            
            # Matched count
            matched = conn.execute("SELECT COUNT(*) FROM matched_results").fetchone()[0]
            
            # Unmatched count
            unmatched = conn.execute("""
                SELECT COUNT(*) FROM sales_data s
                LEFT JOIN matched_results m ON s.id = m.sales_id
                WHERE s.item_type = 'WINE' AND m.sales_id IS NULL
            """).fetchone()[0]
            
            return {
                'total_wines': total,
                'matched_count': matched,
                'unmatched_count': unmatched,
                'match_percentage': (matched / total * 100) if total > 0 else 0
            }
    
    def run_matching(self, batch_size: int = 1000, max_batches: Optional[int] = None, 
                    threshold: float = 0.6):
        """Run the matching process"""
        start_time = datetime.now()
        
        # Load review data
        review_data = self.load_review_data()
        if review_data is None:
            logger.error("Cannot proceed without wine review data")
            return
        
        # Get initial stats
        initial_stats = self.get_stats()
        logger.info(f"Starting matching: {initial_stats['unmatched_count']:,} unmatched wines")
        logger.info(f"Using threshold: {threshold}, batch size: {batch_size}")
        
        if initial_stats['unmatched_count'] == 0:
            logger.info("No unmatched wines found - matching complete!")
            return
        
        total_processed = 0
        total_matches = 0
        batch_count = 0
        offset = 0
        
        try:
            while True:
                if max_batches and batch_count >= max_batches:
                    logger.info(f"Reached batch limit ({max_batches})")
                    break
                
                # Get next batch of unmatched wines
                wine_batch = self.get_unmatched_wines(batch_size, offset)
                
                if wine_batch.empty:
                    logger.info("No more unmatched wines found")
                    break
                
                batch_start = time.time()
                logger.info(f"Processing batch {batch_count + 1}: {len(wine_batch)} wines (offset: {offset})")
                
                # Process the batch
                matches = self.process_batch(wine_batch, review_data, threshold)
                
                # Store matches
                if matches:
                    self.store_matches(matches)
                    total_matches += len(matches)
                
                total_processed += len(wine_batch)
                offset += len(wine_batch)  # Move offset forward for next batch
                batch_count += 1
                
                batch_time = time.time() - batch_start
                match_rate = (len(matches) / len(wine_batch)) * 100 if len(wine_batch) > 0 else 0
                
                logger.info(f"Batch {batch_count} complete: {len(matches)} matches "
                           f"({match_rate:.1f}% rate, {batch_time:.1f}s)")
                
                # Save cache periodically
                if batch_count % 5 == 0:
                    self.save_cache()
        
        finally:
            self.save_cache()
        
        # Final stats
        duration = datetime.now() - start_time
        final_stats = self.get_stats()
        
        logger.info("=" * 60)
        logger.info("WINE MATCHING COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Duration: {duration}")
        logger.info(f"Wines processed: {total_processed:,}")
        logger.info(f"New matches found: {total_matches:,}")
        logger.info(f"Total matched: {final_stats['matched_count']:,}")
        logger.info(f"Remaining unmatched: {final_stats['unmatched_count']:,}")
        logger.info(f"Match percentage: {final_stats['match_percentage']:.1f}%")

def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Clean Wine Matching System")
        print("Usage:")
        print("  python clean_wine_matcher.py match [batch_size] [max_batches] [threshold]")
        print("  python clean_wine_matcher.py status")
        print("  python clean_wine_matcher.py reset")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    matcher = CleanWineMatcher()
    
    if command == "match":
        batch_size = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
        max_batches = int(sys.argv[3]) if len(sys.argv) > 3 else None
        threshold = float(sys.argv[4]) if len(sys.argv) > 4 else 0.6
        matcher.run_matching(batch_size, max_batches, threshold)
    
    elif command == "status":
        stats = matcher.get_stats()
        print("=" * 50)
        print("WINE MATCHING STATUS")
        print("=" * 50)
        print(f"Total wine records:    {stats['total_wines']:,}")
        print(f"Matched records:       {stats['matched_count']:,}")
        print(f"Unmatched records:     {stats['unmatched_count']:,}")
        print(f"Match percentage:      {stats['match_percentage']:.1f}%")
        print(f"Cache size:            {len(matcher.cache):,} entries")
    
    elif command == "reset":
        response = input("This will delete all matching results. Continue? (y/N): ")
        if response.lower() == 'y':
            with sqlite3.connect(matcher.db_path) as conn:
                conn.execute("DELETE FROM matched_results")
                conn.commit()
            if os.path.exists('match_cache.pkl'):
                os.remove('match_cache.pkl')
            print("Reset complete - all matches and cache cleared")
        else:
            print("Reset cancelled")
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()