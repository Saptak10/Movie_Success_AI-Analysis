import requests
import pandas as pd
import time

WIKIDATA_SPARQL_URL = "https://query.wikidata.org/sparql"

# -------------------------------------------------------------------------
# Utility: Run SPARQL Query
# -------------------------------------------------------------------------
def run_sparql(query):
    headers = {"Accept": "application/sparql-results+json"}
    response = requests.get(WIKIDATA_SPARQL_URL, params={'query': query}, headers=headers)
    response.raise_for_status()
    return response.json()

# -------------------------------------------------------------------------
# Field Scrapers
# -------------------------------------------------------------------------
def get_list_field(imdb_id, predicate, var_name):
    query = f"""
    SELECT ?{var_name}Label WHERE {{
      ?movie wdt:P345 "{imdb_id}".
      ?movie wdt:{predicate} ?{var_name}.
      SERVICE wikibase:label {{
        bd:serviceParam wikibase:language "en".
      }}
    }}
    """
    data = run_sparql(query)
    return [row[f"{var_name}Label"]["value"] for row in data["results"]["bindings"]]

def get_single_field(imdb_id, predicate, var_name):
    query = f"""
    SELECT ?{var_name} WHERE {{
      ?movie wdt:P345 "{imdb_id}".
      ?movie wdt:{predicate} ?{var_name}.
    }}
    """
    data = run_sparql(query)
    if data["results"]["bindings"]:
        return data["results"]["bindings"][0][var_name]["value"]
    return None

# Specialized wrappers:
def get_actors(id): return get_list_field(id, "P161", "actor")
def get_director(id): return get_list_field(id, "P57", "director")
def get_production(id): return get_list_field(id, "P272", "company")
def get_budget(id): 
    val = get_single_field(id, "P2130", "budget")
    return float(val) if val else None
def get_release_date(id):
    v = get_single_field(id, "P577", "date")
    return v[:10] if v else None
def get_genre(id): return get_list_field(id, "P136", "genre")
def get_mpaa(id): return get_list_field(id, "P1657", "rating")
def get_runtime(id):
    v = get_single_field(id, "P2047", "runtime")
    return int(float(v)) if v else None

# -------------------------------------------------------------------------
# Load CSV and Scrape
# -------------------------------------------------------------------------
df = pd.read_csv("us_movies_with_reviews.csv")
imdb_ids = df["tconst"].dropna().unique()

results = []

for imdb_id in imdb_ids:
    print(f"Processing {imdb_id}...")
    try:
        result = {
            "IMDb ID": imdb_id,
            "Actors": get_actors(imdb_id),
            "Director": get_director(imdb_id),
            "Production House": get_production(imdb_id),
            "Budget": get_budget(imdb_id),
            "Release Date": get_release_date(imdb_id),
            "Genre": get_genre(imdb_id),
            "MPAA Rating": get_mpaa(imdb_id),
            "Runtime": get_runtime(imdb_id),
        }
        results.append(result)
    except Exception as e:
        print(f"Error for {imdb_id}: {e}")

    time.sleep(1)  # avoid Wikidata rate limits

output_df = pd.DataFrame(results)
output_df.to_csv("movie_metadata_enriched.csv", index=False)

print("Scraping Completed! Saved as movie_metadata_enriched.csv")