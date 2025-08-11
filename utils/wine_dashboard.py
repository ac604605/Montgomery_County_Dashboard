if len(filtered_df) > 0:
            # Data quality summary
            with st.expander("📋 Data Quality Summary"):
                quality_metrics = create_data_quality_summary(filtered_df)
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total Records", f"{quality_metrics['Total Records']:,}")
                    st.metric("Sparkling Wines", f"{quality_metrics['Sparkling Wines']:,}")
                
                with col2:
                    st.metric("Unclassified Countries", f"{quality_metrics['Unclassified Countries']:,}")
                    st.metric("Red Sparkling", f"{quality_metrics['Red Sparkling']:,}")
                
                with col3:
                    st.metric("Unclassified Varieties", f"{quality_metrics['Unclassified Varieties']:,}")
                    st.metric("White Sparkling", f"{quality_metrics['White Sparkling']:,}")
            
            # Main metrics
            metrics = create_summary_metrics(filtered_df)
            
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                st.metric("Retail Sales", f"${metrics['total_sales']:,.0f}")
            with col2:
                st.metric("Warehouse Sales", f"${metrics['warehouse_sales']:,.0f}")
            with col3:
                st.metric("Total Records", f"{metrics['total_wines']:,}")
            with col4:
                st.metric("Unique Varieties", f"{metrics['unique_varieties']:,}")
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
    
    return df

def create_summary_metrics(df):
    """Create summary metrics for the top of dashboard"""
    total_sales = df['RETAIL SALES'].sum()
    warehouse_sales = df['WAREHOUSE SALES'].sum()
    total_wines = len(df)
    unique_varieties = df['final_variety'].nunique()
    sparkling_count = df['total_sparkling'].sum()
    red_sparkling_count = df['red_sparkling'].sum()
    white_sparkling_count = df['white_sparkling'].sum()
    
    return {
        'total_sales': total_sales,
        'warehouse_sales': warehouse_sales,
        'total_wines': total_wines,
        'unique_varieties': unique_varieties,
        'sparkling_count': sparkling_count,
        'red_sparkling_count': red_sparkling_count,
        'white_sparkling_count': white_sparkling_count
    }

def create_monthly_trends_chart(df):
    """Create monthly sales trends chart"""
    monthly_data = df.groupby(['YEAR', 'month_name']).agg({
        'RETAIL SALES': 'sum',
        'WAREHOUSE SALES': 'sum',
        'WINE_NAME_EXTRACTED': 'nunique'
    }).reset_index()
    
    # Create proper date for sorting (convert back to month number for sorting)
    month_order = ['January', 'February', 'March', 'April', 'May', 'June',
                   'July', 'August', 'September', 'October', 'November', 'December']
    monthly_data['month_num'] = monthly_data['month_name'].apply(lambda x: month_order.index(x) + 1)
    monthly_data['Date'] = pd.to_datetime(monthly_data[['YEAR', 'month_num']].assign(day=1))
    monthly_data = monthly_data.sort_values('Date')
    
    # Create subplot with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Add retail sales line
    fig.add_trace(
        go.Scatter(x=monthly_data['Date'], y=monthly_data['RETAIL SALES'], 
                  name="Retail Sales ($)", line=dict(color='#722F37', width=3)),
        secondary_y=False,
    )
    
    # Add warehouse sales line
    fig.add_trace(
        go.Scatter(x=monthly_data['Date'], y=monthly_data['WAREHOUSE SALES'], 
                  name="Warehouse Sales ($)", line=dict(color='#8B4513', width=2)),
        secondary_y=False,
    )
    
    # Add unique products line
    fig.add_trace(
        go.Scatter(x=monthly_data['Date'], y=monthly_data['WINE_NAME_EXTRACTED'], 
                  name="Unique Wines", line=dict(color='orange', width=2, dash='dash')),
        secondary_y=True,
    )
    
    # Update layout
    fig.update_layout(title="Monthly Sales & Product Trends", height=400, hovermode='x unified')
    fig.update_xaxes(title_text="Date")
    fig.update_yaxes(title_text="Sales ($)", secondary_y=False)
    fig.update_yaxes(title_text="Unique Wines", secondary_y=True)
    
    return fig

