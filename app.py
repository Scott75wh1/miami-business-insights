import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# Static Geo Module
from data.geo import get_supported_states, get_cities_for_state, get_zips_for_city
# Analysis Modules
from data.census import fetch_demographics_by_zip
from data.trends import fetch_google_trends
from data.google_reviews import fetch_google_reviews
from data.yelp import fetch_yelp_competitors
# PDF Export
from utils.pdf_report import generate_pdf_report
# OpenAI
import openai

# Streamlit config
st.set_page_config(page_title="Business Insights USA", layout="wide")
st.title("Business Insights USA 🗺️")

# API Keys
CENSUS_API_KEY = st.secrets.get("CENSUS_API_KEY")
YELP_API_KEY = st.secrets.get("YELP_API_KEY")
GOOGLE_PLACES_KEY = st.secrets.get("GOOGLE_PLACES_KEY")
OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

# Session state for dashboard run
if 'run_dashboard' not in st.session_state:
    st.session_state.run_dashboard = False

def run_callback():
    st.session_state.run_dashboard = True

# Sidebar: Hierarchical selection
st.sidebar.header("1. Seleziona Area Geografica")
states = get_supported_states()
state = st.sidebar.selectbox("Stato:", states)
cities_df = get_cities_for_state(state)
city = st.sidebar.selectbox("Città:", cities_df['city_name'].tolist())
zips_df = get_zips_for_city(city)
zip_code = st.sidebar.selectbox("ZIP code:", zips_df['zip_code'].tolist())

st.sidebar.header("2. Settore & Fonti")
categories = ["Ristorazione", "Retail", "Servizi", "Personal Care", "Altro"]
category = st.sidebar.selectbox("Categoria di attività:", categories)
custom_term = st.sidebar.text_input("Query personalizzata (opzionale):")
search_term = custom_term.strip() if custom_term.strip() else category
enable_demo = st.sidebar.checkbox("Dati Demografici", True)
enable_trends = st.sidebar.checkbox("Google Trends", True)
enable_google = st.sidebar.checkbox("Google Reviews", True)
enable_yelp = st.sidebar.checkbox("Yelp", True)

st.sidebar.button("Genera Dashboard", on_click=run_callback)
if not st.session_state.run_dashboard:
    st.info("Configura area, settore e fonti nella sidebar, poi clicca 'Genera Dashboard'.")
    st.stop()

# Fetch & display results
tabs = st.tabs(["Demografici", "Trends", "Competitor", "Mappa", "Analisi AI"])

# Tab 1: Demographics
df_demo = pd.DataFrame()
if enable_demo:
    with tabs[0]:
        st.subheader(f"Dati Demografici per {city}, {state} (ZIP {zip_code})")
        try:
            df_demo = fetch_demographics_by_zip(zip_code, api_key=CENSUS_API_KEY)
            if not df_demo.empty:
                st.dataframe(df_demo)
                chart = df_demo[["population","median_age","median_income"]].T
                chart.columns = [zip_code]
                st.bar_chart(chart)
            else:
                st.warning("Nessun dato demografico disponibile.")
        except Exception as e:
            st.error(f"Errore caricamento dati demografici: {e}")

# Tab 2: Google Trends
df_trends = pd.DataFrame()
if enable_trends:
    with tabs[1]:
        st.subheader(f"Google Trends: {search_term}")
        timeframe = st.selectbox("Intervallo temporale:", ["now 7-d","today 1-m","today 3-m","today 12-m"])
        try:
            df_trends = fetch_google_trends(keyword=search_term, timeframe=timeframe)
            if not df_trends.empty:
                st.line_chart(df_trends['trend_volume'])
            else:
                st.warning("Nessun dato Google Trends disponibile.")
        except Exception as e:
            st.error(f"Errore Google Trends: {e}")

# Tab 3: Competitor Analysis
df_competitors = pd.DataFrame()
if enable_google or enable_yelp:
    with tabs[2]:
        st.subheader(f"Analisi Competitor: {search_term}")
        records = []
        if enable_google:
            st.markdown("**Google Reviews**")
            df_g = fetch_google_reviews(query=search_term, zip_code=zip_code)
            if not df_g.empty:
                st.dataframe(df_g)
                st.bar_chart(df_g.set_index('name')['user_ratings_total'])
                df_g['source'] = 'Google'
                df_g = df_g.rename(columns={'user_ratings_total':'reviews'})
                records.append(df_g[['source','name','rating','reviews']])
            else:
                st.warning("Nessun risultato in Google Reviews.")
        if enable_yelp:
            st.markdown("**Yelp**")
            df_y = fetch_yelp_competitors(term=search_term, zip_code=zip_code)
            if not df_y.empty:
                st.dataframe(df_y)
                st.bar_chart(df_y.set_index('name')['review_count'])
                df_y['source'] = 'Yelp'
                df_y = df_y.rename(columns={'review_count':'reviews'})
                records.append(df_y[['source','name','rating','reviews']])
            else:
                st.warning("Nessun risultato in Yelp.")
        if records:
            df_competitors = pd.concat(records, ignore_index=True)

# Tab 4: Map
with tabs[3]:
    st.subheader("Mappa Interattiva")
    lat, lon = 25.7617, -80.1918
    m = folium.Map(location=[lat, lon], zoom_start=12)
    for df_src in [('Google', 'df_g'), ('Yelp', 'df_y')]:
        if eval(df_src[1]) is not None and not eval(df_src[1]).empty:
            for _, row in eval(df_src[1]).iterrows():
                folium.Marker([lat, lon], popup=row['name']).add_to(m)
    st_folium(m, width=700)

# Tab 5: AI Analysis
with tabs[4]:
    st.subheader("Analisi Avanzata (ChatGPT)")
    if df_competitors.empty:
        st.warning("Nessun dato competitor disponibile per l'analisi AI.")
    else:
        prompt = f"Analizza questi competitor per '{search_term}' a {city}, {state} (ZIP {zip_code}):"
        for _, r in df_competitors.iterrows():
            prompt += f"\n- [{r['source']}] {r['name']}: rating {r['rating']}, reviews {r['reviews']}"
        with st.spinner("Analisi AI in corso…"):
            try:
                resp = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[{"role":"user","content":prompt}],
                    max_tokens=500
                )
                st.markdown(resp.choices[0].message.content)
            except Exception as e:
                st.error(f"Errore API OpenAI: {e}")

# Export PDF
if st.sidebar.button("Esporta PDF Report"):
    pdf = generate_pdf_report(city, state, zip_code, search_term, df_demo, df_trends, df_competitors)
    st.sidebar.download_button(
        "Download PDF",
        data=pdf,
        file_name="report.pdf",
        mime="application/pdf"
    )
