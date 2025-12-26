import streamlit as st
import pandas as pd
import sqlite3
import google.generativeai as genai
import re

# 1. UI Setup
st.set_page_config(page_title="Bishape AI Pro", layout="wide")
st.title("🤖 Bishape Smart AI Reporter")

# 2. AI Setup (Using Secrets)
try:
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"].strip()
    else:
        st.error("Bhai, Secrets mein API Key nahi mili!")
        st.stop()
        
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-flash-latest')
except Exception as e:
    st.error(f"Setup Error: {e}")
    st.stop()

# 3. Logistics Data Loader
@st.cache_data
def load_data(file):
    df = pd.read_excel(file) if file.name.endswith('.xlsx') else pd.read_csv(file)
    df.columns = [re.sub(r'[^a-zA-Z0-9]', '_', c) for c in df.columns]
    df = df.fillna(0) # Error Zeroed
    
    # Date formatting for Packing Slips/Reports
    for col in df.columns:
        if 'date' in col.lower():
            df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime('%Y-%m-%d')
            
    conn = sqlite3.connect('bishape_final.db', check_same_thread=False)
    df.to_sql('mytable', conn, if_exists='replace', index=False)
    return df

uploaded_file = st.sidebar.file_uploader("Upload Logistics Master", type=['xlsx', 'csv'])

if uploaded_file:
    df = load_data(uploaded_file)
    cols = df.columns.tolist()

    st.success(f"Data Loaded! Total Rows: {len(df)}")
    query = st.text_input("Apna sawal pucho (e.g. Owner wise monthly sales):")

    if query:
        with st.spinner('AI Query saaf kar raha hai...'):
            # 🛠️ STRICT PROMPT: No Comments allowed
            prompt = f"""
            Act as a SQLite expert. Table: 'mytable'. Columns: {cols}.
            User Question: {query}
            
            RULES:
            1. Return ONLY the SQL query.
            2. Do NOT use comments (--) inside the query.
            3. Do NOT provide any notes or explanations after the query.
            4. Start directly with SELECT.
            5. End with a semicolon ;
            """
            try:
                response = model.generate_content(prompt)
                raw_sql = response.text.strip()
                
                # 🧼 CLEANING: Sabse pehle 'SELECT' dhoondo
                start_index = raw_text.upper().find("SELECT") if 'raw_text' in locals() else raw_sql.upper().find("SELECT")
                sql_clean = raw_sql[max(0, start_index):].replace('```sql', '').replace('```', '').strip()
                
                # 🧼 FILTER: Semicolon ke baad ka sab delete karo (Notes hatane ke liye)
                sql_final = sql_clean.split(';')[0] + ';'
                
                conn = sqlite3.connect('bishape_final.db')
                result = pd.read_sql_query(sql_final, conn)
                
                st.subheader("AI Ka Jawab:")
                st.dataframe(result, use_container_width=True)
                st.download_button("Download Report", result.to_csv(index=False), "logistics_report.csv")
                
            except Exception as e:
                st.error("Bhai, AI ne extra text likh diya jo SQL nahi samajh pa raha.")
                st.info(f"Query bani thi: {sql_final if 'sql_final' in locals() else 'None'}")
                st.info(f"Technical Error: {e}")

else:
    st.info("Sidebar se file upload karein!")
