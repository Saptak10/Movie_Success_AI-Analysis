import pandas as pd
import requests
import os
import time
import concurrent.futures
import csv

from dotenv import load_dotenv
import os

from parseReviewsOnAndBeforeReleaseDate import add_review_to_dataframe
from parseRevenueMojo import add_revenue_to_dataframe

load_dotenv()
api_key = os.getenv("API_KEY")


base_dir = os.path.dirname(os.path.abspath(__file__))  
data_dir = os.path.join(base_dir, "..", "data")        

basics_path = os.path.join(data_dir, "title.basics.tsv")
akas_path   = os.path.join(data_dir, "title.akas.tsv")

def parseUsMoviesOnly():
    """
    Parse US Movies that are relased between 2015 and 2025.
    
    """
    df = pd.read_csv(basics_path, sep="\t", dtype=str)

    movies = df[df['titleType'] == 'movie']
    movie_data = movies[['tconst','primaryTitle', 'startYear']]
    movie_data = movie_data[movie_data['startYear'] != '\\N']
    movie_data['startYear'] = movie_data['startYear'].astype(int)
    movie_data = movie_data[(movie_data['startYear'] >= 2015) & (movie_data['startYear'] < 2026)]


    akas = pd.read_csv(akas_path, sep="\t", dtype=str)
    akas = akas[['title', 'region', 'titleId', 'isOriginalTitle']]
    # us_titles = akas[(akas['region'] == 'US') & (akas['isOriginalTitle'] == '1')]
    us_titles = akas[(akas['region'] == 'US')]
    us_movies = movie_data.merge(us_titles, left_on='tconst', right_on='titleId', how='inner')

    us_movies = us_movies[['tconst','primaryTitle','startYear','title','region', 'isOriginalTitle']]

    #need to investigate why duplicates are there
    us_movies = us_movies.drop_duplicates(subset=["tconst"], keep="first")


    us_movies.to_csv(os.path.join(data_dir, "us_movies.csv"), index=False)



def get_release_dates(imdb_ids):
    ids_string = " ".join(f'"{id}"' for id in imdb_ids)
    
    query = f"""
    SELECT ?imdb_id ?releaseDate ?placeLabel WHERE {{
        VALUES ?imdb_id {{ {ids_string} }}
        ?film wdt:P345 ?imdb_id; p:P577 ?statement.
        ?statement ps:P577 ?releaseDate.
        OPTIONAL {{ ?statement pq:P291 ?place. }}
        SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
    }}
    """
    
    url = "https://query.wikidata.org/sparql"
    headers = {"Accept": "application/sparql-results+json"}
    
    for attempt in range(3):
        try:
            r = requests.get(url, params={"query": query}, headers=headers, timeout=60)
            if r.status_code == 200:
                results = {}
                for item in r.json()["results"]["bindings"]:
                    mid = item["imdb_id"]["value"]
                    date = item["releaseDate"]["value"].split("T")[0]
                    place = item.get("placeLabel", {}).get("value", "").lower()
                    if mid not in results or place == 'united states':
                        results[mid] = date
                return results
            elif r.status_code == 429:
                time.sleep(2)
        except:
            time.sleep(1)
            
    return {}

def get_release_date_tmdb(imdb_id):
    url = f"https://api.themoviedb.org/3/find/{imdb_id}"
    params = {
        "api_key": api_key,
        "external_source": "imdb_id"
    }
    
    for _ in range(3):
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("movie_results"):
                    return imdb_id, data["movie_results"][0].get("release_date")
                return imdb_id, None
            elif response.status_code == 429:
                time.sleep(1)
        except:
            time.sleep(1)
    return imdb_id, None

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

def get_revenue_tmdb(imdb_id):
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
                    revenue = r2.json().get("revenue")
                    return imdb_id, revenue

                return imdb_id, None

            elif response.status_code == 429:
                time.sleep(1)

        except:
            time.sleep(1)

    return imdb_id, None

def parseUsMoviesWithReleaseDatesWithMultiThreading(dataframe):
    """
    Parse US Movies and get their release dates from TMDb using multithreading.
    """
    ids = dataframe['tconst'].tolist()
    release_dates = {}
    
    # TMDb has rate limits, so we keep workers conservative or handle 429s in the helper
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(get_release_date_tmdb, mid): mid for mid in ids}
        
        for i, future in enumerate(concurrent.futures.as_completed(futures)):
            mid, date = future.result()
            if date:
                release_dates[mid] = date
            
            if (i + 1) % 100 == 0:
                print(f"Processed {i + 1}/{len(ids)} movies...")

    dataframe['release_date'] = dataframe['tconst'].map(release_dates)
    return dataframe


