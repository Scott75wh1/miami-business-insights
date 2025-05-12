import streamlit as st
import requests
import pandas as pd
from pytrends.request import TrendReq
import folium
from streamlit_folium import st_folium

# --- API KEYS ---
CENSUS_API_KEY = st.secrets.get("CENSUS_API_KEY")
YELP_API_KEY = st.secrets.get("YELP_API_KEY")
GOOGLE_PLACES_KEY = st.secrets.get("GOOGLE_PLACES_KEY")

# --- CONSTANTS ---
CENSUS_BASE = "https://api.census.gov/data/2020/acs/acs5"

# --- Functions ---

def fetch_states():
    params = {"get": "NAME,STATE", "for": "state:*", "key": CENSUS_API_KEY}
    resp = requests.get(CENSUS_BASE, params=params)
    resp.raise_for_status()
    data = resp.json()
    df = pd.DataFrame(data[1:], columns=data[0])
    return df.rename(columns={"NAME": "state_name", "STATE": "state_fips"})


def fetch_places(state_fips):
    params = {"get": "NAME,PLACE", "for": "place:*","
              "in": f"state:{state_fips}", "key": CENSUS_API_KEY}
    resp = requests.get(CENSUS_BASE, params=params)
    resp.raise_for_status()
    data = resp.json()
    df = pd.DataFrame(data[1:], columns=data[0])
    return df.rename(columns={"NAME": "place_name", "PLACE": "place_fips"})


def fetch_zipcodes(state_fips, place_fips):
    params = {"get": "GEOID", "for": "zip code tabulation area:*","
              "in": f"state:{state_fips}+place:{place_fips}", "key": CENSUS_API_KEY}
    resp = requests.get(CENSUS_BASE, params=params)
    resp.raise_for_status()
    data = resp.json()
    df = pd.DataFrame(data[1:], columns=data[0])
    return df.rename(columns={"GEOID": "zip_code"})


def fetch_demographics(zip_code):
    vars_map = {"B01003_001E": "population",
                "B01002_001E": "median_age",
                "B19013_001E": "median_income"}
    params = {"get": ",".join(vars_map.keys()),
              "for": f"zip code tabulation area:{zip_code}",
              "key": CENSUS_API_KEY}
    resp = requests.get(CENSUS_BASE, params=params)
    resp.raise_for_status()
    data = resp.json()
    df = pd.DataFrame(data[1:], columns=data[0])
    df = df.rename(columns=vars_map)
    for col in vars_map.values():
        df[col] = pd.to_numeric(df[col], errors='coerce')
    return df

# Google Trends
pytrends = TrendReq(hl='en-US', tz=360)

def fetch_google_trends(keyword, timeframe):
    pytrends.build_payload([keyword], timeframe=timeframe)
    data = pytrends.interest_over_time()
    if data.empty:
        return pd.DataFrame()
    df = data.drop(columns=['isPartial'], errors='ignore')
    return df.rename(columns={keyword: 'trend_volume'})

# Google Reviews

def fetch_google_reviews(query, zip_code, radius=5000, max_results=10):
    SEARCH_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"
    places = requests.get(SEARCH_URL, params={
        "query": f"{query} in {zip_code}",
        "key": GOOGLE_PLACES_KEY,
        "radius": radius,
        "type": "establishment"
    }).json().get('results', [])[:max_results]
    records = []
    for p in places:
        pid = p.get('place_id')
        name = p.get('name')
        addr = p.get('formatted_address')
        det = requests.get(DETAILS_URL, params={
            "place_id": pid,
            "key": GOOGLE_PLACES_KEY,
            "fields": "rating,user_ratings_total"
        }).json().get('result', {})
        records.append({
            'name': name,
            'rating': det.get('rating'),
            'user_ratings_total': det.get('user_ratings_total'),
            'address': addr
        })
    return pd.DataFrame(records)

# Yelp

