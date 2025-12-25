import streamlit as st
import pandas as pd
import sqlite3
import google.generativeai as genai
import re

# 1. Page Config
st.set_page_config(page_title="Bishape AI Pro", layout="wide")
st.title("🤖 Bishape Smart AI Reporter")

# 2. AI Setup (Teri di hui Key yahan set kar di hai)
API_KEY = "AIzaSyDyrJrSLXRyjG_Mp9n6W5DC_UidvGRMO50"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# 3. Heavy File Processing (100MB Friendly)
uploaded_file = st.file_uploader("Apni Excel ya CSV file yahan dalo (100MB tak allow hai)", type=['xlsx', 'csv'])

@st.cache_data
def load_data_to_sqlite(file):
    # Data load karo
    try:
        if file.name.endswith('.csv'):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)
        
        # SQLite Database banana (Memory manage karne ke liye)
        conn = sqlite3.connect('data.db', check_same_thread=False)
        # Column names ko clean karna (Spaces hatana)
        df.columns = [c.replace(' ', '_').replace('(', '').replace(')', '').replace('/', '_') for c in df.columns]
        df.to_sql('mytable', conn, if_exists='replace', index=False)
        return df.columns.tolist(), len(df), df.head(5)
    except Exception as e:
        return None, 0, str(e)

if uploaded_file:
    with st.spinner('Bhai wait kar, file badi hai, dimaag laga raha hoon...'):
        cols, total_rows, preview = load_data_to_sqlite(uploaded_file)
        
        if cols:
            st.success(f"Maza aa gaya! {total_rows} rows mil gayi hain.")
            st.write("Aapke Columns ye hain:", cols)
        else:
            st.error(f"Error: {preview}")

    # 4. Chat Interface
    st.divider()
    st.subheader("💬 Apne Data Se Sawal Puchein")
    query = st.text_input("Example: Sabse zyada sales kisne ki? Ya total count kya hai?")

    if query:
        with st.spinner('AI data check kar raha hai...'):
            # AI ko instruction dena
            prompt = f"""
            You are a SQL expert. We have a table 'mytable' with these columns: {cols}.
            The user wants to know: {query}
            Give me ONLY the SQL query that can answer this. 
            Do not provide any text explanation, only the query.
            Example: SELECT SUM(Sales) FROM mytable
            """
            try:
                # Step 1: AI se SQL likhwana
                response = model.generate_content(prompt)
                clean_sql = re.sub(r'```sql|```', '', response.text).strip()
                
                # Step 2: Database se result nikalna
                conn = sqlite3.connect('data.db')
                result = pd.read_sql_query(clean_sql, conn)
                
                # Step 3: Result dikhana
                st.subheader("AI Ka Jawab:")
                st.dataframe(result)
            except Exception as e:
                st.warning("AI sawal samajh nahi paya. Thoda simple karke pucho (jaise column ka naam use karo).")
                st.info(f"Koshish ki gayi query: {clean_sql if 'clean_sql' in locals() else 'None'}")

# 5. Preview Table
with st.expander("Data ka Preview Dekhein"):
    if uploaded_file and cols:
        st.write(preview)
