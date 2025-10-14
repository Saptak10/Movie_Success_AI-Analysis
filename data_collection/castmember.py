from SPARQLWrapper import SPARQLWrapper, JSON
import time
import ssl
import certifi
import pandas as pd
import requests

# Load the dataset
file_path = '/home/bumu60du/movie_success_analysis/us_movies_with_reviews.csv'
df = pd.read_csv(file_path)
print(f"Loaded {len(df)} movies from dataset")
print(f"Columns: {df.columns.tolist()}\n")

def get_cast_members(imdb_id):
    """
    Query Wikidata for cast members using IMDb ID
    Returns a list of actor names
    """
    sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
    sparql.setReturnFormat(JSON)
    
    query = f"""
    SELECT ?actor ?actorLabel WHERE {{
      ?movie wdt:P345 "{imdb_id}".   # IMDb ID
      ?movie wdt:P161 ?actor.        # P161 = cast member
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }}
    }}
    """
    
    sparql.setQuery(query)
    
    try:
        # Use requests to avoid SSL issues
        
        headers = {
            'User-Agent': 'MovieCastAnalysis/1.0 (Educational purposes)',
            'Accept': 'application/json'
        }
        
        response = requests.get(
            "https://query.wikidata.org/sparql",
            params={'query': query, 'format': 'json'},
            headers=headers
        )
        
        if response.status_code == 200:
            results = response.json()
            actors = [result['actorLabel']['value'] for result in results['results']['bindings']]
            return actors if actors else []
        else:
            print(f"Error {response.status_code} for {imdb_id}")
            return []
    except Exception as e:
        print(f"Error querying {imdb_id}: {e}")
        return []
    

print(f"Processing {len(df)} movies...")
print("This may take a while. Progress updates every 10 movies.")

cast_members_list = []
for idx, imdb_id in enumerate(df['tconst']):
    cast = get_cast_members(imdb_id)
    cast_members_list.append(cast)
    
    # Progress update every 10 movies
    if (idx + 1) % 10 == 0:
        print(f"Processed {idx + 1}/{len(df)} movies...")
    
    # Rate limiting - wait 0.1 seconds between requests to be respectful
    time.sleep(0.1)

# Add as new column
df['cast_members'] = cast_members_list
print("\nDone! Cast members added to 'cast_members' column.")
print(f"\nSample results:")
print(df[['tconst', 'primaryTitle', 'cast_members']].head())

# Save the updated dataframe
output_path = file_path
df.to_csv(output_path, index=False)
print(f"\nSaved updated dataset to: {output_path}")