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
        st.error("Bhai, Streamlit Secrets mein API Key dalo!")
        st.stop()
except Exception as e:
    st.error(f"Setup Error: {e}")
    st.stop()

# 3. Logistics Data Engine
@st.cache_data
def load_and_clean(file):
    try:
        df = pd.read_excel(file) if file.name.endswith('.xlsx') else pd.read_csv(file)
        df.columns = [re.sub(r'[^a-zA-Z0-9]', '_', c) for c in df.columns]
        
        # 🧼 Error Zeroed Logic: Missing values ko 0 karo
        df = df.fillna(0)
        
        # Date conversion for Logistics/Packing Slips
        for col in df.columns:
            if 'date' in col.lower():
                df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime('%Y-%m-%d')
        
        conn = sqlite3.connect('bishape_final_v4.db', check_same_thread=False)
        df.to_sql('mytable', conn, if_exists='replace', index=False)
        return df
    except Exception as e:
        st.error(f"File Load Error: {e}")
        return None

uploaded_file = st.sidebar.file_uploader("Upload Master File", type=['xlsx', 'csv'])

if uploaded_file:
    df = load_and_clean(uploaded_file)
    cols = df.columns.tolist()
    st.success(f"Taiyaar! {len(df)} records ready hain.")

    # KPI View
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if num_cols:
        c1, c2 = st.columns(2)
        c1.metric("Total Records", len(df))
        c2.metric(f"Total {num_cols[0]}", f"₹{df[num_cols[0]].sum():,.0f}")

    # Chat Interface
    st.divider()
    query = st.text_input("Apna sawal pucho (e.g. Month-wise lowest sales owner):")

    if query:
        with st.spinner('AI Query check kar raha hai...'):
            # 🛠️ STRICK PROMPT: CTE (WITH) structure must be correct
            prompt = f"""
            You are a SQLite expert. Table: 'mytable', Columns: {cols}.
            
            Rules for Complex Queries:
            1. If you need ranking or subqueries, use a CTE: 'WITH MonthlySales AS (SELECT...) SELECT...'.
            2. NEVER start with a SELECT and end it with a ')' without a WITH clause at the beginning.
            3. Use double quotes for all columns: "Date", "OWNER", etc.
            4. Start ONLY with 'SELECT' or 'WITH'.
            5. Return ONLY the raw SQL query. No notes.
            """
            try:
                response = model.generate_content(prompt + f" Question: {query}")
                sql_raw = response.text.strip().replace('```sql', '').replace('```', '').strip()
                
                # 🧼 CLEANING: Prefix 'ite' ya notes hatana
                match = re.search(r'(SELECT|WITH)', sql_raw, re.IGNORECASE)
                if match:
                    sql_final = sql_raw[match.start():].split(';')[0] + ';'
                else:
                    sql_final = sql_raw

                # 🧼 AUTO-FIX: Agar AI ne 'WITH' bhool kar query 'MonthlySales AS (' se shuru ki
                if "AS (" in sql_final.upper() and not sql_final.upper().startswith("WITH"):
                    sql_final = "WITH MonthlySales AS " + sql_final

                # Database Execution
                conn = sqlite3.connect('bishape_final_v4.db')
                result = pd.read_sql_query(sql_final, conn)
                
                st.subheader("AI Ka Jawab:")
                st.dataframe(result, use_container_width=True)
                st.download_button("Download as CSV", result.to_csv(index=False), "report.csv")
                
            except Exception as e:
                st.error("Syntax Error! AI ne query galat format mein di.")
                st.info(f"Generated SQL: {sql_final if 'sql_final' in locals() else 'N/A'}")
                st.info(f"Details: {e}")
else:
    st.info("Bhai, pehle sidebar se logistics file upload karo.")
