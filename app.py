import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# Import dei moduli dati
from data.locations import fetch_states, fetch_places, fetch_zipcodes_for_place
from data.census import fetch_demographics_by_zip
from data.trends import fetch_google_trends
from data.google_reviews import fetch_google_reviews
from data.yelp import fetch_yelp_competitors

# Configurazione pagina
st.set_page_config(page_title="Business Insights USA", layout="wide")
st.title("Business Insights USA 🗺️")

# Caricamento API Keys da Streamlit Secrets
CENSUS_API_KEY = st.secrets["CENSUS_API_KEY"]
YELP_API_KEY = st.secrets["YELP_API_KEY"]
GOOGLE_PLACES_KEY = st.secrets["GOOGLE_PLACES_KEY"]

# --- Sidebar: Selezione Geografica ---
st.sidebar.header("1. Selezione Area Geografica")
# Stato
states_df = fetch_states(api_key=CENSUS_API_KEY)
state = st.sidebar.selectbox("Stato:", states_df['state_name'].tolist())
state_fips = states_df.loc[states_df['state_name']==state, 'state_fips'].iat[0]
# Città
places_df = fetch_places(state_fips=state_fips, api_key=CENSUS_API_KEY)
city = st.sidebar.selectbox("Città:", places_df['place_name'].tolist())
place_fips = places_df.loc[places_df['place_name']==city, 'place_fips'].iat[0]
# ZIP code
df_zips = fetch_zipcodes_for_place(state_fips=state_fips, place_fips=place_fips, api_key=CENSUS_API_KEY)
zip_code = st.sidebar.selectbox("ZIP code:", df_zips['zip_code'].tolist())

# --- Sidebar: Settore & Fonti ---
st.sidebar.header("2. Settore & Fonti")
category = st.sidebar.selectbox("Categoria:", ["Ristorazione","Retail","Servizi","Personal Care","Altro"])
custom = st.sidebar.text_input("Custom query (lascia vuoto per categoria):")
search_term = custom.strip() if custom.strip() else category

enable_demo = st.sidebar.checkbox("Dati Demografici", value=True)
enable_trends = st.sidebar.checkbox("Google Trends", value=True)
enable_google = st.sidebar.checkbox("Google Reviews", value=True)
enable_yelp = st.sidebar.checkbox("Yelp", value=True)

# Bottone per generare la dashboard
if st.sidebar.button("Genera Dashboard"):
    # Creazione dei tab
    tabs = st.tabs(["Demografici","Trends","Competitor","Mappa"])

    # --- Tab Demografici ---
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
                st.error(f"Errore demografici: {e}")

    # --- Tab Trends ---
    if enable_trends:
        with tabs[1]:
            st.subheader(f"Google Trends: {search_term}")
            timeframe = st.selectbox("Intervallo Trends:", ['now 7-d','today 1-m','today 3-m','today 12-m'], key='tf')
            df_trends = fetch_google_trends(keyword=search_term, timeframe=timeframe, geo=f"US-{state_fips}")
            if not df_trends.empty:
                st.line_chart(df_trends['trend_volume'])
            else:
                st.warning("Nessun dato Google Trends disponibile.")

    # --- Tab Competitor ---
    if enable_google or enable_yelp:
        with tabs[2]:
            st.subheader(f"Analisi Competitor: {search_term}")
            if enable_google:
                st.markdown("**Google Reviews**")
                df_g = fetch_google_reviews(query=search_term, zip_code=zip_code)
                if not df_g.empty:
                    st.dataframe(df_g)
                    if 'name' in df_g.columns and 'user_ratings_total' in df_g.columns:
                        st.bar_chart(df_g.set_index('name')['user_ratings_total'])
                else:
                    st.warning("Nessun risultato Google Reviews.")
            if enable_yelp:
                st.markdown("**Yelp**")
                df_y = fetch_yelp_competitors(term=search_term, zip_code=zip_code)
                if not df_y.empty:
                    st.dataframe(df_y)
                    if 'name' in df_y.columns and 'review_count' in df_y.columns:
                        st.bar_chart(df_y.set_index('name')['review_count'])
                else:
                    st.warning("Nessun risultato Yelp.")

    # --- Tab Mappa ---
    with tabs[3]:
        st.subheader("Mappa Interattiva dei Competitor")
        # Coordinate di default (da sostituire con geocoding)
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
    st.info("Configura area, settore e fonti nella sidebar, poi premi 'Genera Dashboard'.")
