import requests
import pandas as pd

BASE_URL = "https://api.census.gov/data/2020/acs/acs5/geography"

class CensusGeoError(Exception):
    """Eccezione per errori nel Geography API"""
    pass


def fetch_states(api_key: str) -> pd.DataFrame:
    """
    Recupera l'elenco degli stati USA con i loro codici FIPS.
    Ritorna DataFrame con colonne: state_name, state_fips
    """
    params = {
        "get": "NAME,STATE",
        "for": "state:*","
        "key": api_key
    }
    resp = requests.get(BASE_URL, params=params)
    if resp.status_code != 200:
        raise CensusGeoError(f"HTTP {resp.status_code}: {resp.text}")
    try:
        data = resp.json()
    except ValueError:
        raise CensusGeoError(f"Risposta non valida Geography API: {resp.text[:200]}")
    header, *rows = data
    df = pd.DataFrame(rows, columns=header)
    df = df.rename(columns={"NAME": "state_name", "STATE": "state_fips"})
    return df


def fetch_places(state_fips: str, api_key: str) -> pd.DataFrame:
    """
    Dato il FIPS dello stato, recupera i comuni (place).
    Ritorna DataFrame con colonne: place_name, place_fips
    """
    params = {
        "get": "NAME,PLACE",
        "for": f"place:*","
        "in": f"state:{state_fips}",
        "key": api_key
    }
    resp = requests.get(BASE_URL, params=params)
    if resp.status_code != 200:
        raise CensusGeoError(f"HTTP {resp.status_code}: {resp.text}")
    try:
        data = resp.json()
    except ValueError:
        raise CensusGeoError(f"Risposta non valida Geography API: {resp.text[:200]}")
    header, *rows = data
    df = pd.DataFrame(rows, columns=header)
    df = df.rename(columns={"NAME": "place_name", "PLACE": "place_fips"})
    return df


def fetch_zipcodes_for_place(state_fips: str, place_fips: str, api_key: str) -> pd.DataFrame:
    """
    Dato state_fips e place_fips, recupera i ZIP code tabulation areas (ZCTAs) all'interno del comune.
    Ritorna DataFrame con colonna zip_code
    """
    params = {
        "get": "GEOID",
        "for": "zip code tabulation area:*","
        "in": f"state:{state_fips}+place:{place_fips}",
        "key": api_key
    }
    resp = requests.get(BASE_URL, params=params)
    if resp.status_code != 200:
        raise CensusGeoError(f"HTTP {resp.status_code}: {resp.text}")
    try:
        data = resp.json()
    except ValueError:
        raise CensusGeoError(f"Risposta non valida Geography API: {resp.text[:200]}")
    header, *rows = data
    df = pd.DataFrame(rows, columns=header)
    df = df.rename(columns={"GEOID": "zip_code", "zip code tabulation area": "zip_code"})
    return df[['zip_code']]

# Debug
if __name__ == '__main__':
    API_KEY = 'YOUR_KEY'
    states = fetch_states(API_KEY)
    print(states.head())
    places = fetch_places(states.loc[0,'state_fips'], API_KEY)
    print(places.head())
    zips = fetch_zipcodes_for_place(states.loc[0,'state_fips'], places.loc[0,'place_fips'], API_KEY)
    print(zips.head())
