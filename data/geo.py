# Modulo di geografia statico per la prima versione

# Mapping statico delle città supportate alle loro liste di ZIP code principali
CITY_ZIP_MAP = {
    "Miami": {"state": "FL", "zips": ["33101", "33131", "33132"]},
    "New York": {"state": "NY", "zips": ["10001", "10002", "10003"]},
    "Los Angeles": {"state": "CA", "zips": ["90001", "90002", "90003"]},
    "Chicago": {"state": "IL", "zips": ["60601", "60602", "60603"]},
    "Houston": {"state": "TX", "zips": ["77001", "77002", "77003"]},
    "Phoenix": {"state": "AZ", "zips": ["85001", "85002", "85003"]}
}

import pandas as pd


def get_supported_states():
    """
    Ritorna la lista degli stati disponibili per le città supportate.
    """
    return sorted({info["state"] for info in CITY_ZIP_MAP.values()})


def get_cities_for_state(state: str) -> pd.DataFrame:
    """
    Dato uno stato (codice FIPS a due lettere), restituisce un DataFrame con le città.
    Colonne: city_name
    """
    cities = [city for city, info in CITY_ZIP_MAP.items() if info["state"] == state]
    return pd.DataFrame(cities, columns=["city_name"])


def get_zips_for_city(city: str) -> pd.DataFrame:
    """
    Dato il nome di una città supportata, restituisce un DataFrame con i suoi ZIP code.
    Colonna: zip_code
    """
    zips = CITY_ZIP_MAP.get(city, {}).get("zips", [])
    return pd.DataFrame(zips, columns=["zip_code"])
