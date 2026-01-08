// js/data_completeness_data.js
// Synthetic 0/1 completeness matrix with similar structure to Chart14.
// This is illustrative only – not the exact values from the original plot.

const completenessFeatures = [
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
  
  const numMovies = 100;
  
  // Manual base missingness rates per feature (approximate from the picture)
  const missingRateByFeature = {
    release_date:          0.02,
    title:                 0.00,
    budget:                0.05,
    worldwide_gross:       0.08,
    release_year:          0.01,
    runtime_minutes:       0.10,
    genre:                 0.06,
    creative_type:         0.30,
    franchise:             0.40,
    production_companies:  0.25,
    production_countries:  0.20,
    languages:             0.15,
    director_names:        0.10,
    writer_names:          0.12,
    google_trends_average: 0.35,
    roi:                   0.05
  };
  
  function generateSyntheticCompleteness() {
    const records = [];
    for (let movieIndex = 0; movieIndex < numMovies; movieIndex++) {
      completenessFeatures.forEach(feat => {
        const pMissing = missingRateByFeature[feat] ?? 0.1;
        const isMissing = Math.random() < pMissing;
        records.push({
          movie_index: movieIndex,
          feature: feat,
          value: isMissing ? 0 : 1
        });
      });
    }
    return records;
  }
  
  const completenessHeatmapData = generateSyntheticCompleteness();
  