# EDA Notes
## Column Standardization
- snake_case for all columns
- Dates parsed to datetime
- Budget/gross to int64
- Boolean flags as uint8
## Merge Key
- Primary: (title, release_year)
- Fallback: fuzzy title match (threshold 85)
