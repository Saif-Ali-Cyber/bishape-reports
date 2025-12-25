import streamlit as st
import pandas as pd
import sqlite3
import google.generativeai as genai

# 1. AI Setup (Dimaag)
st.set_page_config(page_title="Bishape AI Reports", layout="wide")
st.title("🤖 Bishape AI Data Assistant")

# Yahan apni API Key daalna (Ya hum Streamlit settings mein baad mein daalenge)
api_key = st.sidebar.text_input("Gemini API Key Yahan Dalein:", type="password")

if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-pro')

# 2. File Upload (100MB Friendly)
uploaded_file = st.file_uploader("Apni Excel file upload karein", type=['xlsx', 'csv'])

@st.cache_data
def process_data(file):
    df = pd.read_excel(file) if file.name.endswith('.xlsx') else pd.read_csv(file)
    # Database mein save karna taaki fast chale
    conn = sqlite3.connect('data.db')
    df.to_sql('mytable', conn, if_exists='replace', index=False)
    return df, df.columns.tolist()

if uploaded_file:
    with st.spinner('Bhai wait kar, file badi hai...'):
        df, columns = process_data(uploaded_file)
        st.success(f"Loaded! Total rows: {len(df)}")
        st.write("Columns found:", columns)

    # 3. AI Chat Box
    st.divider()
    query = st.text_input("Data ke baare mein sawal puchein (e.g. Sabse zyada sales kis city mein hui?)")
    
    if query and api_key:
        # AI ko samjhana ki data kya hai
        prompt = f"Data columns are: {columns}. Summary: {df.describe().to_string()}. User asks: {query}"
        response = model.generate_content(prompt)
        st.subheader("AI Ka Jawab:")
        st.write(response.text)
    elif query and not api_key:
        st.warning("Bhai, pehle API Key toh dalo!")
