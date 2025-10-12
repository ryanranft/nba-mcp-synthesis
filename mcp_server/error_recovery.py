"""
Error Recovery System

Intelligent error handling and recovery:
- Automatic error detection
- Recovery strategies
- Fallback mechanisms
- Error aggregation
- Root cause analysis
- Self-healing capabilities

Features:
- Circuit breaker pattern
- Exponential backoff
- Dead letter queue
- Error classification
- Recovery workflows
- Incident management

Use Cases:
- API failures
- Database connectivity issues
- External service failures
- ML model errors
- Data quality issues
"""

import time
import logging
import traceback
from typing import Any, Callable, Optional, Dict, List, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import threading
from collections import defaultdict

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RecoveryStrategy(Enum):
    """Recovery strategy types"""
    RETRY = "retry"
    FALLBACK = "fallback"
    CIRCUIT_BREAK = "circuit_break"
    DEGRADE = "degrade"
    ALERT = "alert"
    IGNORE = "ignore"


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Failing, block requests
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class ErrorRecord:
    """Record of an error occurrence"""
    error_id: str
    error_type: str
    error_message: str
    severity: ErrorSeverity
    occurred_at: datetime
    stack_trace: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    recovery_attempted: bool = False
    recovery_successful: bool = False
    recovery_strategy: Optional[RecoveryStrategy] = None


@dataclass
class CircuitBreaker:
    """Circuit breaker for fault tolerance"""
    name: str
    failure_threshold: int = 5
    timeout_seconds: int = 60
    half_open_attempts: int = 3

    # State
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    last_failure_time: Optional[datetime] = None
    success_count: int = 0

    def record_success(self) -> None:
        """Record successful operation"""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.half_open_attempts:
                logger.info(f"Circuit breaker '{self.name}' closed (recovered)")
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.success_count = 0
        elif self.state == CircuitState.CLOSED:
            self.failure_count = 0

    def record_failure(self) -> None:
        """Record failed operation"""
        self.last_failure_time = datetime.now()

        if self.state == CircuitState.HALF_OPEN:
            # Failed during recovery test
            logger.warning(f"Circuit breaker '{self.name}' reopened (recovery failed)")
            self.state = CircuitState.OPEN
            self.failure_count = 0
            self.success_count = 0
        elif self.state == CircuitState.CLOSED:
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold:
                logger.error(f"Circuit breaker '{self.name}' opened (threshold reached)")
                self.state = CircuitState.OPEN

    def can_attempt(self) -> bool:
        """Check if operation can be attempted"""
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            # Check if timeout has passed
            if self.last_failure_time:
                elapsed = (datetime.now() - self.last_failure_time).total_seconds()
                if elapsed >= self.timeout_seconds:
                    logger.info(f"Circuit breaker '{self.name}' entering half-open state")
                    self.state = CircuitState.HALF_OPEN
                    self.success_count = 0
                    return True
            return False

        # HALF_OPEN state
        return True


