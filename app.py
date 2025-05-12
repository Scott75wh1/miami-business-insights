import os
import sys
# Aggiunge la cartella data al path per import diretti
sys.path.append(os.path.join(os.path.dirname(__file__), "data"))

import streamlit as st
import folium
from streamlit_folium import st_folium

# Import moduli dai file in data/
import locations
import census
import trends
import google_reviews
import yelp

# Configurazione pagina
st.set_page_config(page_title="Business Insights USA", layout="wide")
st.title("Business Insights USA 🗺️")

# Carica API Key
CENSUS_API_KEY = st.secrets.get("CENSUS_API_KEY")

# --- Sidebar: Selezione Geografica dinamica ---
st.sidebar.header("1. Selezione Area Geografica")
# 1. Stato
states_df = locations.fetch_states(CENSUS_API_KEY)
states = states_df["state_name"].tolist()
state_sel = st.sidebar.selectbox("Seleziona Stato:", states)
state_fips = states_df.loc[states_df["state_name"] == state_sel, "state_fips"].iat[0]

# 2. Città (Place)
places_df = locations.fetch_places(state_fips, CENSUS_API_KEY)
places = places_df["place_name"].tolist()
city_sel = st.sidebar.selectbox("Seleziona Città:", places)
place_fips = places_df.loc[places_df["place_name"] == city_sel, "place_fips"].iat[0]

# 3. ZIP code list per città
zips_df = locations.fetch_zipcodes_for_place(state_fips, place_fips, CENSUS_API_KEY)
zip_codes = zips_df["zip_code"].tolist()
zip_sel = st.sidebar.selectbox("Seleziona ZIP code:", zip_codes)

# --- Sidebar: Definizione Settore e Fonti ---
st.sidebar.header("2. Settore & Fonti")
# Settore
categories = ["Ristorazione", "Retail", "Servizi", "Personal Care", "Altro"]
cat_sel = st.sidebar.selectbox("Categoria:", categories)
custom = st.sidebar.text_input("Custom query (lascia vuoto per categoria):")
search_term = custom.strip() if custom.strip() else cat_sel
# Fonti
enable_demo = st.sidebar.checkbox("Dati Demografici", True)
enable_trends = st.sidebar.checkbox("Google Trends", True)
enable_google = st.sidebar.checkbox("Google Reviews", True)
enable_yelp = st.sidebar.checkbox("Yelp", True)

# Genera Dashboard
if st.sidebar.button("Genera Dashboard"):
    tabs = st.tabs(["Demografici", "Trends", "Competitor", "Mappa"])

    # Demografici
    if enable_demo:
        with tabs[0]:
            st.subheader(f"Dati Demografici per {city_sel}, {state_sel} (ZIP {zip_sel})")
            try:
                df_demo = census.fetch_demographics_by_zip(zip_sel, api_key=CENSUS_API_KEY)
                if not df_demo.empty:
                    st.dataframe(df_demo)
                    chart = df_demo[["population","median_age","median_income"]].T
                    chart.columns = [zip_sel]
                    st.bar_chart(chart)
                else:
                    st.warning("Nessun dato demografico disponibile.")
            except Exception as e:
                st.error(f"Errore demografici: {e}")

    # Trends
    if enable_trends:
        with tabs[1]:
            st.subheader(f"Google Trends per: {search_term}")
            timeframe = st.selectbox("Intervallo Trends:", ['now 7-d','today 1-m','today 3-m','today 12-m'], key='tf')
            df_trends = trends.fetch_google_trends(search_term, timeframe=timeframe)
            if not df_trends.empty:
                st.line_chart(df_trends['trend_volume'])
            else:
                st.warning("Nessun dato Google Trends disponibile.")

    # Competitor
    if enable_google or enable_yelp:
        with tabs[2]:
            st.subheader(f"Analisi Competitor: {search_term}")
            # Google Reviews
            if enable_google:
                st.markdown("**Google Reviews**")
                df_g = google_reviews.fetch_google_reviews(search_term, zip_sel)
                if not df_g.empty:
                    st.dataframe(df_g)
                    if 'name' in df_g.columns and 'user_ratings_total' in df_g.columns:
                        st.bar_chart(df_g.set_index('name')['user_ratings_total'])
                else:
                    st.warning("Nessun risultato Google Reviews.")
            # Yelp
            if enable_yelp:
                st.markdown("**Yelp**")
                df_y = yelp.fetch_yelp_competitors(search_term, zip_sel)
                if not df_y.empty:
                    st.dataframe(df_y)
                    if 'name' in df_y.columns and 'review_count' in df_y.columns:
                        st.bar_chart(df_y.set_index('name')['review_count'])
                else:
                    st.warning("Nessun risultato Yelp.")

    # Mappa
    with tabs[3]:
        st.subheader("Mappa Interattiva dei Competitor")
        # Placeholder coordinate, da sostituire con geocoding reale
        lat, lon = 25.7617, -80.1918
        m = folium.Map(location=[lat, lon], zoom_start=12)
        if enable_google and not df_g.empty:
            for _, r in df_g.iterrows(): folium.Marker([lat, lon], popup=r['name']).add_to(m)
        if enable_yelp and not df_y.empty:
            for _, r in df_y.iterrows(): folium.Marker([lat, lon], icon=folium.Icon(color='red'), popup=r['name']).add_to(m)
        st_folium(m, width=700)
else:
    st.info("Imposta area, settore e fonti, poi clicca ‘Genera Dashboard’.")
