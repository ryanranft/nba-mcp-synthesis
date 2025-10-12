"""
Advanced Monitoring & Forecasting

Enhanced monitoring with predictive capabilities:
- Anomaly forecasting
- Trend prediction
- Capacity planning
- SLA monitoring
- Predictive alerting
- Health scoring

Features:
- Time-series forecasting
- Anomaly prediction
- Resource forecasting
- Pattern recognition
- Automated thresholds
- Predictive maintenance

Use Cases:
- Capacity planning
- Proactive alerting
- Cost forecasting
- Performance prediction
- Failure prevention
"""

import logging
import statistics
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque
from enum import Enum

logger = logging.getLogger(__name__)


class ForecastMethod(Enum):
    """Forecasting methods"""
    MOVING_AVERAGE = "moving_average"
    EXPONENTIAL_SMOOTHING = "exponential_smoothing"
    LINEAR_REGRESSION = "linear_regression"
    SEASONAL = "seasonal"


@dataclass
class TimeSeriesPoint:
    """Single time-series data point"""
    timestamp: datetime
    value: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Forecast:
    """Forecast result"""
    timestamp: datetime
    predicted_value: float
    confidence_lower: float
    confidence_upper: float
    method: ForecastMethod


class TimeSeriesForecaster:
    """Forecast time-series metrics"""

    def __init__(self, history_size: int = 1000):
        self.history: deque = deque(maxlen=history_size)

    def add_point(self, timestamp: datetime, value: float) -> None:
        """Add data point to history"""
        self.history.append(TimeSeriesPoint(timestamp, value))

    def forecast_moving_average(
        self,
        periods_ahead: int = 1,
        window_size: int = 10
    ) -> List[Forecast]:
        """Simple moving average forecast"""
        if len(self.history) < window_size:
            return []

        forecasts = []
        values = [p.value for p in self.history]

        for i in range(periods_ahead):
            # Calculate moving average of last window_size points
            window = values[-(window_size + i):len(values) - i] if i > 0 else values[-window_size:]
            predicted = statistics.mean(window)

            # Estimate confidence interval (simplified)
            std_dev = statistics.stdev(window) if len(window) > 1 else 0
            confidence_range = 1.96 * std_dev  # 95% confidence

            # Estimate timestamp
            last_point = list(self.history)[-1]
            forecast_time = last_point.timestamp + timedelta(minutes=(i + 1))

            forecasts.append(Forecast(
                timestamp=forecast_time,
                predicted_value=predicted,
                confidence_lower=predicted - confidence_range,
                confidence_upper=predicted + confidence_range,
                method=ForecastMethod.MOVING_AVERAGE
            ))

        return forecasts

    def forecast_exponential_smoothing(
        self,
        periods_ahead: int = 1,
        alpha: float = 0.3
    ) -> List[Forecast]:
        """Exponential smoothing forecast"""
        if len(self.history) < 2:
            return []

        values = [p.value for p in self.history]

        # Calculate exponential moving average
        ema = values[0]
        for value in values[1:]:
            ema = alpha * value + (1 - alpha) * ema

        # Forecast (assumes constant trend)
        forecasts = []
        last_point = list(self.history)[-1]

        for i in range(periods_ahead):
            forecast_time = last_point.timestamp + timedelta(minutes=(i + 1))

            # Simple EMA forecast (constant)
            predicted = ema

            # Estimate confidence interval
            residuals = [v - ema for v in values[-20:]]  # Last 20 points
            std_dev = statistics.stdev(residuals) if len(residuals) > 1 else 0
            confidence_range = 1.96 * std_dev

            forecasts.append(Forecast(
                timestamp=forecast_time,
                predicted_value=predicted,
                confidence_lower=predicted - confidence_range,
                confidence_upper=predicted + confidence_range,
                method=ForecastMethod.EXPONENTIAL_SMOOTHING
            ))

        return forecasts

    def forecast_linear_regression(
        self,
        periods_ahead: int = 1
    ) -> List[Forecast]:
        """Linear regression forecast"""
        if len(self.history) < 10:
            return []

        points = list(self.history)
        n = len(points)

        # Convert to numeric x (time index)
        x_values = list(range(n))
        y_values = [p.value for p in points]

        # Calculate linear regression: y = mx + b
        x_mean = statistics.mean(x_values)
        y_mean = statistics.mean(y_values)

        numerator = sum((x_values[i] - x_mean) * (y_values[i] - y_mean) for i in range(n))
        denominator = sum((x_values[i] - x_mean) ** 2 for i in range(n))

        slope = numerator / denominator if denominator != 0 else 0
        intercept = y_mean - slope * x_mean

        # Forecast
        forecasts = []
        last_point = points[-1]

        for i in range(periods_ahead):
            forecast_time = last_point.timestamp + timedelta(minutes=(i + 1))
            x_forecast = n + i
            predicted = slope * x_forecast + intercept

            # Estimate confidence interval
            residuals = [y_values[i] - (slope * x_values[i] + intercept) for i in range(n)]
            std_dev = statistics.stdev(residuals) if len(residuals) > 1 else 0
            confidence_range = 1.96 * std_dev

            forecasts.append(Forecast(
                timestamp=forecast_time,
                predicted_value=predicted,
                confidence_lower=predicted - confidence_range,
                confidence_upper=predicted + confidence_range,
                method=ForecastMethod.LINEAR_REGRESSION
            ))

        return forecasts