class ErrorRecoveryManager:
    """Manage error recovery strategies"""

    def __init__(self):
        self.error_history: List[ErrorRecord] = []
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.recovery_handlers: Dict[str, Callable] = {}
        self.fallback_handlers: Dict[str, Callable] = {}
        self.error_counts: Dict[str, int] = defaultdict(int)
        self._lock = threading.RLock()

    def register_circuit_breaker(
        self,
        name: str,
        failure_threshold: int = 5,
        timeout_seconds: int = 60
    ) -> CircuitBreaker:
        """Register a circuit breaker"""
        with self._lock:
            circuit = CircuitBreaker(
                name=name,
                failure_threshold=failure_threshold,
                timeout_seconds=timeout_seconds
            )
            self.circuit_breakers[name] = circuit
            logger.info(f"Registered circuit breaker: {name}")
            return circuit

    def register_recovery_handler(self, error_type: str, handler: Callable) -> None:
        """Register error recovery handler"""
        self.recovery_handlers[error_type] = handler
        logger.info(f"Registered recovery handler for: {error_type}")

    def register_fallback_handler(self, operation: str, handler: Callable) -> None:
        """Register fallback handler"""
        self.fallback_handlers[operation] = handler
        logger.info(f"Registered fallback handler for: {operation}")

    def record_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM
    ) -> ErrorRecord:
        """Record an error occurrence"""
        error_record = ErrorRecord(
            error_id=f"{type(error).__name__}_{int(time.time() * 1000)}",
            error_type=type(error).__name__,
            error_message=str(error),
            severity=severity,
            occurred_at=datetime.now(),
            stack_trace=traceback.format_exc(),
            context=context or {}
        )

        with self._lock:
            self.error_history.append(error_record)
            self.error_counts[error_record.error_type] += 1

        logger.error(f"Error recorded: {error_record.error_type} - {error_record.error_message}")
        return error_record

    def attempt_recovery(self, error_record: ErrorRecord) -> bool:
        """Attempt to recover from error"""
        error_type = error_record.error_type

        if error_type in self.recovery_handlers:
            logger.info(f"Attempting recovery for {error_type}")
            error_record.recovery_attempted = True

            try:
                handler = self.recovery_handlers[error_type]
                handler(error_record)
                error_record.recovery_successful = True
                error_record.recovery_strategy = RecoveryStrategy.RETRY
                logger.info(f"Recovery successful for {error_type}")
                return True
            except Exception as e:
                logger.error(f"Recovery failed for {error_type}: {e}")
                error_record.recovery_successful = False
                return False

        return False

    def get_circuit_breaker(self, name: str) -> Optional[CircuitBreaker]:
        """Get circuit breaker by name"""
        return self.circuit_breakers.get(name)

    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics"""
        with self._lock:
            total_errors = len(self.error_history)

            # Group by type
            by_type = {}
            for error_type, count in self.error_counts.items():
                by_type[error_type] = count

            # Group by severity
            by_severity = defaultdict(int)
            for error in self.error_history:
                by_severity[error.severity.value] += 1

            # Recent errors (last hour)
            one_hour_ago = datetime.now() - timedelta(hours=1)
            recent_errors = sum(
                1 for error in self.error_history
                if error.occurred_at > one_hour_ago
            )

            # Recovery stats
            recovery_attempted = sum(
                1 for error in self.error_history
                if error.recovery_attempted
            )
            recovery_successful = sum(
                1 for error in self.error_history
                if error.recovery_successful
            )

            return {
                'total_errors': total_errors,
                'by_type': dict(by_type),
                'by_severity': dict(by_severity),
                'recent_errors_1h': recent_errors,
                'recovery_attempted': recovery_attempted,
                'recovery_successful': recovery_successful,
                'recovery_success_rate': (
                    recovery_successful / recovery_attempted * 100
                    if recovery_attempted > 0 else 0
                ),
                'circuit_breakers': {
                    name: cb.state.value
                    for name, cb in self.circuit_breakers.items()
                }
            }

    def clear_old_errors(self, days: int = 7) -> int:
        """Clear errors older than specified days"""
        cutoff = datetime.now() - timedelta(days=days)

        with self._lock:
            old_count = len(self.error_history)
            self.error_history = [
                error for error in self.error_history
                if error.occurred_at > cutoff
            ]
            removed = old_count - len(self.error_history)

        if removed > 0:
            logger.info(f"Cleared {removed} old error records")

        return removed


def with_circuit_breaker(circuit_name: str, manager: ErrorRecoveryManager):
    """Decorator to apply circuit breaker pattern"""
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            circuit = manager.get_circuit_breaker(circuit_name)

            if not circuit:
                # No circuit breaker, execute normally
                return func(*args, **kwargs)

            if not circuit.can_attempt():
                raise Exception(f"Circuit breaker '{circuit_name}' is OPEN")

            try:
                result = func(*args, **kwargs)
                circuit.record_success()
                return result
            except Exception as e:
                circuit.record_failure()
                raise

        return wrapper
    return decorator


def with_retry(
    max_attempts: int = 3,
    backoff_seconds: float = 1.0,
    backoff_multiplier: float = 2.0
):
    """Decorator for automatic retry with exponential backoff"""
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            attempt = 0
            delay = backoff_seconds

            while attempt < max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempt += 1
                    if attempt >= max_attempts:
                        logger.error(f"Max retry attempts ({max_attempts}) reached for {func.__name__}")
                        raise

                    logger.warning(f"Attempt {attempt}/{max_attempts} failed for {func.__name__}: {e}")
                    logger.info(f"Retrying in {delay}s...")
                    time.sleep(delay)
                    delay *= backoff_multiplier

        return wrapper
    return decorator


def with_fallback(fallback_func: Callable):
    """Decorator to provide fallback behavior"""
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.warning(f"{func.__name__} failed, using fallback: {e}")
                return fallback_func(*args, **kwargs)

        return wrapper
    return decorator


# Global error recovery manager
_error_manager = None
_manager_lock = threading.Lock()


def get_error_manager() -> ErrorRecoveryManager:
    """Get global error recovery manager"""
    global _error_manager
    with _manager_lock:
        if _error_manager is None:
            _error_manager = ErrorRecoveryManager()
        return _error_manager


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("=== Error Recovery System Demo ===\n")

    manager = ErrorRecoveryManager()

    # Register circuit breaker
    print("--- Circuit Breaker Demo ---")
    db_circuit = manager.register_circuit_breaker(
        "database",
        failure_threshold=3,
        timeout_seconds=10
    )

    @with_circuit_breaker("database", manager)
    def query_database(query: str):
        """Simulate database query"""
        import random
        if random.random() < 0.7:  # 70% failure rate
            raise Exception("Database connection timeout")
        return f"Results for: {query}"

    # Test circuit breaker
    for i in range(10):
        try:
            result = query_database(f"SELECT * FROM players WHERE id={i}")
            print(f"✓ Query {i}: {result}")
        except Exception as e:
            print(f"✗ Query {i}: {e}")
        time.sleep(0.5)

    print(f"\nCircuit breaker state: {db_circuit.state.value}")

    # Retry decorator demo
    print("\n--- Retry Decorator Demo ---")

    @with_retry(max_attempts=3, backoff_seconds=0.5)
    def unreliable_api_call(player_id: int):
        """Simulate unreliable API"""
        import random
        if random.random() < 0.6:
            raise Exception("API timeout")
        return {"player_id": player_id, "stats": {"ppg": 25.5}}

    try:
        result = unreliable_api_call(23)
        print(f"API call successful: {result}")
    except Exception as e:
        print(f"API call failed: {e}")

    # Fallback decorator demo
    print("\n--- Fallback Decorator Demo ---")

    def fallback_player_stats(player_id: int):
        """Fallback: return cached or default stats"""
        return {"player_id": player_id, "stats": {"ppg": 0.0}, "source": "cache"}

    @with_fallback(fallback_player_stats)
    def get_player_stats(player_id: int):
        """Get player stats from API"""
        raise Exception("API unavailable")

    result = get_player_stats(42)
    print(f"Result (with fallback): {result}")

    # Error statistics
    print("\n--- Error Statistics ---")

    # Simulate some errors
    for i in range(5):
        try:
            if i % 2 == 0:
                raise ValueError(f"Invalid player ID: {i}")
            else:
                raise ConnectionError("Database unavailable")
        except Exception as e:
            manager.record_error(
                e,
                context={"operation": "get_player", "player_id": i},
                severity=ErrorSeverity.HIGH if isinstance(e, ConnectionError) else ErrorSeverity.MEDIUM
            )

    stats = manager.get_error_stats()
    print(f"Total errors: {stats['total_errors']}")
    print(f"By type: {stats['by_type']}")
    print(f"By severity: {stats['by_severity']}")

    print("\n=== Demo Complete ===")

