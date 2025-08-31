import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import io

# Page configuration
st.set_page_config(
    page_title="Control State Wine Market Intelligence",
    page_icon="https://www.rndc-usa.com/wp-content/uploads/2020/12/RNDC_New_Logo_Circle_Red-1.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #722F37;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-container {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #722F37;
    }
    .data-freshness {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 0.25rem;
        padding: 0.5rem;
        margin-bottom: 1rem;
        font-size: 0.9rem;
        color: #856404;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    """Load and cache the wine data"""
    df = pd.read_pickle('data/wine_data_fully_classified.pkl')
    
    # Convert month numbers to names for display
    month_names = {
        1: 'January', 2: 'February', 3: 'March', 4: 'April', 5: 'May', 6: 'June',
        7: 'July', 8: 'August', 9: 'September', 10: 'October', 11: 'November', 12: 'December'
    }
    df['month_name'] = df['MONTH'].map(month_names)
    
    # Replace "Unknown" values with "Unclassified" for better UX
    df['wine_color'] = df['wine_color'].replace('Unknown', 'Unclassified')
    df['final_variety'] = df['final_variety'].replace('Unknown', 'Unclassified')
    df['final_country'] = df['final_country'].fillna('Unclassified')
    df['sparkling_type'] = df['sparkling_type'].replace('Unknown', 'Unclassified')
    
    # Add price tier segmentation based on retail price per bottle (industry standard)
    df['price_per_bottle'] = df['RETAIL SALES'] / df.get('QUANTITY', 1)  # In production, this would use actual bottle count
    
    def categorize_price_tier(price):
        if pd.isna(price) or price <= 0:
            return 'Unclassified'
        elif price < 8:
            return 'Economy (Under $8)'
        elif price < 15:
            return 'Popular ($8-$14.99)'
        elif price < 25:
            return 'Premium ($15-$25)'
        elif price < 50:
            return 'Super-Premium ($26-$49.99)'
        elif price < 100:
            return 'Ultra-Premium ($50-$99.99)'
        else:
            return 'Luxury ($100+)'
    
    df['price_tier'] = df['price_per_bottle'].apply(categorize_price_tier)
    
    # Add quarterly indicators
    df['quarter'] = df['MONTH'].map({
        1: 'Q1', 2: 'Q1', 3: 'Q1',
        4: 'Q2', 5: 'Q2', 6: 'Q2',
        7: 'Q3', 8: 'Q3', 9: 'Q3',
        10: 'Q4', 11: 'Q4', 12: 'Q4'
    })
    
    return df

def create_summary_metrics(df):
    """Create summary metrics for the top of dashboard"""
    control_state_sales = df['RETAIL SALES'].sum()
    licensed_retailer_sales = df['WAREHOUSE SALES'].sum()
    inventory_transfers = df['RETAIL TRANSFERS'].sum()
    total_market_value = control_state_sales + licensed_retailer_sales
    unique_skus = df['ITEM CODE'].nunique()
    unique_varieties = df['final_variety'].nunique()
    sparkling_volume = df['total_sparkling'].sum()
    avg_price_tier = df['price_tier'].mode()[0] if len(df) > 0 else 'N/A'
    
    return {
        'control_state_sales': control_state_sales,
        'licensed_retailer_sales': licensed_retailer_sales,
        'inventory_transfers': inventory_transfers,
        'total_market_value': total_market_value,
        'unique_skus': unique_skus,
        'unique_varieties': unique_varieties,
        'sparkling_volume': sparkling_volume,
        'avg_price_tier': avg_price_tier
    }

def create_price_tier_performance_chart(df):
    """Create price tier performance analysis"""
    tier_data = df.groupby('price_tier').agg({
        'RETAIL SALES': 'sum',
        'WAREHOUSE SALES': 'sum',
        'ITEM CODE': 'nunique'
    }).reset_index()
    
    tier_data['Total_Depletions'] = tier_data['RETAIL SALES'] + tier_data['WAREHOUSE SALES']
    tier_data = tier_data.sort_values('Total_Depletions', ascending=False)
    
    fig = px.bar(
        tier_data,
        x='price_tier',
        y='Total_Depletions',
        title="Market Performance by Price Tier",
        text='Total_Depletions',
        color_discrete_sequence=['#8B0000'] * len(tier_data)  # Same color as Control State Depletions
    )
    
    fig.update_traces(texttemplate='%{text:,.0f} cases', textposition='outside')
    fig.update_layout(height=550, showlegend=False)
    fig.update_xaxes(title_text="Price Tier")
    fig.update_yaxes(title_text="Total Depletions (Cases)")
    
    return fig

def create_quarterly_trends_chart(df):
    """Create quarterly performance trends"""
    quarterly_data = df.groupby(['quarter', 'YEAR']).agg({
        'RETAIL SALES': 'sum',
        'WAREHOUSE SALES': 'sum'
    }).reset_index()
    
    quarterly_data['Total_Depletions'] = quarterly_data['RETAIL SALES'] + quarterly_data['WAREHOUSE SALES']
    
    # Custom color mapping for quarters
    color_map = {
        'Q1': '#228B22',      # Green
        'Q2': '#8B0000',      # Same red as Control State Depletions  
        'Q3': '#DEB887',      # Same gold as Off-Premise Channel
        'Q4': '#191970'       # Deep blue (midnight blue)
    }
    
    fig = px.line(
        quarterly_data,
        x='YEAR',
        y='Total_Depletions',
        color='quarter',
        title="Quarterly Performance Trends",
        markers=True,
        color_discrete_map=color_map
    )
    
    fig.update_layout(
        height=550,
        xaxis_title="Year",
        yaxis_title="Total Depletions ($)",
        legend_title="Quarter"
    )
    
    return fig

def create_performance_benchmark_chart(df, benchmark_type='variety', selected_varieties=None):
    """Create performance benchmarking chart with trend indicators"""
    if benchmark_type == 'variety':
        # If 2 or fewer varieties selected, show top individual products within those varieties
        if selected_varieties and len(selected_varieties) <= 2:
            # Filter to only the selected varieties
            variety_df = df[df['final_variety'].isin(selected_varieties)]
            
            # Group by individual product names to show top SKUs
            perf_data = variety_df.groupby(['WINE_NAME_EXTRACTED', 'final_variety']).agg({
                'RETAIL SALES': 'sum',
                'WAREHOUSE SALES': 'sum'
            }).reset_index()
            
            perf_data['Total_Depletions'] = perf_data['RETAIL SALES'] + perf_data['WAREHOUSE SALES']
            perf_data = perf_data.sort_values('Total_Depletions', ascending=False).head(10)
            
            # Create display labels (show variety in parentheses if multiple varieties)
            if len(selected_varieties) == 1:
                perf_data['display_label'] = perf_data['WINE_NAME_EXTRACTED']
                chart_title = f"Top 10 {selected_varieties[0]} Products"
            else:
                # For multiple varieties, show just the wine name since variety is already in the name
                perf_data['display_label'] = perf_data['WINE_NAME_EXTRACTED']
                chart_title = f"Top 10 Products: {' & '.join(selected_varieties)}"
            
            # Use variety-based colors
            varietal_colors = {
                'Cabernet Sauvignon': '#8B0000', 'Chardonnay': '#F5DEB3', 'Pinot Noir': '#8B0000',
                'Sauvignon Blanc': '#F5DEB3', 'Merlot': '#8B0000', 'Pinot Grigio': '#F5DEB3',
                'Riesling': '#F5DEB3', 'Syrah': '#4B0000', 'Zinfandel': '#8B0000',
                'Moscato': '#F5DEB3', 'Gewürztraminer': '#F5DEB3', 'Chenin Blanc': '#F5DEB3',
                'Sangiovese': '#8B0000'
            }
            
            bar_colors = [varietal_colors.get(variety, '#800050') for variety in perf_data['final_variety']]
            
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                y=perf_data['display_label'],  # Horizontal bar chart
                x=perf_data['Total_Depletions'],
                orientation='h',
                marker_color=bar_colors,
                text=[f"${x:,.0f}" for x in perf_data['Total_Depletions']],
                textposition='inside',
                hovertemplate='<b>%{y}</b><br>Depletions: $%{x:,.0f}<extra></extra>'
            ))
            
            fig.update_layout(
                title=chart_title,
                xaxis_title="Total Depletions ($)",
                yaxis_title="Product Name",
                height=550,
                yaxis={'categoryorder': 'total ascending'},
                showlegend=False
            )
            
        else:
            # Default behavior: show top varieties by depletions
            perf_data = df.groupby('final_variety').agg({
                'RETAIL SALES': 'sum',
                'WAREHOUSE SALES': 'sum'
            }).reset_index()
            perf_data['Total_Depletions'] = perf_data['RETAIL SALES'] + perf_data['WAREHOUSE SALES']
            perf_data = perf_data.sort_values('Total_Depletions', ascending=False).head(10)
            
            # Natural wine colors for varietals
            varietal_colors = {
                'Cabernet Sauvignon': '#8B0000', 'Chardonnay': '#F5DEB3', 'Pinot Noir': '#8B0000',
                'Sauvignon Blanc': '#F5DEB3', 'Merlot': '#8B0000', 'Pinot Grigio': '#F5DEB3',
                'Riesling': '#F5DEB3', 'Syrah': '#4B0000', 'Zinfandel': '#8B0000',
                'Moscato': '#F5DEB3', 'Gewürztraminer': '#F5DEB3', 'Chenin Blanc': '#F5DEB3',
                'Sangiovese': '#8B0000'
            }
            
            # Add mock trend indicators
            np.random.seed(42)
            perf_data['trend'] = np.random.choice(['Great!', 'Wonderful!', 'Take the L!'], size=len(perf_data), p=[0.4, 0.3, 0.3])
            perf_data['change_pct'] = np.random.uniform(-15, 25, size=len(perf_data))
            
            bar_colors = [varietal_colors.get(variety, '#800050') for variety in perf_data['final_variety']]
            
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                x=perf_data['final_variety'],
                y=perf_data['Total_Depletions'],
                text=[f"{trend} {change:.1f}%" for trend, change in zip(perf_data['trend'], perf_data['change_pct'])],
                textposition='outside',
                marker_color=bar_colors,
                hovertemplate='<b>%{x}</b><br>Depletions: $%{y:,.0f}<br>Trend: %{text}<extra></extra>'
            ))
            
            fig.update_layout(
                title="Top 10 Varieties: Performance with Trend Indicators",
                xaxis_title="Wine Variety",
                yaxis_title="Total Depletions ($)",
                height=550,
                showlegend=False
            )
        
    return fig

