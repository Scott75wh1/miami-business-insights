from pytrends.request import TrendReq, ResponseError
import pandas as pd

# Inizializza PyTrends
pytrends = TrendReq(hl='en-US', tz=360)

def fetch_google_trends(keyword: str,
                        timeframe: str = 'today 12-m',
                        geo: str = 'US-FL-12086') -> pd.DataFrame:
    """
    Recupera i dati di Google Trends per una keyword:
    - keyword: termine di ricerca
    - timeframe: intervallo (es. 'now 7-d', 'today 12-m')
    - geo: area geografica (DMA Miami-Fort Lauderdale = 'US-FL-12086')
    Ritorna un DataFrame con indice temporale e colonna 'trend_volume'.
    Gestisce errori di risposta di Google Trends restituendo DataFrame vuoto.
    """
    try:
        pytrends.build_payload([keyword], timeframe=timeframe, geo=geo)
        data = pytrends.interest_over_time()
    except ResponseError as e:
        # Loggare l'errore, restituire DataFrame vuoto
        print(f"Google Trends ResponseError: {e}")
        return pd.DataFrame()

    if data.empty:
        return pd.DataFrame()

    # Rimuove la colonna isPartial
    return data.drop(columns=['isPartial'], errors='ignore') \
               .rename(columns={keyword: 'trend_volume'})
