import streamlit as st
import pandas as pd
import sqlite3
import google.generativeai as genai
import re

# 1. Page Config
st.set_page_config(page_title="Bishape AI Pro", layout="wide")
st.title("🤖 Bishape Smart AI Reporter")

# 2. AI Setup - Model ka naam change kar diya hai
API_KEY = "AIzaSyDyrJrSLXRyjG_Mp9n6W5DC_UidvGRMO50"
genai.configure(api_key=API_KEY)

# Hum yahan 'gemini-pro' use kar rahe hain jo sabse stable hai
model = genai.GenerativeModel('gemini-pro')

# 3. File Processing
uploaded_file = st.file_uploader("Apni Excel/CSV file yahan dalo", type=['xlsx', 'csv'])

@st.cache_data
def load_data_to_sqlite(file):
    try:
        if file.name.endswith('.csv'):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)
        
        conn = sqlite3.connect('data.db', check_same_thread=False)
        # Columns clean karna taaki SQL query fail na ho
        df.columns = [re.sub(r'[^a-zA-Z0-9]', '_', c) for c in df.columns]
        df.to_sql('mytable', conn, if_exists='replace', index=False)
        return df.columns.tolist(), len(df), df.head(5)
    except Exception as e:
        return None, 0, str(e)

if uploaded_file:
    cols, total_rows, preview = load_data_to_sqlite(uploaded_file)
    
    if cols:
        st.success(f"File Ready! {total_rows} rows load ho gayi hain.")
    else:
        st.error(f"File load nahi ho payi: {preview}")

    # 4. Chat Interface
    st.divider()
    query = st.text_input("Data ke baare mein sawal pucho:")

    if query:
        with st.spinner('AI soch raha hai...'):
            # Prompt ko simple rakha hai
            prompt = f"""
            You are a SQL expert. Table name is 'mytable'. 
            Columns are: {cols}.
            User Question: {query}
            Give ONLY the SQL query. No explanation.
            Example: SELECT * FROM mytable LIMIT 5
            """
            try:
                response = model.generate_content(prompt)
                # SQL query nikalna
                sql_query = response.text.replace('```sql', '').replace('```', '').strip()
                
                # Database se data nikalna
                conn = sqlite3.connect('data.db')
                result = pd.read_sql_query(sql_query, conn)
                
                st.subheader("AI Ka Jawab:")
                st.dataframe(result)
            except Exception as e:
                st.error(f"Error: AI query nahi bana paya. Technical details: {e}")

# Data preview hamesha dikhao
with st.expander("Data Preview"):
    if uploaded_file and cols:
        st.write(preview)
