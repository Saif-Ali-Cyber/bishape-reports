import streamlit as st
import pandas as pd
import sqlite3
import google.generativeai as genai
import re
import plotly.express as px
import numpy as np
from sklearn.ensemble import IsolationForest

# 1. Dashboard UI
st.set_page_config(page_title="Bishape Analytics Pro", layout="wide", page_icon="🔬")
st.title("🔬 Professional Analytics Command Center")

# 2. Secure API Setup
try:
    if "GEMINI_API_KEY" in st.secrets:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"].strip())
        model = genai.GenerativeModel('gemini-flash-latest')
    else:
        st.error("Bhai, Secrets mein GEMINI_API_KEY dalo!")
        st.stop()
except Exception as e:
    st.error(f"Setup Error: {e}")
    st.stop()

# 3. Data Science Engine
def clean_engine(df):
    # Fix Duplicates
    cols = pd.Series(df.columns)
    for dup in cols[cols.duplicated()].unique(): 
        cols[cols == dup] = [f"{dup}_{i}" if i != 0 else dup for i in range(sum(cols == dup))]
    df.columns = [re.sub(r'[^a-zA-Z0-9]', '_', str(c)) for c in cols]
    
    # Error Zeroed: Missing values ko 0 karo
    df = df.fillna(0)
    
    # Date Standardization for Logistics Reports
    for col in df.columns:
        if 'date' in col.lower() or 'dt' in col.lower():
            df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime('%Y-%m-%d')
    return df

@st.cache_data
def run_db_sync(file):
    try:
        df = pd.read_excel(file) if file.name.endswith('.xlsx') else pd.read_csv(file)
        df = clean_engine(df)
        # Unique DB for every file to avoid "No such table"
        conn = sqlite3.connect('analytics_final.db', check_same_thread=False)
        df.to_sql('mytable', conn, if_exists='replace', index=False)
        return df
    except Exception as e:
        st.error(f"File Error: {e}")
        return None

# --- MAIN APP ---
uploaded_file = st.file_uploader("Drop Data Here", type=['xlsx', 'csv'])

if uploaded_file:
    df = run_db_sync(uploaded_file)
    if df is not None:
        cols = df.columns.tolist()
        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()

        tab1, tab2, tab3 = st.tabs(["📊 Insights", "🤖 Machine Learning", "💬 AI Chat"])

        with tab1:
            if num_cols:
                st.subheader("Correlation Matrix (Feature Links)")
                fig_corr = px.imshow(df[num_cols].corr(), text_auto=True, color_continuous_scale='RdBu_r')
                st.plotly_chart(fig_corr, use_container_width=True)

        with tab2:
            st.subheader("Automatic Outlier Detection")
            if num_cols:
                # ML logic to find bad data points
                clf = IsolationForest(contamination=0.05, random_state=42)
                preds = clf.fit_predict(df[num_cols[:1]])
                df['Status'] = ["Outlier" if x == -1 else "Normal" for x in preds]
                fig_ml = px.scatter(df, x=df.index, y=num_cols[0], color='Status', 
                                   title="Unusual Data Points (Red)", color_discrete_map={"Normal":"blue", "Outlier":"red"})
                st.plotly_chart(fig_ml, use_container_width=True)

        with tab3:
            query = st.text_input("Ask about packing slips or orders:")
            if query:
                prompt = f"SQL Expert. Table 'mytable', Cols: {cols}. User: {query}. ONLY SQL."
                try:
                    resp = model.generate_content(prompt)
                    sql_raw = resp.text.strip()
                    # Final Cleanup
                    match = re.search(r'(SELECT|WITH)', sql_raw, re.IGNORECASE)
                    if match:
                        sql_final = sql_raw[match.start():].split(';')[0] + ';'
                        conn = sqlite3.connect('analytics_final.db')
                        res = pd.read_sql_query(sql_final, conn)
                        st.dataframe(res, use_container_width=True)
                except Exception as e:
                    st.error(f"Query Fail: {e}")
else:
    st.info("Waiting for Master File...")
