"""
Enhanced Wine Review Matching System - AWS EC2 Optimized
File: aws_wine_matching_system.py

Optimized for cloud deployment with:
- API data fetching with pagination
- Chunked processing for memory efficiency  
- Automated scheduling capabilities
- Database persistence
- Parallel processing options
"""

import pandas as pd
import numpy as np
import requests
import time
import sqlite3
import pickle
import os
from datetime import datetime, timedelta
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Dict, List, Optional, Tuple, Generator
import logging
from dataclasses import dataclass
import hashlib
import json
import re
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


@dataclass
class APIConfig:
    """Configuration for Montgomery County API"""
    base_url: str = "https://data.montgomerycountymd.gov/resource/v76h-r7br.json"
    app_token: str = None  # Add your app token here for higher rate limits
    max_limit: int = 50000  # SODA 2.1 endpoint limit
    chunk_size: int = 10000  # Optimal chunk size for processing
    rate_limit_delay: float = 0.1  # Delay between API calls


@dataclass 
class ProcessingConfig:
    """Configuration for processing parameters"""
    matching_threshold: float = 0.6
    enable_parallel: bool = True
    max_workers: int = 4
    cache_enabled: bool = True
    database_path: str = "wine_data.db"
    backup_enabled: bool = True


class MontgomeryCountyAPI:
    """Handle API calls to Montgomery County alcohol sales data"""
    
    def __init__(self, config: APIConfig):
        self.config = config
        self.session = requests.Session()
        if config.app_token:
            self.session.headers.update({'X-App-Token': config.app_token})
    
    def get_total_records(self) -> int:
        """Get total number of records available"""
        try:
            # Use $select=count(*) to get total count efficiently
            url = f"{self.config.base_url}?$select=count(*)"
            response = self.session.get(url)
            response.raise_for_status()
            
            data = response.json()
            return int(data[0]['count'])
        except Exception as e:
            logger.error(f"Failed to get total record count: {e}")
            return 0
    
    def fetch_data_chunk(self, offset: int, limit: int) -> List[Dict]:
        """Fetch a chunk of data with offset and limit"""
        try:
            params = {
                '$limit': limit,
                '$offset': offset,
                '$order': 'date DESC'  # Get most recent data first
            }
            
            response = self.session.get(self.config.base_url, params=params)
            response.raise_for_status()
            
            time.sleep(self.config.rate_limit_delay)  # Rate limiting
            return response.json()
            
        except Exception as e:
            logger.error(f"Failed to fetch chunk at offset {offset}: {e}")
            return []
    
    def fetch_all_data(self, max_records: Optional[int] = None) -> Generator[pd.DataFrame, None, None]:
        """
        Fetch all data in chunks, yielding DataFrames
        
        Args:
            max_records: Maximum records to fetch (None for all)
            
        Yields:
            DataFrame chunks
        """
        total_records = self.get_total_records()
        if max_records:
            total_records = min(total_records, max_records)
        
        logger.info(f"Fetching {total_records:,} records from Montgomery County API")
        
        offset = 0
        chunk_size = min(self.config.chunk_size, total_records)
        
        while offset < total_records:
            current_limit = min(chunk_size, total_records - offset)
            
            logger.info(f"Fetching records {offset:,} to {offset + current_limit:,}")
            
            chunk_data = self.fetch_data_chunk(offset, current_limit)
            
            if not chunk_data:
                logger.warning(f"No data returned for offset {offset}")
                break
            
            df_chunk = pd.DataFrame(chunk_data)
            
            # Basic data cleaning
            df_chunk = self.clean_chunk(df_chunk)
            
            yield df_chunk
            
            offset += current_limit
    
    def clean_chunk(self, df: pd.DataFrame) -> pd.DataFrame:
        """Basic cleaning for API data chunk"""
        # Standardize column names
        df.columns = df.columns.str.upper().str.replace(' ', '_')
        
        # Convert date columns
        date_columns = ['DATE']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # Clean text columns
        text_columns = ['ITEM_TYPE', 'ITEM_DESCRIPTION', 'SUPPLIER']
        for col in text_columns:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip().str.upper()
        
        return df


