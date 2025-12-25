import streamlit as st
import pandas as pd
import sqlite3
import google.generativeai as genai
import re

# 1. Page Config
st.set_page_config(page_title="Bishape AI Pro", layout="wide")
st.title("🤖 Bishape Smart AI Reporter")

# 2. AI Setup (Smart Detection)
# Pehle Secrets se try karega, fir hardcoded key se
if "GEMINI_API_KEY" in st.secrets:
    API_KEY = st.secrets["GEMINI_API_KEY"]
else:
    API_KEY = "AIzaSyDyrJrSLXRyjG_Mp9n6W5DC_UidvGRMO50"

genai.configure(api_key=API_KEY)

# --- SMART MODEL PICKER ---
@st.cache_resource
def get_working_model():
    try:
        # Sabse pehle 'gemini-1.5-flash' try karo
        m = genai.GenerativeModel('gemini-1.5-flash')
        m.generate_content("Hi") # Test call
        return m
    except:
        try:
            # Agar fail ho, toh list check karo kaunsa available hai
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    return genai.GenerativeModel(m.name)
        except Exception as e:
            st.error(f"API Key issue: {e}")
            return None

model = get_working_model()

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

if uploaded_file and model:
    cols, total_rows, preview = load_data_to_sqlite(uploaded_file)
    if cols:
        st.success(f"Taiyaar! {total_rows} rows mil gayi hain.")
    
    # 4. Chat Interface
    st.divider()
    query = st.text_input("Data ke baare mein sawal pucho (e.g. Total rows kitni hain?)")

    if query:
        with st.spinner('AI dimaag laga raha hai...'):
            prompt = f"Table: 'mytable'. Columns: {cols}. User Query: {query}. Output ONLY the SQL query."
            try:
                response = model.generate_content(prompt)
                sql_query = response.text.replace('```sql', '').replace('```', '').strip()
                conn = sqlite3.connect('data.db')
                result = pd.read_sql_query(sql_query, conn)
                st.subheader("AI Ka Jawab:")
                st.dataframe(result)
            except Exception as e:
                st.error(f"Query Error: {e}")

elif not model:
    st.warning("Bhai, API Key kaam nahi kar rahi ya model nahi mil raha.")

with st.expander("Data Preview"):
    if uploaded_file and 'cols' in locals() and cols:
        st.write(preview)
