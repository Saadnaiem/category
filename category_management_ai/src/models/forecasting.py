import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split

class DemandForecaster:
    def __init__(self):
        self.model = xgb.XGBRegressor(
            objective='reg:squarederror',
            n_estimators=100,
            learning_rate=0.1,
            max_depth=5,
            random_state=42
        )
        self.is_trained = False
        self.features = []

    def prepare_data(self, df: pd.DataFrame, target_col: str):
        """Prepare features and target for XGBoost."""
        # This is a simplified feature selection. 
        # In a real scenario, you'd use lag features and temporal features.
        drop_cols = ['store_id', 'sku', target_col, 'Item Description', 'Primary UOM', 'next_best_action', 'nba_reason']
        self.features = [col for col in df.columns if col not in drop_cols and df[col].dtype in ['int64', 'float64']]
        
        X = df[self.features].fillna(0)
        y = df[target_col].fillna(0)
        return X, y

    def train(self, df: pd.DataFrame, target_col: str = 'total_qty_sold'):
        """Trains the XGBoost model on historical demand."""
        if df.empty or target_col not in df.columns:
            print("Insufficient data to train forecaster.")
            return

        X, y = self.prepare_data(df, target_col)
        
        # Simple train-test split logic
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        print("Training XGBoost Forecaster...")
        self.model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)
        self.is_trained = True
        print("Model training complete.")

    def predict(self, df: pd.DataFrame) -> pd.Series:
        """Predict expected demand."""
        if not self.is_trained or df.empty:
            return pd.Series(0, index=df.index)
            
        X = df[self.features].fillna(0)
        predictions = self.model.predict(X)
        # Demand can't be negative
        predictions = [max(0, p) for p in predictions]
        
        return pd.Series(predictions, index=df.index)