def parseUsMoviesWithBudgetWithMultiThreading(dataframe):
    """
    Parse US Movies and get their release dates from TMDb using multithreading.
    """
    ids = dataframe['tconst'].tolist()
    budgets = {}
    
    # TMDb has rate limits, so we keep workers conservative or handle 429s in the helper
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        futures = {executor.submit(get_budget_tmdb, mid): mid for mid in ids}
        
        for i, future in enumerate(concurrent.futures.as_completed(futures)):
            mid, budget = future.result()
            if budget is not None:
                budgets[mid] = budget
            
            if (i + 1) % 100 == 0:
                print(f"Processed {i + 1}/{len(ids)} movies...")

    dataframe['budget'] = dataframe['tconst'].map(budgets)
    return dataframe

def parseUsMoviesWithRevenueWithMultiThreading(dataframe):
    """
    Parse US Movies and get their release dates from TMDb using multithreading.
    """
    ids = dataframe['tconst'].tolist()
    revenues = {}
    
    # TMDb has rate limits, so we keep workers conservative or handle 429s in the helper
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        futures = {executor.submit(get_revenue_tmdb, mid): mid for mid in ids}
        
        for i, future in enumerate(concurrent.futures.as_completed(futures)):
            mid, revenue = future.result()
            if revenue is not None:
                revenues[mid] = revenue
            
            if (i + 1) % 100 == 0:
                print(f"Processed {i + 1}/{len(ids)} movies...")

    dataframe['revenue'] = dataframe['tconst'].map(revenues)
    return dataframe

