"""
AutoML Integration

Automated machine learning for model selection and tuning:
- Automated model selection
- Hyperparameter optimization
- Feature engineering
- Pipeline optimization
- Model ensembling
- Auto-deployment

Features:
- Multiple algorithms
- Auto feature selection
- Cross-validation
- Model comparison
- Automated training
- Production deployment

Use Cases:
- Model development
- Quick prototyping
- Baseline models
- Production ML
- Continuous learning
"""

import logging
import time
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json

logger = logging.getLogger(__name__)


class ModelType(Enum):
    """ML model types"""
    CLASSIFICATION = "classification"
    REGRESSION = "regression"
    CLUSTERING = "clustering"
    TIME_SERIES = "time_series"


class Algorithm(Enum):
    """Supported algorithms"""
    # Classification
    LOGISTIC_REGRESSION = "logistic_regression"
    RANDOM_FOREST = "random_forest"
    GRADIENT_BOOSTING = "gradient_boosting"
    SVM = "svm"
    NAIVE_BAYES = "naive_bayes"
    
    # Regression
    LINEAR_REGRESSION = "linear_regression"
    RIDGE = "ridge"
    LASSO = "lasso"
    
    # Clustering
    KMEANS = "kmeans"
    DBSCAN = "dbscan"


@dataclass
class ModelConfig:
    """Model configuration"""
    algorithm: Algorithm
    hyperparameters: Dict[str, Any] = field(default_factory=dict)
    features: Optional[List[str]] = None
    training_time_seconds: float = 0.0


@dataclass
class ModelResult:
    """Model training result"""
    config: ModelConfig
    score: float
    metrics: Dict[str, float]
    training_time: float
    model_id: str
    timestamp: datetime = field(default_factory=datetime.now)


class FeatureSelector:
    """Automated feature selection"""
    
    def __init__(self):
        self.selected_features: List[str] = []
        self.feature_importance: Dict[str, float] = {}
    
    def select_features(
        self,
        X: List[List[float]],
        y: List[float],
        feature_names: List[str],
        max_features: Optional[int] = None
    ) -> List[str]:
        """Select most important features"""
        
        n_features = len(feature_names)
        if max_features is None:
            max_features = min(n_features, 20)  # Default to top 20
        
        # Calculate simple correlation-based importance
        importance = {}
        for i, name in enumerate(feature_names):
            feature_values = [row[i] for row in X]
            
            # Simple correlation with target
            mean_x = sum(feature_values) / len(feature_values)
            mean_y = sum(y) / len(y)
            
            numerator = sum((feature_values[j] - mean_x) * (y[j] - mean_y) for j in range(len(y)))
            
            var_x = sum((x - mean_x) ** 2 for x in feature_values)
            var_y = sum((yi - mean_y) ** 2 for yi in y)
            denominator = (var_x * var_y) ** 0.5
            
            correlation = abs(numerator / denominator) if denominator > 0 else 0
            importance[name] = correlation
        
        # Select top features
        sorted_features = sorted(importance.items(), key=lambda x: x[1], reverse=True)
        self.selected_features = [name for name, _ in sorted_features[:max_features]]
        self.feature_importance = dict(sorted_features[:max_features])
        
        logger.info(f"Selected {len(self.selected_features)} features")
        return self.selected_features


class HyperparameterTuner:
    """Automated hyperparameter tuning"""
    
    def __init__(self):
        self.search_history: List[Dict[str, Any]] = []
    
    def get_default_params(self, algorithm: Algorithm) -> Dict[str, Any]:
        """Get default hyperparameters for algorithm"""
        
        defaults = {
            Algorithm.LOGISTIC_REGRESSION: {
                'learning_rate': 0.01,
                'max_iterations': 1000
            },
            Algorithm.RANDOM_FOREST: {
                'n_trees': 100,
                'max_depth': 10,
                'min_samples_split': 2
            },
            Algorithm.GRADIENT_BOOSTING: {
                'n_estimators': 100,
                'learning_rate': 0.1,
                'max_depth': 3
            },
            Algorithm.LINEAR_REGRESSION: {
                'fit_intercept': True
            },
            Algorithm.KMEANS: {
                'k': 3,
                'max_iterations': 100
            }
        }
        
        return defaults.get(algorithm, {})
    
    def tune_hyperparameters(
        self,
        algorithm: Algorithm,
        param_grid: Optional[Dict[str, List[Any]]] = None,
        max_trials: int = 10
    ) -> Dict[str, Any]:
        """Tune hyperparameters using random search"""
        
        if param_grid is None:
            # Use default search space
            param_grid = self._get_default_search_space(algorithm)
        
        best_params = self.get_default_params(algorithm)
        best_score = 0.0
        
        # Random search
        import random
        for trial in range(max_trials):
            # Sample random parameters
            params = {}
            for param_name, param_values in param_grid.items():
                params[param_name] = random.choice(param_values)
            
            # Simulate training and evaluation
            score = self._evaluate_params(algorithm, params)
            
            self.search_history.append({
                'trial': trial,
                'params': params,
                'score': score
            })
            
            if score > best_score:
                best_score = score
                best_params = params
        
        logger.info(f"Best score: {best_score:.4f} with params: {best_params}")
        return best_params
    
    def _get_default_search_space(self, algorithm: Algorithm) -> Dict[str, List[Any]]:
        """Get default search space"""
        
        spaces = {
            Algorithm.RANDOM_FOREST: {
                'n_trees': [50, 100, 200],
                'max_depth': [5, 10, 15, 20],
                'min_samples_split': [2, 5, 10]
            },
            Algorithm.LOGISTIC_REGRESSION: {
                'learning_rate': [0.001, 0.01, 0.1],
                'max_iterations': [500, 1000, 2000]
            },
            Algorithm.GRADIENT_BOOSTING: {
                'n_estimators': [50, 100, 200],
                'learning_rate': [0.01, 0.1, 0.3],
                'max_depth': [3, 5, 7]
            }
        }
        
        return spaces.get(algorithm, {})
    
    def _evaluate_params(self, algorithm: Algorithm, params: Dict[str, Any]) -> float:
        """Simulate evaluation of parameters"""
        # In production, this would train and evaluate the model
        # For demo, return simulated score
        import random
        base_score = 0.7
        variance = random.uniform(-0.1, 0.1)
        return base_score + variance


