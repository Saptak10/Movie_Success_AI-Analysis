import re
import time
import random
import unicodedata
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def create_session():
    session = requests.Session()

    retries = Retry(
        total=5,
        backoff_factor=2,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )

    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)

    session.headers.update({
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "en-US,en;q=0.9"
    })

    return session


session = create_session()


def build_slug(title):
    title = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode()
    title = re.sub(r"[^\w\s-]", "", title)
    return re.sub(r"\s+", "-", title.strip())


import pandas as pd

def candidate_urls(title, year):
    slug = build_slug(title)

    urls = [
        f"https://www.the-numbers.com/movie/{slug}"
    ]

    # add year-based URL only if year is valid
    if pd.notna(year):
        try:
            year_int = int(year)
            urls.append(
                f"https://www.the-numbers.com/movie/{slug}-({year_int})"
            )
        except Exception:
            pass

    return urls

def fetch_numbers_page(title, year):
    for url in candidate_urls(title, year):
        try:
            r = session.get(url, timeout=40, allow_redirects=False)
            if r.status_code == 200:
                return url, r.text
        except Exception:
            pass
    return None, None

def normalize_key(text):
    return (
        text.replace("\xa0", " ")
            .replace(":", "")
            .strip()
            .lower()
    )

def extract_money(text):
    match = re.search(r"\$([\d,]+)", text)
    if match:
        return int(match.group(1).replace(",", ""))
    return None

def find_section_table(soup, section_title):
    """
    Finds the first table that follows a section title text
    like 'Lead Ensemble Members' or 'Production and Technical Credits'
    """
    for el in soup.find_all(string=True):
        if el.strip().lower() == section_title.lower():
            parent = el.parent
            table = parent.find_next("table")
            if table:
                return table
    return None

def extract_lead_cast(soup, max_cast=15):
    section_titles = [
        "Lead Ensemble Members",
        "Principal Cast",
        "Cast"
    ]

    table = None
    for title in section_titles:
        table = find_section_table(soup, title)
        if table:
            break

    if not table:
        return None

    cast = []
    for row in table.find_all("tr"):
        cells = row.find_all("td")
        if not cells:
            continue

        actor = cells[0].find("a")
        if actor:
            cast.append(actor.text.strip())

        if len(cast) >= max_cast:
            break

    return ", ".join(cast) if cast else None


def extract_directors(soup):
    table = find_section_table(soup, "Production and Technical Credits")
    if not table:
        return None

    directors = []

    for row in table.find_all("tr"):
        cells = row.find_all("td")
        if len(cells) < 3:
            continue

        name = cells[0].find("a")
        role = cells[2].text.strip().lower()

        if name and role == "director":
            directors.append(name.text.strip())

    return ", ".join(directors) if directors else None


import pandas as pd

def scrape_the_numbers_metadata(title, year):
    url, html = fetch_numbers_page(title, year)
    if not html:
        return pd.DataFrame()  # empty DF if page not found

    soup = BeautifulSoup(html, "html.parser")

    data = {
        "title": title,
        "release_year": year,
        "movie_url": url,
        "runtime_minutes": None,
        "genre": None,
        "creative_type": None,
        "franchise": None,
        "production_budget": None,
        "production_companies": None,
        "production_countries": None,
        "languages": None,
        "cast": None,
        "director": None
    }

    # ---------- Movie Details tables ----------
    for table in soup.find_all("table"):
        for row in table.find_all("tr"):
            tds = row.find_all("td")
            if len(tds) < 2:
                continue

            key = normalize_key(tds[0].text)
            val_cell = tds[1]

            value = ", ".join(a.text.strip() for a in val_cell.find_all("a"))
            if not value:
                value = val_cell.text.strip()

            if "running time" in key:
                data["runtime_minutes"] = int(value.split()[0])

            elif key == "genre":
                data["genre"] = value

            elif "creative type" in key:
                data["creative_type"] = value

            elif key == "franchise":
                data["franchise"] = value

            elif "production budget" in key:
                data["production_budget"] = extract_money(value)

            elif "production/financing" in key or "production companies" in key:
                data["production_companies"] = value

            elif key == "production countries":
                data["production_countries"] = value

            elif key == "languages":
                data["languages"] = value

    # ---------- Cast & Crew ----------
    data["cast"] = extract_lead_cast(soup)
    data["director"] = extract_directors(soup)

    return data
