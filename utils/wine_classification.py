#!/usr/bin/env python3
"""
Integrated Wine Classification Pipeline
Adapted for existing wine_data.db structure
Adds classification columns to matched_results table
"""

import pandas as pd
import sqlite3
import re
import logging
from datetime import datetime
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseWineClassifier:
    """Wine classifier that works directly with the existing database structure"""
    
    def __init__(self, db_path: str = "wine_data.db"):
        self.db_path = db_path
        self._initialize_patterns()
        self.init_classification_columns()
    
    def _initialize_patterns(self):
        """Initialize classification patterns (subset from original system)"""
        
        # Core abbreviation patterns for wine varieties
        self.abbreviation_patterns = {
            r'\bCAB\b': 'Cabernet Sauvignon', r'\bCHARD\b': 'Chardonnay',
            r'\bP/GRIG\b': 'Pinot Grigio', r'\bP/NOIR\b': 'Pinot Noir',
            r'\bSAUV\b': 'Sauvignon Blanc', r'\bS/BLC\b': 'Sauvignon Blanc',
            r'\bRIESL\b': 'Riesling', r'\bMERLOT\b': 'Merlot',
            r'\bZINF\b': 'Zinfandel', r'\bMALBEC\b': 'Malbec',
            r'\bTEMP\b': 'Tempranillo', r'\bSHIRAZ\b': 'Syrah',
            r'\bMOSCATO\b': 'Moscato', r'\bCHIANTI\b': 'Sangiovese',
            r'\bPROSECCO\b': 'Prosecco'
        }
        
        # Regional patterns for variety detection
        self.regional_patterns = {
            r'\bBAROLO\b': 'Nebbiolo', r'\bBRUNELLO\b': 'Sangiovese',
            r'\bCHIANTI\b': 'Sangiovese', r'\bAMARONE\b': 'Amarone',
            r'\bVALPOLICELLA\b': 'Valpolicella', r'\bSOAVE\b': 'Soave',
            r'\bRIOJA\b': 'Tempranillo', r'\bCHABLIS\b': 'Chardonnay',
            r'\bSANCERRE\b': 'Sauvignon Blanc', r'\bBEAUJOLAIS\b': 'Gamay'
        }
        
        # Country detection patterns (key ones)
        self.country_patterns = {
            # Italian indicators
            r'\bVENETO\b': 'Italy', r'\bTUSCANY\b': 'Italy', r'\bPIEMONTE\b': 'Italy',
            r'\bCHIANTI\b': 'Italy', r'\bBAROLO\b': 'Italy', r'\bPROSECCO\b': 'Italy',
            r'\bRISERVA\b': 'Italy', r'\bROSSO\b': 'Italy', r'\bBIANCO\b': 'Italy',
            
            # French indicators
            r'\bBORDEAUX\b': 'France', r'\bBURGUNDY\b': 'France', r'\bCHAMPAGNE\b': 'France',
            r'\bCHABLIS\b': 'France', r'\bCHATEAU\b': 'France', r'\bDOMAINE\b': 'France',
            
            # Spanish indicators
            r'\bRIOJA\b': 'Spain', r'\bTEMPRANILLO\b': 'Spain', r'\bCRIANZA\b': 'Spain',
            r'\bRESERVA\b': 'Spain', r'\bTINTO\b': 'Spain',
            
            # German indicators
            r'\bRIESLING\b': 'Germany', r'\bMOSEL\b': 'Germany', r'\bKABINETT\b': 'Germany',
            
            # US indicators
            r'\bNAPA\b': 'US', r'\bSONOMA\b': 'US', r'\bCALIFORNIA\b': 'US',
            r'\bOREGON\b': 'US', r'\bWASHINGTON\b': 'US'
        }
        
        # Wine color classification
        self.color_classification = {
            'red_varieties': {
                'cabernet sauvignon', 'merlot', 'pinot noir', 'malbec', 'syrah', 'shiraz',
                'zinfandel', 'tempranillo', 'sangiovese', 'nebbiolo', 'cabernet franc',
                'chianti', 'red blend', 'gamay', 'barbera', 'amarone', 'valpolicella'
            },
            'white_varieties': {
                'chardonnay', 'sauvignon blanc', 'pinot grigio', 'riesling', 'moscato',
                'white blend', 'albariño', 'viognier', 'gewürztraminer', 'chenin blanc',
                'soave', 'prosecco'
            },
            'sparkling_varieties': {
                'prosecco', 'champagne', 'sparkling', 'brut', 'cava'
            }
        }
    
    def init_classification_columns(self):
        """Add classification columns to matched_results table if they don't exist"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Check if classification columns already exist
            cursor.execute("PRAGMA table_info(matched_results)")
            existing_columns = {row[1] for row in cursor.fetchall()}
            
            # Add missing columns
            new_columns = [
                ('final_variety', 'TEXT'),
                ('final_country', 'TEXT'),
                ('wine_color', 'TEXT'),
                ('extracted_variety', 'TEXT'),
                ('extracted_country', 'TEXT'),
                ('classification_confidence', 'REAL'),
                ('classification_date', 'TEXT')  # store ISO8601 strings
            ]
            
            for col_name, col_type in new_columns:
                if col_name not in existing_columns:
                    try:
                        cursor.execute(f"ALTER TABLE matched_results ADD COLUMN {col_name} {col_type}")
                        logger.info(f"Added column: {col_name}")
                    except Exception as e:
                        logger.warning(f"Could not add column {col_name}: {e}")
            
            conn.commit()
    
    def clean_text_for_classification(self, text: str) -> str:
        """Clean text for pattern matching"""
        if pd.isna(text) or not text:
            return ""
        
        text = str(text).upper().strip()
        
        # Remove volume indicators
        text = re.sub(r'\s*-?\s*(750ML|1\.5L|375ML|187ML|3L|500ML|1L|750|1500|375)\s*$', '', text)
        
        # Clean punctuation and normalize whitespace
        text = re.sub(r'[^\w\s]', ' ', text)
        text = ' '.join(text.split())
        
        return text.strip()
    
    def extract_variety_from_text(self, text: str) -> tuple:
        """Extract variety from text using patterns"""
        if not text:
            return None, 0.0
        
        clean_text = self.clean_text_for_classification(text)
        
        # Check abbreviation patterns first (higher confidence)
        for pattern, variety in self.abbreviation_patterns.items():
            if re.search(pattern, clean_text):
                return variety, 0.9
        
        # Check regional patterns
        for pattern, variety in self.regional_patterns.items():
            if re.search(pattern, clean_text):
                return variety, 0.8
        
        return None, 0.0
    
    def extract_country_from_text(self, text: str) -> tuple:
        """Extract country from text using patterns"""
        if not text:
            return None, 0.0
        
        clean_text = self.clean_text_for_classification(text)
        
        for pattern, country in self.country_patterns.items():
            if re.search(pattern, clean_text):
                return country, 0.85
        
        return None, 0.0
    
    def classify_wine_color(self, variety: str) -> str:
        """Classify wine color based on variety"""
        if not variety:
            return 'Unclassified'
        
        variety_lower = variety.lower()
        
        if variety_lower in self.color_classification['sparkling_varieties']:
            return 'Sparkling'
        elif variety_lower in self.color_classification['red_varieties']:
            return 'Red'
        elif variety_lower in self.color_classification['white_varieties']:
            return 'White'
        else:
            return 'Unclassified'
    
    def get_unclassified_matches(self, batch_size: int = 1000) -> pd.DataFrame:
        """Get matched wines that haven't been classified yet"""
        query = """
            SELECT 
                mr.id,
                mr.sales_id,
                mr.review_variety,
                mr.review_country,
                mr.review_title,
                s.item_description
            FROM matched_results mr
            JOIN sales_data s ON mr.sales_id = s.id
            WHERE mr.final_variety IS NULL
            ORDER BY mr.id
            LIMIT ?
        """
        
        with sqlite3.connect(self.db_path) as conn:
            return pd.read_sql_query(query, conn, params=[batch_size])
    
    def classify_wine_record(self, row) -> dict:
        """Classify a single wine record"""
        # Start with review data (highest confidence)
        final_variety = row.get('review_variety', '') or ''
        final_country = row.get('review_country', '') or ''
        
        # Extract from sales description if review data is missing
        extracted_variety = None
        extracted_country = None
        confidence_scores = []
        
        if not final_variety and row.get('item_description'):
            extracted_variety, conf = self.extract_variety_from_text(row['item_description'])
            if extracted_variety:
                final_variety = extracted_variety
                confidence_scores.append(conf)
        
        if not final_country and row.get('item_description'):
            extracted_country, conf = self.extract_country_from_text(row['item_description'])
            if extracted_country:
                final_country = extracted_country
                confidence_scores.append(conf)
        
        # Also try extracting from review title if available
        if not final_variety and row.get('review_title'):
            variety_from_title, conf = self.extract_variety_from_text(row['review_title'])
            if variety_from_title:
                final_variety = variety_from_title
                confidence_scores.append(conf)
        
        # Classify wine color
        wine_color = self.classify_wine_color(final_variety)
        
        # Calculate overall confidence
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 1.0
        
        return {
            'final_variety': final_variety or None,
            'final_country': final_country or None,
            'wine_color': wine_color,
            'extracted_variety': extracted_variety,
            'extracted_country': extracted_country,
            'classification_confidence': avg_confidence
        }
    
    def update_classification_results(self, results: list):
        """Update matched_results table with classification results"""
        if not results:
            return
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            for result in results:
                classification_date = datetime.now().isoformat(timespec='seconds')

                cursor.execute("""
                    UPDATE matched_results
                    SET final_variety = ?, final_country = ?, wine_color = ?,
                        extracted_variety = ?, extracted_country = ?, 
                        classification_confidence = ?, classification_date = ?
                    WHERE id = ?
                """, (
                    result['final_variety'], result['final_country'], result['wine_color'],
                    result['extracted_variety'], result['extracted_country'],
                    result['classification_confidence'], classification_date, result['record_id']
                ))
            
            conn.commit()
        
        logger.info(f"Updated {len(results)} wine classifications")
    
    def run_classification_batch(self, batch_size: int = 1000) -> dict:
        """Run classification on a batch of unclassified wines"""
        # Get unclassified wines
        unclassified = self.get_unclassified_matches(batch_size)
        
        if unclassified.empty:
            return {'processed': 0, 'varieties_found': 0, 'countries_found': 0}
        
        logger.info(f"Classifying {len(unclassified)} wine records...")
        
        # Process each record
        results = []
        varieties_found = 0
        countries_found = 0
        
        for _, row in unclassified.iterrows():
            classification = self.classify_wine_record(row)
            classification['record_id'] = row['id']
            
            results.append(classification)
            
            if classification['final_variety']:
                varieties_found += 1
            if classification['final_country']:
                countries_found += 1
        
        # Update database
        self.update_classification_results(results)
        
        return {
            'processed': len(results),
            'varieties_found': varieties_found,
            'countries_found': countries_found
        }
    
    def run_full_classification(self):
        """Run classification on all unmatched wines"""
        start_time = datetime.now()
        total_processed = 0
        total_varieties = 0
        total_countries = 0
        
        logger.info("Starting wine classification pipeline...")
        
        # Check total unclassified count
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT COUNT(*) FROM matched_results 
                WHERE final_variety IS NULL
            """)
            total_unclassified = cursor.fetchone()[0]
        
        logger.info(f"Found {total_unclassified:,} unclassified wine matches")
        
        if total_unclassified == 0:
            logger.info("All wines already classified!")
            return
        
        # Process in batches
        batch_count = 0
        while True:
            batch_results = self.run_classification_batch(1000)
            
            if batch_results['processed'] == 0:
                break
            
            batch_count += 1
            total_processed += batch_results['processed']
            total_varieties += batch_results['varieties_found']
            total_countries += batch_results['countries_found']
            
            logger.info(f"Batch {batch_count}: Processed {batch_results['processed']}, "
                       f"Varieties: {batch_results['varieties_found']}, "
                       f"Countries: {batch_results['countries_found']}")
        
        # Final statistics
        duration = datetime.now() - start_time
        logger.info("=" * 60)
        logger.info("WINE CLASSIFICATION COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Duration: {duration}")
        logger.info(f"Records processed: {total_processed:,}")
        logger.info(f"Varieties classified: {total_varieties:,}")
        logger.info(f"Countries classified: {total_countries:,}")
    
    def get_classification_stats(self) -> dict:
        """Get classification statistics"""
        with sqlite3.connect(self.db_path) as conn:
            # Total classified wines
            cursor = conn.execute("SELECT COUNT(*) FROM matched_results WHERE final_variety IS NOT NULL")
            variety_classified = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT COUNT(*) FROM matched_results WHERE final_country IS NOT NULL")
            country_classified = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT COUNT(*) FROM matched_results")
            total_matches = cursor.fetchone()[0]
            
            # Color distribution
            cursor = conn.execute("""
                SELECT wine_color, COUNT(*) 
                FROM matched_results 
                WHERE wine_color IS NOT NULL 
                GROUP BY wine_color
            """)
            color_dist = dict(cursor.fetchall())
            
            # Top varieties
            cursor = conn.execute("""
                SELECT final_variety, COUNT(*) 
                FROM matched_results 
                WHERE final_variety IS NOT NULL 
                GROUP BY final_variety 
                ORDER BY COUNT(*) DESC 
                LIMIT 10
            """)
            top_varieties = cursor.fetchall()
            
            return {
                'total_matches': total_matches,
                'variety_classified': variety_classified,
                'country_classified': country_classified,
                'variety_percentage': (variety_classified / total_matches * 100) if total_matches > 0 else 0,
                'country_percentage': (country_classified / total_matches * 100) if total_matches > 0 else 0,
                'color_distribution': color_dist,
                'top_varieties': top_varieties
            }

def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Wine Classification Pipeline")
        print("Usage:")
        print("  python integrated_wine_classifier.py classify    # Run full classification")
        print("  python integrated_wine_classifier.py status     # Show statistics")
        print("  python integrated_wine_classifier.py test       # Classify 100 wines")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    classifier = DatabaseWineClassifier()
    
    if command == "classify":
        classifier.run_full_classification()
    
    elif command == "status":
        stats = classifier.get_classification_stats()
        print("=" * 50)
        print("WINE CLASSIFICATION STATUS")
        print("=" * 50)
        print(f"Total matched wines: {stats['total_matches']:,}")
        print(f"Variety classified: {stats['variety_classified']:,} ({stats['variety_percentage']:.1f}%)")
        print(f"Country classified: {stats['country_classified']:,} ({stats['country_percentage']:.1f}%)")
        
        if stats['color_distribution']:
            print("\nWine Color Distribution:")
            for color, count in stats['color_distribution'].items():
                print(f"  {color}: {count:,}")
        
        if stats['top_varieties']:
            print("\nTop 10 Varieties:")
            for i, (variety, count) in enumerate(stats['top_varieties'], 1):
                print(f"  {i:2d}. {variety}: {count:,}")
    
    elif command == "test":
        result = classifier.run_classification_batch(100)
        print(f"Test classification complete:")
        print(f"Processed: {result['processed']}")
        print(f"Varieties found: {result['varieties_found']}")
        print(f"Countries found: {result['countries_found']}")
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()