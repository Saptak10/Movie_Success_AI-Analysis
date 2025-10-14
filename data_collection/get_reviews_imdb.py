import pandas as pd
import requests
import os
import time
import concurrent.futures
import csv
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.decomposition import PCA

from bs4 import BeautifulSoup
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import concurrent.futures



from dotenv import load_dotenv
import os


output_path = 'data/us_movies_final_with_reviews.csv'
input_path = 'data/us_movies_final_with_cast_directors.csv'
load_dotenv()


headers = {
    "User-Agent": (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.imdb.com/",
    "Connection": "keep-alive",
}


def parseReviewsOnAndBeforeReleaseDate(imdb_id, release_date):
    """
    Parse IMDb reviews of a movie before and including its release date.
    """
    # print(release_date)
    release_date_obj = datetime.strptime(release_date, "%b %d, %Y") #+ timedelta(days=180)
    # print(release_date_obj)
    url = f'https://www.imdb.com/title/{imdb_id}/reviews/?sort=submission_date%2Casc'

    # Retry logic with timeout
    for attempt in range(3):
        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                text = response.text
                break
            elif response.status_code == 429:  # Rate limited
                print(f"Rate limited (429) for {imdb_id} attempt {attempt + 1}/3")
                time.sleep(2 ** attempt)
            else:
                print(f"HTTP {response.status_code} for {imdb_id}, attempt {attempt + 1}/3")
        except requests.exceptions.RequestException as e:
            print(f"Request failed for {imdb_id} attempt {attempt + 1}/3: {e}")
            if attempt < 2:
                time.sleep(1)
            else:
                print(f"All retries complted for {imdb_id}")
                return []
    else:
        print(f"Failed for {imdb_id} after 3 attempts")
        return []

    soup = BeautifulSoup(text, 'html.parser')

    reviews_data = []
    all_articles = soup.find_all('article', class_='user-review-item')
    # print(len(all_articles))

    for review in all_articles:

        date_element = review.find('li', class_='ipc-inline-list__item review-date')
        written_date = ""
        if date_element:
            written_date = date_element.get_text(strip=True)
            written_date_obj = datetime.strptime(written_date, "%b %d, %Y")
            # print(f"Written date: {written_date}")

            #skip reviews after release date
            if written_date_obj > release_date_obj:
                break

        # print(date_element)

        title = ""
        body = ""

        title_element = review.find('div', {'data-testid': 'review-summary'})
        # print(title_element)
        if title_element:
            title_h3 = title_element.find('h3', class_='ipc-title__text')
            if title_h3:
                title = title_h3.get_text(strip=True)
                # print(title)

        body_element = review.find('div', class_='ipc-html-content-inner-div')
        # print(body_element)
        if body_element:
            body = body_element.get_text(separator='\n', strip=True)
            # print(body)

        if title is not None and body is not None:
            reviews_data.append({'title': title,'body': body})

    return reviews_data


def add_review_to_dataframe(dataframe):
    """
    UPDATED: Processes reviews in batches of 10 and saves to Drive.
    """

    # 1. Initialize Column if needed
    if 'reviews' not in dataframe.columns:
        dataframe['reviews'] = None

    # 2. Identify Rows that still need processing
    # We look for rows where 'reviews' is NaN (or None)
    todo_indices = dataframe[dataframe['reviews'].isna()].index.tolist()
    total_todo = len(todo_indices)

    print(f"Total movies remaining to process: {total_todo}")

    if total_todo == 0:
        return dataframe

    # 3. Process in Batches of 10
    BATCH_SIZE = 100

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        for i in range(0, total_todo, BATCH_SIZE):
            batch_indices = todo_indices[i : i + BATCH_SIZE]

            future_to_idx = {}
            for idx in batch_indices:
                row = dataframe.loc[idx]
                tconst = row['tconst']
                release_date = row['release_date']

                # Skip if date is missing or tconst is missing (e.g. no IMDb match found)
                if (pd.isna(release_date) or str(release_date).lower() == 'nan' or 
                    pd.isna(tconst) or str(tconst).lower() == 'nan' or str(tconst).strip() == ''):
                     dataframe.at[idx, 'reviews'] = []
                     continue

                future = executor.submit(parseReviewsOnAndBeforeReleaseDate, tconst, release_date)
                future_to_idx[future] = idx

            # Collect results for this batch
            for future in concurrent.futures.as_completed(future_to_idx):
                idx = future_to_idx[future]
                try:
                    result = future.result()
                    dataframe.at[idx, 'reviews'] = result
                except Exception as e:
                    print(f"Error on row {idx}: {e}")
                    dataframe.at[idx, 'reviews'] = [] # Set empty list on error to avoid infinite retry

            # Progress update
            processed_count = min(i + BATCH_SIZE, total_todo)
            print(f"   >>> Processed {processed_count}/{total_todo} movies ({processed_count/total_todo:.1%})...")

            # Small sleep to be polite
            time.sleep(1)

    return dataframe


import ast

def add_review_embeddings_to_dataframe(dataframe,
                                       review_col_candidates=None,
                                       model_name="all-MiniLM-L6-v2",
                                       pca_components=32,
                                       embedding_dim=384):
    """
    Generate SBERT embeddings for a review text column, apply PCA to `pca_components` dims,
    and append columns `review_pca_0..review_pca_{pca_components-1}`. If there are fewer
    samples than `pca_components`, remaining columns are filled with zeros to keep schema stable.
    """

    if review_col_candidates is None:
        review_col_candidates = [
            "reviews", "review", "review_text",
            "reviews_text", "all_reviews",
            "movie_reviews", "scraped_reviews",
        ]

    review_col = next((c for c in review_col_candidates if c in dataframe.columns), None)
    if review_col is None:
        raise ValueError(f"No review column found. Columns: {dataframe.columns.tolist()}")

    print(f"Using review column: {review_col}")

    # Helper: turn the stored review cell (string/list) into a single text blob
    def _prepare_text(cell):
        # If it's already a string, try to detect a serialized list and parse it
        if isinstance(cell, str):
            s = cell.strip()
            if s.startswith('['):
                try:
                    parsed = ast.literal_eval(s)
                    if isinstance(parsed, list):
                        parts = []
                        for item in parsed:
                            if isinstance(item, dict):
                                parts.append(' '.join(filter(None, [str(item.get('title','')), str(item.get('body',''))])))
                            else:
                                parts.append(str(item))
                        return '\n'.join(parts)
                except Exception:
                    # Fall back to using the raw string
                    return s
            return s
        # If it's a list (already parsed), join titles and bodies
        if isinstance(cell, list):
            parts = []
            for item in cell:
                if isinstance(item, dict):
                    parts.append(' '.join(filter(None, [str(item.get('title','')), str(item.get('body',''))])))
                else:
                    parts.append(str(item))
            return '\n'.join(parts)
        # Everything else -> blank
        return ''

    texts = [ _prepare_text(x) for x in dataframe[review_col] ]

    # Load model
    try:
        model = SentenceTransformer(model_name)
    except Exception as e:
        raise RuntimeError(f"Failed to load SentenceTransformer model '{model_name}': {e}")

    def _encode(text):
        if not isinstance(text, str) or not text.strip():
            return np.zeros(embedding_dim)
        return model.encode(text, show_progress_bar=False)

    print("Generating SBERT embeddings...")
    embeddings = np.vstack([_encode(text) for text in texts])

    n_samples = embeddings.shape[0]
    if n_samples == 0:
        # No samples to process; still create empty columns
        for i in range(pca_components):
            dataframe[f"review_pca_{i}"] = 0.0
        return dataframe

    # Determine effective PCA components (cannot exceed n_samples or embedding_dim)
    effective_pca = min(pca_components, n_samples, embedding_dim)

    print(f"Applying PCA to {effective_pca} dimensions (requested {pca_components})...")
    if effective_pca >= 1:
        pca = PCA(n_components=effective_pca, random_state=42)
        review_pca = pca.fit_transform(embeddings)
    else:
        review_pca = np.zeros((n_samples, 0))

    # Prepare final array with shape (n_samples, pca_components)
    final_pca = np.zeros((n_samples, pca_components))
    if review_pca.shape[1] > 0:
        final_pca[:, :review_pca.shape[1]] = review_pca

    for i in range(pca_components):
        dataframe[f"review_pca_{i}"] = final_pca[:, i]

    return dataframe



if __name__ == "__main__":

    if os.path.exists(output_path):
        # print(f"Found existing progress: {OUTPUT_FILENAME}")
        print("Resuming from Drive...")
        us_movies = pd.read_csv(output_path)
    elif os.path.exists(input_path):
        # print(f"Starting fresh from: {INPUT_FILENAME}")
        us_movies = pd.read_csv(input_path)
    else:
        raise FileNotFoundError(f"Could not find input file: {input_path}")

    # Ensure release_date is string for the flexible parser
    us_movies['release_date'] = us_movies['release_date'].astype('object')
    us_movies['release_date'] = us_movies['release_date'].astype(str)

    # 2. Run the Batch Processor
    # This function now handles the batching (10 at a time) and saving to Drive
    print("Starting review scraping...")
    us_movies = add_review_to_dataframe(us_movies)


