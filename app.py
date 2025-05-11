import streamlit as st

st.set_page_config(page_title="Miami Business Insights")
st.title("Miami Business Insights")

area = st.sidebar.text_input("Inserisci ZIP code o nome quartiere", "33101")
st.header(f"Analisi per: {area}")

st.write("⚙️ Caricamento dati in corso…")
