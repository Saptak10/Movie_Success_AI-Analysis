# Modeling Notes
## Decision Tree Depth Sweep
- depth=5: 60.1% test accuracy (underfit)
- depth=10: 63.9% test accuracy (best)
- depth=15: 63.2% test accuracy (slight overfit)
- depth=20: 62.8% test accuracy (overfit)
## Random Forest
- 200 trees, max_depth=15: 65.8% test accuracy
- OOB score: 64.2%
