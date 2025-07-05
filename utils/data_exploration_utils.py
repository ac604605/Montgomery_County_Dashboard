# ================================
# SPECIALIZED ITEM TYPE ANALYSIS
# ================================

def show_examples_by_item_type_simple(df: pd.DataFrame, n_examples: int = 10,
                                    item_col: str = 'ITEM TYPE') -> None:
    """
    Display examples for each item type using simple iteration.
    
    Straightforward approach to examining item categories in datasets
    with item type classifications. Useful for understanding product
    diversity and category characteristics.
    
    Args:
        df (pd.DataFrame): DataFrame with item type column
        n_examples (int): Number of examples to show per type (default: 10)
        item_col (str): Name of the item type column (default: 'ITEM TYPE')
    
    Returns:
        None: Prints examples for each item type
    
    Examples:
        >>> show_examples_by_item_type_simple(inventory_df, n_examples=5)
        >>> show_examples_by_item_type_simple(product_df, n_examples=15, item_col='category')
        
    Notes:
        Displays most relevant columns for quick understanding of each category.
        Adapts to available columns in the DataFrame.
    """
    try:
        print("="*60)
        print("EXAMPLES BY ITEM TYPE (Simple Method)")
        print("="*60)
        
        # Check if item type column exists
        if item_col not in df.columns:
            print(f"Error: '{item_col}' column not found in DataFrame")
            print(f"Available columns: {list(df.columns)}")
            return
        
        # Get all item types
        item_types = df[item_col].value_counts()
        
        # Determine which columns to show
        possible_cols = ['ITEM CODE', 'ITEM DESCRIPTION', 'SUPPLIER', 'RETAIL SALES',
                        'description', 'name', 'product', 'price', 'sales', 'value']
        columns_to_show = safe_column_access(df, possible_cols)
        
        if not columns_to_show:
            # If no standard columns found, show first 4 columns
            columns_to_show = df.columns[:4].tolist()
        
        for item_type in item_types.index:
            print(f"\n--- {item_type} ({item_types[item_type]:,} total records) ---")
            
            # Get subset for this item type
            subset = df[df[item_col] == item_type]
            
            # Show sample rows
            sample = subset.head(n_examples)
            
            try:
                print(sample[columns_to_show].to_string(index=False))
            except Exception:
                # If error, just show what we can
                print(sample.head(n_examples))
            
            print("-" * 60)
            
    except Exception as e:
        print(f"Error in show_examples_by_item_type_simple: {str(e)}")


def analyze_item_types_detailed(df: pd.DataFrame, n_examples: int = 10,
                              item_col: str = 'ITEM TYPE',
                              value_col: str = None) -> None:
    """
    Perform detailed statistical analysis of each item type.
    
    Comprehensive analysis that combines categorical exploration with
    quantitative metrics for each item type. Provides business insights
    beyond simple categorization.
    
    Args:
        df (pd.DataFrame): DataFrame with item type and sales columns
        n_examples (int): Number of sample items to display (default: 10)
        item_col (str): Name of the item type column (default: 'ITEM TYPE')
        value_col (str): Name of value column for stats (default: auto-detect)
    
    Returns:
        None: Prints detailed analysis for each item type
    
    Examples:
        >>> analyze_item_types_detailed(sales_df, n_examples=8)
        >>> analyze_item_types_detailed(inventory_df, n_examples=12, value_col='revenue')
        
    Notes:
        Calculates key business metrics like total sales, average sales,
        and supplier diversity for each category. Essential for category
        performance analysis.
    """
    try:
        print("="*60)
        print("DETAILED ITEM TYPE ANALYSIS")
        print("="*60)
        
        # Check if item type column exists
        if item_col not in df.columns:
            print(f"Error: '{item_col}' column not found")
            return
        
        # Auto-detect value column if not specified
        if value_col is None:
            value_candidates = ['RETAIL SALES', 'sales', 'revenue', 'value', 'amount', 'price']
            for candidate in value_candidates:
                if candidate in df.columns and pd.api.types.is_numeric_dtype(df[candidate]):
                    value_col = candidate
                    break
        
        # Get item type counts
        item_types = df[item_col].value_counts()
        
        # Identify available columns for analysis
        id_cols = [col for col in df.columns if 'code' in col.lower() or 'id' in col.lower()]
        supplier_cols = [col for col in df.columns if 'supplier' in col.lower() or 'vendor' in col.lower()]
        desc_cols = [col for col in df.columns if 'desc' in col.lower() or 'name' in col.lower()]
        
        for item_type in item_types.index:
            print(f"\n{'='*40}")
            print(f"ITEM TYPE: {item_type}")
            print(f"{'='*40}")
            
            # Get subset
            subset = df[df[item_col] == item_type]
            
            # Basic stats
            print(f"Total records: {len(subset):,}")
            
            # Unique items if ID column exists
            if id_cols:
                unique_items = subset[id_cols[0]].nunique()
                print(f"Unique items: {unique_items:,}")
            
            # Unique suppliers if supplier column exists
            if supplier_cols:
                unique_suppliers = subset[supplier_cols[0]].nunique()
                print(f"Unique suppliers: {unique_suppliers}")
            
            # Value stats if value column exists
            if value_col and value_col in df.columns:
                total_value = subset[value_col].sum()
                avg_value = subset[value_col].mean()
                print(f"Total {value_col}: ${total_value:,.2f}")
                print(f"Average {value_col}: ${avg_value:.2f}")
            
            # Show examples
            print(f"\nSample {min(n_examples, len(subset))} items:")
            sample = subset.head(n_examples)
            
            # Choose columns to display
            display_cols = []
            if id_cols:
                display_cols.extend(id_cols[:1])
            if desc_cols:
                display_cols.extend(desc_cols[:1])
            if supplier_cols:
                display_cols.extend(supplier_cols[:1])
            if value_col and value_col in subset.columns:
                display_cols.append(value_col)
            
            # Ensure we have columns to display
            if not display_cols:
                display_cols = subset.columns[:4].tolist()
            
            display_cols = safe_column_access(subset, display_cols)
            
            try:
                print(sample[display_cols].to_string(index=False))
            except Exception:
                print(sample.head())
            
            print("-" * 60)
            
    except Exception as e:
        print(f"Error in analyze_item_types_detailed: {str(e)}")


