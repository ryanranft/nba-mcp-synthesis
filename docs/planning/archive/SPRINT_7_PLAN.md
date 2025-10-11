# Sprint 7: Machine Learning Tools - Planning Document

**Created**: October 10, 2025
**Status**: PLANNING
**Estimated Effort**: 3-4 hours
**Dependencies**: Sprint 5 ✅ & Sprint 6 ✅ Complete

---

## 🎯 Sprint Objectives

Build on Sprint 5 & 6's analytics foundation to add **12-15 machine learning tools** enabling:
- Player clustering and similarity analysis
- Classification and prediction models
- Anomaly detection for outlier performances
- Feature engineering and selection
- Model evaluation and validation

### Success Criteria
- [ ] 12-15 new ML tools implemented
- [ ] 100% test coverage
- [ ] Pure Python implementation (scikit-learn style)
- [ ] Comprehensive documentation
- [ ] Real-world NBA examples
- [ ] Performance < 0.1s per operation

---

## 📊 Proposed Tools (15 total)

### Category 1: Clustering & Similarity (5 tools)

#### 1. `ml_kmeans_clustering` - K-Means Clustering
**Purpose**: Group similar players/teams

**Algorithm**: Lloyd's K-means
- Initialize k centroids
- Assign points to nearest centroid
- Update centroids
- Repeat until convergence

**Parameters**:
- `data` (list of lists): Data points
- `k` (int): Number of clusters
- `max_iters` (int): Max iterations (default: 100)

**Returns**:
```python
{
    "clusters": [[player_ids], [player_ids], ...],
    "centroids": [[features], [features], ...],
    "inertia": float,  # Sum of squared distances
    "iterations": int
}
```

**Use Case**: "Group players by playing style"
```python
player_features = [
    [25.0, 5.0, 3.0],  # PPG, RPG, APG
    [22.0, 4.0, 8.0],
    [18.0, 10.0, 2.0],
    # ...
]
clusters = ml_kmeans_clustering(player_features, k=3)
```

---

#### 2. `ml_cosine_similarity` - Similarity Measure
**Purpose**: Find similar players based on features

**Formula**: `similarity = (A · B) / (||A|| × ||B||)`

**Returns**: Similarity score (0-1, where 1 = identical)

**Use Case**: "Find players similar to LeBron James"

---

#### 3. `ml_euclidean_distance` - Distance Measure
**Purpose**: Calculate distance between players

**Formula**: `distance = √(Σ(x₁ - x₂)²)`

**Use Case**: "How different are these two players?"

---

#### 4. `ml_find_nearest_neighbors` - K-Nearest Neighbors
**Purpose**: Find K most similar items

**Parameters**:
- `query_point`: Player to find neighbors for
- `data_points`: All players
- `k`: Number of neighbors
- `metric`: "euclidean" or "cosine"

**Returns**: List of k nearest neighbors with distances

**Use Case**: "Find 5 players most similar to this rookie"

---

#### 5. `ml_hierarchical_clustering` - Hierarchical Clustering
**Purpose**: Build player similarity dendrogram

**Algorithm**: Agglomerative (bottom-up)
- Start with each point as cluster
- Merge closest clusters
- Repeat until single cluster

**Returns**: Dendrogram structure + cluster assignments

---

### Category 2: Classification & Prediction (5 tools)

#### 6. `ml_logistic_regression` - Binary Classification
**Purpose**: Predict binary outcomes

**Algorithm**: Logistic function with gradient descent

**Use Cases**:
- "Will team make playoffs?" (Yes/No)
- "Will player score 20+?" (Yes/No)
- "Win/Loss prediction"

**Returns**:
```python
{
    "weights": [float],
    "intercept": float,
    "accuracy": float,
    "predictions": [0, 1, 1, 0, ...]
}
```

---

#### 7. `ml_naive_bayes` - Probabilistic Classification
**Purpose**: Multi-class classification

**Algorithm**: Bayes' theorem with independence assumption

**Use Cases**:
- "Predict player position from stats"
- "Classify play type"
- "Predict outcome category"

---

#### 8. `ml_decision_tree` - Tree-Based Classification
**Purpose**: Interpretable classification/regression

**Algorithm**: Recursive binary splitting (CART)

**Returns**: Tree structure + predictions

**Use Case**: "Classify player type with explainable rules"

---

#### 9. `ml_random_forest` - Ensemble Classification
**Purpose**: Robust classification via voting

**Algorithm**: Multiple decision trees + majority vote

