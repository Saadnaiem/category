import pandas as pd
from sklearn.preprocessing import RobustScaler
from sklearn.cluster import KMeans

class ClusteringEngine:
    def __init__(self, random_state=42):
        self.random_state = random_state
        self.store_scaler = RobustScaler()
        self.sku_scaler = RobustScaler()
        
    def cluster_stores(self, df_stores_features: pd.DataFrame, n_clusters=4) -> pd.DataFrame:
        """Clusters stores based on their aggregated feature profiles."""
        if df_stores_features.empty: 
            return df_stores_features
            
        # Select numeric columns for clustering, ignoring ID columns
        cols_to_drop = ['store_id', 'sku']
        feature_cols = [c for c in df_stores_features.columns if c not in cols_to_drop]
        
        numeric_features = df_stores_features[feature_cols].select_dtypes(include=['float64', 'int64']).fillna(0)
        
        if numeric_features.empty:
            df_stores_features['store_cluster'] = -1
            return df_stores_features

        scaled_features = self.store_scaler.fit_transform(numeric_features)
        
        kmeans = KMeans(n_clusters=n_clusters, random_state=self.random_state, n_init='auto')
        df_stores_features['store_cluster'] = kmeans.fit_predict(scaled_features)
        
        return df_stores_features

    def cluster_skus(self, df_sku_features: pd.DataFrame, n_clusters=4) -> pd.DataFrame:
        """Clusters SKUs based on velocity, margin, and volatility."""
        if df_sku_features.empty: 
            return df_sku_features
            
        cols_to_drop = ['store_id', 'sku']
        feature_cols = [c for c in df_sku_features.columns if c not in cols_to_drop]
        
        numeric_features = df_sku_features[feature_cols].select_dtypes(include=['float64', 'int64']).fillna(0)
        
        if numeric_features.empty:
            df_sku_features['sku_cluster'] = -1
            return df_sku_features

        scaled_features = self.sku_scaler.fit_transform(numeric_features)
        
        kmeans = KMeans(n_clusters=n_clusters, random_state=self.random_state, n_init='auto')
        df_sku_features['sku_cluster'] = kmeans.fit_predict(scaled_features)
        
        return df_sku_features