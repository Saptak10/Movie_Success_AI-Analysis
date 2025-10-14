
import os
import pandas as pd


def add_imdb_info_to_dataframe(dataframe,
                               imdb_tsv_path='data/title.basics.tsv',
                               data_dir='data',
                               save_path=None):
    """
    Enrich a dataframe by attaching IMDb ids/release years (via title.basics.tsv)
    and crew info with resolved names (via title.crew.tsv and name.basics.tsv).
    Returns the updated dataframe; optionally writes to save_path.
    """

    if dataframe is None:
        raise ValueError('dataframe must be provided')

    df = dataframe.copy()

    # 1. Parse release_date to get __source_year__
    if 'release_date' in df.columns:
        df['__source_year__'] = pd.to_datetime(df['release_date'], errors='coerce').dt.year
    else:
        df['__source_year__'] = float('nan')

    # --- Match titles to get tconst + release year ---
    imdb_cols = ['tconst', 'primaryTitle', 'titleType', 'startYear']
    df_imdb = pd.read_csv(imdb_tsv_path, sep='\t', usecols=imdb_cols, dtype=str)
    df_imdb = df_imdb[df_imdb['titleType'] == 'movie'].copy()

    df['clean_title'] = df['title'].astype(str).str.lower().str.strip()
    df_imdb['clean_title'] = df_imdb['primaryTitle'].astype(str).str.lower().str.strip()

    # 3. Filter df_imdb to only relevant titles to save memory
    relevant_titles = set(df['clean_title'].unique())
    df_imdb = df_imdb[df_imdb['clean_title'].isin(relevant_titles)].copy()

    df_imdb['startYear'] = pd.to_numeric(df_imdb['startYear'], errors='coerce')
    
    # Preserve original index for deduplication and sorting restoration
    df['__orig_index__'] = df.index

    # 4. Merge df and df_imdb (left join) on clean_title
    # Note: We do NOT drop duplicates in df_imdb by title immediately (Item 2)
    df_merged = pd.merge(
        df,
        df_imdb[['clean_title', 'tconst', 'startYear']],
        on='clean_title',
        how='left'
    )

    # 5. Calculate __diff__ = abs(__source_year__ - startYear)
    df_merged['__diff__'] = (df_merged['__source_year__'] - df_merged['startYear']).abs()

    # 6. Sort by __orig_index__ and __diff__
    # NaNs in diff (missing startYear or source_year) go last by default.
    df_merged.sort_values(by=['__orig_index__', '__diff__'], inplace=True)

    # 7. Implement the ambiguity rule
    df_merged['__candidate_count__'] = df_merged.groupby('__orig_index__')['tconst'].transform('count')
    
    # If a movie has multiple IMDb candidates (count > 1) BUT the __diff__ is NaN 
    # (because release_date is missing), invalidate the match.
    mask_ambiguous = (df_merged['__candidate_count__'] > 1) & (df_merged['__diff__'].isna())
    
    df_merged.loc[mask_ambiguous, 'tconst'] = None
    df_merged.loc[mask_ambiguous, 'startYear'] = None

    # 8. Drop duplicates on __orig_index__ to keep the best match
    df = df_merged.drop_duplicates(subset=['__orig_index__'], keep='first').copy()

    # Reporting logic (adapted since we are not dropping rows)
    initial_count = len(dataframe)
    final_count = len(df)
    dropped_count = df['tconst'].isna().sum() 

    # 10. Rename startYear and clean up temporary columns
    df.rename(columns={'startYear': 'imdb_release_year'}, inplace=True)
    
    temp_cols = ['clean_title', '__source_year__', '__orig_index__', '__diff__', '__candidate_count__']
    df.drop(columns=[c for c in temp_cols if c in df.columns], inplace=True)

    # --- Crew join and name resolution ---
    crew_cols = ['tconst', 'directors', 'writers']
    crew_path = os.path.join(data_dir, 'title.crew.tsv')
    crew_df = pd.read_csv(
        crew_path,
        sep='\t',
        na_values='\\N',
        usecols=crew_cols,
        quoting=3,
        low_memory=False,
    )

    df = df.join(crew_df.set_index('tconst'), on='tconst', how='left', rsuffix='_drop')

    name_basics_path = os.path.join(data_dir, 'name.basics.tsv')
    directors_ids = df['directors'].dropna().str.split(',').explode()
    writers_ids = df['writers'].dropna().str.split(',').explode()
    needed_nconsts = set(directors_ids).union(set(writers_ids))

    nconst_to_name = {}
    chunk_size = 100000
    with pd.read_csv(
        name_basics_path,
        sep='\t',
        usecols=['nconst', 'primaryName'],
        dtype=str,
        na_values='\\N',
        quoting=3,
        chunksize=chunk_size,
    ) as reader:
        for chunk in reader:
            matched = chunk[chunk['nconst'].isin(needed_nconsts)]
            if not matched.empty:
                nconst_to_name.update(zip(matched['nconst'], matched['primaryName']))

    def resolve_names(id_str):
        if pd.isna(id_str):
            return None
        ids = id_str.split(',')
        names = [nconst_to_name.get(x, x) for x in ids]
        return ','.join(names)

    df['director_names'] = df['directors'].apply(resolve_names)
    df['writer_names'] = df['writers'].apply(resolve_names)

    if save_path:
        df.to_csv(save_path, index=False)
        print("-" * 30)
        print(f"Original Count: {initial_count}")
        print(f"Movies without IMDb Match: {dropped_count}")
        print(f"Final Count: {final_count}")
        print(f"Saved cleanly matched data to: {save_path}")
        print("-" * 30)

    return df


