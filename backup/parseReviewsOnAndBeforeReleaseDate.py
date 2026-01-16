import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import concurrent.futures
import pandas as pd
import time

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
    release_date_obj = datetime.strptime(release_date, "%Y-%m-%d") #+ timedelta(days=180)
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
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor: 
        futures = []
        results = []

        # Submit tasks preserving order
        for tconst, release_date in zip(dataframe['tconst'], dataframe['release_date']):
            # Skip movies with missing release dates
            if pd.isna(release_date):
                futures.append(None)
            else:
                futures.append(executor.submit(parseReviewsOnAndBeforeReleaseDate, tconst, release_date))
          
        # Collect results
        for i, future in enumerate(futures):
            if future is None:
                results.append([])
            else:
                try:
                    results.append(future.result())
                except Exception as e:
                    print(f"Error processing row {i}: {e}")
                    results.append([])
           

            if (i + 1) % 100 == 0:
                print(f"Processed {i + 1} reviews")
    
    dataframe['reviews'] = results
    return dataframe

   
# print(parseReviewsOnAndBeforeReleaseDate("tt0111161", "1994-10-14"))


# curl -v --location --max-time 30 https://www.imdb.com/title/tt0111161/reviews/