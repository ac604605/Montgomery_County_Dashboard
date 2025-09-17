#!/usr/bin/env python3
"""
Enhanced Wine Review Matching System
Incorporates advanced fuzzy matching logic from supplier matching system
- Weighted scoring combining sequential and word-overlap similarity
- Sophisticated text cleaning and normalization
- Caching system for duplicate wine names
- Progress tracking and performance optimization
"""

import pandas as pd
import sqlite3
import pickle
import os
import re
import time
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Dict, List, Optional, Tuple
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

class EnhancedWineMatcher:
    def __init__(self, db_path: str = "wine_data.db", enable_parallel: bool = True, max_workers: int = 4):
        self.db_path = db_path
        self.enable_parallel = enable_parallel
        self.max_workers = max_workers
        self.cache = {}
        self.wine_name_cache = {}  # New: cache for cleaned wine names
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
            logger.info(f"Loaded {len(df):,} wine reviews")
            return df
        except Exception as e:
            logger.error(f"Error loading wine review data: {e}")
            return None
    
    def clean_wine_name(self, name: str) -> str:
        """
        Enhanced wine name cleaning based on supplier matching logic
        """
        if pd.isna(name) or not name:
            return ""
        
        name = str(name).upper().strip()
        
        # Remove volume indicators and common wine suffixes
        volume_patterns = [
            r'\s*-?\s*(750ML|1\.5L|375ML|187ML|3L|500ML|1L|750|1500|375)\s*$',
            r'\s*-?\s*(ML|L)\s*$',
            r'\s+\d+\s*(ML|L)\s*$'
        ]
        for pattern in volume_patterns:
            name = re.sub(pattern, '', name)
        
        # Remove common wine descriptors that don't help matching
        descriptors_to_remove = [
            ' WINE', ' RED', ' WHITE', ' ROSE', ' SPARKLING', ' BOTTLE', ' BTL',
            ' DRY', ' SWEET', ' RESERVE', ' SPECIAL', ' VINTAGE', ' CLASSIC',
            ' TRADITIONAL', ' PREMIUM', ' SELECT', ' COLLECTION'
        ]
        for descriptor in descriptors_to_remove:
            if name.endswith(descriptor):
                name = name[:-len(descriptor)].strip()
        
        # Expand wine abbreviations (more comprehensive than before)
        abbreviations = {
            'CH ': 'CHATEAU ', 'CH.': 'CHATEAU', 'CHÂT': 'CHATEAU',
            'DOM ': 'DOMAINE ', 'DOM.': 'DOMAINE', 'DOMN': 'DOMAINE',
            'S/BLC': 'SAUVIGNON BLANC', 'SAUV BLANC': 'SAUVIGNON BLANC', 'SB': 'SAUVIGNON BLANC',
            'P/GRIG': 'PINOT GRIGIO', 'P/GRIS': 'PINOT GRIS', 'P/NOIR': 'PINOT NOIR', 'PN': 'PINOT NOIR',
            'CAB SAV': 'CABERNET SAUVIGNON', 'CAB': 'CABERNET', 'CS': 'CABERNET SAUVIGNON',
            'CHARD': 'CHARDONNAY', 'MERLOT': 'MERLOT', 'SHIRAZ': 'SYRAH',
            'TEMP': 'TEMPRANILLO', 'SANG': 'SANGIOVESE', 'BARBERA': 'BARBERA',
            'RIESLING': 'RIESLING', 'GEWURZ': 'GEWURZTRAMINER'
        }
        
        for abbrev, full in abbreviations.items():
            name = name.replace(abbrev, full)
        
        # Remove punctuation and normalize (like supplier matching)
        name = name.replace('.', ' ').replace(',', ' ').replace('-', ' ').replace('&', 'AND')
        name = re.sub(r'[^\w\s]', ' ', name)
        name = ' '.join(name.split())  # Normalize whitespace
        
        return name.strip()
    
    def find_best_wine_match(self, wine_name: str, review_data: pd.DataFrame, threshold: float = 0.6) -> Dict:
        """
        Enhanced wine matching using weighted scoring like supplier matching
        """
        if len(wine_name) < 3:
            return {'wine_name': wine_name, 'match_score': 0}
        
        # Check cache first
        if wine_name in self.cache:
            cached_match = self.cache[wine_name]
            if cached_match.get('match_score', 0) >= threshold:
                return cached_match
        
        # Clean the wine name for matching
        wine_clean = self.clean_wine_name(wine_name)
        if len(wine_clean) < 3:
            return {'wine_name': wine_name, 'match_score': 0}
        
        # Create search mask (improved from original)
        search_words = [word for word in wine_clean.split() if len(word) > 2]
        if not search_words:
            return {'wine_name': wine_name, 'match_score': 0}
        
        # Find potential matches using word-based filtering
        mask = pd.Series([False] * len(review_data))
        for word in search_words:
            mask |= review_data['title'].str.contains(word, case=False, na=False)
        
        potential_matches = review_data[mask].head(100)
        
        if potential_matches.empty:
            return {'wine_name': wine_name, 'match_score': 0}
        
        # Find best match using enhanced scoring
        best_score = 0
        best_match = None
        wine_words = set(wine_clean.split())
        
        for _, candidate in potential_matches.iterrows():
            candidate_clean = self.clean_wine_name(candidate['title'])
            candidate_words = set(candidate_clean.split())
            
            if not candidate_clean:
                continue
            
            # Calculate sequential similarity (like original)
            seq_score = SequenceMatcher(None, wine_clean, candidate_clean).ratio()
            
            # Calculate word overlap similarity (like supplier matching)
            if wine_words and candidate_words:
                word_overlap = len(wine_words.intersection(candidate_words)) / len(wine_words.union(candidate_words))
            else:
                word_overlap = 0
            
            # Weighted combination (like supplier matching)
            combined_score = (seq_score * 0.7) + (word_overlap * 0.3)
            
            # Additional bonus for producer/brand name matches
            wine_first_word = wine_clean.split()[0] if wine_clean.split() else ""
            candidate_first_word = candidate_clean.split()[0] if candidate_clean.split() else ""
            
            if (len(wine_first_word) > 3 and len(candidate_first_word) > 3 and 
                wine_first_word == candidate_first_word):
                combined_score += 0.1  # Brand name match bonus
            
            if combined_score > best_score and combined_score >= threshold:
                best_score = combined_score
                best_match = candidate
        
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
            
            # Cache the result
            self.cache[wine_name] = result
            return result
        
        return {'wine_name': wine_name, 'match_score': 0}
    
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
        
        return df
    
    def process_wine_batch_enhanced(self, wine_batch: pd.DataFrame, review_data: pd.DataFrame, 
                                   threshold: float = 0.6) -> List[Dict]:
        """
        Process a batch of wine records using enhanced matching
        Includes caching for duplicate wine names (like supplier matching)
        """
        matches = []
        unique_wine_cache = {}  # Local cache for this batch
        
        for _, row in wine_batch.iterrows():
            raw_wine_name = row.get('item_description', '')
            
            if pd.isna(raw_wine_name) or len(str(raw_wine_name).strip()) < 3:
                continue
            
            wine_name = str(raw_wine_name).strip()
            
            # Check if we've already processed this exact wine name in this batch
            if wine_name in unique_wine_cache:
                match_result = unique_wine_cache[wine_name]
            else:
                match_result = self.find_best_wine_match(wine_name, review_data, threshold)
                unique_wine_cache[wine_name] = match_result
            
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
    
    def get_matching_stats(self) -> Dict:
        """Get current matching statistics"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM sales_data WHERE item_type = 'WINE'")
            total_wines = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT COUNT(*) FROM matched_results")
            matched_count = cursor.fetchone()[0]
            
            cursor = conn.execute("""
                SELECT COUNT(*) FROM sales_data s
                LEFT JOIN matched_results m ON s.id = m.sales_id
                WHERE s.item_type = 'WINE' AND m.sales_id IS NULL
            """)
            unmatched_count = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT AVG(review_match_score) FROM matched_results")
            avg_score = cursor.fetchone()[0] or 0
            
            # Score distribution
            cursor = conn.execute("""
                SELECT 
                    COUNT(CASE WHEN review_match_score >= 0.9 THEN 1 END) as excellent,
                    COUNT(CASE WHEN review_match_score >= 0.8 AND review_match_score < 0.9 THEN 1 END) as very_good,
                    COUNT(CASE WHEN review_match_score >= 0.7 AND review_match_score < 0.8 THEN 1 END) as good,
                    COUNT(CASE WHEN review_match_score >= 0.6 AND review_match_score < 0.7 THEN 1 END) as acceptable
                FROM matched_results
            """)
            score_dist = cursor.fetchone()
        
        return {
            'total_wines': total_wines,
            'matched_count': matched_count,
            'unmatched_count': unmatched_count,
            'match_percentage': (matched_count / total_wines * 100) if total_wines > 0 else 0,
            'average_score': avg_score,
            'score_distribution': {
                'excellent (0.9+)': score_dist[0] if score_dist else 0,
                'very_good (0.8-0.9)': score_dist[1] if score_dist else 0,
                'good (0.7-0.8)': score_dist[2] if score_dist else 0,
                'acceptable (0.6-0.7)': score_dist[3] if score_dist else 0
            }
        }
    
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
    
    def run_enhanced_matching(self, batch_size: int = 1000, max_batches: Optional[int] = None, 
                            threshold: float = 0.6, test_mode: bool = False):
        """Run the enhanced matching process"""
        start_time = datetime.now()
        
        # Load review data
        review_data = self.load_review_data()
        if review_data is None:
            logger.error("Cannot proceed without wine review data")
            return
        
        # Get initial stats
        initial_stats = self.get_matching_stats()
        logger.info(f"Enhanced matching starting: {initial_stats['unmatched_count']:,} unmatched wines")
        logger.info(f"Using threshold: {threshold}, batch size: {batch_size}")
        
        if initial_stats['unmatched_count'] == 0:
            logger.info("No unmatched wines found - matching complete!")
            return
        
        if test_mode:
            max_batches = 1
            batch_size = min(batch_size, 100)
            logger.info(f"TEST MODE: Processing {batch_size} wines only")
        
        total_processed = 0
        total_matches = 0
        batch_count = 0
        
        try:
            while True:
                if max_batches and batch_count >= max_batches:
                    logger.info(f"Reached batch limit ({max_batches})")
                    break
                
                wine_batch = self.get_unmatched_wines(batch_size)
                
                if wine_batch.empty:
                    logger.info("No more unmatched wines found")
                    break
                
                batch_start = time.time()
                logger.info(f"Processing batch {batch_count + 1}: {len(wine_batch)} wines")
                
                # Process batch with enhanced matching
                if self.enable_parallel and len(wine_batch) > 50 and not test_mode:
                    chunk_size = max(10, len(wine_batch) // self.max_workers)
                    chunks = [wine_batch[i:i + chunk_size] for i in range(0, len(wine_batch), chunk_size)]
                    
                    all_matches = []
                    with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
                        futures = [executor.submit(self.process_wine_batch_enhanced, chunk, review_data, threshold) 
                                 for chunk in chunks]
                        for future in as_completed(futures):
                            all_matches.extend(future.result())
                else:
                    all_matches = self.process_wine_batch_enhanced(wine_batch, review_data, threshold)
                
                # Store matches
                if all_matches:
                    self.store_matches(all_matches)
                    total_matches += len(all_matches)
                
                total_processed += len(wine_batch)
                batch_count += 1
                
                batch_time = time.time() - batch_start
                match_rate = (len(all_matches) / len(wine_batch)) * 100
                
                logger.info(f"Batch {batch_count} complete: {len(all_matches)} matches "
                           f"({match_rate:.1f}% rate, {batch_time:.1f}s)")
                
                # Save cache periodically
                if batch_count % 5 == 0:
                    self.save_cache()
        
        finally:
            self.save_cache()
        
        # Final statistics
        duration = datetime.now() - start_time
        final_stats = self.get_matching_stats()
        
        logger.info("=" * 70)
        logger.info("ENHANCED WINE MATCHING COMPLETE")
        logger.info("=" * 70)
        logger.info(f"Duration: {duration}")
        logger.info(f"Wines processed: {total_processed:,}")
        logger.info(f"New matches found: {total_matches:,}")
        logger.info(f"Total wines: {final_stats['total_wines']:,}")
        logger.info(f"Total matched: {final_stats['matched_count']:,}")
        logger.info(f"Remaining unmatched: {final_stats['unmatched_count']:,}")
        logger.info(f"Match percentage: {final_stats['match_percentage']:.1f}%")
        logger.info(f"Average match score: {final_stats['average_score']:.3f}")
        
        # Score distribution
        score_dist = final_stats['score_distribution']
        logger.info("Score distribution:")
        for category, count in score_dist.items():
            logger.info(f"  {category}: {count:,}")

def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Enhanced Wine Matching System")
        print("Usage:")
        print("  python enhanced_wine_matcher.py match                    # Run enhanced matching")
        print("  python enhanced_wine_matcher.py match 1000              # Custom batch size")
        print("  python enhanced_wine_matcher.py match 1000 10           # Batch size + max batches")
        print("  python enhanced_wine_matcher.py match 1000 10 0.7       # + custom threshold")
        print("  python enhanced_wine_matcher.py test                    # Test enhanced matching")
        print("  python enhanced_wine_matcher.py status                  # Show matching stats")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    matcher = EnhancedWineMatcher()
    
    if command == "match":
        batch_size = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
        max_batches = int(sys.argv[3]) if len(sys.argv) > 3 else None
        threshold = float(sys.argv[4]) if len(sys.argv) > 4 else 0.6
        matcher.run_enhanced_matching(batch_size, max_batches, threshold)
    
    elif command == "test":
        batch_size = int(sys.argv[2]) if len(sys.argv) > 2 else 100
        threshold = float(sys.argv[3]) if len(sys.argv) > 3 else 0.6
        matcher.run_enhanced_matching(batch_size, test_mode=True, threshold=threshold)
    
    elif command == "status":
        stats = matcher.get_matching_stats()
        print("=" * 60)
        print("ENHANCED WINE MATCHING STATUS")
        print("=" * 60)
        print(f"Total wine records:     {stats['total_wines']:,}")
        print(f"Matched records:        {stats['matched_count']:,}")
        print(f"Unmatched records:      {stats['unmatched_count']:,}")
        print(f"Match percentage:       {stats['match_percentage']:.1f}%")
        print(f"Average match score:    {stats['average_score']:.3f}")
        print(f"Cache size:             {len(matcher.cache):,} entries")
        print("\nScore Distribution:")
        for category, count in stats['score_distribution'].items():
            print(f"  {category:<20} {count:>8,}")
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()