class AnomalyPredictor:
    """Predict future anomalies"""

    def __init__(self):
        self.patterns: List[Dict[str, Any]] = []

    def learn_pattern(self, pattern_type: str, conditions: Dict[str, Any]) -> None:
        """Learn anomaly pattern"""
        self.patterns.append({
            'type': pattern_type,
            'conditions': conditions,
            'learned_at': datetime.now()
        })

    def predict_anomaly_likelihood(
        self,
        current_metrics: Dict[str, float],
        forecast_horizon_minutes: int = 60
    ) -> Dict[str, Any]:
        """Predict likelihood of anomaly"""

        # Simple heuristic-based prediction
        risk_score = 0.0
        risk_factors = []

        # Check metric trends
        cpu = current_metrics.get('cpu_percent', 0)
        memory = current_metrics.get('memory_percent', 0)
        latency = current_metrics.get('latency_ms', 0)

        if cpu > 70:
            risk_score += 0.3
            risk_factors.append("High CPU usage")

        if memory > 80:
            risk_score += 0.3
            risk_factors.append("High memory usage")

        if latency > 500:
            risk_score += 0.2
            risk_factors.append("High latency")

        # Check for combined conditions
        if cpu > 70 and memory > 80:
            risk_score += 0.2
            risk_factors.append("Resource contention likely")

        risk_score = min(risk_score, 1.0)

        # Determine risk level
        if risk_score >= 0.7:
            risk_level = "HIGH"
        elif risk_score >= 0.4:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        return {
            'risk_score': round(risk_score, 2),
            'risk_level': risk_level,
            'risk_factors': risk_factors,
            'forecast_horizon_minutes': forecast_horizon_minutes,
            'recommendation': self._get_recommendation(risk_level, risk_factors)
        }

    def _get_recommendation(self, risk_level: str, factors: List[str]) -> str:
        """Get recommendation based on risk"""
        if risk_level == "HIGH":
            return "Immediate action recommended: Scale resources or investigate anomaly"
        elif risk_level == "MEDIUM":
            return "Monitor closely: Prepare to scale if trend continues"
        else:
            return "Normal operation: Continue monitoring"


