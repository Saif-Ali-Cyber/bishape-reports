import streamlit as st
import google.generativeai as genai

st.title("Bishape Debugger 🛠️")

# Teri API Key
API_KEY = "AIzaSyDyrJrSLXRyjG_Mp9n6W5DC_UidvGRMO50"
genai.configure(api_key=API_KEY)

st.write("Checking available models for your key...")

try:
    # Ye line tere account ke saare available models dikhayegi
    available_models = [m.name for m in genai.list_models()]
    st.write("Models found:", available_models)
    
    # Sabse basic model try karte hain
    test_model = genai.GenerativeModel('gemini-1.5-flash')
    response = test_model.generate_content("Bhai, kya tum zinda ho?")
    
    st.success("AI ka Jawab: " + response.text)

except Exception as e:
    st.error(f"Abhi bhi error hai: {e}")
