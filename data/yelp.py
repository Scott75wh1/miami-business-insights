import streamlit as st
import requests
import pandas as pd

# Prendi la chiave dai Secrets
API_KEY = st.secrets["YELP_API_KEY"]
BASE_URL = "https://api.yelp.com/v3/businesses/search"

def fetch_yelp_competitors(term: str, zip_code: str, radius: int = 5000, limit: int = 10) -> pd.DataFrame:
    """
    Cerca attività su Yelp:
    - term: es. 'coffee shop'
    - zip_code: ZIP di Miami
    - radius: in metri (max 40000)
    - limit: numero massimo di risultati
    Ritorna DataFrame con nome, rating, review_count e indirizzo.
    """
    headers = {"Authorization": f"Bearer {API_KEY}"}
    params = {
        "term": term,
        "location": zip_code,
        "radius": radius,
        "limit": limit
    }
    resp = requests.get(BASE_URL, headers=headers, params=params)
    resp.raise_for_status()
    data = resp.json().get("businesses", [])

    items = []
    for biz in data:
        items.append({
            "name": biz.get("name"),
            "rating": biz.get("rating"),
            "review_count": biz.get("review_count"),
            "address": " • ".join(biz.get("location", {}).get("display_address", []))
        })
    return pd.DataFrame(items)

# Test rapido
if __name__ == "__main__":
    df = fetch_yelp_competitors("coffee shop", "33101")
    print(df)
