from fastapi import FastAPI, File, UploadFile, Form, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import shutil
import os
import sys
import subprocess
from typing import List
import pandas as pd
import math

app = FastAPI()

# Mount the static directory to serve the frontend
static_dir = os.path.join(os.path.dirname(__file__), 'static')
app.mount("/static", StaticFiles(directory=static_dir), name="static")

RAW_DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'raw'))
MAIN_PY_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'main.py'))

@app.get("/")
def read_root():
    with open(os.path.join(static_dir, "index.html"), "r") as f:
        return HTMLResponse(content=f.read())

def run_pipeline(days: int):
    print(f"Running pipeline with {days} days...")
    # Safe execute using sys.executable so Linux/Render environments don't fail searching for 'python'
    try:
        subprocess.run([sys.executable, MAIN_PY_PATH, "--days", str(days)], check=True)
        print("Pipeline finished successfully.")
    except Exception as e:
        print(f"Pipeline crashed: {e}")

@app.post("/upload")
async def upload_files(
    background_tasks: BackgroundTasks,
    consumption_days: int = Form(...),
    files: List[UploadFile] = File(...)
):
    os.makedirs(RAW_DATA_DIR, exist_ok=True)
    saved_files = []
    
    for file in files:
        file_path = os.path.join(RAW_DATA_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        saved_files.append(file.filename)
        
    # Trigger the AI pipeline in the background so the UI doesn't freeze
    background_tasks.add_task(run_pipeline, consumption_days)
    
    return JSONResponse(content={
        "message": "Files uploaded successfully. The AI processing pipeline has started in the background.",
        "files": saved_files,
        "days": consumption_days
    })

@app.get("/api/dashboard")
def get_dashboard_data():
    out_path = os.path.join(RAW_DATA_DIR, '..', 'outputs', 'nba_master.csv')
    if not os.path.exists(out_path):
        return {"error": "No data available. Run pipeline first."}
        
    try:
        df = pd.read_csv(out_path)
        
        # Calculate high level KPIs
        stores = int(df['Pharmacy Code'].nunique() if 'Pharmacy Code' in df.columns else df.get('store_id', pd.Series()).nunique())
        skus = int(df['Item Code'].nunique() if 'Item Code' in df.columns else df.get('sku', pd.Series()).nunique())
        reorders = int(len(df[df['next_best_action'] == 'REORDER']))
        
        # Display top 500 records securely to not crash React
        display_cols = ['Pharmacy Code', 'Item Code', 'total_qty_sold', 'Onhand', 'stock_cover_days', 'store_cluster', 'sku_cluster', 'predicted_demand', 'next_best_action', 'nba_reason']
        # Fallbacks mapping
        fallback_map = {'Onhand': 'stock_on_hand', 'Pharmacy Code': 'store_id', 'Item Code': 'sku'}
        final_cols = []
        for c in display_cols:
            if c in df.columns:
                final_cols.append(c)
            elif fallback_map.get(c) in df.columns:
                final_cols.append(fallback_map[c])
                
        table_df = df[final_cols].head(500).fillna("")
        
        # Handle nan values that JSON can't parser
        rows = table_df.to_dict(orient="records")
        
        return {
            "kpis": {
                "total_stores": stores,
                "total_skus": skus,
                "reorder_count": reorders
            },
            "columns": final_cols,
            "rows": rows
        }
    except Exception as e:
        return {"error": str(e)}