def create_variety_performance_chart(df, top_n=15):
    """Create top wine varieties performance chart"""
    variety_stats = df.groupby('final_variety').agg({
        'RETAIL SALES': 'sum',
        'WAREHOUSE SALES': 'sum',
        'WINE_NAME_EXTRACTED': 'nunique'
    }).reset_index()
    
    variety_stats = variety_stats.sort_values('RETAIL SALES', ascending=False).head(top_n)
    
    fig = go.Figure()
    
    # Add bar chart
    fig.add_trace(go.Bar(
        x=variety_stats['RETAIL SALES'],
        y=variety_stats['final_variety'],
        orientation='h',
        marker_color='#722F37',
        name='Retail Sales',
        text=[f'${x:,.0f}' for x in variety_stats['RETAIL SALES']],
        textposition='inside'
    ))
    
    fig.update_layout(
        title=f"Top {len(variety_stats)} Wine Varieties by Retail Sales",
        xaxis_title="Retail Sales ($)",
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
        'WINE_NAME_EXTRACTED': 'nunique'
    }).reset_index()
    
    fig = px.pie(
        color_data,
        values='RETAIL SALES',
        names='wine_color',
        title="Retail Sales by Wine Color",
        color_discrete_map={
            'Red': '#722F37',
            'White': '#F5F5DC', 
            'Rosé': '#FF69B4',
            'Unclassified': '#808080'
        }
    )
    
    fig.update_layout(height=400)
    return fig

