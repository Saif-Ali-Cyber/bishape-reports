import streamlit as st
import pandas as pd
import sqlite3
import google.generativeai as genai

# 1. AI Setup (Bilkul Clean)
st.set_page_config(page_title="Bishape AI Pro", layout="wide")
st.title("🤖 Bishape Smart AI Reporter")

# API Key ko saaf karke uthana (Extra space hata kar)
try:
    raw_key = st.secrets["GEMINI_API_KEY"]
    api_key = raw_key.strip() # Strip se f फालतू spaces hat jayenge
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error("Bhai API Key setup mein dikkat hai. Streamlit Secrets check kar.")
    st.stop()

# 2. Heavy File Processing
uploaded_file = st.file_uploader("Apni 100MB wali file dalo", type=['xlsx', 'csv'])

@st.cache_data
def load_to_db(file):
    # Data load karo
    df = pd.read_excel(file) if file.name.endswith('.xlsx') else pd.read_csv(file)
    # Database se connect karo
    conn = sqlite3.connect('bishape_data.db', check_same_thread=False)
    # Data ko SQL table mein daal do
    df.to_sql('mytable', conn, if_exists='replace', index=False)
    return df.columns.tolist(), len(df)

if uploaded_file:
    cols, row_count = load_to_db(uploaded_file)
    st.success(f"File Ready! {row_count} rows aur {len(cols)} columns mile.")

    # 3. Chat Logic
    query = st.text_input("Data ke baare mein pucho (e.g. Total sales kitni hai?)")

    if query:
        with st.spinner('AI dimaag laga raha hai...'):
            # AI ko sirf Columns dikhao, pura data nahi!
            prompt = f"""
            You are a SQL expert. We have a table named 'mytable' with these columns: {cols}.
            The user wants to know: {query}
            Give me ONLY the SQL query to answer this. No explanation.
            Example: SELECT SUM(Sales) FROM mytable
            """
            try:
                # Step 1: AI se SQL query likhwao
                response = model.generate_content(prompt)
                sql_query = response.text.strip().replace('```sql', '').replace('```', '')
                
                # Step 2: Wo query Database par chalao
                conn = sqlite3.connect('bishape_data.db')
                result = pd.read_sql_query(sql_query, conn)
                
                # Step 3: Result dikhao
                st.subheader("AI ka Jawab:")
                st.write(result)
                
            except Exception as e:
                st.error(f"Error: AI thoda confuse ho gaya. Try again!")
                st.info("Tip: Sawal thoda clear pucho, jaise 'Sales column ka total dikhao'")
