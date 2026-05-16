import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Accumulative Data", layout="wide")

st.title("ðŸ“Š Accumulative Item Data")
st.markdown("View total consumption and on-hand inventory across the entire pharmacy network.")

def load_data():
    # Go up from pages -> app -> category_management_ai
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    file_path = os.path.join(base_dir, 'data', 'outputs', 'nba_master.csv')
    if os.path.exists(file_path):
        return pd.read_csv(file_path)
    return pd.DataFrame()

df = load_data()

if df.empty:
    st.warning("No data found. Please run the `main.py` pipeline first.")
else:
    st.subheader("Filters")
    col1, col2 = st.columns(2)
    
    # Setup Filters for Status, Division
    status_options = ["All"] + list(df['Status'].dropna().unique()) if 'Status' in df.columns else ["All"]
    selected_status = col1.selectbox("Store Status", status_options)
    
    div_col = next((c for c in df.columns if 'division' in c.lower()), None)
    div_options = ["All"] + list(df[div_col].dropna().unique()) if div_col else ["All"]
    selected_division = col2.selectbox("Division", div_options)
    
    st.markdown("##### Item Level Filters (Type to search and choose)")
    col_item1, col_item2, col_item3 = st.columns(3)
    
    item_col = 'Item Code' if 'Item Code' in df.columns else 'sku'
    item_options = list(df[item_col].dropna().unique())
    selected_items = col_item1.multiselect(f"{item_col} (Leave blank for all)", item_options)
    
    desc_col = next((c for c in df.columns if 'description' in c.lower()), None)
    selected_desc = []
    if desc_col:
        desc_options = list(df[desc_col].dropna().unique())
        selected_desc = col_item2.multiselect("Item Description (Leave blank for all)", desc_options)
        
    brand_col = next((c for c in df.columns if 'brand' in c.lower()), None)
    selected_brand_multi = []
    if brand_col:
        brand_options = list(df[brand_col].dropna().unique())
        selected_brand_multi = col_item3.multiselect("Brand (Leave blank for all)", brand_options)
    
    # Filter Data
    filtered_df = df.copy()
    if 'Status' in filtered_df.columns and selected_status != "All":
        filtered_df = filtered_df[filtered_df['Status'] == selected_status]
    if div_col and selected_division != "All":
        filtered_df = filtered_df[filtered_df[div_col] == selected_division]
        
    if len(selected_items) > 0:
        filtered_df = filtered_df[filtered_df[item_col].isin(selected_items)]
    if desc_col and len(selected_desc) > 0:
        filtered_df = filtered_df[filtered_df[desc_col].isin(selected_desc)]
    if brand_col and len(selected_brand_multi) > 0:
        filtered_df = filtered_df[filtered_df[brand_col].isin(selected_brand_multi)]
        
    # Get relevant column names securely
    onhand_col = 'Onhand' if 'Onhand' in df.columns else 'stock_on_hand'
    
    st.markdown("---")
    st.subheader("Unique Items Summary")
    
    # Ensure grouping columns exist
    groupby_cols = [item_col]
    if desc_col:
        groupby_cols.append(desc_col)
    if brand_col:
        groupby_cols.append(brand_col)
        
    # If the user filters down to 0 rows, handle gracefully
    if filtered_df.empty:
        st.info("No data matches the current filters.")
    else:
        # Calculate accumulative sums across all pharmacies
        agg_funcs = {
            'total_qty_sold': 'sum',
            onhand_col: 'sum'
        }
        
        accumulative_df = filtered_df.groupby(groupby_cols).agg(agg_funcs).reset_index()
        
        # Rename for clean presentation
        accumulative_df = accumulative_df.rename(columns={
            'total_qty_sold': 'Accumulative Consumption',
            onhand_col: 'Total Onhand'
        })
        
        # Display the aggregated table
        st.dataframe(accumulative_df, use_container_width=True)
        
        st.markdown("---")
        st.subheader("Pharmacy Breakdown")
        st.markdown("View exactly how the selected items are distributed across the pharmacies.")
        
        store_col = 'Pharmacy Code' if 'Pharmacy Code' in filtered_df.columns else 'store_id'
        store_name_col = 'Pharmacy Name' if 'Pharmacy Name' in filtered_df.columns else None
        
        pharmacy_groupby = [store_col]
        if store_name_col:
            pharmacy_groupby.append(store_name_col)
            
        pharmacy_df = filtered_df.groupby(pharmacy_groupby).agg(agg_funcs).reset_index()
        pharmacy_df = pharmacy_df.rename(columns={
            'total_qty_sold': 'Pharmacy Consumption',
            onhand_col: 'Pharmacy Onhand'
        })
        
        st.dataframe(pharmacy_df, use_container_width=True)
        
        # Display summary call-outs below the table
        st.markdown("<br>", unsafe_allow_html=True)
        colA, colB = st.columns(2)
        colA.metric(label="Total Selected Consumption", value=f"{accumulative_df['Accumulative Consumption'].sum():,.0f}")
        colB.metric(label="Total Selected Onhand", value=f"{accumulative_df['Total Onhand'].sum():,.0f}")