class CapacityPlanner:
    """Plan resource capacity needs"""

    def __init__(self, forecaster: TimeSeriesForecaster):
        self.forecaster = forecaster

    def plan_capacity(
        self,
        current_capacity: float,
        target_utilization: float = 0.7,
        planning_horizon_days: int = 30
    ) -> Dict[str, Any]:
        """Plan capacity requirements"""

        # Forecast demand
        periods = planning_horizon_days * 24  # Hourly forecasts
        forecasts = self.forecaster.forecast_linear_regression(periods_ahead=periods)

        if not forecasts:
            return {
                'status': 'insufficient_data',
                'recommendation': 'Collect more data for accurate planning'
            }

        # Find peak demand
        peak_demand = max(f.predicted_value for f in forecasts)
        avg_demand = statistics.mean(f.predicted_value for f in forecasts)

        # Calculate required capacity
        required_capacity = peak_demand / target_utilization

        # Determine if scaling needed
        needs_scaling = required_capacity > current_capacity
        scale_factor = required_capacity / current_capacity if current_capacity > 0 else 1.0

        # When to scale
        if needs_scaling:
            # Find when we'll hit capacity
            for i, forecast in enumerate(forecasts):
                if forecast.predicted_value > current_capacity * target_utilization:
                    days_until_scale = i / 24
                    break
            else:
                days_until_scale = planning_horizon_days
        else:
            days_until_scale = None

        return {
            'current_capacity': current_capacity,
            'peak_forecast': round(peak_demand, 2),
            'average_forecast': round(avg_demand, 2),
            'required_capacity': round(required_capacity, 2),
            'needs_scaling': needs_scaling,
            'scale_factor': round(scale_factor, 2),
            'days_until_scale_needed': days_until_scale,
            'recommendation': self._get_capacity_recommendation(
                needs_scaling, days_until_scale, scale_factor
            )
        }

    def _get_capacity_recommendation(
        self,
        needs_scaling: bool,
        days_until: Optional[float],
        scale_factor: float
    ) -> str:
        """Get capacity recommendation"""
        if not needs_scaling:
            return "Current capacity sufficient for planning horizon"

        if days_until and days_until < 7:
            return f"Urgent: Scale capacity by {scale_factor:.1f}x within {days_until:.0f} days"
        elif days_until and days_until < 14:
            return f"Soon: Plan to scale capacity by {scale_factor:.1f}x within {days_until:.0f} days"
        else:
            return f"Future: Consider scaling capacity by {scale_factor:.1f}x in coming weeks"


class HealthScorer:
    """Calculate system health score"""

    def calculate_health_score(self, metrics: Dict[str, float]) -> Dict[str, Any]:
        """Calculate overall health score"""

        scores = {}

        # Performance score (0-100)
        latency = metrics.get('latency_ms', 0)
        if latency < 100:
            perf_score = 100
        elif latency < 500:
            perf_score = 100 - ((latency - 100) / 4)
        else:
            perf_score = max(0, 100 - ((latency - 100) / 2))
        scores['performance'] = perf_score

        # Availability score
        uptime = metrics.get('uptime_percent', 100)
        scores['availability'] = uptime

        # Resource score
        cpu = metrics.get('cpu_percent', 0)
        memory = metrics.get('memory_percent', 0)
        resource_usage = max(cpu, memory)
        resource_score = max(0, 100 - resource_usage)
        scores['resources'] = resource_score

        # Error rate score
        error_rate = metrics.get('error_rate_percent', 0)
        error_score = max(0, 100 - (error_rate * 10))
        scores['errors'] = error_score

        # Overall health (weighted average)
        overall_health = (
            scores['performance'] * 0.3 +
            scores['availability'] * 0.3 +
            scores['resources'] * 0.2 +
            scores['errors'] * 0.2
        )

        # Health status
        if overall_health >= 90:
            status = "EXCELLENT"
            color = "green"
        elif overall_health >= 75:
            status = "GOOD"
            color = "green"
        elif overall_health >= 60:
            status = "FAIR"
            color = "yellow"
        elif overall_health >= 40:
            status = "POOR"
            color = "orange"
        else:
            status = "CRITICAL"
            color = "red"

        return {
            'overall_score': round(overall_health, 1),
            'status': status,
            'color': color,
            'component_scores': {k: round(v, 1) for k, v in scores.items()},
            'metrics': metrics
        }