**Parameters**:
- `data`, `labels`
- `n_trees` (int): Number of trees
- `max_depth` (int): Tree depth limit

**Use Case**: "Predict All-Star selection"

---

#### 10. `ml_predict_proba` - Probability Estimates
**Purpose**: Get prediction probabilities

**Returns**: Probability for each class

**Use Case**: "What's the probability of making playoffs?"

---

### Category 3: Anomaly Detection (3 tools)

#### 11. `ml_outlier_detection` - Z-Score Method
**Purpose**: Identify statistical outliers

**Algorithm**: Z-score = (x - μ) / σ

**Threshold**: |Z| > 3 = outlier

**Use Case**: "Find unusually high/low performances"

---

#### 12. `ml_isolation_forest` - Advanced Outlier Detection
**Purpose**: Detect anomalies in multidimensional data

**Algorithm**: Isolation trees - anomalies easier to isolate

**Use Case**: "Find players with unusual stat combinations"

---

#### 13. `ml_local_outlier_factor` - Density-Based Outliers
**Purpose**: Find outliers based on local density

**Algorithm**: Compare local density to neighbors

**Use Case**: "Find players who don't fit any archetype"

---

### Category 4: Feature Engineering (2 tools)

#### 14. `ml_normalize_features` - Feature Scaling
**Purpose**: Scale features to comparable ranges

**Methods**:
- Min-max scaling: [0, 1]
- Z-score normalization: mean=0, std=1
- Robust scaling: median/IQR

**Use Case**: "Normalize PPG, RPG, APG for fair comparison"

---

#### 15. `ml_feature_importance` - Feature Ranking
**Purpose**: Identify most predictive features

**Methods**:
- Correlation with target
- Mutual information
- Variance threshold

**Use Case**: "Which stats best predict winning?"

---

## 🏗️ Implementation Plan

### Phase 1: Clustering Tools (1.5 hours)

**Files to Create**:
1. `mcp_server/tools/ml_clustering_helper.py` (~450 lines)
   - K-means clustering
   - Similarity measures (cosine, euclidean)
   - K-nearest neighbors
   - Hierarchical clustering

2. `mcp_server/tools/params.py` (add ~200 lines)
   - `KMeansParams` - data, k, max_iters
   - `SimilarityParams` - vector_a, vector_b, metric
   - `KNNParams` - query, data, k, metric
   - `HierarchicalParams` - data, linkage method

**Tools to Register**:
- ml_kmeans_clustering
- ml_cosine_similarity
- ml_euclidean_distance
- ml_find_nearest_neighbors
- ml_hierarchical_clustering

---

### Phase 2: Classification Tools (1.5 hours)

**Files to Create**:
1. `mcp_server/tools/ml_classification_helper.py` (~500 lines)
   - Logistic regression (gradient descent)
   - Naive Bayes classifier
   - Decision tree (CART algorithm)
   - Random forest (ensemble)
   - Probability prediction

2. `mcp_server/tools/params.py` (add ~150 lines)
   - `LogisticRegressionParams`
   - `NaiveBayesParams`
   - `DecisionTreeParams`
   - `RandomForestParams`

**Tools to Register**:
- ml_logistic_regression
- ml_naive_bayes
- ml_decision_tree
- ml_random_forest
- ml_predict_proba

---

### Phase 3: Anomaly Detection & Feature Tools (1 hour)

**Files to Create**:
1. `mcp_server/tools/ml_anomaly_helper.py` (~350 lines)
   - Z-score outlier detection
   - Isolation forest
   - Local outlier factor (LOF)

2. `mcp_server/tools/ml_feature_helper.py` (~200 lines)
   - Feature normalization (min-max, z-score, robust)
   - Feature importance (correlation, mutual info)

**Tools to Register**:
- ml_outlier_detection
- ml_isolation_forest
- ml_local_outlier_factor
- ml_normalize_features
- ml_feature_importance

---

### Phase 4: Testing & Documentation (30 min)

**Files to Create**:
1. `scripts/test_sprint7_features.py` (~700 lines)
   - 50+ automated tests
   - Clustering validation
   - Classification accuracy tests
   - Anomaly detection tests
   - Interactive demo mode

2. `SPRINT_7_GUIDE.md` (~900 lines)
   - Complete ML tools documentation
   - Algorithm explanations
   - NBA use cases
   - Performance tips

3. Update `README.md`
   - Add Sprint 7 tools section
   - Update tool count (70 total)

---

## 📐 Technical Specifications

