import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Category Management AI", layout="wide")

st.title("🤖 AI-Powered Category Management System")
st.markdown("Decision Intelligence Dashboard for Pharmacy Network")

# Load data
# Removed @st.cache_data so the dashboard always reads the freshest output from main.py
def load_data():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    file_path = os.path.join(base_dir, 'data', 'outputs', 'nba_master.csv')
    if os.path.exists(file_path):
        return pd.read_csv(file_path)
    return pd.DataFrame()

df = load_data()

if df.empty:
    st.warning("No Next Best Action (NBA) data found. Please run the `main.py` pipeline first.")
else:
    # Top Level KPIs
    st.subheader("Enterprise KPIs")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Stores Analyzed", df['Pharmacy Code'].nunique() if 'Pharmacy Code' in df.columns else df.get('store_id', pd.Series()).nunique())
    col2.metric("Total SKUs Managed", df['Item Code'].nunique() if 'Item Code' in df.columns else df.get('sku', pd.Series()).nunique())
    col3.metric("Total Items to Reorder", len(df[df['next_best_action'] == 'REORDER']))

    st.markdown("---")

    # Filters
    st.subheader("Filter Opportunities")
    
    # Check for Division column (often 'NEW DIVISION' or 'Division')
    div_col = next((c for c in df.columns if 'division' in c.lower()), None)
    
    colA, colB, colC, colD = st.columns(4)
    
    status_options = ["All"] + list(df['Status'].dropna().unique()) if 'Status' in df.columns else ["All"]
    selected_status = colA.selectbox("Store Status", status_options)
    
    store_col = 'Pharmacy Code' if 'Pharmacy Code' in df.columns else 'store_id'
    selected_store = colB.selectbox("Select Store", ["All"] + list(df[store_col].unique()))
    
    selected_action = colC.selectbox("Next Best Action", ["All"] + list(df['next_best_action'].unique()))
    
    div_options = ["All"] + list(df[div_col].dropna().unique()) if div_col else ["All"]
    selected_division = colD.selectbox("Division", div_options)
    
    st.markdown("##### Additional Filters")
    colG, colH = st.columns(2)
    sku_cat_options = ["All"] + list(df['SKU Category'].dropna().unique()) if 'SKU Category' in df.columns else ["All"]
    selected_sku_category = colG.selectbox("SKU Category (Active/Inactive)", sku_cat_options)
    
    st.markdown("##### Machine Learning Segments")
    colE, colF = st.columns(2)
    store_cluster_options = ["All"] + list(df['store_cluster'].dropna().unique()) if 'store_cluster' in df.columns else ["All"]
    selected_store_cluster = colE.selectbox("Store Cluster (AI Grouping)", store_cluster_options)
    
    sku_cluster_options = ["All"] + list(df['sku_cluster'].dropna().unique()) if 'sku_cluster' in df.columns else ["All"]
    selected_sku_cluster = colF.selectbox("SKU Cluster (AI Grouping)", sku_cluster_options)

    # Apply Filters
    filtered_df = df.copy()
    if 'Status' in filtered_df.columns and selected_status != "All":
        filtered_df = filtered_df[filtered_df['Status'] == selected_status]
    if selected_store != "All":
        filtered_df = filtered_df[filtered_df[store_col] == selected_store]
    if selected_action != "All":
        filtered_df = filtered_df[filtered_df['next_best_action'] == selected_action]
    if div_col and selected_division != "All":
        filtered_df = filtered_df[filtered_df[div_col] == selected_division]
    if 'SKU Category' in filtered_df.columns and selected_sku_category != "All":
        filtered_df = filtered_df[filtered_df['SKU Category'] == selected_sku_category]
    if 'store_cluster' in filtered_df.columns and selected_store_cluster != "All":
        filtered_df = filtered_df[filtered_df['store_cluster'] == selected_store_cluster]
    if 'sku_cluster' in filtered_df.columns and selected_sku_cluster != "All":
        filtered_df = filtered_df[filtered_df['sku_cluster'] == selected_sku_cluster]

    # Data Display
    # Find any column that looks like item description to show in dashboard
    desc_col = next((c for c in df.columns if 'description' in c.lower()), None)
    
    item_col = 'Item Code' if 'Item Code' in df.columns else 'sku'
    display_cols = [store_col, 'store_cluster', item_col]
    if desc_col:
        display_cols.append(desc_col)
    
    onhand_col = 'Onhand' if 'Onhand' in df.columns else 'stock_on_hand'
    display_cols.extend(['SKU Category', 'sku_cluster', 'total_qty_sold', onhand_col, 'predicted_demand', 'next_best_action', 'nba_reason'])
    
    # Filter columns to only those explicitly remaining in the dataframe
    display_cols = [c for c in display_cols if c in filtered_df.columns]
    
    st.dataframe(filtered_df[display_cols], use_container_width=True)

    st.markdown("---")
    st.subheader("Availability Report by Store")
    st.markdown("Measures the percentage of assigned items (from Consumption data) that are fully covered by at least 7 days of stock.")

    if 'stock_cover_days' in filtered_df.columns and 'in_consumption' in filtered_df.columns:
        # Determine strict availability boolean matching 7+ days cover requirement
        filtered_df['is_available'] = filtered_df['stock_cover_days'] >= 7

        def calc_availability(group):
            consumption_group = group[group['in_consumption'] == True]
            total_items = len(consumption_group)
            if total_items == 0:
                return 0.0
            available_items = consumption_group['is_available'].sum()
            return (available_items / total_items) * 100

        availability_df = filtered_df.groupby(store_col).apply(calc_availability).reset_index(name='Availability %')
        
        col_chart, col_data = st.columns([2, 1])
        with col_chart:
            st.bar_chart(data=availability_df.set_index(store_col))
        with col_data:
            st.dataframe(availability_df.style.format({'Availability %': '{:.2f}%'}), use_container_width=True)
    else:
        st.info("Insufficient data columns (stock_cover_days, in_consumption) to calculate availability report.")