if __name__ == "__main__":
    
    #saving a base file inorder to prevent re running join each time i.e a checkpoint
    # parseUsMoviesOnly()

    # us_movies = pd.read_csv(os.path.join(data_dir, "us_movies.csv"))
    # # us_movies = us_movies[:1000]
    # us_movies = parseUsMoviesWithReleaseDatesWithMultiThreading(us_movies)
    # us_movies.to_csv(os.path.join(data_dir, "us_movies_with_release_dates_tmdb.csv"), index=False)

    # total = 66496
    # 7 days = 66354 
    # 30 days = 66333 

    #-------------------------------------------------------------------

    # us_movies = pd.read_csv(os.path.join(data_dir, "us_movies_with_release_dates_tmdb.csv"))
    # us_movies = us_movies.dropna(subset=['release_date'])
    # # us_movies = us_movies[us_movies['tconst'] == 'tt10236164']
    # us_movies = add_review_to_dataframe(us_movies)
    # us_movies.to_csv(os.path.join(data_dir, "us_movies_with_reviews.csv"), index=False)



    #-------------------------------------------------------------------

    # us_movies = pd.read_csv(os.path.join(data_dir, "us_movies_with_reviews.csv"))
    # us_movies = us_movies[:10]
    # us_movies = parseUsMoviesWithBudgetWithMultiThreading(us_movies)
    # us_movies.to_csv(os.path.join(data_dir, "us_movies_with_budget_tmdb.csv"), index=False)

    #------------------------------------------------------------------------------

    # us_movies = pd.read_csv(os.path.join(data_dir, "us_movies_with_reviews.csv"))
    # # us_movies = us_movies[:10]
    # us_movies = parseUsMoviesWithRevenueWithMultiThreading(us_movies)
    # us_movies.to_csv(os.path.join(data_dir, "us_movies_with_revenue_tmdb.csv"), index=False)

    #------------------------------------------------------------------------------

    # us_movies = pd.read_csv(os.path.join(data_dir, "us_movies_with_reviews.csv"))
    # # us_movies = us_movies[:1000]
    # us_movies = add_revenue_to_dataframe(us_movies)
    # us_movies.to_csv(os.path.join(data_dir, "us_movies_with_revenue_and_budget_3_source.csv"), index=False)

    #------------------------------------------------------------------------------
    us_movies = pd.read_csv(os.path.join(data_dir, "us_movies_with_revenue_and_budget_3_source.csv"))

    basics_cols = ['tconst', 'primaryTitle', 'runtimeMinutes', 'genres', 'isAdult']

    basic_df = pd.read_csv(os.path.join(data_dir,
            "title.basics.tsv"),
            sep='\t',
            na_values='\\N',      # Handle IMDb's null format
            # compression='gzip', <-- REMOVED (Files are unzipped)
            usecols=basics_cols,
            quoting=3,            # Fix parsing errors for quotes
            low_memory=False
        )
    #remove rows with no revenue as we proceed with regression task
    us_movies = us_movies[us_movies['revenue'].notna()]
    
    us_movies = us_movies.join(basic_df.set_index('tconst'), on='tconst', how='left', rsuffix='_drop')
    us_movies.to_csv(os.path.join(data_dir, "us_movies_with_basics.csv"), index=False)
    
    #------------------------------------------------------------------------------
    us_movies = pd.read_csv(os.path.join(data_dir, "us_movies_with_basics.csv"))
    crew_cols = ['tconst', 'directors', 'writers']
    crew_df = pd.read_csv(os.path.join(data_dir,
            "title.crew.tsv"),
            sep='\t',
            na_values='\\N',      # Handle IMDb's null format
            # compression='gzip', <-- REMOVED (Files are unzipped)
            usecols=crew_cols,
            quoting=3,            # Fix parsing errors for quotes
            low_memory=False
        )
    us_movies = us_movies.join(crew_df.set_index('tconst'), on='tconst', how='left', rsuffix='_drop')
    us_movies.to_csv(os.path.join(data_dir, "us_movies_with_crew.csv"), index=False)
    # ------------------------------------------------------------------------------
    
    us_movies = pd.read_csv(os.path.join(data_dir, "us_movies_with_crew.csv"))
    name_basics_path = os.path.join(data_dir, "name.basics.tsv")

    directors_ids = us_movies['directors'].dropna().str.split(',').explode()
    writers_ids = us_movies['writers'].dropna().str.split(',').explode()
    needed_nconsts = set(directors_ids).union(set(writers_ids))

     # Build a dictionary mapping nconst -> primaryName
    # name.basics.tsv is large, so read in chunks and filter immediately
    nconst_to_name = {}
    chunk_size = 100000
    
    with pd.read_csv(name_basics_path, sep='\t', usecols=['nconst', 'primaryName'], 
                     dtype=str, na_values='\\N', quoting=3, chunksize=chunk_size) as reader:
        for chunk in reader:
            matched = chunk[chunk['nconst'].isin(needed_nconsts)]
            if not matched.empty:
                nconst_to_name.update(zip(matched['nconst'], matched['primaryName']))

    #  Helper function to map comma-separated IDs to comma-separated Names
    def resolve_names(id_str):
        if pd.isna(id_str):
            return None
        ids = id_str.split(',')
        # Use the name if found, otherwise keep the ID
        names = [nconst_to_name.get(x, x) for x in ids]
        joined_names = ",".join(names)
        # return f'"{joined_names}"'
        return joined_names

    us_movies['director_names'] = us_movies['directors'].apply(resolve_names)
    us_movies['writer_names'] = us_movies['writers'].apply(resolve_names)


    #------------------------------------------------------------------------------

    # us_movies = pd.read_csv(os.path.join(data_dir, "us_movies_with_names.csv"))
    # Add cast members only 
    df_with_cast = pd.read_csv(os.path.join(data_dir, "us_movies_with_reviews_cast.csv"))
    # print(df_with_cast.columns)
    df_with_cast = df_with_cast[['tconst', 'cast_members']]
    us_movies = us_movies.join(df_with_cast.set_index('tconst'), on='tconst', how='left', rsuffix='_drop')
    
    # Format names for TF-IDF: "Christopher Nolan, Jonathan Nolan" -> "Christopher_Nolan Jonathan_Nolan"
    def format_names(names_str):
        if pd.isna(names_str):
            return ""
        # Split by comma, strip whitespace, replace spaces with underscores
        return " ".join([n.strip().replace(" ", "_") for n in names_str.split(',')])

    def format_cast_names(names_str):
        if pd.isna(names_str):
            return ""
        # Remove brackets and quotes if present (e.g., "['Actor A', 'Actor B']")
        cleaned = names_str.replace("[", "").replace("]", "").replace("'", "").replace('"', "")
        # Split by comma, strip whitespace, replace spaces with underscores
        return " ".join([n.strip().replace(" ", "_") for n in cleaned.split(',')])

    us_movies['director_names'] = us_movies['director_names'].apply(format_names)
    us_movies['writer_names'] = us_movies['writer_names'].apply(format_names)
    us_movies['cast_members'] = us_movies['cast_members'].apply(format_cast_names)

    us_movies.to_csv(os.path.join(data_dir, "us_movies_final_with_cast_directors.csv"), index=False, quoting=csv.QUOTE_NONNUMERIC)