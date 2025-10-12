"""
Resource Pooling

Efficient resource management through pooling:
- Connection pooling
- Thread pooling
- Object pooling
- Resource lifecycle management
- Health checking
- Dynamic sizing

Features:
- Min/max pool size
- Idle timeout
- Connection validation
- Pool statistics
- Resource recycling
- Overflow handling

Use Cases:
- Database connections
- HTTP connections
- ML model instances
- Worker threads
- File handles
"""

import time
import logging
import threading
from typing import Generic, TypeVar, Optional, Callable, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from queue import Queue, Empty, Full
from contextlib import contextmanager

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ResourceState(Enum):
    """Resource state"""
    IDLE = "idle"
    IN_USE = "in_use"
    INVALID = "invalid"
    CLOSED = "closed"


@dataclass
class PooledResource(Generic[T]):
    """Wrapper for pooled resource"""
    resource: T
    resource_id: str
    state: ResourceState = ResourceState.IDLE
    created_at: datetime = field(default_factory=datetime.now)
    last_used_at: Optional[datetime] = None
    use_count: int = 0
    error_count: int = 0
    
    def mark_in_use(self) -> None:
        """Mark resource as in use"""
        self.state = ResourceState.IN_USE
        self.last_used_at = datetime.now()
        self.use_count += 1
    
    def mark_idle(self) -> None:
        """Mark resource as idle"""
        self.state = ResourceState.IDLE
    
    def mark_invalid(self) -> None:
        """Mark resource as invalid"""
        self.state = ResourceState.INVALID
        self.error_count += 1
    
    def is_expired(self, max_age_seconds: int) -> bool:
        """Check if resource has expired"""
        age = (datetime.now() - self.created_at).total_seconds()
        return age >= max_age_seconds
    
    def idle_time_seconds(self) -> float:
        """Get time since last use"""
        if not self.last_used_at:
            return (datetime.now() - self.created_at).total_seconds()
        return (datetime.now() - self.last_used_at).total_seconds()