def create_export_data():
    """Create downloadable data export"""
    # This would be your filtered dataset formatted for business users
    return "Export functionality would provide filtered data in business-friendly format"

def create_monthly_trends_chart(df):
    """Create monthly sales trends chart with Control State vs Licensed Retailer breakdown"""
    monthly_data = df.groupby(['YEAR', 'month_name']).agg({
        'RETAIL SALES': 'sum',
        'WAREHOUSE SALES': 'sum'
    }).reset_index()
    
    # Create proper date for sorting
    month_order = ['January', 'February', 'March', 'April', 'May', 'June',
                   'July', 'August', 'September', 'October', 'November', 'December']
    monthly_data['month_num'] = monthly_data['month_name'].apply(lambda x: month_order.index(x) + 1)
    
    monthly_data['Date'] = pd.to_datetime(
        monthly_data['YEAR'].astype(str) + '-' + 
        monthly_data['month_num'].astype(str).str.zfill(2) + '-01'
    )
    monthly_data = monthly_data.sort_values('Date')
    
    fig = go.Figure()
    
    # Add Control State Sales line
    fig.add_trace(
        go.Scatter(x=monthly_data['Date'], y=monthly_data['RETAIL SALES'], 
                  name="Control State Depletions", line=dict(color='#8B0000', width=3),
                  hovertemplate='<b>Control State Depletions</b><br>%{x}<br>%{y:,.0f} cases<extra></extra>')
    )
    
    # Add Licensed Retailer sales line
    fig.add_trace(
        go.Scatter(x=monthly_data['Date'], y=monthly_data['WAREHOUSE SALES'], 
                  name="Off-Premise Channel", line=dict(color='#DEB887', width=3),
                  hovertemplate='<b>Off-Premise Channel</b><br>%{x}<br>%{y:,.0f} cases<extra></extra>')
    )
    
    fig.update_layout(
        title="Monthly Sales Performance: Control State vs Off-Premise",
        height=550, 
        hovermode='x unified',
        xaxis_title="Date",
        yaxis_title="Depletions (Cases)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    return fig

def main():
    # Header
    st.image("https://www.rndc-usa.com/wp-content/uploads/2020/12/RNDC_New_Logo_Circle_Red-1.png", width=150)
    st.markdown('<h1 class="main-header">Control State Wine Market Intelligence</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Distribution Channel Performance & Category Analytics</p>', unsafe_allow_html=True)
    
    # Data freshness indicator
    st.markdown('''
     <div class="data-freshness">
        <strong>Data as of:</strong> March 2024 (Portfolio Demonstration Dataset)
        |  <strong>Pipeline Processing:</strong> Standard refresh ~20 seconds | Full regex matching ~2.5 hours for entity resolution
        |  <strong>Production Schedule:</strong> Monthly/bi-weekly data refresh, Quarterly entity resolution tuning
    </div>
    ''', unsafe_allow_html=True)
    
    try:
        # Load data
        df = load_data()
        
        # SIDEBAR FILTERS - Enhanced for sales management
        st.sidebar.header("📊 Market Analysis Filters")
        
        # Year filter
        years = sorted(df['YEAR'].unique())
        selected_years = st.sidebar.multiselect("Years", years, default=years)
        
        # Month filter
        months = sorted(df['month_name'].unique(), key=lambda x: ['January', 'February', 'March', 'April', 'May', 'June',
                       'July', 'August', 'September', 'October', 'November', 'December'].index(x))
        selected_months = st.sidebar.multiselect("Months", months, default=months)
        
        # Quarterly filter
        quarters = ['Q1', 'Q2', 'Q3', 'Q4']
        selected_quarters = st.sidebar.multiselect("Quarterly Focus", quarters, default=quarters)
        
        # Price tier filter - KEY ADDITION
        price_tiers = sorted(df['price_tier'].unique())
        selected_price_tiers = st.sidebar.multiselect("Price Tiers", price_tiers, default=price_tiers)
        
        # Wine category filter
        sparkling_choice = st.sidebar.radio("Category Focus", ["All Categories", "Sparkling Only", "Still Wine Only"])
        
        # Wine color filter
        colors = sorted(df['wine_color'].unique())
        selected_colors = st.sidebar.multiselect("Wine Categories", colors, default=colors)
        
        # Variety filter - focus on top performers, exclude blank/empty values
        top_varieties = df[df['final_variety'].notna() & (df['final_variety'] != '') & (df['final_variety'] != 'Unclassified')].groupby('final_variety').agg({'RETAIL SALES': 'sum', 'WAREHOUSE SALES': 'sum'})
        top_varieties['Total'] = top_varieties['RETAIL SALES'] + top_varieties['WAREHOUSE SALES']
        top_varieties = top_varieties.sort_values('Total', ascending=False).head(30).index.tolist()
        selected_varieties = st.sidebar.multiselect("Wine Varieties (Top 30)", top_varieties, default=top_varieties[:15])
        
        # Country filter - clean up empty values with descriptive label
        top_countries = df.groupby('final_country').agg({'RETAIL SALES': 'sum', 'WAREHOUSE SALES': 'sum'})
        top_countries['Total'] = top_countries['RETAIL SALES'] + top_countries['WAREHOUSE SALES']
        top_countries = top_countries.sort_values('Total', ascending=False).head(15)

        # Rename empty/null country values for better UX
        country_list = top_countries.index.tolist()
        if '' in country_list:
            country_list[country_list.index('')] = "Ask me about Data Limitations!"
    
        selected_countries = st.sidebar.multiselect("Countries (Top 15)", country_list, default=country_list[:10])
        
        # APPLY FILTERS
        filtered_df = df.copy()
        
        if selected_years:
            filtered_df = filtered_df[filtered_df['YEAR'].isin(selected_years)]
            
        if selected_months:
            filtered_df = filtered_df[filtered_df['month_name'].isin(selected_months)]
            
        if selected_quarters:
            filtered_df = filtered_df[filtered_df['quarter'].isin(selected_quarters)]
            
        if selected_price_tiers:
            filtered_df = filtered_df[filtered_df['price_tier'].isin(selected_price_tiers)]
            
        if sparkling_choice == "Sparkling Only":
            filtered_df = filtered_df[filtered_df['total_sparkling'] == True]
        elif sparkling_choice == "Still Wine Only":
            filtered_df = filtered_df[filtered_df['total_sparkling'] == False]
        
        if selected_colors:
            filtered_df = filtered_df[filtered_df['wine_color'].isin(selected_colors)]
            
        if selected_varieties:
            filtered_df = filtered_df[filtered_df['final_variety'].isin(selected_varieties)]
            
        if selected_countries:
            filtered_df = filtered_df[filtered_df['final_country'].isin(selected_countries)]
        
        # Show filtering results
        metrics = create_summary_metrics(filtered_df)
        st.write(f"**Market Analysis:** {len(filtered_df):,} depletion records | **Total Case Volume:** {metrics['total_market_value']:,.0f} cases | **SKU Portfolio:** {metrics['unique_skus']:,} products | **Dominant Tier:** {metrics['avg_price_tier']}")
        
        if len(filtered_df) > 0:
            # Main performance metrics
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                st.metric("Control State", f"{metrics['control_state_sales']:,.0f} cases")
            with col2:
                st.metric("Off-Premise", f"{metrics['licensed_retailer_sales']:,.0f} cases")
            with col3:
                st.metric("Transfers", f"{metrics['inventory_transfers']:,.0f} cases")
            with col4:
                st.metric("Active SKUs", f"{metrics['unique_skus']:,}")
            with col5:
                st.metric("Sparkling", f"{metrics['sparkling_volume']:,} cases")
            
            # ENHANCED CHARTS SECTION
            st.subheader("Market Performance & Strategic Analysis")
            
            # Row 1: Trends and Price Tier Analysis
            col1, col2 = st.columns(2)
            
            with col1:
                monthly_chart = create_monthly_trends_chart(filtered_df)
                st.plotly_chart(monthly_chart, use_container_width=True)
            
            with col2:
                price_tier_chart = create_price_tier_performance_chart(filtered_df)
                st.plotly_chart(price_tier_chart, use_container_width=True)
            
            # Row 2: Seasonal Trends and Performance Benchmarks
            col1, col2 = st.columns(2)
            
            with col1:
                quarterly_chart = create_quarterly_trends_chart(filtered_df)
                st.plotly_chart(quarterly_chart, use_container_width=True)
            
            with col2:
                benchmark_chart = create_performance_benchmark_chart(filtered_df, selected_varieties=selected_varieties)
                st.plotly_chart(benchmark_chart, use_container_width=True)
            
            # Export functionality
            st.subheader("📤 Data Export & Reporting")
            col1, col2 = st.columns([1, 3])
            
            with col1:
                # Create downloadable CSV
                csv_data = filtered_df[['WINE_NAME_EXTRACTED', 'final_variety', 'wine_color', 'final_country', 'price_tier',
                                      'RETAIL SALES', 'WAREHOUSE SALES', 'quarter']].copy()
                csv_data.columns = ['Product Name', 'Variety', 'Category', 'Country', 'Price Tier',
                                  'Control State ($)', 'Off-Premise ($)', 'Season']
                
                csv_buffer = io.StringIO()
                csv_data.head(1000).to_csv(csv_buffer, index=False)
                
                st.download_button(
                    label="Download Market Data (CSV)",
                    data=csv_buffer.getvalue(),
                    file_name=f"wine_market_analysis_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
            
            with col2:
                st.info("💡 **Export Note:** CSV includes top 1000 records from filtered dataset. In production, this would include full dataset with additional business metrics and formatting.")
            
            # Data table
            with st.expander("🔍 Detailed Market Data"):
                display_cols = ['WINE_NAME_EXTRACTED', 'final_variety', 'wine_color', 'final_country', 'price_tier',
                               'RETAIL SALES', 'WAREHOUSE SALES', 'quarter']
                
                display_df = filtered_df[display_cols].copy()
                display_df.columns = ['Product Name', 'Variety', 'Category', 'Country', 'Price Tier',
                                     'Control State ($)', 'Off-Premise ($)', 'Season']
                
                st.dataframe(display_df.head(100), use_container_width=True)
                
                if len(filtered_df) > 100:
                    st.info(f"Showing first 100 of {len(filtered_df):,} depletion records")
            
        else:
            st.warning("⚠️ No market data matches your current filter selection. Try expanding your criteria.")
            
    except FileNotFoundError:
        st.error("❌ Data file not found. Please check the file path in the load_data() function.")
    except Exception as e:
        st.error(f"❌ Error loading market data: {str(e)}")
        st.info("Please verify data file format and column structure.")

if __name__ == "__main__":
    main()