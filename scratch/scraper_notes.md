# Scraper Notes
- Retry up to 3 times on connection error
- Exponential backoff: 2^n seconds
- Log failed URLs to failed_urls.txt for manual review
- Scraper now handles network instability
