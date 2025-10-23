#!/usr/bin/env python3
"""
Resource Monitor for NBA MCP Synthesis System

Monitors and prevents resource limit violations including:
- API quota tracking (Gemini, Claude)
- Disk space monitoring
- Memory usage tracking
- Alert system for threshold breaches
- Automatic throttling when approaching limits

Author: NBA MCP Synthesis System
Version: 3.0
"""

import os
import time
import psutil
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Tuple
import json

logger = logging.getLogger(__name__)


class ResourceMonitor:
    """Monitor and prevent resource limit violations."""

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize Resource Monitor.

        Args:
            config_path: Optional path to configuration file
        """
        self.config = self._load_config(config_path)

        # API Quotas (tokens per minute)
        self.api_quotas = {
            'gemini': {
                'limit': self.config.get('gemini_quota', 1000000),  # 1M tokens/min
                'used': 0,
                'reset_interval': 60,  # seconds
                'last_reset': datetime.now(),
                'warning_threshold': 0.80,
                'critical_threshold': 0.95
            },
            'claude': {
                'limit': self.config.get('claude_quota', 20000),  # 20K tokens/min
                'used': 0,
                'reset_interval': 60,
                'last_reset': datetime.now(),
                'warning_threshold': 0.80,
                'critical_threshold': 0.95
            }
        }

        # Disk space limits (GB)
        self.disk_limits = {
            'total_gb': self.config.get('disk_limit_gb', 50),
            'cache_gb': self.config.get('cache_limit_gb', 30),
            'results_gb': self.config.get('results_limit_gb', 15),
            'warning_threshold': 0.80,
            'critical_threshold': 0.95
        }

        # Memory limits (GB)
        self.memory_limits = {
            'total_gb': self.config.get('memory_limit_gb', 16),
            'warning_threshold': 0.80,
            'critical_threshold': 0.90
        }

        # Monitoring state
        self.alerts = []
        self.throttled = False
        self.throttle_until = None

        # Paths to monitor
        self.cache_dir = Path(self.config.get('cache_dir', 'cache'))
        self.results_dir = Path(self.config.get('results_dir', 'analysis_results'))

        logger.info("Resource Monitor initialized")
        logger.info(f"API Quotas: Gemini={self.api_quotas['gemini']['limit']}, Claude={self.api_quotas['claude']['limit']}")
        logger.info(f"Disk Limits: Total={self.disk_limits['total_gb']}GB")
        logger.info(f"Memory Limits: Total={self.memory_limits['total_gb']}GB")

    def _load_config(self, config_path: Optional[Path]) -> Dict:
        """Load configuration from file or use defaults."""
        if config_path and config_path.exists():
            try:
                with open(config_path) as f:
                    return json.load(f).get('resource_monitoring', {})
            except Exception as e:
                logger.warning(f"Failed to load config from {config_path}: {e}")
        return {}

    def check_api_quota(self, model: str, tokens: int) -> Tuple[bool, Optional[str]]:
        """
        Check if API call would exceed quota.

        Args:
            model: Model name ('gemini' or 'claude')
            tokens: Number of tokens for the request

        Returns:
            Tuple of (allowed: bool, reason: Optional[str])
        """
        if model not in self.api_quotas:
            logger.warning(f"Unknown model: {model}")
            return True, None

        # Reset quota if interval has passed
        self._reset_quota_if_needed(model)

        quota = self.api_quotas[model]
        current_usage = quota['used']
        limit = quota['limit']
        projected_usage = current_usage + tokens
        usage_percent = projected_usage / limit

        # Critical threshold - block request
        if usage_percent >= quota['critical_threshold']:
            reason = (
                f"❌ API quota critical for {model}: "
                f"{projected_usage}/{limit} tokens ({usage_percent:.1%})"
            )
            logger.error(reason)
            self._add_alert('critical', reason)
            return False, reason

        # Warning threshold - allow but warn
        if usage_percent >= quota['warning_threshold']:
            reason = (
                f"⚠️  API quota warning for {model}: "
                f"{projected_usage}/{limit} tokens ({usage_percent:.1%})"
            )
            logger.warning(reason)
            self._add_alert('warning', reason)

        return True, None

    def track_api_usage(self, model: str, tokens: int):
        """
        Track API token usage.

        Args:
            model: Model name
            tokens: Number of tokens used
        """
        if model in self.api_quotas:
            self.api_quotas[model]['used'] += tokens
            logger.debug(f"API usage tracked: {model} +{tokens} tokens")

    def _reset_quota_if_needed(self, model: str):
        """Reset quota if reset interval has passed."""
        quota = self.api_quotas[model]
        now = datetime.now()
        elapsed = (now - quota['last_reset']).total_seconds()

        if elapsed >= quota['reset_interval']:
            old_used = quota['used']
            quota['used'] = 0
            quota['last_reset'] = now
            logger.debug(f"API quota reset for {model}: {old_used} → 0 tokens")

    def monitor_disk_space(self) -> Dict:
        """
        Check available disk space.

        Returns:
            Dict with disk space metrics
        """
        try:
            # Get overall disk usage
            disk = psutil.disk_usage('/')
            total_gb = disk.total / (1024**3)
            used_gb = disk.used / (1024**3)
            free_gb = disk.free / (1024**3)
            usage_percent = disk.percent / 100.0

            # Get directory sizes
            cache_size_gb = self._get_directory_size(self.cache_dir)
            results_size_gb = self._get_directory_size(self.results_dir)

            metrics = {
                'total_gb': round(total_gb, 2),
                'used_gb': round(used_gb, 2),
                'free_gb': round(free_gb, 2),
                'usage_percent': round(usage_percent, 3),
                'cache_gb': round(cache_size_gb, 2),
                'results_gb': round(results_size_gb, 2)
            }

            # Check thresholds
            if usage_percent >= self.disk_limits['critical_threshold']:
                reason = (
                    f"❌ Disk space critical: {free_gb:.1f}GB free "
                    f"({usage_percent:.1%} used)"
                )
                logger.error(reason)
                self._add_alert('critical', reason)
            elif usage_percent >= self.disk_limits['warning_threshold']:
                reason = (
                    f"⚠️  Disk space warning: {free_gb:.1f}GB free "
                    f"({usage_percent:.1%} used)"
                )
                logger.warning(reason)
                self._add_alert('warning', reason)

            # Check cache size
            if cache_size_gb >= self.disk_limits['cache_gb'] * 0.9:
                reason = (
                    f"⚠️  Cache directory large: {cache_size_gb:.1f}GB "
                    f"(limit: {self.disk_limits['cache_gb']}GB)"
                )
                logger.warning(reason)
                self._add_alert('warning', reason)

            return metrics

        except Exception as e:
            logger.error(f"Failed to monitor disk space: {e}")
            return {}

    def _get_directory_size(self, path: Path) -> float:
        """Get directory size in GB."""
        if not path.exists():
            return 0.0

        total_size = 0
        try:
            for item in path.rglob('*'):
                if item.is_file():
                    total_size += item.stat().st_size
        except Exception as e:
            logger.warning(f"Failed to get size of {path}: {e}")

        return total_size / (1024**3)  # Convert to GB

    def monitor_memory_usage(self) -> Dict:
        """
        Check memory usage.

        Returns:
            Dict with memory metrics
        """
        try:
            memory = psutil.virtual_memory()
            total_gb = memory.total / (1024**3)
            used_gb = memory.used / (1024**3)
            available_gb = memory.available / (1024**3)
            usage_percent = memory.percent / 100.0

            metrics = {
                'total_gb': round(total_gb, 2),
                'used_gb': round(used_gb, 2),
                'available_gb': round(available_gb, 2),
                'usage_percent': round(usage_percent, 3)
            }

            # Check thresholds
            if usage_percent >= self.memory_limits['critical_threshold']:
                reason = (
                    f"❌ Memory usage critical: {available_gb:.1f}GB available "
                    f"({usage_percent:.1%} used)"
                )
                logger.error(reason)
                self._add_alert('critical', reason)
            elif usage_percent >= self.memory_limits['warning_threshold']:
                reason = (
                    f"⚠️  Memory usage warning: {available_gb:.1f}GB available "
                    f"({usage_percent:.1%} used)"
                )
                logger.warning(reason)
                self._add_alert('warning', reason)

            return metrics

        except Exception as e:
            logger.error(f"Failed to monitor memory: {e}")
            return {}

    def get_system_metrics(self) -> Dict:
        """
        Get all system metrics.

        Returns:
            Dict with all metrics
        """
        return {
            'timestamp': datetime.now().isoformat(),
            'api_quotas': {
                model: {
                    'used': quota['used'],
                    'limit': quota['limit'],
                    'usage_percent': round(quota['used'] / quota['limit'], 3)
                }
                for model, quota in self.api_quotas.items()
            },
            'disk': self.monitor_disk_space(),
            'memory': self.monitor_memory_usage(),
            'alerts': self.get_recent_alerts(10),
            'throttled': self.throttled
        }

    def _add_alert(self, level: str, message: str):
        """Add alert to alert list."""
        alert = {
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'message': message
        }
        self.alerts.append(alert)

        # Keep only last 100 alerts
        if len(self.alerts) > 100:
            self.alerts = self.alerts[-100:]

    def get_recent_alerts(self, count: int = 10) -> list:
        """Get recent alerts."""
        return self.alerts[-count:] if self.alerts else []

    def should_throttle(self) -> Tuple[bool, Optional[str]]:
        """
        Check if workflow should be throttled.

        Returns:
            Tuple of (should_throttle: bool, reason: Optional[str])
        """
        # Check if already throttled
        if self.throttled and self.throttle_until:
            if datetime.now() < self.throttle_until:
                remaining = (self.throttle_until - datetime.now()).total_seconds()
                return True, f"Throttled for {remaining:.0f}s more"
            else:
                # Throttle period ended
                self.throttled = False
                self.throttle_until = None
                logger.info("Throttling period ended")

        # Check API quotas
        for model, quota in self.api_quotas.items():
            usage_percent = quota['used'] / quota['limit']
            if usage_percent >= quota['critical_threshold']:
                # Throttle for remaining interval
                remaining = quota['reset_interval'] - (
                    datetime.now() - quota['last_reset']
                ).total_seconds()
                if remaining > 0:
                    self.throttled = True
                    self.throttle_until = datetime.now() + timedelta(seconds=remaining)
                    reason = f"API quota critical for {model}, throttling for {remaining:.0f}s"
                    logger.warning(reason)
                    return True, reason

        # Check disk space
        disk_metrics = self.monitor_disk_space()
        if disk_metrics.get('usage_percent', 0) >= self.disk_limits['critical_threshold']:
            reason = f"Disk space critical: {disk_metrics.get('free_gb', 0):.1f}GB free"
            logger.error(reason)
            return True, reason

        # Check memory
        memory_metrics = self.monitor_memory_usage()
        if memory_metrics.get('usage_percent', 0) >= self.memory_limits['critical_threshold']:
            reason = f"Memory critical: {memory_metrics.get('available_gb', 0):.1f}GB available"
            logger.error(reason)
            return True, reason

        return False, None

    def wait_if_throttled(self, max_wait_seconds: int = 300):
        """
        Wait if throttled, with maximum wait time.

        Args:
            max_wait_seconds: Maximum time to wait (default 5 minutes)
        """
        should_throttle, reason = self.should_throttle()
        if should_throttle:
            if self.throttle_until:
                wait_seconds = min(
                    (self.throttle_until - datetime.now()).total_seconds(),
                    max_wait_seconds
                )
                if wait_seconds > 0:
                    logger.warning(f"Throttling: {reason}, waiting {wait_seconds:.0f}s")
                    time.sleep(wait_seconds)
                    logger.info("Throttling wait complete")

    def save_metrics(self, output_path: Path):
        """
        Save current metrics to file.

        Args:
            output_path: Path to save metrics JSON
        """
        try:
            metrics = self.get_system_metrics()
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump(metrics, f, indent=2)
            logger.info(f"Metrics saved to {output_path}")
        except Exception as e:
            logger.error(f"Failed to save metrics: {e}")

    def print_status(self):
        """Print current resource status."""
        metrics = self.get_system_metrics()

        print("\n" + "="*60)
        print("📊 Resource Monitor Status")
        print("="*60)

        # API Quotas
        print("\n🔌 API Quotas:")
        for model, quota_data in metrics['api_quotas'].items():
            usage_pct = quota_data['usage_percent'] * 100
            status = "✅" if usage_pct < 80 else "⚠️" if usage_pct < 95 else "❌"
            print(f"  {status} {model.capitalize()}: {quota_data['used']:,}/{quota_data['limit']:,} tokens ({usage_pct:.1f}%)")

        # Disk Space
        print("\n💾 Disk Space:")
        disk = metrics['disk']
        if disk:
            usage_pct = disk['usage_percent'] * 100
            status = "✅" if usage_pct < 80 else "⚠️" if usage_pct < 95 else "❌"
            print(f"  {status} Total: {disk['free_gb']:.1f}GB free / {disk['total_gb']:.1f}GB total ({usage_pct:.1f}% used)")
            print(f"     Cache: {disk['cache_gb']:.1f}GB")
            print(f"     Results: {disk['results_gb']:.1f}GB")

        # Memory
        print("\n🧠 Memory:")
        memory = metrics['memory']
        if memory:
            usage_pct = memory['usage_percent'] * 100
            status = "✅" if usage_pct < 80 else "⚠️" if usage_pct < 90 else "❌"
            print(f"  {status} {memory['available_gb']:.1f}GB available / {memory['total_gb']:.1f}GB total ({usage_pct:.1f}% used)")

        # Alerts
        if metrics['alerts']:
            print("\n⚠️  Recent Alerts:")
            for alert in metrics['alerts'][-5:]:
                print(f"  {alert['level'].upper()}: {alert['message']}")

        # Throttling
        if metrics['throttled']:
            print("\n🚦 Status: THROTTLED")
        else:
            print("\n✅ Status: OPERATIONAL")

        print("="*60 + "\n")


def main():
    """Test resource monitoring."""
    import argparse

    parser = argparse.ArgumentParser(description='Resource Monitor')
    parser.add_argument('--config', type=Path, help='Configuration file')
    parser.add_argument('--watch', action='store_true', help='Continuous monitoring')
    parser.add_argument('--interval', type=int, default=5, help='Watch interval (seconds)')
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    monitor = ResourceMonitor(config_path=args.config)

    if args.watch:
        print("Starting continuous monitoring (Ctrl+C to stop)...")
        try:
            while True:
                monitor.print_status()
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\nMonitoring stopped")
    else:
        monitor.print_status()


if __name__ == '__main__':
    main()







