import streamlit as st
import pandas as pd
import sqlite3
import google.generativeai as genai
import re
import plotly.express as px
import plotly.graph_objects as go

# 1. Advance Page Configuration
st.set_page_config(page_title="Bishape AI Command Center", layout="wide", page_icon="📈")

# Custom CSS for Dark/Premium Look
st.markdown("""
    <style>
    .stApp { background: #0e1117; color: white; }
    .metric-card { background: #1e2130; padding: 20px; border-radius: 15px; border-left: 5px solid #00f2fe; }
    .insight-box { background: #262730; padding: 15px; border-radius: 10px; border: 1px solid #4a4a4a; }
    </style>
    """, unsafe_allow_html=True)

# 2. AI Setup
API_KEY = "AIzaSyDyrJrSLXRyjG_Mp9n6W5DC_UidvGRMO50"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-flash-latest')

# 3. Sidebar with Professional Branding
with st.sidebar:
    st.header("🚀 Bishape AI Pro")
    uploaded_file = st.file_uploader("Upload your Master Excel/CSV", type=['xlsx', 'csv'])
    st.divider()
    if uploaded_file:
        st.success("Data Connection Active!")
    else:
        st.warning("Upload Data to Activate AI")

@st.cache_data
def load_and_clean_data(file):
    df = pd.read_excel(file) if file.name.endswith('.xlsx') else pd.read_csv(file)
    df.columns = [re.sub(r'[^a-zA-Z0-9]', '_', c) for c in df.columns]
    
    # Auto-convert dates
    for col in df.columns:
        if 'date' in col.lower():
            df[col] = pd.to_datetime(df[col], errors='coerce').dt.strftime('%Y-%m-%d')
            
    conn = sqlite3.connect('bishape_pro.db', check_same_thread=False)
    df.to_sql('mytable', conn, if_exists='replace', index=False)
    return df

if uploaded_file:
    df = load_and_clean_data(uploaded_file)
    cols = df.columns.tolist()
    num_cols = df.select_dtypes(include=['number']).columns.tolist()

    # --- SECTION 1: AUTO-PILOT INSIGHTS ---
    st.title("🛡️ Enterprise Data Intelligence")
    
    with st.expander("🤖 AI Auto-Executive Summary", expanded=True):
        if st.button("Generate Smart Insights"):
            summary_stats = df.describe().to_string()
            insight_prompt = f"Analyze this data summary and tell me 3 critical business insights in points: {summary_stats}"
            st.info(model.generate_content(insight_prompt).text)

    # --- SECTION 2: SMART METRICS GRID ---
    st.subheader("📊 Live Business Pulse")
    m1, m2, m3, m4 = st.columns(4)
    with m1: st.metric("Database Size", f"{len(df):,}")
    with m2: 
        val = df[num_cols[0]].sum() if num_cols else 0
        st.metric("Gross Value", f"₹{val:,.0f}")
    with m3:
        avg = df[num_cols[0]].mean() if num_cols else 0
        st.metric("Efficiency Avg", f"{avg:,.2f}")
    with m4:
        unique = len(df.iloc[:, 0].unique())
        st.metric("Unique Entities", unique)

    # --- SECTION 3: ADVANCE TABS ---
    tab1, tab2, tab3, tab4 = st.tabs(["🔥 AI Data Talk", "📈 Advanced Visualization", "🧬 Data Audit", "📋 Export Center"])

    with tab1:
        st.subheader("Chat with your Business Database")
        query = st.text_input("Type complex questions (e.g., 'Compare ASM performance for last 6 months')")
        if query:
            prompt = f"SQL Expert. Table: 'mytable', Columns: {cols}. User: {query}. ONLY SQL Output."
            try:
                response = model.generate_content(prompt)
                sql = re.sub(r'^(sqlite|sql|ite)\s*', '', response.text.replace('```sql', '').replace('```', '').strip(), flags=re.IGNORECASE)
                conn = sqlite3.connect('bishape_pro.db')
                result = pd.read_sql_query(sql, conn)
                
                col_left, col_right = st.columns([2, 1])
                with col_left:
                    st.dataframe(result, use_container_width=True)
                with col_right:
                    st.write("📈 AI Quick Analysis")
                    st.bar_chart(result.iloc[:, :2].set_index(result.columns[0]))
            except Exception as e:
                st.error("Complex Query detected. Please refine.")

    with tab2:
        st.subheader("Deep-Dive Graphics")
        c_col1, c_col2 = st.columns(2)
        with c_col1:
            x_ax = st.selectbox("Select X Axis", cols)
            y_ax = st.selectbox("Select Y Axis", num_cols)
            fig1 = px.scatter(df, x=x_ax, y=y_ax, color=cols[0] if cols else None, size=y_ax, hover_name=cols[1] if len(cols)>1 else None, template="plotly_dark")
            st.plotly_chart(fig1, use_container_width=True)
        with c_col2:
            fig2 = px.pie(df, names=cols[0], values=num_cols[0] if num_cols else None, hole=0.4, template="plotly_dark")
            st.plotly_chart(fig2, use_container_width=True)

    with tab3:
        st.subheader("Database Quality Audit")
        st.write(df.isnull().sum().rename("Missing Values"))
        if st.button("Fix Missing Values (AI Auto-Fill)"):
            st.warning("Processing... AI is estimating missing values.")

    with tab4:
        st.subheader("Download Tailored Reports")
        st.download_button("📥 Download Full Cleaned Data", df.to_csv(index=False), "cleaned_data.csv")
        st.info("Coming Soon: One-click PDF Presentation generation.")

else:
    st.title("Bishape AI Analytics 🚀")
    st.header("Please upload your data to start the engine.")
    st.video("https://www.youtube.com/watch?v=dQw4w9WgXcQ") # Bas mazaak ke liye!
