import requests
import pandas as pd

BASE_URL = "https://api.census.gov/data/2020/acs/acs5"

class CensusAPIError(Exception):
    pass

def fetch_demographics_by_zip(zip_code: str, api_key: str) -> pd.DataFrame:
    """
    Recupera statistiche demografiche ACS5 per il dato ZIP code.
    Restituisce un DataFrame con variabili: population, median_age, median_income.
    Solleva CensusAPIError in caso di problemi.
    """
    vars_map = {
        "B01003_001E": "population",
        "B01002_001E": "median_age",
        "B19013_001E": "median_income"
    }
    params = {
        "get": ",".join(vars_map.keys()),
        "for": f"zip code tabulation area:{zip_code}",
        "key": api_key
    }
    resp = requests.get(BASE_URL, params=params)
    # Verifica status HTTP
    if resp.status_code != 200:
        raise CensusAPIError(f"HTTP {resp.status_code}: {resp.text}")
    # Controlla che la risposta sia JSON valido
    try:
        data = resp.json()
    except ValueError:
        raise CensusAPIError(f"Risposta non valida dalla Census API: {resp.text[:200]}")
    # Verifica formato dei dati
    if not isinstance(data, list) or len(data) < 2:
        raise CensusAPIError(f"Nessun dato per ZIP {zip_code}: {data}")
    header, *rows = data
    df = pd.DataFrame(rows, columns=header)
    # Converti e rinomina
    df = df.rename(columns=vars_map)
    for col in vars_map.values():
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df = df.rename(columns={"zip code tabulation area": "zip_code"})
    return df

# Test in locale
if __name__ == '__main__':
    try:
        df = fetch_demographics_by_zip('33101', api_key='YOUR_KEY_HERE')
        print(df)
    except CensusAPIError as e:
        print(f"Errore Census API: {e}")
