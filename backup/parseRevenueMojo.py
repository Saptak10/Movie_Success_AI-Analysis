import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
import concurrent.futures
from dotenv import load_dotenv
import re
from curl_cffi import requests as cffi_requests

load_dotenv()
API_KEY = os.getenv("API_KEY")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

def clean_money(money_str):
    """Helper to clean currency strings."""
    try:
        return int(money_str.replace('$', '').replace(',', ''))
    except (ValueError, AttributeError):
        return None

def get_mojo_revenue(imdb_id):
    """Scrapes Box Office Mojo for revenue and budget."""
    url = f"https://www.boxofficemojo.com/title/{imdb_id}/"
    
    for _ in range(3):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=10)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.content, 'html.parser')
                data = {'budget': None, 'revenue': None}
                
                # 1. Get Revenue (Prefer Worldwide, fallback to Domestic)
                perf = soup.find('div', class_='mojo-performance-summary-table')
                if perf:
                    for row in perf.find_all('div', class_='a-section'):
                        text = row.get_text()
                        val = row.find('span', class_='money')
                        amount = clean_money(val.text) if val else None
                        
                        if 'Worldwide' in text: 
                            data['revenue'] = amount
                        elif 'Domestic' in text and not data['revenue']: 
                            data['revenue'] = amount

                # 2. Get Budget
                summary = soup.find('div', class_='mojo-summary-values')
                if summary:
                    for row in summary.find_all('div', class_='a-section'):
                        if 'Budget' in row.get_text():
                            val = row.find('span', class_='money')
                            data['budget'] = clean_money(val.text) if val else None
                
                return data
            elif resp.status_code == 404:
                return None
            time.sleep(1)
        except Exception:
            time.sleep(1)
    return None

def get_tmdb_financials(imdb_id):
    """Fetches financial data from TMDb API."""
    find_url = f"https://api.themoviedb.org/3/find/{imdb_id}"
    movie_url = "https://api.themoviedb.org/3/movie/{}"
    
    for _ in range(3):
        try:
            resp = requests.get(find_url, params={"api_key": API_KEY, "external_source": "imdb_id"}, timeout=10)
            if resp.status_code != 200: continue
            
            results = resp.json().get("movie_results")
            if not results: return None
            
            tmdb_id = results[0]["id"]
            resp = requests.get(movie_url.format(tmdb_id), params={"api_key": API_KEY}, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                budget = data.get("budget")
                revenue = data.get("revenue")
                return {
                    'budget': budget if budget and budget > 0 else None,
                    'revenue': revenue if revenue and revenue > 0 else None
                }
        except Exception:
            time.sleep(1)
    return None

def get_wikidata_financials(imdb_id):
    """Fetches financial data from Wikidata."""
    query = f"""
    SELECT ?budget ?revenue WHERE {{
        ?film wdt:P345 "{imdb_id}".
        OPTIONAL {{ ?film wdt:P2130 ?budget. }}
        OPTIONAL {{ ?film wdt:P2142 ?revenue. }}
    }}
    """
    url = "https://query.wikidata.org/sparql"
    headers = {"Accept": "application/sparql-results+json"}
    
    for _ in range(3):
        try:
            r = requests.get(url, params={"query": query}, headers=headers, timeout=10)
            if r.status_code == 200:
                results = r.json().get("results", {}).get("bindings", [])
                budget = None
                revenue = None
                
                for item in results:
                    if 'budget' in item:
                        try:
                            val = float(item['budget']['value'])
                            if budget is None or val > budget:
                                budget = val
                        except: pass
                    if 'revenue' in item:
                        try:
                            val = float(item['revenue']['value'])
                            if revenue is None or val > revenue:
                                revenue = val
                        except: pass
                
                return {'budget': budget, 'revenue': revenue}
            elif r.status_code == 429:
                time.sleep(2)
        except Exception:
            time.sleep(1)
            
    return None

def slugify(text):
    if not text: return ""
    text = text.replace(':', '').replace("'", "")
    return re.sub(r'[\W_]+', '-', text).strip('-')

def get_the_numbers_financials(imdb_id, title, year):
    """Scrapes The Numbers for revenue and budget using Google Cache and curl_cffi."""
    if not title: return None
    
    slug = slugify(title)
    urls = [
        f"https://www.the-numbers.com/movie/{slug}#tab=summary",
        f"https://www.the-numbers.com/movie/{slug}-({year})#tab=summary"
    ]
    
    for url in urls:
        cache_url = f"http://webcache.googleusercontent.com/search?q=cache:{url}"
        try:
            # Impersonate Chrome to avoid Google blocking
            resp = cffi_requests.get(cache_url, impersonate="chrome110", timeout=5)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.content, 'html.parser')
                data = {'budget': None, 'revenue': None}
                
                tables = soup.find_all('table')
                for table in tables:
                    for row in table.find_all('tr'):
                        row_text = row.get_text()
                        if 'Production Budget' in row_text:
                            val = row.find_all('td')[-1].get_text()
                            data['budget'] = clean_money(val)
                        elif 'Worldwide Box Office' in row_text:
                            val = row.find_all('td')[-1].get_text()
                            data['revenue'] = clean_money(val)
                
                if data['budget'] or data['revenue']:
                    return data
        except Exception:
            pass
            
    return None

