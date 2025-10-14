import pandas as pd
import requests
import os
import time
import concurrent.futures
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("API_KEY")

base_dir = os.path.dirname(os.path.abspath(__file__))  
data_dir = os.path.join(base_dir, "..", "data")

def get_budget_tmdb(imdb_id):
    url = f"https://api.themoviedb.org/3/find/{imdb_id}"
    params = {"api_key": api_key, "external_source": "imdb_id"}

    for _ in range(3):
        try:
            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                movie_results = data.get("movie_results")
                if not movie_results:
                    return imdb_id, None

                tmdb_id = movie_results[0].get("id")
                if not tmdb_id:
                    return imdb_id, None

                movie_url = f"https://api.themoviedb.org/3/movie/{tmdb_id}"
                r2 = requests.get(movie_url, params={"api_key": api_key}, timeout=10)
                if r2.status_code == 200:
                    budget = r2.json().get("budget")
                    return imdb_id, budget

                return imdb_id, None

            elif response.status_code == 429:
                time.sleep(1)

        except:
            time.sleep(1)

    return imdb_id, None

def parseUsMoviesWithBudgetWithMultiThreading(dataframe):
    """
    Parse US Movies and get their budget from TMDb using multithreading.
    """
    ids = dataframe['tconst'].tolist()
    budgets = {}
    
    # TMDb has rate limits, so we keep workers conservative or handle 429s in the helper
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        futures = {executor.submit(get_budget_tmdb, mid): mid for mid in ids}
        
        for i, future in enumerate(concurrent.futures.as_completed(futures)):
            mid, budget = future.result()
            if budget:
                budgets[mid] = budget
            
            if (i + 1) % 100 == 0:
                print(f"Processed {i + 1}/{len(ids)} movies...")

    dataframe['budget'] = dataframe['tconst'].map(budgets)
    return dataframe


if __name__ == "__main__":
    us_movies = pd.read_csv(os.path.join(data_dir, "us_movies.csv"))
    us_movies = us_movies[:10]
    us_movies = parseUsMoviesWithBudgetWithMultiThreading(us_movies)
    us_movies.to_csv(os.path.join(data_dir, "us_movies_with_budget_tmdb.csv"), index=False)