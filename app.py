# Enhanced Amazon SCM Dashboard
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# Configure page
st.set_page_config(page_title="Amazon SCM Dashboard", layout="wide")
st.title("📊 Amazon India Sales Analytics")

# Load data with caching
from sqlalchemy import create_engine
import pymysql

@st.cache_data
def load_data():
    # MySQL connection setup
    connection_string = "mysql+pymysql://root:wordpass@localhost/scm"
    engine = create_engine(connection_string)

    # Query the sales table
    df = pd.read_sql("SELECT * FROM sales", engine)

    # Column renaming (same as before)
    mapper = {
        'Order_ID':'order_ID', 'Status':'ship_status', 'Fulfilment':'fullfilment',
        'ship_service':'service_level', 'Style':'style', 'SKU':'sku', 'Category':'product_category', 
        'Size':'size', 'ASIN':'asin', 'Courier_Status':'courier_ship_status', 'Qty':'order_quantity', 
        'Amount':'order_amount_($)', 'ship_city':'city', 'ship_state':'state', 'ship_postal_code':'zip', 
        'promotion_ids':'promotion', 'B2B':'customer_type'
    }
    df.rename(columns=mapper, inplace=True)

    # Convert currency
    exchange_rate = 0.0120988
    df['order_amount_($)'] = df['order_amount_($)'] * exchange_rate

    # Customer type mapping
    df['customer_type'].replace(to_replace=[1,0], value=['business','customer'], inplace=True)

    # Generate dummy date column if missing
    if 'date' not in df.columns:
        import random
        from datetime import timedelta
        start_date = datetime(2022, 4, 1)
        df['date'] = [start_date + timedelta(days=random.randint(0, 89)) for _ in range(len(df))]

    df['date'] = pd.to_datetime(df['date'])
    df = df[df['date'].dt.month != 3]
    df['month'] = df['date'].dt.month.map({4: 'april', 5: 'may', 6: 'june'})

    # Order size categories
    size_order = ['Free','XS', 'S', 'M', 'L', 'XL', 'XXL', '3XL', '4XL', '5XL', '6XL']
    df['size'] = pd.Categorical(df['size'], categories=size_order, ordered=True)

    return df


df = load_data()

# Sidebar filters
st.sidebar.header("🔍 Filters")
selected_categories = st.sidebar.multiselect(
    "Product Categories",
    options=df["product_category"].unique(),
    default=["Set", "Western Dress", "kurta"]
)

selected_months = st.sidebar.multiselect(
    "Months",
    options=["april", "may", "june"],
    default=["april", "may", "june"]
)

# Apply filters
filtered_df = df[
    (df["product_category"].isin(selected_categories)) & 
    (df["month"].isin(selected_months))
]

# Main Dashboard
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Revenue Analysis", "Product Performance", "Regional Trends", "Inventory Planner", "AI insights"])

