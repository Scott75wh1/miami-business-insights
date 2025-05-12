import streamlit as st
from data.census import fetch_demographics_by_zip
from data.trends import fetch_google_trends
from data.google_reviews import fetch_google_reviews
from data.yelp import fetch_yelp_competitors
import folium
from streamlit_folium import st_folium

# Configurazione pagina
st.set_page_config(page_title="Miami Business Insights", layout="wide")
st.title("Miami Business Insights 🏝️")

# --- Sidebar Inputs ---
st.sidebar.header("Definisci l'Analisi")
# Area
area_type = st.sidebar.radio("Seleziona Area:", ["ZIP code", "Quartiere"], index=0)
if area_type == "ZIP code":
    area = st.sidebar.text_input("Inserisci ZIP code:", "33101")
else:
    neighborhoods = ["Downtown", "Wynwood", "South Beach", "Coconut Grove"]
    area = st.sidebar.selectbox("Seleziona quartiere:", neighborhoods)

# Settore
st.sidebar.subheader("Settore / Attività")
categories = ["Ristorazione", "Retail", "Servizi", "Personal Care", "Altro"]
category = st.sidebar.selectbox("Categoria:", categories)
custom = st.sidebar.text_input("Custom query (lascia vuoto per categoria):")
search_term = custom.strip() if custom.strip() else category

# Fonti
st.sidebar.subheader("Fonti dati")
enable_demo = st.sidebar.checkbox("Dati Demografici", value=True)
enable_trends = st.sidebar.checkbox("Google Trends", value=True)
enable_google = st.sidebar.checkbox("Google Reviews", value=True)
enable_yelp = st.sidebar.checkbox("Yelp", value=True)

# Genera
generate = st.sidebar.button("Genera Dashboard")

# Se non generato, mostra istruzioni
if not generate:
    st.sidebar.info("Seleziona area, settore e fonti, poi clicca 'Genera Dashboard'.")
    st.info("Imposta i parametri nella sidebar e premi 'Genera Dashboard' per avviare l'analisi.")
else:
    # Tab per risultati
    tabs = st.tabs(["Demografici", "Trends", "Competitor", "Mappa"])

    # Demografici
    if enable_demo:
        with tabs[0]:
            st.subheader("Dati Demografici per: {}".format(area))
            try:
                df_demo = fetch_demographics_by_zip(area, api_key=st.secrets["CENSUS_API_KEY"])
                if not df_demo.empty:
                    st.dataframe(df_demo)
                    chart = df_demo[["population", "median_age", "median_income"]].T
                    chart.columns = [area]
                    st.bar_chart(chart)
                else:
                    st.warning("Nessun dato demografico disponibile.")
            except Exception as e:
                st.error(f"Errore demografici: {e}")

    # Trends
    if enable_trends:
        with tabs[1]:
            st.subheader("Google Trends per: {}".format(search_term))
            timeframe = st.selectbox("Intervallo Trends:", ['now 7-d', 'today 1-m', 'today 3-m', 'today 12-m'])
            df_trends = fetch_google_trends(search_term, timeframe=timeframe)
            if not df_trends.empty:
                st.line_chart(df_trends['trend_volume'])
            else:
                st.warning("Nessun dato Google Trends disponibile.")

    # Competitor
    if enable_google or enable_yelp:
        with tabs[2]:
            st.subheader("Analisi Competitor: {}".format(search_term))
            if enable_google:
                st.markdown("**Google Reviews**")
                df_g = fetch_google_reviews(search_term, area)
                if not df_g.empty:
                    st.dataframe(df_g)
                    if 'name' in df_g.columns and 'user_ratings_total' in df_g.columns:
                        st.bar_chart(df_g.set_index('name')['user_ratings_total'])
                else:
                    st.warning("Nessun risultato Google Reviews.")
            if enable_yelp:
                st.markdown("**Yelp**")
                df_y = fetch_yelp_competitors(search_term, area)
                if not df_y.empty:
                    st.dataframe(df_y)
                    if 'name' in df_y.columns and 'review_count' in df_y.columns:
                        st.bar_chart(df_y.set_index('name')['review_count'])
                else:
                    st.warning("Nessun risultato Yelp.")

    # Mappa
    with tabs[3]:
        st.subheader("Mappa Interattiva dei Competitor")
        coords = {'33101': (25.7751, -80.2105)}
        lat, lon = coords.get(area, (25.7617, -80.1918))
        m = folium.Map(location=[lat, lon], zoom_start=13)
        if enable_google and 'df_g' in locals() and not df_g.empty:
            for _, r in df_g.iterrows(): folium.Marker([lat, lon], popup=r['name']).add_to(m)
        if enable_yelp and 'df_y' in locals() and not df_y.empty:
            for _, r in df_y.iterrows(): folium.Marker([lat, lon], icon=folium.Icon(color='red'), popup=r['name']).add_to(m)
        st_folium(m, width=700)
