import pandas as pd
from pytrends.request import TrendReq
from datetime import datetime, timedelta
import time
import random
import os


def parse_monthly_average_google_trends_movie(movie_title, release_date):
    """
    Fetches the average Google Trends interest for a movie 30 days before its release.
    """
    # Initialize without retry logic (we handle it manually)
    pytrends = TrendReq(hl='en-US', tz=360, timeout=(10, 25))

    if pd.isna(release_date) or not release_date:
        return None

    try:
        # Date Parsing - accept both 'May 20, 2011' and '2011-05-20'
        try:
            date_obj = datetime.strptime(release_date, "%b %d, %Y")
        except Exception:
            date_obj = datetime.strptime(release_date, "%Y-%m-%d")
        
        # Skip future dates (Google Trends can't predict the future)
        if date_obj > datetime.now():
            return None

        # Define Timeframe (30 days before release) in ISO format (YYYY-MM-DD YYYY-MM-DD)
        date_30_days_before = date_obj - timedelta(days=30)
        timeframe_str = f'{date_30_days_before.strftime("%Y-%m-%d")} {date_obj.strftime("%Y-%m-%d")}'

        # --- MANUAL RETRY LOOP WITH EXPONENTIAL BACKOFF ---
        max_retries = 5
        for attempt in range(max_retries):
            try:
                # cat=34 is 'Movies' category
                pytrends.build_payload([movie_title], cat=34, timeframe=timeframe_str, geo='', gprop='')
                data = pytrends.interest_over_time()
                break  # Success
            except Exception as e:
                err_msg = str(e)
                # Check for Rate Limit (429)
                if "429" in err_msg:
                    wait = 60
                    print(f"!! 429 Rate Limit. Sleeping {wait}s...")
                    time.sleep(wait)
                    continue
                # On other errors: exponential backoff with jitter
                if attempt < max_retries - 1:
                    wait = 5 * (2 ** attempt)
                    wait = wait + random.uniform(0, 2)
                    print(f"   Connection error ({attempt+1}/{max_retries}): {repr(e)}. Retrying in {int(wait)}s...")
                    time.sleep(wait)
                    continue
                else:
                    # Final failure after retries -> re-raise to be handled by outer except
                    raise e

        if data.empty:
            return 0 

        # Extract Score
        clean_key = movie_title.replace('"', '')
        if clean_key in data.columns:
            return data[clean_key].mean()
        elif len(data.columns) > 0:
            return data.iloc[:, 0].mean()
        else:
            return 0

    except Exception as e:
        # Log full exception for debugging (but avoid too noisy logs for 429)
        if "429" not in str(e):
            print(f"!! Error on '{movie_title}': {type(e).__name__}: {repr(e)}")
        return None

def add_google_trends_to_dataframe(dataframe, save_path=None):
    if 'google_trends_average' not in dataframe.columns:
        dataframe['google_trends_average'] = None

    total_rows = len(dataframe)

    for index, row in dataframe.iterrows():
        # --- RESUME LOGIC ---
        # If the cell is not empty (has a value), SKIP IT.
        # This ensures we only process the missing ones.
        if pd.notna(row['google_trends_average']):
            continue

        movie = row['primaryTitle']
        date = row['release_date']
        
        print(f"[{index + 1}/{total_rows}] Processing: {movie} ({date})")

        result = parse_monthly_average_google_trends_movie(movie, date)
        
        # Update the dataframe
        dataframe.at[index, 'google_trends_average'] = result

        # Save progress every 10 rows
        if save_path and (index + 1) % 10 == 0:
            dataframe.to_csv(save_path, index=False)
        
        # --- FASTER SLEEP ---
        # Sleep 2-5 seconds (standard human behavior)
        sleep_time = random.uniform(2, 5)
        time.sleep(sleep_time)

    # Final save
    if save_path:
        dataframe.to_csv(save_path, index=False)

    return dataframe

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    
    input_file = 'data/movie_budgets_clean_matched.csv'
    output_file = 'data/movie_budgets_with_trends.csv'
    
    # 1. SMART LOAD (Resume Logic)
    # If the output file exists, load it to resume progress.
    if os.path.exists(output_file):
        print(f"Found existing progress file: {output_file}")
        print("Resuming from where we left off...")
        df = pd.read_csv(output_file)
    elif os.path.exists(input_file):
        print(f"Starting fresh from: {input_file}")
        df = pd.read_csv(input_file)
    else:
        # Fallback for folder structures
        if os.path.exists('data/' + input_file):
            print(f"Starting fresh from: data/{input_file}")
            df = pd.read_csv('data/' + input_file)
        else:
            raise FileNotFoundError(f"Could not find {input_file}")

    # 2. Fix Column Names & Date Format
    # Ensure titles are mapped
    if 'primaryTitle' not in df.columns:
        df['primaryTitle'] = df['title']

    # Convert dates to datetime objects for filtering
    df['release_date_dt'] = pd.to_datetime(df['release_date'], errors='coerce')

    # 3. FILTER: Movies > 1990
    # We only keep rows where Year > 1990
    print(f"Total rows before filter: {len(df)}")
    df = df[df['release_date_dt'].dt.year > 1990].copy()
    print(f"Rows after filtering (Year > 1990): {len(df)}")

    # Format dates back to string for the API function
    # 'release_date' column needs to be string 'YYYY-MM-DD'
    df['release_date'] = df['release_date_dt'].dt.strftime('%Y-%m-%d')
    
    # Clean up helper column
    df.drop(columns=['release_date_dt'], inplace=True)

    # 4. Run Collection
    print(f"Starting Google Trends collection...")
    df = add_google_trends_to_dataframe(df, save_path=output_file)
    
    print("Done!")