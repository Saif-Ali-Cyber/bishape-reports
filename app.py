import streamlit as st
import pandas as pd
import sqlite3
import google.generativeai as genai
import re
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from sklearn.ensemble import IsolationForest

# 1. Advanced Page Config
st.set_page_config(page_title="Bishape Analytics Pro", layout="wide", page_icon="🔬")
st.title("🔬 Advanced Data Analytics Engine")

# 2. Secure API Setup
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"].strip())
    model = genai.GenerativeModel('gemini-flash-latest')
else:
    st.error("Bhai, Secrets mein API Key dalo!")
    st.stop()

# 3. HIGH-END DATA CLEANING
def deep_clean(df):
    # Duplicate Column Fix
    cols = pd.Series(df.columns)
    for dup in cols[cols.duplicated()].unique(): 
        cols[cols == dup] = [f"{dup}_{i}" if i != 0 else dup for i in range(sum(cols == dup))]
    df.columns = [re.sub(r'[^a-zA-Z0-9]', '_', str(c)) for c in cols]
    
    # Missing Values (Error Zeroed)
    df = df.fillna(0)
    
    # Date Handling
    for col in df.columns:
        if 'date' in col.lower() or 'dt' in col.lower():
            df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime('%Y-%m-%d')
    return df

@st.cache_data
def engine_load(file):
    df = pd.read_excel(file) if file.name.endswith('.xlsx') else pd.read_csv(file)
    df = deep_clean(df)
    conn = sqlite3.connect('analytics_pro.db', check_same_thread=False)
    df.to_sql('mytable', conn, if_exists='replace', index=False)
    return df

# --- INTERFACE ---
uploaded_file = st.file_uploader("Drag & Drop your Master Data here", type=['xlsx', 'csv'])

if uploaded_file:
    df = engine_load(uploaded_file)
    if df is not None:
        cols = df.columns.tolist()
        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()

        # TABS FOR ADVANCED ANALYTICS
        tab_smart, tab_ml, tab_query = st.tabs(["📉 Smart Dashboard", "🤖 ML Insights", "💬 AI Query"])

        with tab_smart:
            st.subheader("Key Business Drivers")
            if num_cols:
                # Correlation Heatmap
                corr = df[num_cols].corr()
                fig_corr = px.imshow(corr, text_auto=True, title="Data Correlation Matrix (Advanced)")
                st.plotly_chart(fig_corr, use_container_width=True)

        with tab_ml:
            st.subheader("Anomalies & Outliers (Self-Learning)")
            if len(num_cols) >= 1:
                # Isolation Forest for Outlier Detection
                clf = IsolationForest(contamination=0.05, random_state=42)
                preds = clf.fit_predict(df[num_cols[:1]])
                df['Is_Anomaly'] = ["Anomaly" if x == -1 else "Normal" for x in preds]
                
                fig_out = px.scatter(df, x=df.index, y=num_cols[0], color='Is_Anomaly', 
                                    title="Outlier Detection in Sales/Value",
                                    color_discrete_map={"Normal": "blue", "Anomaly": "red"})
                st.plotly_chart(fig_out, use_container_width=True)
                st.info("AI has automatically detected 5% of your data as outliers.")

        with tab_query:
            query = st.text_input("Deep Search (No keywords needed):")
            if query:
                with st.spinner('AI thinking...'):
                    prompt = f"SQLite Expert. Table 'mytable', Cols: {cols}. User: {query}. Return ONLY SQL."
                    try:
                        resp = model.generate_content(prompt)
                        sql_raw = resp.text.strip()
                        
                        # 🧼 THE ULTIMATE SANITIZER (No 'ite' or 'bhashan')
                        match = re.search(r'(SELECT|WITH)', sql_raw, re.IGNORECASE)
                        if match:
                            sql_final = sql_raw[match.start():].split(';')[0] + ';'
                            sql_final = re.sub(r'--.*', '', sql_final).replace('\n', ' ').strip()
                            
                            conn = sqlite3.connect('analytics_pro.db')
                            res_df = pd.read_sql_query(sql_final, conn)
                            st.dataframe(res_df, use_container_width=True)
                        else: st.warning("AI query generate nahi kar paya.")
                    except Exception as e:
                        st.error(f"Execution Error: {e}")
    else: st.error("File load nahi ho payi.")
else:
    st.info("Awaiting Data Upload...")