class ModelSelector:
    """Automated model selection"""
    
    def __init__(self):
        self.results: List[ModelResult] = []
    
    def compare_algorithms(
        self,
        X: List[List[float]],
        y: List[float],
        model_type: ModelType,
        algorithms: Optional[List[Algorithm]] = None
    ) -> List[ModelResult]:
        """Compare multiple algorithms"""
        
        if algorithms is None:
            algorithms = self._get_default_algorithms(model_type)
        
        results = []
        
        for algo in algorithms:
            logger.info(f"Training {algo.value}...")
            
            # Get default parameters
            tuner = HyperparameterTuner()
            params = tuner.get_default_params(algo)
            
            # Simulate training
            start_time = time.time()
            score = self._train_and_evaluate(algo, X, y, params)
            training_time = time.time() - start_time
            
            result = ModelResult(
                config=ModelConfig(
                    algorithm=algo,
                    hyperparameters=params,
                    training_time_seconds=training_time
                ),
                score=score,
                metrics={
                    'accuracy': score,
                    'training_time': training_time
                },
                training_time=training_time,
                model_id=f"{algo.value}_{int(time.time())}"
            )
            
            results.append(result)
            self.results.append(result)
        
        # Sort by score
        results.sort(key=lambda r: r.score, reverse=True)
        
        logger.info(f"Best algorithm: {results[0].config.algorithm.value} (score: {results[0].score:.4f})")
        return results
    
    def _get_default_algorithms(self, model_type: ModelType) -> List[Algorithm]:
        """Get default algorithms for model type"""
        
        if model_type == ModelType.CLASSIFICATION:
            return [
                Algorithm.LOGISTIC_REGRESSION,
                Algorithm.RANDOM_FOREST,
                Algorithm.GRADIENT_BOOSTING
            ]
        elif model_type == ModelType.REGRESSION:
            return [
                Algorithm.LINEAR_REGRESSION,
                Algorithm.RIDGE,
                Algorithm.LASSO
            ]
        elif model_type == ModelType.CLUSTERING:
            return [Algorithm.KMEANS]
        else:
            return []
    
    def _train_and_evaluate(
        self,
        algorithm: Algorithm,
        X: List[List[float]],
        y: List[float],
        params: Dict[str, Any]
    ) -> float:
        """Simulate training and evaluation"""
        # In production, this would actually train the model
        # For demo, return simulated score
        import random
        
        # Different algorithms have different base performance
        base_scores = {
            Algorithm.RANDOM_FOREST: 0.85,
            Algorithm.LOGISTIC_REGRESSION: 0.80,
            Algorithm.GRADIENT_BOOSTING: 0.87,
            Algorithm.LINEAR_REGRESSION: 0.75,
            Algorithm.NAIVE_BAYES: 0.78
        }
        
        base = base_scores.get(algorithm, 0.70)
        variance = random.uniform(-0.05, 0.05)
        return base + variance


