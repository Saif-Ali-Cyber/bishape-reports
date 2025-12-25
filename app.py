import streamlit as st
import pandas as pd
import sqlite3
import google.generativeai as genai
import re
import plotly.express as px

# 1. Page Config
st.set_page_config(page_title="Bishape AI Analytics", layout="wide", page_icon="🚀")

# 2. AI Setup
API_KEY = "AIzaSyDyrJrSLXRyjG_Mp9n6W5DC_UidvGRMO50"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-flash-latest')

# 3. Sidebar
with st.sidebar:
    st.title("Settings")
    uploaded_file = st.file_uploader("Upload Data (Excel/CSV)", type=['xlsx', 'csv'])

@st.cache_data
def process_data(file):
    try:
        df = pd.read_excel(file) if file.name.endswith('.xlsx') else pd.read_csv(file)
        # Column names clean karna
        df.columns = [re.sub(r'[^a-zA-Z0-9]', '_', c) for c in df.columns]
        
        # 💡 DATE FIX: Date columns ko SQLite format (YYYY-MM-DD) mein badalna
        for col in df.columns:
            if 'date' in col.lower():
                df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime('%Y-%m-%d')
        
        conn = sqlite3.connect('data.db', check_same_thread=False)
        df.to_sql('mytable', conn, if_exists='replace', index=False)
        return df
    except Exception as e:
        st.error(f"File Processing Error: {e}")
        return None

if uploaded_file:
    df = process_data(uploaded_file)
    if df is not None:
        cols = df.columns.tolist()

        # KPI Cards
        st.subheader("📌 Quick Metrics")
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Records", f"{len(df):,}")
        num_cols = df.select_dtypes(include=['number']).columns
        if len(num_cols) > 0:
            c2.metric("Primary Metric Sum", f"{df[num_cols[0]].sum():,.0f}")
            c3.metric("Max Value", f"{df[num_cols[0]].max():,.0f}")

        # Tabs
        tab1, tab2 = st.tabs(["💬 AI Manager", "📊 Analytics"])

        with tab1:
            query = st.text_input("Ask anything about your data:")
            if query:
                with st.spinner('AI is generating report...'):
                    # Prompt ko aur strict kiya hai
                    prompt = f"""You are a SQLite expert. Table: 'mytable', Columns: {cols}.
                    User Question: {query}. 
                    Output ONLY the SQL query. 
                    - NEVER wrap the whole query in quotes.
                    - Start directly with SELECT.
                    - Use STRFTIME('%Y-%m', "DateColumn") for month-year analysis.
                    """
                    
                    try:
                        response = model.generate_content(prompt)
                        # 🛠️ ADVANCED CLEANING: Quotes aur markdown hatana
                        raw_sql = response.text.strip()
                        sql_query = re.sub(r'^[ \t]*["\'`]|["\'`][ \t]*$', '', raw_sql) # Shuru aur aakhir ke quotes hatana
                        sql_query = sql_query.replace('```sql', '').replace('```', '').strip()
                        
                        conn = sqlite3.connect('data.db')
                        result = pd.read_sql_query(sql_query, conn)
                        
                        st.dataframe(result, use_container_width=True)
                        
                        # AI Explanation
                        st.info("💡 Insight")
                        st.write(model.generate_content(f"Explain this result in 1 simple sentence: {result.head(3).to_string()}").text)
                        
                    except Exception as e:
                        st.error(f"Query Error: {e}")
                        st.code(sql_query if 'sql_query' in locals() else "No query generated")

        with tab2:
            st.subheader("Dynamic Charts")
            if len(num_cols) > 0:
                sel_col = st.selectbox("Select Column for Analysis", num_cols)
                fig = px.box(df, y=sel_col, title=f"Analysis of {sel_col}")
                st.plotly_chart(fig, use_container_width=True)

else:
    st.info("Bhai, sidebar se file upload karo pehle!")
