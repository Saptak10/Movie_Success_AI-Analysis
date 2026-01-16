import requests
from datetime import datetime, timedelta
import pandas as pd
import time

# The Wikimedia Pageviews API only has data from July 2015 onwards. 
file_path = '/home/bumu60du/movie_success_analysis/us_movies_with_reviews.csv'
df = pd.read_csv(file_path)
print(f"Loaded {len(df)} movies from dataset")
print(f"Columns: {df.columns.tolist()}\n")

def page_views(movie_name, release_date):
    end_date = datetime.now() - timedelta(days=1)
    start_date = end_date - timedelta(days=30)

    start_date_str = start_date.strftime('%Y%m%d')
    end_date_str = end_date.strftime('%Y%m%d')

    # Fetch recent pageviews
    url = f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/all-agents/{movie_name}/daily/{start_date_str}/{end_date_str}"

    headers = {'User-Agent': 'MoviePageViewsAnalysis/1.0 (Educational purposes)'}
    response = requests.get(url, headers=headers)

    if response.status_code == 200: # API request successful
        data = response.json()
        
        # Extract pageview data
        pageviews = []
        for item in data['items']:
            pageviews.append({
                'date': datetime.strptime(item['timestamp'], '%Y%m%d%H').date(),
                'views': item['views']
            })
        
        # Create DataFrame
        df_views = pd.DataFrame(pageviews)
        return df_views

    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None


print(f"Processing {len(df)} movies...")
print("This may take a while. Progress updates every 10 movies.\n")

# Store results
pageviews_results = []

for idx, row in df.iterrows():
    movie_name = row['primaryTitle']
    release_date = row['release_date']
    
    print(f"Processing {idx + 1}/{len(df)}: {movie_name}")
    
    df_views = page_views(movie_name, release_date)
    
    if df_views is not None and len(df_views) > 0:
        total_views = df_views['views'].sum()
        avg_views = df_views['views'].mean()
        peak_views = df_views['views'].max()
    else:
        total_views = 0
        avg_views = 0
        peak_views = 0
    
    pageviews_results.append({
        'total_views_30days': total_views,
        'avg_daily_views': avg_views,
        'peak_views': peak_views
    })
    
    # Progress update every 10 movies
    if (idx + 1) % 10 == 0:
        print(f"Completed {idx + 1}/{len(df)} movies...\n")
    
    # Rate limiting - wait 0.1 seconds between requests
    time.sleep(0.1)

# Add pageview columns to dataframe
df['total_views_30days'] = [r['total_views_30days'] for r in pageviews_results]
df['avg_daily_views'] = [r['avg_daily_views'] for r in pageviews_results]
df['peak_views'] = [r['peak_views'] for r in pageviews_results]

print("\nDone! Pageview data added to dataframe.")
print(f"\nSample results:")
print(df[['primaryTitle', 'release_date', 'total_views_30days', 'avg_daily_views', 'peak_views']].head())

# Save the updated dataframe
output_path = file_path
df.to_csv(output_path, index=False)
print(f"\nSaved updated dataset to: {output_path}")