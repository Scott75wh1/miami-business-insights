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

# --- Sidebar Wizard ---
st.sidebar.header("1. Seleziona Area")
area_method = st.sidebar.radio("Metodo di selezione:", ["ZIP code", "Quartiere predefinito"])
if area_method == "ZIP code":
    area = st.sidebar.text_input("Inserisci ZIP code:", "33101")
else:
    neighborhoods = ["Downtown", "Wynwood", "South Beach", "Coconut Grove"]
    area = st.sidebar.selectbox("Seleziona quartiere:", neighborhoods)

st.sidebar.header("2. Seleziona Settore")
categories = ["Ristorazione", "Retail", "Servizi", "Personal Care", "Altro"]
category = st.sidebar.selectbox("Categoria di attività:", categories)
custom_query = st.sidebar.text_input("Query personalizzata (Lascia vuoto per usare la categoria):", "")
search_term = custom_query if custom_query else category

st.sidebar.header("3. Seleziona Fonti")
enable_demo = st.sidebar.checkbox("Dati demografici", True)
enable_trends = st.sidebar.checkbox("Google Trends", True)
enable_google = st.sidebar.checkbox("Google Reviews", True)
enable_yelp = st.sidebar.checkbox("Yelp", True)

# Button per generare dashboard
generate = st.sidebar.button("Genera Dashboard")

if generate:
    # Crea tabs
    tabs = st.tabs(["Demografici", "Trends", "Competitor", "Mappa"])

    # --- Demografici ---
    if enable_demo:
        with tabs[0]:
            st.subheader("Dati Demografici")
            try:
                df_demo = fetch_demographics_by_zip(area, api_key=st.secrets["CENSUS_API_KEY"])
                if not df_demo.empty:
                    st.dataframe(df_demo)
                    chart = df_demo[ ["population", "median_age", "median_income"] ].T
                    chart.columns = [area]
                    st.bar_chart(chart)
                else:
                    st.warning("Nessun dato demografico disponibile per l'area selezionata.")
            except Exception as e:
                st.error(f"Errore caricamento demografici: {e}")

    # --- Trends ---
    if enable_trends:
        with tabs[1]:
            st.subheader("Google Trends")
            df_trends = fetch_google_trends(search_term)
            if not df_trends.empty:
                st.line_chart(df_trends['trend_volume'])
            else:
                st.warning("Nessun dato Google Trends disponibile.")

    # --- Competitor ---
    if enable_google or enable_yelp:
        with tabs[2]:
            st.subheader("Analisi Competitor")
            if enable_google:
                st.markdown("**Google Reviews**")
                df_g = fetch_google_reviews(search_term, area)
                if not df_g.empty:
                    st.dataframe(df_g)
                    if 'name' in df_g and 'user_ratings_total' in df_g:
                        st.bar_chart(df_g.set_index('name')['user_ratings_total'])
                else:
                    st.warning("Nessun risultato in Google Reviews.")
            if enable_yelp:
                st.markdown("**Yelp**")
                df_y = fetch_yelp_competitors(search_term, area)
                if not df_y.empty:
                    st.dataframe(df_y)
                    if 'name' in df_y and 'review_count' in df_y:
                        st.bar_chart(df_y.set_index('name')['review_count'])
                else:
                    st.warning("Nessun risultato in Yelp.")

    # --- Mappa ---
    with tabs[3]:
        st.subheader("Mappa Interattiva")
        default_coords = {'33101': (25.7751, -80.2105)}
        lat, lon = default_coords.get(area, (25.7617, -80.1918))
        m = folium.Map(location=[lat, lon], zoom_start=13)
        # Marker Google
        if enable_google and 'df_g' in locals() and not df_g.empty:
            for _, row in df_g.iterrows():
                folium.Marker([lat, lon], popup=f"{row['name']} (⭐{row['rating']})")
        # Marker Yelp
        if enable_yelp and 'df_y' in locals() and not df_y.empty:
            for _, row in df_y.iterrows():
                folium.Marker([lat, lon], icon=folium.Icon(color='red'), popup=f"{row['name']} (⭐{row['rating']})")
        st_folium(m, width=700)
else:
    st.info("Completa i tre step nella sidebar e premi 'Genera Dashboard' per visualizzare l'analisi.")

