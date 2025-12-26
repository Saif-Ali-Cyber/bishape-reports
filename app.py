import streamlit as st
import pandas as pd
import sqlite3
import google.generativeai as genai
import re
import plotly.express as px

# 1. UI Setup
st.set_page_config(page_title="Bishape Pro Analytics", layout="wide")
st.title("🛡️ Bishape Smart Analytics")

# 2. API Setup
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"].strip())
    model = genai.GenerativeModel('gemini-flash-latest')
else:
    st.error("Bhai, Secrets mein API Key dalo!")
    st.stop()

# 3. Data Engine
@st.cache_data
def load_data(file):
    df = pd.read_excel(file) if file.name.endswith('.xlsx') else pd.read_csv(file)
    df.columns = [re.sub(r'[^a-zA-Z0-9]', '_', str(c)) for c in df.columns]
    df = df.fillna(0)
    conn = sqlite3.connect('bishape_final.db', check_same_thread=False)
    df.to_sql('mytable', conn, if_exists='replace', index=False)
    return df

uploaded_file = st.file_uploader("Upload File", type=['xlsx', 'csv'])

if uploaded_file:
    df = load_data(uploaded_file)
    cols = df.columns.tolist()

    # --- YE HAI ASLI SOLUTION: SIDEBAR MAPPING ---
    with st.sidebar:
        st.header("⚙️ Column Settings")
        st.write("AI ko batao kaunsa column kya hai:")
        sales_col = st.selectbox("Sales/Value Column", cols)
        date_col = st.selectbox("Date Column", cols)
        name_col = st.selectbox("Customer/Product Name Column", cols)

    # 4. Metrics (Ab ₹0 nahi aayega)
    st.subheader("📌 Business Summary")
    c1, c2 = st.columns(2)
    c1.metric("Total Records", f"{len(df):,}")
    
    # Selected column ka total nikalna
    total_sales = pd.to_numeric(df[sales_col], errors='coerce').sum()
    c2.metric(f"Total {sales_col}", f"₹{total_sales:,.0f}")

    # 5. AI Chat (With Mapping Knowledge)
    st.divider()
    query = st.text_input("Apna sawal pucho (e.g. Oct-Nov sales vs Dec):")

    if query:
        with st.spinner('AI analyzing...'):
            # AI ko ab pata hai ki Date aur Sales column kaunse hain
            prompt = f"""
            Expert SQLite. Table: 'mytable'.
            Mapping Info: 
            - Sales/Value is in "{sales_col}"
            - Dates are in "{date_col}"
            - Names/Products are in "{name_col}"
            
            Columns: {cols}
            User Question: {query}
            
            Rule: Return ONLY SQL. If searching for text like 'iq ball pen', use LIKE '%iq ball pen%'.
            """
            try:
                resp = model.generate_content(prompt)
                sql = resp.text.strip().replace('```sql', '').replace('```', '')
                sql = re.sub(r'^(sqlite|sql|ite)\s*', '', sql, flags=re.IGNORECASE)
                
                conn = sqlite3.connect('bishape_final.db')
                result = pd.read_sql_query(sql, conn)
                
                if not result.empty:
                    st.dataframe(result, use_container_width=True)
                else:
                    st.warning("Data nahi mila. Shayad spelling check karni pade.")
                    st.code(sql) # Debug ke liye query dikhao
            except Exception as e:
                st.error(f"Error: {e}")

else:
    st.info("Bhai, file upload karo pehle.")
