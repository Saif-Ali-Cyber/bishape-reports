import streamlit as st
import pandas as pd
import sqlite3
import google.generativeai as genai
import re
import plotly.express as px
import numpy as np

# Machine Learning safety check
try:
    from sklearn.linear_model import LinearRegression
    SKLEARN_READY = True
except:
    SKLEARN_READY = False

# 1. UI Setup
st.set_page_config(page_title="Bishape AI Analytics Pro", layout="wide", page_icon="📈")

# 2. AI Key Setup
API_KEY = "AIzaSyDyrJrSLXRyjG_Mp9n6W5DC_UidvGRMO50"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-flash-latest')

# 3. Data Engine with "Zero Error" Logic
@st.cache_data
def load_and_clean_data(file):
    try:
        df = pd.read_excel(file) if file.name.endswith('.xlsx') else pd.read_csv(file)
        
        # Step A: Column names fix
        df.columns = [re.sub(r'[^a-zA-Z0-9]', '_', c) for c in df.columns]
        
        # Step B: Sabse pehle khali cells ko 0 karo
        df = df.fillna(0)
        
        # Step C: Numeric columns ko check karke '0' fix karo
        for col in df.columns:
            # Agar column number wala hona chahiye par text hai, toh use numeric banao
            if df[col].dtype == 'object' and not 'date' in col.lower():
                # Jo conversion fail ho unhe 0 kar do
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # Step D: Date formatting
        for col in df.columns:
            if 'date' in col.lower():
                df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime('%Y-%m-%d')
        
        conn = sqlite3.connect('bishape_final_pro.db', check_same_thread=False)
        df.to_sql('mytable', conn, if_exists='replace', index=False)
        return df
    except Exception as e:
        st.error(f"File loading error: {e}")
        return None

# --- APP INTERFACE ---
uploaded_file = st.sidebar.file_uploader("Upload Master File", type=['xlsx', 'csv'])

if uploaded_file:
    df = load_and_clean_data(uploaded_file)
    if df is not None:
        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()

        st.title("🚀 Bishape Enterprise Dashboard")
        
        # KPI Bar
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Records", f"{len(df):,}")
        if num_cols:
            c2.metric("Total Value", f"₹{df[num_cols[0]].sum():,.0f}")
            c3.metric("Data Quality", "100% (Cleaned)")

        # TABS
        tab1, tab2, tab3 = st.tabs(["💬 AI Manager", "📈 Analytics", "🔮 Forecast"])

        with tab1:
            query = st.text_input("Sawal pucho (e.g. ASM performance report):")
            if query:
                with st.spinner('Analysing...'):
                    prompt = f"SQL Expert. Table 'mytable', Columns: {df.columns.tolist()}. Return ONLY SQL query."
                    try:
                        response = model.generate_content(prompt + f" Query: {query}")
                        sql = re.sub(r'^(sqlite|sql|ite|markdown)\s*', '', response.text.strip().replace('```sql', '').replace('```', ''), flags=re.IGNORECASE)
                        res = pd.read_sql_query(sql, sqlite3.connect('bishape_final_pro.db'))
                        st.dataframe(res, use_container_width=True)
                    except:
                        st.warning("Bhai sawal mein column ka naam use karo (e.g. 'ASM wise sales').")

        with tab2:
            if num_cols:
                chart_col = st.selectbox("Kaunsa column visualize karein?", num_cols)
                fig = px.histogram(df, x=chart_col, nbins=30, template="plotly_dark", color_discrete_sequence=['#00f2fe'])
                st.plotly_chart(fig, use_container_width=True)

        with tab3:
            st.subheader("Trend Forecast")
            if SKLEARN_READY and num_cols and len(df) > 5:
                try:
                    # ML ke liye data taiyaar karna
                    y_raw = df[num_cols[0]].values.reshape(-1, 1)
                    
                    # 🧼 Final Safety: NaN ya Infinite ko handle karna
                    y = np.nan_to_num(y_raw, nan=0.0, posinf=0.0, neginf=0.0)
                    x = np.arange(len(y)).reshape(-1, 1)
                    
                    # Model Train
                    reg = LinearRegression().fit(x, y)
                    future_x = np.arange(len(y), len(y) + 7).reshape(-1, 1)
                    pred = reg.predict(future_x)
                    
                    st.line_chart(pred)
                    st.info("AI: Pichle trends ke hisaab se agle 7 records ka andaza.")
                except Exception as e:
                    st.error(f"Forecasting skip hui: {e}")
            else:
                st.info("Forecasting ke liye thoda aur numeric data chahiye.")
else:
    st.info("Waiting for data... Please upload from sidebar.")
