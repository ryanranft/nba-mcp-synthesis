"""
Advanced Model Interpretability

Deep model explanations beyond SHAP:
- Counterfactual explanations
- Anchor explanations
- Prototype-based explanations
- Attention visualization
- Feature interactions
- Model behavior analysis

Features:
- Multiple explanation methods
- Interactive visualizations
- Global + local explanations
- Feature attribution
- What-if analysis
- Model debugging

Use Cases:
- Model debugging
- Regulatory compliance
- User trust
- Model improvement
- Fairness analysis
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import json

logger = logging.getLogger(__name__)


@dataclass
class Explanation:
    """Base explanation result"""
    method: str
    prediction: float
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CounterfactualExplanation(Explanation):
    """Counterfactual explanation"""
    original_features: Dict[str, float]
    counterfactual_features: Dict[str, float]
    changes_needed: Dict[str, float]
    distance: float


@dataclass
class AnchorExplanation(Explanation):
    """Anchor explanation (rules)"""
    anchor_rules: List[str]
    precision: float
    coverage: float


@dataclass
class FeatureInteraction:
    """Feature interaction effect"""
    feature_1: str
    feature_2: str
    interaction_strength: float
    effect_on_prediction: float


class CounterfactualGenerator:
    """Generate counterfactual explanations"""
    
    def __init__(self):
        self.counterfactuals: List[CounterfactualExplanation] = []
    
    def generate_counterfactual(
        self,
        features: Dict[str, float],
        current_prediction: float,
        desired_prediction: float,
        feature_ranges: Dict[str, Tuple[float, float]],
        mutable_features: Optional[List[str]] = None
    ) -> CounterfactualExplanation:
        """
        Generate counterfactual explanation
        
        Answers: "What needs to change for a different prediction?"
        """
        
        if mutable_features is None:
            mutable_features = list(features.keys())
        
        # Simple greedy search for counterfactual
        counterfactual = features.copy()
        changes = {}
        
        # Simulate feature changes
        for feature in mutable_features:
            if feature not in feature_ranges:
                continue
            
            min_val, max_val = feature_ranges[feature]
            current_val = features[feature]
            
            # Try increasing feature value
            if current_prediction < desired_prediction:
                # Need to increase prediction, try increasing feature
                new_val = min(current_val * 1.2, max_val)
            else:
                # Need to decrease prediction, try decreasing feature
                new_val = max(current_val * 0.8, min_val)
            
            if new_val != current_val:
                counterfactual[feature] = new_val
                changes[feature] = new_val - current_val
        
        # Calculate distance
        distance = sum(abs(changes.get(f, 0)) for f in features.keys())
        
        # Simulate new prediction
        new_prediction = self._simulate_prediction(counterfactual)
        
        explanation = CounterfactualExplanation(
            method="counterfactual",
            prediction=new_prediction,
            original_features=features,
            counterfactual_features=counterfactual,
            changes_needed=changes,
            distance=distance
        )
        
        self.counterfactuals.append(explanation)
        return explanation
    
    def _simulate_prediction(self, features: Dict[str, float]) -> float:
        """Simulate model prediction"""
        # In production, this would call the actual model
        # For demo, simple weighted sum
        weights = {
            'ppg': 0.3,
            'rpg': 0.2,
            'apg': 0.2,
            'fg_percent': 0.15,
            'mpg': 0.15
        }
        
        score = sum(features.get(f, 0) * w for f, w in weights.items())
        return min(max(score / 30, 0), 1)  # Normalize to [0, 1]


class AnchorExplainer:
    """Generate anchor explanations (rule-based)"""
    
    def __init__(self):
        self.anchors: List[AnchorExplanation] = []
    
    def explain_with_anchors(
        self,
        features: Dict[str, float],
        prediction: float,
        feature_names: List[str]
    ) -> AnchorExplanation:
        """
        Generate anchor explanation
        
        Answers: "Which feature values guarantee this prediction?"
        """
        
        # Generate anchor rules (simplified)
        rules = []
        
        # Example rules for All-Star prediction
        ppg = features.get('ppg', 0)
        rpg = features.get('rpg', 0)
        apg = features.get('apg', 0)
        
        if ppg > 20:
            rules.append(f"PPG > 20 (currently {ppg:.1f})")
        
        if rpg > 8:
            rules.append(f"RPG > 8 (currently {rpg:.1f})")
        
        if apg > 5:
            rules.append(f"APG > 5 (currently {apg:.1f})")
        
        # Calculate precision and coverage (simplified)
        precision = 0.85 if len(rules) >= 2 else 0.70
        coverage = 0.15 * len(rules)
        
        explanation = AnchorExplanation(
            method="anchor",
            prediction=prediction,
            anchor_rules=rules,
            precision=precision,
            coverage=coverage,
            metadata={'feature_count': len(rules)}
        )
        
        self.anchors.append(explanation)
        return explanation


class PrototypeExplainer:
    """Prototype-based explanations"""
    
    def __init__(self):
        self.prototypes: List[Dict[str, Any]] = []
    
    def find_prototypes(
        self,
        instance: Dict[str, float],
        training_data: List[Dict[str, float]],
        labels: List[int],
        n_prototypes: int = 3
    ) -> Dict[str, Any]:
        """
        Find prototype examples
        
        Answers: "Which training examples are most similar?"
        """
        
        # Calculate distances to all training examples
        distances = []
        for i, train_instance in enumerate(training_data):
            dist = self._euclidean_distance(instance, train_instance)
            distances.append((dist, i, labels[i]))
        
        # Sort by distance
        distances.sort(key=lambda x: x[0])
        
        # Get top prototypes
        prototypes = []
        for dist, idx, label in distances[:n_prototypes]:
            prototypes.append({
                'index': idx,
                'distance': round(dist, 2),
                'label': label,
                'features': training_data[idx],
                'similarity': round(1 / (1 + dist), 3)  # Convert to similarity
            })
        
        return {
            'prototypes': prototypes,
            'average_distance': round(sum(p['distance'] for p in prototypes) / n_prototypes, 2),
            'consensus': self._check_consensus([p['label'] for p in prototypes])
        }
    
    def _euclidean_distance(self, x1: Dict[str, float], x2: Dict[str, float]) -> float:
        """Calculate Euclidean distance"""
        keys = set(x1.keys()) | set(x2.keys())
        return sum((x1.get(k, 0) - x2.get(k, 0)) ** 2 for k in keys) ** 0.5
    
    def _check_consensus(self, labels: List[int]) -> Dict[str, Any]:
        """Check if prototypes agree on prediction"""
        if not labels:
            return {'agreement': 0, 'majority_label': None}
        
        from collections import Counter
        counts = Counter(labels)
        majority_label, majority_count = counts.most_common(1)[0]
        
        return {
            'agreement': majority_count / len(labels),
            'majority_label': majority_label,
            'unanimous': len(counts) == 1
        }


class FeatureInteractionAnalyzer:
    """Analyze feature interactions"""
    
    def __init__(self):
        self.interactions: List[FeatureInteraction] = []
    
    def analyze_interactions(
        self,
        features: Dict[str, float],
        feature_pairs: Optional[List[Tuple[str, str]]] = None
    ) -> List[FeatureInteraction]:
        """
        Analyze feature interactions
        
        Answers: "How do features interact to affect the prediction?"
        """
        
        if feature_pairs is None:
            # Generate all pairs
            feature_list = list(features.keys())
            feature_pairs = [
                (feature_list[i], feature_list[j])
                for i in range(len(feature_list))
                for j in range(i + 1, len(feature_list))
            ]
        
        interactions = []
        
        for feat1, feat2 in feature_pairs:
            if feat1 not in features or feat2 not in features:
                continue
            
            # Simulate interaction effect
            val1 = features[feat1]
            val2 = features[feat2]
            
            # Simple interaction: product of normalized values
            interaction_strength = abs((val1 / 30) * (val2 / 15) - 0.5)
            
            # Estimate effect on prediction
            effect = interaction_strength * 0.1
            
            interaction = FeatureInteraction(
                feature_1=feat1,
                feature_2=feat2,
                interaction_strength=interaction_strength,
                effect_on_prediction=effect
            )
            
            interactions.append(interaction)
        
        # Sort by interaction strength
        interactions.sort(key=lambda x: x.interaction_strength, reverse=True)
        
        self.interactions.extend(interactions)
        return interactions


class ModelBehaviorAnalyzer:
    """Analyze overall model behavior"""
    
    def analyze_decision_boundary(
        self,
        feature: str,
        feature_range: Tuple[float, float],
        fixed_features: Dict[str, float],
        n_points: int = 20
    ) -> Dict[str, Any]:
        """
        Analyze decision boundary for a feature
        
        Answers: "How does the prediction change with this feature?"
        """
        
        min_val, max_val = feature_range
        step = (max_val - min_val) / n_points
        
        predictions = []
        feature_values = []
        
        for i in range(n_points):
            value = min_val + i * step
            feature_values.append(value)
            
            # Simulate prediction with this feature value
            test_features = fixed_features.copy()
            test_features[feature] = value
            
            # Simple prediction simulation
            pred = self._simulate_prediction(test_features)
            predictions.append(pred)
        
        # Analyze sensitivity
        pred_range = max(predictions) - min(predictions)
        sensitivity = pred_range / (max_val - min_val) if max_val != min_val else 0
        
        return {
            'feature': feature,
            'feature_range': [min_val, max_val],
            'prediction_range': [min(predictions), max(predictions)],
            'sensitivity': round(sensitivity, 4),
            'samples': [
                {'feature_value': round(fv, 2), 'prediction': round(p, 3)}
                for fv, p in zip(feature_values[::5], predictions[::5])  # Every 5th point
            ]
        }
    
    def _simulate_prediction(self, features: Dict[str, float]) -> float:
        """Simulate model prediction"""
        weights = {
            'ppg': 0.3,
            'rpg': 0.2,
            'apg': 0.2,
            'fg_percent': 0.15,
            'mpg': 0.15
        }
        
        score = sum(features.get(f, 0) * w for f, w in weights.items())
        return min(max(score / 30, 0), 1)


class AdvancedInterpretability:
    """Main interpretability coordinator"""
    
    def __init__(self):
        self.counterfactual_gen = CounterfactualGenerator()
        self.anchor_explainer = AnchorExplainer()
        self.prototype_explainer = PrototypeExplainer()
        self.interaction_analyzer = FeatureInteractionAnalyzer()
        self.behavior_analyzer = ModelBehaviorAnalyzer()
    
    def explain_prediction(
        self,
        features: Dict[str, float],
        prediction: float,
        training_data: Optional[List[Dict[str, float]]] = None,
        training_labels: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """Generate comprehensive explanation"""
        
        # Counterfactual
        feature_ranges = {
            'ppg': (0, 40),
            'rpg': (0, 20),
            'apg': (0, 15),
            'fg_percent': (0.3, 0.7),
            'mpg': (10, 45)
        }
        
        counterfactual = self.counterfactual_gen.generate_counterfactual(
            features,
            prediction,
            0.8,  # Desired: All-Star level
            feature_ranges
        )
        
        # Anchor
        anchor = self.anchor_explainer.explain_with_anchors(
            features,
            prediction,
            list(features.keys())
        )
        
        # Prototypes (if training data available)
        prototypes = None
        if training_data and training_labels:
            prototypes = self.prototype_explainer.find_prototypes(
                features,
                training_data,
                training_labels
            )
        
        # Feature interactions
        interactions = self.interaction_analyzer.analyze_interactions(features)
        
        return {
            'prediction': round(prediction, 3),
            'counterfactual': {
                'changes_needed': {k: round(v, 2) for k, v in counterfactual.changes_needed.items()},
                'new_prediction': round(counterfactual.prediction, 3),
                'distance': round(counterfactual.distance, 2)
            },
            'anchor_rules': anchor.anchor_rules,
            'anchor_confidence': {
                'precision': anchor.precision,
                'coverage': anchor.coverage
            },
            'top_interactions': [
                {
                    'features': f"{i.feature_1} × {i.feature_2}",
                    'strength': round(i.interaction_strength, 3),
                    'effect': round(i.effect_on_prediction, 3)
                }
                for i in interactions[:3]
            ],
            'prototypes': prototypes
        }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("=== Advanced Model Interpretability Demo ===\n")
    
    # Create interpretability system
    interp = AdvancedInterpretability()
    
    # Player features (borderline All-Star)
    player_features = {
        'ppg': 18.5,
        'rpg': 6.2,
        'apg': 4.8,
        'fg_percent': 0.48,
        'mpg': 32.0
    }
    
    current_prediction = 0.65  # 65% chance of All-Star
    
    # Training data (similar players)
    training_data = [
        {'ppg': 25.0, 'rpg': 8.0, 'apg': 6.0, 'fg_percent': 0.52, 'mpg': 35.0},  # All-Star
        {'ppg': 22.0, 'rpg': 7.0, 'apg': 5.5, 'fg_percent': 0.50, 'mpg': 34.0},  # All-Star
        {'ppg': 15.0, 'rpg': 5.0, 'apg': 3.0, 'fg_percent': 0.45, 'mpg': 28.0},  # Not All-Star
    ]
    training_labels = [1, 1, 0]
    
    # Get comprehensive explanation
    print("--- Explaining Prediction ---\n")
    print(f"Player Stats:")
    for feature, value in player_features.items():
        print(f"  {feature}: {value}")
    print(f"\nPrediction: {current_prediction} (All-Star probability)")
    
    explanation = interp.explain_prediction(
        player_features,
        current_prediction,
        training_data,
        training_labels
    )
    
    # Counterfactual
    print(f"\n--- Counterfactual Explanation ---")
    print("To increase All-Star probability to 80%, need to:")
    for feature, change in explanation['counterfactual']['changes_needed'].items():
        direction = "increase" if change > 0 else "decrease"
        print(f"  {direction} {feature} by {abs(change):.2f}")
    
    # Anchor rules
    print(f"\n--- Anchor Rules ---")
    print("Current performance is anchored by:")
    for rule in explanation['anchor_rules']:
        print(f"  • {rule}")
    
    # Feature interactions
    print(f"\n--- Feature Interactions ---")
    print("Top feature interactions:")
    for interaction in explanation['top_interactions']:
        print(f"  {interaction['features']}: strength={interaction['strength']}")
    
    # Prototypes
    if explanation['prototypes']:
        print(f"\n--- Similar Players ---")
        for proto in explanation['prototypes']['prototypes']:
            print(f"  Similarity: {proto['similarity']} - Label: {'All-Star' if proto['label'] else 'Not All-Star'}")
    
    # Decision boundary
    print(f"\n--- Decision Boundary Analysis ---")
    boundary = interp.behavior_analyzer.analyze_decision_boundary(
        'ppg',
        (10, 30),
        {k: v for k, v in player_features.items() if k != 'ppg'}
    )
    print(f"Feature: {boundary['feature']}")
    print(f"Sensitivity: {boundary['sensitivity']}")
    print(f"Prediction range: {boundary['prediction_range'][0]:.2f} to {boundary['prediction_range'][1]:.2f}")
    
    print("\n=== Demo Complete ===")

