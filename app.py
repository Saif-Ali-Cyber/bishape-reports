import streamlit as st
import pandas as pd
import sqlite3
import google.generativeai as genai

# 1. Page Config & AI Setup
st.set_page_config(page_title="Bishape AI Reports", layout="wide")
st.title("🤖 Bishape AI Data Assistant (100MB Pro)")

# Secrets se API Key uthana
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash') # 1.5-flash fast hai aur badi file handle karta hai
except:
    st.error("Bhai, Streamlit Secrets mein API Key nahi mili!")
    st.stop()

# 2. Heavy File Upload & Processing
uploaded_file = st.file_uploader("Apni Excel ya CSV file upload karein", type=['xlsx', 'csv'])

@st.cache_data
def process_data(file):
    # Memory bachane ke liye chunking ya fast processing
    if file.name.endswith('.csv'):
        df = pd.read_csv(file)
    else:
        df = pd.read_excel(file)
    
    # SQLite Database banana (Badi files ke liye zaruri)
    conn = sqlite3.connect('data.db')
    df.to_sql('mytable', conn, if_exists='replace', index=False)
    
    # AI ko sirf columns aur thoda sa data dikhayenge taaki wo confuse na ho
    summary = df.head(10).to_string() 
    cols = df.columns.tolist()
    return df, cols, summary

if uploaded_file:
    with st.spinner('100MB file hai bhai, thoda sabr rakh...'):
        df, columns, data_summary = process_data(uploaded_file)
        st.success(f"File loaded! {len(df)} rows mil gayi hain.")

    # 3. AI Chat Interface
    st.divider()
    st.subheader("💬 Apne Data Se Baat Karein")
    query = st.text_input("Sawal pucho: (e.g. Total sales kitni hui? Ya top 5 customers kaun hain?)")

    if query:
        with st.spinner('AI data check kar raha hai...'):
            # AI ko "Context" dena ki data kaisa hai
            prompt = f"""
            You are a data expert. Here is the structure of the user's data:
            Columns: {columns}
            Sample Data: {data_summary}
            Total Rows: {len(df)}
            
            User Question: {query}
            
            Answer strictly based on this data. If you need to perform calculations, explain the logic.
            """
            response = model.generate_content(prompt)
            st.markdown(f"**AI Ka Jawab:**\n\n{response.text}")

# 4. Data Preview
with st.expander("Data Preview Dekhein"):
    st.dataframe(df.head(100))
