import os
import requests
import pandas as pd
from dotenv import load_dotenv

# Carica le variabili d'ambiente dai Secrets (in Codespaces/GitHub Actions)
load_dotenv()

CENSUS_API_KEY = os.getenv("CENSUS_API_KEY")
BASE_URL = "https://api.census.gov/data/2020/acs/acs5"

def fetch_demographics_by_zip(zip_code: str) -> pd.DataFrame:
    """
    Recupera statistiche demografiche ACS5 per il dato ZIP code.
    Restituisce un DataFrame con nome area e variabili selezionate.
    """
    # Variabili di esempio: popolazione totale, età mediana, reddito mediano
    vars = {
        "B01003_001E": "population",
        "B01002_001E": "median_age",
        "B19013_001E": "median_income"
    }

    params = {
        "get": ",".join(vars.keys()),
        "for": f"zip code tabulation area:{zip_code}",
        "key": CENSUS_API_KEY
    }

    resp = requests.get(BASE_URL, params=params)
    resp.raise_for_status()
    data = resp.json()

    # La prima riga è l'intestazione delle chiavi
    header, *rows = data
    df = pd.DataFrame(rows, columns=header)

    # Rinominare e convertire a tipi numerici
    df = df.rename(columns=vars)
    for col in vars.values():
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Sposta il ZIP in colonna
    df = df.rename(columns={"zip code tabulation area": "zip_code"})
    return df

# Test rapido (verrà lanciato solo in locale/Codespace)
if __name__ == "__main__":
    sample = fetch_demographics_by_zip("33101")
    print(sample)
