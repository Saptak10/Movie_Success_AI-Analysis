import requests
from bs4 import BeautifulSoup
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import time

def slugify(text):
    text = text.replace(':', '').replace("'", "")
    return re.sub(r'[\W_]+', '-', text).strip('-')

def debug_numbers(imdb_id, title=None, year=None):
    if not title: return
    
    slug = slugify(title)
    urls = [
        f"https://www.the-numbers.com/movie/{slug}#tab=summary",
        f"https://www.the-numbers.com/movie/{slug}-({year})#tab=summary"
    ]
    
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    print("Initializing WebDriver...")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        for url in urls:
            print(f"Trying URL: {url}...")
            driver.get(url)
            time.sleep(5) # Wait for JS/Cloudflare
            
            title = driver.title
            print(f"Page Title: {title}")
            
            if "Verifying" not in title:
                print("Success!")
                parse_movie_page(BeautifulSoup(driver.page_source, 'html.parser'))
                return
            else:
                print("Failed or blocked.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.quit()

def parse_movie_page(soup):
    print("Parsing movie page...")
    tables = soup.find_all('table')
    for table in tables:
        for row in table.find_all('tr'):
            row_text = row.get_text()
            if 'Production Budget' in row_text:
                print(f"Budget Row: {row_text.strip()}")
            elif 'Worldwide Box Office' in row_text:
                print(f"Revenue Row: {row_text.strip()}")

if __name__ == "__main__":
    debug_numbers('tt0499549', 'Avatar', '2009')
