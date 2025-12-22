# Hyperparameter Tuning - RandomizedSearchCV
## Search Space
- n_estimators: [100, 200, 300, 400, 500]
- max_depth: [3, 4, 5, 6, 7, 8, 9]
- learning_rate: [0.01, 0.05, 0.1, 0.15, 0.2, 0.3]
- subsample: [0.6, 0.7, 0.8, 0.9, 1.0]
- colsample_bytree: [0.6, 0.7, 0.8, 0.9, 1.0]
## Best from RandomizedSearch
- max_depth=7, lr=0.22, n_estimators=202
- CV score: 0.668