class AutoMLPipeline:
    """Complete AutoML pipeline"""
    
    def __init__(self):
        self.feature_selector = FeatureSelector()
        self.hyperparameter_tuner = HyperparameterTuner()
        self.model_selector = ModelSelector()
        self.best_model: Optional[ModelResult] = None
    
    def auto_train(
        self,
        X: List[List[float]],
        y: List[float],
        feature_names: List[str],
        model_type: ModelType,
        max_time_minutes: int = 60
    ) -> Dict[str, Any]:
        """Automated end-to-end training"""
        
        start_time = time.time()
        
        logger.info("Starting AutoML pipeline...")
        
        # Step 1: Feature selection
        logger.info("Step 1: Feature selection")
        selected_features = self.feature_selector.select_features(X, y, feature_names)
        
        # Step 2: Model selection
        logger.info("Step 2: Model selection")
        results = self.model_selector.compare_algorithms(X, y, model_type)
        
        # Get best model
        best_result = results[0]
        
        # Step 3: Hyperparameter tuning for best algorithm
        logger.info(f"Step 3: Tuning {best_result.config.algorithm.value}")
        best_params = self.hyperparameter_tuner.tune_hyperparameters(
            best_result.config.algorithm,
            max_trials=10
        )
        
        # Update best model with tuned params
        tuned_score = self.model_selector._train_and_evaluate(
            best_result.config.algorithm,
            X, y,
            best_params
        )
        
        self.best_model = ModelResult(
            config=ModelConfig(
                algorithm=best_result.config.algorithm,
                hyperparameters=best_params,
                features=selected_features
            ),
            score=tuned_score,
            metrics={
                'accuracy': tuned_score,
                'training_time': time.time() - start_time
            },
            training_time=time.time() - start_time,
            model_id=f"automl_{int(time.time())}"
        )
        
        total_time = time.time() - start_time
        
        logger.info(f"AutoML complete in {total_time:.2f}s")
        logger.info(f"Best model: {self.best_model.config.algorithm.value}")
        logger.info(f"Score: {self.best_model.score:.4f}")
        
        return {
            'best_model': {
                'algorithm': self.best_model.config.algorithm.value,
                'score': round(self.best_model.score, 4),
                'hyperparameters': self.best_model.config.hyperparameters,
                'features': self.best_model.config.features,
                'model_id': self.best_model.model_id
            },
            'all_models': [
                {
                    'algorithm': r.config.algorithm.value,
                    'score': round(r.score, 4)
                }
                for r in results
            ],
            'feature_importance': self.feature_selector.feature_importance,
            'total_time_seconds': round(total_time, 2),
            'timestamp': datetime.now().isoformat()
        }
    
    def deploy_model(self, model_id: str) -> Dict[str, Any]:
        """Deploy trained model"""
        
        if not self.best_model or self.best_model.model_id != model_id:
            return {
                'status': 'error',
                'message': 'Model not found'
            }
        
        # Simulate deployment
        deployment_id = f"deploy_{int(time.time())}"
        
        logger.info(f"Deploying model {model_id} as {deployment_id}")
        
        return {
            'status': 'success',
            'deployment_id': deployment_id,
            'model_id': model_id,
            'endpoint': f"/api/predict/{deployment_id}",
            'deployed_at': datetime.now().isoformat()
        }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("=== AutoML Integration Demo ===\n")
    
    # Create AutoML pipeline
    automl = AutoMLPipeline()
    
    # Simulate training data (NBA player classification)
    print("--- Preparing Data ---\n")
    
    # Features: [ppg, rpg, apg, mpg, age]
    X_train = [
        [25.0, 8.0, 5.0, 35.0, 28],  # Star player
        [22.0, 7.5, 6.0, 34.0, 26],  # Star player
        [10.0, 3.0, 2.0, 20.0, 24],  # Role player
        [8.0, 2.5, 1.5, 18.0, 23],   # Role player
        [18.0, 5.0, 4.0, 30.0, 25],  # Starter
    ]
    
    # Labels: 1 = All-Star, 0 = Not All-Star
    y_train = [1, 1, 0, 0, 1]
    
    feature_names = ['ppg', 'rpg', 'apg', 'mpg', 'age']
    
    print(f"Training samples: {len(X_train)}")
    print(f"Features: {', '.join(feature_names)}")
    
    # Run AutoML
    print("\n--- Running AutoML ---\n")
    result = automl.auto_train(
        X_train,
        y_train,
        feature_names,
        model_type=ModelType.CLASSIFICATION,
        max_time_minutes=5
    )
    
    # Results
    print("\n--- Results ---\n")
    print(f"Best Model: {result['best_model']['algorithm']}")
    print(f"Score: {result['best_model']['score']}")
    print(f"Training Time: {result['total_time_seconds']}s")
    
    print(f"\nSelected Features:")
    for feature, importance in list(result['feature_importance'].items())[:3]:
        print(f"  {feature}: {importance:.3f}")
    
    print(f"\nAll Models Tried:")
    for model in result['all_models']:
        print(f"  {model['algorithm']}: {model['score']}")
    
    # Deploy
    print("\n--- Deploying Model ---\n")
    deployment = automl.deploy_model(result['best_model']['model_id'])
    print(f"✓ Deployed: {deployment['deployment_id']}")
    print(f"  Endpoint: {deployment['endpoint']}")
    
    print("\n=== Demo Complete ===")

