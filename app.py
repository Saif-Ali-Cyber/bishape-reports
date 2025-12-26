import streamlit as st
import pandas as pd
import sqlite3
import google.generativeai as genai
import re
import numpy as np

# 1. UI & Branding
st.set_page_config(page_title="Bishape AI Auto-Pilot", layout="wide", page_icon="🤖")
st.title("🛡️ Bishape Reinforced AI Analyst")

# 2. Secure AI Setup
try:
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"].strip()
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-flash-latest')
    else:
        st.error("Bhai, Streamlit Secrets mein API Key missing hai!")
        st.stop()
except Exception as e:
    st.error(f"Setup Error: {e}")
    st.stop()

# 3. SELF-HEALING DATA ENGINE
def reinforced_cleaning(df):
    # Duplicate Column Fix
    cols = pd.Series(df.columns)
    for dup in cols[cols.duplicated()].unique(): 
        cols[cols == dup] = [f"{dup}_{i}" if i != 0 else dup for i in range(sum(cols == dup))]
    df.columns = cols
    
    # Special Characters & Spaces Fix
    df.columns = [re.sub(r'[^a-zA-Z0-9]', '_', str(c)) for c in df.columns]
    
    # Missing Values (Error Zeroed)
    df = df.fillna(0)
    
    # Auto-Date Detection & Formatting
    for col in df.columns:
        if 'date' in col.lower() or 'dt' in col.lower():
            df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime('%Y-%m-%d')
            
    return df

@st.cache_data
def load_and_sync(file):
    try:
        df = pd.read_excel(file) if file.name.endswith('.xlsx') else pd.read_csv(file)
        df = reinforced_cleaning(df)
        conn = sqlite3.connect('bishape_reinforced.db', check_same_thread=False)
        df.to_sql('mytable', conn, if_exists='replace', index=False)
        return df
    except Exception as e:
        st.error(f"Data Load Error: {e}")
        return None

# 4. REINFORCED SQL SANITIZER
def sanitize_sql(raw_text):
    # AI ke bhashan mein se sirf SELECT ya WITH uthana
    match = re.search(r'(SELECT|WITH)', raw_text, re.IGNORECASE)
    if not match: return None
    
    sql = raw_text[match.start():].split(';')[0] + ';'
    sql = re.sub(r'--.*', '', sql) # Inline comments hatana
    sql = sql.replace('\n', ' ').replace('`', '"').strip() # Quotes fix
    return " ".join(sql.split())

# --- APP LOGIC ---
uploaded_file = st.sidebar.file_uploader("Upload Logistics/Order Data", type=['xlsx', 'csv'])

if uploaded_file:
    df = load_and_sync(uploaded_file)
    if df is not None:
        cols = df.columns.tolist()
        
        # --- AUTOMATIC DATA AUDIT ---
        with st.expander("✅ Data Health Audit (Automated)", expanded=False):
            st.write(f"Total Rows: {len(df)} | Columns: {len(cols)}")
            st.write("Missing values handled and dates standardized.")

        # --- AUTO-PILOT DASHBOARD ---
        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if num_cols:
            c1, c2, c3 = st.columns(3)
            c1.metric("Orders Processed", f"{len(df):,}")
            c2.metric("Gross Value", f"₹{df[num_cols[0]].sum():,.0f}")
            c3.metric("Avg Ticket Size", f"₹{df[num_cols[0]].mean():,.2f}")

        # --- SMART CHAT ---
        st.divider()
        query = st.text_input("Sawal pucho (e.g. ASM performance this month):")
        
        if query:
            with st.spinner('AI logic aur syntax check kar raha hai...'):
                prompt = f"""
                SQLite Expert. Table: 'mytable', Columns: {cols}.
                Query: {query}
                Rule: Output ONLY raw SQL. No comments. Use double quotes for columns.
                """
                try:
                    response = model.generate_content(prompt)
                    sql_final = sanitize_sql(response.text)
                    
                    if sql_final:
                        conn = sqlite3.connect('bishape_reinforced.db')
                        result = pd.read_sql_query(sql_final, conn)
                        st.subheader("📊 Analysis Result")
                        st.dataframe(result, use_container_width=True)
                        st.download_button("Download Report", result.to_csv(index=False), "auto_report.csv")
                    else:
                        st.warning("AI query samajh nahi paya. Thoda saaf sawal pucho.")
                except Exception as e:
                    st.error(f"Execution Error! AI ne query todi. Details: {e}")
                    # Auto-Correction Tip
                    if "no such column" in str(e).lower():
                        st.info("Tip: Column ka sahi naam use karein jaise Excel mein hai.")
    else:
        st.warning("File processing fail hui.")
else:
    st.info("Sidebar se logistics file upload karein aur dashboard activate karein!")
