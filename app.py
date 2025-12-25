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
        
        # 🛠️ DATE FIX: Agar column mein 'Date' hai toh use sahi format mein badlo
        for col in df.columns:
            if 'date' in col.lower():
                df[col] = pd.to_datetime(df[col]).dt.strftime('%Y-%m-%d')
        
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
    query = st.text_input("Data ke baare mein sawal pucho (e.g. Index trends dikhao):")

    if query:
        with st.spinner('AI data analysis kar raha hai...'):
            # 🛠️ IMPROVED PROMPT
            prompt = f"""
            You are a SQLite expert. Table: 'mytable'. Columns: {cols}.
            User Question: {query}
            
            RULES:
            1. Wrap ALL column names in double quotes, like "Index" or "Date".
            2. For trends, group by Date or Month.
            3. Output ONLY the raw SQL query.
            """
            try:
                response = model.generate_content(prompt)
                sql_query = response.text.strip()
                sql_query = re.sub(r'^(sqlite|ite|sql|markdown)\s*', '', sql_query, flags=re.IGNORECASE)
                sql_query = sql_query.replace('```sql', '').replace('```', '').strip()
                
                conn = sqlite3.connect('data.db')
                result = pd.read_sql_query(sql_query, conn)
                
                st.subheader("AI Ka Jawab:")
                st.dataframe(result)
                
                # 🛠️ CHART AUTO-GENERATION: Agar trends hai toh graph bhi dikhao
                if len(result.columns) >= 2:
                    st.line_chart(result.set_index(result.columns[0]))
                    
            except Exception as e:
                st.error(f"Error: {e}")
                st.info(f"Query check karein: {sql_query if 'sql_query' in locals() else 'None'}")

with st.expander("Data Preview"):
    if uploaded_file and 'cols' in locals() and cols:
        st.write(preview)
