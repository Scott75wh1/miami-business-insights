import os
import sys
import pathlib
import importlib.util
import streamlit as st
import folium
from streamlit_folium import st_folium

# --- Debug: verifica struttura del progetto ---
st.write("Working directory:", os.getcwd())
st.write("sys.path:", sys.path)
root_files = os.listdir(os.getcwd())
st.write("Root files:", root_files)
if "data" in root_files:
    st.write("Data directory contents:", os.listdir(os.path.join(os.getcwd(), "data")))
else:
    st.error("'data' directory not found in project root.")

# ---- Caricamento dinamico dei moduli da 'data/' ----
DATA_DIR = pathlib.Path(__file__).parent / "data"

def load_module(name):
    path = DATA_DIR / f"{name}.py"
    if not path.exists():
        st.error(f"Module file not found: {path}")
        return None
    spec = importlib.util.spec_from_file_location(name, str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

locations = load_module("locations")
census_api = load_module("census")
trends_mod = load_module("trends")
google_reviews_mod = load_module("google_reviews")
yelp_mod = load_module("yelp")

# Stop if modules missing
if not locations or not census_api:
    st.stop()

# Configurazione pagina
st.set_page_config(page_title="Business Insights USA", layout="wide")
st.title("Business Insights USA 🗺️")

# API Key
CENSUS_API_KEY = st.secrets.get("CENSUS_API_KEY")

# --- Sidebar: selezione geografica ---
st.sidebar.header("1. Selezione Area Geografica")
# Stato
states_df = locations.fetch_states(CENSUS_API_KEY)
states = states_df["state_name"].tolist()
state_sel = st.sidebar.selectbox("Seleziona Stato:", states)
state_fips = states_df.loc[states_df["state_name"] == state_sel, "state_fips"].iat[0]
# Città
places_df = locations.fetch_places(state_fips, CENSUS_API_KEY)
places = places_df["place_name"].tolist()
city_sel = st.sidebar.selectbox("Seleziona Città:", places)
place_fips = places_df.loc[places_df["place_name"] == city_sel, "place_fips"].iat[0]
# ZIP codes
zips_df = locations.fetch_zipcodes_for_place(state_fips, place_fips, CENSUS_API_KEY)
zip_codes = zips_df["zip_code"].tolist()
zip_sel = st.sidebar.selectbox("Seleziona ZIP code:", zip_codes)

# --- Sidebar: settore e fonti ---
st.sidebar.header("2. Settore & Fonti")
categories = ["Ristorazione", "Retail", "Servizi", "Personal Care", "Altro"]
cat_sel = st.sidebar.selectbox("Categoria:", categories)
custom = st.sidebar.text_input("Custom query (lascia vuoto per categoria):")
search_term = custom.strip() if custom.strip() else cat_sel
# Fonti
enable_demo = st.sidebar.checkbox("Dati Demografici", True)
enable_trends = st.sidebar.checkbox("Google Trends", True)
enable_google = st.sidebar.checkbox("Google Reviews", True)
enable_yelp = st.sidebar.checkbox("Yelp", True)

# Bottone Genera Dashboard
if st.sidebar.button("Genera Dashboard"):
    tabs = st.tabs(["Demografici", "Trends", "Competitor", "Mappa"])

    # Demografici
    if enable_demo:
        with tabs[0]:
            st.subheader(f"Dati Demografici per {city_sel}, {state_sel} (ZIP {zip_sel})")
            try:
                df_demo = census_api.fetch_demographics_by_zip(zip_sel, api_key=CENSUS_API_KEY)
                if not df_demo.empty:
                    st.dataframe(df_demo)
                    chart = df_demo[["population","median_age","median_income"]].T
                    chart.columns = [zip_sel]
                    st.bar_chart(chart)
                else:
                    st.warning("Nessun dato demografico disponibile.")
            except Exception as e:
                st.error(f"Errore demografici: {e}")

    # Google Trends
    if enable_trends:
        with tabs[1]:
            st.subheader(f"Google Trends per: {search_term}")
            timeframe = st.selectbox("Intervallo Trends:", ['now 7-d','today 1-m','today 3-m','today 12-m'], key='tf')
            df_trends = trends_mod.fetch_google_trends(search_term, timeframe=timeframe)
            if not df_trends.empty:
                st.line_chart(df_trends['trend_volume'])
            else:
                st.warning("Nessun dato Google Trends disponibile.")

    # Competitor
    if enable_google or enable_yelp:
        with tabs[2]:
            st.subheader(f"Analisi Competitor: {search_term}")
            if enable_google:
                st.markdown("**Google Reviews**")
                df_g = google_reviews_mod.fetch_google_reviews(search_term, zip_sel)
                if not df_g.empty:
                    st.dataframe(df_g)
                    if 'name' in df_g.columns and 'user_ratings_total' in df_g.columns:
                        st.bar_chart(df_g.set_index('name')['user_ratings_total'])
                else:
                    st.warning("Nessun risultato Google Reviews.")
            if enable_yelp:
                st.markdown("**Yelp**")
                df_y = yelp_mod.fetch_yelp_competitors(search_term, zip_sel)
                if not df_y.empty:
                    st.dataframe(df_y)
                    if 'name' in df_y.columns and 'review_count' in df_y.columns:
                        st.bar_chart(df_y.set_index('name')['review_count'])
                else:
                    st.warning("Nessun risultato Yelp.")

    # Mappa Interattiva
    with tabs[3]:
        st.subheader("Mappa Interattiva dei Competitor")
        # Placeholder: geocoding da implementare
        lat, lon = 25.7617, -80.1918
        m = folium.Map(location=[lat, lon], zoom_start=12)
        if enable_google and 'df_g' in locals() and not df_g.empty:
            for _, r in df_g.iterrows():
                folium.Marker([lat, lon], popup=r['name']).add_to(m)
        if enable_yelp and 'df_y' in locals() and not df_y.empty:
            for _, r in df_y.iterrows():
                folium.Marker([lat, lon], icon=folium.Icon(color='red'), popup=r['name']).add_to(m)
        st_folium(m, width=700)
else:
    st.info("Imposta area, settore e fonti, poi clicca 'Genera Dashboard'.")
