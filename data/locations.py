import requests
import pandas as pd

# Base URL dell'API ACS5 per geografie
BASE_URL = "https://api.census.gov/data/2020/acs/acs5"

class CensusGeoError(Exception):
    """Eccezione per errori nelle chiamate Geography API"""
    pass


def fetch_states(api_key: str) -> pd.DataFrame:
    """
    Recupera l'elenco degli Stati USA con i loro codici FIPS.
    Restituisce un DataFrame con colonne: state_name, state_fips.
    """
    params = {
        "get": "NAME,STATE",
        "for": "state:*","
        "key": api_key
    }
    try:
        resp = requests.get(BASE_URL, params=params)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        raise CensusGeoError(f"Errore fetch_states: {e}")

    header, *rows = data
    df = pd.DataFrame(rows, columns=header)
    return df.rename(columns={"NAME": "state_name", "STATE": "state_fips"})


def fetch_places(state_fips: str, api_key: str) -> pd.DataFrame:
    """
    Dato il FIPS di uno Stato, recupera i comuni (place) di quello Stato.
    Restituisce un DataFrame con colonne: place_name, place_fips.
    """
    params = {
        "get": "NAME,PLACE",
        "for": "place:*","
        "in": f"state:{state_fips}",
        "key": api_key
    }
    try:
        resp = requests.get(BASE_URL, params=params)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        raise CensusGeoError(f"Errore fetch_places: {e}")

    header, *rows = data
    df = pd.DataFrame(rows, columns=header)
    return df.rename(columns={"NAME": "place_name", "PLACE": "place_fips"})


def fetch_zipcodes_for_place(state_fips: str, place_fips: str, api_key: str) -> pd.DataFrame:
    """
    Dato state_fips e place_fips, recupera i ZIP code tabulation areas (ZCTAs) all'interno del comune.
    Restituisce un DataFrame con colonna: zip_code.
    """
    params = {
        "get": "GEOID",
        "for": "zip code tabulation area:*","
        "in": f"state:{state_fips}+place:{place_fips}",
        "key": api_key
    }
    try:
        resp = requests.get(BASE_URL, params=params)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        raise CensusGeoError(f"Errore fetch_zipcodes_for_place: {e}")

    header, *rows = data
    df = pd.DataFrame(rows, columns=header)
    return df.rename(columns={"GEOID": "zip_code"})
