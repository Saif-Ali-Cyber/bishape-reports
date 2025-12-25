import streamlit as st
import pandas as pd
import sqlite3
import google.generativeai as genai
import re

# 1. Page Config
st.set_page_config(page_title="Bishape AI Pro", layout="wide")
st.title("🤖 Bishape Smart AI Reporter")

# 2. AI Setup
API_KEY = "AIzaSyDyrJrSLXRyjG_Mp9n6W5DC_UidvGRMO50"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-flash-latest')

# 3. File Processing
uploaded_file = st.file_uploader("Apni Excel/CSV file dalo", type=['xlsx', 'csv'])

@st.cache_data
def load_data_to_sqlite(file):
    try:
        df = pd.read_excel(file) if file.name.endswith('.xlsx') else pd.read_csv(file)
        conn = sqlite3.connect('data.db', check_same_thread=False)
        # Columns clean karna
        df.columns = [re.sub(r'[^a-zA-Z0-9]', '_', c) for c in df.columns]
        df.to_sql('mytable', conn, if_exists='replace', index=False)
        return df.columns.tolist(), len(df), df.head(5)
    except Exception as e:
        return None, 0, str(e)

if uploaded_file:
    cols, total_rows, preview = load_data_to_sqlite(uploaded_file)
    if cols:
        st.success(f"Taiyaar! {total_rows} rows load ho gayi hain.")

    # 4. Chat Interface
    st.divider()
    query = st.text_input("Data ke baare mein sawal pucho (e.g. RSM wise monthly sales):")

    if query:
        with st.spinner('AI Report taiyaar kar raha hai...'):
            # Prompt ko aur strict kar diya hai
            prompt = f"""
            You are a SQLite expert. Table: 'mytable'. Columns: {cols}.
            Question: {query}
            Instruction: Provide ONLY the SQL query. 
            Start the query directly with the word SELECT.
            Use STRFTIME('%m', "Date") for month and STRFTIME('%Y', "Date") for year.
            """
            try:
                response = model.generate_content(prompt)
                raw_text = response.text.strip()
                
                # 🛠️ SUPER CLEANER: 'SELECT' dhoondo aur wahan se query shuru karo
                # Isse 'ite', 'sqlite', 'sql' sab apne aap hat jayenge
                start_index = raw_text.upper().find("SELECT")
                if start_index != -1:
                    sql_query = raw_text[start_index:].replace('```', '').strip()
                else:
                    sql_query = raw_text # Fallback agar SELECT na mile
                
                # Database query chalana
                conn = sqlite3.connect('data.db')
                result = pd.read_sql_query(sql_query, conn)
                
                st.subheader("AI Ka Jawab:")
                st.dataframe(result)
                
                # Option to download result
                st.download_button("Download Report", result.to_csv(index=False), "report.csv")
                
            except Exception as e:
                st.error(f"Error: AI ki query fail ho gayi.")
                st.info(f"Query jo bani thi: {sql_query if 'sql_query' in locals() else 'None'}")
                st.info(f"Wajah: {e}")

with st.expander("Data Preview"):
    if uploaded_file and 'cols' in locals() and cols:
        st.write(preview)
