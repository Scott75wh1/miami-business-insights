import streamlit as st
import pandas as pd
import requests
import folium
from streamlit_folium import st_folium
import openai
from fpdf import FPDF
import io

# --- Configurazione API Keys ---
CENSUS_API_KEY = st.secrets["CENSUS_API_KEY"]
YELP_API_KEY = st.secrets["YELP_API_KEY"]
GOOGLE_PLACES_KEY = st.secrets["GOOGLE_PLACES_KEY"]
OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY", None)
if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY

# --- Static Mapping Neighborhoods in Miami to ZIP codes ---
NEIGHBORHOODS = {
    "Downtown": "33131",
    "Wynwood": "33127",
    "South Beach": "33139",
    "Coconut Grove": "33133"
}

# --- Census API: Demographics by ZIP ---
CENSUS_BASE = "https://api.census.gov/data/2020/acs/acs5"
def fetch_demographics_by_zip(zip_code: str, api_key: str) -> pd.DataFrame:
    vars_map = {"B01003_001E":"population","B01002_001E":"median_age","B19013_001E":"median_income"}
    params = {"get": ",".join(vars_map.keys()),"for":f"zip code tabulation area:{zip_code}","key":api_key}
    resp = requests.get(CENSUS_BASE, params=params)
    resp.raise_for_status()
    data = resp.json()
    if len(data) < 2: return pd.DataFrame()
    header, *rows = data
    df = pd.DataFrame(rows, columns=header)
    df = df.rename(columns=vars_map)
    for c in vars_map.values(): df[c] = pd.to_numeric(df[c], errors='coerce')
    return df

# --- Google Trends ---
from pytrends.request import TrendReq
pytrends = TrendReq(hl='en-US', tz=360)
def fetch_google_trends(keyword: str, timeframe: str = 'today 12-m') -> pd.DataFrame:
    pytrends.build_payload([keyword], timeframe=timeframe)
    data = pytrends.interest_over_time()
    if data.empty: return pd.DataFrame()
    df = data.drop(columns=['isPartial'], errors='ignore')
    return df.rename(columns={keyword:'trend_volume'})

# --- Google Reviews (Places API) ---
def fetch_google_reviews(query: str, zip_code: str, radius: int=5000, max_results:int=5) -> pd.DataFrame:
    search_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    details_url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {"query":f"{query} in {zip_code}","key":GOOGLE_PLACES_KEY,"radius":radius}
    res = requests.get(search_url, params=params).json().get('results',[])[:max_results]
    recs = []
    for p in res:
        pid,name,addr = p.get('place_id'),p.get('name'),p.get('formatted_address')
        det = requests.get(details_url,params={"place_id":pid,"key":GOOGLE_PLACES_KEY,"fields":"rating,user_ratings_total"}).json().get('result',{})
        recs.append({'source':'Google','name':name,'rating':det.get('rating'), 'reviews':det.get('user_ratings_total'), 'address':addr})
    return pd.DataFrame(recs)

# --- Yelp Competitors ---
def fetch_yelp_competitors(term: str, zip_code: str, radius: int=5000, limit: int=5) -> pd.DataFrame:
    url = "https://api.yelp.com/v3/businesses/search"
    headers = {"Authorization":f"Bearer {YELP_API_KEY}"}
    params = {'term':term,'location':zip_code,'radius':radius,'limit':limit}
    data = requests.get(url, headers=headers, params=params).json().get('businesses',[])
    recs=[]
    for b in data:
        recs.append({'source':'Yelp','name':b.get('name'),'rating':b.get('rating'),'reviews':b.get('review_count'),'address':' • '.join(b.get('location',{}).get('display_address',[]))})
    return pd.DataFrame(recs)

# --- PDF Report Generation ---
class PDFReport(FPDF):
    def header(self):
        self.set_font('Arial','B',16)
        self.cell(0,10,'Business Insights Report',0,1,'C');self.ln(5)
    def footer(self):
        self.set_y(-15);self.set_font('Arial','I',8);self.cell(0,10,f'Page {self.page_no()}',0,0,'C')
