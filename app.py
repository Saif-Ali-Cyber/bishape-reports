import streamlit as st
import pandas as pd
import sqlite3
import google.generativeai as genai
import re
import plotly.express as px

# --- ERROR-FREE IMPORTS ---
try:
    from sklearn.linear_model import LinearRegression
    import numpy as np
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

# 1. Advanced UI Config
st.set_page_config(page_title="Bishape AI Command Center", layout="wide", page_icon="🚀")

# 2. AI Configuration
API_KEY = "AIzaSyDyrJrSLXRyjG_Mp9n6W5DC_UidvGRMO50"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-flash-latest')

# 3. Sidebar
with st.sidebar:
    st.header("📦 Logistics Intelligence")
    uploaded_file = st.file_uploader("Upload Master Data", type=['xlsx', 'csv'])
    if not SKLEARN_AVAILABLE:
        st.warning("Prediction feature disabled. Please check requirements.txt")

@st.cache_data
def load_data(file):
    df = pd.read_excel(file) if file.name.endswith('.xlsx') else pd.read_csv(file)
    # Cleaning columns for SQL compatibility
    df.columns = [re.sub(r'[^a-zA-Z0-9]', '_', c) for c in df.columns]
    
    # Standardizing Date Formats for SQLite
    for col in df.columns:
        if 'date' in col.lower():
            df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime('%Y-%m-%d')
            
    conn = sqlite3.connect('bishape_final.db', check_same_thread=False)
    df.to_sql('mytable', conn, if_exists='replace', index=False)
    return df

if uploaded_file:
    df = load_data(uploaded_file)
    cols = df.columns.tolist()
    num_cols = df.select_dtypes(include=['number']).columns.tolist()

    st.title("📊 Data Analysis & Reporting Automation")

    # --- KPI DASHBOARD ---
    st.subheader("Business Overview")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Records", len(df))
    if num_cols:
        k2.metric("Total Value", f"₹{df[num_cols[0]].sum():,.0f}")
        k3.metric("Average Value", f"₹{df[num_cols[0]].mean():,.2f}")
    k4.metric("Data Quality", "High" if df.isnull().sum().sum() == 0 else "Review Needed")

    # --- MAIN ENGINE TABS ---
    tab1, tab2, tab3 = st.tabs(["💬 AI Analyst", "📈 Visual Insights", "🔮 Forecast Engine"])

    with tab1:
        query = st.text_input("Sawal pucho (e.g. 'Month-wise trends dikhao')")
        if query:
            with st.spinner('AI Report generate ho rahi hai...'):
                prompt = f"""
                You are a SQLite expert. 
                Table: 'mytable'
                Columns: {cols}
                
                Instruction: Return ONLY the SQL query. 
                - Use double quotes for all column names like "Date" or "Value".
                - Ensure SQLite compatibility.
                - No markdown, no prefixes like 'sql' or 'sqlite'.
                """
                try:
                    response = model.generate_content(prompt + f" User Question: {query}")
                    # 🛠️ SUPER CLEANER: Removes any prefix or extra characters
                    sql = response.text.strip().replace('```sql', '').replace('```', '')
                    sql = re.sub(r'^(sqlite|sql|ite|markdown)\s*', '', sql, flags=re.IGNORECASE)
                    
                    conn = sqlite3.connect('bishape_final.db')
                    result = pd.read_sql_query(sql, conn)
                    
                    st.dataframe(result, use_container_width=True)
                    st.download_button("Download as CSV", result.to_csv(index=False), "report.csv")
                except Exception as e:
                    st.error(f"SQL Error: AI ne galat query banayi. Koshish karein ki column ka naam sawal mein likhein.")
                    st.code(sql if 'sql' in locals() else "No SQL generated")

    with tab2:
        if num_cols:
            c1, c2 = st.columns(2)
            with c1:
                fig1 = px.histogram(df, x=num_cols[0], title=f"Distribution of {num_cols[0]}")
                st.plotly_chart(fig1, use_container_width=True)
            with c2:
                # Top 10 entries by first numeric column
                top_10 = df.nlargest(10, num_cols[0])
                fig2 = px.bar(top_10, x=df.columns[0], y=num_cols[0], title="Top 10 Performance")
                st.plotly_chart(fig2, use_container_width=True)

    with tab3:
        if SKLEARN_AVAILABLE and num_cols and len(df) > 5:
            st.subheader("Future Prediction")
            st.write("AI is analyzing trends to predict next week...")
            # Simple Prediction Logic
            y = df[num_cols[0]].values.reshape(-1, 1)
            x = np.arange(len(y)).reshape(-1, 1)
            reg = LinearRegression().fit(x, y)
            future_x = np.arange(len(y), len(y) + 7).reshape(-1, 1)
            prediction = reg.predict(future_x)
            st.line_chart(prediction)
        else:
            st.info("Bhai, prediction ke liye thoda aur data ya libraries chahiye.")

else:
    st.info("Awaiting data upload... Sidebar se file select karein.")