def create_sparkling_analysis_chart(df):
    """Create sparkling wine breakdown chart"""
    sparkling_data = df[df['total_sparkling'] == True].groupby('sparkling_type').agg({
        'RETAIL SALES': 'sum',
        'WINE_NAME_EXTRACTED': 'nunique'
    }).reset_index()
    
    if len(sparkling_data) > 0:
        fig = px.bar(
            sparkling_data,
            x='sparkling_type',
            y='RETAIL SALES',
            title="Sparkling Wine Sales by Type",
            color='sparkling_type',
            text='RETAIL SALES'
        )
        
        fig.update_traces(texttemplate='$%{text:,.0f}', textposition='outside')
        fig.update_layout(height=400, showlegend=False)
        fig.update_xaxes(title_text="Sparkling Type")
        fig.update_yaxes(title_text="Retail Sales ($)")
        
        return fig
    else:
        # Return empty figure if no sparkling data
        fig = go.Figure()
        fig.add_annotation(text="No sparkling wine data available", 
                          xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        fig.update_layout(title="Sparkling Wine Sales by Type", height=400)
        return fig

def create_country_performance_chart(df):
    """Create country performance chart"""
    country_data = df.groupby('final_country').agg({
        'RETAIL SALES': 'sum',
        'WAREHOUSE SALES': 'sum',
        'WINE_NAME_EXTRACTED': 'nunique'
    }).reset_index()
    
    # Filter out unclassified countries and get top 10
    country_data = country_data[country_data['final_country'] != 'Unclassified']
    country_data = country_data.sort_values('RETAIL SALES', ascending=False).head(10)
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Add retail sales bars
    fig.add_trace(
        go.Bar(x=country_data['final_country'], y=country_data['RETAIL SALES'],
               name="Retail Sales", marker_color='#722F37'),
        secondary_y=False,
    )
    
    # Add warehouse sales bars
    fig.add_trace(
        go.Bar(x=country_data['final_country'], y=country_data['WAREHOUSE SALES'],
               name="Warehouse Sales", marker_color='#8B4513'),
        secondary_y=False,
    )
    
    # Add unique wines line
    fig.add_trace(
        go.Scatter(x=country_data['final_country'], y=country_data['WINE_NAME_EXTRACTED'],
                  mode='lines+markers', name="Unique Wines", line=dict(color='orange')),
        secondary_y=True,
    )
    
    fig.update_layout(title="Top 10 Countries: Sales & Wine Variety", height=400)
    fig.update_xaxes(title_text="Country")
    fig.update_yaxes(title_text="Sales ($)", secondary_y=False)
    fig.update_yaxes(title_text="Unique Wines", secondary_y=True)
    
    return fig

def create_data_quality_summary(df):
    """Create data quality summary"""
    quality_metrics = {
        'Total Records': len(df),
        'Unclassified Countries': len(df[df['final_country'] == 'Unclassified']),
        'Unclassified Varieties': len(df[df['final_variety'] == 'Unclassified']),
        'Unclassified Colors': len(df[df['wine_color'] == 'Unclassified']),
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
        
        # Month filter - using month names
        months = sorted(df['month_name'].unique(), key=lambda x: ['January', 'February', 'March', 'April', 'May', 'June',
                       'July', 'August', 'September', 'October', 'November', 'December'].index(x))
        selected_months = st.sidebar.multiselect("Months", months, default=months)
        
        # Wine type filter
        sparkling_choice = st.sidebar.radio("Wine Type", ["All", "Sparkling Only", "Non-Sparkling Only"])
        
        # Sparkling type filter (only show if relevant)
        if sparkling_choice in ["All", "Sparkling Only"]:
            sparkling_types = [t for t in df['sparkling_type'].unique() if t != 'not_sparkling']
            selected_sparkling_types = st.sidebar.multiselect("Sparkling Types", sparkling_types, default=sparkling_types)
        
        # Wine color filter
        colors = sorted(df['wine_color'].unique())
        selected_colors = st.sidebar.multiselect("Wine Colors", colors, default=colors)
        
        # Variety filter
        top_varieties = df['final_variety'].value_counts().head(50).index.tolist()
        selected_varieties = st.sidebar.multiselect("Wine Varieties (Top 50)", top_varieties, default=top_varieties[:15])
        
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
                    st.metric("Total Records", f"{quality_metrics['Total Records']:,}")
                    st.metric("Sparkling Wines", f"{quality_metrics['Sparkling Wines']:,}")
                
                with col2:
                    st.metric("Unclassified Countries", f"{quality_metrics['Unclassified Countries']:,}")
                    st.metric("Red Sparkling", f"{quality_metrics['Red Sparkling']:,}")
                
                with col3:
                    st.metric("Unclassified Varieties", f"{quality_metrics['Unclassified Varieties']:,}")
                    st.metric("White Sparkling", f"{quality_metrics['White Sparkling']:,}")
            
            # Main metrics
            metrics = create_summary_metrics(filtered_df)
            
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                st.metric("Retail Sales", f"${metrics['total_sales']:,.0f}")
            with col2:
                st.metric("Warehouse Sales", f"${metrics['warehouse_sales']:,.0f}")
            with col3:
                st.metric("Total Records", f"{metrics['total_wines']:,}")
            with col4:
                st.metric("Unique Varieties", f"{metrics['unique_varieties']:,}")
            with col5:
                st.metric("Sparkling Wines", f"{metrics['sparkling_count']:,}")
            
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
                # Sparkling wine analysis
                sparkling_chart = create_sparkling_analysis_chart(chart_df)
                st.plotly_chart(sparkling_chart, use_container_width=True)
            
            # Data table
            with st.expander("🔍 View Filtered Data"):
                # Show key columns only - user-friendly names
                display_cols = ['WINE_NAME_EXTRACTED', 'final_variety', 'wine_color', 'final_country', 
                               'RETAIL SALES', 'WAREHOUSE SALES', 'sparkling_type']
                
                # Rename columns for display
                display_df = filtered_df[display_cols].copy()
                display_df.columns = ['Wine Name', 'Variety', 'Color', 'Country', 
                                     'Retail Sales ($)', 'Warehouse Sales ($)', 'Sparkling Type']
                
                st.dataframe(display_df.head(100), use_container_width=True)
                
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