def investigate_item_type_patterns(df: pd.DataFrame, n_examples: int = 5,
                                 item_col: str = 'ITEM TYPE',
                                 desc_col: str = None) -> None:
    """
    Investigate patterns and anomalies within each item type.
    
    Advanced pattern recognition that looks for business rule violations,
    data quality issues, and category misclassifications. Critical for
    understanding data integrity at the category level.
    
    Args:
        df (pd.DataFrame): DataFrame with item classifications
        n_examples (int): Number of examples to show for patterns (default: 5)
        item_col (str): Name of item type column (default: 'ITEM TYPE')
        desc_col (str): Name of description column (default: auto-detect)
    
    Returns:
        None: Prints pattern analysis for each item type
    
    Examples:
        >>> investigate_item_type_patterns(beverage_df, n_examples=3)
        >>> investigate_item_type_patterns(retail_df, n_examples=8)
        
    Notes:
        Identifies potential misclassifications and data quality issues
        within categories. Essential for category validation and cleanup.
    """
    try:
        print("="*60)
        print("PATTERN INVESTIGATION BY ITEM TYPE")
        print("="*60)
        
        if item_col not in df.columns:
            print(f"Error: '{item_col}' column not found")
            return
        
        # Auto-detect description column
        if desc_col is None:
            desc_candidates = ['ITEM DESCRIPTION', 'description', 'name', 'product_name', 'item_name']
            for candidate in desc_candidates:
                if candidate in df.columns:
                    desc_col = candidate
                    break
        
        # Auto-detect supplier column
        supplier_candidates = ['SUPPLIER', 'supplier', 'vendor', 'manufacturer']
        supplier_col = None
        for candidate in supplier_candidates:
            if candidate in df.columns:
                supplier_col = candidate
                break
        
        item_types = df[item_col].value_counts()
        
        for item_type in item_types.index:
            print(f"\n{'*'*30} {item_type} {'*'*30}")
            
            subset = df[df[item_col] == item_type]
            
            # Look for patterns in descriptions
            if desc_col and desc_col in subset.columns:
                print(f"Sample descriptions:")
                descriptions = subset[desc_col].dropna().head(n_examples)
                for i, desc in enumerate(descriptions, 1):
                    print(f"  {i}. {desc}")
            
            # Check for missing suppliers in this type
            if supplier_col:
                missing_suppliers = subset[supplier_col].isnull().sum()
                if missing_suppliers > 0:
                    print(f"⚠️  Missing suppliers: {missing_suppliers} ({missing_suppliers/len(subset)*100:.1f}%)")
                    
                    # Show examples without suppliers
                    if desc_col:
                        no_supplier = subset[subset[supplier_col].isnull()]
                        print(f"Examples without suppliers:")
                        for desc in no_supplier[desc_col].head(3):
                            print(f"    - {desc}")
            
            # Look for suspicious patterns in descriptions
            if desc_col and desc_col in subset.columns:
                try:
                    descriptions_str = ' '.join(subset[desc_col].fillna('').str.upper())
                    
                    # Define keywords based on item type
                    if 'BEER' in item_type.upper() or 'WINE' in item_type.upper():
                        non_alcoholic_keywords = ['OPENER', 'GLASS', 'MIXER', 'TOOL', 'ACCESSORY']
                    else:
                        non_alcoholic_keywords = ['EQUIPMENT', 'SUPPLIES', 'DISPLAY', 'MERCHANDISE']
                    
                    found_keywords = []
                    
                    for keyword in non_alcoholic_keywords:
                        if keyword in descriptions_str:
                            count = subset[desc_col].str.contains(keyword, case=False, na=False).sum()
                            if count > 0:
                                found_keywords.append(f"{keyword}({count})")
                    
                    if found_keywords:
                        print(f"🔍 Potentially miscategorized items found: {', '.join(found_keywords)}")
                        
                except Exception as e:
                    print(f"  Could not analyze descriptions: {str(e)}")
            
            print("-" * 60)
            
    except Exception as e:
        print(f"Error in investigate_item_type_patterns: {str(e)}")


def compare_item_types_summary(df: pd.DataFrame, 
                             item_col: str = 'ITEM TYPE',
                             value_col: str = None) -> pd.DataFrame:
    """
    Create comparative analysis table of all item types.
    
    Generates executive summary comparing key metrics across all item
    categories. Essential for category performance comparison and
    strategic decision making.
    
    Args:
        df (pd.DataFrame): DataFrame with item type and sales data
        item_col (str): Name of item type column (default: 'ITEM TYPE')
        value_col (str): Name of value column for totals (default: auto-detect)
    
    Returns:
        pd.DataFrame: Summary comparison table with key metrics per category
    
    Examples:
        >>> summary = compare_item_types_summary(sales_df)
        >>> print(summary.sort_values('Total Sales', ascending=False))
        >>> summary.to_csv('category_comparison.csv', index=False)
        
    Notes:
        Returns DataFrame for further analysis or export. Includes
        metrics like record counts, unique items, suppliers, and sales.
    """
    try:
        print("="*60)
        print("ITEM TYPE COMPARISON SUMMARY")
        print("="*60)
        
        if item_col not in df.columns:
            print(f"Error: '{item_col}' column not found")
            return pd.DataFrame()
        
        # Auto-detect columns
        if value_col is None:
            value_candidates = ['RETAIL SALES', 'sales', 'revenue', 'value', 'amount']
            for candidate in value_candidates:
                if candidate in df.columns and pd.api.types.is_numeric_dtype(df[candidate]):
                    value_col = candidate
                    break
        
        # Find relevant columns
        id_cols = [col for col in df.columns if 'code' in col.lower() or 'id' in col.lower()]
        supplier_cols = [col for col in df.columns if 'supplier' in col.lower() or 'vendor' in col.lower()]
        
        summary_data = []
        
        for item_type in df[item_col].value_counts().index:
            subset = df[df[item_col] == item_type]
            
            row_data = {
                'Item Type': item_type,
                'Total Records': len(subset)
            }
            
            # Add unique counts if columns exist
            if id_cols:
                row_data['Unique Items'] = subset[id_cols[0]].nunique()
            
            if supplier_cols:
                row_data['Unique Suppliers'] = subset[supplier_cols[0]].nunique()
                row_data['Missing Suppliers'] = subset[supplier_cols[0]].isnull().sum()
            
            # Add value stats if column exists
            if value_col and value_col in subset.columns:
                row_data[f'Total {value_col}'] = subset[value_col].sum()
                row_data[f'Avg {value_col}'] = subset[value_col].mean()
            
            summary_data.append(row_data)
        
        summary_df = pd.DataFrame(summary_data)
        
        # Sort by total records by default
        summary_df = summary_df.sort_values('Total Records', ascending=False)
        
        print(summary_df.to_string(index=False))
        
        return summary_df
        
    except Exception as e:
        print(f"Error in compare_item_types_summary: {str(e)}")
        return pd.DataFrame()


# ================================
# MODULE USAGE INFORMATION
# ================================

def print_module_usage() -> None:
    """
    Display comprehensive usage guide for the module.
    
    Provides examples and guidance for using all functions in the module.
    Essential reference for understanding function capabilities and
    choosing the right function for specific analysis needs.
    
    Returns:
        None: Prints comprehensive usage guide
    
    Examples:
        >>> import data_exploration_utils as deu
        >>> deu.print_module_usage()
        
    Notes:
        Call this function to see all available functions and their
        recommended use cases. Great for onboarding new team members.
    """
    print("="*70)
    print("DATA EXPLORATION UTILS (v2.0) - USAGE GUIDE")
    print("="*70)
    
    print("""
QUICK START:
-----------
# Import the module
import data_exploration_utils as deu

# Basic exploration of any dataset
report = deu.validate_dataframe(df)

# Comprehensive cleaning pipeline
df_clean, report = deu.run_phase_1_2_cleaning(df, "Dataset Name")

# Real analyst exploration process
deu.explore_like_a_real_analyst(df)

KEY IMPROVEMENTS IN v2.0:
------------------------
✅ Added error handling throughout
✅ Column existence validation
✅ Memory usage warnings for large datasets
✅ Implemented missing dictionary strategy in handle_missing_values()
✅ Added type hints for better IDE support
✅ Output limiting to prevent console overflow
✅ Adaptive column detection for item type analysis

MAIN FUNCTIONS BY CATEGORY:
--------------------------

📊 UNIVERSAL VALIDATION:
  validate_dataframe(df) - Comprehensive validation with report
  basic_data_exploration(df) - Quick overview
  explore_like_a_real_analyst(df) - Complete professional process

🧹 SYSTEMATIC CLEANING:
  run_phase_1_2_cleaning(df, name) - Full cleaning pipeline
  document_raw_data(df, name) - Initial assessment
  analyze_missing_patterns(df, name) - Missing value analysis
  handle_missing_values(df, strategy) - Apply missing value fixes
    Strategies: 'drop_rows', 'drop_cols', 'flag_only'
    Dict strategies: {'col': 'fill_mean'/'fill_median'/'fill_mode'/etc}

🔍 SPECIALIZED ANALYSIS:
  For datasets with categories/item types:
  - show_examples_by_item_type_simple(df, item_col='ITEM TYPE')
  - analyze_item_types_detailed(df, item_col='ITEM TYPE')
  - investigate_item_type_patterns(df)
  - compare_item_types_summary(df) -> Returns DataFrame

🕵️ MANUAL INVESTIGATION:
  manual_column_investigation(df) - Column-by-column analysis
  investigate_missing_values_manually(df) - Missing pattern detective work
  spot_anomalies_manually(df) - Find data quality issues
  ask_business_questions(df) - Generate investigation questions

TYPICAL WORKFLOW:
----------------
1. validate_dataframe(df)  # Quick health check
2. explore_like_a_real_analyst(df)  # Deep exploration
3. run_phase_1_2_cleaning(df, "name")  # Systematic cleaning
4. [Specialized analysis based on findings]

EXAMPLE USAGE:
-------------
import pandas as pd
import data_exploration_utils as deu

# Load your data
df = pd.read_csv('your_data.csv')

# Start with validation
validation_report = deu.validate_dataframe(df)

# Full exploration
deu.explore_like_a_real_analyst(df)

# Clean the data with custom strategies
clean_df, report = deu.run_phase_1_2_cleaning(
    df=df,
    table_name="Sales Data",
    missing_strategy={
        'price': 'fill_median',
        'description': 'flag_only',
        'quantity': 'fill_zero'
    },
    duplicate_subset=['order_id', 'product_id'],
    type_corrections={
        'order_date': 'datetime',
        'price': 'numeric',
        'category': 'category'
    }
)

# Category analysis (if applicable)
if 'category' in clean_df.columns:
    summary = deu.compare_item_types_summary(clean_df, item_col='category')
    summary.to_csv('category_analysis.csv', index=False)

ERROR HANDLING:
--------------
All functions now include try-except blocks and will:
- Print error messages instead of crashing
- Return empty DataFrames or dictionaries on error
- Validate column existence before operations
- Handle unexpected data types gracefully

MEMORY CONSIDERATIONS:
--------------------
- Functions warn when processing datasets > 1GB
- Use output_limit parameter in validate_dataframe() for large datasets
- Consider chunking very large datasets before processing

NEW FEATURES:
------------
1. Dictionary strategy for handle_missing_values():
   strategy = {
       'numeric_col': 'fill_mean',
       'category_col': 'fill_mode',
       'date_col': 'fill_forward'
   }

2. Adaptive column detection for item analysis:
   - Functions auto-detect common column patterns
   - Works with various naming conventions
   - Falls back gracefully if expected columns missing

3. Return values for programmatic use:
   - validate_dataframe() returns validation report dict
   - ask_business_questions() returns findings dict
   - compare_item_types_summary() returns DataFrame

TIPS:
-----
- Use verbose=False in document_raw_data() for silent operation
- Set max_cols in manual_column_investigation() for wide datasets
- Use output_limit in validate_dataframe() to control console output
- Check return values for 'error' keys when automation needed
""")


