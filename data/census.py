# data/census.py
import requests
import pandas as pd

BASE_URL = "https://api.census.gov/data/2020/acs/acs5"

def fetch_demographics_by_zip(zip_code: str, api_key: str) -> pd.DataFrame:
    """
    Recupera statistiche demografiche ACS5 per il dato ZIP code.
    Richiede ora di passare la api_key esplicitamente.
    """
    vars = {
        "B01003_001E": "population",
        "B01002_001E": "median_age",
        "B19013_001E": "median_income"
    }
    params = {
        "get": ",".join(vars.keys()),
        "for": f"zip code tabulation area:{zip_code}",
        "key": api_key
    }
    resp = requests.get(BASE_URL, params=params)
    resp.raise_for_status()
    data = resp.json()
    if not isinstance(data, list):
        # gestisce eventuale errore API
        raise RuntimeError(f"Errore Census API: {data}")
    header, *rows = data
    df = pd.DataFrame(rows, columns=header)
    df = df.rename(columns=vars).astype({v: "float" for v in vars.values()})
    return df.rename(columns={"zip code tabulation area": "zip_code"})
