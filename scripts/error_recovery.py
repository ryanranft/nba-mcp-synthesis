#!/usr/bin/env python3
"""
Error Recovery Manager - Automatic retry with exponential backoff

Implements comprehensive error recovery with retry logic for common failures.
Provides fallback strategies and graceful degradation.

Features:
- Automatic retry with exponential backoff
- Configurable retry policies per error type
- Fallback strategies
- Partial result preservation
- Error categorization and logging

Usage:
    from error_recovery import ErrorRecoveryManager

    recovery = ErrorRecoveryManager()

    # Execute with automatic recovery
    result = await recovery.execute_with_recovery(
        operation=expensive_api_call,
        error_type='api_timeout',
        fallback=lambda: use_cached_result()
    )
"""

import asyncio
import logging
from typing import Callable, Optional, Any, Dict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import json

logger = logging.getLogger(__name__)


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""

    retries: int
    backoff: float  # Initial backoff in seconds
    max_backoff: float = 300.0  # Max 5 minutes
    exponential: bool = True


class ErrorRecoveryManager:
    """
    Automatic retry with exponential backoff.

    Retry Configuration:
    - api_timeout: 3 retries, 2s initial backoff
    - rate_limit: 5 retries, 60s initial backoff
    - json_decode: 2 retries, 1s initial backoff
    - network_error: 3 retries, 5s initial backoff
    - file_io_error: 2 retries, 1s initial backoff
    - validation_error: 1 retry, 2s initial backoff

    Fallback Strategies:
    - Use alternative model if primary fails
    - Use cached results if available
    - Save partial results before failing
    - Graceful degradation (return partial data)
    """

    RETRY_CONFIG = {
        "api_timeout": RetryConfig(retries=3, backoff=2.0),
        "rate_limit": RetryConfig(retries=5, backoff=60.0),
        "json_decode": RetryConfig(retries=2, backoff=1.0),
        "network_error": RetryConfig(retries=3, backoff=5.0),
        "file_io_error": RetryConfig(retries=2, backoff=1.0),
        "validation_error": RetryConfig(retries=1, backoff=2.0),
        "database_error": RetryConfig(retries=3, backoff=2.0),
        "auth_error": RetryConfig(retries=2, backoff=5.0),
    }

    def __init__(self, error_log_path: Optional[Path] = None):
        """Initialize error recovery manager."""
        self.error_log_path = error_log_path or Path(
            "implementation_plans/error_log.json"
        )
        self.error_log_path.parent.mkdir(parents=True, exist_ok=True)

        self.errors = self._load_error_log()

        logger.info("🛡️  Error Recovery Manager initialized")
        logger.info(f"   Total errors logged: {len(self.errors['errors'])}")

    def _load_error_log(self) -> Dict:
        """Load error log from disk."""
        if self.error_log_path.exists():
            return json.loads(self.error_log_path.read_text())
        else:
            return {
                "errors": [],
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
            }

    def _save_error_log(self):
        """Save error log to disk."""
        self.errors["last_updated"] = datetime.now().isoformat()
        self.error_log_path.write_text(json.dumps(self.errors, indent=2))

    def _log_error(
        self,
        error_type: str,
        operation: str,
        attempt: int,
        error: Exception,
        recovered: bool = False,
    ):
        """Log error for analysis."""
        error_record = {
            "timestamp": datetime.now().isoformat(),
            "error_type": error_type,
            "operation": operation,
            "attempt": attempt,
            "error_message": str(error),
            "error_class": type(error).__name__,
            "recovered": recovered,
        }

        self.errors["errors"].append(error_record)
        self._save_error_log()

    async def execute_with_recovery(
        self,
        operation: Callable,
        error_type: str,
        fallback: Optional[Callable] = None,
        operation_name: str = "",
        **operation_kwargs,
    ) -> Any:
        """
        Execute operation with automatic recovery.

        Args:
            operation: Async or sync callable to execute
            error_type: Type of error expected (determines retry config)
            fallback: Optional fallback function if all retries fail
            operation_name: Human-readable name for logging
            **operation_kwargs: Arguments to pass to operation

        Returns:
            Result from operation or fallback

        Raises:
            Exception if all retries fail and no fallback provided
        """
        config = self.RETRY_CONFIG.get(error_type, RetryConfig(retries=2, backoff=2.0))

        operation_desc = operation_name or operation.__name__

        logger.info(f"🔄 Executing with recovery: {operation_desc}")
        logger.info(f"   Error type: {error_type}")
        logger.info(f"   Max retries: {config.retries}")

        for attempt in range(config.retries + 1):  # +1 for initial attempt
            try:
                # Execute operation
                if asyncio.iscoroutinefunction(operation):
                    result = await operation(**operation_kwargs)
                else:
                    result = operation(**operation_kwargs)

                if attempt > 0:
                    logger.info(f"✅ Recovered after {attempt} retries")
                    self._log_error(
                        error_type, operation_desc, attempt, None, recovered=True
                    )

                return result

            except Exception as e:
                self._log_error(error_type, operation_desc, attempt, e, recovered=False)

                if attempt < config.retries:
                    # Calculate backoff
                    if config.exponential:
                        wait_time = min(
                            config.backoff * (2**attempt), config.max_backoff
                        )
                    else:
                        wait_time = config.backoff

                    logger.warning(
                        f"⚠️  Attempt {attempt + 1}/{config.retries + 1} failed: {type(e).__name__}: {str(e)}"
                    )
                    logger.info(f"   Retrying in {wait_time:.1f}s...")

                    await asyncio.sleep(wait_time)
                else:
                    # Final attempt failed
                    logger.error(f"❌ All {config.retries + 1} attempts failed")

                    if fallback:
                        logger.info("🔄 Attempting fallback strategy...")
                        try:
                            if asyncio.iscoroutinefunction(fallback):
                                result = await fallback()
                            else:
                                result = fallback()

                            logger.info("✅ Fallback succeeded")
                            return result

                        except Exception as fallback_error:
                            logger.error(f"❌ Fallback also failed: {fallback_error}")
                            raise
                    else:
                        raise

    def categorize_error(self, error: Exception) -> str:
        """
        Categorize exception into error type.

        Args:
            error: Exception to categorize

        Returns:
            Error type string for retry configuration
        """
        error_name = type(error).__name__.lower()
        error_msg = str(error).lower()

        # Timeout errors
        if "timeout" in error_name or "timeout" in error_msg:
            return "api_timeout"

        # Rate limit errors
        if "rate" in error_msg or "limit" in error_msg or "429" in error_msg:
            return "rate_limit"

        # JSON/parsing errors
        if "json" in error_name or "decode" in error_name:
            return "json_decode"

        # Network errors
        if any(x in error_name for x in ["connection", "network", "socket"]):
            return "network_error"

        # File I/O errors
        if "file" in error_name or "io" in error_name:
            return "file_io_error"

        # Validation errors
        if "validation" in error_name or "invalid" in error_msg:
            return "validation_error"

        # Database errors
        if "database" in error_name or "sql" in error_name:
            return "database_error"

        # Auth errors
        if (
            "auth" in error_name
            or "permission" in error_msg
            or "401" in error_msg
            or "403" in error_msg
        ):
            return "auth_error"

        # Default
        return "network_error"

    async def execute_with_auto_categorization(
        self,
        operation: Callable,
        fallback: Optional[Callable] = None,
        operation_name: str = "",
        **operation_kwargs,
    ) -> Any:
        """
        Execute operation with automatic error categorization.

        Automatically determines error type from exception and applies
        appropriate retry strategy.

        Args:
            operation: Callable to execute
            fallback: Optional fallback function
            operation_name: Human-readable name
            **operation_kwargs: Arguments for operation

        Returns:
            Result from operation or fallback
        """
        operation_desc = operation_name or operation.__name__

        try:
            if asyncio.iscoroutinefunction(operation):
                return await operation(**operation_kwargs)
            else:
                return operation(**operation_kwargs)

        except Exception as e:
            error_type = self.categorize_error(e)
            logger.info(f"🔍 Auto-categorized error as: {error_type}")

            # Retry with categorized error type
            return await self.execute_with_recovery(
                operation=operation,
                error_type=error_type,
                fallback=fallback,
                operation_name=operation_desc,
                **operation_kwargs,
            )

    def save_partial_results(
        self, operation: str, partial_data: Any, output_path: Optional[Path] = None
    ):
        """
        Save partial results before failing.

        Useful for long-running operations that fail partway through.
        Allows resuming from checkpoint.

        Args:
            operation: Operation name
            partial_data: Data to save
            output_path: Where to save (defaults to implementation_plans/)
        """
        if output_path is None:
            output_path = Path(
                f"implementation_plans/partial_results/{operation}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )

        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Save data
        with open(output_path, "w") as f:
            json.dump(
                {
                    "timestamp": datetime.now().isoformat(),
                    "operation": operation,
                    "data": partial_data,
                },
                f,
                indent=2,
            )

        logger.info(f"💾 Saved partial results: {output_path}")

    def generate_error_report(self) -> str:
        """Generate human-readable error report."""
        report = f"""# Error Recovery Report

**Generated:** {datetime.now().isoformat()}
**Total Errors:** {len(self.errors['errors'])}

## Error Summary by Type

"""

        # Count errors by type
        error_counts = {}
        recovered_counts = {}

        for error in self.errors["errors"]:
            error_type = error["error_type"]
            error_counts[error_type] = error_counts.get(error_type, 0) + 1

            if error["recovered"]:
                recovered_counts[error_type] = recovered_counts.get(error_type, 0) + 1

        report += "| Error Type | Total | Recovered | Recovery Rate |\n"
        report += "|------------|-------|-----------|---------------|\n"

        for error_type, count in sorted(error_counts.items()):
            recovered = recovered_counts.get(error_type, 0)
            rate = (recovered / count * 100) if count > 0 else 0
            report += f"| {error_type} | {count} | {recovered} | {rate:.1f}% |\n"

        report += f"\n## Recent Errors\n\n"

        # Show last 10 errors
        recent = self.errors["errors"][-10:]
        for error in reversed(recent):
            status = "✅ Recovered" if error["recovered"] else "❌ Failed"
            report += f"- **{error['timestamp']}**: {error['operation']} - {error['error_type']} ({error['error_class']}) - {status}\n"
            report += f"  - Message: {error['error_message'][:100]}\n"

        return report


# Example usage
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    # Initialize manager
    recovery = ErrorRecoveryManager()

    # Example: API call with retry
    async def flaky_api_call():
        """Simulated flaky API call."""
        import random

        if random.random() < 0.7:  # 70% chance of failure
            raise TimeoutError("API timeout")
        return {"status": "success"}

    async def cached_fallback():
        """Fallback to cached data."""
        return {"status": "cached", "warning": "Using cached data"}

    # Test recovery
    async def test():
        result = await recovery.execute_with_recovery(
            operation=flaky_api_call,
            error_type="api_timeout",
            fallback=cached_fallback,
            operation_name="Test API Call",
        )
        print(f"\nResult: {result}")

        # Generate report
        print("\n" + recovery.generate_error_report())

    asyncio.run(test())
