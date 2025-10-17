"""
Advanced Metrics & Monitoring

Advanced metrics collection and analysis:
- Custom metrics
- Histogram metrics
- Time-series analysis
- Metric aggregation
- Percentile calculations
- Metric forecasting

Features:
- Multi-dimensional metrics
- Metric labels and tags
- Histogram buckets
- Summary statistics
- Metric retention
- Query optimization

Use Cases:
- Performance monitoring
- SLA tracking
- Capacity planning
- Anomaly detection
- Trend analysis
"""

import time
import logging
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
from enum import Enum
import threading
import statistics

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Metric types"""

    COUNTER = "counter"  # Monotonically increasing
    GAUGE = "gauge"  # Can go up or down
    HISTOGRAM = "histogram"  # Distribution of values
    SUMMARY = "summary"  # Pre-calculated percentiles


@dataclass
class MetricValue:
    """Single metric value"""

    value: float
    timestamp: datetime
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class MetricSample:
    """Metric sample with labels"""

    name: str
    type: MetricType
    value: float
    timestamp: datetime
    labels: Dict[str, str] = field(default_factory=dict)

    def label_key(self) -> str:
        """Get unique key for labels"""
        if not self.labels:
            return ""
        sorted_labels = sorted(self.labels.items())
        return ",".join(f"{k}={v}" for k, v in sorted_labels)


class Counter:
    """Counter metric (monotonically increasing)"""

    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.values: Dict[str, float] = defaultdict(float)
        self._lock = threading.RLock()

    def inc(self, amount: float = 1.0, labels: Optional[Dict[str, str]] = None) -> None:
        """Increment counter"""
        key = self._label_key(labels)
        with self._lock:
            self.values[key] += amount

    def get(self, labels: Optional[Dict[str, str]] = None) -> float:
        """Get counter value"""
        key = self._label_key(labels)
        with self._lock:
            return self.values.get(key, 0.0)

    def _label_key(self, labels: Optional[Dict[str, str]]) -> str:
        """Get label key"""
        if not labels:
            return ""
        sorted_labels = sorted(labels.items())
        return ",".join(f"{k}={v}" for k, v in sorted_labels)

    def collect(self) -> List[MetricSample]:
        """Collect all samples"""
        samples = []
        with self._lock:
            for label_key, value in self.values.items():
                labels = self._parse_label_key(label_key)
                samples.append(
                    MetricSample(
                        name=self.name,
                        type=MetricType.COUNTER,
                        value=value,
                        timestamp=datetime.now(),
                        labels=labels,
                    )
                )
        return samples

    def _parse_label_key(self, key: str) -> Dict[str, str]:
        """Parse label key back to dict"""
        if not key:
            return {}
        labels = {}
        for pair in key.split(","):
            k, v = pair.split("=")
            labels[k] = v
        return labels


class Gauge:
    """Gauge metric (can go up or down)"""

    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.values: Dict[str, float] = defaultdict(float)
        self._lock = threading.RLock()

    def set(self, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Set gauge value"""
        key = self._label_key(labels)
        with self._lock:
            self.values[key] = value

    def inc(self, amount: float = 1.0, labels: Optional[Dict[str, str]] = None) -> None:
        """Increment gauge"""
        key = self._label_key(labels)
        with self._lock:
            self.values[key] += amount

    def dec(self, amount: float = 1.0, labels: Optional[Dict[str, str]] = None) -> None:
        """Decrement gauge"""
        key = self._label_key(labels)
        with self._lock:
            self.values[key] -= amount

    def get(self, labels: Optional[Dict[str, str]] = None) -> float:
        """Get gauge value"""
        key = self._label_key(labels)
        with self._lock:
            return self.values.get(key, 0.0)

    def _label_key(self, labels: Optional[Dict[str, str]]) -> str:
        """Get label key"""
        if not labels:
            return ""
        sorted_labels = sorted(labels.items())
        return ",".join(f"{k}={v}" for k, v in sorted_labels)

    def collect(self) -> List[MetricSample]:
        """Collect all samples"""
        samples = []
        with self._lock:
            for label_key, value in self.values.items():
                labels = self._parse_label_key(label_key)
                samples.append(
                    MetricSample(
                        name=self.name,
                        type=MetricType.GAUGE,
                        value=value,
                        timestamp=datetime.now(),
                        labels=labels,
                    )
                )
        return samples

    def _parse_label_key(self, key: str) -> Dict[str, str]:
        """Parse label key"""
        if not key:
            return {}
        labels = {}
        for pair in key.split(","):
            k, v = pair.split("=")
            labels[k] = v
        return labels