# ================================
# MODULE INITIALIZATION
# ================================

if __name__ == "__main__":
    print("✅ Data Exploration and Cleaning Utilities Module v2.0 Loaded Successfully!")
    print("📚 Call print_module_usage() for comprehensive usage guide")
    print("🚀 Start with: validate_dataframe(your_df) for any dataset")
    print("\n🆕 New in v2.0: Enhanced error handling, column validation, and missing value strategies")# ================================
# SPECIALIZED EXPLORATION FUNCTIONS
# ================================

def basic_data_exploration(df: pd.DataFrame, head_rows: int = 5) -> None:
    """
    Perform basic data exploration suitable for any dataset.
    
    Quick overview function that provides essential information about
    any DataFrame without making assumptions about structure or content.
    
    Args:
        df (pd.DataFrame): DataFrame to explore
        head_rows (int): Number of rows to display (default: 5)
    
    Returns:
        None: Prints exploration results
    
    Examples:
        >>> basic_data_exploration(customer_df)
        >>> basic_data_exploration(sales_df, head_rows=10)
        
    Notes:
        This is the starting point for any data exploration. Use before
        more specialized analysis functions.
    """
    try:
        print("="*50)
        print("BASIC DATA EXPLORATION")
        print("="*50)
        
        print("Dataset shape:", df.shape)
        print(f"Memory usage: {df.memory_usage(deep=True).sum() / 1024**2:.1f} MB")
        
        print(f"\nFirst {head_rows} rows:")
        print(df.head(head_rows))
        
        print("\nData types and non-null counts:")
        print(df.info())
        
        print("\nBasic statistics:")
        print(df.describe(include='all'))
        
        print("\nMissing values:")
        missing = df.isnull().sum()
        missing = missing[missing > 0]
        if len(missing) > 0:
            print(missing.sort_values(ascending=False))
        else:
            print("No missing values")
        
        print("\nDuplicate rows:", df.duplicated().sum())
        
    except Exception as e:
        print(f"Error in basic_data_exploration: {str(e)}")


def manual_column_investigation(df: pd.DataFrame, max_cols: int = None) -> None:
    """
    Perform manual column-by-column investigation.
    
    Systematic examination of each column that mimics how analysts
    manually explore unknown datasets. Provides detailed insights
    into each column's characteristics and potential issues.
    
    Args:
        df (pd.DataFrame): DataFrame to investigate
        max_cols (int, optional): Maximum columns to investigate (default: all)
    
    Returns:
        None: Prints detailed column analysis
    
    Examples:
        >>> manual_column_investigation(unknown_df)
        >>> manual_column_investigation(large_df, max_cols=20)
        
    Notes:
        This function is designed to replicate the manual process
        that experienced analysts use when first encountering a dataset.
        Look for patterns, anomalies, and data quality issues.
    """
    try:
        print("\n" + "="*50)
        print("MANUAL COLUMN-BY-COLUMN INVESTIGATION")
        print("="*50)
        
        cols_to_investigate = df.columns[:max_cols] if max_cols else df.columns
        
        for i, col in enumerate(cols_to_investigate, 1):
            print(f"\n--- [{i}/{len(cols_to_investigate)}] {col} ---")
            print(f"Type: {df[col].dtype}")
            print(f"Non-null count: {df[col].count():,} / {len(df):,}")
            print(f"Unique values: {df[col].nunique():,}")
            
            try:
                # Show value counts for categorical-like columns
                if df[col].dtype == 'object' or df[col].nunique() < 20:
                    print("Value counts:")
                    value_counts = df[col].value_counts().head(10)
                    for val, count in value_counts.items():
                        print(f"  {val}: {count:,}")
                    if len(df[col].value_counts()) > 10:
                        print(f"  ... and {len(df[col].value_counts()) - 10} more unique values")
                else:
                    print("Sample values:")
                    sample_vals = df[col].dropna().head(5).tolist()
                    print(f"  {sample_vals}")
                
                # Check for obvious issues
                if pd.api.types.is_numeric_dtype(df[col]):
                    print(f"Range: {df[col].min()} to {df[col].max()}")
                    if (df[col] < 0).any():
                        print("⚠️  Contains negative values")
                    if (df[col] == 0).sum() > len(df) * 0.1:
                        print(f"⚠️  Contains {(df[col] == 0).sum():,} zeros ({(df[col] == 0).sum()/len(df)*100:.1f}%)")
                
            except Exception as e:
                print(f"  Error analyzing column: {str(e)}")
            
            print("-" * 30)
        
        if max_cols and len(df.columns) > max_cols:
            print(f"\n... {len(df.columns) - max_cols} more columns not shown")
            
    except Exception as e:
        print(f"Error in manual_column_investigation: {str(e)}")


