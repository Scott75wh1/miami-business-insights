import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# Modulo geo statico
from data.geo import get_supported_states, get_cities_for_state, get_zips_for_city

# Dati e analisi
from data.census import fetch_demographics_by_zip
from data.trends import fetch_google_trends
from data.google_reviews import fetch_google_reviews
from data.yelp import fetch_yelp_competitors\ nfrom data.census import fetch_demographics_by_zip
from data.trends import fetch_google_trends
from data.google_reviews import fetch_google_reviews
from data.yelp import fetch_yelp_competitors

# Configurazione pagina
st.set_page_config(page_title="Business Insights USA", layout="wide")
st.title("Business Insights USA 🗺️")

# Carica API Keys da Secrets
CENSUS_API_KEY = st.secrets["CENSUS_API_KEY"]
YELP_API_KEY = st.secrets["YELP_API_KEY"]
GOOGLE_PLACES_KEY = st.secrets["GOOGLE_PLACES_KEY"]

# --- Sidebar: Flusso gerarchico ---
st.sidebar.header("1. Seleziona Area Geografica")
# 1. Stato
states = get_supported_states()
state = st.sidebar.selectbox("Stato:", states)
# 2. Città
cities_df = get_cities_for_state(state)
city = st.sidebar.selectbox("Città:", cities_df["city_name"].tolist())
# 3. ZIP
zips_df = get_zips_for_city(city)
zip_code = st.sidebar.selectbox("ZIP code:", zips_df["zip_code"].tolist())

# --- Sidebar: Settore & Fonti ---
st.sidebar.header("2. Settore & Fonti")
categories = ["Ristorazione", "Retail", "Servizi", "Personal Care", "Altro"]
category = st.sidebar.selectbox("Categoria di attività:", categories)
custom = st.sidebar.text_input("Query personalizzata (opzionale):")
search_term = custom.strip() if custom.strip() else category
# Fonti
enable_demo = st.sidebar.checkbox("Dati Demografici", True)
enable_trends = st.sidebar.checkbox("Google Trends", True)
enable_google = st.sidebar.checkbox("Google Reviews", True)
enable_yelp = st.sidebar.checkbox("Yelp", True)

# Bottone per generare la dashboard
if st.sidebar.button("Genera Dashboard"):
    tabs = st.tabs(["Demografici", "Trends", "Competitor", "Mappa"])

    # --- Tab 1: Demografici ---
    if enable_demo:
        with tabs[0]:
            st.subheader(f"Dati Demografici per {city}, {state} (ZIP {zip_code})")
            try:
                df_demo = fetch_demographics_by_zip(zip_code, api_key=CENSUS_API_KEY)
                if not df_demo.empty:
                    st.dataframe(df_demo)
                    chart = df_demo[["population", "median_age", "median_income"]].T
                    chart.columns = [zip_code]
                    st.bar_chart(chart)
                else:
                    st.warning("Nessun dato demografico disponibile.")
            except Exception as e:
                st.error(f"Errore caricamento demografici: {e}")

    # --- Tab 2: Google Trends ---
    if enable_trends:
        with tabs[1]:
            st.subheader(f"Google Trends: {search_term}")
            timeframe = st.selectbox("Intervallo temporale:", ['now 7-d', 'today 1-m', 'today 3-m', 'today 12-m'], key='tf')
            df_trends = fetch_google_trends(keyword=search_term, timeframe=timeframe)
            if not df_trends.empty:
                st.line_chart(df_trends['trend_volume'])
            else:
                st.warning("Nessun dato Google Trends disponibile.")

    # --- Tab 3: Competitor ---
    if enable_google or enable_yelp:
        with tabs[2]:
            st.subheader(f"Analisi Competitor: {search_term}")
            if enable_google:
                st.markdown("**Google Reviews**")
                df_g = fetch_google_reviews(query=search_term, zip_code=zip_code)
                if not df_g.empty:
                    st.dataframe(df_g)
                    st.bar_chart(df_g.set_index('name')['user_ratings_total'])
                else:
                    st.warning("Nessun risultato in Google Reviews.")
            if enable_yelp:
                st.markdown("**Yelp**")
                df_y = fetch_yelp_competitors(term=search_term, zip_code=zip_code)
                if not df_y.empty:
                    st.dataframe(df_y)
                    st.bar_chart(df_y.set_index('name')['review_count'])
                else:
                    st.warning("Nessun risultato in Yelp.")

    # --- Tab 4: Mappa ---
    with tabs[3]:
        st.subheader("Mappa Interattiva")
        # Placeholder coordinate, da sostituire con geocoding
        lat, lon = 25.7617, -80.1918
        m = folium.Map(location=[lat, lon], zoom_start=12)
        if enable_google and 'df_g' in locals() and not df_g.empty:
            for _, row in df_g.iterrows():
                folium.Marker([lat, lon], popup=row['name']).add_to(m)
        if enable_yelp and 'df_y' in locals() and not df_y.empty:
            for _, row in df_y.iterrows():
                folium.Marker([lat, lon], icon=folium.Icon(color='red'), popup=row['name']).add_to(m)
        st_folium(m, width=700)
else:
    st.info("Seleziona area, settore e fonti nella sidebar, poi clicca 'Genera Dashboard'.")
