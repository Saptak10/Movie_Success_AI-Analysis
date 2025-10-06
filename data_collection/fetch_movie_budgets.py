import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from tqdm import tqdm

BASE_URL = "https://www.the-numbers.com/movie/budgets/all/{}"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
}

def parse_money(value):
    if value is None:
        return None
    value = value.text.strip().replace("$", "").replace(",", "")
    return int(value) if value.isdigit() else None

def scrape_page(start_index):
    url = BASE_URL.format(start_index)
    response = requests.get(url, headers=HEADERS, timeout=15)

    if response.status_code != 200:
        raise Exception(f"Failed at page {start_index}")

    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table")
    rows = table.find_all("tr")[1:]  # skip header

    data = []

    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 6:
            continue

        data.append({
            "rank": int(cols[0].text.strip().replace(",", "")),
            "release_date": cols[1].text.strip(),
            "title": cols[2].text.strip(),
            "budget": parse_money(cols[3]),
            "domestic_gross": parse_money(cols[4]),
            "worldwide_gross": parse_money(cols[5]),
        })

    return data

def scrape_all_movies(start=1, end=7000, step=100):
    all_movies = []

    for i in tqdm(range(start, end + 1, step)):
        try:
            page_data = scrape_page(i)
            all_movies.extend(page_data)
            time.sleep(2)  # IMPORTANT: avoid getting blocked
        except Exception as e:
            print(f"Error at {i}: {e}")
            time.sleep(10)

    return pd.DataFrame(all_movies)