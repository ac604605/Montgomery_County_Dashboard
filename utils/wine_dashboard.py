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
    .color-filter-section {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
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
    classified_wines = (df['final_variety'] != '').sum()
    classification_rate = (classified_wines / total_wines) * 100
    unique_varieties = df['final_variety'].nunique()
    sparkling_percentage = (df['total_sparkling'].sum() / len(df)) * 100
    
    return {
        'total_sales': total_sales,
        'total_wines': total_wines,
        'classification_rate': classification_rate,
        'unique_varieties': unique_varieties,
        'sparkling_percentage': sparkling_percentage
    }

def create_wine_color_distribution_chart(df):
    """Create wine color distribution chart"""
    color_data = df['wine_color'].value_counts().reset_index()
    color_data.columns = ['Wine Color', 'Count']
    
    # Define colors for the chart based on wine types
    color_map = {
        'Red': '#722F37',
        'White': '#F7E7CE', 
        'Rosé': '#FFB6C1',
        'Sparkling': '#FFD700',
        'Dessert': '#8B4513',
        'Fortified': '#800080'
    }
    
    colors = [color_map.get(color, '#666666') for color in color_data['Wine Color']]
    
    fig = px.pie(
        color_data,
        values='Count',
        names='Wine Color',
        title="Wine Color Distribution",
        color_discrete_sequence=colors
    )
    
    fig.update_layout(height=400, title_font_size=20)
    return fig

def create_sparkling_analysis_chart(df):
    """Create detailed sparkling wine analysis"""
    sparkling_data = df.groupby('sparkling_type').agg({
        'RETAIL SALES': 'sum',
        'ITEM CODE': 'count'
    }).reset_index()
    
    sparkling_data.columns = ['Sparkling Type', 'Sales', 'Count']
    sparkling_data = sparkling_data[sparkling_data['Sparkling Type'] != 'not_sparkling']
    
    if sparkling_data.empty:
        fig = go.Figure()
        fig.add_annotation(text="No sparkling wine data available", 
                          xref="paper", yref="paper",
                          x=0.5, y=0.5, showarrow=False)
        fig.update_layout(height=400, title="Sparkling Wine Analysis")
        return fig
    
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('Sales by Sparkling Type', 'Volume by Sparkling Type'),
        specs=[[{"type": "bar"}, {"type": "bar"}]]
    )
    
    fig.add_trace(
        go.Bar(x=sparkling_data['Sparkling Type'], y=sparkling_data['Sales'], 
               name='Sales ($)', marker_color='#FFD700'),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Bar(x=sparkling_data['Sparkling Type'], y=sparkling_data['Count'], 
               name='Count', marker_color='#FFA500'),
        row=1, col=2
    )
    
    fig.update_layout(height=400, title_text="Sparkling Wine Analysis", 
                      title_font_size=20, showlegend=False)
    
    return fig

def create_monthly_trends_chart(df):
    """Create monthly sales trends chart with color breakdown"""
    monthly_data = df.groupby(['YEAR', 'MONTH', 'wine_color'])['RETAIL SALES'].sum().reset_index()
    monthly_data['Date'] = pd.to_datetime(monthly_data[['YEAR', 'MONTH']].assign(day=1))
    
    fig = px.line(
        monthly_data, 
        x='Date', 
        y='RETAIL SALES',
        color='wine_color',
        title="Monthly Sales Trends by Wine Color",
        labels={'RETAIL SALES': 'Sales ($)', 'Date': 'Date', 'wine_color': 'Wine Color'}
    )
    
    fig.update_layout(
        height=400,
        title_font_size=20
    )
    
    return fig

def create_variety_performance_chart(df, top_n=15):
    """Create top wine varieties performance chart using final_variety"""
    if df.empty or len(df) == 0:
        fig = go.Figure(data=[go.Bar(x=[0], y=['No Data'], orientation='h')])
        fig.update_layout(title="No Data Available", height=600)
        return fig
    
    if 'final_variety' not in df.columns or 'RETAIL SALES' not in df.columns:
        fig = go.Figure(data=[go.Bar(x=[0], y=['Column Missing'], orientation='h')])
        fig.update_layout(title="Required Columns Missing", height=600)
        return fig
    
    clean_df = df.dropna(subset=['final_variety', 'RETAIL SALES'])
    
    if clean_df.empty:
        fig = go.Figure(data=[go.Bar(x=[0], y=['No Valid Data'], orientation='h')])
        fig.update_layout(title="No Valid Data After Cleaning", height=600)
        return fig
    
    variety_sales = clean_df.groupby('final_variety')['RETAIL SALES'].sum().sort_values(ascending=False).head(top_n)
    
    if variety_sales.empty:
        fig = go.Figure(data=[go.Bar(x=[0], y=['No Results'], orientation='h')])
        fig.update_layout(title="No Variety Data Found", height=600)
        return fig
    
    fig = go.Figure(data=[
        go.Bar(
            x=variety_sales.values,
            y=variety_sales.index,
            orientation='h',
            marker_color='#722F37'
        )
    ])
    
    fig.update_layout(
        title=f"Top {len(variety_sales)} Wine Varieties by Sales (Final Classification)",
        xaxis_title="Sales ($)",
        yaxis_title="Wine Variety",
        height=600,
        title_font_size=20,
        yaxis={'categoryorder': 'total ascending'}
    )
    
    return fig

