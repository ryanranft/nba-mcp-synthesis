#!/usr/bin/env python3
"""
Circuit Breaker implementation for API calls.
Skips problematic APIs and continues with working ones.
"""

import asyncio
import logging
import time
from typing import Dict, List, Any, Optional
from enum import Enum
from dataclasses import dataclass

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Circuit is open, failing fast
    HALF_OPEN = "half_open"  # Testing if service is back


@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 3
    recovery_timeout: int = 60  # seconds
    success_threshold: int = 2


class CircuitBreaker:
    """Circuit breaker implementation for API calls."""

    def __init__(self, name: str, config: CircuitBreakerConfig = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.last_success_time = None

    def can_execute(self) -> bool:
        """Check if the circuit breaker allows execution."""
        if self.state == CircuitState.CLOSED:
            return True
        elif self.state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if (
                self.last_failure_time
                and time.time() - self.last_failure_time >= self.config.recovery_timeout
            ):
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
                logger.info(
                    f"🔄 Circuit breaker {self.name} transitioning to HALF_OPEN"
                )
                return True
            return False
        elif self.state == CircuitState.HALF_OPEN:
            return True
        return False

    def on_success(self):
        """Handle successful execution."""
        self.failure_count = 0
        self.last_success_time = time.time()

        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self.state = CircuitState.CLOSED
                logger.info(
                    f"✅ Circuit breaker {self.name} closed - service recovered"
                )
        elif self.state == CircuitState.CLOSED:
            # Reset success count on successful calls
            self.success_count = 0

    def on_failure(self):
        """Handle failed execution."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        self.success_count = 0

        if self.failure_count >= self.config.failure_threshold:
            self.state = CircuitState.OPEN
            logger.warning(f"🚨 Circuit breaker {self.name} opened - too many failures")

    def get_state_info(self) -> Dict[str, Any]:
        """Get current circuit breaker state information."""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": self.last_failure_time,
            "last_success_time": self.last_success_time,
            "can_execute": self.can_execute(),
        }


class ResilientAPIManager:
    """Manages API calls with circuit breaker pattern."""

    def __init__(self):
        self.circuit_breakers = {
            "google": CircuitBreaker("Google Gemini"),
            "deepseek": CircuitBreaker("DeepSeek"),
            "claude": CircuitBreaker("Claude"),
            "gpt4": CircuitBreaker("GPT-4"),
        }

        # Track which APIs are known to be broken
        self.broken_apis = set()

    async def execute_with_circuit_breaker(
        self, api_name: str, coro_func, *args, **kwargs
    ) -> Dict[str, Any]:
        """Execute API call with circuit breaker protection."""
        circuit = self.circuit_breakers.get(api_name)

        if not circuit:
            logger.error(f"❌ No circuit breaker found for {api_name}")
            return {"success": False, "error": f"No circuit breaker for {api_name}"}

        # Check if API is known to be broken
        if api_name in self.broken_apis:
            logger.warning(f"⚠️ Skipping {api_name} - known to be broken")
            return {
                "success": False,
                "error": f"{api_name} is known to be broken",
                "skipped": True,
            }

        # Check circuit breaker state
        if not circuit.can_execute():
            logger.warning(f"⚠️ Circuit breaker {api_name} is OPEN - skipping")
            return {
                "success": False,
                "error": f"{api_name} circuit breaker is open",
                "skipped": True,
            }

        try:
            logger.info(f"🔄 Executing {api_name} API call...")
            result = await coro_func(*args, **kwargs)

            if result.get("success", False):
                circuit.on_success()
                logger.info(f"✅ {api_name} API call succeeded")
                return result
            else:
                circuit.on_failure()
                logger.warning(
                    f"⚠️ {api_name} API call failed: {result.get('error', 'Unknown error')}"
                )
                return result

        except Exception as e:
            circuit.on_failure()
            logger.error(f"❌ {api_name} API call exception: {str(e)}")
            return {"success": False, "error": str(e)}

    def mark_api_broken(self, api_name: str):
        """Mark an API as permanently broken."""
        self.broken_apis.add(api_name)
        logger.warning(f"🚫 Marked {api_name} as permanently broken")

    def get_circuit_breaker_status(self) -> Dict[str, Any]:
        """Get status of all circuit breakers."""
        return {
            api_name: circuit.get_state_info()
            for api_name, circuit in self.circuit_breakers.items()
        }

    def get_working_apis(self) -> List[str]:
        """Get list of APIs that are currently working."""
        working = []
        for api_name, circuit in self.circuit_breakers.items():
            if api_name not in self.broken_apis and circuit.can_execute():
                working.append(api_name)
        return working


# Global circuit breaker manager
circuit_manager = ResilientAPIManager()

# Mark known broken APIs based on debug results
circuit_manager.mark_api_broken("claude")  # Method signature issues
circuit_manager.mark_api_broken("gpt4")  # Missing methods

logger.info("🛡️ Circuit breaker system initialized")
logger.info(f"✅ Working APIs: {circuit_manager.get_working_apis()}")
logger.info(f"🚫 Broken APIs: {list(circuit_manager.broken_apis)}")
