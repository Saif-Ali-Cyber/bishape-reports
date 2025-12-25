import streamlit as st
import pandas as pd
import sqlite3
import google.generativeai as genai
import re

# 1. Simple Setup
st.set_page_config(page_title="Bishape AI Pro", layout="wide")
st.title("🚀 Bishape Fast AI Reporter")

# AI Setup
API_KEY = "AIzaSyDyrJrSLXRyjG_Mp9n6W5DC_UidvGRMO50"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-flash-latest')

# 2. Fast Data Loader
@st.cache_data
def fast_load(file):
    df = pd.read_excel(file) if file.name.endswith('.xlsx') else pd.read_csv(file)
    # Column names clean karo
    df.columns = [re.sub(r'[^a-zA-Z0-9]', '_', c) for c in df.columns]
    df = df.fillna(0)
    # Date format fix
    for col in df.columns:
        if 'date' in col.lower():
            df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime('%Y-%m-%d')
    conn = sqlite3.connect('bishape.db', check_same_thread=False)
    df.to_sql('mytable', conn, if_exists='replace', index=False)
    return df

uploaded_file = st.sidebar.file_uploader("Upload File", type=['xlsx', 'csv'])

if uploaded_file:
    df = fast_load(uploaded_file)
    cols = df.columns.tolist()
    
    # 3. Simple KPI (Jo tune pucha tha - Total Sales fix)
    st.subheader("📌 Quick Summary")
    num_cols = df.select_dtypes(include=['number']).columns.tolist()
    c1, c2 = st.columns(2)
    c1.metric("Total Rows", len(df))
    if num_cols:
        # Pehla numeric column ko Sales maan kar sum dikhana
        st.session_state.sales_col = num_cols[0] 
        c2.metric(f"Total {num_cols[0]}", f"₹{df[num_cols[0]].sum():,.0f}")

    # 4. Direct Question Box (No Chat History to avoid hanging)
    st.divider()
    query = st.text_input("Apna sawal yahan likhein (e.g. Sales in Oct-Nov but not Dec):")

    if query:
        with st.spinner('AI dimaag laga raha hai...'):
            # Prompt ko itna strong kiya hai ki AI galti na kare
            prompt = f"""
            Act as a SQLite Expert. Table name: 'mytable'.
            Columns: {cols}
            
            Task: Provide ONLY the SQL query for this: {query}
            Rules:
            - Use STRFTIME('%m', Date_Column) to find months (10 for Oct, 11 for Nov, 12 for Dec).
            - For 'Oct/Nov but not Dec', use 'WHERE month IN (10,11) AND customer NOT IN (SELECT customer FROM mytable WHERE month=12)'.
            - Use double quotes for all column names.
            - NO markdown, NO 'sql' text. Start with SELECT.
            """
            try:
                response = model.generate_content(prompt)
                # Clean query
                sql = response.text.strip().replace('```sql', '').replace('```', '')
                sql = re.sub(r'^(sqlite|sql|ite|markdown)\s*', '', sql, flags=re.IGNORECASE)
                
                conn = sqlite3.connect('bishape.db')
                result = pd.read_sql_query(sql, conn)
                
                if not result.empty:
                    st.success(f"Bhai, {len(result)} records mile hain!")
                    st.dataframe(result, use_container_width=True)
                    st.download_button("Download Report", result.to_csv(index=False), "bishape_report.csv")
                else:
                    st.warning("Query toh bani par data nahi mila. Ek baar date format check karein.")
                    st.code(sql) # Debug ke liye query dikhao
            except Exception as e:
                st.error(f"Error: AI confuse ho gaya. Detail: {e}")

else:
    st.info("Sidebar se file upload karo bhai!")
