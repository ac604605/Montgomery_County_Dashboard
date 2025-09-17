#!/usr/bin/env python3
"""
Corrected Montgomery County API Ingestion
Based on official API documentation:
- Max 1,000 rows per request ($limit=1000)
- Max 50,000 total records per endpoint (SODA 2.0)
- Unlimited offset pagination ($offset=0,1000,2000,3000...)
"""

import pandas as pd
import requests
import sqlite3
import time
import hashlib
from datetime import datetime
from typing import List, Dict, Tuple, Optional

class MontgomeryCountyAPI:
    def __init__(self, base_url: str, rate_delay: float = 0.5):
        self.base_url = base_url
        self.rate_delay = rate_delay
        self.records_fetched = 0
        self.max_records_per_batch = 50000  # SODA 2.0 limit per batch
        self.total_api_records = None
        
    def get_total_count(self) -> Optional[int]:
        """Get total record count from API"""
        try:
            print(" Getting total record count...")
            response = requests.get(
                self.base_url, 
                params={'$select': 'count(*)'}, 
                timeout=30
            )
            time.sleep(self.rate_delay)
            
            response.raise_for_status()
            data = response.json()
            
            if data and len(data) > 0 and 'count' in data[0]:
                total = int(data[0]['count'])
                self.total_api_records = total
                print(f" API reports {total:,} total records")
                
                if total > self.max_records_per_batch:
                    batches_needed = (total + self.max_records_per_batch - 1) // self.max_records_per_batch
                    print(f" Will need {batches_needed} batches of {self.max_records_per_batch:,} records each")
                
                return total
            return None
        except Exception as e:
            print(f" Error getting count: {e}")
            return None
    
    def fetch_chunk(self, offset: int, limit: int = 1000, batch_limit: Optional[int] = None) -> List[Dict]:
        """Fetch a single chunk of data"""
        # Apply batch limit if specified
        if batch_limit and self.records_fetched >= batch_limit:
            return []
            
        # Adjust limit if we're near the batch limit
        if batch_limit:
            remaining = batch_limit - self.records_fetched
            actual_limit = min(limit, remaining)
        else:
            actual_limit = limit
        
        try:
            params = {'$limit': actual_limit, '$offset': offset}
            
            print(f" Fetching offset {offset:,} (limit {actual_limit})")
            response = requests.get(self.base_url, params=params, timeout=30)
            time.sleep(self.rate_delay)
            
            response.raise_for_status()
            data = response.json()
            
            self.records_fetched += len(data)
            print(f"    Got {len(data)} records (batch total: {self.records_fetched:,})")
            
            return data
            
        except Exception as e:
            print(f" Error fetching offset {offset}: {e}")
            return []
    
    def fetch_batch(self, start_offset: int = 0, max_records: Optional[int] = None) -> List[Dict]:
        """Fetch a single batch of up to 50,000 records"""
        batch_limit = max_records or self.max_records_per_batch
        self.records_fetched = 0  # Reset for this batch
        
        all_data = []
        offset = start_offset
        chunk_size = 1000  # Max per request
        
        print(f" Starting batch from offset {start_offset:,} (max {batch_limit:,} records)")
        
        while self.records_fetched < batch_limit:
            chunk = self.fetch_chunk(offset, chunk_size, batch_limit)
            
            if not chunk:
                print(" No more data returned")
                break
                
            all_data.extend(chunk)
            offset += len(chunk)
            
            # Progress update every 10 chunks
            if len(all_data) % 10000 == 0:
                print(f" Batch progress: {len(all_data):,} records collected")
            
            # If we got less than requested, we've hit the end
            if len(chunk) < chunk_size:
                print(" Reached end of dataset")
                break
        
        print(f" Batch complete: {len(all_data):,} records fetched")
        return all_data
    
    def fetch_all_data_complete(self, max_records: Optional[int] = None) -> List[Dict]:
        """Fetch ALL data using multiple batches to bypass 50K limit"""
        if not self.total_api_records:
            self.get_total_count()
        
        if not self.total_api_records:
            print(" Could not determine total record count")
            return []
        
        # Determine how many records to actually fetch
        target_records = max_records or self.total_api_records
        target_records = min(target_records, self.total_api_records)
        
        print(f" Target: {target_records:,} of {self.total_api_records:,} total records")
        
        all_data = []
        current_offset = 0
        batch_num = 1
        
        while len(all_data) < target_records:
            remaining_records = target_records - len(all_data)
            batch_size = min(self.max_records_per_batch, remaining_records)
            
            print(f"\n BATCH {batch_num} (offset {current_offset:,})")
            print("-" * 40)
            
            batch_data = self.fetch_batch(current_offset, batch_size)
            
            if not batch_data:
                print(f"️  No data returned for batch {batch_num}, stopping")
                break
            
            all_data.extend(batch_data)
            current_offset += len(batch_data)
            batch_num += 1
            
            print(f" Total progress: {len(all_data):,} / {target_records:,} records")
            
            # If we got less than the batch size, we've hit the end
            if len(batch_data) < batch_size:
                print(" Reached end of available data")
                break
        
        print(f"\n COMPLETE: Fetched {len(all_data):,} records total")
        return all_data