def process_movie(tconst, title=None, year=None):
    """Orchestrates data fetching: Mojo -> TMDb -> Wikidata -> The Numbers."""
    data = get_mojo_revenue(tconst) or {'budget': None, 'revenue': None}
    
    # Backfill with TMDb
    if not data['budget'] or not data['revenue']:
        tmdb = get_tmdb_financials(tconst)
        if tmdb:
            data['budget'] = data['budget'] or tmdb.get('budget')
            data['revenue'] = data['revenue'] or tmdb.get('revenue')
            
    # Backfill with Wikidata
    if not data['budget'] or not data['revenue']:
        wiki = get_wikidata_financials(tconst)
        if wiki:
            data['budget'] = data['budget'] or wiki.get('budget')
            data['revenue'] = data['revenue'] or wiki.get('revenue')

    # Backfill with The Numbers (Google Cache)
    if not data['budget'] or not data['revenue']:
        nums = get_the_numbers_financials(tconst, title, year)
        if nums:
            data['budget'] = data['budget'] or nums.get('budget')
            data['revenue'] = data['revenue'] or nums.get('revenue')
            
    return data

def add_revenue_to_dataframe(df, output_path=None):
    processed = set()
    if output_path and os.path.exists(output_path):
        try: processed = set(pd.read_csv(output_path)['tconst'])
        except: pass
    
    to_process = df[~df['tconst'].isin(processed)]
    print(f"Processing {len(to_process)} movies...")
    
    if to_process.empty:
        return pd.read_csv(output_path) if output_path else df

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            executor.submit(process_movie, row['tconst'], row.get('primaryTitle'), row.get('startYear')): row.to_dict() 
            for _, row in to_process.iterrows()
        }
        
        for i, future in enumerate(concurrent.futures.as_completed(futures)):
            row = futures[future]
            try:
                financials = future.result()
                row['revenue'] = financials.get('revenue')
                row['budget'] = financials.get('budget')
            except Exception as e:
                print(f"Error {row['tconst']}: {e}")
            
            results.append(row)
            print(f"Processed {i+1}/{len(to_process)}")
            
            # Batch Save
            if output_path and len(results) >= 10:
                pd.DataFrame(results).to_csv(output_path, mode='a', header=not os.path.exists(output_path), index=False)
                results = []

    # Final Save
    if output_path and results:
        pd.DataFrame(results).to_csv(output_path, mode='a', header=not os.path.exists(output_path), index=False)

    return pd.read_csv(output_path) if output_path else pd.DataFrame(results)
