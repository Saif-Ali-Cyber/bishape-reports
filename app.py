import streamlit as st
import pandas as pd
import sqlite3
import google.generativeai as genai
import re
import numpy as np

# 1. Page Config
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

# 3. ADVANCED Data Engine (Fixes Duplicate Columns)
def rename_duplicates(df):
    cols = pd.Series(df.columns)
    for dup in cols[cols.duplicated()].unique(): 
        cols[cols == dup] = [f"{dup}_{i}" if i != 0 else dup for i in range(sum(cols == dup))]
    df.columns = cols
    return df

@st.cache_data
def load_and_clean(file):
    try:
        # File load karna
        df = pd.read_excel(file) if file.name.endswith('.xlsx') else pd.read_csv(file)
        
        # 🧼 STEP 1: Pehle duplicate columns handle karo
        df = rename_duplicates(df)
        
        # 🧼 STEP 2: Special characters hatana
        df.columns = [re.sub(r'[^a-zA-Z0-9]', '_', c) for c in df.columns]
        
        # 🧼 STEP 3: Duplicate cleaning phir se (cleaning ke baad banne wale duplicates)
        df = rename_duplicates(df)

        # 🧼 STEP 4: Missing values ko 0 karo
        df = df.fillna(0)
        
        # Date conversion for Packing Slips
        for col in df.columns:
            if 'date' in col.lower():
                df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime('%Y-%m-%d')
        
        # Database mein save karna
        conn = sqlite3.connect('bishape_v5.db', check_same_thread=False)
        df.to_sql('mytable', conn, if_exists='replace', index=False)
        return df
    except Exception as e:
        st.error(f"File Load Error: {e}")
        return None

# Sidebar Upload
uploaded_file = st.sidebar.file_uploader("Upload Logistics Master", type=['xlsx', 'csv'])

if uploaded_file:
    df = load_and_clean(uploaded_file)
    
    # 🛠️ SAFETY CHECK: Agar df None hai toh aage mat badho
    if df is not None:
        cols = df.columns.tolist()
        st.success(f"Taiyaar! {len(df)} records load ho gaye hain.")

        # KPI Header
        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if num_cols:
            c1, c2 = st.columns(2)
            c1.metric("Total Records", len(df))
            c2.metric(f"Total {num_cols[0]}", f"₹{df[num_cols[0]].sum():,.0f}")

        # Chat Interface
        st.divider()
        query = st.text_input("Data se sawal pucho (e.g. State wise sales):")

        if query:
            with st.spinner('AI Query bana raha hai...'):
                prompt = f"SQLite expert. Table: 'mytable', Columns: {cols}. User Query: {query}. Start with SELECT."
                try:
                    response = model.generate_content(prompt)
                    sql_raw = response.text.strip().replace('```sql', '').replace('```', '').strip()
                    
                    # SELECT filter
                    match = re.search(r'(SELECT|WITH)', sql_raw, re.IGNORECASE)
                    if match:
                        sql_final = sql_raw[match.start():].split(';')[0] + ';'
                    else:
                        sql_final = sql_raw

                    conn = sqlite3.connect('bishape_v5.db')
                    result = pd.read_sql_query(sql_final, conn)
                    st.subheader("AI Ka Jawab:")
                    st.dataframe(result, use_container_width=True)
                except Exception as e:
                    st.error(f"Execution Error: {e}")
                    st.info(f"Query: {sql_final if 'sql_final' in locals() else 'N/A'}")
    else:
        st.warning("Bhai, file mein gadbad hai. Please column names check karein.")
else:
    st.info("Sidebar se file upload karein!")