class ResourcePool(Generic[T]):
    """Generic resource pool"""
    
    def __init__(
        self,
        factory: Callable[[], T],
        validator: Optional[Callable[[T], bool]] = None,
        destructor: Optional[Callable[[T], None]] = None,
        min_size: int = 2,
        max_size: int = 10,
        max_idle_seconds: int = 300,
        max_age_seconds: int = 3600,
        validation_interval_seconds: int = 60
    ):
        self.factory = factory
        self.validator = validator or (lambda r: True)
        self.destructor = destructor or (lambda r: None)
        self.min_size = min_size
        self.max_size = max_size
        self.max_idle_seconds = max_idle_seconds
        self.max_age_seconds = max_age_seconds
        self.validation_interval_seconds = validation_interval_seconds
        
        # Pool state
        self._resources: Dict[str, PooledResource[T]] = {}
        self._available: Queue[str] = Queue(maxsize=max_size)
        self._lock = threading.RLock()
        self._next_id = 0
        
        # Monitoring
        self._total_created = 0
        self._total_destroyed = 0
        self._total_acquisitions = 0
        self._total_validation_failures = 0
        
        # Background threads
        self._cleaner_thread: Optional[threading.Thread] = None
        self._validator_thread: Optional[threading.Thread] = None
        self._running = False
        
        # Initialize pool
        self._initialize_pool()
        self._start_background_tasks()
    
    def _generate_id(self) -> str:
        """Generate unique resource ID"""
        with self._lock:
            resource_id = f"resource_{self._next_id}"
            self._next_id += 1
            return resource_id
    
    def _create_resource(self) -> PooledResource[T]:
        """Create new pooled resource"""
        try:
            resource = self.factory()
            pooled = PooledResource(
                resource=resource,
                resource_id=self._generate_id()
            )
            
            with self._lock:
                self._resources[pooled.resource_id] = pooled
                self._total_created += 1
            
            logger.debug(f"Created resource: {pooled.resource_id}")
            return pooled
        except Exception as e:
            logger.error(f"Failed to create resource: {e}")
            raise
    
    def _destroy_resource(self, pooled: PooledResource[T]) -> None:
        """Destroy pooled resource"""
        try:
            pooled.state = ResourceState.CLOSED
            self.destructor(pooled.resource)
            
            with self._lock:
                if pooled.resource_id in self._resources:
                    del self._resources[pooled.resource_id]
                self._total_destroyed += 1
            
            logger.debug(f"Destroyed resource: {pooled.resource_id}")
        except Exception as e:
            logger.error(f"Error destroying resource {pooled.resource_id}: {e}")
    
    def _initialize_pool(self) -> None:
        """Initialize pool with minimum resources"""
        for _ in range(self.min_size):
            pooled = self._create_resource()
            self._available.put_nowait(pooled.resource_id)
    
    def _validate_resource(self, pooled: PooledResource[T]) -> bool:
        """Validate resource"""
        try:
            return self.validator(pooled.resource)
        except Exception as e:
            logger.error(f"Validation error for {pooled.resource_id}: {e}")
            return False
    
    def _cleanup_loop(self) -> None:
        """Background thread to cleanup idle/expired resources"""
        while self._running:
            time.sleep(10)  # Run every 10 seconds
            
            with self._lock:
                to_remove = []
                
                for resource_id, pooled in self._resources.items():
                    # Check if idle too long
                    if pooled.state == ResourceState.IDLE:
                        if pooled.idle_time_seconds() >= self.max_idle_seconds:
                            to_remove.append(pooled)
                            logger.info(f"Removing idle resource: {resource_id}")
                    
                    # Check if too old
                    if pooled.is_expired(self.max_age_seconds):
                        to_remove.append(pooled)
                        logger.info(f"Removing expired resource: {resource_id}")
                    
                    # Check if invalid
                    if pooled.state == ResourceState.INVALID:
                        to_remove.append(pooled)
                
                # Remove from available queue
                for pooled in to_remove:
                    try:
                        # Try to remove from queue (may not be there)
                        temp_queue = Queue()
                        while True:
                            try:
                                rid = self._available.get_nowait()
                                if rid != pooled.resource_id:
                                    temp_queue.put_nowait(rid)
                            except Empty:
                                break
                        
                        # Put back non-removed items
                        while True:
                            try:
                                self._available.put_nowait(temp_queue.get_nowait())
                            except Empty:
                                break
                    except Exception as e:
                        logger.error(f"Error removing from queue: {e}")
                    
                    # Destroy resource
                    self._destroy_resource(pooled)
                
                # Ensure minimum size
                current_size = len(self._resources)
                if current_size < self.min_size:
                    for _ in range(self.min_size - current_size):
                        try:
                            pooled = self._create_resource()
                            self._available.put_nowait(pooled.resource_id)
                        except Exception as e:
                            logger.error(f"Failed to restore minimum pool size: {e}")
    
    def _validation_loop(self) -> None:
        """Background thread to validate idle resources"""
        while self._running:
            time.sleep(self.validation_interval_seconds)
            
            with self._lock:
                for pooled in self._resources.values():
                    if pooled.state == ResourceState.IDLE:
                        if not self._validate_resource(pooled):
                            pooled.mark_invalid()
                            self._total_validation_failures += 1
                            logger.warning(f"Resource validation failed: {pooled.resource_id}")
    
    def _start_background_tasks(self) -> None:
        """Start background maintenance threads"""
        self._running = True
        
        self._cleaner_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self._cleaner_thread.start()
        
        self._validator_thread = threading.Thread(target=self._validation_loop, daemon=True)
        self._validator_thread.start()
        
        logger.info("Resource pool background tasks started")
    
    def acquire(self, timeout: Optional[float] = 10.0) -> T:
        """Acquire resource from pool"""
        self._total_acquisitions += 1
        
        while True:
            try:
                # Try to get from available queue
                resource_id = self._available.get(timeout=timeout)
                
                with self._lock:
                    pooled = self._resources.get(resource_id)
                    
                    if not pooled:
                        continue  # Resource was destroyed
                    
                    # Validate resource
                    if not self._validate_resource(pooled):
                        pooled.mark_invalid()
                        self._destroy_resource(pooled)
                        continue
                    
                    # Mark as in use
                    pooled.mark_in_use()
                    logger.debug(f"Acquired resource: {resource_id}")
                    return pooled.resource
                    
            except Empty:
                # Queue timeout, try to create new resource if under max
                with self._lock:
                    if len(self._resources) < self.max_size:
                        try:
                            pooled = self._create_resource()
                            pooled.mark_in_use()
                            logger.debug(f"Created and acquired new resource: {pooled.resource_id}")
                            return pooled.resource
                        except Exception as e:
                            logger.error(f"Failed to create resource: {e}")
                            raise
                    else:
                        raise RuntimeError("Pool exhausted and cannot create more resources")
    
    def release(self, resource: T) -> None:
        """Release resource back to pool"""
        with self._lock:
            # Find the pooled resource
            pooled = None
            for pr in self._resources.values():
                if pr.resource is resource:
                    pooled = pr
                    break
            
            if not pooled:
                logger.warning("Attempting to release unknown resource")
                return
            
            # Validate before returning to pool
            if self._validate_resource(pooled):
                pooled.mark_idle()
                try:
                    self._available.put_nowait(pooled.resource_id)
                    logger.debug(f"Released resource: {pooled.resource_id}")
                except Full:
                    # Pool full, destroy resource
                    logger.warning(f"Pool full, destroying resource: {pooled.resource_id}")
                    self._destroy_resource(pooled)
            else:
                # Invalid, destroy it
                pooled.mark_invalid()
                self._destroy_resource(pooled)
    
    @contextmanager
    def get_resource(self, timeout: Optional[float] = 10.0):
        """Context manager for acquiring/releasing resource"""
        resource = self.acquire(timeout=timeout)
        try:
            yield resource
        finally:
            self.release(resource)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics"""
        with self._lock:
            total_resources = len(self._resources)
            idle_resources = sum(
                1 for r in self._resources.values()
                if r.state == ResourceState.IDLE
            )
            in_use_resources = sum(
                1 for r in self._resources.values()
                if r.state == ResourceState.IN_USE
            )
            invalid_resources = sum(
                1 for r in self._resources.values()
                if r.state == ResourceState.INVALID
            )
            
            return {
                'total_resources': total_resources,
                'idle_resources': idle_resources,
                'in_use_resources': in_use_resources,
                'invalid_resources': invalid_resources,
                'available_capacity': self.max_size - total_resources,
                'utilization_percent': (in_use_resources / self.max_size * 100) if self.max_size > 0 else 0,
                'total_created': self._total_created,
                'total_destroyed': self._total_destroyed,
                'total_acquisitions': self._total_acquisitions,
                'total_validation_failures': self._total_validation_failures
            }
    
    def shutdown(self) -> None:
        """Shutdown pool and cleanup resources"""
        logger.info("Shutting down resource pool...")
        self._running = False
        
        # Wait for background threads
        if self._cleaner_thread:
            self._cleaner_thread.join(timeout=5)
        if self._validator_thread:
            self._validator_thread.join(timeout=5)
        
        # Destroy all resources
        with self._lock:
            for pooled in list(self._resources.values()):
                self._destroy_resource(pooled)
        
        logger.info("Resource pool shutdown complete")


# Example: Database connection pool
class MockConnection:
    """Mock database connection for demo"""
    def __init__(self):
        self.connected = True
        self.query_count = 0
    
    def query(self, sql: str) -> List[Dict[str, Any]]:
        if not self.connected:
            raise Exception("Connection closed")
        self.query_count += 1
        time.sleep(0.1)  # Simulate query
        return [{"result": f"Query result for: {sql}"}]
    
    def close(self) -> None:
        self.connected = False


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("=== Resource Pool Demo ===\n")
    
    # Create connection pool
    def create_connection():
        logger.info("Creating new database connection")
        return MockConnection()
    
    def validate_connection(conn: MockConnection) -> bool:
        return conn.connected
    
    def close_connection(conn: MockConnection) -> None:
        logger.info("Closing database connection")
        conn.close()
    
    pool = ResourcePool(
        factory=create_connection,
        validator=validate_connection,
        destructor=close_connection,
        min_size=2,
        max_size=5,
        max_idle_seconds=30
    )
    
    print("--- Basic Usage ---")
    
    # Acquire and release
    conn = pool.acquire()
    result = conn.query("SELECT * FROM players")
    print(f"Query result: {result[0]}")
    pool.release(conn)
    
    # Context manager
    print("\n--- Context Manager ---")
    with pool.get_resource() as conn:
        result = conn.query("SELECT * FROM games")
        print(f"Query result: {result[0]}")
    
    # Multiple acquisitions
    print("\n--- Concurrent Usage ---")
    connections = []
    for i in range(3):
        conn = pool.acquire()
        connections.append(conn)
        print(f"Acquired connection {i+1}")
    
    # Release them
    for i, conn in enumerate(connections):
        pool.release(conn)
        print(f"Released connection {i+1}")
    
    # Statistics
    print("\n--- Pool Statistics ---")
    stats = pool.get_stats()
    print(f"Total resources: {stats['total_resources']}")
    print(f"Idle: {stats['idle_resources']}")
    print(f"In use: {stats['in_use_resources']}")
    print(f"Utilization: {stats['utilization_percent']:.1f}%")
    print(f"Total created: {stats['total_created']}")
    print(f"Total acquisitions: {stats['total_acquisitions']}")
    
    # Cleanup
    pool.shutdown()
    
    print("\n=== Demo Complete ===")

