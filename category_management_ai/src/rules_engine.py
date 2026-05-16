import pandas as pd
import numpy as np

class RulesEngine:
    def __init__(self):
        pass
        
    def apply_next_best_action(self, df_features: pd.DataFrame) -> pd.DataFrame:
        """
        Applies deterministic business rules to generate NBA (Next Best Action).
        Actions include: [REORDER, PROMOTE, DISCOUNT, DELIST, HOLD, TRANSFER]
        """
        if df_features.empty: 
            return df_features
        
        # Initialize default action
        df_features['next_best_action'] = 'HOLD'
        df_features['nba_reason'] = 'Parameters are within healthy thresholds.'

        # Rule 1: Auto-Reorder logic.
        # Simple heuristic: If stock is below 7 days of average daily sales
        if 'avg_daily_sales' in df_features.columns and 'stock_on_hand' in df_features.columns:
            reorder_mask = df_features['stock_on_hand'] < (df_features['avg_daily_sales'] * 7)
            
            df_features.loc[reorder_mask, 'next_best_action'] = 'REORDER'
            df_features.loc[reorder_mask, 'nba_reason'] = 'SOH below predicted lead time demand (7 days cover).'

        # Rule 2: Overstock / Discount logic
        # Simple heuristic: If stock cover is greater than 90 days
        if 'stock_cover_days' in df_features.columns:
            # Ignoring items where stock cover days is technically infinite due to zero sales ('999')
            # They might be re-classified as "Dead Stock"
            discount_mask = (df_features['stock_cover_days'] > 90) & (df_features['stock_cover_days'] < 900)
            
            df_features.loc[discount_mask, 'next_best_action'] = 'DISCOUNT'
            df_features.loc[discount_mask, 'nba_reason'] = 'Excess inventory (>90 days cover).'
            
            # Dead stock flag
            dead_stock_mask = (df_features['stock_cover_days'] >= 900) & (df_features['stock_on_hand'] > 0)
            df_features.loc[dead_stock_mask, 'next_best_action'] = 'DELIST'
            df_features.loc[dead_stock_mask, 'nba_reason'] = 'Dead stock: Zero or negligible movement with existing inventory.'

        # Note: Further clustering constraints (e.g., Traffic Builder, Hospital Adjacent rules)
        # can be layered here once the KMeans cluster IDs are assigned descriptive labels.

        return df_features