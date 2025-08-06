import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

# Page configuration
st.set_page_config(
    page_title="Wine Market Intelligence Dashboard",
    page_icon="🍷",
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
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 0.25rem solid #722F37;
    }
    .success-banner {
        background-color: #d4edda;
        color: #155724;
        padding: 0.75rem;
        border-radius: 0.25rem;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    """Load and cache the wine data"""
    df = pd.read_pickle('wine_data_fully_classified.pkl')
    return df
    
df = load_data()
    
def create_summary_metrics(df):
    """Create summary metrics for the top of dashboard"""
    total_sales = df['RETAIL SALES'].sum()
    total_wines = len(df)
    classified_wines = (df['review_variety'] != '').sum()
    classification_rate = (classified_wines / total_wines) * 100
    unique_varieties = df['review_variety'].nunique()
    
    return {
        'total_sales': total_sales,
        'total_wines': total_wines,
        'classification_rate': classification_rate,
        'unique_varieties': unique_varieties
    }

def create_monthly_trends_chart(df):
    """Create monthly sales trends chart"""
    monthly_data = df.groupby(['YEAR', 'MONTH'])['RETAIL SALES'].sum().reset_index()
    monthly_data['Date'] = pd.to_datetime(monthly_data[['YEAR', 'MONTH']].assign(day=1))
    
    fig = px.line(
        monthly_data, 
        x='Date', 
        y='RETAIL SALES',
        title="Monthly Sales Trends",
        labels={'RETAIL SALES': 'Sales ($)', 'Date': 'Date'}
    )
    
    fig.update_layout(
        height=400,
        title_font_size=20,
        showlegend=False
    )
    
    return fig

def create_variety_performance_chart(df, top_n=15):
    """Create top wine varieties performance chart"""
    # Check if dataframe is empty or has no data
    if df.empty or len(df) == 0:
        fig = go.Figure(data=[go.Bar(x=[0], y=['No Data'], orientation='h')])
        fig.update_layout(title="No Data Available", height=600)
        return fig
    
    # Check if the required columns exist
    if 'review_variety' not in df.columns or 'RETAIL SALES' not in df.columns:
        fig = go.Figure(data=[go.Bar(x=[0], y=['Column Missing'], orientation='h')])
        fig.update_layout(title="Required Columns Missing", height=600)
        return fig
    
    # Remove any null values
    clean_df = df.dropna(subset=['review_variety', 'RETAIL SALES'])
    
    if clean_df.empty:
        fig = go.Figure(data=[go.Bar(x=[0], y=['No Valid Data'], orientation='h')])
        fig.update_layout(title="No Valid Data After Cleaning", height=600)
        return fig
    
    # Group and aggregate
    variety_sales = clean_df.groupby('review_variety')['RETAIL SALES'].sum().sort_values(ascending=False).head(top_n)
    
    # Check if we have results
    if variety_sales.empty:
        fig = go.Figure(data=[go.Bar(x=[0], y=['No Results'], orientation='h')])
        fig.update_layout(title="No Variety Data Found", height=600)
        return fig
    
    # Create the chart using go.Figure instead of px.bar
    fig = go.Figure(data=[
        go.Bar(
            x=variety_sales.values,
            y=variety_sales.index,
            orientation='h'
        )
    ])
    
    fig.update_layout(
        title=f"Top {len(variety_sales)} Wine Varieties by Sales",
        xaxis_title="Sales ($)",
        yaxis_title="Wine Variety",
        height=600,
        title_font_size=20,
        yaxis={'categoryorder': 'total ascending'}
    )
    
    return fig

def create_country_analysis_chart(df):
    """Create country/region analysis chart"""
    country_data = df.groupby('review_country').agg({
        'RETAIL SALES': 'sum',
        'review_variety': 'nunique'
    }).reset_index()
    
    country_data = country_data.sort_values('RETAIL SALES', ascending=False).head(10)
    
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('Sales by Country', 'Variety Diversity by Country'),
        specs=[[{"secondary_y": False}, {"secondary_y": False}]]
    )
    
    fig.add_trace(
        go.Bar(x=country_data['review_country'], y=country_data['RETAIL SALES'], name='Sales'),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Bar(x=country_data['review_country'], y=country_data['review_variety'], name='Varieties'),
        row=1, col=2
    )
    
    fig.update_layout(height=400, title_text="Geographic Analysis", title_font_size=20)
    
    return fig

def create_classification_success_chart(df):
    """Show the success of the wine classification system"""
    classification_data = df['REVIEW_MATCH_STATUS'].value_counts().reset_index()
    classification_data.columns = ['Method', 'Count']
    
    # Filter out nulls and create meaningful labels
    classification_data = classification_data[classification_data['Method'].notna()]
    classification_data['Method'] = classification_data['Method'].replace({
        'abbreviation_match': 'Abbreviation Recognition',
        'regional_match': 'Regional Pattern',
        'brand_match': 'Brand Recognition',
        'color_match': 'Color Classification',
        'sparkling_match': 'Sparkling Detection',
        'no_match': 'No Classification'
    })
    
    fig = px.pie(
        classification_data,
        values='Count',
        names='Method',
        title="Wine Classification Method Success"
    )
    
    fig.update_layout(height=400, title_font_size=20)
    
    return fig

