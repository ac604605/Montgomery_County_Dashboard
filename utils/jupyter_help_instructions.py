# ============================================================================
# UTILITY HELP GUIDE - Quick Reference for Jupyter Notebook
# ============================================================================

def show_help():
    """Display help for all utility functions available in this notebook"""
    
    print("="*70)
    print("UTILITY FUNCTIONS HELP GUIDE")
    print("="*70)
    
    print("""
WINE CLASSIFICATION SYSTEM:
---------------------------
Main Function:
  run_complete_wine_classification(df)
    - Classifies wine varieties with 90%+ accuracy
    - Returns: (classified_dataframe, variety_counts)
    - Usage: df_classified, counts = run_complete_wine_classification(df)

Quick Summary:
  quick_classification_summary(df_classified)
    - Shows brief results overview
    - Usage: quick_classification_summary(df_classified)

View Documentation:
  help(run_complete_wine_classification)  # Detailed function help
  run_complete_wine_classification?       # Quick Jupyter help

DATA EXPLORATION UTILITIES:
---------------------------
Quick Start:
  deu.validate_dataframe(df)              # Health check any dataset
  deu.basic_data_exploration(df)          # Quick overview
  deu.explore_like_a_real_analyst(df)     # Complete professional exploration

Full Cleaning Pipeline:
  df_clean, report = deu.run_phase_1_2_cleaning(df, "Dataset Name")
    - Complete systematic cleaning process
    - Returns cleaned dataframe and report

Specialized Analysis:
  deu.show_examples_by_item_type_simple(df)      # View by categories
  deu.analyze_item_types_detailed(df)            # Category performance
  deu.compare_item_types_summary(df)             # Returns comparison table

Manual Investigation:
  deu.manual_column_investigation(df)            # Column-by-column analysis
  deu.investigate_missing_values_manually(df)    # Missing value patterns
  deu.spot_anomalies_manually(df)               # Data quality issues

View Documentation:
  help(deu)                               # Full module documentation
  deu.print_module_usage()               # Comprehensive usage guide
  help(deu.function_name)                # Specific function help

DASHBOARD CREATION:
------------------
Sales Dashboard:
  df_analysis = create_sales_dashboard(df_final)
    - Creates 6-chart sales analysis dashboard
    - Usage: df_analysis = create_sales_dashboard(df_final)

Variety Explorer:
  varieties = interactive_variety_explorer(df_analysis)
    - Shows available wine varieties for analysis
    - Usage: varieties = interactive_variety_explorer(df_analysis)

Detailed Analysis:
  analyze_variety_performance(df_analysis, 'Chardonnay')
    - Deep dive into specific wine variety
    - Usage: analyze_variety_performance(df_analysis, 'variety_name')

DATA MANAGEMENT:
---------------
Save Data:
  df.to_pickle('filename.pkl')           # Save for later use
  df.to_csv('filename.csv', index=False) # Universal format

Load Data:
  df = pd.read_pickle('filename.pkl')    # Fast loading
  df = pd.read_csv('filename.csv')       # Universal loading

Check Data:
  df.info()                              # Structure and types
  df.head()                              # First 5 rows
  df.shape                               # (rows, columns)
  df.describe()                          # Statistical summary

QUICK EXAMPLES:
--------------
# Complete wine classification workflow:
df_classified, counts = run_complete_wine_classification(df)
df = df_classified  # Update main dataframe
quick_classification_summary(df)

# Full data exploration:
deu.explore_like_a_real_analyst(df)

# Create analysis dashboard:
df_analysis = create_sales_dashboard(df)
varieties = interactive_variety_explorer(df_analysis)
analyze_variety_performance(df_analysis, 'Cabernet Sauvignon')

# Save your work:
df.to_pickle('wine_data_classified.pkl')

GETTING MORE HELP:
-----------------
For any function, use:
  help(function_name)     # Detailed documentation
  function_name?          # Quick help in Jupyter
  function_name??         # View source code

For modules:
  help(module_name)       # Module documentation
  dir(module_name)        # List all functions

TROUBLESHOOTING:
---------------
If you get errors:
1. Check column names: df.columns.tolist()
2. Check data types: df.dtypes
3. Check for missing values: df.isnull().sum()
4. Verify data shape: df.shape

Common Issues:
- "Column not found": Check spelling and use df.columns to see available columns
- "Tuple has no attribute": You assigned multiple return values incorrectly
- Memory warnings: Your dataset might be very large

Remember: All utility functions include error handling and will guide you if something goes wrong!
""")

# Quick command shortcuts
def quick_help():
    """Show just the most common commands"""
    print("QUICK REFERENCE:")
    print("help(function_name)           # Get help for any function")
    print("df.info()                     # Check dataframe structure")
    print("df.head()                     # View first 5 rows")
    print("deu.explore_like_a_real_analyst(df)  # Full data exploration")
    print("show_help()                   # This complete help guide")

# Display on import
print("Utility functions loaded! Type 'show_help()' for complete guide or 'quick_help()' for shortcuts.")