def create_extraction_method_analysis(df):
    """Analyze the success of different variety extraction methods"""
    # Filter for records that have extraction methods
    extraction_df = df[df['extraction_method'].notna()].copy()
    
    if extraction_df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No extraction method data available", 
                          xref="paper", yref="paper",
                          x=0.5, y=0.5, showarrow=False)
        fig.update_layout(height=400, title="Variety Extraction Method Analysis")
        return fig
    
    method_stats = extraction_df.groupby('extraction_method').agg({
        'RETAIL SALES': 'sum',
        'ITEM CODE': 'count',
        'extraction_confidence': 'mean'
    }).round(2).reset_index()
    
    method_stats.columns = ['Method', 'Sales', 'Count', 'Avg Confidence']
    
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Sales by Method', 'Count by Method', 
                       'Average Confidence', 'Method Distribution'),
        specs=[[{"type": "bar"}, {"type": "bar"}],
               [{"type": "bar"}, {"type": "pie"}]]
    )
    
    fig.add_trace(
        go.Bar(x=method_stats['Method'], y=method_stats['Sales'], 
               name='Sales', marker_color='#722F37'),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Bar(x=method_stats['Method'], y=method_stats['Count'], 
               name='Count', marker_color='#8B4513'),
        row=1, col=2
    )
    
    fig.add_trace(
        go.Bar(x=method_stats['Method'], y=method_stats['Avg Confidence'], 
               name='Confidence', marker_color='#2E8B57'),
        row=2, col=1
    )
    
    fig.add_trace(
        go.Pie(values=method_stats['Count'], labels=method_stats['Method'], 
               name='Distribution'),
        row=2, col=2
    )
    
    fig.update_layout(height=600, title_text="Variety Extraction Method Analysis", 
                      title_font_size=20, showlegend=False)
    
    return fig

def create_country_analysis_chart(df):
    """Create country/region analysis chart"""
    country_data = df.groupby('review_country').agg({
        'RETAIL SALES': 'sum',
        'final_variety': 'nunique'
    }).reset_index()
    
    country_data = country_data.sort_values('RETAIL SALES', ascending=False).head(10)
    
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('Sales by Country', 'Variety Diversity by Country'),
        specs=[[{"secondary_y": False}, {"secondary_y": False}]]
    )
    
    fig.add_trace(
        go.Bar(x=country_data['review_country'], y=country_data['RETAIL SALES'], 
               name='Sales', marker_color='#722F37'),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Bar(x=country_data['review_country'], y=country_data['final_variety'], 
               name='Varieties', marker_color='#8B4513'),
        row=1, col=2
    )
    
    fig.update_layout(height=400, title_text="Geographic Analysis", title_font_size=20)
    
    return fig

