import pandas as pd

class KPICalculator:
    @staticmethod
    def calculate_enterprise_metrics(df_features: pd.DataFrame) -> dict:
        """Calculates global KPIs like Revenue and Inventory Values."""
        if df_features.empty:
            return {}
            
        metrics = {}
        if 'total_cost_value' in df_features.columns:
            metrics['Total Revenue (Cost Base)'] = df_features['total_cost_value'].sum()
            
        if 'stock_on_hand' in df_features.columns and 'Item Cost' in df_features.columns:
            # Assuming Item Cost is joined from Item Master
            metrics['Total Working Capital Tied Up'] = (df_features['stock_on_hand'] * df_features['Item Cost']).sum()
            
        return metrics

    @staticmethod
    def calculate_store_metrics(df_features: pd.DataFrame) -> pd.DataFrame:
        """Calculates store level aggregates."""
        if df_features.empty:
            return df_features
            
        store_kpis = df_features.groupby('store_id').agg(
            total_items_sold=('total_qty_sold', 'sum'),
            total_inventory_units=('stock_on_hand', 'sum')
        ).reset_index()
        
        store_kpis['store_sell_through'] = store_kpis['total_items_sold'] / (store_kpis['total_items_sold'] + store_kpis['total_inventory_units'] + 1e-9)
        
        return store_kpis