class Histogram:
    """Histogram metric (distribution of values)"""

    def __init__(
        self, name: str, description: str = "", buckets: Optional[List[float]] = None
    ):
        self.name = name
        self.description = description
        self.buckets = buckets or [
            0.005,
            0.01,
            0.025,
            0.05,
            0.075,
            0.1,
            0.25,
            0.5,
            0.75,
            1.0,
            2.5,
            5.0,
            7.5,
            10.0,
            float("inf"),
        ]

        # Store observations per label set
        self.observations: Dict[str, List[float]] = defaultdict(list)
        self.counts: Dict[str, int] = defaultdict(int)
        self.sums: Dict[str, float] = defaultdict(float)

        self._lock = threading.RLock()

    def observe(self, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Observe a value"""
        key = self._label_key(labels)
        with self._lock:
            self.observations[key].append(value)
            self.counts[key] += 1
            self.sums[key] += value

    def get_percentiles(
        self, percentiles: List[float], labels: Optional[Dict[str, str]] = None
    ) -> Dict[float, float]:
        """Calculate percentiles"""
        key = self._label_key(labels)
        with self._lock:
            obs = self.observations.get(key, [])
            if not obs:
                return {p: 0.0 for p in percentiles}

            sorted_obs = sorted(obs)
            results = {}
            for p in percentiles:
                idx = int(len(sorted_obs) * p / 100.0)
                idx = min(idx, len(sorted_obs) - 1)
                results[p] = sorted_obs[idx]

            return results

    def get_histogram(
        self, labels: Optional[Dict[str, str]] = None
    ) -> Dict[float, int]:
        """Get histogram buckets"""
        key = self._label_key(labels)
        with self._lock:
            obs = self.observations.get(key, [])

            histogram = {bucket: 0 for bucket in self.buckets}
            for value in obs:
                for bucket in self.buckets:
                    if value <= bucket:
                        histogram[bucket] += 1

            return histogram

    def get_stats(self, labels: Optional[Dict[str, str]] = None) -> Dict[str, float]:
        """Get summary statistics"""
        key = self._label_key(labels)
        with self._lock:
            obs = self.observations.get(key, [])
            if not obs:
                return {
                    "count": 0,
                    "sum": 0.0,
                    "mean": 0.0,
                    "min": 0.0,
                    "max": 0.0,
                    "stddev": 0.0,
                }

            return {
                "count": len(obs),
                "sum": sum(obs),
                "mean": statistics.mean(obs),
                "min": min(obs),
                "max": max(obs),
                "stddev": statistics.stdev(obs) if len(obs) > 1 else 0.0,
            }

    def _label_key(self, labels: Optional[Dict[str, str]]) -> str:
        """Get label key"""
        if not labels:
            return ""
        sorted_labels = sorted(labels.items())
        return ",".join(f"{k}={v}" for k, v in sorted_labels)

    def collect(self) -> List[MetricSample]:
        """Collect all samples"""
        samples = []
        with self._lock:
            for label_key in self.observations.keys():
                labels = self._parse_label_key(label_key)

                # Add count
                samples.append(
                    MetricSample(
                        name=f"{self.name}_count",
                        type=MetricType.HISTOGRAM,
                        value=self.counts[label_key],
                        timestamp=datetime.now(),
                        labels=labels,
                    )
                )

                # Add sum
                samples.append(
                    MetricSample(
                        name=f"{self.name}_sum",
                        type=MetricType.HISTOGRAM,
                        value=self.sums[label_key],
                        timestamp=datetime.now(),
                        labels=labels,
                    )
                )

                # Add buckets
                histogram = self.get_histogram(labels)
                for bucket, count in histogram.items():
                    bucket_labels = {**labels, "le": str(bucket)}
                    samples.append(
                        MetricSample(
                            name=f"{self.name}_bucket",
                            type=MetricType.HISTOGRAM,
                            value=count,
                            timestamp=datetime.now(),
                            labels=bucket_labels,
                        )
                    )

        return samples

    def _parse_label_key(self, key: str) -> Dict[str, str]:
        """Parse label key"""
        if not key:
            return {}
        labels = {}
        for pair in key.split(","):
            k, v = pair.split("=")
            labels[k] = v
        return labels


class TimeSeriesMetric:
    """Time-series metric with history"""

    def __init__(self, name: str, max_age_seconds: int = 3600):
        self.name = name
        self.max_age = max_age_seconds
        self.values: deque = deque()
        self._lock = threading.RLock()

    def add(self, value: float, timestamp: Optional[datetime] = None) -> None:
        """Add value to time series"""
        if timestamp is None:
            timestamp = datetime.now()

        with self._lock:
            self.values.append(MetricValue(value=value, timestamp=timestamp))
            self._cleanup()

    def _cleanup(self) -> None:
        """Remove old values"""
        cutoff = datetime.now() - timedelta(seconds=self.max_age)
        while self.values and self.values[0].timestamp < cutoff:
            self.values.popleft()

    def get_range(
        self, start: Optional[datetime] = None, end: Optional[datetime] = None
    ) -> List[MetricValue]:
        """Get values in time range"""
        if start is None:
            start = datetime.now() - timedelta(seconds=self.max_age)
        if end is None:
            end = datetime.now()

        with self._lock:
            return [v for v in self.values if start <= v.timestamp <= end]

    def get_stats(self, window_seconds: int = 60) -> Dict[str, float]:
        """Get statistics for time window"""
        end = datetime.now()
        start = end - timedelta(seconds=window_seconds)

        values = [v.value for v in self.get_range(start, end)]

        if not values:
            return {"count": 0, "mean": 0.0, "min": 0.0, "max": 0.0, "rate": 0.0}

        return {
            "count": len(values),
            "mean": statistics.mean(values),
            "min": min(values),
            "max": max(values),
            "rate": len(values) / window_seconds,
        }


class MetricsRegistry:
    """Central metrics registry"""

    def __init__(self):
        self.counters: Dict[str, Counter] = {}
        self.gauges: Dict[str, Gauge] = {}
        self.histograms: Dict[str, Histogram] = {}
        self._lock = threading.RLock()

    def counter(self, name: str, description: str = "") -> Counter:
        """Get or create counter"""
        with self._lock:
            if name not in self.counters:
                self.counters[name] = Counter(name, description)
            return self.counters[name]

    def gauge(self, name: str, description: str = "") -> Gauge:
        """Get or create gauge"""
        with self._lock:
            if name not in self.gauges:
                self.gauges[name] = Gauge(name, description)
            return self.gauges[name]

    def histogram(
        self, name: str, description: str = "", buckets: Optional[List[float]] = None
    ) -> Histogram:
        """Get or create histogram"""
        with self._lock:
            if name not in self.histograms:
                self.histograms[name] = Histogram(name, description, buckets)
            return self.histograms[name]

    def collect_all(self) -> List[MetricSample]:
        """Collect all metrics"""
        samples = []

        with self._lock:
            for counter in self.counters.values():
                samples.extend(counter.collect())

            for gauge in self.gauges.values():
                samples.extend(gauge.collect())

            for histogram in self.histograms.values():
                samples.extend(histogram.collect())

        return samples

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of all metrics"""
        with self._lock:
            return {
                "counters": len(self.counters),
                "gauges": len(self.gauges),
                "histograms": len(self.histograms),
                "total_metrics": len(self.counters)
                + len(self.gauges)
                + len(self.histograms),
            }


# Global registry
_registry = None
_registry_lock = threading.Lock()


def get_registry() -> MetricsRegistry:
    """Get global metrics registry"""
    global _registry
    with _registry_lock:
        if _registry is None:
            _registry = MetricsRegistry()
        return _registry


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("=== Advanced Metrics Demo ===\n")

    # Get registry
    registry = get_registry()

    # Counter example
    print("--- Counter Metrics ---\n")
    requests = registry.counter("http_requests_total", "Total HTTP requests")

    requests.inc(labels={"method": "GET", "status": "200"})
    requests.inc(labels={"method": "GET", "status": "200"})
    requests.inc(labels={"method": "POST", "status": "201"})
    requests.inc(amount=5, labels={"method": "GET", "status": "404"})

    print(f"GET 200: {requests.get(labels={'method': 'GET', 'status': '200'})}")
    print(f"POST 201: {requests.get(labels={'method': 'POST', 'status': '201'})}")
    print(f"GET 404: {requests.get(labels={'method': 'GET', 'status': '404'})}")

    # Gauge example
    print("\n--- Gauge Metrics ---\n")
    active_users = registry.gauge("active_users", "Currently active users")

    active_users.set(150)
    active_users.inc(10)
    active_users.dec(5)

    print(f"Active users: {active_users.get()}")

    # Histogram example
    print("\n--- Histogram Metrics ---\n")
    response_time = registry.histogram(
        "response_time_seconds",
        "HTTP response time in seconds",
        buckets=[0.1, 0.5, 1.0, 2.0, 5.0, float("inf")],
    )

    # Simulate requests
    for t in [0.05, 0.15, 0.3, 0.7, 1.2, 0.1, 0.4, 2.5, 0.2]:
        response_time.observe(t)

    stats = response_time.get_stats()
    print(f"Count: {stats['count']}")
    print(f"Mean: {stats['mean']:.3f}s")
    print(f"Min: {stats['min']:.3f}s")
    print(f"Max: {stats['max']:.3f}s")

    percentiles = response_time.get_percentiles([50, 90, 95, 99])
    print(f"\nPercentiles:")
    for p, val in percentiles.items():
        print(f"  P{p}: {val:.3f}s")

    # Time series example
    print("\n--- Time Series Metrics ---\n")
    cpu_usage = TimeSeriesMetric("cpu_usage", max_age_seconds=300)

    # Add some values
    for i in range(10):
        cpu_usage.add(50 + i * 2)
        time.sleep(0.01)

    ts_stats = cpu_usage.get_stats(window_seconds=10)
    print(f"Recent CPU usage:")
    print(f"  Count: {ts_stats['count']}")
    print(f"  Mean: {ts_stats['mean']:.1f}%")
    print(f"  Min: {ts_stats['min']:.1f}%")
    print(f"  Max: {ts_stats['max']:.1f}%")

    # Registry summary
    print("\n--- Registry Summary ---")
    summary = registry.get_metrics_summary()
    print(f"Total metrics: {summary['total_metrics']}")
    print(f"  Counters: {summary['counters']}")
    print(f"  Gauges: {summary['gauges']}")
    print(f"  Histograms: {summary['histograms']}")

    print("\n=== Demo Complete ===")
