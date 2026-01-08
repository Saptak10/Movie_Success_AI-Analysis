// js/data_missing_pattern.js
// Synthetic missing-data pattern similar to Chart15 (500 movies x 16 features).

const missingPatternFeatures = [
    "release_date",
    "title",
    "budget",
    "worldwide_gross",
    "release_year",
    "runtime_minutes",
    "genre",
    "creative_type",
    "franchise",
    "production_companies",
    "production_countries",
    "languages",
    "director_names",
    "writer_names",
    "google_trends_average",
    "roi"
  ];
  
  const numMissingMovies = 500;
  
  // Approximate missingness rates per feature (based on the plot)
  const missingRatePattern = {
    release_date:          0.02,
    title:                 0.00,
    budget:                0.05,
    worldwide_gross:       0.15,
    release_year:          0.01,
    runtime_minutes:       0.10,
    genre:                 0.06,
    creative_type:         0.30,
    franchise:             0.40,
    production_companies:  0.25,
    production_countries:  0.20,
    languages:             0.15,
    director_names:        0.35,
    writer_names:          0.30,
    google_trends_average: 0.40,
    roi:                   0.05
  };
  
  // Generate a synthetic 0/1 matrix: 0 = missing (dark), 1 = present (light)
  function generateSyntheticMissingPattern() {
    const records = [];
    for (let movieIndex = 0; movieIndex < numMissingMovies; movieIndex++) {
      missingPatternFeatures.forEach(feat => {
        const pMissing = missingRatePattern[feat] ?? 0.1;
        const isMissing = Math.random() < pMissing;
        records.push({
          movie_index: movieIndex + 1,     // label rows 1..500
          feature: feat,
          value: isMissing ? 0 : 1
        });
      });
    }
    return records;
  }
  
  const missingPatternData = generateSyntheticMissingPattern();
  