def main():
    # Header
    st.markdown('<h1 class="main-header">🍷 Wine Market Intelligence Dashboard</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Advanced Analytics on Montgomery County Wine Sales Data with Color Classification</p>', unsafe_allow_html=True)
    
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
        - **Interactive filtering** by year, variety, color, and country
        - **Wine color classification** analysis and filtering
        - **Sparkling wine detection** with detailed breakdown
        - **Variety extraction method** performance analysis
        - **Key performance metrics** with classification success story
        - **Monthly sales trends** with color breakdown
        - **Top variety performance** using final classifications
        - **Geographic analysis** by wine regions
        """)
        return
    
    # Success banner showing classification achievement
    st.markdown("""
    <div class="success-banner">
        🎯 <strong>Enhanced Classification Success:</strong> Achieved comprehensive wine variety identification and color classification using advanced text mining, pattern recognition, and extraction methods on 187k+ records
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

    # Wine Color Filter Section
    st.sidebar.markdown('<div class="color-filter-section">', unsafe_allow_html=True)
    st.sidebar.subheader("🎨 Wine Color Filters")
    
    # Wine color filter
    colors = sorted(df['wine_color'].unique())
    selected_colors = create_filter_with_buttons("Select Wine Colors", colors, "colors")
    
    # Sparkling wine filters
    st.sidebar.subheader("🥂 Sparkling Wine Filters")
    show_sparkling_only = st.sidebar.checkbox("Show Sparkling Wines Only")
    show_red_sparkling = st.sidebar.checkbox("Include Red Sparkling")
    show_white_sparkling = st.sidebar.checkbox("Include White Sparkling", value=True)
    
    sparkling_types = sorted(df['sparkling_type'].unique())
    selected_sparkling_types = st.sidebar.multiselect(
        "Select Sparkling Types",
        options=sparkling_types,
        default=[t for t in sparkling_types if t != 'not_sparkling']
    )
    
    st.sidebar.markdown('</div>', unsafe_allow_html=True)

    # Traditional filters
    st.sidebar.subheader("📅 Traditional Filters")
    
    # Year filter
    years = sorted(df['YEAR'].unique())
    selected_years = create_filter_with_buttons("Select Years", years, "years")

    # Final variety filter (using the consolidated variety column)
    varieties = sorted(df['final_variety'].unique())
    selected_varieties = create_filter_with_buttons("Select Wine Varieties (Final Classification)", varieties, "varieties")

    # Country filter
    countries = sorted(df['review_country'].dropna().unique())
    selected_countries = create_filter_with_buttons("Select Countries", countries, "countries")

    # Winery filter
    wineries = sorted(df['review_winery'].dropna().unique())
    selected_wineries = create_filter_with_buttons("Select Wineries/Producers", wineries, "wineries")

    # Supplier filter
    suppliers = sorted(df['SUPPLIER'].dropna().unique())
    selected_suppliers = create_filter_with_buttons("Select Suppliers", suppliers, "suppliers")

    # Region filter
    regions = sorted(df['review_region_1'].dropna().unique())
    selected_regions = create_filter_with_buttons("Select Regions", regions, "regions")

    # Extraction method filter (new)
    extraction_methods = sorted(df['extraction_method'].dropna().unique())
    selected_extraction_methods = st.sidebar.multiselect(
        "Select Extraction Methods",
        options=extraction_methods,
        default=extraction_methods
    )
    
    # Apply filters
    filtered_df = df.copy()
    
    if selected_years:
        filtered_df = filtered_df[filtered_df['YEAR'].isin(selected_years)]
    
    if selected_colors:
        filtered_df = filtered_df[filtered_df['wine_color'].isin(selected_colors)]
    
    if show_sparkling_only:
        filtered_df = filtered_df[filtered_df['total_sparkling'] == True]
    
    if not show_red_sparkling:
        filtered_df = filtered_df[filtered_df['red_sparkling'] == False]
        
    if not show_white_sparkling:
        filtered_df = filtered_df[filtered_df['white_sparkling'] == False]
    
    if selected_sparkling_types:
        filtered_df = filtered_df[filtered_df['sparkling_type'].isin(selected_sparkling_types)]
    
    if selected_varieties:
        filtered_df = filtered_df[filtered_df['final_variety'].isin(selected_varieties)]
    
    if selected_countries:
        filtered_df = filtered_df[filtered_df['review_country'].isin(selected_countries)]
    
    if selected_wineries:
        filtered_df = filtered_df[filtered_df['review_winery'].isin(selected_wineries)]
    
    if selected_suppliers:
        filtered_df = filtered_df[filtered_df['SUPPLIER'].isin(selected_suppliers)]
    
    if selected_regions:
        filtered_df = filtered_df[filtered_df['review_region_1'].isin(selected_regions)]
    
    if selected_extraction_methods:
        # Only filter if extraction method is not null
        method_filter = (filtered_df['extraction_method'].isin(selected_extraction_methods)) | (filtered_df['extraction_method'].isna())
        filtered_df = filtered_df[method_filter]
    
    # Display filter results
    st.write(f"📊 **Filtered Results:** {filtered_df.shape[0]:,} records out of {df.shape[0]:,} total")
    
    # Create and display metrics
    metrics = create_summary_metrics(filtered_df)
    
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Sales", f"${metrics['total_sales']:,.0f}")
    with col2:
        st.metric("Total Records", f"{metrics['total_wines']:,}")
    with col3:
        st.metric("Classification Rate", f"{metrics['classification_rate']:.1f}%")
    with col4:
        st.metric("Unique Varieties", f"{metrics['unique_varieties']:,}")
    with col5:
        st.metric("Sparkling %", f"{metrics['sparkling_percentage']:.1f}%")
    
    # Create and display charts
    col1, col2 = st.columns(2)
    
    with col1:
        color_chart = create_wine_color_distribution_chart(filtered_df)
        st.plotly_chart(color_chart, use_container_width=True)
    
    with col2:
        sparkling_chart = create_sparkling_analysis_chart(filtered_df)
        st.plotly_chart(sparkling_chart, use_container_width=True)
    
    # Monthly trends with color breakdown
    monthly_chart = create_monthly_trends_chart(filtered_df)
    st.plotly_chart(monthly_chart, use_container_width=True)
    
    # Variety performance chart
    variety_chart = create_variety_performance_chart(filtered_df)
    st.plotly_chart(variety_chart, use_container_width=True)
    
    # Extraction method analysis
    extraction_chart = create_extraction_method_analysis(filtered_df)
    st.plotly_chart(extraction_chart, use_container_width=True)
    
    # Geographic analysis
    country_chart = create_country_analysis_chart(filtered_df)
    st.plotly_chart(country_chart, use_container_width=True)
    
if __name__ == "__main__":
    main()