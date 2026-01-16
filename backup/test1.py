import requests
import time
import csv  # Added for file saving

class TMDbFetcher:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.themoviedb.org/3"
        self.headers = {
            "accept": "application/json"
        }

    def get_tmdb_id_from_imdb(self, imdb_id):
        """
        Converts an IMDb ID (tt12345) to a TMDb numeric ID.
        """
        url = f"{self.base_url}/find/{imdb_id}"
        params = {
            "api_key": self.api_key,
            "external_source": "imdb_id"
        }

        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()

            # Check movie results
            if data.get("movie_results"):
                return data["movie_results"][0]["id"]
            # Check TV results (just in case it's a show)
            elif data.get("tv_results"):
                return data["tv_results"][0]["id"]
            else:
                return None
        except requests.exceptions.RequestException as e:
            print(f"Error finding ID: {e}")
            return None

    def get_movie_details(self, tmdb_id):
        """
        Fetches basic metadata (Title, Global Rating).
        """
        url = f"{self.base_url}/movie/{tmdb_id}"
        params = {"api_key": self.api_key}
        
        response = requests.get(url, headers=self.headers, params=params)
        return response.json() if response.status_code == 200 else None

    def get_all_reviews(self, tmdb_id):
        """
        Fetches ALL reviews by handling pagination loops.
        """
        all_reviews = []
        current_page = 1
        total_pages = 1  # Will update this after first request

        print(f"Fetching reviews (starting at page 1)...")

        while current_page <= total_pages:
            url = f"{self.base_url}/movie/{tmdb_id}/reviews"
            params = {
                "api_key": self.api_key,
                "page": current_page
            }

            try:
                response = requests.get(url, headers=self.headers, params=params)
                data = response.json()

                if response.status_code != 200:
                    print(f"Error on page {current_page}: {data.get('status_message')}")
                    break

                # Update the total pages from the API response
                total_pages = data.get("total_pages", 1)
                results = data.get("results", [])
                
                all_reviews.extend(results)
                
                print(f" - Retrieved page {current_page} of {total_pages} ({len(results)} reviews)")
                
                current_page += 1
                
                # Basic rate limiting (optional but good practice)
                time.sleep(0.2) 

            except Exception as e:
                print(f"Network error: {e}")
                break
        
        return all_reviews

def main():
    # --- CONFIGURATION ---
    # Replace this with your actual TMDb API Key
    API_KEY = "25cfd1a6f2808426d31a787931ebc7ae" 
    
    # The IMDb ID you want to look up (e.g., Fight Club)
    TARGET_IMDB_ID = "tt2395427" 
    
    # Output filename
    OUTPUT_FILE = "reviews.csv"
    # ---------------------

    if API_KEY == "YOUR_API_KEY_HERE":
        print("Error: Please replace 'YOUR_API_KEY_HERE' with your actual TMDb API key.")
        return

    fetcher = TMDbFetcher(API_KEY)

    print(f"--- Processing ID: {TARGET_IMDB_ID} ---")

    # 1. Convert IMDb ID to TMDb ID
    tmdb_id = fetcher.get_tmdb_id_from_imdb(TARGET_IMDB_ID)

    if not tmdb_id:
        print("Could not find a TMDb movie with that IMDb ID.")
        return
    
    print(f"Found TMDb ID: {tmdb_id}")

    # 2. Get Details
    details = fetcher.get_movie_details(tmdb_id)
    if details:
        print(f"Movie: {details.get('title')} ({details.get('release_date')})")
        print(f"TMDb Rating: {details.get('vote_average')}/10 based on {details.get('vote_count')} votes")

    # 3. Get All Reviews (Pagination Handling)
    reviews = fetcher.get_all_reviews(tmdb_id)

    print(f"\n--- Total Reviews Found: {len(reviews)} ---\n")

    # 4. Save Results to CSV (Updated Logic)
    if reviews:
        print(f"Saving reviews to {OUTPUT_FILE}...")
        try:
            with open(OUTPUT_FILE, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                # Header
                writer.writerow(['Author', 'Rating', 'Date', 'Content'])
                
                for review in reviews:
                    author = review.get('author', 'Anonymous')
                    rating = review.get('author_details', {}).get('rating')
                    date = review.get('created_at', '').split('T')[0]
                    content = review.get('content', '')
                    
                    writer.writerow([author, rating, date, content])
            
            print("Success! File saved.")
        except IOError as e:
            print(f"Error saving file: {e}")
    else:
        print("No reviews to save.")

if __name__ == "__main__":
    main()