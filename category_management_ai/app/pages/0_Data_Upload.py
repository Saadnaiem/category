import streamlit as st
import os
import sys
import subprocess

st.set_page_config(page_title="Data Upload", layout="centered")

st.title("☁️ Data Upload & AI Processing")
st.markdown("Upload your raw data files here to securely run the AI engine.")

st.info("**Required Files:** Consumption.csv, Consumption_1.csv, Stores.xlsx, Final IMF.xlsx, Onhand.xlsx")

days = st.number_input("Consumption Days (Data Timeframe)", min_value=1, value=30, help="Days covered by your CSVs to determine velocity models.")

uploaded_files = st.file_uploader("Drop your files here", accept_multiple_files=True)

if st.button("Upload Data & Run AI Pipeline", type="primary", use_container_width=True):
    if not uploaded_files:
        st.error("Please select at least one file to upload.")
    else:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        raw_dir = os.path.join(base_dir, 'data', 'raw')
        os.makedirs(raw_dir, exist_ok=True)
        
        # Save files
        for uf in uploaded_files:
            with open(os.path.join(raw_dir, uf.name), "wb") as f:
                f.write(uf.getbuffer())
                
        st.success(f"Successfully saved {len(uploaded_files)} files!")
        
        # Run pipeline
        main_py = os.path.join(base_dir, 'main.py')
        
        with st.spinner("🧠 Computing Machine Learning Clusters and Demand Forecasts... Please wait."):
            try:
                result = subprocess.run(
                    [sys.executable, main_py, "--days", str(days)], 
                    capture_output=True, 
                    text=True
                )
                if result.returncode == 0:
                    st.success("✅ AI Pipeline Completed Successfully! You can now navigate to the 'Dashboard' page on the left.")
                else:
                    st.error(f"Pipeline failed! Error details:\n{result.stderr}")
            except Exception as e:
                st.error(f"Execution Error: {str(e)}")