### Dependencies
- **Zero ML libraries** (no scikit-learn)
- Pure Python + numpy-style operations
- Use stdlib: math, statistics, random

### Algorithms to Implement

**K-Means**:
```python
def kmeans(data, k, max_iters=100):
    # Initialize random centroids
    centroids = random_init(data, k)

    for _ in range(max_iters):
        # Assign to nearest centroid
        clusters = assign_clusters(data, centroids)

        # Update centroids
        new_centroids = compute_centroids(clusters)

        # Check convergence
        if converged(centroids, new_centroids):
            break
        centroids = new_centroids

    return clusters, centroids
```

**Logistic Regression**:
```python
def logistic_regression(X, y, lr=0.01, epochs=1000):
    weights = initialize_weights(X.shape[1])

    for _ in range(epochs):
        # Forward pass
        predictions = sigmoid(X @ weights)

        # Compute gradient
        gradient = X.T @ (predictions - y)

        # Update weights
        weights -= lr * gradient

    return weights
```

**Decision Tree**:
```python
def build_tree(X, y, depth=0, max_depth=10):
    if should_stop(depth, y):
        return leaf(y)

    # Find best split
    feature, threshold = best_split(X, y)

    # Split data
    left_X, left_y = split_left(X, y, feature, threshold)
    right_X, right_y = split_right(X, y, feature, threshold)

    # Recursive build
    left_tree = build_tree(left_X, left_y, depth+1, max_depth)
    right_tree = build_tree(right_X, right_y, depth+1, max_depth)

    return Node(feature, threshold, left_tree, right_tree)
```

### Performance Targets
- K-means: < 0.1s for 100 points, 5 clusters
- Logistic regression: < 0.2s for 1000 samples
- Decision tree: < 0.1s for 500 samples
- Anomaly detection: < 0.05s for 100 points

### Error Handling
- Validate data dimensions match
- Handle empty clusters in K-means
- Check for convergence in iterative algorithms
- Prevent infinite loops with max iterations

---

## 🎯 Use Cases & Examples

### Use Case 1: Player Archetype Discovery

```python
# Get player stats
players = get_season_stats()  # PPG, RPG, APG, STL, BLK

# Normalize features
normalized = ml_normalize_features(players, method="z-score")

# Find player archetypes
clusters = ml_kmeans_clustering(normalized, k=5)

# Archetypes might be:
# - Cluster 0: Score-first guards
# - Cluster 1: Defensive specialists
# - Cluster 2: Playmakers
# - Cluster 3: Rim protectors
# - Cluster 4: All-around players
```

---

### Use Case 2: Rookie Success Prediction

```python
# Historical rookie data + outcomes
rookie_stats = [PPG, RPG, APG, TS%, USG%]
became_allstar = [0, 1, 1, 0, 1, ...]  # Binary labels

# Train classifier
model = ml_logistic_regression(rookie_stats, became_allstar)

# Predict for new rookie
new_rookie_stats = [18.5, 5.2, 4.1, 0.562, 24.3]
prob = ml_predict_proba(model, new_rookie_stats)
# Returns: {"probability": 0.73, "prediction": 1}
```

---

### Use Case 3: Find Player Comparisons

```python
# Current player stats
lebron_stats = [27.0, 7.5, 7.4, 0.580, 28.5]

# All players database
all_players_stats = get_all_players()

# Find most similar
similar = ml_find_nearest_neighbors(
    query_point=lebron_stats,
    data_points=all_players_stats,
    k=5,
    metric="cosine"
)

# Returns: Top 5 most similar players with similarity scores
```

---

### Use Case 4: Outlier Performance Detection

```python
# Player's game-by-game scoring
game_scores = [22, 25, 23, 45, 24, 21, ...]  # 45 is outlier

# Detect outliers
outliers = ml_outlier_detection(game_scores, method="z-score")
# Returns: {
#   "outliers": [3],  # Index 3 (45 points)
#   "z_scores": [...],
#   "threshold": 3.0
# }
```

---

### Use Case 5: Feature Importance for Winning

```python
# Team stats + win/loss
team_stats = [
    [ORtg, DRtg, eFG%, TOV%, ORB%, FTR],  # Game 1
    [ORtg, DRtg, eFG%, TOV%, ORB%, FTR],  # Game 2
    # ...
]
outcomes = [1, 0, 1, 1, 0, ...]  # Win=1, Loss=0

# Find most important features
importance = ml_feature_importance(team_stats, outcomes)
# Returns: {
#   "features": ["ORtg", "DRtg", "eFG%", ...],
#   "scores": [0.85, 0.82, 0.71, ...],
#   "ranking": ["ORtg", "DRtg", ...]
# }
```

