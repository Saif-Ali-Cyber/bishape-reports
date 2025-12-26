import streamlit as st
import pandas as pd
import sqlite3
import google.generativeai as genai
import re

# 1. UI Setup
st.set_page_config(page_title="Bishape AI Pro", layout="wide")
st.title("🤖 Bishape Smart AI Reporter")

# 2. AI Setup (Using Secrets for Security)
try:
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
    else:
        st.error("Bhai, Secrets mein API Key nahi mili! Pehle Secrets setup karo.")
        st.stop()
        
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-flash-latest')
except Exception as e:
    st.error(f"Setup Error: {e}")
    st.stop()

# 3. File Processing
uploaded_file = st.file_uploader("Apni Excel/CSV file dalo", type=['xlsx', 'csv'])

@st.cache_data
def load_data_to_sqlite(file):
    try:
        df = pd.read_excel(file) if file.name.endswith('.xlsx') else pd.read_csv(file)
        conn = sqlite3.connect('data.db', check_same_thread=False)
        df.columns = [re.sub(r'[^a-zA-Z0-9]', '_', c) for c in df.columns]
        df.to_sql('mytable', conn, if_exists='replace', index=False)
        return df.columns.tolist(), len(df), df.head(5)
    except Exception as e:
        return None, 0, str(e)

if uploaded_file:
    cols, total_rows, preview = load_data_to_sqlite(uploaded_file)
    if cols:
        st.success(f"Taiyaar! {total_rows} rows load ho gayi hain.")

    st.divider()
    query = st.text_input("Data ke baare mein sawal pucho:")

    if query:
        with st.spinner('AI Query bana raha hai...'):
            prompt = f"SQLite expert. Table: 'mytable'. Columns: {cols}. Question: {query}. Start query with SELECT."
            try:
                response = model.generate_content(prompt)
                raw_text = response.text.strip()
                
                # 'SELECT' se query start karne ka logic
                start_index = raw_text.upper().find("SELECT")
                if start_index != -1:
                    sql_query = raw_text[start_index:].replace('```', '').strip()
                    
                    conn = sqlite3.connect('data.db')
                    result = pd.read_sql_query(sql_query, conn)
                    st.subheader("AI Ka Jawab:")
                    st.dataframe(result)
                else:
                    st.warning("AI query theek se nahi bana paya. Thoda saaf sawal pucho.")
            except Exception as e:
                st.error(f"Error: {e}")

with st.expander("Data Preview"):
    if uploaded_file and 'cols' in locals() and cols:
        st.write(preview)
