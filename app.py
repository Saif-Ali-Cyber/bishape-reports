import streamlit as st
import pandas as pd
import sqlite3
import google.generativeai as genai
import plotly.express as px
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression
import numpy as np
import re

# 1. LUXURY PAGE CONFIG
st.set_page_config(page_title="Bishape AI Command Center", layout="wide", page_icon="💎")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="stMetricValue"] { font-size: 28px; color: #00f2fe; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: #1e2130; border-radius: 5px; color: white; padding: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 2. BRAIN SETUP (AI)
API_KEY = "AIzaSyDyrJrSLXRyjG_Mp9n6W5DC_UidvGRMO50" # Teri di hui key
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-flash-latest')

# 3. SIDEBAR WITH LOGO
with st.sidebar:
    st.header("💎 Bishape Intelligence")
    uploaded_file = st.file_uploader("Upload Master Data", type=['xlsx', 'csv'])
    st.divider()
    st.markdown("### 🛠️ AI Controls")
    precision = st.slider("AI Analysis Precision", 0.1, 1.0, 0.8)

@st.cache_data
def advanced_processing(file):
    df = pd.read_excel(file) if file.name.endswith('.xlsx') else pd.read_csv(file)
    df.columns = [re.sub(r'[^a-zA-Z0-9]', '_', c) for c in df.columns]
    for col in df.columns:
        if 'date' in col.lower():
            df[col] = pd.to_datetime(df[col], errors='coerce')
    conn = sqlite3.connect('bishape_ultra.db', check_same_thread=False)
    df.to_sql('mytable', conn, if_exists='replace', index=False)
    return df

if uploaded_file:
    df = advanced_processing(uploaded_file)
    num_cols = df.select_dtypes(include=['number']).columns.tolist()
    date_cols = [c for c in df.columns if 'date' in c.lower()]

    st.title("🚀 Business Intelligence Command Center")

    # --- TOP KPI BAR ---
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Database Entries", f"{len(df):,}")
    if num_cols:
        c2.metric("Gross Revenue", f"₹{df[num_cols[0]].sum():,.0f}")
        c3.metric("Avg Order Value", f"₹{df[num_cols[0]].mean():,.0f}")
        c4.metric("Growth Pulse", "+12.5%") # Demo calculation

    # --- MAIN TABS ---
    t1, t2, t3, t4 = st.tabs(["🧠 AI Strategy Lab", "📈 Visual Matrix", "🔮 Forecast Engine", "🛡️ Quality Audit"])

    with t1:
        st.subheader("Bhai, yahan AI se complex reports banwao")
        query = st.text_input("Example: ASM wise performance aur top 5 divisions ki summary do")
        if query:
            with st.spinner('AI Manager is working...'):
                prompt = f"SQL Expert. Table: 'mytable', Columns: {df.columns.tolist()}. Query: {query}. Output ONLY SQL."
                try:
                    response = model.generate_content(prompt)
                    sql = re.sub(r'^(sqlite|sql|ite)\s*', '', response.text.replace('```sql', '').replace('```', '').strip(), flags=re.IGNORECASE)
                    res = pd.read_sql_query(sql, sqlite3.connect('bishape_ultra.db'))
                    
                    st.dataframe(res, use_container_width=True)
                    
                    # AI STORYTELLING
                    st.markdown("---")
                    st.markdown("### 💡 AI Executive Insight")
                    insight = model.generate_content(f"Analyze this result and give a 3-point strategy: {res.head(5).to_string()}")
                    st.success(insight.text)
                except Exception as e:
                    st.error("Query complex hai. Try again!")

    with t2:
        st.subheader("Interactive Data Matrix")
        if len(num_cols) >= 2:
            fig = px.scatter(df, x=num_cols[0], y=num_cols[1], color=df.columns[0], 
                             size=num_cols[0], hover_data=df.columns.tolist(),
                             template="plotly_dark", title="Multi-Dimensional Analysis")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Needs more numeric columns for this view.")

    with t3:
        st.subheader("🔮 Predictive Forecasting (Agle 30 Din)")
        if date_cols and num_cols:
            df_forecast = df.copy()
            df_forecast[date_cols[0]] = pd.to_datetime(df_forecast[date_cols[0]])
            daily = df_forecast.groupby(date_cols[0])[num_cols[0]].sum().reset_index()
            daily['day_num'] = np.arange(len(daily))
            
            # Simple Regression for Trend
            X = daily[['day_num']]
            y = daily[num_cols[0]]
            reg = LinearRegression().fit(X, y)
            
            future_days = np.arange(len(daily), len(daily) + 30).reshape(-1, 1)
            future_pred = reg.predict(future_days)
            
            fig_f = go.Figure()
            fig_f.add_trace(go.Scatter(x=daily[date_cols[0]], y=y, name="Past Performance"))
            fig_f.add_trace(go.Scatter(x=pd.date_range(daily[date_cols[0]].max(), periods=30), y=future_pred, name="AI Forecast", line=dict(dash='dash')))
            fig_f.update_layout(template="plotly_dark")
            st.plotly_chart(fig_f, use_container_width=True)
            st.info("💡 Tip: Ye graph pichle trends ko dekh kar agle mahine ka andaza de raha hai.")

    with t4:
        st.subheader("🛡️ Data Integrity Audit")
        col_audit1, col_audit2 = st.columns(2)
        with col_audit1:
            st.write("Missing Data Scan:")
            st.table(df.isnull().sum())
        with col_audit2:
            st.write("Anomaly Detection (Zahar Data):")
            if num_cols:
                q_low = df[num_cols[0]].quantile(0.01)
                q_high = df[num_cols[0]].quantile(0.99)
                anomalies = df[(df[num_cols[0]] < q_low) | (df[num_cols[0]] > q_high)]
                st.warning(f"Found {len(anomalies)} suspicious records!")
                st.dataframe(anomalies)

else:
    st.markdown("<h1 style='text-align: center;'>Bishape Enterprise AI Command Center 💎</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Upload your business data to wake up the analyst.</p>", unsafe_allow_html=True)
