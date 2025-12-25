import streamlit as st
import pandas as pd
import sqlite3
import google.generativeai as genai
import re
import plotly.express as px
import numpy as np

# 1. UI Setup
st.set_page_config(page_title="Bishape AI Pro Analytics", layout="wide", page_icon="📈")
st.title("🛡️ Bishape Enterprise Command Center")

# 2. AI Setup
API_KEY = "AIzaSyDyrJrSLXRyjG_Mp9n6W5DC_UidvGRMO50"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-flash-latest')

@st.cache_data
def load_and_clean(file):
    df = pd.read_excel(file) if file.name.endswith('.xlsx') else pd.read_csv(file)
    df.columns = [re.sub(r'[^a-zA-Z0-9]', '_', c) for c in df.columns]
    df = df.fillna(0)
    
    # Date Standardization
    for col in df.columns:
        if 'date' in col.lower():
            df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime('%Y-%m-%d')
            
    conn = sqlite3.connect('bishape_final.db', check_same_thread=False)
    df.to_sql('mytable', conn, if_exists='replace', index=False)
    return df

# --- SIDEBAR & UPLOAD ---
with st.sidebar:
    st.header("Settings")
    uploaded_file = st.file_uploader("Upload Data", type=['xlsx', 'csv'])
    st.divider()

if uploaded_file:
    df = load_and_clean(uploaded_file)
    cols = df.columns.tolist()

    # --- NEW: COLUMN MAPPING (Isse AI smart banega) ---
    with st.sidebar.expander("🛠️ Column Mapping (Zaroori Hai)", expanded=True):
        date_col = st.selectbox("Date Column Choose Karo", cols, index=0)
        customer_col = st.selectbox("Customer Name Column", cols, index=min(1, len(cols)-1))
        sales_col = st.selectbox("Sales Value Column", cols, index=min(2, len(cols)-1))
        state_col = st.selectbox("State/Region Column", cols, index=min(3, len(cols)-1))

    # --- DASHBOARD METRICS ---
    st.subheader("📌 Key Business Metrics")
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Records", f"{len(df):,}")
    
    # Correct Metric Calculation
    total_sales = pd.to_numeric(df[sales_col], errors='coerce').sum()
    m2.metric("Total Business Value", f"₹{total_sales:,.0f}")
    m3.metric("Mapped Columns", "Ready ✅")

    tab1, tab2 = st.tabs(["💬 AI Manager (Super Search)", "📊 Analytics"])

    with tab1:
        st.markdown(f"**AI Guide:** Maine `{customer_col}`, `{sales_col}`, aur `{date_col}` ko map kar liya hai.")
        query = st.text_input("Apna complex sawal pucho (e.g. Sales in Oct-Nov but not in Dec):")
        
        if query:
            with st.spinner('AI dimaag laga raha hai...'):
                # AI ko map kiye hue columns batao taaki wo fail na ho
                prompt = f"""
                You are a SQLite expert. Table name is 'mytable'.
                Mapping Information:
                - Date column is: "{date_col}"
                - Customer name column is: "{customer_col}"
                - Sales/Value column is: "{sales_col}"
                - State/Region column is: "{state_col}"
                
                Columns list: {cols}
                
                User Request: {query}
                
                Instructions:
                1. Use STRFTIME('%m', "{date_col}") for month comparison.
                2. To find customers in Oct/Nov but not Dec, use EXCEPT or NOT IN.
                3. Return ONLY the raw SQL query. No markdown.
                """
                
                try:
                    response = model.generate_content(prompt)
                    sql = response.text.strip().replace('```sql', '').replace('```', '')
                    sql = re.sub(r'^(sqlite|sql|ite)\s*', '', sql, flags=re.IGNORECASE)
                    
                    conn = sqlite3.connect('bishape_final.db')
                    result = pd.read_sql_query(sql, conn)
                    
                    if not result.empty:
                        st.success(f"Bhai, {len(result)} records mile hain!")
                        st.dataframe(result, use_container_width=True)
                        st.download_button("Download Report", result.to_csv(index=False), "ai_report.csv")
                    else:
                        st.warning("Query toh sahi thi, par koi data match nahi hua.")
                        st.code(sql)
                except Exception as e:
                    st.error("AI thoda confuse hai. Try adding more detail to the question.")
                    st.code(sql if 'sql' in locals() else "No SQL Generated")

    with tab2:
        st.subheader("Sales Breakdown")
        fig = px.histogram(df, x=state_col, y=sales_col, color=state_col, title="State-wise Sales Contribution")
        st.plotly_chart(fig, use_container_width=True)

else:
    st.info("Bhai, sidebar se file upload karo aur columns map karo!")
