import streamlit as st
from data.census import fetch_demographics_by_zip

# Configurazione Streamlit Secrets per API Key
CENSUS_API_KEY = st.secrets["CENSUS_API_KEY"]

st.set_page_config(page_title="Miami Business Insights", layout="wide")
st.title("Miami Business Insights 🏝️")

# Sidebar: selezione area (ZIP code)
area = st.sidebar.text_input("Inserisci ZIP code (Miami)", "33101")

if area:
    # Richiesta dati demografici
    with st.spinner(f"Caricamento dati demografici per {area}..."):
        df = fetch_demographics_by_zip(area, api_key=CENSUS_API_KEY)

    if not df.empty:
        st.subheader(f"Dati demografici per ZIP {area}")
        # Mostra tabella
        st.dataframe(df)

        # Visualizzazione a barre delle metriche principali
        st.subheader("Analisi visuale")
        chart_data = df.loc[:, ["population", "median_age", "median_income"]].T
        chart_data.columns = [f"ZIP {area}"]
        st.bar_chart(chart_data)
    else:
        st.error("Nessun dato trovato per il ZIP code inserito. Controlla e riprova.")
else:
    st.info("Inserisci un codice ZIP nella sidebar per iniziare l'analisi.")

