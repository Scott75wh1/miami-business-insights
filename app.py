import streamlit as st
from data.census import fetch_demographics_by_zip
from data.trends import fetch_google_trends
from data.google_reviews import fetch_google_reviews
from data.yelp import fetch_yelp_competitors

st.set_page_config(page_title="Miami Business Insights", layout="wide")
st.title("Miami Business Insights 🏝️")

# --- Sidebar Wizard ---
st.sidebar.header("1. Seleziona Area")
area_method = st.sidebar.radio("Metodo di selezione:", ["ZIP code", "Quartiere predefinito"])
if area_method == "ZIP code":
    area = st.sidebar.text_input("Inserisci ZIP code (Miami)", "33101")
else:
    neighborhoods = ["Downtown", "Wynwood", "South Beach", "Coconut Grove"]
    area = st.sidebar.selectbox("Seleziona quartiere:", neighborhoods)

st.sidebar.header("2. Seleziona Settore")
categories = ["Ristorazione", "Retail", "Servizi", "Personal Care", "Altro"]
category = st.sidebar.selectbox("Categoria di attività:", categories)
if category == "Altro":
    custom_query = st.sidebar.text_input("Inserisci settore personalizzato:", "")
else:
    custom_query = category.lower()

st.sidebar.header("3. Seleziona Fonti")
enable_demo = st.sidebar.checkbox("Dati demografici", True)
enable_trends = st.sidebar.checkbox("Google Trends", True)
enable_google = st.sidebar.checkbox("Google Reviews", True)
enable_yelp = st.sidebar.checkbox("Yelp", True)

# Pulsante per generare dashboard
if st.sidebar.button("Genera Dashboard"):
    # Main area tabs
    tabs = st.tabs(["Demografici", "Trends", "Competitor", "Mappa"])
    # Demografici
    if enable_demo:
        with tabs[0]:
            st.subheader("Dati Demografici")
            try:
                df_demo = fetch_demographics_by_zip(area, api_key=st.secrets["CENSUS_API_KEY"])
                st.dataframe(df_demo)
                chart = df_demo.loc[:, ["population", "median_age", "median_income"]].T
                chart.columns = [area]
                st.bar_chart(chart)
            except Exception as e:
                st.error(f"Errore caricamento demografici: {e}")
    # Trends
    if enable_trends:
        with tabs[1]:
            st.subheader("Google Trends")
            trend_kw = st.text_input("Keyword per Trends:", custom_query)
            timeframe = st.selectbox("Intervallo:", ['now 7-d', 'today 1-m', 'today 3-m', 'today 12-m'])
            if trend_kw:
                df_trends = fetch_google_trends(trend_kw, timeframe=timeframe)
                if not df_trends.empty:
                    st.line_chart(df_trends['trend_volume'])
                else:
                    st.warning("Nessun dato Trends disponibile.")
    # Competitor
    if enable_google or enable_yelp:
        with tabs[2]:
            st.subheader("Analisi Competitor")
            if enable_google:
                st.markdown("**Google Reviews**")
                google_kw = st.text_input("Keyword Google Reviews:", custom_query)
                if google_kw:
                    df_g = fetch_google_reviews(google_kw, area)
                    st.dataframe(df_g)
                    # Verifica colonne prima di plottare
                    if 'name' in df_g.columns and 'user_ratings_total' in df_g.columns:
                        st.bar_chart(df_g.set_index('name')['user_ratings_total'])
                    else:
                        st.warning('Impossibile creare il grafico Google Reviews: dati mancanti.')
            if enable_yelp:
                st.markdown("**Yelp**")
                yelp_kw = st.text_input("Keyword Yelp:", custom_query)
                if yelp_kw:
                    df_y = fetch_yelp_competitors(yelp_kw, area)
                    st.dataframe(df_y)
                    # Verifica colonne prima di plottare
                    if 'name' in df_y.columns and 'review_count' in df_y.columns:
                        st.bar_chart(df_y.set_index('name')['review_count'])
                    else:
                        st.warning('Impossibile creare il grafico Yelp: dati mancanti.')
    # Mappa
    with tabs[3]:
        st.subheader("Mappa Interattiva")
        # Crea mappa centrata sull'area selezionata (si usa geocoding semplice: ZIP -> lat/lng di default)
        try:
            import folium
            from streamlit_folium import st_folium

            # Coordinate approssimative per Miami ZIPs (potenziare con geocoding real)
            default_coords = {'33101': (25.7751, -80.2105)}
            lat, lon = default_coords.get(area, (25.7617, -80.1918))
            m = folium.Map(location=[lat, lon], zoom_start=13)

            # Aggiungi marker per competitor Google
            if enable_google and 'df_g' in locals() and not df_g.empty:
                for _, row in df_g.iterrows():
                    # Qui potremmo usare geocoding per l'indirizzo
                    folium.Marker([lat, lon],
                                  popup=f"{row['name']} (⭐ {row['rating']}, {row['user_ratings_total']} recensioni)")
            # Aggiungi marker per Yelp
            if enable_yelp and 'df_y' in locals():
                for _, row in df_y.iterrows():
                    folium.Marker([lat, lon],
                                  icon=folium.Icon(color='red'),
                                  popup=f"{row['name']} (⭐ {row['rating']}, {row['review_count']} recensioni)")

            st_folium(m, width=700)
        except ImportError:
            st.error("Per la mappa è necessario installare 'folium' e 'streamlit_folium'.")
else:
    st.info("Completa i tre step nella sidebar e clicca 'Genera Dashboard' per visualizzare l'analisi.")
    st.info("Completa i tre step nella sidebar e clicca 'Genera Dashboard' per visualizzare l'analisi.")
