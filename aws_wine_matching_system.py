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
        self.max_records = 50000  # SODA 2.0 limit
        
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
                print(f" API reports {total:,} total records")
                
                if total > self.max_records:
                    print(f"️  API has {total:,} records but limit is {self.max_records:,}")
                    print(f"   Will fetch maximum allowed: {self.max_records:,}")
                
                return total
            return None
        except Exception as e:
            print(f" Error getting count: {e}")
            return None
    
    def fetch_chunk(self, offset: int, limit: int = 1000) -> List[Dict]:
        """Fetch a single chunk of data"""
        if self.records_fetched >= self.max_records:
            print(f"️  Hit record limit ({self.max_records:,})")
            return []
            
        # Adjust limit if we're near the max
        remaining = self.max_records - self.records_fetched
        actual_limit = min(limit, remaining)
        
        try:
            params = {'$limit': actual_limit, '$offset': offset}
            
            print(f" Fetching offset {offset:,} (limit {actual_limit})")
            response = requests.get(self.base_url, params=params, timeout=30)
            time.sleep(self.rate_delay)
            
            response.raise_for_status()
            data = response.json()
            
            self.records_fetched += len(data)
            print(f"    Got {len(data)} records (total fetched: {self.records_fetched:,})")
            
            return data
            
        except Exception as e:
            print(f" Error fetching offset {offset}: {e}")
            return []
    
    def fetch_all_data(self, max_records: Optional[int] = None) -> List[Dict]:
        """Fetch all data using offset pagination"""
        if max_records:
            self.max_records = min(self.max_records, max_records)
            
        all_data = []
        offset = 0
        chunk_size = 1000  # Max per request
        
        print(f" Starting data fetch (max {self.max_records:,} records)")
        
        while self.records_fetched < self.max_records:
            chunk = self.fetch_chunk(offset, chunk_size)
            
            if not chunk:
                print(" No more data returned")
                break
                
            all_data.extend(chunk)
            offset += len(chunk)
            
            # Progress update every 10 chunks
            if len(all_data) % 10000 == 0:
                print(f" Progress: {len(all_data):,} records collected")
            
            # If we got less than requested, we've hit the end
            if len(chunk) < chunk_size:
                print(" Reached end of dataset")
                break
        
        print(f" Data fetch complete: {len(all_data):,} records")
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
    
    def get_database_stats(self) -> Dict:
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
    
    def log_ingestion(self, start_time: datetime, records_fetched: int, 
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
        elif mode == "sample":
            max_records = max_records or 10000
            print(f" SAMPLE MODE: Limited to {max_records:,} records")
        else:
            print(f" FULL MODE: Up to {api.max_records:,} records")
        
        # Fetch data
        raw_data = api.fetch_all_data(max_records)
        
        if not raw_data:
            print(" No data fetched")
            return
        
        # Process and store data
        df = db.clean_and_prepare_data(raw_data)
        processed, new_records = db.store_data(df)
        
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