import streamlit as st
import pandas as pd
import sqlite3
import google.generativeai as genai
import re
import numpy as np

# 1. Page Config & Branding
st.set_page_config(page_title="Bishape AI Pro", layout="wide")
st.title("🤖 Bishape Ultra-Robust AI Analyst")

# 2. AI Key Setup (Using Secrets)
try:
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"].strip()
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-flash-latest')
    else:
        st.error("Bhai, Streamlit Secrets mein API Key nahi mili!")
        st.stop()
except Exception as e:
    st.error(f"Setup Error: {e}")
    st.stop()

# 3. SELF-REPAIRING DATA ENGINE
def full_clean(df):
    # Duplicate Column Check
    cols = pd.Series(df.columns)
    for dup in cols[cols.duplicated()].unique(): 
        cols[cols == dup] = [f"{dup}_{i}" if i != 0 else dup for i in range(sum(cols == dup))]
    df.columns = cols
    
    # Column Formatting for SQL
    df.columns = [re.sub(r'[^a-zA-Z0-9]', '_', str(c)) for c in df.columns]
    
    # Missing Values to 0 (Fixing ValueError)
    df = df.fillna(0)
    
    # Auto-Date Standardization for Logistics Reports
    for col in df.columns:
        if 'date' in col.lower() or 'dt' in col.lower():
            df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime('%Y-%m-%d')
    return df

@st.cache_data
def sync_to_db(file):
    try:
        df = pd.read_excel(file) if file.name.endswith('.xlsx') else pd.read_csv(file)
        df = full_clean(df)
        
        # 🛠️ Database Connection (Ensuring table exists)
        conn = sqlite3.connect('bishape_final.db', check_same_thread=False)
        df.to_sql('mytable', conn, if_exists='replace', index=False)
        return df
    except Exception as e:
        st.error(f"File Loading Error: {e}")
        return None

# Sidebar Upload
uploaded_file = st.sidebar.file_uploader("Upload Logistics Master", type=['xlsx', 'csv'])

if uploaded_file:
    df = sync_to_db(uploaded_file)
    if df is not None:
        cols = df.columns.tolist()
        st.success(f"Success! {len(df)} records are live.")

        # --- SMART DASHBOARD ---
        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if num_cols:
            c1, c2 = st.columns(2)
            c1.metric("Total Records", f"{len(df):,}")
            # Dynamic Total Value calculation
            total_val = df[num_cols[0]].sum()
            c2.metric("Total Business Value", f"₹{total_val:,.0f}")

        # --- CHAT / QUERY SECTION ---
        st.divider()
        query = st.text_input("Ask about your data (e.g. ASM performance list):")
        
        if query:
            with st.spinner('AI analyzing...'):
                prompt = f"""
                Act as a SQLite Expert. 
                Table name: 'mytable', Columns: {cols}.
                User Question: {query}
                Rule: Output ONLY the raw SQL query. No explanations.
                """
                try:
                    response = model.generate_content(prompt)
                    raw_sql = response.text.strip()
                    
                    # 🧼 AGGRESSIVE SQL SANITIZER
                    match = re.search(r'(SELECT|WITH)', raw_sql, re.IGNORECASE)
                    if match:
                        sql_final = raw_sql[match.start():].split(';')[0] + ';'
                        sql_final = re.sub(r'--.*', '', sql_final).replace('\n', ' ').strip()
                        
                        # Database Execution
                        conn = sqlite3.connect('bishape_final.db')
                        result = pd.read_sql_query(sql_final, conn)
                        
                        st.subheader("📊 Result")
                        st.dataframe(result, use_container_width=True)
                    else:
                        st.warning("AI couldn't build a valid query. Try being more specific.")
                except Exception as e:
                    st.error(f"Query Error: {e}")
                    # Debug view for learning Python
                    with st.expander("Show SQL Debug Info"):
                        st.code(sql_final if 'sql_final' in locals() else "None")
    else:
        st.error("Data could not be synchronized.")
else:
    st.info("Please upload a file to start.")