def investigate_missing_values_manually(df: pd.DataFrame, 
                                      sample_size: int = 3,
                                      context_cols: int = 5) -> None:
    """
    Manual investigation of missing value patterns and relationships.
    
    Detective-style analysis of missing values to understand if they
    follow systematic patterns or represent business rules. Critical
    for determining appropriate handling strategies.
    
    Args:
        df (pd.DataFrame): DataFrame with potential missing values
        sample_size (int): Number of sample rows to show (default: 3)
        context_cols (int): Number of context columns to show (default: 5)
    
    Returns:
        None: Prints missing value investigation results
    
    Examples:
        >>> investigate_missing_values_manually(survey_df)
        >>> investigate_missing_values_manually(sales_df, sample_size=5)
        
    Notes:
        Looks for relationships between missing values across columns
        and identifies potential systematic missing data patterns.
        Essential for understanding data collection processes.
    """
    try:
        print("\n" + "="*50)
        print("MANUAL MISSING VALUES INVESTIGATION")
        print("="*50)
        
        # Find columns with missing values
        missing_cols = df.columns[df.isnull().any()].tolist()
        
        if not missing_cols:
            print("No missing values to investigate")
            return
        
        print(f"Columns with missing values: {missing_cols}")
        
        for col in missing_cols:
            print(f"\n🔍 Investigating {col}:")
            missing_count = df[col].isnull().sum()
            print(f"Missing count: {missing_count:,} ({missing_count/len(df)*100:.1f}%)")
            
            # Look at rows with missing values
            missing_rows = df[df[col].isnull()]
            
            if len(missing_rows) > 0:
                print(f"Sample rows with missing {col}:")
                
                # Show other columns for context
                other_cols = [c for c in df.columns if c != col][:context_cols]
                
                # Display sample
                sample_missing = missing_rows[other_cols].head(sample_size)
                print(sample_missing.to_string())
                
                # Look for patterns
                print(f"\nLooking for patterns in missing {col}:")
                
                # Check if other columns have values when this one is missing
                for other_col in other_cols:
                    try:
                        if df[other_col].dtype == 'object' or df[other_col].nunique() < 50:
                            # For categorical columns, show most common values when target is missing
                            pattern = missing_rows[other_col].value_counts().head(3)
                            if len(pattern) > 0 and not pattern.index[0] is pd.NA:
                                print(f"  When {col} is missing, {other_col} is often: {pattern.index[0]} ({pattern.iloc[0]:,} times)")
                    except Exception:
                        continue
        
        # Check for rows with multiple missing values
        print("\n🔍 Checking for rows with multiple missing values:")
        missing_counts_per_row = df.isnull().sum(axis=1)
        multi_missing = missing_counts_per_row[missing_counts_per_row > 1]
        
        if len(multi_missing) > 0:
            print(f"Found {len(multi_missing):,} rows with multiple missing values")
            print(f"Distribution of missing values per row:")
            print(multi_missing.value_counts().sort_index())
            
    except Exception as e:
        print(f"Error in investigate_missing_values_manually: {str(e)}")


def spot_anomalies_manually(df: pd.DataFrame, 
                           numeric_sample: int = 10,
                           text_sample: int = 5) -> None:
    """
    Manual anomaly detection using analyst heuristics.
    
    Identifies potential data quality issues and anomalies using
    common patterns that experienced analysts look for. Focuses
    on practical issues that impact analysis quality.
    
    Args:
        df (pd.DataFrame): DataFrame to check for anomalies
        numeric_sample (int): Max numeric columns to analyze (default: 10)
        text_sample (int): Max text columns to analyze (default: 5)
    
    Returns:
        None: Prints anomaly detection results
    
    Examples:
        >>> spot_anomalies_manually(transaction_df)
        >>> spot_anomalies_manually(customer_df, numeric_sample=20)
        
    Notes:
        Uses practical heuristics for anomaly detection rather than
        statistical methods. Focuses on business logic violations
        and data entry errors.
    """
    try:
        print("\n" + "="*50)
        print("MANUAL ANOMALY DETECTION")
        print("="*50)
        
        # Check for suspicious patterns
        print("🔍 Looking for suspicious patterns:")
        
        # Numeric columns with zeros
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if numeric_cols:
            print("\nNumeric columns with potential issues:")
            for i, col in enumerate(numeric_cols[:numeric_sample]):
                try:
                    zero_count = (df[col] == 0).sum()
                    if zero_count > 0:
                        zero_pct = zero_count / len(df) * 100
                        print(f"  {col}: {zero_count:,} zeros ({zero_pct:.1f}%)")
                    
                    # Check for suspiciously round numbers
                    if df[col].dtype in ['int64', 'float64']:
                        round_numbers = df[col].value_counts().head()
                        suspicious_rounds = [val for val in round_numbers.index 
                                           if val % 100 == 0 or val % 1000 == 0]
                        if suspicious_rounds:
                            print(f"    ⚠️  Suspicious round numbers: {suspicious_rounds}")
                except Exception:
                    continue
        
        # Text columns with unusual patterns
        text_cols = df.select_dtypes(include=['object']).columns.tolist()
        if text_cols:
            print("\nText columns analysis:")
            for i, col in enumerate(text_cols[:text_sample]):
                try:
                    print(f"\n🔍 Examining {col} for patterns:")
                    
                    # Look at length distribution
                    non_null = df[col].dropna()
                    if len(non_null) > 0:
                        lengths = non_null.astype(str).str.len()
                        print(f"  Text length range: {lengths.min()} to {lengths.max()}")
                        
                        # Check for suspicious patterns
                        if lengths.min() == lengths.max():
                            print(f"  ⚠️  All values have same length ({lengths.min()})")
                        
                        # Look for placeholder values
                        placeholders = ['N/A', 'NA', 'NULL', 'None', 'TBD', 'XXX', 'Test', 'test']
                        for placeholder in placeholders:
                            count = non_null.astype(str).str.contains(placeholder, case=False, na=False).sum()
                            if count > 0:
                                print(f"  ⚠️  Found {count:,} values containing '{placeholder}'")
                        
                        # Sample some values
                        print(f"  Sample values: {non_null.head(3).tolist()}")
                        
                except Exception as e:
                    print(f"  Error examining {col}: {str(e)}")
                    
    except Exception as e:
        print(f"Error in spot_anomalies_manually: {str(e)}")