with tab1:
    st.header("💰 Revenue Performance")
    
    # KPI Cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        total_sales = filtered_df["order_amount_($)"].sum()
        st.metric("Total Sales", f"${total_sales:,.2f}")
    with col2:
        avg_order = filtered_df["order_amount_($)"].mean()
        st.metric("Avg Order Value", f"${avg_order:,.2f}")
    with col3:
        cancelled = len(filtered_df[filtered_df['ship_status'].isin(['Cancelled', 'Shipped - Lost in Transit'])])
        st.metric("Cancelled Orders", f"{cancelled:,}")
    with col4:
        returned = len(filtered_df[filtered_df['ship_status'].isin(['Shipped - Returned to Seller', 'Shipped - Returning to Seller'])])
        st.metric("Returned Orders", f"{returned:,}")
    
    # Monthly Revenue Trend
    st.subheader("Monthly Revenue Trend")
    monthly_sales = filtered_df.groupby('month')['order_amount_($)'].sum().reset_index()
    fig = px.bar(
        monthly_sales, 
        x='month', 
        y='order_amount_($)',
        text_auto='.2s',
        labels={'order_amount_($)': 'Revenue ($)', 'month': 'Month'},
        color='month',
        color_discrete_sequence=['#969696', '#bdbdbd', 'orange']
    )
    st.plotly_chart(fig, use_container_width=True)

    # Daily Sales Trend
    st.subheader("Daily Sales Trend (Time Series)")

    daily_sales = filtered_df.groupby('date')['order_amount_($)'].sum().reset_index()

    fig = px.line(
        daily_sales,
        x='date',
        y='order_amount_($)',
        labels={'order_amount_($)': 'Revenue ($)', 'date': 'Date'},
        title='Daily Revenue Over Time',
        markers=True,
        line_shape='spline'
    )

    fig.update_traces(line=dict(color='orange', width=2))
    st.plotly_chart(fig, use_container_width=True)

    
    
    # Revenue by Category
    st.subheader("Revenue by Product Category")
    category_sales = filtered_df.groupby('product_category')['order_amount_($)'].sum().reset_index()
    fig = px.pie(
        category_sales,
        names='product_category',
        values='order_amount_($)',
        hole=0.3,
        color_discrete_sequence=px.colors.sequential.RdBu
    )
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.header("📦 Product Performance")
    
    # Top Products by Revenue
    st.subheader("Top Products by Revenue")
    top_products = filtered_df.groupby('product_category')['order_amount_($)'].sum().nlargest(5).reset_index()
    fig = px.bar(
        top_products,
        x='product_category',
        y='order_amount_($)',
        text_auto='.2s',
        labels={'order_amount_($)': 'Revenue ($)', 'product_category': 'Product Category'},
        color='product_category',
        color_discrete_sequence=['orange' if x == 'Western Dress' else '#969696' for x in top_products['product_category']]
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Product Size Analysis
    st.subheader("Sales by Product Size")
    size_sales = filtered_df.groupby('size')['order_amount_($)'].sum().reset_index()
    fig = px.bar(
        size_sales,
        x='size',
        y='order_amount_($)',
        labels={'order_amount_($)': 'Revenue ($)', 'size': 'Size'},
        color='size',
        color_discrete_sequence=['orange' if x in ['S', 'M', 'L'] else '#969696' for x in size_sales['size']]
    )
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.header("🌍 Regional Trends")
    
    # Top States by Revenue
    st.subheader("Top States by Revenue")
    state_sales = filtered_df.groupby('state')['order_amount_($)'].sum().nlargest(10).reset_index()
    fig = px.bar(
        state_sales,
        x='state',
        y='order_amount_($)',
        text_auto='.2s',
        labels={'order_amount_($)': 'Revenue ($)', 'state': 'State'},
        color='state',
        color_discrete_sequence=px.colors.sequential.Plasma
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Popular Categories by State
    st.subheader("Popular Categories by State")
    state_category = filtered_df.groupby(['state', 'product_category'])['order_quantity'].sum().reset_index()
    state_category = state_category.sort_values(['state', 'order_quantity'], ascending=[True, False])
    top_state_category = state_category.groupby('state').head(1)
    fig = px.bar(
        top_state_category,
        x='state',
        y='order_quantity',
        color='product_category',
        labels={'order_quantity': 'Quantity Sold', 'state': 'State', 'product_category': 'Category'},
        text='product_category'
    )
    st.plotly_chart(fig, use_container_width=True)

# Insights Section
with tab5:
    st.header("💡 Key Insights")
    with st.subheader("View Insights from Analysis"):
        st.markdown("""
        **Revenue Trends:**
        - Q2 2022 saw an 18.77% decrease in revenue from April to June
        - Western Dress category showed strong growth potential (14.28% of total revenue)
        
        **Product Performance:**
        - "Set" category dominates with 49.88% of total revenue
        - Sizes S, M, and L account for majority of sales
        
        **Customer Behavior:**
        - Business customers spend more (avg $8.21 vs $7.37 for regular customers)
        - Cancellation rate of 14.22% is a concern
        
        **Recommendations:**
        1. Implement targeted promotions for Western Dress category
        2. Focus inventory on sizes S, M, and L
        3. Investigate reasons for high cancellation rate
        4. Develop business customer loyalty programs
        """)


#Inventory Planner

with tab4:
    st.header("🔄 Smart Inventory Recommender")
    
    # Choose forecast horizon
    st.subheader("Choose Parameters")
    buffer_pct = st.slider("Buffer Percentage for Safety Stock", min_value=0, max_value=100, value=20)
    
    st.markdown("Forecasting based on average monthly demand (April - June) per SKU.")

    # Compute forecast: average monthly sales per SKU
    sku_forecast = (
        filtered_df
        .groupby('sku')['order_quantity']
        .sum()
        .div(3)  # average over 3 months
        .reset_index()
        .rename(columns={'order_quantity': 'monthly_forecast'})
    )

    # Add buffer
    sku_forecast['recommended_restock'] = (sku_forecast['monthly_forecast'] * (1 + buffer_pct / 100)).round().astype(int)

    st.dataframe(sku_forecast.sort_values(by='recommended_restock', ascending=False), use_container_width=True)

    st.subheader("📥 Stock Adjustment Calculator")

    # Get list of SKUs from the forecast table
    sku_options = sku_forecast['sku'].unique()
    selected_sku = st.selectbox("Select SKU", options=sku_options)

    # Input for current stock
    current_stock = st.number_input("Enter Current Stock", min_value=0, step=1)

    # Get the recommended_restock for the selected SKU
    selected_row = sku_forecast[sku_forecast['sku'] == selected_sku]
    if not selected_row.empty:
        recommended = int(selected_row['recommended_restock'].values[0])
        restock_needed = max(0, recommended - current_stock)

        st.markdown(f"""
        ### 📦 Restock Summary for **{selected_sku}**
        - **Recommended Restock:** {recommended}
        - **Current Stock:** {current_stock}
        - 👉 **Stock Needed:** {restock_needed}
        """)


    # Optional Download
    csv = sku_forecast.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Download Restock Plan", csv, "restock_plan.csv", "text/csv")

# Raw Data Section
with st.expander("📁 View Raw Data"):
    st.dataframe(filtered_df)