class DataManager:
    """Handle database operations and data persistence"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database with required tables"""
        conn = sqlite3.connect(self.db_path)
        
        # Sales data table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS sales_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                item_type TEXT,
                item_description TEXT,
                supplier TEXT,
                item_code TEXT,
                year INTEGER,
                month INTEGER,
                data_hash TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Matched results table
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
        
        # Processing metadata
        conn.execute('''
            CREATE TABLE IF NOT EXISTS processing_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                process_type TEXT,
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                records_processed INTEGER,
                matches_found INTEGER,
                success BOOLEAN,
                notes TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info(f"Database initialized at {self.db_path}")
    
    def store_sales_chunk(self, df: pd.DataFrame) -> List[int]:
        """Store sales data chunk and return list of IDs"""
        conn = sqlite3.connect(self.db_path)
        
        # Add data hash for deduplication
        df['data_hash'] = df.apply(
            lambda row: hashlib.md5(
                str(row.to_dict()).encode()
            ).hexdigest(), axis=1
        )
        
        try:
            # Insert with IGNORE to handle duplicates
            df.to_sql('sales_data', conn, if_exists='append', index=False, method='replace')
            
            # Get the IDs of inserted records
            cursor = conn.execute(
                "SELECT id FROM sales_data WHERE data_hash IN ({})".format(
                    ','.join(['?' for _ in df['data_hash']])
                ), df['data_hash'].tolist()
            )
            
            ids = [row[0] for row in cursor.fetchall()]
            conn.commit()
            return ids
            
        except Exception as e:
            logger.error(f"Error storing sales chunk: {e}")
            return []
        finally:
            conn.close()
    
    def get_recent_sales_data(self, days: int = 30) -> pd.DataFrame:
        """Get recent sales data for incremental updates"""
        conn = sqlite3.connect(self.db_path)
        
        query = """
            SELECT * FROM sales_data 
            WHERE created_at >= datetime('now', '-{} days')
            AND item_type = 'WINE'
            ORDER BY created_at DESC
        """.format(days)
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    
    def store_matches(self, matches: List[Dict]):
        """Store matching results"""
        conn = sqlite3.connect(self.db_path)
        
        df_matches = pd.DataFrame(matches)
        df_matches.to_sql('matched_results', conn, if_exists='append', index=False)
        
        conn.commit()
        conn.close()


class OptimizedWineMatcher:
    """Optimized wine matching with parallel processing and caching"""
    
    def __init__(self, config: ProcessingConfig):
        self.config = config
        self.cache = {}
        
        # Load cache if it exists
        if config.cache_enabled and os.path.exists('match_cache.pkl'):
            try:
                with open('match_cache.pkl', 'rb') as f:
                    self.cache = pickle.load(f)
                logger.info(f"Loaded {len(self.cache)} cached matches")
            except Exception as e:
                logger.warning(f"Could not load cache: {e}")
    
    def clean_text_for_matching(self, text: str) -> str:
        """Enhanced text cleaning for matching"""
        if pd.isna(text):
            return ""
        
        text = str(text).upper()
        
        # Remove volume indicators
        text = re.sub(r'\s*-\s*(750ML|1\.5L|375ML|187ML|3L|500ML|1L)\s*$', '', text)
        
        # Expand common abbreviations
        abbreviations = {
            'CH ': 'CHATEAU ', 'DOM ': 'DOMAINE ', 'S/BLC': 'SAUVIGNON BLANC',
            'P/GRIG': 'PINOT GRIGIO', 'P/GRIS': 'PINOT GRIS', 'P/NOIR': 'PINOT NOIR',
            'CAB SAV': 'CABERNET SAUVIGNON', 'CAB': 'CABERNET', 'CHARD': 'CHARDONNAY'
        }
        
        for abbrev, full_form in abbreviations.items():
            text = text.replace(abbrev, full_form)
        
        # Clean punctuation and extra spaces
        text = re.sub(r'[^\w\s]', ' ', text)
        text = ' '.join(text.split())
        
        return text.strip()
    
    def match_chunk_parallel(self, sales_chunk: pd.DataFrame, 
                           review_data: pd.DataFrame) -> List[Dict]:
        """Match a chunk of sales data against reviews using parallel processing"""
        
        wine_sales = sales_chunk[sales_chunk['ITEM_TYPE'] == 'WINE'].copy()
        
        if len(wine_sales) == 0:
            return []
        
        matches = []
        cache_hits = 0
        
        if self.config.enable_parallel and len(wine_sales) > 100:
            # Use parallel processing for large chunks
            chunk_size = max(10, len(wine_sales) // self.config.max_workers)
            chunks = [wine_sales[i:i+chunk_size] for i in range(0, len(wine_sales), chunk_size)]
            
            with ProcessPoolExecutor(max_workers=self.config.max_workers) as executor:
                futures = [
                    executor.submit(self._process_wine_chunk, chunk, review_data)
                    for chunk in chunks
                ]
                
                for future in as_completed(futures):
                    chunk_matches = future.result()
                    matches.extend(chunk_matches)
        else:
            # Sequential processing for smaller chunks
            matches = self._process_wine_chunk(wine_sales, review_data)
        
        return matches
    
    def _process_wine_chunk(self, wine_chunk: pd.DataFrame, 
                          review_data: pd.DataFrame) -> List[Dict]:
        """Process a single chunk of wine data"""
        matches = []
        
        for _, row in wine_chunk.iterrows():
            item_desc = row['ITEM_DESCRIPTION']
            
            # Check cache first
            if item_desc in self.cache:
                match_result = self.cache[item_desc]
            else:
                # Find match
                wine_name = self.clean_text_for_matching(item_desc)
                match_result = self._find_wine_match(wine_name, review_data)
                
                # Cache result
                if self.config.cache_enabled:
                    self.cache[item_desc] = match_result
            
            if match_result['match_score'] >= self.config.matching_threshold:
                match_dict = {
                    'sales_id': row.get('id'),
                    'wine_name_extracted': match_result['wine_name'],
                    'review_match_score': match_result['match_score'],
                    'review_title': match_result.get('title', ''),
                    'review_country': match_result.get('country', ''),
                    'review_variety': match_result.get('variety', ''),
                    'review_points': match_result.get('points', 0),
                    'review_price': match_result.get('price', 0.0)
                }
                matches.append(match_dict)
        
        return matches
    
    def _find_wine_match(self, wine_name: str, review_data: pd.DataFrame) -> Dict:
        """Find best matching wine review"""
        if len(wine_name) < 3:
            return {'wine_name': wine_name, 'match_score': 0}
        
        # Pre-filter using vectorized string operations
        search_words = wine_name.split()
        if not search_words:
            return {'wine_name': wine_name, 'match_score': 0}
        
        # Create boolean mask for potential matches
        mask = pd.Series([False] * len(review_data))
        
        for word in search_words:
            if len(word) > 2:
                mask |= review_data['title'].str.contains(word, case=False, na=False)
        
        potential_matches = review_data[mask].head(50)  # Limit for performance
        
        if len(potential_matches) == 0:
            return {'wine_name': wine_name, 'match_score': 0}
        
        # Find best match using vectorized operations
        best_score = 0
        best_match = None
        
        for _, candidate in potential_matches.iterrows():
            candidate_clean = self.clean_text_for_matching(candidate['title'])
            score = SequenceMatcher(None, wine_name, candidate_clean).ratio()
            
            if score > best_score:
                best_score = score
                best_match = candidate
        
        if best_match is not None and best_score >= self.config.matching_threshold:
            return {
                'wine_name': wine_name,
                'match_score': best_score,
                **best_match.to_dict()
            }
        
        return {'wine_name': wine_name, 'match_score': 0}
    
    def save_cache(self):
        """Save matching cache to disk"""
        if self.config.cache_enabled and self.cache:
            try:
                with open('match_cache.pkl', 'wb') as f:
                    pickle.dump(self.cache, f)
                logger.info(f"Saved {len(self.cache)} cached matches")
            except Exception as e:
                logger.error(f"Could not save cache: {e}")


class WineMatchingPipeline:
    """Main pipeline orchestrator"""
    
    def __init__(self, api_config: APIConfig, processing_config: ProcessingConfig):
        self.api = MontgomeryCountyAPI(api_config)
        self.data_manager = DataManager(processing_config.database_path)
        self.matcher = OptimizedWineMatcher(processing_config)
        self.processing_config = processing_config
    
    def run_full_update(self, max_records: Optional[int] = None):
        """Run complete data update and matching process"""
        start_time = datetime.now()
        total_processed = 0
        total_matches = 0
        
        logger.info("Starting full wine matching pipeline")
        
        # Load review data (assuming it's static or updated separately)
        review_data = self._load_review_data()
        
        if review_data is None or len(review_data) == 0:
            logger.error("No review data available")
            return
        
        try:
            # Process data in chunks
            for chunk_df in self.api.fetch_all_data(max_records):
                logger.info(f"Processing chunk with {len(chunk_df)} records")
                
                # Store sales data
                sales_ids = self.data_manager.store_sales_chunk(chunk_df)
                
                # Add IDs to chunk for matching
                chunk_df['id'] = sales_ids
                
                # Match wines in this chunk
                matches = self.matcher.match_chunk_parallel(chunk_df, review_data)
                
                # Store matches
                if matches:
                    self.data_manager.store_matches(matches)
                    total_matches += len(matches)
                
                total_processed += len(chunk_df)
                logger.info(f"Chunk complete: {len(matches)} matches found")
            
            # Save cache
            self.matcher.save_cache()
            
            end_time = datetime.now()
            duration = end_time - start_time
            
            # Log completion
            self._log_processing_metadata(
                'full_update', start_time, end_time,
                total_processed, total_matches, True,
                f"Processed {total_processed:,} records, found {total_matches:,} matches"
            )
            
            logger.info(f"Pipeline complete: {total_processed:,} records processed, "
                       f"{total_matches:,} matches found in {duration}")
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            self._log_processing_metadata(
                'full_update', start_time, datetime.now(),
                total_processed, total_matches, False, str(e)
            )
            raise
    
    def run_incremental_update(self, days: int = 7):
        """Run incremental update for recent data"""
        logger.info(f"Running incremental update for last {days} days")
        
        # Get recent unmatched data
        recent_data = self.data_manager.get_recent_sales_data(days)
        
        if len(recent_data) == 0:
            logger.info("No recent data to process")
            return
        
        # Load review data
        review_data = self._load_review_data()
        
        # Match recent wines
        matches = self.matcher.match_chunk_parallel(recent_data, review_data)
        
        # Store matches
        if matches:
            self.data_manager.store_matches(matches)
        
        logger.info(f"Incremental update complete: {len(matches)} new matches")
    
    def _load_review_data(self) -> Optional[pd.DataFrame]:
        """Load wine review data from Kaggle dataset or cached file"""
        # This would load your Kaggle wine review dataset
        # You could implement caching, database storage, or API fetching here
        try:
            # Example implementation - adjust path as needed
            return pd.read_csv('wine_reviews.csv')
        except FileNotFoundError:
            logger.error("Wine review data not found - download from Kaggle first")
            return None
    
    def _log_processing_metadata(self, process_type: str, start_time: datetime,
                               end_time: datetime, records_processed: int,
                               matches_found: int, success: bool, notes: str):
        """Log processing metadata to database"""
        conn = sqlite3.connect(self.data_manager.db_path)
        
        metadata = {
            'process_type': process_type,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'records_processed': records_processed,
            'matches_found': matches_found,
            'success': success,
            'notes': notes
        }
        
        df_meta = pd.DataFrame([metadata])
        df_meta.to_sql('processing_metadata', conn, if_exists='append', index=False)
        conn.commit()
        conn.close()


# Example usage and configuration
def main():
    """Main execution function"""
    
    # Configuration
    api_config = APIConfig(
        app_token="YOUR_APP_TOKEN_HERE",  # Get from https://dev.socrata.com/
        chunk_size=5000,  # Smaller chunks for memory efficiency
        rate_limit_delay=0.1
    )
    
    processing_config = ProcessingConfig(
        matching_threshold=0.6,
        enable_parallel=True,
        max_workers=4,
        cache_enabled=True,
        database_path="wine_data.db"
    )
    
    # Create pipeline
    pipeline = WineMatchingPipeline(api_config, processing_config)
    
    # Run different update types based on schedule
    import sys
    
    if len(sys.argv) > 1:
        mode = sys.argv[1]
        if mode == "full":
            pipeline.run_full_update()
        elif mode == "incremental":
            pipeline.run_incremental_update(days=7)
        elif mode == "test":
            pipeline.run_full_update(max_records=1000)  # Test with 1000 records
    else:
        print("Usage: python aws_wine_matching_system.py [full|incremental|test]")


if __name__ == "__main__":
    main()