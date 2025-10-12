"""
Idempotency Module
Ensures operations can be safely retried without side effects.
"""

import logging
import hashlib
import json
from typing import Dict, Optional, Any, Callable
from datetime import datetime, timedelta
from functools import wraps
import threading

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IdempotencyKeyStore:
    """In-memory store for idempotency keys (use Redis in production)"""
    
    def __init__(self, ttl_seconds: int = 86400):  # 24 hours default
        self.store: Dict[str, Dict[str, Any]] = {}
        self.ttl_seconds = ttl_seconds
        self.lock = threading.Lock()
    
    def generate_key(self, *args, **kwargs) -> str:
        """Generate idempotency key from arguments"""
        content = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cached result for idempotency key"""
        with self.lock:
            if key in self.store:
                entry = self.store[key]
                # Check if expired
                created_at = datetime.fromisoformat(entry["created_at"])
                if datetime.utcnow() - created_at > timedelta(seconds=self.ttl_seconds):
                    del self.store[key]
                    return None
                return entry
            return None
    
    def set(self, key: str, result: Any, metadata: Optional[Dict] = None):
        """Store result for idempotency key"""
        with self.lock:
            self.store[key] = {
                "result": result,
                "created_at": datetime.utcnow().isoformat(),
                "metadata": metadata or {}
            }
    
    def delete(self, key: str):
        """Delete idempotency key"""
        with self.lock:
            if key in self.store:
                del self.store[key]
    
    def clear_expired(self):
        """Clear all expired keys"""
        with self.lock:
            now = datetime.utcnow()
            expired_keys = [
                key for key, entry in self.store.items()
                if now - datetime.fromisoformat(entry["created_at"]) > timedelta(seconds=self.ttl_seconds)
            ]
            for key in expired_keys:
                del self.store[key]
            if expired_keys:
                logger.info(f"Cleared {len(expired_keys)} expired idempotency keys")


# Global idempotency store
_idempotency_store = IdempotencyKeyStore()


def idempotent(ttl_seconds: int = 86400):
    """
    Decorator to make a function idempotent.
    
    Args:
        ttl_seconds: Time-to-live for idempotency key (default 24 hours)
    
    Example:
        @idempotent(ttl_seconds=3600)
        def create_payment(user_id, amount):
            # Process payment
            return {"transaction_id": "tx123"}
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate idempotency key
            key = _idempotency_store.generate_key(func.__name__, *args, **kwargs)
            
            # Check if result already exists
            cached = _idempotency_store.get(key)
            if cached:
                logger.info(f"Idempotent call to {func.__name__}: returning cached result")
                return cached["result"]
            
            # Execute function
            logger.info(f"Idempotent call to {func.__name__}: executing")
            result = func(*args, **kwargs)
            
            # Store result
            _idempotency_store.set(key, result, {
                "function": func.__name__,
                "executed_at": datetime.utcnow().isoformat()
            })
            
            return result
        
        return wrapper
    return decorator


class IdempotentOperationManager:
    """Manages idempotent operations with explicit control"""
    
    def __init__(self):
        self.store = IdempotencyKeyStore()
    
    def execute_once(
        self,
        operation_id: str,
        operation_func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute an operation once, even if called multiple times.
        
        Args:
            operation_id: Unique operation identifier
            operation_func: Function to execute
            *args, **kwargs: Arguments for function
            
        Returns:
            Operation result
        """
        # Check if already executed
        cached = self.store.get(operation_id)
        if cached:
            logger.info(f"Operation '{operation_id}' already executed, returning cached result")
            return cached["result"]
        
        # Execute operation
        logger.info(f"Executing operation '{operation_id}'")
        result = operation_func(*args, **kwargs)
        
        # Store result
        self.store.set(operation_id, result, {
            "operation_id": operation_id,
            "executed_at": datetime.utcnow().isoformat()
        })
        
        return result
    
    def is_executed(self, operation_id: str) -> bool:
        """Check if operation was already executed"""
        return self.store.get(operation_id) is not None
    
    def get_result(self, operation_id: str) -> Optional[Any]:
        """Get result of executed operation"""
        cached = self.store.get(operation_id)
        return cached["result"] if cached else None
    
    def clear_operation(self, operation_id: str):
        """Clear an operation (allow re-execution)"""
        self.store.delete(operation_id)
        logger.info(f"Cleared operation '{operation_id}'")


# Example usage
if __name__ == "__main__":
    print("=" * 80)
    print("IDEMPOTENCY MODULE DEMO")
    print("=" * 80)
    
    # Example 1: Using @idempotent decorator
    print("\n" + "=" * 80)
    print("EXAMPLE 1: Decorator-based Idempotency")
    print("=" * 80)
    
    @idempotent(ttl_seconds=60)
    def create_payment(user_id: int, amount: float):
        """Simulate payment creation"""
        import random
        transaction_id = f"tx_{random.randint(1000, 9999)}"
        logger.info(f"Processing payment: user={user_id}, amount=${amount}, tx_id={transaction_id}")
        return {
            "transaction_id": transaction_id,
            "user_id": user_id,
            "amount": amount,
            "status": "completed"
        }
    
    # First call - executes
    print("\nFirst call:")
    result1 = create_payment(user_id=123, amount=99.99)
    print(f"Result: {result1}")
    
    # Second call - returns cached result (idempotent)
    print("\nSecond call (should return cached):")
    result2 = create_payment(user_id=123, amount=99.99)
    print(f"Result: {result2}")
    
    # Verify same transaction_id
    print(f"\nTransaction IDs match: {result1['transaction_id'] == result2['transaction_id']}")
    
    # Example 2: Using IdempotentOperationManager
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Manager-based Idempotency")
    print("=" * 80)
    
    manager = IdempotentOperationManager()
    
    def send_notification(user_id: int, message: str):
        """Simulate sending notification"""
        logger.info(f"Sending notification to user {user_id}: {message}")
        return {"notification_id": f"notif_{user_id}", "sent_at": datetime.utcnow().isoformat()}
    
    operation_id = "send_welcome_email_user_456"
    
    # First execution
    print(f"\nExecuting operation '{operation_id}':")
    result1 = manager.execute_once(
        operation_id,
        send_notification,
        user_id=456,
        message="Welcome to NBA MCP!"
    )
    print(f"Result: {result1}")
    
    # Second execution (idempotent)
    print(f"\nRe-executing operation '{operation_id}':")
    result2 = manager.execute_once(
        operation_id,
        send_notification,
        user_id=456,
        message="Welcome to NBA MCP!"
    )
    print(f"Result: {result2}")
    
    # Check if executed
    print(f"\nOperation executed: {manager.is_executed(operation_id)}")
    
    # Get result
    print(f"Stored result: {manager.get_result(operation_id)}")
    
    # Clear and re-execute
    print("\n" + "=" * 80)
    print("Clearing operation and re-executing:")
    print("=" * 80)
    
    manager.clear_operation(operation_id)
    result3 = manager.execute_once(
        operation_id,
        send_notification,
        user_id=456,
        message="Welcome to NBA MCP!"
    )
    print(f"Result after clear: {result3}")
    
    print("\n" + "=" * 80)
    print("Idempotency Demo Complete!")
    print("=" * 80)

