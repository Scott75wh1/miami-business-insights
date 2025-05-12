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

# --- Sidebar Wizard Form ---
with st.sidebar.form(key='inputs'):
    st.header("1. Seleziona Area")
    area_method = st.radio("Metodo di selezione:", ["ZIP code", "Quartiere predefinito"], key='area_method')
    if area_method == "ZIP code":
        area = st.text_input("Inserisci ZIP code:", "33101", key='area')
    else:
        neighborhoods = ["Downtown", "Wynwood", "South Beach", "Coconut Grove"]
        area = st.selectbox("Seleziona quartiere:", neighborhoods, key='area_nb')

    st.header("2. Seleziona Settore")
    categories = ["Ristorazione", "Retail", "Servizi", "Personal Care", "Altro"]
    category = st.selectbox("Categoria di attività:", categories, key='category')
    custom_query = st.text_input("Query personalizzata (lascia vuoto per categoria):", "", key='custom_query')
    search_term = custom_query if custom_query else category

    st.header("3. Seleziona Fonti")
    enable_demo = st.checkbox("Dati demografici", True, key='enable_demo')
    enable_trends = st.checkbox("Google Trends", True, key='enable_trends')
    enable_google = st.checkbox("Google Reviews", True, key='enable_google')
    enable_yelp = st.checkbox("Yelp", True, key='enable_yelp')

    submit = st.form_submit_button(label='Genera Dashboard')

# Verifica se form è stato inviato
if submit:
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
                    chart = df_demo[["population", "median_age", "median_income"]].T
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
                    if 'name' in df_g.columns and 'user_ratings_total' in df_g.columns:
                        st.bar_chart(df_g.set_index('name')['user_ratings_total'])
                else:
                    st.warning("Nessun risultato in Google Reviews.")
            if enable_yelp:
                st.markdown("**Yelp**")
                df_y = fetch_yelp_competitors(search_term, area)
                if not df_y.empty:
                    st.dataframe(df_y)
                    if 'name' in df_y.columns and 'review_count' in df_y.columns:
                        st.bar_chart(df_y.set_index('name')['review_count'])
                else:
                    st.warning("Nessun risultato in Yelp.")

    # --- Mappa ---
    with tabs[3]:
        st.subheader("Mappa Interattiva")
        default_coords = {'33101': (25.7751, -80.2105)}
        lat, lon = default_coords.get(area, (25.7617, -80.1918))
        m = folium.Map(location=[lat, lon], zoom_start=13)
        if enable_google and 'df_g' in locals() and not df_g.empty:
            for _, row in df_g.iterrows():
                folium.Marker([lat, lon], popup=f"{row['name']} (⭐{row['rating']})").add_to(m)
        if enable_yelp and 'df_y' in locals() and not df_y.empty:
            for _, row in df_y.iterrows():
                folium.Marker([lat, lon], icon=folium.Icon(color='red'), popup=f"{row['name']} (⭐{row['rating']})").add_to(m)
        st_folium(m, width=700)
else:
    st.info("Completa i tre step nella sidebar e premi 'Genera Dashboard' per visualizzare l'analisi.")
