import requests
from bs4 import BeautifulSoup
import sys

# imdb allows direct descending sort in the url itself
URL = "https://www.imdb.com/title/tt0111161/reviews/?sort=submission_date%2Casc"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9"
}


try:
    response = requests.get(URL, headers=HEADERS)
    soup = BeautifulSoup(response.text, 'html.parser')
    reviews_data = []
    #all  <article>
    all_review_articles = soup.find_all('article', class_='user-review-item')
    if not all_review_articles:
        print("No articles found for ...")
        
    for review in all_review_articles:
        title = ""
        body = ""
        #title
        title_element = review.find('div', {'data-testid': 'review-summary'})
        if title_element:
            title_h3 = title_element.find('h3', class_='ipc-title__text')
            if title_h3:
                title = title_h3.get_text(strip=True)
        
        body_element = review.find('div', class_='ipc-html-content-inner-div')
        if body_element:
            body = body_element.get_text(separator='\n', strip=True)
        
        if title and body:
            reviews_data.append({'title': title,'body': body})
    print(reviews_data)


except Exception as e:
    print(f"Error: {e}")