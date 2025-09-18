import sqlite3
import pandas as pd

# Connect to the database
conn = sqlite3.connect("wine_data.db")

# Pull 50 random rows from your classified table
query = """
SELECT *
FROM matched_results
ORDER BY RANDOM()
LIMIT 50;
"""
df = pd.read_sql_query(query, conn)

# Show the sample in Jupyter / console
print(df.head())

# Save to CSV or JSON for dashboard use
df.to_csv("wine_sample.csv", index=False)
df.to_json("wine_sample.json", orient="records", indent=2)

conn.close()