class DatabaseManager:
    def __init__(self, db_path: str = "wine_data.db"):
        self.db_path = db_path
        self.init_database()
        
    def init_database(self):
        """Initialize database with proper schema"""
        with sqlite3.connect(self.db_path) as conn:
            # Main sales data table
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
            
            # Indexes for performance
            conn.execute('CREATE INDEX IF NOT EXISTS idx_data_hash ON sales_data (data_hash)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_date_type ON sales_data (calendar_year, cal_month_num, item_type)')
            
            # Metadata table
            conn.execute('''
                CREATE TABLE IF NOT EXISTS ingestion_metadata (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    start_time TIMESTAMP,
                    end_time TIMESTAMP,
                    records_fetched INTEGER,
                    records_stored INTEGER,
                    api_record_count INTEGER,
                    success BOOLEAN,
                    notes TEXT
                )
            ''')
            
            # Ingestion progress tracking
            conn.execute('''
                CREATE TABLE IF NOT EXISTS ingestion_progress (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    total_api_records INTEGER,
                    records_ingested INTEGER,
                    last_offset INTEGER,
                    completed_at TIMESTAMP,
                    is_complete BOOLEAN DEFAULT FALSE
                )
            ''')
            
            conn.commit()
        print(" Database initialized")
    
    def clean_and_prepare_data(self, raw_data: List[Dict]) -> pd.DataFrame:
        """Clean raw API data and prepare for storage"""
        if not raw_data:
            return pd.DataFrame()
            
        print(f" Cleaning {len(raw_data):,} records...")
        
        # Convert to DataFrame
        df = pd.DataFrame(raw_data)
        
        # Standardize column names
        df.columns = df.columns.str.upper()
        
        # Clean text columns
        text_columns = ['ITEM_TYPE', 'ITEM_DESCRIPTION', 'SUPPLIER']
        for col in text_columns:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip().str.upper()
        
        # Generate hash for deduplication
        df['data_hash'] = df.apply(self._generate_hash, axis=1)
        
        print(f" Data cleaned, {len(df)} records ready")
        return df
    
    def _generate_hash(self, row) -> str:
        """Generate unique hash for each record"""
        key_fields = ['CALENDAR_YEAR', 'CAL_MONTH_NUM', 'SUPPLIER', 'ITEM_CODE', 'ITEM_DESCRIPTION']
        hash_string = '|'.join([str(row.get(field, '')) for field in key_fields])
        return hashlib.md5(hash_string.encode()).hexdigest()
    
    def store_data(self, df: pd.DataFrame) -> Tuple[int, int]:
        """Store data with deduplication, return (total_processed, new_records)"""
        if df.empty:
            return 0, 0
            
        total_processed = len(df)
        new_records = 0
        
        print(f" Storing {total_processed:,} records...")
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Store records with deduplication
                for _, row in df.iterrows():
                    cursor = conn.execute("""
                        INSERT OR IGNORE INTO sales_data 
                        (calendar_year, cal_month_num, supplier, item_code, item_description,
                         item_type, rtl_sales, rtl_transfers, whs_sales, data_hash)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        row.get('CALENDAR_YEAR'), row.get('CAL_MONTH_NUM'),
                        row.get('SUPPLIER'), row.get('ITEM_CODE'), row.get('ITEM_DESCRIPTION'),
                        row.get('ITEM_TYPE'), row.get('RTL_SALES'), row.get('RTL_TRANSFERS'),
                        row.get('WHS_SALES'), row.get('data_hash')
                    ))
                    if cursor.rowcount > 0:
                        new_records += 1
                
                conn.commit()
                
        except Exception as e:
            print(f" Error storing data: {e}")
            raise
            
        print(f" Storage complete: {new_records:,} new records added")
        return total_processed, new_records
    
    def is_complete_ingestion_done(self) -> bool:
        """Check if we've already done a complete ingestion"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT is_complete FROM ingestion_progress 
                WHERE is_complete = TRUE 
                ORDER BY completed_at DESC 
                LIMIT 1
            """)
            result = cursor.fetchone()
            return bool(result)
    
    def get_ingestion_progress(self) -> Optional[Tuple[int, int]]:
        """Get current ingestion progress (total_api_records, records_ingested)"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT total_api_records, records_ingested 
                FROM ingestion_progress 
                ORDER BY id DESC 
                LIMIT 1
            """)
            result = cursor.fetchone()
            return result if result else None
    
    def update_ingestion_progress(self, total_api_records: int, records_ingested: int, 
                                 last_offset: int, is_complete: bool = False):
        """Update ingestion progress"""
        with sqlite3.connect(self.db_path) as conn:
            if is_complete:
                conn.execute("""
                    INSERT INTO ingestion_progress 
                    (total_api_records, records_ingested, last_offset, completed_at, is_complete)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP, TRUE)
                """, (total_api_records, records_ingested, last_offset))
            else:
                conn.execute("""
                    INSERT INTO ingestion_progress 
                    (total_api_records, records_ingested, last_offset, is_complete)
                    VALUES (?, ?, ?, FALSE)
                """, (total_api_records, records_ingested, last_offset))
            conn.commit()
        """Get current database statistics"""
        with sqlite3.connect(self.db_path) as conn:
            stats = {}
            
            # Total records
            cursor = conn.execute("SELECT COUNT(*) FROM sales_data")
            stats['total_records'] = cursor.fetchone()[0]
            
            # Wine records
            cursor = conn.execute("SELECT COUNT(*) FROM sales_data WHERE item_type = 'WINE'")
            stats['wine_records'] = cursor.fetchone()[0]
            
            # Item type breakdown
            cursor = conn.execute("""
                SELECT item_type, COUNT(*) 
                FROM sales_data 
                GROUP BY item_type 
                ORDER BY COUNT(*) DESC
            """)
            stats['item_types'] = dict(cursor.fetchall())
            
            # Date range
            cursor = conn.execute("""
                SELECT MIN(calendar_year), MAX(calendar_year),
                       COUNT(DISTINCT calendar_year || '-' || cal_month_num)
                FROM sales_data
            """)
            date_info = cursor.fetchone()
            stats['date_range'] = {
                'min_year': date_info[0],
                'max_year': date_info[1], 
                'unique_months': date_info[2]
            }
            
        return stats
    
    def get_database_stats(self) -> Dict: 
                     records_stored: int, api_count: int, success: bool, notes: str = ""):
        """Log ingestion metadata"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO ingestion_metadata 
                (start_time, end_time, records_fetched, records_stored, api_record_count, success, notes)
                VALUES (?, CURRENT_TIMESTAMP, ?, ?, ?, ?, ?)
            """, (start_time, records_fetched, records_stored, api_count, success, notes))
            conn.commit()

def run_ingestion(mode: str = "full", max_records: Optional[int] = None):
    """Run the ingestion process"""
    
    api_url = "https://data.montgomerycountymd.gov/resource/v76h-r7br.json"
    
    print(" MONTGOMERY COUNTY WINE DATA INGESTION")
    print("="*50)
    
    start_time = datetime.now()
    api = MontgomeryCountyAPI(api_url)
    db = DatabaseManager()
    
    try:
        # Get API metadata
        api_total_count = api.get_total_count()
        
        # Set limits based on mode
        if mode == "test":
            max_records = max_records or 1000
            print(f" TEST MODE: Limited to {max_records:,} records")
            raw_data = api.fetch_batch(0, max_records)
        elif mode == "sample":
            max_records = max_records or 10000
            print(f" SAMPLE MODE: Limited to {max_records:,} records")
            raw_data = api.fetch_batch(0, max_records)
        else:
            # Check if complete ingestion already done
            if db.is_complete_ingestion_done():
                print(" Complete ingestion already done!")
                progress = db.get_ingestion_progress()
                if progress:
                    print(f" Database has {progress[1]:,} of {progress[0]:,} API records")
                return
            
            print(f" FULL MODE: Fetching ALL {api_total_count:,} records")
            raw_data = api.fetch_all_data_complete()
        
        # Fetch data
        if not raw_data:
            print(" No data fetched")
            return
        
        if not raw_data:
            print(" No data fetched")
            return
        
        # Process and store data
        df = db.clean_and_prepare_data(raw_data)
        processed, new_records = db.store_data(df)
        
        # Update progress tracking
        if mode == "full":
            db.update_ingestion_progress(
                api_total_count or 0, 
                new_records, 
                len(raw_data), 
                is_complete=True
            )
        
        # Get final stats
        stats = db.get_database_stats()
        
        # Log the ingestion
        db.log_ingestion(start_time, len(raw_data), new_records, 
                        api_total_count or 0, True, f"Mode: {mode}")
        
        # Final report
        duration = datetime.now() - start_time
        print("\n" + "="*50)
        print(" INGESTION COMPLETE")
        print("-"*50)
        print(f"️  Duration: {duration}")
        print(f" Records Fetched: {len(raw_data):,}")
        print(f" Records Processed: {processed:,}")
        print(f" New Records Added: {new_records:,}")
        print(f" Total DB Records: {stats['total_records']:,}")
        print(f" Wine Records: {stats['wine_records']:,}")
        
        if stats['item_types']:
            print(f"\n Item Types:")
            for item_type, count in stats['item_types'].items():
                percentage = (count / stats['total_records'] * 100) if stats['total_records'] > 0 else 0
                print(f"   {item_type:<15} {count:>8,} ({percentage:>5.1f}%)")
        
        print(f"\n Date Range: {stats['date_range']['min_year']} to {stats['date_range']['max_year']}")
        print(f" Unique Months: {stats['date_range']['unique_months']}")
        
    except Exception as e:
        print(f" Ingestion failed: {e}")
        db.log_ingestion(start_time, 0, 0, 0, False, str(e))
        raise

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python corrected_montgomery_api.py test      # Test with 1,000 records")
        print("  python corrected_montgomery_api.py sample    # Sample with 10,000 records") 
        print("  python corrected_montgomery_api.py full      # Full ingestion (up to 50,000)")
        print("  python corrected_montgomery_api.py test 500  # Test with custom limit")
        sys.exit(1)
    
    mode = sys.argv[1].lower()
    max_records = int(sys.argv[2]) if len(sys.argv) > 2 else None
    
    if mode in ["test", "sample", "full"]:
        run_ingestion(mode, max_records)
    else:
        print(f"Unknown mode: {mode}")
        sys.exit(1)