class AdvancedMonitoring:
    """Main advanced monitoring coordinator"""

    def __init__(self):
        self.forecaster = TimeSeriesForecaster()
        self.anomaly_predictor = AnomalyPredictor()
        self.capacity_planner = CapacityPlanner(self.forecaster)
        self.health_scorer = HealthScorer()

    def add_metric(self, timestamp: datetime, value: float) -> None:
        """Add metric for forecasting"""
        self.forecaster.add_point(timestamp, value)

    def get_monitoring_dashboard(
        self,
        current_metrics: Dict[str, float],
        current_capacity: float = 100.0
    ) -> Dict[str, Any]:
        """Get comprehensive monitoring dashboard"""

        # Health score
        health = self.health_scorer.calculate_health_score(current_metrics)

        # Anomaly prediction
        anomaly = self.anomaly_predictor.predict_anomaly_likelihood(current_metrics)

        # Capacity planning
        capacity = self.capacity_planner.plan_capacity(current_capacity)

        # Forecasts (if data available)
        forecasts_ma = self.forecaster.forecast_moving_average(periods_ahead=12)
        forecasts_lr = self.forecaster.forecast_linear_regression(periods_ahead=12)

        return {
            'health': health,
            'anomaly_prediction': anomaly,
            'capacity_planning': capacity,
            'forecasts': {
                'moving_average': [
                    {
                        'timestamp': f.timestamp.isoformat(),
                        'value': round(f.predicted_value, 2),
                        'confidence': [round(f.confidence_lower, 2), round(f.confidence_upper, 2)]
                    }
                    for f in forecasts_ma[:6]  # Next 6 periods
                ],
                'trend': [
                    {
                        'timestamp': f.timestamp.isoformat(),
                        'value': round(f.predicted_value, 2)
                    }
                    for f in forecasts_lr[:6]
                ]
            }
        }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("=== Advanced Monitoring Demo ===\n")

    # Create monitoring
    monitoring = AdvancedMonitoring()

    # Add historical data
    print("--- Adding Historical Data ---\n")
    base_time = datetime.now() - timedelta(hours=24)
    for i in range(100):
        timestamp = base_time + timedelta(minutes=i * 15)
        value = 50 + i * 0.5 + (i % 10) * 2  # Trending up with noise
        monitoring.add_metric(timestamp, value)

    print("✓ Added 100 data points")

    # Current metrics
    current_metrics = {
        'latency_ms': 150,
        'cpu_percent': 65,
        'memory_percent': 70,
        'uptime_percent': 99.9,
        'error_rate_percent': 0.1
    }

    # Get dashboard
    print("\n--- Monitoring Dashboard ---\n")
    dashboard = monitoring.get_monitoring_dashboard(current_metrics, current_capacity=100)

    # Health
    print("Health Status:")
    print(f"  Overall: {dashboard['health']['overall_score']}/100 ({dashboard['health']['status']})")
    print(f"  Performance: {dashboard['health']['component_scores']['performance']}")
    print(f"  Availability: {dashboard['health']['component_scores']['availability']}")
    print(f"  Resources: {dashboard['health']['component_scores']['resources']}")

    # Anomaly prediction
    print(f"\nAnomaly Prediction:")
    print(f"  Risk Level: {dashboard['anomaly_prediction']['risk_level']}")
    print(f"  Risk Score: {dashboard['anomaly_prediction']['risk_score']}")
    print(f"  Recommendation: {dashboard['anomaly_prediction']['recommendation']}")

    # Capacity
    print(f"\nCapacity Planning:")
    print(f"  Needs Scaling: {dashboard['capacity_planning']['needs_scaling']}")
    print(f"  Recommendation: {dashboard['capacity_planning']['recommendation']}")

    print("\n=== Demo Complete ===")

