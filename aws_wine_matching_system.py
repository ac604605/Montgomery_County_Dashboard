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
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Dict, List, Optional
import logging
from dataclasses import dataclass
import hashlib
import json
import re
from difflib import SequenceMatcher
import aiohttp
import asyncio

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
    base_url: str = "https://data.montgomerycountymd.gov/resource/v76h-r7br.json"
    app_token: Optional[str] = None
    max_limit: int = 50000
    chunk_size: int = 1000
    rate_limit_delay: float = 0.1

@dataclass 
class ProcessingConfig:
    matching_threshold: float = 0.6
    enable_parallel: bool = True
    max_workers: int = 4
    cache_enabled: bool = True
    database_path: str = "wine_data.db"
    backup_enabled: bool = True

class MontgomeryCountyAPI:
    def __init__(self, config: APIConfig):
        self.config = config
        self.session = requests.Session()
        if config.app_token:
            self.session.headers.update({'X-App-Token': config.app_token})

    def fetch_data_chunk(self, offset: int, limit: int) -> List[Dict]:
        """Fetch a chunk of data with offset and limit"""
        try:
            params = {'$limit': limit, '$offset': offset}
            response = self.session.get(self.config.base_url, params=params)
            response.raise_for_status()
            time.sleep(self.config.rate_limit_delay)
            return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch chunk at offset {offset}: {e}")
            return []

    async def _fetch_chunk(self, session, offset, limit):
        url = f"{self.config.base_url}?$limit={limit}&$offset={offset}"
        async with session.get(url) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def _fetch_all_chunks(self, start, end, limit=1000, concurrency=5):
        async with aiohttp.ClientSession() as session:
            for i in range(start, end, limit * concurrency):
                tasks = [
                    self._fetch_chunk(session, offset, limit)
                    for offset in range(i, min(i + limit * concurrency, end), limit)
                ]
                for batch in await asyncio.gather(*tasks):
                    yield batch

    def fetch_all_data_streaming(self, max_records=None):
        """Synchronous generator yielding DataFrames chunk-by-chunk"""
        if max_records is None:
            max_records = self.config.max_limit

        async def wrapper():
            async for chunk in self._fetch_all_chunks(0, max_records, self.config.chunk_size):
                yield pd.DataFrame(chunk)

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        agen = wrapper()

        try:
            while True:
                chunk_df = loop.run_until_complete(agen.__anext__())
                yield chunk_df
        except StopAsyncIteration:
            loop.close()

    def clean_chunk(self, df: pd.DataFrame) -> pd.DataFrame:
        df.columns = df.columns.str.upper()
        text_columns = ['ITEM_TYPE', 'ITEM_DESCRIPTION', 'SUPPLIER']
        for col in text_columns:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip().str.upper()
        return df

class DataManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS sales_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    calendar_year TEXT,
                    cal_month_num TEXT,
                    supplier TEXT,
                    item_code TEXT,
                    item_description TEXT,
                    item_type TEXT,
                    rtl_sales TEXT,
                    rtl_transfers TEXT,
                    whs_sales TEXT,
                    data_hash TEXT UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
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
            conn.execute('''
                CREATE TABLE IF NOT EXISTS processing_watermarks (
                    data_source TEXT PRIMARY KEY,
                    last_processed_offset INTEGER,
                    last_update_time TIMESTAMP
                )
            ''')
            conn.commit()
        logger.info(f"Database initialized at {self.db_path}")

    def store_sales_chunk(self, df: pd.DataFrame) -> List[int]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM sales_data")
                start_id = cursor.fetchone()[0] + 1
                df.to_sql('sales_data', conn, if_exists='append', index=False)
                ids = list(range(start_id, start_id + len(df)))
                conn.commit()
                return ids
        except Exception as e:
            logger.error(f"Error storing sales chunk: {e}")
            return []

    def store_matches(self, matches: List[Dict]):
        if not matches:
            return
        try:
            with sqlite3.connect(self.db_path) as conn:
                pd.DataFrame(matches).to_sql('matched_results', conn, if_exists='append', index=False)
                conn.commit()
        except Exception as e:
            logger.error(f"Error storing matches: {e}")

