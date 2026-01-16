import pandas as pd
import numpy as np
import ast
import os

# ---------------------------------------------------------
# CONFIG: adjust only if file names / paths differ
# ---------------------------------------------------------
BASE_PATH = os.path.dirname(__file__)           # folder where this .py lives (archive/)
MOVIES_FILE  = os.path.join(BASE_PATH, "movies_metadata.csv")
CREDITS_FILE = os.path.join(BASE_PATH, "credits.csv")

ACTOR_OUT    = os.path.join(BASE_PATH, "actor_credibility_from_public.csv")
DIRECTOR_OUT = os.path.join(BASE_PATH, "director_credibility_from_public.csv")

CUTOFF_YEAR = 2020          # use movies released before this year to build credibility
RATING_HIT_THRESHOLD = 7.0  # defines a "hit" movie

# ---------------------------------------------------------
# 1. LOAD MOVIES WITH REVENUE + RATINGS
# ---------------------------------------------------------
print("Loading movies_metadata.csv ...")
movies = pd.read_csv(MOVIES_FILE, low_memory=False)

# The Movies Dataset columns: id, revenue, vote_average, vote_count, release_date, ...
movies = movies[["id", "revenue", "vote_average", "vote_count", "release_date"]].copy()
movies = movies.rename(columns={"id": "movie_id"})

# Clean types
movies["movie_id"] = pd.to_numeric(movies["movie_id"], errors="coerce")
movies["revenue"] = pd.to_numeric(movies["revenue"], errors="coerce")
movies["vote_average"] = pd.to_numeric(movies["vote_average"], errors="coerce")
movies["vote_count"] = pd.to_numeric(movies["vote_count"], errors="coerce")

# Drop movies without revenue or ratings
movies = movies.dropna(subset=["movie_id", "revenue", "vote_average", "vote_count"])

# Extract release_year
movies["release_year"] = pd.to_datetime(movies["release_date"], errors="coerce").dt.year
movies = movies.dropna(subset=["release_year"])
movies["release_year"] = movies["release_year"].astype(int)

# Use only historical movies for credibility computation
movies_hist = movies[movies["release_year"] < CUTOFF_YEAR].copy()
movies_hist["is_hit"] = (movies_hist["vote_average"] >= RATING_HIT_THRESHOLD).astype(int)

print(f"Movies used for credibility: {len(movies_hist):,}")

# ---------------------------------------------------------
# 2. LOAD CREDITS AND PARSE CAST/CREW JSON
# ---------------------------------------------------------
print("Loading credits.csv ...")
credits = pd.read_csv(CREDITS_FILE, low_memory=False)

def parse_json_list(cell):
    try:
        return ast.literal_eval(cell)
    except Exception:
        return []

credits["cast_parsed"] = credits["cast"].apply(parse_json_list)
credits["crew_parsed"] = credits["crew"].apply(parse_json_list)

# ---------------- Actors: actor–movie table ----------------
actor_rows = []
for _, row in credits.iterrows():
    mid = row["id"]
    for person in row["cast_parsed"]:
        pid = person.get("id")
        name = person.get("name")
        if pid is None:
            continue
        actor_rows.append((mid, pid, name))

actors_df = pd.DataFrame(actor_rows, columns=["movie_id", "person_id", "person_name"])

# ---------------- Directors: director–movie table ----------------
director_rows = []
for _, row in credits.iterrows():
    mid = row["id"]
    for person in row["crew_parsed"]:
        if person.get("job") == "Director":
            pid = person.get("id")
            name = person.get("name")
            if pid is None:
                continue
            director_rows.append((mid, pid, name))

directors_df = pd.DataFrame(director_rows, columns=["movie_id", "person_id", "person_name"])

# ---------------------------------------------------------
# 3. MERGE WITH MOVIE REVENUE & RATINGS
# ---------------------------------------------------------
actor_movie = actors_df.merge(
    movies_hist[["movie_id", "revenue", "vote_average", "vote_count", "is_hit"]],
    on="movie_id",
    how="inner",
)

director_movie = directors_df.merge(
    movies_hist[["movie_id", "revenue", "vote_average", "vote_count", "is_hit"]],
    on="movie_id",
    how="inner",
)

print(f"Actor–movie rows: {len(actor_movie):,}")
print(f"Director–movie rows: {len(director_movie):,}")

# ---------------------------------------------------------
# 4. AGGREGATE METRICS PER ACTOR / DIRECTOR
# ---------------------------------------------------------
def weighted_mean(x, w):
    s = (x * w).sum()
    return s / w.sum() if w.sum() > 0 else np.nan

# ---- Actors ----
g_actor = actor_movie.groupby(["person_id", "person_name"])

actor_stats = g_actor.apply(
    lambda g: pd.Series({
        "actor_avg_box_office"    : g["revenue"].mean(),
        "actor_median_box_office" : g["revenue"].median(),
        "actor_max_box_office"    : g["revenue"].max(),
        "actor_movie_count"       : len(g),
        "actor_hit_rate"          : g["is_hit"].mean(),
    })
).reset_index()

# ---- Directors ----
g_dir = director_movie.groupby(["person_id", "person_name"])

director_stats = g_dir.apply(
    lambda g: pd.Series({
        "director_avg_box_office" : g["revenue"].mean(),
        "director_max_box_office" : g["revenue"].max(),
        "director_movie_count"    : len(g),
        "director_hit_rate"       : g["is_hit"].mean(),
    })
).reset_index()

# ---------------------------------------------------------
# 5. OPTIONAL: COMPOSITE CREDIBILITY SCORES
# ---------------------------------------------------------
actor_stats["actor_credibility_score"] = (
    0.5 * np.log1p(actor_stats["actor_avg_box_office"]) +
    0.3 * (actor_stats["actor_hit_rate"] * 10) +
    0.2 * np.log1p(actor_stats["actor_movie_count"])
)

director_stats["director_credibility_score"] = (
    0.5 * np.log1p(director_stats["director_avg_box_office"]) +
    0.3 * (director_stats["director_hit_rate"] * 10) +
    0.2 * np.log1p(director_stats["director_movie_count"])
)

# require minimum history so stats are stable
MIN_MOVIES = 3
actor_stats = actor_stats[actor_stats["actor_movie_count"] >= MIN_MOVIES].copy()
director_stats = director_stats[director_stats["director_movie_count"] >= MIN_MOVIES].copy()

# ---------------------------------------------------------
# 6. SAVE FOR USE IN YOUR IMDB PROJECT
# ---------------------------------------------------------
actor_stats.to_csv(ACTOR_OUT, index=False)
director_stats.to_csv(DIRECTOR_OUT, index=False)

print(f"Saved actor credibility to   {ACTOR_OUT}")
print(f"Saved director credibility to {DIRECTOR_OUT}")