def ask_business_questions(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate business questions that analysts should investigate.
    
    Provides a framework of business-oriented questions that help
    guide data exploration beyond technical validation. Essential
    for connecting data quality to business impact.
    
    Args:
        df (pd.DataFrame): DataFrame to generate questions about
    
    Returns:
        dict: Dictionary with questions and automated findings
    
    Examples:
        >>> questions = ask_business_questions(sales_df)
        >>> ask_business_questions(inventory_df)
        
    Notes:
        Questions are generated based on common column patterns and
        data characteristics. Use these to guide deeper investigation
        and stakeholder conversations.
    """
    try:
        print("\n" + "="*50)
        print("BUSINESS QUESTIONS TO INVESTIGATE")
        print("="*50)
        
        findings = {}
        
        print("Questions I would ask about this dataset:")
        questions = [
            "1. What time period does this data cover?",
            "2. What is the primary key or unique identifier?",
            "3. Are there any data quality issues that would impact analysis?",
            "4. What's the granularity of this data (transaction, daily, customer-level)?",
            "5. Are there any obvious gaps or biases in the data?",
            "6. Does the data follow expected business rules?"
        ]
        
        for q in questions:
            print(q)
        
        # Try to answer some automatically
        print("\nQuick answers from the data:")
        
        # Time period - look for date-like columns
        date_cols = df.select_dtypes(include=['datetime']).columns.tolist()
        time_indicators = ['year', 'date', 'time', 'month', 'day']
        
        for col in df.columns:
            if any(indicator in col.lower() for indicator in time_indicators):
                if col not in date_cols and col in df.columns:
                    try:
                        if df[col].dtype in ['int64', 'float64']:
                            print(f"  Time period ({col}): {df[col].min()} to {df[col].max()}")
                            findings['time_period'] = {'column': col, 
                                                     'min': df[col].min(), 
                                                     'max': df[col].max()}
                    except Exception:
                        pass
        
        for col in date_cols:
            print(f"  Date range ({col}): {df[col].min()} to {df[col].max()}")
            findings['date_range'] = {'column': col, 
                                    'min': str(df[col].min()), 
                                    'max': str(df[col].max())}
        
        # Look for ID columns
        for col in df.columns:
            if 'id' in col.lower() or df[col].nunique() == len(df):
                print(f"  Potential ID column: {col} ({df[col].nunique():,} unique values)")
                if 'potential_ids' not in findings:
                    findings['potential_ids'] = []
                findings['potential_ids'].append(col)
        
        # Data quality summary
        missing_pct = (df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100
        dup_pct = (df.duplicated().sum() / len(df)) * 100
        
        print(f"  Data quality: {missing_pct:.1f}% missing values, {dup_pct:.1f}% duplicate rows")
        findings['data_quality'] = {
            'missing_pct': missing_pct,
            'duplicate_pct': dup_pct
        }
        
        return findings
        
    except Exception as e:
        print(f"Error in ask_business_questions: {str(e)}")
        return {'error': str(e)}


def explore_like_a_real_analyst(df: pd.DataFrame) -> None:
    """
    Complete real-world data exploration process.
    
    Replicates the systematic approach that experienced data analysts
    use when encountering unknown datasets. Combines technical validation
    with business-oriented investigation.
    
    Args:
        df (pd.DataFrame): Unknown DataFrame to explore systematically
    
    Returns:
        None: Prints comprehensive exploration report with next steps
    
    Examples:
        >>> explore_like_a_real_analyst(mystery_df)
        >>> explore_like_a_real_analyst(new_dataset)
        
    Notes:
        This is the master function that demonstrates professional
        data exploration methodology. Use this as a template for
        systematic data investigation.
    """
    try:
        print("REAL-WORLD DATA EXPLORATION PROCESS")
        print("="*60)
        
        # Check memory usage first
        check_memory_usage(df)
        
        # Step 1: Always start with basics
        basic_data_exploration(df)
        
        # Step 2: Look at each column manually (limit to first 20 for large datasets)
        max_cols = 20 if len(df.columns) > 20 else None
        manual_column_investigation(df, max_cols=max_cols)
        
        # Step 3: Investigate missing values
        investigate_missing_values_manually(df)
        
        # Step 4: Look for anomalies
        spot_anomalies_manually(df)
        
        # Step 5: Ask business questions
        findings = ask_business_questions(df)
        
        print("\n" + "="*60)
        print("NEXT STEPS:")
        print("="*60)
        print("Based on this exploration, I would:")
        
        # Generate customized recommendations based on findings
        recommendations = []
        
        if df.isnull().sum().sum() > 0:
            recommendations.append("Investigate missing value patterns and determine handling strategy")
        
        if df.duplicated().sum() > 0:
            recommendations.append("Remove or investigate duplicate records")
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            recommendations.append("Deep dive into numeric distributions and outliers")
        
        text_cols = df.select_dtypes(include=['object']).columns
        if len(text_cols) > 0:
            recommendations.append("Standardize text fields and check for data entry errors")
        
        if not recommendations:
            recommendations.append("Data appears clean - proceed with analysis")
        
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec}")
            
    except Exception as e:
        print(f"Error in explore_like_a_real_analyst: {str(e)}")"""
Data Exploration and Cleaning Utilities Module (Enhanced Version)

This module provides comprehensive functions for data exploration, validation, 
and cleaning processes commonly used in data analysis workflows. The functions
are designed to work with pandas DataFrames and provide detailed insights into
data quality, structure, and patterns.

Author: Data Analyst Portfolio
Version: 2.0 (Enhanced with error handling and robustness)
Requirements: pandas, numpy
"""

import pandas as pd
import numpy as np
import warnings
from typing import Optional, Dict, List, Union, Tuple, Any


# ================================
# HELPER FUNCTIONS
# ================================

def validate_required_columns(df: pd.DataFrame, required_cols: List[str], 
                            function_name: str = "") -> bool:
    """
    Check if required columns exist in DataFrame.
    
    Args:
        df: DataFrame to check
        required_cols: List of required column names
        function_name: Name of calling function for error message
        
    Returns:
        bool: True if all columns exist
        
    Raises:
        ValueError: If any required columns are missing
    """
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"{function_name}: Missing required columns: {missing}")
    return True


def check_memory_usage(df: pd.DataFrame, threshold_gb: float = 1.0) -> None:
    """
    Warn if DataFrame memory usage exceeds threshold.
    
    Args:
        df: DataFrame to check
        threshold_gb: Memory threshold in gigabytes
    """
    memory_gb = df.memory_usage(deep=True).sum() / (1024**3)
    if memory_gb > threshold_gb:
        warnings.warn(f"Large dataset detected ({memory_gb:.1f}GB). "
                     "Operations may use significant memory.", 
                     ResourceWarning)


def safe_column_access(df: pd.DataFrame, columns: List[str]) -> List[str]:
    """
    Return list of columns that actually exist in the DataFrame.
    
    Args:
        df: DataFrame to check
        columns: List of desired columns
        
    Returns:
        List of columns that exist in df
    """
    return [col for col in columns if col in df.columns]


# ================================
# PHASE 1: INITIAL ASSESSMENT & DOCUMENTATION
# ================================

def document_raw_data(df: pd.DataFrame, table_name: str, 
                     verbose: bool = True) -> Dict[str, Any]:
    """
    Document the initial state of a dataset with comprehensive overview.
    
    This function provides a complete initial assessment of a DataFrame,
    including shape, memory usage, data types, missing values, and duplicates.
    Essential for understanding the raw data before any cleaning operations.
    
    Args:
        df (pd.DataFrame): The DataFrame to document
        table_name (str): Human-readable name for the dataset for reporting
        verbose (bool): Whether to print detailed output (default: True)
    
    Returns:
        dict: Dictionary containing:
            - 'original_shape': Tuple of (rows, columns)
            - 'missing_values': Dict of column names and missing counts
            - 'duplicate_count': Number of duplicate rows
            - 'memory_usage_mb': Memory usage in megabytes
            - 'column_types': Dict of column names and their data types
    
    Examples:
        >>> assessment = document_raw_data(sales_df, "Sales Data")
        >>> print(f"Dataset has {assessment['duplicate_count']} duplicates")
        
    Notes:
        Prints comprehensive report to console if verbose=True. 
        Best used as first step in any data exploration workflow.
    """
    try:
        check_memory_usage(df)
        
        if verbose:
            print(f"\n{'='*50}")
            print(f"PHASE 1: INITIAL ASSESSMENT - {table_name}")
            print(f"{'='*50}")
        
        # Basic shape and info
        memory_mb = df.memory_usage(deep=True).sum() / 1024**2
        
        if verbose:
            print(f"Dataset Shape: {df.shape}")
            print(f"Memory Usage: {memory_mb:.2f} MB")
        
        # Data types summary
        dtype_counts = df.dtypes.value_counts()
        column_types = df.dtypes.to_dict()
        
        if verbose:
            print(f"\nData Types Distribution:")
            for dtype, count in dtype_counts.items():
                print(f"  {dtype}: {count} columns")
        
        # Missing values analysis
        missing_info = df.isnull().sum()
        missing_info = missing_info[missing_info > 0].sort_values(ascending=False)
        
        if verbose:
            if len(missing_info) > 0:
                print(f"\nMissing Values by Column:")
                for col, count in missing_info.items():
                    pct = (count / len(df)) * 100
                    print(f"  {col}: {count} ({pct:.2f}%)")
            else:
                print("\nNo missing values found")
        
        # Duplicate analysis
        duplicate_count = df.duplicated().sum()
        if verbose:
            print(f"\nDuplicate Rows: {duplicate_count}")
        
        # Column-wise summary
        if verbose:
            print(f"\nColumn Details:")
            for col in df.columns[:20]:  # Limit to first 20 columns
                dtype = df[col].dtype
                unique_count = df[col].nunique()
                print(f"  {col}: {dtype} | {unique_count} unique values")
            
            if len(df.columns) > 20:
                print(f"  ... and {len(df.columns) - 20} more columns")
        
        return {
            'original_shape': df.shape,
            'missing_values': missing_info.to_dict() if len(missing_info) > 0 else {},
            'duplicate_count': duplicate_count,
            'memory_usage_mb': memory_mb,
            'column_types': column_types
        }
        
    except Exception as e:
        print(f"Error in document_raw_data: {str(e)}")
        return {
            'error': str(e),
            'original_shape': df.shape if 'df' in locals() else None
        }


def create_data_dictionary_template(df: pd.DataFrame, table_name: str,
                                  max_samples: int = 3) -> pd.DataFrame:
    """
    Create a template for documenting column definitions and business rules.
    
    Generates a structured template for creating comprehensive data documentation.
    Essential for maintaining data governance and ensuring reproducible analysis.
    
    Args:
        df (pd.DataFrame): The DataFrame to create dictionary for
        table_name (str): Name of the dataset for the dictionary header
        max_samples (int): Maximum number of sample values to show (default: 3)
    
    Returns:
        pd.DataFrame: Template DataFrame with columns:
            - 'column': Column name
            - 'data_type': Data type
            - 'description': Placeholder for business description
            - 'business_rules': Placeholder for validation rules
            - 'sample_values': First n non-null values
    
    Examples:
        >>> template = create_data_dictionary_template(df, "Customer Data")
        >>> template.to_csv("data_dictionary_template.csv", index=False)
        
    Notes:
        Creates a foundation for data documentation that should be filled
        in with business knowledge and domain expertise.
    """
    try:
        print(f"\n{'='*50}")
        print(f"DATA DICTIONARY TEMPLATE - {table_name}")
        print(f"{'='*50}")
        
        template = []
        for col in df.columns:
            try:
                sample_values = df[col].dropna().head(max_samples).tolist()
                # Convert to string representation for better display
                sample_values = [str(val)[:50] for val in sample_values]  # Limit length
            except Exception:
                sample_values = ['[Error reading samples]']
            
            template.append({
                'column': col,
                'data_type': str(df[col].dtype),
                'non_null_count': df[col].count(),
                'null_count': df[col].isnull().sum(),
                'unique_count': df[col].nunique(),
                'description': '[TO BE FILLED]',
                'business_rules': '[TO BE FILLED]',
                'sample_values': ', '.join(sample_values) if sample_values else '[No samples]'
            })
        
        dict_df = pd.DataFrame(template)
        
        # Only print first 10 columns to avoid overwhelming output
        if len(dict_df) > 10:
            print(dict_df.head(10).to_string(index=False))
            print(f"\n... and {len(dict_df) - 10} more columns")
        else:
            print(dict_df.to_string(index=False))
        
        return dict_df
        
    except Exception as e:
        print(f"Error creating data dictionary: {str(e)}")
        return pd.DataFrame()


# ================================
# PHASE 2: STRUCTURAL ISSUES
# ================================

def analyze_missing_patterns(df: pd.DataFrame, table_name: str,
                           max_patterns: int = 10) -> Optional[pd.Series]:
    """
    Analyze patterns and relationships in missing data.
    
    Performs comprehensive missing value analysis including individual column
    analysis and cross-column missing value patterns. Critical for understanding
    if missing data is random or systematic.
    
    Args:
        df (pd.DataFrame): DataFrame to analyze
        table_name (str): Name for reporting purposes
        max_patterns (int): Maximum number of patterns to display (default: 10)
    
    Returns:
        pd.Series or None: Series of missing value counts by column (descending),
                          or None if no missing values found
    
    Examples:
        >>> missing_analysis = analyze_missing_patterns(df, "Sales Data")
        >>> if missing_analysis is not None:
        ...     print(f"Column with most missing: {missing_analysis.index[0]}")
        
    Notes:
        Identifies systematic missing patterns that may indicate data quality
        issues or business rules. Shows combinations of missing values across
        columns to detect structural problems.
    """
    try:
        print(f"\n{'='*50}")
        print(f"PHASE 2A: MISSING VALUE ANALYSIS - {table_name}")
        print(f"{'='*50}")
        
        # Missing value patterns
        missing_data = df.isnull()
        
        if missing_data.sum().sum() == 0:
            print("No missing values to analyze")
            return None
        
        # Missing by column
        missing_by_col = missing_data.sum().sort_values(ascending=False)
        missing_by_col = missing_by_col[missing_by_col > 0]
        
        print("Missing Values by Column:")
        for col, count in missing_by_col.items():
            pct = (count / len(df)) * 100
            print(f"  {col}: {count} ({pct:.2f}%)")
        
        # Missing value combinations (only if we have a reasonable number of columns)
        if len(missing_by_col) > 1 and len(missing_by_col) < 20:
            print(f"\nMissing Value Patterns (showing top {max_patterns}):")
            try:
                # Only analyze patterns for columns with missing values
                cols_with_missing = missing_by_col.index.tolist()
                missing_subset = missing_data[cols_with_missing]
                
                # Convert to tuple for grouping
                pattern_series = missing_subset.apply(tuple, axis=1)
                missing_patterns = pattern_series.value_counts()
                
                pattern_count = 0
                for pattern_tuple, count in missing_patterns.items():
                    if any(pattern_tuple) and pattern_count < max_patterns:
                        # Create readable pattern string
                        pattern_parts = []
                        for col, is_missing in zip(cols_with_missing, pattern_tuple):
                            if is_missing:
                                pattern_parts.append(f"{col}=Missing")
                        
                        if pattern_parts:  # Only show if at least one column is missing
                            pattern_str = ', '.join(pattern_parts)
                            print(f"  {pattern_str}: {count} rows")
                            pattern_count += 1
                            
            except Exception as e:
                print(f"  Could not analyze patterns: {str(e)}")
        
        return missing_by_col
        
    except Exception as e:
        print(f"Error in analyze_missing_patterns: {str(e)}")
        return None


def handle_missing_values(df: pd.DataFrame, 
                         missing_strategy: Union[str, Dict[str, str], None] = None) -> pd.DataFrame:
    """
    Handle missing values according to specified strategy.
    
    Applies various missing value handling strategies based on analysis needs.
    Supports multiple approaches from conservative flagging to aggressive removal.
    
    Args:
        df (pd.DataFrame): DataFrame with missing values to handle
        missing_strategy (str or dict, optional): Strategy to apply:
            - 'drop_rows': Remove rows with any missing values
            - 'drop_cols': Remove columns with >50% missing values
            - 'flag_only': Add boolean flags for missing values
            - dict: Custom strategy per column {'column': 'strategy'}
              Supported strategies: 'drop_rows', 'fill_zero', 'fill_mean', 
              'fill_median', 'fill_mode', 'fill_forward', 'fill_backward'
    
    Returns:
        pd.DataFrame: DataFrame with missing values handled according to strategy
    
    Examples:
        >>> # Conservative approach - just flag
        >>> df_flagged = handle_missing_values(df, 'flag_only')
        >>> 
        >>> # Aggressive cleaning
        >>> df_clean = handle_missing_values(df, 'drop_rows')
        >>> 
        >>> # Custom per column
        >>> df_custom = handle_missing_values(df, {
        ...     'price': 'fill_median', 
        ...     'description': 'flag_only',
        ...     'category': 'fill_mode'
        ... })
        
    Notes:
        Always creates a copy of the original DataFrame. Logs all changes
        for transparency and reproducibility.
    """
    print(f"\n{'='*30}")
    print(f"MISSING VALUE HANDLING")
    print(f"{'='*30}")
    
    if missing_strategy is None:
        print("No strategy provided. Available strategies:")
        print("  'drop_rows' - Remove rows with any missing values")
        print("  'drop_cols' - Remove columns with >50% missing values")
        print("  'flag_only' - Just flag missing values, don't remove")
        print("  Custom dictionary: {'column_name': 'strategy'}")
        print("    Strategies: 'drop_rows', 'fill_zero', 'fill_mean', 'fill_median',")
        print("                'fill_mode', 'fill_forward', 'fill_backward'")
        return df
    
    df_clean = df.copy()
    changes_log = []
    
    try:
        if isinstance(missing_strategy, str):
            if missing_strategy == 'drop_rows':
                original_rows = len(df_clean)
                df_clean = df_clean.dropna()
                removed_rows = original_rows - len(df_clean)
                changes_log.append(f"Removed {removed_rows} rows with missing values")
            
            elif missing_strategy == 'drop_cols':
                threshold = 0.5
                cols_to_drop = []
                for col in df_clean.columns:
                    missing_pct = df_clean[col].isnull().sum() / len(df_clean)
                    if missing_pct > threshold:
                        cols_to_drop.append(col)
                
                if cols_to_drop:
                    df_clean = df_clean.drop(columns=cols_to_drop)
                    changes_log.append(f"Removed columns with >50% missing: {cols_to_drop}")
            
            elif missing_strategy == 'flag_only':
                # Add flag columns for missing values
                for col in df_clean.columns:
                    if df_clean[col].isnull().sum() > 0:
                        flag_col = f"{col}_missing_flag"
                        df_clean[flag_col] = df_clean[col].isnull()
                        changes_log.append(f"Added missing flag column: {flag_col}")
        
        elif isinstance(missing_strategy, dict):
            # Custom strategy per column
            for col, strategy in missing_strategy.items():
                if col not in df_clean.columns:
                    changes_log.append(f"Warning: Column '{col}' not found")
                    continue
                
                if df_clean[col].isnull().sum() == 0:
                    continue  # No missing values in this column
                
                try:
                    if strategy == 'drop_rows':
                        original_rows = len(df_clean)
                        df_clean = df_clean[df_clean[col].notna()]
                        removed = original_rows - len(df_clean)
                        changes_log.append(f"{col}: Dropped {removed} rows with missing values")
                    
                    elif strategy == 'fill_zero':
                        df_clean[col] = df_clean[col].fillna(0)
                        changes_log.append(f"{col}: Filled missing with 0")
                    
                    elif strategy == 'fill_mean':
                        if pd.api.types.is_numeric_dtype(df_clean[col]):
                            mean_val = df_clean[col].mean()
                            df_clean[col] = df_clean[col].fillna(mean_val)
                            changes_log.append(f"{col}: Filled missing with mean ({mean_val:.2f})")
                        else:
                            changes_log.append(f"{col}: Cannot fill with mean (not numeric)")
                    
                    elif strategy == 'fill_median':
                        if pd.api.types.is_numeric_dtype(df_clean[col]):
                            median_val = df_clean[col].median()
                            df_clean[col] = df_clean[col].fillna(median_val)
                            changes_log.append(f"{col}: Filled missing with median ({median_val:.2f})")
                        else:
                            changes_log.append(f"{col}: Cannot fill with median (not numeric)")
                    
                    elif strategy == 'fill_mode':
                        mode_result = df_clean[col].mode()
                        if len(mode_result) > 0:
                            mode_val = mode_result[0]
                            df_clean[col] = df_clean[col].fillna(mode_val)
                            changes_log.append(f"{col}: Filled missing with mode ({mode_val})")
                        else:
                            changes_log.append(f"{col}: No mode found")
                    
                    elif strategy == 'fill_forward':
                        df_clean[col] = df_clean[col].fillna(method='ffill')
                        changes_log.append(f"{col}: Forward filled missing values")
                    
                    elif strategy == 'fill_backward':
                        df_clean[col] = df_clean[col].fillna(method='bfill')
                        changes_log.append(f"{col}: Backward filled missing values")
                    
                    elif strategy == 'flag_only':
                        flag_col = f"{col}_missing_flag"
                        df_clean[flag_col] = df_clean[col].isnull()
                        changes_log.append(f"{col}: Added missing flag column")
                    
                    else:
                        changes_log.append(f"{col}: Unknown strategy '{strategy}'")
                        
                except Exception as e:
                    changes_log.append(f"{col}: Error applying {strategy} - {str(e)}")
        
        # Log changes
        for change in changes_log:
            print(f"  {change}")
        
        return df_clean
        
    except Exception as e:
        print(f"Error in handle_missing_values: {str(e)}")
        return df


def analyze_duplicates(df: pd.DataFrame, table_name: str, 
                      subset: Optional[List[str]] = None,
                      show_examples: bool = True) -> Dict[str, int]:
    """
    Analyze duplicate records in the dataset.
    
    Identifies both complete duplicates and partial duplicates based on
    specified columns. Essential for understanding data quality issues
    and potential data entry problems.
    
    Args:
        df (pd.DataFrame): DataFrame to analyze for duplicates
        table_name (str): Name for reporting purposes
        subset (list, optional): List of columns to check for partial duplicates.
                               If None, only checks for complete duplicates.
        show_examples (bool): Whether to show example duplicates (default: True)
    
    Returns:
        dict: Dictionary containing:
            - 'full_duplicates': Count of complete duplicate rows
            - 'partial_duplicates': Count of partial duplicates (0 if subset not provided)
    
    Examples:
        >>> # Check for complete duplicates only
        >>> dup_analysis = analyze_duplicates(df, "Sales Data")
        >>> 
        >>> # Check for duplicates based on key columns
        >>> dup_analysis = analyze_duplicates(df, "Sales Data", subset=['customer_id', 'date'])
        >>> print(f"Found {dup_analysis['partial_duplicates']} partial duplicates")
        
    Notes:
        Shows sample duplicate rows for manual inspection. Partial duplicates
        are useful for identifying business key violations or data entry errors.
    """
    try:
        print(f"\n{'='*50}")
        print(f"PHASE 2B: DUPLICATE ANALYSIS - {table_name}")
        print(f"{'='*50}")
        
        # Full duplicates
        full_duplicates = df.duplicated()
        full_dup_count = full_duplicates.sum()
        
        print(f"Full Duplicates: {full_dup_count}")
        
        if full_dup_count > 0 and show_examples:
            print("Sample duplicate rows:")
            duplicate_rows = df[full_duplicates].head(3)
            
            # Show only first few columns if too many
            if len(duplicate_rows.columns) > 10:
                display_cols = duplicate_rows.columns[:10].tolist()
                print(duplicate_rows[display_cols].to_string(index=False))
                print(f"  ... {len(duplicate_rows.columns) - 10} more columns not shown")
            else:
                print(duplicate_rows.to_string(index=False))
        
        # Partial duplicates (if subset specified)
        partial_dup_count = 0
        if subset:
            # Validate subset columns exist
            subset = safe_column_access(df, subset)
            if subset:
                partial_duplicates = df.duplicated(subset=subset)
                partial_dup_count = partial_duplicates.sum()
                print(f"\nPartial Duplicates (on {subset}): {partial_dup_count}")
                
                if partial_dup_count > 0 and show_examples:
                    print("Sample partial duplicate rows:")
                    partial_dup_rows = df[partial_duplicates].head(3)
                    
                    # Show the subset columns plus a few more for context
                    display_cols = subset + [col for col in df.columns if col not in subset][:3]
                    display_cols = safe_column_access(df, display_cols)
                    print(partial_dup_rows[display_cols].to_string(index=False))
            else:
                print(f"\nWarning: None of the specified subset columns exist in DataFrame")
        
        return {
            'full_duplicates': full_dup_count,
            'partial_duplicates': partial_dup_count
        }
        
    except Exception as e:
        print(f"Error in analyze_duplicates: {str(e)}")
        return {'full_duplicates': 0, 'partial_duplicates': 0}


def remove_duplicates(df: pd.DataFrame, method: Union[str, bool] = 'first', 
                     subset: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Remove duplicate records from the DataFrame.
    
    Removes duplicates with configurable options for which records to keep
    and which columns to consider for duplication.
    
    Args:
        df (pd.DataFrame): DataFrame to deduplicate
        method (str or bool): Which duplicates to keep:
            - 'first': Keep first occurrence (default)
            - 'last': Keep last occurrence
            - False: Drop all duplicates
        subset (list, optional): List of columns to consider for identifying duplicates.
                               If None, considers all columns.
    
    Returns:
        pd.DataFrame: Deduplicated DataFrame
    
    Examples:
        >>> # Remove complete duplicates, keep first
        >>> df_clean = remove_duplicates(df)
        >>> 
        >>> # Remove duplicates based on key columns, keep last
        >>> df_clean = remove_duplicates(df, method='last', subset=['id', 'date'])
        >>> 
        >>> # Remove all duplicates (keep none)
        >>> df_clean = remove_duplicates(df, method=False)
        
    Notes:
        Always reports the number of rows removed for transparency.
        Consider business rules when choosing which duplicates to keep.
    """
    try:
        print(f"\n{'='*30}")
        print(f"DUPLICATE REMOVAL")
        print(f"{'='*30}")
        
        original_rows = len(df)
        
        # Validate subset columns if provided
        if subset:
            subset = safe_column_access(df, subset)
            if not subset:
                print("Warning: None of the specified subset columns exist. Using all columns.")
                subset = None
        
        df_clean = df.drop_duplicates(subset=subset, keep=method)
        removed_rows = original_rows - len(df_clean)
        
        print(f"Removed {removed_rows} duplicate rows")
        print(f"Kept method: {method}")
        if subset:
            print(f"Based on columns: {subset}")
        
        return df_clean
        
    except Exception as e:
        print(f"Error in remove_duplicates: {str(e)}")
        return df


def fix_data_types(df: pd.DataFrame, 
                  type_corrections: Optional[Dict[str, str]] = None) -> pd.DataFrame:
    """
    Fix data type issues in the DataFrame.
    
    Converts columns to appropriate data types based on provided mapping.
    Handles common type conversion issues and reports any failures.
    
    Args:
        df (pd.DataFrame): DataFrame with type issues to fix
        type_corrections (dict, optional): Mapping of column names to target types:
            - 'datetime': Convert to datetime
            - 'numeric': Convert to numeric (coerces errors to NaN)
            - 'category': Convert to categorical
            - 'string': Convert to string
            - Standard pandas dtypes: 'int64', 'float64', 'str', etc.
    
    Returns:
        pd.DataFrame: DataFrame with corrected data types
    
    Examples:
        >>> # Fix common type issues
        >>> corrections = {
        ...     'date_column': 'datetime',
        ...     'price_column': 'numeric',
        ...     'category_column': 'category'
        ... }
        >>> df_typed = fix_data_types(df, corrections)
        >>> 
        >>> # Convert to specific pandas types
        >>> corrections = {'year': 'int64', 'amount': 'float64'}
        >>> df_typed = fix_data_types(df, corrections)
        
    Notes:
        Uses pandas' error handling for robust conversions. Reports both
        successful conversions and failures with error messages.
    """
    print(f"\n{'='*50}")
    print(f"PHASE 2C: DATA TYPE CORRECTIONS")
    print(f"{'='*50}")
    
    if type_corrections is None:
        print("Current data types:")
        print(df.dtypes)
        print("\nProvide type_corrections dictionary like:")
        print("{'column_name': 'target_type'}")
        print("Supported types: 'datetime', 'numeric', 'category', 'string', ")
        print("                 'int64', 'float64', etc.")
        return df
    
    df_clean = df.copy()
    
    for col, target_type in type_corrections.items():
        if col in df_clean.columns:
            try:
                original_type = df_clean[col].dtype
                
                if target_type == 'datetime':
                    df_clean[col] = pd.to_datetime(df_clean[col], errors='coerce')
                elif target_type == 'numeric':
                    df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
                elif target_type == 'category':
                    df_clean[col] = df_clean[col].astype('category')
                elif target_type == 'string':
                    df_clean[col] = df_clean[col].astype('string')
                else:
                    df_clean[col] = df_clean[col].astype(target_type)
                
                print(f"  ✓ {col}: {original_type} → {df_clean[col].dtype}")
                
                # Report any conversion issues
                if target_type in ['datetime', 'numeric']:
                    new_nulls = df_clean[col].isnull().sum() - df[col].isnull().sum()
                    if new_nulls > 0:
                        print(f"    Warning: {new_nulls} values could not be converted")
                
            except Exception as e:
                print(f"  ✗ ERROR converting {col}: {str(e)}")
        else:
            print(f"  ✗ Column '{col}' not found in DataFrame")
    
    return df_clean


# ================================
# MAIN EXECUTION FUNCTION
# ================================

def run_phase_1_2_cleaning(df: pd.DataFrame, table_name: str, 
                          missing_strategy: Union[str, Dict[str, str], None] = None, 
                          duplicate_subset: Optional[List[str]] = None, 
                          type_corrections: Optional[Dict[str, str]] = None,
                          remove_duplicates_flag: bool = True) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Execute complete Phase 1 & 2 data cleaning process.
    
    Comprehensive data cleaning pipeline that combines documentation,
    structural issue identification, and automated cleaning steps.
    
    Args:
        df (pd.DataFrame): Raw DataFrame to clean
        table_name (str): Name for reporting and documentation
        missing_strategy (str or dict, optional): Strategy for handling missing values
        duplicate_subset (list, optional): Columns to check for partial duplicates
        type_corrections (dict, optional): Column type corrections to apply
        remove_duplicates_flag (bool): Whether to remove duplicates (default: True)
    
    Returns:
        tuple: (cleaned_dataframe, cleaning_report_dict)
            - cleaned_dataframe: DataFrame after all cleaning steps
            - cleaning_report_dict: Dictionary with all analysis results
    
    Examples:
        >>> # Basic cleaning with documentation
        >>> df_clean, report = run_phase_1_2_cleaning(df, "Sales Data")
        >>> 
        >>> # Full cleaning pipeline
        >>> df_clean, report = run_phase_1_2_cleaning(
        ...     df=raw_df,
        ...     table_name="Customer Data",
        ...     missing_strategy='flag_only',
        ...     duplicate_subset=['customer_id'],
        ...     type_corrections={'signup_date': 'datetime', 'age': 'int64'}
        ... )
        
    Notes:
        This is the main function for systematic data cleaning. Always
        preserves original data and provides comprehensive reporting.
    """
    try:
        print(f"\n{'#'*60}")
        print(f"DATA CLEANING PHASES 1 & 2: {table_name}")
        print(f"{'#'*60}")
        
        check_memory_usage(df)
        
        # Phase 1: Documentation
        initial_assessment = document_raw_data(df, table_name)
        data_dict = create_data_dictionary_template(df, table_name)
        
        # Phase 2: Structural Issues
        missing_analysis = analyze_missing_patterns(df, table_name)
        duplicate_analysis = analyze_duplicates(df, table_name, subset=duplicate_subset)
        
        # Apply corrections if strategies provided
        df_cleaned = df.copy()
        
        if missing_strategy:
            df_cleaned = handle_missing_values(df_cleaned, missing_strategy)
        
        if remove_duplicates_flag and duplicate_analysis['full_duplicates'] > 0:
            df_cleaned = remove_duplicates(df_cleaned, subset=duplicate_subset)
        
        if type_corrections:
            df_cleaned = fix_data_types(df_cleaned, type_corrections)
        
        # Final summary
        print(f"\n{'='*50}")
        print(f"CLEANING SUMMARY")
        print(f"{'='*50}")
        print(f"Original shape: {df.shape}")
        print(f"Cleaned shape: {df_cleaned.shape}")
        print(f"Rows removed: {df.shape[0] - df_cleaned.shape[0]}")
        print(f"Columns added/removed: {df_cleaned.shape[1] - df.shape[1]}")
        
        return df_cleaned, {
            'initial_assessment': initial_assessment,
            'data_dictionary': data_dict,
            'missing_analysis': missing_analysis.to_dict() if missing_analysis is not None else {},
            'duplicate_analysis': duplicate_analysis,
            'cleaning_summary': {
                'original_shape': df.shape,
                'cleaned_shape': df_cleaned.shape,
                'rows_removed': df.shape[0] - df_cleaned.shape[0],
                'columns_changed': df_cleaned.shape[1] - df.shape[1]
            }
        }
        
    except Exception as e:
        print(f"Error in run_phase_1_2_cleaning: {str(e)}")
        return df, {'error': str(e)}