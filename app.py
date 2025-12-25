import streamlit as st
import pandas as pd
import sqlite3
import google.generativeai as genai
import re

# 1. Page Config
st.set_page_config(page_title="Bishape AI Pro", layout="wide")
st.title("🤖 Bishape Smart AI Reporter")

# 2. AI Setup (Smart Auto-Detection)
API_KEY = "AIzaSyDyrJrSLXRyjG_Mp9n6W5DC_UidvGRMO50"
genai.configure(api_key=API_KEY)

# --- SMART MODEL PICKER ---
@st.cache_resource
def get_working_model():
    try:
        # Sabse pehle hum check karenge ki aapke paas kaun-kaun se models hain
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        if not available_models:
            st.error("Bhai, aapki API Key mein koi model nahi mil raha!")
            return None
        
        # Sabse naya model uthane ki koshish (Flash mil jaye toh best hai)
        for model_name in ['models/gemini-1.5-flash', 'models/gemini-pro', 'models/gemini-1.5-pro']:
            if model_name in available_models:
                return genai.GenerativeModel(model_name)
        
        # Agar koi bhi nahi mila toh jo list mein pehla hai wo utha lo
        return genai.GenerativeModel(available_models[0])
    except Exception as e:
        st.error(f"API Key issue: {e}")
        return None

model = get_working_model()

# 3. Heavy File Processing (100MB Friendly)
uploaded_file = st.file_uploader("Apni Excel/CSV file dalo", type=['xlsx', 'csv'])

@st.cache_data
def load_data_to_sqlite(file):
    try:
        # Excel ya CSV read karna
        df = pd.read_excel(file) if file.name.endswith('.xlsx') else pd.read_csv(file)
        
        # Database se connect karna
        conn = sqlite3.connect('data.db', check_same_thread=False)
        
        # Columns clean karna (Special characters hatao taaki SQL na toote)
        df.columns = [re.sub(r'[^a-zA-Z0-9]', '_', c) for c in df.columns]
        
        df.to_sql('mytable', conn, if_exists='replace', index=False)
        return df.columns.tolist(), len(df), df.head(5)
    except Exception as e:
        return None, 0, str(e)

if uploaded_file and model:
    cols, total_rows, preview = load_data_to_sqlite(uploaded_file)
    if cols:
        st.success(f"Taiyaar! {total_rows} rows load ho gayi hain.")
        st.info(f"AI Model in use: {model.model_name}")

    # 4. Chat Interface
    st.divider()
    query = st.text_input("Data ke baare mein sawal pucho (e.g. Total rows kitni hain?)")

    if query:
        with st.spinner('AI dimaag laga raha hai...'):
            prompt = f"""
            You are a SQL expert. 
            Table: 'mytable'
            Columns: {cols}
            User Question: {query}
            
            Instruction: Provide ONLY the SQL query. No explanation.
            Example: SELECT COUNT(*) FROM mytable
            """
            try:
                response = model.generate_content(prompt)
                sql_query = response.text.replace('```sql', '').replace('```', '').strip()
                
                # Database query chalana
                conn = sqlite3.connect('data.db')
                result = pd.read_sql_query(sql_query, conn)
                
                st.subheader("AI Ka Jawab:")
                st.dataframe(result)
            except Exception as e:
                st.error(f"Error: {e}")

elif not model:
    st.warning("API Key load ho rahi hai, ya fir key mein koi dikat hai.")

# Preview Table
with st.expander("Data Preview"):
    if uploaded_file and 'cols' in locals() and cols:
        st.write(preview)