def main():
    # Header
    st.markdown('<h1 class="main-header">🍷 Wine Market Intelligence Dashboard</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Advanced Analytics on Montgomery County Wine Sales Data</p>', unsafe_allow_html=True)
    
    # Load data
    df = load_data()
    
    # If no data loaded (demo mode), show instructions
    if df is None:
        st.markdown("""
        ## 🚀 Setup Instructions
        
        1. Save this code as `wine_dashboard.py`
        2. Replace the `load_data()` function with:
        ```python
        @st.cache_data
        def load_data():
            df = pd.read_pickle('wine_data_fully_classified.pkl')
            return df
        ```
        3. Run with: `streamlit run wine_dashboard.py`
        
        ## 📊 Dashboard Features
        - **Interactive filtering** by year, variety, and country
        - **Key performance metrics** with your classification success story
        - **Monthly sales trends** with hover details
        - **Top variety performance** rankings
        - **Geographic analysis** by wine regions
        - **Classification method breakdown** showing your ML pipeline success
        """)
        return
    
    # Success banner showing classification achievement
    st.markdown("""
    <div class="success-banner">
        🎯 <strong>Classification Success:</strong> Achieved 89.9% wine variety identification using advanced text mining and pattern recognition on 187k+ records
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar filters
    
    st.sidebar.header("📊 Filter Options")

    # Helper function for select all/deselect all buttons
    def create_filter_with_buttons(label, options, key_prefix, default_selection=None):
        """Create a multiselect with Select All/Deselect All buttons"""
        col1, col2 = st.sidebar.columns(2)
        
        # Initialize session state if not exists
        if f"{key_prefix}_selected" not in st.session_state:
            st.session_state[f"{key_prefix}_selected"] = default_selection or options[:10] if len(options) > 10 else options
        
        with col1:
            if st.button("Select All", key=f"{key_prefix}_all"):
                st.session_state[f"{key_prefix}_selected"] = options
        
        with col2:
            if st.button("Deselect All", key=f"{key_prefix}_none"):
                st.session_state[f"{key_prefix}_selected"] = []
        
        selected = st.sidebar.multiselect(
            label,
            options=options,
            default=st.session_state[f"{key_prefix}_selected"],
            key=f"{key_prefix}_multiselect"
        )
        
        # Update session state
        st.session_state[f"{key_prefix}_selected"] = selected
        return selected

    # Year filter
    years = sorted(df['YEAR'].unique())
    selected_years = create_filter_with_buttons("Select Years", years, "years")

    # Variety filter
    varieties = sorted(df['review_variety'].unique())
    selected_varieties = create_filter_with_buttons("Select Wine Varieties", varieties, "varieties")

    # Country filter
    countries = sorted(df['review_country'].dropna().unique())
    selected_countries = create_filter_with_buttons("Select Countries", countries, "countries")

    # Winery filter (Producer/Brand equivalent)
    wineries = sorted(df['review_winery'].dropna().unique())
    selected_wineries = create_filter_with_buttons("Select Wineries/Producers", wineries, "wineries")

    # Supplier filter
    suppliers = sorted(df['SUPPLIER'].dropna().unique())
    selected_suppliers = create_filter_with_buttons("Select Suppliers", suppliers, "suppliers")

       # Region filter (additional drill-down option)
    regions = sorted(df['review_region_1'].dropna().unique())
    selected_regions = create_filter_with_buttons("Select Regions", regions, "regions")
    
    # Apply filters
    filtered_df = df.copy()
    
    if selected_years:
        filtered_df = filtered_df[filtered_df['YEAR'].isin(selected_years)]
    
    if selected_varieties:
        filtered_df = filtered_df[filtered_df['review_variety'].isin(selected_varieties)]
    
    if selected_countries:
        filtered_df = filtered_df[filtered_df['review_country'].isin(selected_countries)]
    
    if selected_wineries:
        filtered_df = filtered_df[filtered_df['review_winery'].isin(selected_wineries)]
    
    if selected_suppliers:
        filtered_df = filtered_df[filtered_df['SUPPLIER'].isin(selected_suppliers)]
    
    if selected_regions:
        filtered_df = filtered_df[filtered_df['review_region_1'].isin(selected_regions)]
    
    # Debug info (temporary)
    st.write(f"Filtered data shape: {filtered_df.shape}")
    
    # Create and display metrics
    metrics = create_summary_metrics(filtered_df)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Sales", f"${metrics['total_sales']:,.0f}")
    with col2:
        st.metric("Total Records", f"{metrics['total_wines']:,}")
    with col3:
        st.metric("Classification Rate", f"{metrics['classification_rate']:.1f}%")
    with col4:
        st.metric("Unique Varieties", f"{metrics['unique_varieties']:,}")
    
    # Create and display charts
    col1, col2 = st.columns(2)
    
    with col1:
        monthly_chart = create_monthly_trends_chart(filtered_df)
        st.plotly_chart(monthly_chart, use_container_width=True)
    
    with col2:
        variety_chart = create_variety_performance_chart(filtered_df)
        st.plotly_chart(variety_chart, use_container_width=True)
    
    # Additional charts
    country_chart = create_country_analysis_chart(filtered_df)
    st.plotly_chart(country_chart, use_container_width=True)
    
    classification_chart = create_classification_success_chart(filtered_df)
    st.plotly_chart(classification_chart, use_container_width=True)
    
if __name__ == "__main__":
    main()