class OptimizedWineMatcher:
    def __init__(self, config: ProcessingConfig):
        self.config = config
        self.cache = {}
        if config.cache_enabled and os.path.exists('match_cache.pkl'):
            try:
                with open('match_cache.pkl', 'rb') as f:
                    self.cache = pickle.load(f)
                logger.info(f"Loaded {len(self.cache)} cached matches")
            except Exception as e:
                logger.warning(f"Could not load cache: {e}")

    @staticmethod
    def clean_text_for_matching(text: str) -> str:
        if pd.isna(text):
            return ""
        text = str(text).upper()
        text = re.sub(r'\s*-\s*(750ML|1\.5L|375ML|187ML|3L|500ML|1L)\s*$', '', text)
        abbreviations = {
            'CH ': 'CHATEAU ', 'DOM ': 'DOMAINE ', 'S/BLC': 'SAUVIGNON BLANC',
            'P/GRIG': 'PINOT GRIGIO', 'P/GRIS': 'PINOT GRIS', 'P/NOIR': 'PINOT NOIR',
            'CAB SAV': 'CABERNET SAUVIGNON', 'CAB': 'CABERNET', 'CHARD': 'CHARDONNAY'
        }
        for abbrev, full in abbreviations.items():
            text = text.replace(abbrev, full)
        text = re.sub(r'[^\w\s]', ' ', text)
        text = ' '.join(text.split())
        return text.strip()

    def match_chunk_parallel(self, sales_chunk: pd.DataFrame, review_data: pd.DataFrame) -> List[Dict]:
        wine_sales = sales_chunk[sales_chunk['ITEM_TYPE'] == 'WINE'].copy() if 'ITEM_TYPE' in sales_chunk.columns else sales_chunk.copy()
        if len(wine_sales) == 0:
            return []

        matches = []

        if self.config.enable_parallel and len(wine_sales) > 100:
            chunk_size = max(10, len(wine_sales) // self.config.max_workers)
            chunks = [wine_sales[i:i + chunk_size] for i in range(0, len(wine_sales), chunk_size)]
            with ProcessPoolExecutor(max_workers=self.config.max_workers) as executor:
                futures = [executor.submit(self._process_wine_chunk, chunk, review_data) for chunk in chunks]
                for future in as_completed(futures):
                    matches.extend(future.result())
        else:
            matches = self._process_wine_chunk(wine_sales, review_data)

        if self.config.cache_enabled:
            for match in matches:
                if match['wine_name_extracted'] not in self.cache:
                    self.cache[match['wine_name_extracted']] = match

        return matches

    @staticmethod
    def _process_wine_chunk(wine_chunk: pd.DataFrame, review_data: pd.DataFrame) -> List[Dict]:
        matches = []
        for _, row in wine_chunk.iterrows():
            wine_name = OptimizedWineMatcher.clean_text_for_matching(row.get('ITEM_DESCRIPTION', ''))
            best_match = OptimizedWineMatcher._find_wine_match_static(wine_name, review_data)
            if best_match['match_score'] >= 0.6:
                matches.append({
                    'sales_id': row.get('id'),
                    'wine_name_extracted': best_match['wine_name'],
                    'review_match_score': best_match['match_score'],
                    'review_title': best_match.get('title', ''),
                    'review_country': best_match.get('country', ''),
                    'review_variety': best_match.get('variety', ''),
                    'review_points': best_match.get('points', 0),
                    'review_price': best_match.get('price', 0.0)
                })
        return matches

    @staticmethod
    def _find_wine_match_static(wine_name: str, review_data: pd.DataFrame) -> Dict:
        if len(wine_name) < 3:
            return {'wine_name': wine_name, 'match_score': 0}
        search_words = wine_name.split()
        mask = pd.Series([False] * len(review_data))
        for word in search_words:
            if len(word) > 2:
                mask |= review_data['title'].str.contains(word, case=False, na=False)
        potential_matches = review_data[mask].head(50)
        if potential_matches.empty:
            return {'wine_name': wine_name, 'match_score': 0}

        best_score = 0
        best_match = None
        for _, candidate in potential_matches.iterrows():
            candidate_clean = OptimizedWineMatcher.clean_text_for_matching(candidate['title'])
            score = SequenceMatcher(None, wine_name, candidate_clean).ratio()
            if score > best_score:
                best_score = score
                best_match = candidate

        if best_match is not None and best_score >= 0.6:
            return {'wine_name': wine_name, 'match_score': best_score, **best_match.to_dict()}

        return {'wine_name': wine_name, 'match_score': 0}

    def save_cache(self):
        if self.config.cache_enabled and self.cache:
            try:
                with open('match_cache.pkl', 'wb') as f:
                    pickle.dump(self.cache, f)
                logger.info(f"Saved {len(self.cache)} cached matches")
            except Exception as e:
                logger.error(f"Could not save cache: {e}")

# ------------------ Pipeline ------------------

class WineMatchingPipeline:
    def __init__(self, api_config: APIConfig, processing_config: ProcessingConfig):
        self.data_manager = DataManager(processing_config.database_path)
        self.api = MontgomeryCountyAPI(api_config)
        self.matcher = OptimizedWineMatcher(processing_config)
        self.processing_config = processing_config

    def _load_review_data(self) -> Optional[pd.DataFrame]:
        try:
            df = pd.read_csv('data/winemag-data-130k-v2.csv')
            return df
        except Exception as e:
            logger.error(f"Error loading wine review data: {e}")
            return None

    def run_full_update(self, max_records: Optional[int] = None):
        start_time = datetime.now()
        total_processed = 0
        total_matches = 0

        review_data = self._load_review_data()
        if review_data is None or review_data.empty:
            logger.error("No review data available")
            return

        try:
            chunk_count = 0
            for chunk_df in self.api.fetch_all_data_streaming(max_records):
                chunk_df = self.api.clean_chunk(chunk_df)
                sales_ids = self.data_manager.store_sales_chunk(chunk_df)
                chunk_df['id'] = sales_ids
                matches = self.matcher.match_chunk_parallel(chunk_df, review_data)
                if matches:
                    self.data_manager.store_matches(matches)
                    total_matches += len(matches)
                total_processed += len(chunk_df)
                chunk_count += 1
                if chunk_count % 5 == 0:
                    self.matcher.save_cache()
        finally:
            self.matcher.save_cache()
            logger.info(f"Full update complete: {total_processed} records processed, {total_matches} matches found")

    def run_incremental_update(self):
        with sqlite3.connect(self.data_manager.db_path) as conn:
            cursor = conn.execute(
                "SELECT last_processed_offset FROM processing_watermarks WHERE data_source='sales_data'"
            )
            row = cursor.fetchone()
            last_offset = row[0] if row else 0
            query = f"SELECT * FROM sales_data WHERE id > {last_offset} AND item_type = 'WINE' ORDER BY id ASC"
            recent_data = pd.read_sql_query(query, conn)

        if recent_data.empty:
            logger.info("No new sales data to process")
            return

        review_data = self._load_review_data()
        if review_data is None or review_data.empty:
            logger.error("No review data available; skipping incremental update")
            return

        matches = self.matcher.match_chunk_parallel(recent_data, review_data)
        if matches:
            self.data_manager.store_matches(matches)

        new_offset = recent_data['id'].max()
        with sqlite3.connect(self.data_manager.db_path) as conn:
            conn.execute("""
                INSERT INTO processing_watermarks (data_source, last_processed_offset, last_update_time)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(data_source) DO UPDATE SET
                    last_processed_offset=excluded.last_processed_offset,
                    last_update_time=CURRENT_TIMESTAMP
            """, ('sales_data', new_offset))
            conn.commit()

        logger.info(f"Incremental update complete: {len(matches)} new matches, checkpoint updated to ID {new_offset}")

# ------------------ Main ------------------

def main():
    import sys
    with open('config.json', 'r') as f:
        config_data = json.load(f)

    api_config = APIConfig(
        base_url=config_data['api']['base_url'],
        chunk_size=config_data['api']['chunk_size'],
        rate_limit_delay=config_data['api']['rate_limit_delay']
    )
    processing_config = ProcessingConfig(database_path="wine_data.db")

    pipeline = WineMatchingPipeline(api_config, processing_config)

    if len(sys.argv) > 1:
        mode = sys.argv[1]
        if mode == "full":
            pipeline.run_full_update()
        elif mode == "incremental":
            pipeline.run_incremental_update()
        elif mode == "test":
            pipeline.run_full_update(max_records=1000)
    else:
        print("Usage: python aws_wine_matching_system.py [full|incremental|test]")

if __name__ == "__main__":
    main()
