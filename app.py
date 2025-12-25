import streamlit as st
import pandas as pd
import sqlite3
import google.generativeai as genai
import re

# 1. AI Setup
st.set_page_config(page_title="Bishape AI Pro", layout="wide")
st.title("🤖 Bishape Smart AI Reporter")

# API Key ko saaf (clean) karke uthana
try:
    if "GEMINI_API_KEY" not in st.secrets:
        st.error("Bhai, Streamlit Secrets mein API Key nahi mili!")
        st.stop()
    
    api_key = st.secrets["GEMINI_API_KEY"].strip() # Faltu spaces hatane ke liye
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"Setup Error: {e}")
    st.stop()

# 2. Heavy File Processing (100MB Friendly)
uploaded_file = st.file_uploader("Apni Excel/CSV file dalo", type=['xlsx', 'csv'])

@st.cache_data
def load_data_to_sqlite(file):
    # Data load karo
    if file.name.endswith('.csv'):
        df = pd.read_csv(file)
    else:
        df = pd.read_excel(file)
    
    # SQLite Database banana
    conn = sqlite3.connect('data.db', check_same_thread=False)
    # Column names se spaces hatana taaki SQL query na toote
    df.columns = [c.replace(' ', '_').replace('(', '').replace(')', '') for c in df.columns]
    df.to_sql('mytable', conn, if_exists='replace', index=False)
    return df.columns.tolist(), len(df)

if uploaded_file:
    with st.spinner('File process ho rahi hai...'):
        cols, total_rows = load_data_to_sqlite(uploaded_file)
        st.success(f"Taiyaar! {total_rows} rows aur ye columns mile: {', '.join(cols)}")

    # 3. Chat Logic
    query = st.text_input("Sawal pucho (e.g. Total sales kitni hai?)")

    if query:
        with st.spinner('AI dimaag laga raha hai...'):
            # AI ko sirf instruction do, data nahi
            prompt = f"""
            You are a SQL expert. We have a table 'mytable' with columns: {cols}.
            User wants to know: {query}
            Output ONLY the SQL query. No text, no markdown.
            Example: SELECT SUM(Sales) FROM mytable
            """
            try:
                response = model.generate_content(prompt)
                # Query se ```sql aur faltu cheezein hatana
                clean_sql = re.sub(r'```sql|```', '', response.text).strip()
                
                # Database se answer nikalna
                conn = sqlite3.connect('data.db')
                result = pd.read_sql_query(clean_sql, conn)
                
                st.subheader("AI Ka Jawab:")
                st.write(result)
            except Exception as e:
                st.error("AI thoda confuse ho gaya. Koshish karein ki column ka naam sawal mein likhein.")
                st.info(f"Technical Error: {e}")
