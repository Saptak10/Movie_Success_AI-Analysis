import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
import random

# Constants
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "data")
INPUT_FILE = os.path.join(DATA_DIR, "us_movies.csv")
OUTPUT_FILE = os.path.join(DATA_DIR, "us_movies_with_revenue_mojo.csv")

# Headers to mimic a browser and avoid 403 Forbidden
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9"
}

def get_mojo_revenue(imdb_id):
    """
    Fetches revenue data from Box Office Mojo for a given IMDb ID.
    Returns a dictionary with Domestic, International, and Worldwide revenue.
    """
    url = f"https://www.boxofficemojo.com/title/{imdb_id}/"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code != 200:
            # 404 means page not found, other codes might be blocks or server errors
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        revenue_data = {
            'domestic_revenue': None,
            'international_revenue': None,
            'worldwide_revenue': None
        }
        
        # Box Office Mojo usually puts the main grosses in a specific div
        # Class: a-section a-spacing-none mojo-performance-summary-table
        performance_div = soup.find('div', class_='a-section a-spacing-none mojo-performance-summary-table')
        
        if performance_div:
            # The structure usually has spans with class 'money'
            # We need to be careful about which money corresponds to which category
            # The layout is often:
            # Domestic (label) -> Money
            # International (label) -> Money
            # Worldwide (label) -> Money
            
            # Let's look for the rows
            rows = performance_div.find_all('div', class_='a-section a-spacing-none')
            
            for row in rows:
                text = row.get_text(strip=True)
                money_span = row.find('span', class_='money')
                if not money_span:
                    continue
                
                amount_str = money_span.get_text(strip=True).replace('$', '').replace(',', '')
                try:
                    amount = int(amount_str)
                except ValueError:
                    continue

                if 'Domestic' in text:
                    revenue_data['domestic_revenue'] = amount
                elif 'International' in text:
                    revenue_data['international_revenue'] = amount
                elif 'Worldwide' in text:
                    revenue_data['worldwide_revenue'] = amount
            
            return revenue_data
                
        return None

    except Exception as e:
        print(f"Error fetching {imdb_id}: {e}")
        return None

def main():
    # 1. Load Input Data
    if not os.path.exists(INPUT_FILE):
        print(f"Input file not found: {INPUT_FILE}")
        return

    print(f"Loading movies from {INPUT_FILE}...")
    df = pd.read_csv(INPUT_FILE)
    # df = df[:100]
    
    # 2. Check for existing progress
    if os.path.exists(OUTPUT_FILE):
        print(f"Found existing output file: {OUTPUT_FILE}. Resuming...")
        existing_df = pd.read_csv(OUTPUT_FILE)
        processed_ids = set(existing_df['tconst'])
    else:
        print("Starting fresh...")
        existing_df = pd.DataFrame(columns=['tconst', 'domestic_revenue', 'international_revenue', 'worldwide_revenue'])
        existing_df.to_csv(OUTPUT_FILE, index=False)
        processed_ids = set()

    # 3. Filter movies to process
    movies_to_process = df[~df['tconst'].isin(processed_ids)]
    total_movies = len(movies_to_process)
    print(f"Movies left to process: {total_movies}")

    # 4. Processing Loop
    batch_size = 10
    batch_data = []
    
    for index, row in movies_to_process.iterrows():
        imdb_id = row['tconst']
        title = row['primaryTitle']
        
        print(f"[{index}/{len(df)}] Fetching {title} ({imdb_id})...", end="", flush=True)
        
        revenue = get_mojo_revenue(imdb_id)
        
        result = {
            'tconst': imdb_id,
            'domestic_revenue': revenue['domestic_revenue'] if revenue else None,
            'international_revenue': revenue['international_revenue'] if revenue else None,
            'worldwide_revenue': revenue['worldwide_revenue'] if revenue else None
        }
        
        if revenue:
            print(f" Found: ${revenue.get('worldwide_revenue', 'N/A')}")
        else:
            print(" No data")
            
        batch_data.append(result)
        
        # Save batch
        if len(batch_data) >= batch_size:
            batch_df = pd.DataFrame(batch_data)
            batch_df.to_csv(OUTPUT_FILE, mode='a', header=False, index=False)
            batch_data = [] # Clear batch
            
        # Rate limiting - Random delay between 1 and 2 seconds
        time.sleep(random.uniform(1.0, 2.0))

    # Save remaining
    if batch_data:
        batch_df = pd.DataFrame(batch_data)
        batch_df.to_csv(OUTPUT_FILE, mode='a', header=False, index=False)

    print("Done!")

if __name__ == "__main__":
    main()
