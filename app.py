import streamlit as st
import pandas as pd
import sqlite3
import google.generativeai as genai
import re
import numpy as np

# 1. UI Setup
st.set_page_config(page_title="Bishape AI Pro", layout="wide")
st.title("🤖 Bishape Smart AI Reporter")

# 2. AI Setup
try:
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"].strip()
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-flash-latest')
    else:
        st.error("Bhai, Secrets mein API Key dalo!")
        st.stop()
except Exception as e:
    st.error(f"Setup Error: {e}")
    st.stop()

# 3. Data Engine (Duplicate Column Fix)
def rename_duplicates(df):
    cols = pd.Series(df.columns)
    for dup in cols[cols.duplicated()].unique(): 
        cols[cols == dup] = [f"{dup}_{i}" if i != 0 else dup for i in range(sum(cols == dup))]
    df.columns = cols
    return df

@st.cache_data
def load_and_clean(file):
    try:
        df = pd.read_excel(file) if file.name.endswith('.xlsx') else pd.read_csv(file)
        df = rename_duplicates(df)
        df.columns = [re.sub(r'[^a-zA-Z0-9]', '_', c) for c in df.columns]
        df = rename_duplicates(df)
        df = df.fillna(0) # Error Zeroed logic
        
        # Date Handling for Logistics/Packing Slips
        for col in df.columns:
            if 'date' in col.lower():
                df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime('%Y-%m-%d')
        
        conn = sqlite3.connect('bishape_ultra_safe.db', check_same_thread=False)
        df.to_sql('mytable', conn, if_exists='replace', index=False)
        return df
    except Exception as e:
        st.error(f"File Load Error: {e}")
        return None

# Sidebar
uploaded_file = st.sidebar.file_uploader("Upload Logistics Master", type=['xlsx', 'csv'])

if uploaded_file:
    df = load_and_clean(uploaded_file)
    if df is not None:
        cols = df.columns.tolist()
        st.success(f"Taiyaar! {len(df)} records ready hain.")

        # Chat Interface
        st.divider()
        query = st.text_input("Data se sawal pucho (e.g. Monthly sales pivot):")

        if query:
            with st.spinner('AI Query ko sanitize kar raha hai...'):
                prompt = f"""
                Act as a SQLite expert. Table: 'mytable'. Columns: {cols}.
                User Query: {query}
                
                STRICT RULES:
                1. Return ONLY the raw SQL query.
                2. NO explanations, NO intro text, NO markdown code blocks.
                3. DO NOT use comments (--) inside the query.
                4. Start directly with SELECT or WITH.
                """
                try:
                    response = model.generate_content(prompt)
                    sql_raw = response.text.strip()
                    
                    # 🛠️ AGGRESSIVE SANITIZER
                    # 1. 'SELECT' ya 'WITH' dhoondo aur wahan se shuru karo
                    match = re.search(r'(SELECT|WITH)', sql_raw, re.IGNORECASE)
                    if match:
                        sql_final = sql_raw[match.start():].split(';')[0] + ';'
                        # 2. Saare inline comments (--) aur newlines saaf karo
                        sql_final = re.sub(r'--.*', '', sql_final) 
                        sql_final = sql_final.replace('\n', ' ').strip()
                    else:
                        sql_final = sql_raw

                    conn = sqlite3.connect('bishape_ultra_safe.db')
                    result = pd.read_sql_query(sql_final, conn)
                    
                    st.subheader("AI Ka Jawab:")
                    st.dataframe(result, use_container_width=True)
                    st.download_button("Download Report (CSV)", result.to_csv(index=False), "bishape_report.csv")
                except Exception as e:
                    st.error("Syntax Error!")
                    st.info(f"Sanitized Query: {sql_final if 'sql_final' in locals() else 'None'}")
                    st.info(f"Reason: {e}")
else:
    st.info("Bhai, sidebar se logistics file upload karo pehle!")