def load_and_add_imdb_ids(budgets_csv_path='data/the_numbers_movie_budgets.csv',
                          imdb_tsv_path='data/title.basics.tsv',
                          save_path='data/movie_budgets_clean_matched.csv'):
    """
    Convenience loader: reads budgets CSV into a dataframe and calls
    `add_imdb_info_to_dataframe`. Returns the cleaned dataframe.
    """
    df_budget = pd.read_csv(budgets_csv_path)
    return add_imdb_info_to_dataframe(df_budget, imdb_tsv_path=imdb_tsv_path, save_path=save_path)


def add_crew_and_names_to_dataframe(dataframe,
                                    data_dir='data',
                                    save_path=None):
    """
    Enrich a movies dataframe (with tconst) by attaching directors/writers and
    resolving their names from name.basics.tsv. Does not train or persist unless
    save_path is provided.
    """

    if dataframe is None:
        raise ValueError('dataframe must be provided')

    df = dataframe.copy()

    crew_cols = ['tconst', 'directors', 'writers']
    crew_path = os.path.join(data_dir, 'title.crew.tsv')
    crew_df = pd.read_csv(
        crew_path,
        sep='\t',
        na_values='\\N',
        usecols=crew_cols,
        quoting=3,
        low_memory=False,
    )

    df = df.join(crew_df.set_index('tconst'), on='tconst', how='left', rsuffix='_drop')

    name_basics_path = os.path.join(data_dir, 'name.basics.tsv')
    directors_ids = df['directors'].dropna().str.split(',').explode()
    writers_ids = df['writers'].dropna().str.split(',').explode()
    needed_nconsts = set(directors_ids).union(set(writers_ids))

    nconst_to_name = {}
    chunk_size = 100000
    with pd.read_csv(
        name_basics_path,
        sep='\t',
        usecols=['nconst', 'primaryName'],
        dtype=str,
        na_values='\\N',
        quoting=3,
        chunksize=chunk_size,
    ) as reader:
        for chunk in reader:
            matched = chunk[chunk['nconst'].isin(needed_nconsts)]
            if not matched.empty:
                nconst_to_name.update(zip(matched['nconst'], matched['primaryName']))

    def resolve_names(id_str):
        if pd.isna(id_str):
            return None
        ids = id_str.split(',')
        names = [nconst_to_name.get(x, x) for x in ids]
        return ','.join(names)

    df['director_names'] = df['directors'].apply(resolve_names)
    df['writer_names'] = df['writers'].apply(resolve_names)

    if save_path:
        df.to_csv(save_path, index=False)

    return df


if __name__ == "__main__":
    # Preserve original script behavior when run directly: read budgets and save result
    load_and_add_imdb_ids()