def fetch_yelp_competitors(term, zip_code, radius=5000, limit=10):
    URL = "https://api.yelp.com/v3/businesses/search"
    headers = {"Authorization": f"Bearer {YELP_API_KEY}"}
    data = requests.get(URL, headers=headers, params={
        'term': term,
        'location': zip_code,
        'radius': radius,
        'limit': limit
    }).json().get('businesses', [])
    records = []
    for b in data:
        records.append({
            'name': b.get('name'),
            'rating': b.get('rating'),
            'review_count': b.get('review_count'),
            'address': ' • '.join(b.get('location', {}).get('display_address', []))
        })
    return pd.DataFrame(records)

# --- Streamlit UI ---
st.set_page_config(page_title="Business Insights USA", layout="wide")
st.title("Business Insights USA 🗺️")

# Sidebar selection
st.sidebar.header("1. Selezione Area")
states_df = fetch_states()
state = st.sidebar.selectbox("Stato:", states_df['state_name'].tolist())
fips = states_df.loc[states_df['state_name']==state, 'state_fips'].iat[0]
places_df = fetch_places(fips)
city = st.sidebar.selectbox("Città:", places_df['place_name'].tolist())
pf = places_df.loc[places_df['place_name']==city, 'place_fips'].iat[0]
zips_df = fetch_zipcodes(fips, pf)
zip_code = st.sidebar.selectbox("ZIP code:", zips_df['zip_code'].tolist())

st.sidebar.header("2. Settore & Fonti")
category = st.sidebar.selectbox("Categoria:", ['Ristorazione','Retail','Servizi','Personal Care','Altro'])
custom = st.sidebar.text_input("Custom query:")
search_term = custom.strip() or category
sources = {
    'Demografici': st.sidebar.checkbox("Dati Demografici", True),
    'Trends': st.sidebar.checkbox("Google Trends", True),
    'Google Reviews': st.sidebar.checkbox("Google Reviews", True),
    'Yelp': st.sidebar.checkbox("Yelp", True)
}
run = st.sidebar.button("Genera Dashboard")

if run:
    tabs = st.tabs(list(sources.keys()) + ['Mappa'])
    if sources['Demografici']:
        with tabs[0]:
            st.subheader(f"Dati Demografici per {city}, {state} (ZIP {zip_code})")
            df = fetch_demographics(zip_code)
            if not df.empty:
                st.dataframe(df)
                chart = df[['population','median_age','median_income']].T
                chart.columns = [zip_code]
                st.bar_chart(chart)
            else:
                st.warning("Nessun dato demografico.")
    if sources['Trends']:
        with tabs[1]:
            st.subheader(f"Google Trends: {search_term}")
            timeframe = st.selectbox("Intervallo:", ['now 7-d','today 1-m','today 3-m','today 12-m'])
            df = fetch_google_trends(search_term, timeframe)
            if not df.empty:
                st.line_chart(df['trend_volume'])
            else:
                st.warning("Nessun dato Google Trends.")
    if sources['Google Reviews']:
        with tabs[2]:
            st.subheader(f"Google Reviews: {search_term}")
            df = fetch_google_reviews(search_term, zip_code)
            if not df.empty:
                st.dataframe(df)
                st.bar_chart(df.set_index('name')['user_ratings_total'])
            else:
                st.warning("Nessun Google Reviews.")
    if sources['Yelp']:
        with tabs[3]:
            st.subheader(f"Yelp: {search_term}")
            df = fetch_yelp_competitors(search_term, zip_code)
            if not df.empty:
                st.dataframe(df)
                st.bar_chart(df.set_index('name')['review_count'])
            else:
                st.warning("Nessun Yelp.")
    # Mappa
    with tabs[4]:
        st.subheader("Mappa Interattiva")
        lat, lon = 25.7617, -80.1918
        m = folium.Map(location=[lat, lon], zoom_start=12)
        if sources['Google Reviews'] and not df.empty:
            for _, r in df.iterrows(): folium.Marker([lat, lon], popup=r['name']).add_to(m)
        if sources['Yelp'] and not df.empty:
            for _, r in df.iterrows(): folium.Marker([lat, lon], icon=folium.Icon(color='red'), popup=r['name']).add_to(m)
        st_folium(m)
else:
    st.info("Configura i parametri nella sidebar e clicca 'Genera Dashboard'.")

