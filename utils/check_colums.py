# Quick column checker script
# Save this as check_columns.py and run it

import pandas as pd

# Load your data
df = pd.read_pickle('../wine_data_fully_classified.pkl')

print("=== COLUMN NAMES ===")
for i, col in enumerate(df.columns):
    print(f"{i:2d}: '{col}'")

print(f"\n=== DATASET INFO ===")
print(f"Shape: {df.shape}")

print(f"\n=== COLUMNS CONTAINING 'color' ===")
color_cols = [col for col in df.columns if 'color' in col.lower()]
for col in color_cols:
    print(f"- {col}")
    print(f"  Sample values: {df[col].unique()[:5]}")

print(f"\n=== COLUMNS CONTAINING 'wine' ===")
wine_cols = [col for col in df.columns if 'wine' in col.lower()]
for col in wine_cols:
    print(f"- {col}")
    if df[col].dtype == 'object':
        print(f"  Sample values: {df[col].unique()[:5]}")
    else:
        print(f"  Data type: {df[col].dtype}")

print(f"\n=== BOOLEAN COLUMNS ===")
bool_cols = [col for col in df.columns if df[col].dtype == 'bool']
for col in bool_cols:
    print(f"- {col}: {df[col].value_counts().to_dict()}")