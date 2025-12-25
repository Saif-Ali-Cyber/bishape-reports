import streamlit as st
import pandas as pd
import sqlite3
import google.generativeai as genai
import re
import plotly.express as px
import numpy as np

# sklearn import with safety
try:
    from sklearn.linear_model import LinearRegression
    SKLEARN_READY = True
except:
    SKLEARN_READY = False

# 1. Advanced UI
st.set_page_config(page_title="Bishape AI Analytics Pro", layout="wide", page_icon="📈")

# 2. AI Key Setup
API_KEY = "AIzaSyDyrJrSLXRyjG_Mp9n6W5DC_UidvGRMO50"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-flash-latest')

# 3. Data Engine
@st.cache_data
def load_and_clean(file):
    df = pd.read_excel(file) if file.name.endswith('.xlsx') else pd.read_csv(file)
    df.columns = [re.sub(r'[^a-zA-Z0-9]', '_', c) for c in df.columns]
    
    # 🧼 CLEANING: Khali cells ko 0 se bhar do taaki AI crash na ho
    df = df.fillna(0) 
    
    # Date standardization
    for col in df.columns:
        if 'date' in col.lower():
            df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime('%Y-%m-%d')
            
    conn = sqlite3.connect('bishape_pro.db', check_same_thread=False)
    df.to_sql('mytable', conn, if_exists='replace', index=False)
    return df

if uploaded_file := st.sidebar.file_uploader("Upload Master File", type=['xlsx', 'csv']):
    df = load_and_clean(uploaded_file)
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()

    # --- KPI HEADER ---
    st.title("🚀 Bishape Intelligence Dashboard")
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Orders/Rows", len(df))
    if num_cols:
        c2.metric("Total Business Value", f"₹{df[num_cols[0]].sum():,.0f}")
        c3.metric("Avg Order Size", f"₹{df[num_cols[0]].mean():,.2f}")

    # --- TABS ---
    tab1, tab2, tab3 = st.tabs(["💬 AI Manager", "📈 Visual Analytics", "🔮 Trend Forecast"])

    with tab1:
        st.subheader("Data se sawal pucho (e.g. ASM wise Packing Slips ki report do)")
        query = st.text_input("Sawal:")
        if query:
            with st.spinner('AI Report bana raha hai...'):
                prompt = f"SQLite Expert. Table 'mytable', Columns: {df.columns.tolist()}. Return ONLY SQL query using double quotes for columns."
                try:
                    response = model.generate_content(prompt + f" Query: {query}")
                    sql = re.sub(r'^(sqlite|sql|ite|markdown)\s*', '', response.text.strip().replace('```sql', '').replace('```', ''), flags=re.IGNORECASE)
                    
                    conn = sqlite3.connect('bishape_pro.db')
                    res = pd.read_sql_query(sql, conn)
                    st.dataframe(res, use_container_width=True)
                except Exception as e:
                    st.error("Bhai sawal thoda clear pucho, ya column ka sahi naam likho.")

    with tab2:
        st.subheader("Interactive Distribution")
        if num_cols:
            sel_col = st.selectbox("Kaunsa column analyze karein?", num_cols)
            fig = px.violin(df, y=sel_col, box=True, points="all", template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)

    with tab3:
        st.subheader("🔮 Predictive Forecasting")
        if SKLEARN_READY and num_cols and len(df) > 10:
            try:
                # 🧼 FINAL CLEANING for Prediction
                y = df[num_cols[0]].values.reshape(-1, 1)
                x = np.arange(len(y)).reshape(-1, 1)
                
                # Model Training
                reg = LinearRegression().fit(x, y)
                future_x = np.arange(len(y), len(y) + 10).reshape(-1, 1)
                pred = reg.predict(future_x)
                
                st.write(f"Analyzing trends for **{num_cols[0]}**...")
                st.line_chart(pred)
                st.success("Ye AI ka andaza hai agle 10 records ke liye.")
            except Exception as e:
                st.warning(f"Forecasting mein dikat hai: {e}")
        else:
            st.info("Bhai, forecasting ke liye kam se kam 10 numeric records chahiye.")

else:
    st.info("Waiting for your Master Excel... Sidebar se upload karo!")
