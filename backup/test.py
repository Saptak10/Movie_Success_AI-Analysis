# =========================================================
# GOOGLE COLAB + DRIVE
# =========================================================

# =========================================================
# IMPORTS
# =========================================================
import os
import pandas as pd

from get_imdb_id_in_numbers_dataset import add_imdb_info_to_dataframe
from get_google_trends import add_google_trends_to_dataframe
from get_reviews_imdb import add_review_to_dataframe, add_review_embeddings_to_dataframe

# =========================================================
# CONFIG
# =========================================================
BASE_DIR = "data"

RAW_CSV = f"{BASE_DIR}/the_numbers_movie_budgets.csv"

IMDB_DIR = f"{BASE_DIR}/imdb"
INTERIM_DIR = f"{BASE_DIR}/interim"

IMDB_BASICS = f"data/title.basics.tsv"

STAGE1_PATH = f"{INTERIM_DIR}/stage1_imdb.csv"
STAGE2_PATH = f"{INTERIM_DIR}/stage2_trends.csv"
STAGE3_PATH = f"{INTERIM_DIR}/stage3_reviews.csv"

N_ROWS = -1

# =========================================================
# FLAGS controls
# =========================================================
RUN_STAGE_1 = True  # IMDb Enrichment
RUN_STAGE_2 = False  # Google Trends
RUN_STAGE_3 = True  # Reviews
RUN_STAGE_4 = True  # Embeddings

os.makedirs(IMDB_DIR, exist_ok=True)
os.makedirs(INTERIM_DIR, exist_ok=True)

# =========================================================
# HELPER FOR LOADING/SLICING
# =========================================================
def load_and_slice(path):
    print(f"Loading cached data from {path}...")
    d = pd.read_csv(path)
    if N_ROWS != -1:
        d = d.head(N_ROWS).copy()
    return d

# =========================================================
# ENSURE IMDb DATASETS
# =========================================================
def ensure_imdb_files():
    files = [
        "title.basics.tsv",
        "title.crew.tsv",
        "name.basics.tsv",
    ]
    missing = [f for f in files if not os.path.exists(f"{IMDB_DIR}/{f}")]
    if missing:
        print("Downloading IMDb datasets...")
        # os.system(f"wget https://datasets.imdbws.com/title.basics.tsv.gz -P {IMDB_DIR}")
        # os.system(f"wget https://datasets.imdbws.com/title.crew.tsv.gz   -P {IMDB_DIR}")
        # os.system(f"wget https://datasets.imdbws.com/name.basics.tsv.gz  -P {IMDB_DIR}")
        # os.system(f"gunzip -f {IMDB_DIR}/*.gz")

ensure_imdb_files()

# =========================================================
# STAGE 0: LOAD RAW
# =========================================================
# Logic: We might not need Raw if we skip Stage 1 and have cached Stage 1 output.
# But for simplicity, we can init df.
df = None

# =========================================================
# STAGE 1: IMDb ENRICHMENT
# =========================================================
if RUN_STAGE_1:
    print("Running Stage 1: IMDb enrichment...")
    # Load raw if not present
    if df is None:
        print(f"Loading raw data from {RAW_CSV}...")
        df = load_and_slice(RAW_CSV)
    
    df = add_imdb_info_to_dataframe(
            dataframe=df,
            imdb_tsv_path=IMDB_BASICS,
            save_path=STAGE1_PATH
    )
    # Ensure schema for future stages
    if "primaryTitle" not in df.columns:
        df["primaryTitle"] = df["title"]

else:
    # If skipping Stage 1, check if we can load its output to assist next stages
    if os.path.exists(STAGE1_PATH) and df is None:
        # Load Stage 1 output to be ready for Stage 2
        df = load_and_slice(STAGE1_PATH)
    elif df is None:
        # If no Stage 1 output, fall back to Raw (Stage 2 will likely look for 'title')
        print(f"Loading raw data from {RAW_CSV}...")
        df = load_and_slice(RAW_CSV)
    
    # Ensure schema if we loaded file or raw
    if "primaryTitle" not in df.columns and "title" in df.columns:
         df["primaryTitle"] = df["title"]

# =========================================================
# STAGE 2: GOOGLE TRENDS
# =========================================================
if RUN_STAGE_2:
    print("Running Stage 2: Google Trends...")
    df = add_google_trends_to_dataframe(
        df,
        save_path=STAGE2_PATH
    )
else:
    # Logic: Only load cached Stage 2 if Stage 1 was NOT run (to avoid overwriting fresh data).
    # If Stage 1 was run, current `df` is fresher than any Stage 2 cache.
    if not RUN_STAGE_1 and os.path.exists(STAGE2_PATH):
        df = load_and_slice(STAGE2_PATH)

# =========================================================
# STAGE 3: IMDb REVIEWS
# =========================================================
if RUN_STAGE_3:
    print("Running Stage 3: IMDb Reviews...")
    df = add_review_to_dataframe(df)
    df.to_csv(STAGE3_PATH, index=False)
else:
    # Logic: Only load cached Stage 3 if previous stages were NOT run.
    if not RUN_STAGE_1 and not RUN_STAGE_2 and os.path.exists(STAGE3_PATH):
        df = load_and_slice(STAGE3_PATH)

# =========================================================
# STAGE 4: REVIEW EMBEDDINGS (Optional, can be slow)
# =========================================================
if RUN_STAGE_4:
    print("Generating review embeddings (this may download a model and take time)...")
    try:
        # This function will raise a clear error if no review column exists
        df = add_review_embeddings_to_dataframe(df)
        # Save again (overwrites) with embedding columns
        df.to_csv(STAGE3_PATH, index=False)
        print("Review embeddings added and saved.")
    except Exception as e:
        print(f"!! Failed to compute review embeddings: {type(e).__name__}: {e}")

print("PIPELINE COMPLETED SUCCESSFULLY ✅")
print(f"Final output saved to: {STAGE3_PATH}")
