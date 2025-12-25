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
        # Columns clean karna taaki SQL query na toote
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
    query = st.text_input("Data ke baare mein sawal pucho:")

    if query:
        with st.spinner('AI SQLite query bana raha hai...'):
            # MAINE YAHAN INSTRUCTION BADAL DI HAI
            prompt = f"""
            You are a SQLite expert. Table name is 'mytable'. 
            Columns are: {cols}.
            User Question: {query}
            
            STRICT RULES:
            1. Use ONLY SQLite syntax.
            2. For Year, use: strftime('%Y', column_name)
            3. For Month, use: strftime('%m', column_name)
            4. Output ONLY the raw SQL query. No explanation.
            """
            try:
                response = model.generate_content(prompt)
                sql_query = response.text.replace('```sql', '').replace('```', '').strip()
                
                conn = sqlite3.connect('data.db')
                result = pd.read_sql_query(sql_query, conn)
                
                st.subheader("AI Ka Jawab:")
                st.dataframe(result)
            except Exception as e:
                st.error(f"Technical error: {e}")
                st.info("Tip: Agar date wala error aaye, toh check karein ki Excel mein date column sahi format mein hai ya nahi.")

with st.expander("Data Preview"):
    if uploaded_file and 'cols' in locals() and cols:
        st.write(preview)
