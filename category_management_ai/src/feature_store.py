import pandas as pd
import numpy as np

class FeatureStore:
    def __init__(self, data_ingestion):
        self.data_ingestion = data_ingestion
        
        # Internal raw dataframes
        self.df_sales = pd.DataFrame()
        self.df_onhand = pd.DataFrame()
        self.df_stores = pd.DataFrame()
        self.df_items = pd.DataFrame()

    def load_all_data(self):
        """Loads data from the ingestion module."""
        print("Loading Sales Data...")
        self.df_sales = self.data_ingestion.load_consumption_data()
        
        print("Loading Onhand Inventory Data...")
        self.df_onhand = self.data_ingestion.load_onhand_data()
        
        print("Loading Store Master Data...")
        self.df_stores = self.data_ingestion.load_stores_data()
        
        print("Loading Item Master Data...")
        self.df_items = self.data_ingestion.load_item_master_data()
        
        # Note: 'sku' standardization is now fully handled in data_ingestion.py
        # no need to duplicate renaming here.

    def build_store_sku_features(self, consumption_days: float = 30.0) -> pd.DataFrame:
        """
        Merge sales, inventory, stores, and item hierarchy to calculate
        velocity, profitability, and risk metrics.
        """
        if self.df_sales.empty:
            print("Sales data is empty, cannot build core features.")
            return pd.DataFrame()
            
        # Group by Store ID and SKU
        sales_agg = self.df_sales.groupby(['store_id', 'sku']).agg(
            total_qty_sold=('Primary Quantity', 'sum'),
            total_cost_value=('Transaction Cost Value', 'sum')
        ).reset_index()
        
        # Tag these items as originating from the consumption file
        sales_agg['in_consumption'] = True
        
        # We explicitly lock to 'Onhand' column since we verified the raw data
        stock_col = 'Onhand'
        
        if stock_col in self.df_onhand.columns and not self.df_onhand.empty:
            onhand_agg = self.df_onhand.groupby(['store_id', 'sku'])[stock_col].sum().reset_index()
            onhand_agg = onhand_agg.rename(columns={stock_col: 'stock_on_hand'})
            
            # Also extract the true 'Item Cost' and 'SKU Category' columns from the onhand file to carry through
            cols_to_extract = ['store_id', 'sku']
            if 'Item Cost' in self.df_onhand.columns:
                cols_to_extract.append('Item Cost')
            if 'SKU Category' in self.df_onhand.columns:
                cols_to_extract.append('SKU Category')
                
            if len(cols_to_extract) > 2:
                cost_df = self.df_onhand[cols_to_extract].drop_duplicates(['store_id', 'sku'])
                onhand_agg = pd.merge(onhand_agg, cost_df, on=['store_id', 'sku'], how='left')

            # Merge sales and onhand
            features = pd.merge(sales_agg, onhand_agg, on=['store_id', 'sku'], how='outer')
        else:
            features = sales_agg.copy()
            features['stock_on_hand'] = 0

        # Fill False for anything brought in strictly via Onhand
        features['in_consumption'] = features['in_consumption'].fillna(False)

        # Merge with item master (Final IMF) to get hierarchy
        if not self.df_items.empty:
            features = pd.merge(features, self.df_items, on='sku', how='left')
            
        # Merge with store master
        if not self.df_stores.empty:
            features = pd.merge(features, self.df_stores, on='store_id', how='left')

        # Compute preliminary features (Sales Velocity / Stock Cover Days)
        # Handle zero divisions securely
        features['stock_on_hand'] = features['stock_on_hand'].fillna(0)
        features['total_qty_sold'] = features['total_qty_sold'].fillna(0)
        
        # Calculate average daily sales based on the customizable timeframe (e.g., 7, 15, or 30 days)
        features['avg_daily_sales'] = features['total_qty_sold'] / float(consumption_days)
        
        # Determine stock cover days accurately:
        # If sales > 0, calculate normally.
        # If sales == 0 and stock == 0, cover logic is 0.
        # If sales == 0 and stock > 0, cover is theoretically infinite (we assign 999).
        conditions = [
            features['avg_daily_sales'] > 0,
            (features['avg_daily_sales'] == 0) & (features['stock_on_hand'] > 0)
        ]
        choices = [
            features['stock_on_hand'] / features['avg_daily_sales'],
            999
        ]
        features['stock_cover_days'] = np.select(conditions, choices, default=0)

        return features
