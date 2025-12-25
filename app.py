import streamlit as st
import pandas as pd
import sqlite3
import google.generativeai as genai
import re
import plotly.express as px

# 1. Page Config (Khatarnak Look ke liye)
st.set_page_config(page_title="Bishape AI Analytics", layout="wide", page_icon="🚀")
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# 2. AI Setup
API_KEY = "AIzaSyDyrJrSLXRyjG_Mp9n6W5DC_UidvGRMO50"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-flash-latest')

# 3. Sidebar - Stats aur Upload
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2103/2103633.png", width=100)
    st.title("Settings")
    uploaded_file = st.file_uploader("Data Upload Karein", type=['xlsx', 'csv'])
    st.divider()
    st.info("Bhai, 100MB file bhi makkhan chalegi!")

@st.cache_data
def process_data(file):
    df = pd.read_excel(file) if file.name.endswith('.xlsx') else pd.read_csv(file)
    df.columns = [re.sub(r'[^a-zA-Z0-9]', '_', c) for c in df.columns]
    conn = sqlite3.connect('data.db', check_same_thread=False)
    df.to_sql('mytable', conn, if_exists='replace', index=False)
    return df

if uploaded_file:
    df = process_data(uploaded_file)
    cols = df.columns.tolist()

    # --- TOP KPI CARDS ---
    st.subheader("📌 Key Metrics")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Rows", f"{len(df):,}")
    col2.metric("Total Columns", len(cols))
    
    # Automaticaly numeric column dhund kar uska sum dikhana
    num_cols = df.select_dtypes(include=['number']).columns
    if len(num_cols) > 0:
        col3.metric("Total Value (Sum)", f"{df[num_cols[0]].sum():,.0f}")
        col4.metric("Avg Value", f"{df[num_cols[0]].mean():,.2f}")

    # --- TABS SYSTEM ---
    tab1, tab2, tab3 = st.tabs(["💬 AI Chat & Reports", "📊 Visual Analytics", "📁 Raw Data"])

    with tab1:
        st.subheader("Apne AI Manager se baat karein")
        query = st.text_input("Sawal pucho: (e.g. Division wise sales ka bar chart dikhao)")
        
        if query:
            with st.spinner('AI Report taiyaar kar raha hai...'):
                prompt = f"""You are a SQLite expert. Table: 'mytable', Columns: {cols}.
                User Query: {query}. Output ONLY the SQL query in double quotes for columns."""
                
                try:
                    response = model.generate_content(prompt)
                    sql_query = re.sub(r'^(sqlite|sql|ite)\s*', '', response.text.replace('```sql', '').replace('```', '').strip(), flags=re.IGNORECASE)
                    
                    conn = sqlite3.connect('data.db')
                    result = pd.read_sql_query(sql_query, conn)
                    
                    # Layout for Results
                    res_col, ins_col = st.columns([2, 1])
                    with res_col:
                        st.dataframe(result, use_container_width=True)
                        st.download_button("Download Report (CSV)", result.to_csv(index=False), "report.csv", "text/csv")
                    
                    with ins_col:
                        # AI se insights lena (Insan jaisa explanation)
                        st.info("💡 AI Insights")
                        insight_prompt = f"Data results: {result.head(5).to_string()}. Briefly explain what this means in 2-3 sentences."
                        st.write(model.generate_content(insight_prompt).text)
                except Exception as e:
                    st.error(f"Error: AI thoda confuse hai. {e}")

    with tab2:
        st.subheader("Automatic Charts")
        if len(num_cols) > 0:
            chart_col = st.selectbox("Kaunse column ka graph dekhna hai?", num_cols)
            fig = px.histogram(df, x=chart_col, title=f"Distribution of {chart_col}", template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Graph banane ke liye koi Number wala column nahi mila.")

    with tab3:
        st.subheader("Full Data Preview")
        st.dataframe(df.head(100), use_container_width=True)

else:
    st.warning("Waiting for data... Pehle sidebar se file upload karo bhai!")
