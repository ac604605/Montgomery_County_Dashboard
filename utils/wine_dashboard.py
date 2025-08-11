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
    .metric-container {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #722F37;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    """Load and cache the wine data"""
    # Update this path to match your actual data file
    df = pd.read_pickle('wine_data_fully_classified.pkl')
    return df

def create_summary_metrics(df):
    """Create summary metrics for the top of dashboard"""
    total_sales = df['RETAIL SALES'].sum()
    total_wines = len(df)
    unique_varieties = df['final_variety'].nunique()
    sparkling_count = df['total_sparkling'].sum()
    avg_match_score = df['REVIEW_MATCH_SCORE'].mean()
    
    return {
        'total_sales': total_sales,
        'total_wines': total_wines,
        'unique_varieties': unique_varieties,
        'sparkling_count': sparkling_count,
        'avg_match_score': avg_match_score
    }

def create_monthly_trends_chart(df):
    """Create monthly sales trends chart"""
    monthly_data = df.groupby(['YEAR', 'MONTH']).agg({
        'RETAIL SALES': 'sum',
        'ITEM CODE': 'nunique'
    }).reset_index()
    monthly_data['Date'] = pd.to_datetime(monthly_data[['YEAR', 'MONTH']].assign(day=1))
    
    # Create subplot with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Add sales line
    fig.add_trace(
        go.Scatter(x=monthly_data['Date'], y=monthly_data['RETAIL SALES'], 
                  name="Sales ($)", line=dict(color='#722F37')),
        secondary_y=False,
    )
    
    # Add unique products line
    fig.add_trace(
        go.Scatter(x=monthly_data['Date'], y=monthly_data['ITEM CODE'], 
                  name="Unique Products", line=dict(color='#8B4513')),
        secondary_y=True,
    )
    
    # Update layout
    fig.update_layout(title="Monthly Sales & Product Trends", height=400)
    fig.update_xaxes(title_text="Date")
    fig.update_yaxes(title_text="Sales ($)", secondary_y=False)
    fig.update_yaxes(title_text="Unique Products", secondary_y=True)
    
    return fig

def create_variety_performance_chart(df, top_n=15):
    """Create top wine varieties performance chart"""
    variety_stats = df.groupby('final_variety').agg({
        'RETAIL SALES': 'sum',
        'ITEM CODE': 'nunique',
        'REVIEW_MATCH_SCORE': 'mean'
    }).reset_index()
    
    variety_stats = variety_stats.sort_values('RETAIL SALES', ascending=False).head(top_n)
    
    fig = go.Figure()
    
    # Add bar chart
    fig.add_trace(go.Bar(
        x=variety_stats['RETAIL SALES'],
        y=variety_stats['final_variety'],
        orientation='h',
        marker_color='#722F37',
        name='Sales',
        text=[f'${x:,.0f}' for x in variety_stats['RETAIL SALES']],
        textposition='inside'
    ))
    
    fig.update_layout(
        title=f"Top {len(variety_stats)} Wine Varieties by Sales",
        xaxis_title="Sales ($)",
        yaxis_title="Wine Variety",
        height=600,
        yaxis={'categoryorder': 'total ascending'},
        showlegend=False
    )
    
    return fig

def create_wine_color_chart(df):
    """Create wine color distribution chart"""
    color_data = df.groupby('wine_color').agg({
        'RETAIL SALES': 'sum',
        'ITEM CODE': 'nunique'
    }).reset_index()
    
    fig = px.pie(
        color_data,
        values='RETAIL SALES',
        names='wine_color',
        title="Sales by Wine Color",
        color_discrete_map={
            'Red': '#722F37',
            'White': '#F5F5DC', 
            'Rosé': '#FF69B4',
            'Unknown': '#808080'
        }
    )
    
    fig.update_layout(height=400)
    return fig

def create_country_performance_chart(df):
    """Create country performance chart with match score overlay"""
    country_data = df.groupby('final_country').agg({
        'RETAIL SALES': 'sum',
        'REVIEW_MATCH_SCORE': 'mean',
        'ITEM CODE': 'nunique'
    }).reset_index()
    
    # Filter out null countries and get top 10
    country_data = country_data[country_data['final_country'].notna()]
    country_data = country_data.sort_values('RETAIL SALES', ascending=False).head(10)
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Add sales bars
    fig.add_trace(
        go.Bar(x=country_data['final_country'], y=country_data['RETAIL SALES'],
               name="Sales", marker_color='#722F37'),
        secondary_y=False,
    )
    
    # Add match score line
    fig.add_trace(
        go.Scatter(x=country_data['final_country'], y=country_data['REVIEW_MATCH_SCORE'],
                  mode='lines+markers', name="Avg Match Score", line=dict(color='orange')),
        secondary_y=True,
    )
    
    fig.update_layout(title="Top 10 Countries: Sales vs Review Match Quality", height=400)
    fig.update_xaxes(title_text="Country")
    fig.update_yaxes(title_text="Sales ($)", secondary_y=False)
    fig.update_yaxes(title_text="Average Match Score", secondary_y=True, range=[0, 1])
    
    return fig

def create_match_quality_analysis(df):
    """Analyze review match quality"""
    match_bins = pd.cut(df['REVIEW_MATCH_SCORE'], bins=5, labels=['Very Low', 'Low', 'Medium', 'High', 'Very High'])
    match_analysis = df.groupby(match_bins).agg({
        'RETAIL SALES': 'sum',
        'ITEM CODE': 'nunique'
    }).reset_index()
    
    fig = px.bar(match_analysis, x='REVIEW_MATCH_SCORE', y='RETAIL SALES',
                title="Sales by Review Match Quality",
                labels={'REVIEW_MATCH_SCORE': 'Match Quality', 'RETAIL SALES': 'Sales ($)'},
                color='RETAIL SALES', color_continuous_scale='Viridis')
    
    fig.update_layout(height=400)
    return fig

def create_data_quality_summary(df):
    """Create data quality summary"""
    quality_metrics = {
        'Total Records': len(df),
        'Records with Reviews': len(df[df['REVIEW_MATCH_STATUS'] != 'No Match']),
        'Avg Match Score': df['REVIEW_MATCH_SCORE'].mean(),
        'Missing Countries': df['final_country'].isna().sum(),
        'Missing Varieties': df['final_variety'].isna().sum(),
        'Sparkling Wines': df['total_sparkling'].sum(),
        'Red Sparkling': df['red_sparkling'].sum(),
        'White Sparkling': df['white_sparkling'].sum()
    }
    
    return quality_metrics

def main():
    # Header
    st.markdown('<h1 class="main-header">🍷 Wine Market Intelligence Dashboard</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Montgomery County Wine Sales Analytics</p>', unsafe_allow_html=True)
    
    try:
        # Load data
        df = load_data()
        
        # SIDEBAR FILTERS
        st.sidebar.header("🔍 Filters")
        
        # Year filter
        years = sorted(df['YEAR'].unique())
        selected_years = st.sidebar.multiselect("Years", years, default=years)
        
        # Month filter  
        months = sorted(df['MONTH'].unique())
        selected_months = st.sidebar.multiselect("Months", months, default=months)
        
        # Supplier filter
        top_suppliers = df['SUPPLIER'].value_counts().head(50).index.tolist()
        selected_suppliers = st.sidebar.multiselect("Suppliers (Top 50)", top_suppliers, default=top_suppliers[:10])
        
        # Wine type filter
        sparkling_choice = st.sidebar.radio("Wine Type", ["All", "Sparkling Only", "Non-Sparkling Only"])
        
        # Match quality filter
        match_threshold = st.sidebar.slider("Minimum Match Score", 0.0, 1.0, 0.0, 0.1)
        
        # Wine color filter
        colors = sorted(df['wine_color'].unique())
        selected_colors = st.sidebar.multiselect("Wine Colors", colors, default=colors)
        
        # Variety filter
        top_varieties = df['final_variety'].value_counts().head(75).index.tolist()
        selected_varieties = st.sidebar.multiselect("Wine Varieties (Top 75)", top_varieties, default=top_varieties[:20])
        
        # Country filter
        top_countries = df['final_country'].value_counts().head(20).index.tolist()
        selected_countries = st.sidebar.multiselect("Countries (Top 20)", top_countries, default=top_countries[:10])
        
        # APPLY FILTERS
        filtered_df = df.copy()
        
        if selected_years:
            filtered_df = filtered_df[filtered_df['YEAR'].isin(selected_years)]
            
        if selected_months:
            filtered_df = filtered_df[filtered_df['MONTH'].isin(selected_months)]
            
        if selected_suppliers:
            filtered_df = filtered_df[filtered_df['SUPPLIER'].isin(selected_suppliers)]
            
        if sparkling_choice == "Sparkling Only":
            filtered_df = filtered_df[filtered_df['total_sparkling'] == True]
        elif sparkling_choice == "Non-Sparkling Only":
            filtered_df = filtered_df[filtered_df['total_sparkling'] == False]
        
        # Apply match score filter
        filtered_df = filtered_df[filtered_df['REVIEW_MATCH_SCORE'] >= match_threshold]
        
        if selected_colors:
            filtered_df = filtered_df[filtered_df['wine_color'].isin(selected_colors)]
            
        if selected_varieties:
            filtered_df = filtered_df[filtered_df['final_variety'].isin(selected_varieties)]
            
        if selected_countries:
            filtered_df = filtered_df[filtered_df['final_country'].isin(selected_countries)]
        
        # Create chart data (less restrictive for better insights)
        chart_df = df.copy()
        
        # Apply core filters only
        if selected_years:
            chart_df = chart_df[chart_df['YEAR'].isin(selected_years)]
            
        if selected_months:
            chart_df = chart_df[chart_df['MONTH'].isin(selected_months)]
            
        if sparkling_choice == "Sparkling Only":
            chart_df = chart_df[chart_df['total_sparkling'] == True]
        elif sparkling_choice == "Non-Sparkling Only":
            chart_df = chart_df[chart_df['total_sparkling'] == False]
        
        chart_df = chart_df[chart_df['REVIEW_MATCH_SCORE'] >= match_threshold]
        
        # Apply other filters to charts too if they're not too restrictive
        if len(selected_colors) > 1:  # Only if multiple colors selected
            chart_df = chart_df[chart_df['wine_color'].isin(selected_colors)]
        
        # Show filtering results
        st.write(f"📊 **Filtered Data:** {len(filtered_df):,} records | **Chart Data:** {len(chart_df):,} records | **Total:** {len(df):,}")
        
        if len(filtered_df) > 0:
            # Data quality summary
            with st.expander("📋 Data Quality Summary"):
                quality_metrics = create_data_quality_summary(filtered_df)
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Match Coverage", f"{(quality_metrics['Records with Reviews']/quality_metrics['Total Records']*100):.1f}%")
                    st.metric("Avg Match Score", f"{quality_metrics['Avg Match Score']:.3f}")
                
                with col2:
                    st.metric("Missing Countries", f"{quality_metrics['Missing Countries']:,}")
                    st.metric("Sparkling Wines", f"{quality_metrics['Sparkling Wines']:,}")
                
                with col3:
                    st.metric("Red Sparkling", f"{quality_metrics['Red Sparkling']:,}")
                    st.metric("White Sparkling", f"{quality_metrics['White Sparkling']:,}")
            
            # Main metrics
            metrics = create_summary_metrics(filtered_df)
            
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                st.metric("Total Sales", f"${metrics['total_sales']:,.0f}")
            with col2:
                st.metric("Total Records", f"{metrics['total_wines']:,}")
            with col3:
                st.metric("Unique Varieties", f"{metrics['unique_varieties']:,}")
            with col4:
                st.metric("Sparkling Wines", f"{metrics['sparkling_count']:,}")
            with col5:
                st.metric("Avg Match Score", f"{metrics['avg_match_score']:.3f}")
            
            # Charts
            st.subheader("📈 Sales Trends & Analysis")
            
            col1, col2 = st.columns(2)
            
            with col1:
                monthly_chart = create_monthly_trends_chart(chart_df)
                st.plotly_chart(monthly_chart, use_container_width=True)
            
            with col2:
                color_chart = create_wine_color_chart(chart_df)
                st.plotly_chart(color_chart, use_container_width=True)
            
            # Variety performance chart
            variety_chart = create_variety_performance_chart(chart_df)
            st.plotly_chart(variety_chart, use_container_width=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Country performance chart
                country_chart = create_country_performance_chart(chart_df)
                st.plotly_chart(country_chart, use_container_width=True)
            
            with col2:
                # Match quality analysis
                match_chart = create_match_quality_analysis(chart_df)
                st.plotly_chart(match_chart, use_container_width=True)
            
            # Data table
            with st.expander("🔍 View Filtered Data"):
                # Show key columns only
                display_cols = ['ITEM DESCRIPTION', 'final_variety', 'wine_color', 'final_country', 
                               'RETAIL SALES', 'REVIEW_MATCH_SCORE', 'SUPPLIER']
                st.dataframe(filtered_df[display_cols].head(100), use_container_width=True)
                
                if len(filtered_df) > 100:
                    st.info(f"Showing first 100 of {len(filtered_df):,} records")
            
        else:
            st.warning("❌ No data matches your current filters. Try expanding your selection!")
            
    except FileNotFoundError:
        st.error("❌ Data file not found. Please check the file path in the load_data() function.")
    except Exception as e:
        st.error(f"❌ Error loading data: {str(e)}")
        st.info("Please check your data file format and column names.")

if __name__ == "__main__":
    main()