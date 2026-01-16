import requests
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("API_KEY")

print(f"API Key present: {bool(api_key)}")

def get_budget_tmdb(imdb_id):
    print(f"Checking {imdb_id}...")
    url = f"https://api.themoviedb.org/3/find/{imdb_id}"
    params = {"api_key": api_key, "external_source": "imdb_id"}

    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"Find response status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            movie_results = data.get("movie_results")
            if not movie_results:
                print("No movie results found in find endpoint")
                return imdb_id, None

            tmdb_id = movie_results[0].get("id")
            print(f"TMDB ID: {tmdb_id}")
            if not tmdb_id:
                return imdb_id, None

            movie_url = f"https://api.themoviedb.org/3/movie/{tmdb_id}"
            r2 = requests.get(movie_url, params={"api_key": api_key}, timeout=10)
            print(f"Details response status: {r2.status_code}")
            if r2.status_code == 200:
                budget = r2.json().get("budget")
                print(f"Budget found: {budget}")
                return imdb_id, budget
            else:
                print(f"Error fetching details: {r2.text}")

            return imdb_id, None

        elif response.status_code == 429:
            print("Rate limited")
        else:
            print(f"Error: {response.status_code} {response.text}")

    except Exception as e:
        print(f"Exception: {e}")

    return imdb_id, None

# Test with Inception (should have budget)
print("\n--- Testing Inception (tt1375666) ---")
get_budget_tmdb("tt1375666")

# Test with The Tango of the Widower (tt0062336) (missing in csv)
print("\n--- Testing tt0062336 ---")
get_budget_tmdb("tt0062336")
