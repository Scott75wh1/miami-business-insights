import streamlit as st
from data.census import fetch_demographics_by_zip
from data.google_reviews import fetch_google_reviews

# Configurazione Streamlit Secrets per API Key
CENSUS_API_KEY = st.secrets["CENSUS_API_KEY"]

st.set_page_config(page_title="Miami Business Insights", layout="wide")
st.title("Miami Business Insights 🏝️")

# Sidebar: selezione area (ZIP code) e keyword competitor
area = st.sidebar.text_input("Inserisci ZIP code (Miami)", "33101")
competitor_query = st.sidebar.text_input("Cerca competitor (es. 'coffee shop')", "coffee shop")

if area:
    # Dati demografici
    with st.spinner(f"Caricamento dati demografici per ZIP {area}..."):
        df_demo = fetch_demographics_by_zip(area)
    if not df_demo.empty:
        st.subheader(f"Dati demografici per ZIP {area}")
        st.dataframe(df_demo)
        st.subheader("Analisi demografica visiva")
        demo_chart = df_demo.loc[:, ["population", "median_age", "median_income"]].T
        demo_chart.columns = [f"ZIP {area}"]
        st.bar_chart(demo_chart)
    else:
        st.error("Nessun dato demografico per il ZIP code inserito.")

    # Analisi competitor
    if competitor_query:
        with st.spinner(f"Caricamento dati competitor per '{competitor_query}'..."):
            df_comp = fetch_google_reviews(competitor_query, area)
        if not df_comp.empty:
            st.subheader(f"Analisi Competitor: {competitor_query} a ZIP {area}")
            st.dataframe(df_comp)
            # Visualizza numero recensioni per competitor
            comp_chart = df_comp.set_index("name")["user_ratings_total"]
            st.bar_chart(comp_chart)
        else:
            st.warning(f"Nessun risultato per {competitor_query} nel ZIP {area}.")
else:
    st.info("Inserisci un codice ZIP nella sidebar per iniziare l'analisi.")


