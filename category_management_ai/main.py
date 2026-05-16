import os
import pandas as pd
import argparse
from src.data_ingestion import DataIngestion
from src.feature_store import FeatureStore
from src.models.clustering import ClusteringEngine
from src.models.forecasting import DemandForecaster
from src.rules_engine import RulesEngine
from src.evaluation import KPICalculator

def main():
    parser = argparse.ArgumentParser(description="Run Category Management AI Pipeline")
    parser.add_argument('--days', type=int, default=30, help="Number of days the consumption data represents")
    args = parser.parse_args()

    print("Starting Category Management AI Pipeline...\n")
    
    # --- CONFIGURATION ---
    # Using parsed argument for consumption days
    CONSUMPTION_DAYS = args.days
    # ---------------------
    
    # Paths setup
    base_dir = os.path.dirname(os.path.abspath(__file__))
    raw_data_dir = os.path.join(base_dir, 'data', 'raw')
    outputs_dir = os.path.join(base_dir, 'data', 'outputs')
    
    # 1. Ingestion & Feature Store
    print(f"--- 1. Data Ingestion & Feature Store (Period: {CONSUMPTION_DAYS} days) ---")
    data_ingestion = DataIngestion(raw_data_dir)
    feature_store = FeatureStore(data_ingestion)
    
    feature_store.load_all_data()
    df_features = feature_store.build_store_sku_features(consumption_days=CONSUMPTION_DAYS)
    
    if df_features.empty:
        print("Error: Feature dataset is empty. Check raw data.")
        return

    # 2. Clustering
    print("\n--- 2. Clustering ---")
    clustering = ClusteringEngine()
    df_features = clustering.cluster_stores(df_features)
    df_features = clustering.cluster_skus(df_features)

    # 3. Forecasting
    print("\n--- 3. Forecasting Pipeline ---")
    forecaster = DemandForecaster()
    # Using 'total_qty_sold' as placeholder target
    forecaster.train(df_features, target_col='total_qty_sold')
    df_features['predicted_demand'] = forecaster.predict(df_features)

    # 4. Rules Engine
    print("\n--- 4. Business Rules Engine ---")
    rules_engine = RulesEngine()
    df_final = rules_engine.apply_next_best_action(df_features)

    # 5. KPIs & Evaluation
    print("\n--- 5. KPI Calculation ---")
    ent_metrics = KPICalculator.calculate_enterprise_metrics(df_final)
    print("Enterprise Metrics:", ent_metrics)

    # 6. Save Outputs
    output_path = os.path.join(outputs_dir, 'nba_master.csv')
    
    # Rename internal variables back to user-preferred business terms for the output files
    rename_map = {
        'store_id': 'Pharmacy Code',
        'sku': 'Item Code',
        'stock_on_hand': 'Onhand'
    }
    df_final = df_final.rename(columns=rename_map)
    df_final.to_csv(output_path, index=False)
    print(f"\nPipeline successfully completed! Output saved to: {output_path}")

if __name__ == "__main__":
    main()