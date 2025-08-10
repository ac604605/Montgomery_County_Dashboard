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
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    """Load and cache the wine data"""
    df = pd.read_pickle('wine_data_fully_classified.pkl')
    return df

def create_summary_metrics(df):
    """Create summary metrics for the top of dashboard"""
    total_sales = df['RETAIL SALES'].sum()
    total_wines = len(df)
    unique_varieties = df['final_variety'].nunique()
    sparkling_count = df['total_sparkling'].sum()
    
    return {
        'total_sales': total_sales,
        'total_wines': total_wines,
        'unique_varieties': unique_varieties,
        'sparkling_count': sparkling_count
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
    
    fig.update_layout(height=400, title_font_size=20, showlegend=False)
    return fig

def create_variety_performance_chart(df, top_n=15):
    """Create top wine varieties performance chart"""
    variety_sales = df.groupby('final_variety')['RETAIL SALES'].sum().sort_values(ascending=False).head(top_n)
    
    fig = go.Figure(data=[
        go.Bar(
            x=variety_sales.values,
            y=variety_sales.index,
            orientation='h',
            marker_color='#722F37'
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

def create_wine_color_chart(df):
    """Create wine color distribution chart"""
    color_data = df.groupby('wine_color')['RETAIL SALES'].sum().sort_values(ascending=False)
    
    fig = px.pie(
        values=color_data.values,
        names=color_data.index,
        title="Sales by Wine Color"
    )
    
    fig.update_layout(height=400, title_font_size=20)
    return fig

def create_country_chart(df):
    """Create top countries chart"""
    country_data = df.groupby('review_country')['RETAIL SALES'].sum().sort_values(ascending=False).head(10)
    
    fig = go.Figure(data=[
        go.Bar(
            x=country_data.index,
            y=country_data.values,
            marker_color='#8B4513'
        )
    ])
    
    fig.update_layout(
        title="Top 10 Countries by Sales",
        xaxis_title="Country",
        yaxis_title="Sales ($)",
        height=400,
        title_font_size=20
    )
    
    return fig

def main():
    # Header
    st.markdown('<h1 class="main-header">🍷 Wine Market Intelligence Dashboard</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Montgomery County Wine Sales Analytics</p>', unsafe_allow_html=True)
    
    # Load data
    df = load_data()
    
    # SIMPLE SIDEBAR FILTERS - NO COMPLEX LOGIC
    st.sidebar.header(" Filters")
    
    # Year filter
    years = sorted(df['YEAR'].unique())
    selected_years = st.sidebar.multiselect("Years", years, default=years)
    
    # Month filter  
    months = sorted(df['MONTH'].unique())
    selected_months = st.sidebar.multiselect("Months", months, default=months)
    
    # Supplier filter (increased from 20 to 50)
    top_suppliers = df['SUPPLIER'].value_counts().head(50).index.tolist()
    selected_suppliers = st.sidebar.multiselect("Suppliers (Top 50)", top_suppliers, default=top_suppliers)
    
    # Sparkling vs Non-Sparkling
    sparkling_choice = st.sidebar.radio("Wine Type", ["All", "Sparkling Only", "Non-Sparkling Only"])
    
    # Sparkling type (only show if relevant)
    if sparkling_choice in ["All", "Sparkling Only"]:
        sparkling_types = [t for t in df['sparkling_type'].unique() if t != 'not_sparkling']
        selected_sparkling_types = st.sidebar.multiselect("Sparkling Types", sparkling_types, default=sparkling_types)
    
    # Wine Color (include Unknown to show classification gaps)
    colors = sorted(df['wine_color'].unique())
    selected_colors = st.sidebar.multiselect("Wine Colors", colors, default=colors)
    
    # Final Variety (increased from 30 to 75)
    top_varieties = df['final_variety'].value_counts().head(75).index.tolist()
    selected_varieties = st.sidebar.multiselect("Wine Varieties (Top 75)", top_varieties, default=top_varieties)
    
    # Country (handle empty countries better)
    country_counts = df['review_country'].value_counts()
    top_countries = country_counts.head(20).index.tolist()  # Increased to top 20
    # Add empty string handling
    if '' in country_counts.index:
        top_countries.append('')  # Include empty countries to show data gaps
    selected_countries = st.sidebar.multiselect("Countries (Top 20 + Unknown)", top_countries, default=top_countries)
    
    # APPLY FILTERS - SIMPLE AND CLEAR
    filtered_df = df.copy()
    
    if selected_years:
        filtered_df = filtered_df[filtered_df['YEAR'].isin(selected_years)]
        
    if selected_months:
        filtered_df = filtered_df[filtered_df['MONTH'].isin(selected_months)]
        
    if selected_suppliers:
        filtered_df = filtered_df[filtered_df['SUPPLIER'].isin(selected_suppliers)]
        
    if sparkling_choice == "Sparkling Only":
        filtered_df = filtered_df[filtered_df['total_sparkling'] == True]
        if 'selected_sparkling_types' in locals():
            filtered_df = filtered_df[filtered_df['sparkling_type'].isin(selected_sparkling_types)]
    elif sparkling_choice == "Non-Sparkling Only":
        filtered_df = filtered_df[filtered_df['total_sparkling'] == False]
        
    if selected_colors:
        filtered_df = filtered_df[filtered_df['wine_color'].isin(selected_colors)]
        
    if selected_varieties:
        filtered_df = filtered_df[filtered_df['final_variety'].isin(selected_varieties)]
        
    if selected_countries:
        filtered_df = filtered_df[filtered_df['review_country'].isin(selected_countries)]
    
    # CREATE CHART-SPECIFIC DATAFRAMES - More inclusive for better insights
    # Use broader filters for charts to show more complete data patterns
    chart_df = df.copy()
    
    # Apply only the core filters to chart data (skip the restrictive ones)
    if selected_years:
        chart_df = chart_df[chart_df['YEAR'].isin(selected_years)]
        
    if selected_months:
        chart_df = chart_df[chart_df['MONTH'].isin(selected_months)]
        
    # Skip supplier filter for charts - we want to see all varieties/colors/countries
    
    if sparkling_choice == "Sparkling Only":
        chart_df = chart_df[chart_df['total_sparkling'] == True]
        if 'selected_sparkling_types' in locals():
            chart_df = chart_df[chart_df['sparkling_type'].isin(selected_sparkling_types)]
    elif sparkling_choice == "Non-Sparkling Only":
        chart_df = chart_df[chart_df['total_sparkling'] == False]
    
    # Apply color/variety/country filters to charts too
    if selected_colors:
        chart_df = chart_df[chart_df['wine_color'].isin(selected_colors)]
        
    if selected_varieties:
        chart_df = chart_df[chart_df['final_variety'].isin(selected_varieties)]
        
    if selected_countries:
        chart_df = chart_df[chart_df['review_country'].isin(selected_countries)]
    
    # Show results
    st.write(f" **Table Data:** {len(filtered_df):,} records | **Chart Data:** {len(chart_df):,} records | **Total:** {len(df):,}")
    st.info(" **Charts show more complete data** (ignoring supplier limits) while **table/metrics use filtered data** for focused analysis")
    
    # DEBUG SECTION - Show what's missing
    missing_count = len(df) - len(filtered_df)
    if missing_count > 0:
        st.expander_debug = st.expander(f" Debug: What happened to the missing {missing_count:,} records?")
        with st.expander_debug:
            
            # Check each filter to see what's being excluded
            temp_df = df.copy()
            
            st.write("**Filter Impact Analysis:**")
            
            # Year filter impact
            if selected_years:
                before = len(temp_df)
                temp_df = temp_df[temp_df['YEAR'].isin(selected_years)]
                after = len(temp_df)
                if before != after:
                    st.write(f"- Years filter: Removed {before-after:,} records")
            
            # Month filter impact
            if selected_months:
                before = len(temp_df)
                temp_df = temp_df[temp_df['MONTH'].isin(selected_months)]
                after = len(temp_df)
                if before != after:
                    st.write(f"- Months filter: Removed {before-after:,} records")
            
            # Supplier filter impact
            if selected_suppliers:
                before = len(temp_df)
                temp_df = temp_df[temp_df['SUPPLIER'].isin(selected_suppliers)]
                after = len(temp_df)
                if before != after:
                    st.write(f"- Suppliers filter: Removed {before-after:,} records")
                    # Show which suppliers were excluded
                    excluded_suppliers = df[~df['SUPPLIER'].isin(selected_suppliers)]['SUPPLIER'].value_counts().head(10)
                    if len(excluded_suppliers) > 0:
                        st.write("  - Top excluded suppliers:", excluded_suppliers.to_dict())
            
            # Sparkling filter impact
            if sparkling_choice != "All":
                before = len(temp_df)
                if sparkling_choice == "Sparkling Only":
                    temp_df = temp_df[temp_df['total_sparkling'] == True]
                else:
                    temp_df = temp_df[temp_df['total_sparkling'] == False]
                after = len(temp_df)
                if before != after:
                    st.write(f"- Sparkling filter: Removed {before-after:,} records")
            
            # Wine color filter impact
            if selected_colors:
                before = len(temp_df)
                temp_df = temp_df[temp_df['wine_color'].isin(selected_colors)]
                after = len(temp_df)
                if before != after:
                    st.write(f"- Wine color filter: Removed {before-after:,} records")
                    # Show which colors were excluded
                    excluded_colors = df[~df['wine_color'].isin(selected_colors)]['wine_color'].value_counts()
                    if len(excluded_colors) > 0:
                        st.write("  - Excluded colors:", excluded_colors.to_dict())
            
            # Variety filter impact
            if selected_varieties:
                before = len(temp_df)
                temp_df = temp_df[temp_df['final_variety'].isin(selected_varieties)]
                after = len(temp_df)
                if before != after:
                    st.write(f"- Varieties filter: Removed {before-after:,} records")
                    # Show top excluded varieties
                    excluded_varieties = df[~df['final_variety'].isin(selected_varieties)]['final_variety'].value_counts().head(10)
                    if len(excluded_varieties) > 0:
                        st.write("  - Top excluded varieties:", excluded_varieties.to_dict())
            
            # Country filter impact  
            if selected_countries:
                before = len(temp_df)
                temp_df = temp_df[temp_df['review_country'].isin(selected_countries)]
                after = len(temp_df)
                if before != after:
                    st.write(f"- Countries filter: Removed {before-after:,} records")
                    # Show excluded countries
                    excluded_countries = df[~df['review_country'].isin(selected_countries)]['review_country'].value_counts().head(10)
                    if len(excluded_countries) > 0:
                        st.write("  - Top excluded countries:", excluded_countries.to_dict())
            
            # Show sample records that were filtered out
            st.write("**Sample of Excluded Records:**")
            excluded_df = df[~df.index.isin(filtered_df.index)]
            if len(excluded_df) > 0:
                sample_excluded = excluded_df[['ITEM DESCRIPTION', 'final_variety', 'wine_color', 'review_country', 'SUPPLIER']].head(10)
                st.dataframe(sample_excluded)
                
                # Show common patterns in excluded data
                st.write("**Common Patterns in Excluded Data:**")
                st.write("- Final varieties:", excluded_df['final_variety'].value_counts().head(10).to_dict())
                st.write("- Wine colors:", excluded_df['wine_color'].value_counts().to_dict())
                st.write("- Countries:", excluded_df['review_country'].value_counts().head(5).to_dict())
    
    # Create and display metrics
    if len(filtered_df) > 0:
        metrics = create_summary_metrics(filtered_df)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Sales", f"${metrics['total_sales']:,.0f}")
        with col2:
            st.metric("Total Records", f"{metrics['total_wines']:,}")
        with col3:
            st.metric("Unique Varieties", f"{metrics['unique_varieties']:,}")
        with col4:
            st.metric("Sparkling Wines", f"{metrics['sparkling_count']:,}")
        
        # Create charts using chart_df (more complete data)
        col1, col2 = st.columns(2)
        
        with col1:
            monthly_chart = create_monthly_trends_chart(chart_df)
            st.plotly_chart(monthly_chart, use_container_width=True)
        
        with col2:
            color_chart = create_wine_color_chart(chart_df)
            st.plotly_chart(color_chart, use_container_width=True)
        
        # Variety performance chart using chart_df
        variety_chart = create_variety_performance_chart(chart_df)
        st.plotly_chart(variety_chart, use_container_width=True)
        
        # Country chart using chart_df
        country_chart = create_country_chart(chart_df)
        st.plotly_chart(country_chart, use_container_width=True)
        
    else:
        st.warning("No data matches your current filters. Try expanding your selection!")

if __name__ == "__main__":
    main()