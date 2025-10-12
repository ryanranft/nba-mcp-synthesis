"""
Advanced Performance Optimizer

Comprehensive performance optimization:
- Query optimization
- Cache tuning
- Auto-scaling strategies
- Resource optimization
- Bottleneck detection
- Performance recommendations

Features:
- Automated profiling
- Query analysis
- Cache optimization
- Resource right-sizing
- Load balancing
- Auto-tuning

Use Cases:
- Performance tuning
- Cost optimization
- Capacity planning
- Bottleneck resolution
- System optimization
"""

import logging
import time
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict

logger = logging.getLogger(__name__)


class BottleneckType(Enum):
    """Types of performance bottlenecks"""
    CPU = "cpu"
    MEMORY = "memory"
    DISK_IO = "disk_io"
    NETWORK = "network"
    DATABASE = "database"
    CACHE = "cache"


class OptimizationStrategy(Enum):
    """Optimization strategies"""
    SCALE_UP = "scale_up"  # Vertical scaling
    SCALE_OUT = "scale_out"  # Horizontal scaling
    OPTIMIZE_CODE = "optimize_code"
    ADD_CACHE = "add_cache"
    OPTIMIZE_QUERY = "optimize_query"
    ADD_INDEX = "add_index"


@dataclass
class PerformanceMetrics:
    """Performance metrics snapshot"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_io_mbps: float
    network_mbps: float
    request_rate: float
    avg_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float


@dataclass
class Bottleneck:
    """Identified bottleneck"""
    bottleneck_type: BottleneckType
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    description: str
    impact_score: float
    detected_at: datetime = field(default_factory=datetime.now)


@dataclass
class Optimization:
    """Performance optimization recommendation"""
    strategy: OptimizationStrategy
    priority: str  # LOW, MEDIUM, HIGH, CRITICAL
    description: str
    estimated_improvement: float  # Percentage improvement
    estimated_cost: float  # Monthly cost in USD
    implementation_time_hours: float


class QueryOptimizer:
    """Optimize database queries"""
    
    def __init__(self):
        self.slow_queries: List[Dict[str, Any]] = []
    
    def analyze_query(self, query: str, execution_time_ms: float) -> Dict[str, Any]:
        """Analyze query performance"""
        
        issues = []
        recommendations = []
        
        # Check for SELECT *
        if "SELECT *" in query.upper():
            issues.append("Using SELECT * fetches unnecessary columns")
            recommendations.append("Specify only required columns")
        
        # Check for missing WHERE clause
        if "WHERE" not in query.upper() and "SELECT" in query.upper():
            issues.append("Query lacks WHERE clause (full table scan)")
            recommendations.append("Add WHERE clause to filter rows")
        
        # Check for missing indexes (simplified)
        if "WHERE" in query.upper() and execution_time_ms > 100:
            issues.append("Slow WHERE clause execution suggests missing index")
            recommendations.append("Add index on filtered columns")
        
        # Check for N+1 queries
        if execution_time_ms < 10 and len(self.slow_queries) > 10:
            issues.append("Possible N+1 query pattern detected")
            recommendations.append("Use JOIN instead of multiple queries")
        
        # Check for subqueries
        if query.upper().count("SELECT") > 1:
            issues.append("Nested subqueries can be inefficient")
            recommendations.append("Consider using JOINs or CTEs")
        
        # Calculate optimization potential
        if execution_time_ms > 1000:
            optimization_potential = 80  # 80% improvement possible
        elif execution_time_ms > 500:
            optimization_potential = 60
        elif execution_time_ms > 100:
            optimization_potential = 40
        else:
            optimization_potential = 20
        
        return {
            'query': query[:100] + "..." if len(query) > 100 else query,
            'execution_time_ms': execution_time_ms,
            'issues': issues,
            'recommendations': recommendations,
            'optimization_potential': optimization_potential,
            'needs_optimization': execution_time_ms > 100 or len(issues) > 0
        }
    
    def recommend_indexes(self, query: str) -> List[str]:
        """Recommend indexes for query"""
        
        recommendations = []
        
        # Extract WHERE clause columns (simplified)
        if "WHERE" in query.upper():
            # Simple pattern matching
            import re
            where_match = re.search(r'WHERE\s+(\w+)', query, re.IGNORECASE)
            if where_match:
                column = where_match.group(1)
                recommendations.append(f"CREATE INDEX idx_{column} ON table_name ({column});")
        
        # Extract JOIN columns
        if "JOIN" in query.upper():
            join_match = re.search(r'ON\s+\w+\.(\w+)\s*=', query, re.IGNORECASE)
            if join_match:
                column = join_match.group(1)
                recommendations.append(f"CREATE INDEX idx_{column}_fk ON table_name ({column});")
        
        return recommendations


class CacheOptimizer:
    """Optimize caching strategy"""
    
    def __init__(self):
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0
        }
    
    def analyze_cache_performance(
        self,
        hit_rate: float,
        avg_ttl_seconds: int,
        cache_size_mb: float,
        memory_limit_mb: float
    ) -> Dict[str, Any]:
        """Analyze cache performance"""
        
        issues = []
        recommendations = []
        
        # Check hit rate
        if hit_rate < 0.7:
            issues.append(f"Low cache hit rate: {hit_rate:.1%}")
            recommendations.append("Increase cache size or adjust TTL")
        elif hit_rate < 0.85:
            recommendations.append("Consider prewarming cache for hot data")
        
        # Check memory usage
        memory_usage = cache_size_mb / memory_limit_mb if memory_limit_mb > 0 else 0
        
        if memory_usage > 0.9:
            issues.append(f"Cache memory near limit: {memory_usage:.1%}")
            recommendations.append("Increase memory limit or reduce TTL")
        elif memory_usage < 0.5:
            recommendations.append("Cache underutilized, can increase TTL")
        
        # Check TTL
        if avg_ttl_seconds < 300:
            recommendations.append("Consider increasing TTL for stable data")
        elif avg_ttl_seconds > 3600:
            recommendations.append("Long TTL may serve stale data")
        
        # Calculate optimization potential
        improvement_potential = (0.95 - hit_rate) * 100 if hit_rate < 0.95 else 0
        
        return {
            'hit_rate': round(hit_rate, 3),
            'memory_usage_percent': round(memory_usage * 100, 1),
            'avg_ttl_seconds': avg_ttl_seconds,
            'issues': issues,
            'recommendations': recommendations,
            'improvement_potential': round(improvement_potential, 1)
        }
    
    def recommend_cache_strategy(
        self,
        request_patterns: Dict[str, int]
    ) -> Dict[str, Any]:
        """Recommend caching strategy based on patterns"""
        
        total_requests = sum(request_patterns.values())
        
        # Identify hot keys (top 20%)
        sorted_patterns = sorted(request_patterns.items(), key=lambda x: x[1], reverse=True)
        hot_key_threshold = int(len(sorted_patterns) * 0.2)
        hot_keys = sorted_patterns[:hot_key_threshold]
        
        hot_key_requests = sum(count for _, count in hot_keys)
        hot_key_coverage = hot_key_requests / total_requests if total_requests > 0 else 0
        
        # Determine strategy
        if hot_key_coverage > 0.8:
            strategy = "Aggressive caching of hot keys"
            ttl_recommendation = 3600  # 1 hour
        elif hot_key_coverage > 0.5:
            strategy = "Balanced caching"
            ttl_recommendation = 1800  # 30 minutes
        else:
            strategy = "Conservative caching"
            ttl_recommendation = 600  # 10 minutes
        
        return {
            'strategy': strategy,
            'recommended_ttl_seconds': ttl_recommendation,
            'hot_key_coverage': round(hot_key_coverage, 2),
            'top_hot_keys': [key for key, _ in hot_keys[:5]],
            'cache_size_recommendation_mb': len(hot_keys) * 0.1  # Rough estimate
        }


class ResourceOptimizer:
    """Optimize resource allocation"""
    
    def analyze_resource_usage(
        self,
        metrics_history: List[PerformanceMetrics]
    ) -> Dict[str, Any]:
        """Analyze resource usage patterns"""
        
        if not metrics_history:
            return {'error': 'No metrics available'}
        
        # Calculate statistics
        cpu_usage = [m.cpu_percent for m in metrics_history]
        memory_usage = [m.memory_percent for m in metrics_history]
        latency = [m.avg_latency_ms for m in metrics_history]
        
        avg_cpu = sum(cpu_usage) / len(cpu_usage)
        max_cpu = max(cpu_usage)
        avg_memory = sum(memory_usage) / len(memory_usage)
        max_memory = max(memory_usage)
        avg_latency = sum(latency) / len(latency)
        
        # Identify bottlenecks
        bottlenecks = []
        
        if avg_cpu > 70:
            bottlenecks.append(Bottleneck(
                bottleneck_type=BottleneckType.CPU,
                severity="HIGH" if avg_cpu > 85 else "MEDIUM",
                description=f"High CPU usage: {avg_cpu:.1f}%",
                impact_score=avg_cpu / 100
            ))
        
        if avg_memory > 80:
            bottlenecks.append(Bottleneck(
                bottleneck_type=BottleneckType.MEMORY,
                severity="HIGH" if avg_memory > 90 else "MEDIUM",
                description=f"High memory usage: {avg_memory:.1f}%",
                impact_score=avg_memory / 100
            ))
        
        if avg_latency > 500:
            bottlenecks.append(Bottleneck(
                bottleneck_type=BottleneckType.DATABASE,
                severity="HIGH" if avg_latency > 1000 else "MEDIUM",
                description=f"High latency: {avg_latency:.0f}ms",
                impact_score=min(avg_latency / 1000, 1.0)
            ))
        
        return {
            'summary': {
                'avg_cpu_percent': round(avg_cpu, 1),
                'max_cpu_percent': round(max_cpu, 1),
                'avg_memory_percent': round(avg_memory, 1),
                'max_memory_percent': round(max_memory, 1),
                'avg_latency_ms': round(avg_latency, 1)
            },
            'bottlenecks': [
                {
                    'type': b.bottleneck_type.value,
                    'severity': b.severity,
                    'description': b.description,
                    'impact_score': round(b.impact_score, 2)
                }
                for b in bottlenecks
            ]
        }
    
    def recommend_scaling(
        self,
        current_capacity: Dict[str, Any],
        projected_growth: float = 1.5
    ) -> List[Optimization]:
        """Recommend scaling strategies"""
        
        optimizations = []
        
        current_cpu = current_capacity.get('cpu_cores', 4)
        current_memory_gb = current_capacity.get('memory_gb', 16)
        current_instances = current_capacity.get('instances', 2)
        
        # Calculate projected needs
        projected_cpu = current_cpu * projected_growth
        projected_memory = current_memory_gb * projected_growth
        
        # Vertical scaling option
        if projected_cpu <= 16 and projected_memory <= 64:
            optimizations.append(Optimization(
                strategy=OptimizationStrategy.SCALE_UP,
                priority="MEDIUM",
                description=f"Upgrade to {int(projected_cpu)} CPUs, {int(projected_memory)}GB RAM",
                estimated_improvement=30.0,
                estimated_cost=500.0,  # Per month
                implementation_time_hours=2.0
            ))
        
        # Horizontal scaling option
        additional_instances = int((projected_growth - 1) * current_instances)
        if additional_instances > 0:
            optimizations.append(Optimization(
                strategy=OptimizationStrategy.SCALE_OUT,
                priority="HIGH",
                description=f"Add {additional_instances} instances with load balancing",
                estimated_improvement=50.0,
                estimated_cost=800.0 * additional_instances,
                implementation_time_hours=4.0
            ))
        
        return optimizations


class AdvancedPerformanceOptimizer:
    """Main performance optimization coordinator"""
    
    def __init__(self):
        self.query_optimizer = QueryOptimizer()
        self.cache_optimizer = CacheOptimizer()
        self.resource_optimizer = ResourceOptimizer()
    
    def analyze_system_performance(
        self,
        metrics_history: List[PerformanceMetrics],
        slow_queries: List[Tuple[str, float]],
        cache_metrics: Dict[str, Any],
        current_capacity: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Comprehensive performance analysis"""
        
        # Resource analysis
        resource_analysis = self.resource_optimizer.analyze_resource_usage(metrics_history)
        
        # Query analysis
        query_analysis = []
        for query, exec_time in slow_queries[:10]:  # Top 10 slow queries
            analysis = self.query_optimizer.analyze_query(query, exec_time)
            if analysis['needs_optimization']:
                query_analysis.append(analysis)
        
        # Cache analysis
        cache_analysis = self.cache_optimizer.analyze_cache_performance(
            hit_rate=cache_metrics.get('hit_rate', 0.5),
            avg_ttl_seconds=cache_metrics.get('avg_ttl_seconds', 600),
            cache_size_mb=cache_metrics.get('size_mb', 100),
            memory_limit_mb=cache_metrics.get('limit_mb', 512)
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            resource_analysis,
            query_analysis,
            cache_analysis,
            current_capacity
        )
        
        return {
            'resource_analysis': resource_analysis,
            'query_analysis': query_analysis,
            'cache_analysis': cache_analysis,
            'recommendations': recommendations,
            'analyzed_at': datetime.now().isoformat()
        }
    
    def _generate_recommendations(
        self,
        resource_analysis: Dict[str, Any],
        query_analysis: List[Dict[str, Any]],
        cache_analysis: Dict[str, Any],
        current_capacity: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate prioritized recommendations"""
        
        recommendations = []
        
        # Query optimizations
        if query_analysis:
            total_optimization_potential = sum(q['optimization_potential'] for q in query_analysis)
            avg_potential = total_optimization_potential / len(query_analysis)
            
            recommendations.append({
                'category': 'Database',
                'priority': 'HIGH' if avg_potential > 60 else 'MEDIUM',
                'title': f'Optimize {len(query_analysis)} slow queries',
                'description': f'Average optimization potential: {avg_potential:.0f}%',
                'estimated_improvement': f'{avg_potential:.0f}%',
                'actions': [q['recommendations'][0] for q in query_analysis if q['recommendations']][:3]
            })
        
        # Cache optimizations
        if cache_analysis['improvement_potential'] > 10:
            recommendations.append({
                'category': 'Caching',
                'priority': 'MEDIUM',
                'title': 'Improve cache hit rate',
                'description': f'Current: {cache_analysis["hit_rate"]:.1%}, Target: 95%',
                'estimated_improvement': f'{cache_analysis["improvement_potential"]:.0f}%',
                'actions': cache_analysis['recommendations']
            })
        
        # Resource optimizations
        if resource_analysis.get('bottlenecks'):
            high_severity = [b for b in resource_analysis['bottlenecks'] if b['severity'] == 'HIGH']
            if high_severity:
                recommendations.append({
                    'category': 'Resources',
                    'priority': 'HIGH',
                    'title': 'Address resource bottlenecks',
                    'description': f'{len(high_severity)} high-severity bottlenecks detected',
                    'estimated_improvement': '40%',
                    'actions': [b['description'] for b in high_severity]
                })
        
        # Sort by priority
        priority_order = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}
        recommendations.sort(key=lambda r: priority_order.get(r['priority'], 3))
        
        return recommendations


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("=== Advanced Performance Optimizer Demo ===\n")
    
    # Create optimizer
    optimizer = AdvancedPerformanceOptimizer()
    
    # Simulate metrics history
    print("--- Preparing Performance Data ---\n")
    
    metrics_history = []
    base_time = datetime.now() - timedelta(hours=1)
    
    for i in range(60):  # Last hour, minute by minute
        metrics = PerformanceMetrics(
            timestamp=base_time + timedelta(minutes=i),
            cpu_percent=70 + (i % 20),
            memory_percent=75 + (i % 15),
            disk_io_mbps=50 + (i % 10),
            network_mbps=100 + (i % 20),
            request_rate=1000 + (i * 10),
            avg_latency_ms=250 + (i % 50),
            p95_latency_ms=500 + (i % 100),
            p99_latency_ms=800 + (i % 150)
        )
        metrics_history.append(metrics)
    
    # Simulate slow queries
    slow_queries = [
        ("SELECT * FROM games WHERE season = '2023-24'", 850),
        ("SELECT * FROM players WHERE team_id = 5", 650),
        ("SELECT COUNT(*) FROM stats", 1200)
    ]
    
    # Cache metrics
    cache_metrics = {
        'hit_rate': 0.65,
        'avg_ttl_seconds': 600,
        'size_mb': 200,
        'limit_mb': 512
    }
    
    # Current capacity
    current_capacity = {
        'cpu_cores': 4,
        'memory_gb': 16,
        'instances': 2
    }
    
    print("✓ Prepared 60 minutes of metrics")
    print(f"✓ Identified {len(slow_queries)} slow queries")
    
    # Analyze performance
    print("\n--- Analyzing Performance ---\n")
    analysis = optimizer.analyze_system_performance(
        metrics_history,
        slow_queries,
        cache_metrics,
        current_capacity
    )
    
    # Display results
    print("=== Resource Analysis ===")
    summary = analysis['resource_analysis']['summary']
    print(f"CPU: {summary['avg_cpu_percent']}% avg, {summary['max_cpu_percent']}% max")
    print(f"Memory: {summary['avg_memory_percent']}% avg, {summary['max_memory_percent']}% max")
    print(f"Latency: {summary['avg_latency_ms']}ms avg")
    
    if analysis['resource_analysis']['bottlenecks']:
        print(f"\n⚠️ Bottlenecks Detected:")
        for bottleneck in analysis['resource_analysis']['bottlenecks']:
            print(f"  • {bottleneck['description']} ({bottleneck['severity']})")
    
    print(f"\n=== Cache Analysis ===")
    cache = analysis['cache_analysis']
    print(f"Hit Rate: {cache['hit_rate']:.1%}")
    print(f"Memory Usage: {cache['memory_usage_percent']}%")
    print(f"Improvement Potential: {cache['improvement_potential']}%")
    
    print(f"\n=== Query Analysis ===")
    print(f"Slow queries analyzed: {len(analysis['query_analysis'])}")
    for i, query in enumerate(analysis['query_analysis'][:2], 1):
        print(f"\nQuery {i}:")
        print(f"  Execution time: {query['execution_time_ms']}ms")
        print(f"  Optimization potential: {query['optimization_potential']}%")
        print(f"  Top recommendation: {query['recommendations'][0] if query['recommendations'] else 'None'}")
    
    print(f"\n=== Recommendations ===")
    for i, rec in enumerate(analysis['recommendations'], 1):
        print(f"\n{i}. [{rec['priority']}] {rec['title']}")
        print(f"   Category: {rec['category']}")
        print(f"   Expected Improvement: {rec['estimated_improvement']}")
        if rec['actions']:
            print(f"   Actions:")
            for action in rec['actions'][:2]:
                print(f"     • {action}")
    
    print("\n=== Demo Complete ===")

