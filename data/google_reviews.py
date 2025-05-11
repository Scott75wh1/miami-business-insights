import streamlit as st
import requests
import pandas as pd

# Recupera la chiave da Streamlit Secrets
API_KEY = st.secrets["GOOGLE_PLACES_KEY"]

# Endpoint per la Text Search e Details
BASE_SEARCH_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
BASE_DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"

def fetch_google_reviews(query: str, zip_code: str, radius: int = 5000, max_results: int = 10) -> pd.DataFrame:
    """
    Cerca luoghi tramite il parametro 'query' e 'zip_code', restituisce un DataFrame con:
    - name: nome attività
    - rating: punteggio medio
    - user_ratings_total: numero di recensioni totali
    - address: indirizzo formattato
    """
    # Primo: ricerca dei luoghi
    search_params = {
        "query": f"{query} in {zip_code}",
        "key": API_KEY,
        "radius": radius,
        "type": "establishment"
    }
    resp = requests.get(BASE_SEARCH_URL, params=search_params)
    resp.raise_for_status()
    results = resp.json().get("results", [])[:max_results]

    places = []
    for place in results:
        place_id = place.get("place_id")
        name = place.get("name")
        address = place.get("formatted_address")
        # Dettagli per ottenere il numero di recensioni
        details_params = {
            "place_id": place_id,
            "key": API_KEY,
            "fields": "rating,user_ratings_total"
        }
        det_resp = requests.get(BASE_DETAILS_URL, params=details_params)
        det_resp.raise_for_status()
        det = det_resp.json().get("result", {})

        places.append({
            "name": name,
            "rating": det.get("rating"),
            "user_ratings_total": det.get("user_ratings_total"),
            "address": address
        })

    df = pd.DataFrame(places)
    return df

# Test rapido (solo in locale/Codespace)
if __name__ == "__main__":
    df = fetch_google_reviews("coffee shop", "33101")
    print(df)
