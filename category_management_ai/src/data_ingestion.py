import pandas as pd
import glob
import os

class DataIngestion:
    def __init__(self, raw_data_dir: str):
        self.raw_data_dir = raw_data_dir
        
    def load_consumption_data(self) -> pd.DataFrame:
        """Loads and combines all consumption CSV files."""
        all_files = glob.glob(os.path.join(self.raw_data_dir, "Consumption*.csv"))
        df_list = []
        for file in all_files:
            try:
                df = pd.read_csv(file)
                # Ensure pharmacy name column is standardized to 'store_id'
                if 'Organization' in df.columns:
                    df = df.rename(columns={'Organization': 'store_id'})
                # Standardize sku column
                if 'Item Code' in df.columns:
                    df = df.rename(columns={'Item Code': 'sku'})
                elif 'ERP code' in df.columns:
                    df = df.rename(columns={'ERP code': 'sku'})
                elif 'ERP Code' in df.columns:
                    df = df.rename(columns={'ERP Code': 'sku'})
                df_list.append(df)
            except Exception as e:
                print(f"Error reading {file}: {e}")
                
        if not df_list:
            return pd.DataFrame()
            
        combined_df = pd.concat(df_list, ignore_index=True)
        
        # Exclude stores that deliver stock rather than acting as true pharmacies (as requested)
        exclude_stores = ['SUL', 'QPS', 'JPS', 'KSM', 'DGS']
        if 'store_id' in combined_df.columns:
            # Create a boolean mask of rows to keep
            mask = ~combined_df['store_id'].isin(exclude_stores)
            combined_df = combined_df[mask]
            
        return combined_df
        
    def load_onhand_data(self) -> pd.DataFrame:
        """Loads stock on hand data."""
        # Check for Onhand.xlsx or Onhand.csv
        file_path_xlsx = os.path.join(self.raw_data_dir, "Onhand.xlsx")
        file_path_csv = os.path.join(self.raw_data_dir, "Onhand.csv")
        
        df = pd.DataFrame()
        if os.path.exists(file_path_xlsx):
            df = pd.read_excel(file_path_xlsx)
        elif os.path.exists(file_path_csv):
            df = pd.read_csv(file_path_csv)
            
        if not df.empty and 'Organization Code' in df.columns:
            df = df.rename(columns={'Organization Code': 'store_id'})
            
        # Standardize sku column
        if not df.empty:
            if 'Item Code' in df.columns:
                df = df.rename(columns={'Item Code': 'sku'})
            elif 'ERP code' in df.columns:
                df = df.rename(columns={'ERP code': 'sku'})
            elif 'ERP Code' in df.columns:
                df = df.rename(columns={'ERP Code': 'sku'})
            
        return df

    def load_stores_data(self) -> pd.DataFrame:
        """Loads stores master data."""
        # Find store data
        file_path_xlsx = os.path.join(self.raw_data_dir, "Stores.xlsx")
        file_path_csv = os.path.join(self.raw_data_dir, "Stores.csv")
        
        df = pd.DataFrame()
        if os.path.exists(file_path_xlsx):
            df = pd.read_excel(file_path_xlsx)
        elif os.path.exists(file_path_csv):
            df = pd.read_csv(file_path_csv)
            
        if not df.empty and 'Pharmacy Code' in df.columns:
            df = df.rename(columns={'Pharmacy Code': 'store_id'})
            
        return df

    def load_item_master_data(self) -> pd.DataFrame:
        """Loads the Item Master data (Final IMF) with product hierarchy."""
        file_path = os.path.join(self.raw_data_dir, "Final IMF.xlsx")
        
        try:
            df = pd.read_excel(file_path)
            # Standardize Item Code to sku
            if 'Item Code' in df.columns:
                df = df.rename(columns={'Item Code': 'sku'})
            elif 'ERP code' in df.columns:
                df = df.rename(columns={'ERP code': 'sku'})
            elif 'ERP Code' in df.columns:
                df = df.rename(columns={'ERP Code': 'sku'})
            elif 'ERP CODE' in df.columns:
                df = df.rename(columns={'ERP CODE': 'sku'})
            return df
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return pd.DataFrame()

if __name__ == "__main__":
    # Test ingestion
    pass