def generate_pdf_report(neighs,search_term,df_demo,df_trends,df_competitors):
    pdf=PDFReport();pdf.add_page();pdf.set_font('Arial',size=12)
    pdf.cell(0,8,f'Quartieri: {", ".join(neighs)}',ln=1)
    pdf.cell(0,8,f'Query: {search_term}',ln=1);pdf.ln(5)
    # Demographics
    pdf.set_font('Arial','B',14);pdf.cell(0,8,'Dati Demografici',ln=1)
    for _,row in df_demo.iterrows():
        for c in ['population','median_age','median_income']:
            pdf.cell(0,6,f'{c}: {row[c]}',ln=1)
    pdf.ln(5)
    # Trends
    if not df_trends.empty:
        pdf.set_font('Arial','B',14);pdf.cell(0,8,'Google Trends (ultimo valore)',ln=1)
        pdf.set_font('Arial',size=12);pdf.cell(0,6,str(df_trends['trend_volume'].iloc[-1]),ln=1)
        pdf.ln(5)
    # Competitors
    if not df_competitors.empty:
        pdf.set_font('Arial','B',14);pdf.cell(0,8,'Competitor',ln=1)
        pdf.set_font('Arial',size=12)
        for _,r in df_competitors.iterrows():
            pdf.cell(0,6,f"[{r['source']}] {r['name']} - Rating:{r['rating']}, Reviews:{r['reviews']}",ln=1)
    buf=io.BytesIO();pdf.output(buf);buf.seek(0);return buf.read()

# --- STREAMLIT UI ---
st.set_page_config(page_title='Miami Business Analyzer',layout='wide')
st.title('Miami Business Opportunity Analyzer 🏝️')

# Sidebar: select neighborhoods
st.sidebar.header('Seleziona Quartieri (Miami)')
sel = st.sidebar.multiselect('Quartieri:', list(NEIGHBORHOODS.keys()), default=['Downtown'])

# Sidebar: sector & sources
st.sidebar.header('Settore e Fonti')
category = st.sidebar.selectbox('Categoria:', ['Ristorazione','Retail','Servizi','Personal Care','Altro'])
custom = st.sidebar.text_input('Query personalizzata:', '')
search_term = custom.strip() or category
enable_demo = st.sidebar.checkbox('Dati Demografici', True)
enable_trends = st.sidebar.checkbox('Google Trends', True)
enable_comp = st.sidebar.checkbox('Competitor', True)
enable_ai = st.sidebar.checkbox('Analisi AI', True)

if st.sidebar.button('Analizza'):
    # Demographics
    df_demo = pd.DataFrame()
    if enable_demo:
        dfs=[]
        for n in sel:
            z=NEIGHBORHOODS[n];df=fetch_demographics_by_zip(z,CENSUS_API_KEY)
            if not df.empty:df['neighborhood']=n;dfs.append(df)
        df_demo = pd.concat(dfs,ignore_index=True) if dfs else pd.DataFrame()
    # Trends
    df_trends = pd.DataFrame()
    if enable_trends:
        df_trends = fetch_google_trends(search_term)
    # Competitors
    df_comp = pd.DataFrame()
    if enable_comp:
        comps=[]
        for n in sel:
            z=NEIGHBORHOODS[n]
            comps.append(fetch_google_reviews(search_term,z))
            comps.append(fetch_yelp_competitors(search_term,z))
        df_comp = pd.concat(comps,ignore_index=True) if comps else pd.DataFrame()

    # Tabs
    tabs = st.tabs(['Demografici','Trends','Competitor','Mappa','AI Analysis'])
    if enable_demo:
        with tabs[0]:
            st.subheader('Dati Demografici')
            if not df_demo.empty: st.dataframe(df_demo)
            else: st.warning('No demographic data available.')
    if enable_trends:
        with tabs[1]: st.subheader('Google Trends');
        if not df_trends.empty: st.line_chart(df_trends['trend_volume'])
        else: st.warning('No trends data available.')
    if enable_comp:
        with tabs[2]: st.subheader('Competitor');
        if not df_comp.empty: st.dataframe(df_comp)
        else: st.warning('No competitor data available.')
    with tabs[3]:
        st.subheader('Mappa')
        m=folium.Map(location=[25.7617,-80.1918],zoom_start=12)
        st_folium(m)
    if enable_ai:
        with tabs[4]:
            st.subheader('Analisi AI')
            if df_comp.empty: st.warning('No competitor data for AI analysis.')
            else:
                prompt=f"Analizza questi competitor per '{search_term}':"
                for _,r in df_comp.iterrows(): prompt+=f"\n- [{r['source']}] {r['name']} (rating {r['rating']}, reviews {r['reviews']})"
                with st.spinner('AI analysis in progress...'):
                    resp=openai.ChatCompletion.create(model='gpt-4',messages=[{'role':'user','content':prompt}],max_tokens=500)
                    st.markdown(resp.choices[0].message.content)

    # Export PDF\ n    if st.sidebar.button('Esporta PDF'):
        pdf_bytes=generate_pdf_report(sel,search_term,df_demo,df_trends,df_comp)
        st.sidebar.download_button('Download PDF',data=pdf_bytes,file_name='report.pdf',mime='application/pdf')
