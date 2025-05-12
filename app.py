import streamlit as st
from data.trends import fetch_google_trends
from data.census import fetch_demographics_by_zip
from data.google_reviews import fetch_google_reviews
from data.yelp import fetch_yelp_competitors


# Configurazione Streamlit Secrets per API Key
CENSUS_API_KEY = st.secrets["CENSUS_API_KEY"]

st.set_page_config(page_title="Miami Business Insights", layout="wide")
st.title("Miami Business Insights 🏝️")

# Sidebar: selezione area (ZIP code) e keyword competitor
area = st.sidebar.text_input("Inserisci ZIP code (Miami)", "33101")
competitor_query = st.sidebar.text_input("Cerca competitor (es. 'coffee shop')", "coffee shop")
yelp_query = st.sidebar.text_input("Yelp competitor (es. 'coffee shop')", "coffee shop")
trend_keyword = st.sidebar.text_input("Keyword Trends (es. 'coffee shop')", "coffee shop")
timeframe = st.sidebar.selectbox(
    "Intervallo Trends",
    ['now 7-d', 'today 1-m', 'today 3-m', 'today 12-m']
)


if area:
    # Dati demografici
    with st.spinner(f"Caricamento dati demografici per ZIP {area}..."):
        # Passa la chiave API al modulo census
        df_demo = fetch_demographics_by_zip(area, api_key=CENSUS_API_KEY)
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
            st.subheader("Numero di recensioni per competitor")
            comp_chart = df_comp.set_index("name")["user_ratings_total"]
            st.bar_chart(comp_chart)
        else:
            st.warning(f"Nessun risultato per {competitor_query} nel ZIP {area}.")
else:
    st.info("Inserisci un codice ZIP nella sidebar per iniziare l'analisi.")
    # ——————————————————————————————————————————
# Sezione Google Trends
if trend_keyword:
    with st.spinner(f"Caricamento Google Trends per '{trend_keyword}'..."):
        df_trends = fetch_google_trends(trend_keyword, timeframe=timeframe)
    if not df_trends.empty:
        st.subheader(f"Google Trends: {trend_keyword} ({timeframe})")
        st.line_chart(df_trends['trend_volume'])
    else:
        st.warning(f"Nessun dato Trends per '{trend_keyword}' nel periodo selezionato.")
        # ——————————————————————————————————————————
# Sezione Yelp Competitor
if yelp_query:
    with st.spinner(f"Caricamento dati Yelp per '{yelp_query}'..."):
        df_yelp = fetch_yelp_competitors(yelp_query, area)
    if not df_yelp.empty:
        st.subheader(f"Yelp Competitor: {yelp_query} a ZIP {area}")
        st.dataframe(df_yelp)
        st.subheader("Numero di recensioni da Yelp")
        yelp_chart = df_yelp.set_index("name")["review_count"]
        st.bar_chart(yelp_chart)
    else:
        st.warning(f"Nessun risultato Yelp per {yelp_query} nel ZIP {area}.")


