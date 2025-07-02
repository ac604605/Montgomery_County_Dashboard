import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

# Configure the page - only run if in streamlit environment
try:
    st.set_page_config(
        page_title="🍷 Wine Sales Analytics Dashboard",
        page_icon="🍷",
        layout="wide",
        initial_sidebar_state="expanded"
    )
except Exception:
    # Running in Jupyter or other environment
    pass

# Custom CSS for better styling
st.markdown("""
<style>
    .main > div {
        padding-top: 2rem;
    }
    .stMetric {
        background-color: #f0f2f6;
        border: 1px solid #e1e5e9;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12);
    }
    .metric-container {
        display: flex;
        justify-content: space-around;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# Sample data - replace with your actual data loading
def load_data():
    # Sample wine sales data
    countries_data = {
        'Country': ['US', 'Italy', 'France', 'New Zealand', 'Australia', 'Spain', 'Argentina', 'Portugal', 'Chile', 'Germany'],
        'Sales': [914734.89, 128143.53, 103706.88, 77030.45, 73642.82, 68144.0, 34759.87, 30964.95, 19913.72, 15085.19],
        'Unique_Wines': [7091, 2461, 2643, 228, 412, 768, 430, 398, 495, 130],
        'Avg_Price': [129.12, 52.09, 39.25, 337.83, 178.85, 88.74, 80.84, 77.75, 40.23, 116.04]
    }
    
    suppliers_data = {
        'Supplier': ['A VINTNERS SELECTIONS', 'A I G WINE & SPIRITS', 'AMERICAN BEVERAGE CORPORATION', 
                    'AIKO IMPORTERS INC', 'ALLIED IMPORTERS USA LTD', 'A&E INC', '8 VINI INC', 'A&W BORDERS LLC'],
        'Sales': [42695.53, 206.53, 94.69, 19.73, 24.0, 11.49, 3.53, 1.3],
        'Wine_Count': [245, 12, 8, 3, 2, 1, 1, 1]
    }
    
    # Create time series data
    dates = pd.date_range('2023-01-01', '2024-12-31', freq='M')
    monthly_sales = np.random.normal(75000, 15000, len(dates))
    monthly_sales = np.cumsum(np.random.normal(0, 5000, len(dates))) + monthly_sales
    
    time_series_data = {
        'Date': dates,
        'Monthly_Sales': monthly_sales,
        'Orders': np.random.poisson(150, len(dates))
    }
    
    return pd.DataFrame(countries_data), pd.DataFrame(suppliers_data), pd.DataFrame(time_series_data)

# Check if we're in a Streamlit environment
try:
    countries_df, suppliers_df, time_series_df = load_data()
except:
    # If caching fails, load data without caching
    countries_df, suppliers_df, time_series_df = load_data()

# Header
st.title("🍷 Wine Sales Analytics Dashboard")
st.markdown("**Comprehensive insights into global wine sales performance**")
st.divider()

# Sidebar filters
st.sidebar.header("🔍 Filters & Controls")

# Country selection
selected_countries = st.sidebar.multiselect(
    "Select Countries:",
    options=countries_df['Country'].tolist(),
    default=countries_df['Country'].tolist()[:5]
)

# Sales range filter
sales_range = st.sidebar.slider(
    "Sales Range ($):",
    min_value=int(countries_df['Sales'].min()),
    max_value=int(countries_df['Sales'].max()),
    value=(int(countries_df['Sales'].min()), int(countries_df['Sales'].max())),
    format="$%d"
)

# Chart type selection
chart_type = st.sidebar.selectbox(
    "Primary Chart Type:",
    ["Bar Chart", "Treemap", "Sunburst"]
)

# Filter data based on selections
filtered_countries = countries_df[
    (countries_df['Country'].isin(selected_countries)) &
    (countries_df['Sales'] >= sales_range[0]) &
    (countries_df['Sales'] <= sales_range[1])
]

# Key Metrics Row
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="💰 Total Sales",
        value=f"${filtered_countries['Sales'].sum():,.0f}",
        delta=f"{len(filtered_countries)} countries"
    )

with col2:
    st.metric(
        label="🍾 Total Unique Wines",
        value=f"{filtered_countries['Unique_Wines'].sum():,}",
        delta=f"Top: {filtered_countries.loc[filtered_countries['Unique_Wines'].idxmax(), 'Country']}"
    )

with col3:
    st.metric(
        label="📊 Average Price",
        value=f"${filtered_countries['Avg_Price'].mean():.2f}",
        delta=f"Range: ${filtered_countries['Avg_Price'].min():.0f}-${filtered_countries['Avg_Price'].max():.0f}"
    )

with col4:
    st.metric(
        label="🏆 Market Leader",
        value=filtered_countries.loc[filtered_countries['Sales'].idxmax(), 'Country'],
        delta=f"${filtered_countries['Sales'].max():,.0f}"
    )

st.divider()

# Main Charts Row
col1, col2 = st.columns(2)

with col1:
    st.subheader("📈 Sales Performance by Country")
    
    if chart_type == "Bar Chart":
        fig1 = px.bar(
            filtered_countries.sort_values('Sales', ascending=True),
            x='Sales',
            y='Country',
            orientation='h',
            color='Sales',
            color_continuous_scale='viridis',
            title="Sales by Country"
        )
        fig1.update_layout(height=400, showlegend=False)
        
    elif chart_type == "Treemap":
        fig1 = px.treemap(
            filtered_countries,
            values='Sales',
            names='Country',
            color='Avg_Price',
            color_continuous_scale='RdYlBu',
            title="Sales Treemap (Color = Avg Price)"
        )
        fig1.update_layout(height=400)
        
    else:  # Sunburst
        # Create hierarchical data for sunburst
        sunburst_data = filtered_countries.copy()
        sunburst_data['Region'] = sunburst_data['Country'].apply(
            lambda x: 'Europe' if x in ['Italy', 'France', 'Spain', 'Portugal', 'Germany'] 
            else 'Americas' if x in ['US', 'Argentina', 'Chile'] 
            else 'Oceania'
        )
        
        fig1 = px.sunburst(
            sunburst_data,
            path=['Region', 'Country'],
            values='Sales',
            color='Avg_Price',
            color_continuous_scale='viridis',
            title="Sales by Region & Country"
        )
        fig1.update_layout(height=400)
    
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.subheader("🎯 Wine Diversity Analysis")
    
    fig2 = px.scatter(
        filtered_countries,
        x='Unique_Wines',
        y='Sales',
        size='Avg_Price',
        color='Country',
        hover_data=['Avg_Price'],
        title="Sales vs Wine Diversity",
        labels={'Unique_Wines': 'Number of Unique Wines', 'Sales': 'Sales ($)'}
    )
    fig2.update_layout(height=400)
    st.plotly_chart(fig2, use_container_width=True)

# Second Row of Charts
col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 Top Suppliers Performance")
    
    fig3 = px.bar(
        suppliers_df.sort_values('Sales', ascending=False).head(8),
        x='Sales',
        y='Supplier',
        orientation='h',
        color='Wine_Count',
        color_continuous_scale='plasma',
        title="Top Suppliers by Sales"
    )
    fig3.update_layout(
        height=400,
        yaxis=dict(tickfont=dict(size=10))
    )
    st.plotly_chart(fig3, use_container_width=True)

with col2:
    st.subheader("📅 Sales Trend Over Time")
    
    fig4 = go.Figure()
    fig4.add_trace(go.Scatter(
        x=time_series_df['Date'],
        y=time_series_df['Monthly_Sales'],
        mode='lines+markers',
        name='Monthly Sales',
        line=dict(color='#1f77b4', width=3),
        fill='tonexty'
    ))
    
    fig4.update_layout(
        title="Monthly Sales Trend",
        xaxis_title="Date",
        yaxis_title="Sales ($)",
        height=400,
        hovermode='x unified'
    )
    st.plotly_chart(fig4, use_container_width=True)

# Advanced Analytics Section
st.divider()
st.subheader("🔬 Advanced Analytics")

tab1, tab2, tab3 = st.tabs(["📊 Correlation Analysis", "🎯 Market Insights", "📋 Data Table"])

with tab1:
    col1, col2 = st.columns(2)
    
    with col1:
        # Correlation heatmap
        corr_data = filtered_countries[['Sales', 'Unique_Wines', 'Avg_Price']].corr()
        fig_corr = px.imshow(
            corr_data,
            text_auto=True,
            aspect="auto",
            color_continuous_scale='RdBu',
            title="Correlation Matrix"
        )
        st.plotly_chart(fig_corr, use_container_width=True)
    
    with col2:
        # Price distribution
        fig_dist = px.histogram(
            filtered_countries,
            x='Avg_Price',
            nbins=10,
            title="Average Price Distribution",
            color_discrete_sequence=['#ff7f0e']
        )
        fig_dist.update_layout(showlegend=False)
        st.plotly_chart(fig_dist, use_container_width=True)

with tab2:
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🎯 Key Insights")
        st.markdown(f"""
        - **Highest Sales**: {countries_df.loc[countries_df['Sales'].idxmax(), 'Country']} (${countries_df['Sales'].max():,.0f})
        - **Most Diverse**: {countries_df.loc[countries_df['Unique_Wines'].idxmax(), 'Country']} ({countries_df['Unique_Wines'].max():,} wines)
        - **Premium Market**: {countries_df.loc[countries_df['Avg_Price'].idxmax(), 'Country']} (${countries_df['Avg_Price'].max():.2f} avg)
        - **Sales Concentration**: Top 3 countries represent {(countries_df.nlargest(3, 'Sales')['Sales'].sum() / countries_df['Sales'].sum() * 100):.1f}% of total sales
        """)
    
    with col2:
        st.markdown("#### 📈 Recommendations")
        st.markdown("""
        - Focus marketing efforts on high-value, low-volume markets
        - Expand wine selection in underperforming regions
        - Investigate pricing strategies in premium markets
        - Consider supplier diversification for risk management
        """)

with tab3:
    st.markdown("#### 📋 Detailed Country Data")
    
    # Enhanced data table with formatting
    display_df = filtered_countries.copy()
    display_df['Sales'] = display_df['Sales'].apply(lambda x: f"${x:,.2f}")
    display_df['Avg_Price'] = display_df['Avg_Price'].apply(lambda x: f"${x:.2f}")
    display_df['Unique_Wines'] = display_df['Unique_Wines'].apply(lambda x: f"{x:,}")
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )
    
    # Download button
    csv = filtered_countries.to_csv(index=False)
    st.download_button(
        label="📥 Download Data as CSV",
        data=csv,
        file_name="wine_sales_data.csv",
        mime="text/csv"
    )

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #666; font-size: 0.9em;'>
    🍷 Wine Sales Dashboard | Built with Streamlit & Plotly | Last Updated: 2024
</div>
""", unsafe_allow_html=True)