import streamlit as st
import pandas as pd
import sqlite3
import google.generativeai as genai
import re
import plotly.express as px
import numpy as np

# 1. UI Setup
st.set_page_config(page_title="Bishape AI Pro Analytics", layout="wide", page_icon="📈")
st.title("🛡️ Bishape Enterprise Command Center")

# 2. AI Setup
API_KEY = "AIzaSyDyrJrSLXRyjG_Mp9n6W5DC_UidvGRMO50"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-flash-latest')

# 3. Session State Initialization (Yaaddasht setup)
if "messages" not in st.session_state:
    st.session_state.messages = []

@st.cache_data
def load_and_clean(file):
    df = pd.read_excel(file) if file.name.endswith('.xlsx') else pd.read_csv(file)
    df.columns = [re.sub(r'[^a-zA-Z0-9]', '_', c) for c in df.columns]
    df = df.fillna(0)
    for col in df.columns:
        if 'date' in col.lower():
            df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime('%Y-%m-%d')
    conn = sqlite3.connect('bishape_final.db', check_same_thread=False)
    df.to_sql('mytable', conn, if_exists='replace', index=False)
    return df

# --- SIDEBAR & DATA LOADING ---
with st.sidebar:
    st.header("Settings")
    uploaded_file = st.file_uploader("Upload Data", type=['xlsx', 'csv'])
    if st.button("Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

if uploaded_file:
    df = load_and_clean(uploaded_file)
    cols = df.columns.tolist()

    # Column Mapping for Logistics/Packing Slips
    with st.sidebar.expander("🛠️ Column Mapping", expanded=True):
        date_col = st.selectbox("Date Column", cols)
        sales_col = st.selectbox("Sales/Value Column", cols)
        customer_col = st.selectbox("Customer Name", cols)

    # Metrics Display
    st.subheader("📌 Live Business Metrics")
    m1, m2 = st.columns(2)
    m1.metric("Total Rows", len(df))
    # Correcting the Total Sales calculation
    actual_sales = pd.to_numeric(df[sales_col], errors='coerce').sum()
    m2.metric("Total Business Value", f"₹{actual_sales:,.0f}")

    # --- ADVANCE CHAT INTERFACE ---
    # Purane messages dikhana
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if "df" in message:
                st.dataframe(message["df"])
            else:
                st.markdown(message["content"])

    # Naya Sawal (Chat Input)
    if prompt_input := st.chat_input("Apna sawal yahan likhein..."):
        # User ka sawal screen par dikhao
        st.session_state.messages.append({"role": "user", "content": prompt_input})
        with st.chat_message("user"):
            st.markdown(prompt_input)

        # AI ka response generate karo
        with st.chat_message("assistant"):
            with st.spinner("AI dimaag laga raha hai..."):
                ai_prompt = f"""
                SQLite expert. Table 'mytable'.
                Mapping: Date="{date_col}", Sales="{sales_col}", Customer="{customer_col}".
                Columns: {cols}
                User query: {prompt_input}
                Return ONLY raw SQL.
                """
                try:
                    response = model.generate_content(ai_prompt)
                    sql = re.sub(r'^(sqlite|sql|ite|markdown)\s*', '', response.text.strip().replace('```sql', '').replace('```', ''), flags=re.IGNORECASE)
                    
                    conn = sqlite3.connect('bishape_final.db')
                    res_df = pd.read_sql_query(sql, conn)
                    
                    if not res_df.empty:
                        st.dataframe(res_df)
                        st.session_state.messages.append({"role": "assistant", "content": "Ye raha aapka result:", "df": res_df})
                    else:
                        st.write("Data nahi mila.")
                        st.session_state.messages.append({"role": "assistant", "content": "Koi record nahi mila."})
                except Exception as e:
                    st.error(f"Error: {e}")
                    st.session_state.messages.append({"role": "assistant", "content": "Bhai, SQL query mein gadbad ho gayi."})

else:
    st.info("Sidebar se file upload karein aur Analytics chalu karein!")