---

## 🧪 Testing Strategy

### Unit Tests (50+ tests)
- **Clustering**: K-means convergence, empty clusters
- **Similarity**: Identical vectors = 1.0, orthogonal = 0.0
- **Classification**: Accuracy on known datasets
- **Anomaly**: Detect planted outliers
- **Features**: Normalization preserves relationships

### Integration Tests
- Test via MCP server
- Validate parameter models
- Test response structures
- Performance benchmarks

### Real-World Validation
- Use actual NBA player data
- Compare clustering to known archetypes
- Validate classification accuracy
- Check anomaly detection on historic outliers

---

## 📊 Success Metrics

| Metric | Target |
|--------|--------|
| Tools Implemented | 15 |
| Test Coverage | 100% |
| Tests Passing | 50+ |
| Documentation | 900+ lines |
| Performance | < 0.1s avg |
| Dependencies | 0 (pure Python) |

---

## 🚀 Rollout Plan

### Day 1: Clustering (1.5 hours)
1. Implement clustering algorithms
2. Add similarity measures
3. Create K-NN implementation
4. Register 5 tools

### Day 2: Classification (1.5 hours)
1. Implement logistic regression
2. Add Naive Bayes
3. Build decision tree
4. Implement random forest
5. Register 5 tools

### Day 3: Anomaly & Features (1 hour)
1. Implement outlier detection
2. Add advanced anomaly methods
3. Create feature tools
4. Register 5 tools

### Day 4: Testing & Docs (30 min)
1. Write comprehensive tests
2. Create user guide
3. Real-world validation
4. Update README

---

## 🎓 Learning Resources

### Clustering
- K-means algorithm (Lloyd's method)
- Hierarchical clustering (agglomerative)
- Similarity metrics (cosine, euclidean, Manhattan)

### Classification
- Logistic regression (sigmoid + gradient descent)
- Naive Bayes (Bayes' theorem)
- Decision trees (CART algorithm)
- Random forests (bagging + voting)

### Anomaly Detection
- Statistical methods (Z-score, IQR)
- Isolation forests
- Local outlier factor (LOF)

---

## 📝 Open Questions

1. **Clustering**: Include DBSCAN (density-based)?
2. **Classification**: Add SVM (support vector machine)?
3. **Validation**: Include cross-validation tool?
4. **Features**: Add PCA (dimensionality reduction)?

---

## 🔄 Future Enhancements (Sprint 8)

### Advanced ML
- Neural networks (MLP)
- Gradient boosting (XGBoost style)
- Time series forecasting (ARIMA)

### Model Ops
- Model persistence (save/load)
- Hyperparameter tuning
- Automated feature selection
- Model comparison tools

### Visualization
- Cluster visualization
- Decision boundary plots
- Feature importance charts
- Confusion matrices

---

## 📋 Checklist

**Before Starting**:
- [x] Sprint 6 complete and validated
- [x] Sprint 7 plan reviewed
- [ ] Confirm 15 tools scope
- [ ] Review algorithm implementations

**During Implementation**:
- [ ] Create ml_clustering_helper.py
- [ ] Create ml_classification_helper.py
- [ ] Create ml_anomaly_helper.py
- [ ] Create ml_feature_helper.py
- [ ] Add parameter models
- [ ] Register 15 tools in fastmcp_server.py
- [ ] Write 50+ tests
- [ ] Create documentation

**After Implementation**:
- [ ] All tests pass
- [ ] Documentation complete
- [ ] Real-world validation
- [ ] Update README
- [ ] Performance benchmarks

---

**Document Version**: 1.0
**Status**: PLANNING
**Ready to Implement**: Pending Approval
**Estimated Time**: 3-4 hours
**Expected Completion**: TBD

---

## 💡 Why Machine Learning Now?

**Foundation Built**:
- ✅ Sprint 5: Math & stats fundamentals
- ✅ Sprint 6: Correlation, regression, time series
- ✅ 55 tools providing rich data pipeline

**Natural Progression**:
1. **Data access** (Database tools) →
2. **Basic math** (Sprint 5) →
3. **Statistics & analytics** (Sprint 6) →
4. **Machine learning** (Sprint 7) →
5. **Visualization** (Sprint 8)

**Immediate Value**:
- Player similarity for scouting
- Outcome prediction for strategy
- Outlier detection for highlights
- Feature analysis for insights

**System becomes a complete NBA analytics platform!** 🚀
