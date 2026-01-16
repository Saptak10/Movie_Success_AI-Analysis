import pandas as pd
import os
import numpy as np

# --- CONFIGURATION ---
# Path to your unzipped TSV files
BASE_PATH = '/Users/saptakchakraborty/Downloads/Uni Docs/OVGU/1ST SEM/Data Science with Python/Project_IMDB/movie-success-analysis/data/IMDB'
OUTPUT_FILE = os.path.join(BASE_PATH, 'movie_success_dataset.csv')

def load_imdb_file(filename, cols=None):
    """
    Loads unzipped TSV files (.tsv)
    """
    full_path = os.path.join(BASE_PATH, filename)
    print(f"Loading: {filename}...")
    try:
        return pd.read_csv(
            full_path,
            sep='\t',
            na_values='\\N',      # Handle IMDb's null format
            # compression='gzip', <-- REMOVED (Files are unzipped)
            usecols=cols,
            quoting=3,            # Fix parsing errors for quotes
            low_memory=False
        )
    except FileNotFoundError:
        print(f"❌ Error: File not found at {full_path}")
        print(f"   Please ensure the file is named '{filename}' (without .gz)")
        return None

def main():
    print("=== STARTING IMDB DATA EXTRACTION (UNZIPPED) ===\n")

    # 1. LOAD MOVIES (title.basics.tsv)
    print(">>> Step 1: Loading Movie Metadata...")
    basics_cols = ['tconst', 'titleType', 'primaryTitle', 'startYear', 'runtimeMinutes', 'genres', 'isAdult']
    # Note: Updated filename to remove .gz
    df_basics = load_imdb_file('title.basics.tsv', cols=basics_cols)
    
    if df_basics is None: return

    # Filter: Keep only movies
    df_movies = df_basics[df_basics['titleType'] == 'movie'].copy()
    print(f"    Found {len(df_movies):,} movies.")

    # Data Cleaning
    df_movies['startYear'] = pd.to_numeric(df_movies['startYear'], errors='coerce')
    df_movies['runtimeMinutes'] = pd.to_numeric(df_movies['runtimeMinutes'], errors='coerce')
    df_movies = df_movies.dropna(subset=['startYear', 'runtimeMinutes']) 

    # 2. LOAD RATINGS (title.ratings.tsv)
    print("\n>>> Step 2: Loading Ratings...")
    df_ratings = load_imdb_file('title.ratings.tsv')
    
    # Merge Movies + Ratings
    if df_ratings is not None:
        df_main = pd.merge(df_movies, df_ratings, on='tconst', how='inner')
        print(f"    Movies with ratings: {len(df_main):,}")
    else:
        print("Could not proceed without ratings.")
        return

    # 3. CREATE TARGET VARIABLE (Proxy Method)
    print("\n>>> Step 3: Creating Target Labels...")
    
    def define_success(row):
        votes = row['numVotes']
        rating = row['averageRating']
        
        if votes > 10000 and rating >= 7.0:
            return 'Hit'
        elif votes < 1000 or rating < 5.0:
            return 'Flop'
        else:
            return 'Average'

    df_main['Target'] = df_main.apply(define_success, axis=1)
    print("    Target Distribution:")
    print(df_main['Target'].value_counts())

    # 4. LOAD DIRECTORS (title.crew.tsv)
    print("\n>>> Step 4: Loading Directors...")
    df_crew = load_imdb_file('title.crew.tsv', cols=['tconst', 'directors'])
    if df_crew is not None:
        df_main = pd.merge(df_main, df_crew, on='tconst', how='left')

    # 5. LOAD ACTORS (title.principals.tsv)
    print("\n>>> Step 5: Loading & Processing Actors...")
    df_principals = load_imdb_file('title.principals.tsv', 
                                   cols=['tconst', 'nconst', 'category', 'ordering'])
    
    if df_principals is not None:
        actors_only = df_principals[df_principals['category'].isin(['actor', 'actress'])]
        # Sort to get main cast
        actors_only = actors_only.sort_values(['tconst', 'ordering'])
        # Top 3 actors
        top_actors = actors_only.groupby('tconst').head(3)
        
        actor_lists = top_actors.groupby('tconst')['nconst'].agg(lambda x: ','.join(x)).reset_index()
        actor_lists.rename(columns={'nconst': 'actors'}, inplace=True)
        
        df_main = pd.merge(df_main, actor_lists, on='tconst', how='left')

    # 6. SAVE FINAL DATASET
    print(f"\n>>> Step 6: Saving Final Dataset to {OUTPUT_FILE}...")
    final_columns = [
        'tconst', 'primaryTitle', 'startYear', 'runtimeMinutes', 'genres', 
        'averageRating', 'numVotes', 'Target', 'directors', 'actors'
    ]
    df_main[final_columns].to_csv(OUTPUT_FILE, index=False)
    print("✅ SUCCESS: Dataset created successfully!")

if __name__ == "__main__":
    main()
