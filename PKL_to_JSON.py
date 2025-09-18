import sqlite3
import json

def convert_sqlite_to_json():
    # Connect to SQLite database
    conn = sqlite3.connect('wine_data.db')
    conn.row_factory = sqlite3.Row  # This enables column access by name
    cursor = conn.cursor()
    
    # Query all data (adjust table name as needed)
    cursor.execute("SELECT * FROM matched_results")  # Replace with your table name
    
    # Convert to list of dictionaries
    data = [dict(row) for row in cursor.fetchall()]
    
    # Save as JSON for the dashboard
    with open('../wine_data.json', 'w') as f:
        json.dump(data, f, indent=2)
    
    conn.close()
    print(f"Converted {len(data)} records to JSON")

if __name__ == "__main__":
    convert_sqlite_to_json()