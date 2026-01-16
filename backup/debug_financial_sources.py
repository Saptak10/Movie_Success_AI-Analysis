import time
import os
import sys
from dotenv import load_dotenv

# Add current directory to path to allow imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from parseRevenueMojo import get_mojo_revenue, get_tmdb_financials, get_wikidata_financials, get_the_numbers_financials
except ImportError:
    # Fallback if running from root
    sys.path.append(os.path.join(os.getcwd(), 'data_extraction_and_preprocessing'))
    from parseRevenueMojo import get_mojo_revenue, get_tmdb_financials, get_wikidata_financials, get_the_numbers_financials

load_dotenv()

# Sample IMDb IDs:
# tt0499549: Avatar (Blockbuster)
# tt4154796: Avengers: Endgame (Blockbuster)
# tt1630029: Avatar: The Way of Water
# tt0000000: Invalid ID (Edge case)
TEST_IDS = ['tt0499549', 'tt4154796', 'tt1630029'] 

def test_source(name, func, imdb_id):
    print(f"Testing {name} for {imdb_id}...", end=" ", flush=True)
    start = time.time()
    try:
        result = func(imdb_id)
        duration = time.time() - start
        print(f"Done in {duration:.2f}s. Result: {result}")
    except Exception as e:
        duration = time.time() - start
        print(f"Failed in {duration:.2f}s. Error: {e}")

def run_debug():
    print("Starting debug of financial sources...")
    print("This script tests each data source individually to identify timeouts or hangs.")
    
    for imdb_id in TEST_IDS:
        print(f"\n--- Movie ID: {imdb_id} ---")
        test_source("Box Office Mojo", get_mojo_revenue, imdb_id)
        test_source("TMDb", get_tmdb_financials, imdb_id)
        test_source("Wikidata", get_wikidata_financials, imdb_id)
        test_source("The Numbers", get_the_numbers_financials, imdb_id)

if __name__ == "__main__":
    run_debug()
