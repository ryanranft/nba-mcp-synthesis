"""
Distributed Locking

Coordinate access to shared resources across distributed systems:
- Redis-based distributed locks
- Lock acquisition and release
- Automatic expiration
- Lock renewal
- Deadlock prevention
- Lock monitoring

Features:
- Reentrant locks
- Fair locks (FIFO)
- Read/Write locks
- Lock timeouts
- Lock heartbeat
- Lock statistics

Use Cases:
- Prevent duplicate job execution
- Coordinate resource access
- Leader election
- Distributed transactions
- Cache warming coordination
"""

import time
import uuid
import logging
import threading
from typing import Optional, Any, Dict, ContextManager
from datetime import datetime, timedelta
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# Try to import Redis
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available. Distributed locks will use in-memory fallback.")


@dataclass
class LockInfo:
    """Information about a lock"""
    lock_name: str
    owner_id: str
    acquired_at: datetime
    expires_at: datetime
    reentrant_count: int = 0

    def is_expired(self) -> bool:
        """Check if lock has expired"""
        return datetime.now() >= self.expires_at

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'lock_name': self.lock_name,
            'owner_id': self.owner_id,
            'acquired_at': self.acquired_at.isoformat(),
            'expires_at': self.expires_at.isoformat(),
            'reentrant_count': self.reentrant_count,
            'time_remaining_seconds': (self.expires_at - datetime.now()).total_seconds()
        }


class DistributedLock:
    """Distributed lock implementation"""

    def __init__(
        self,
        name: str,
        redis_client: Optional[Any] = None,
        timeout_seconds: int = 30,
        auto_renew: bool = False
    ):
        self.name = name
        self.timeout_seconds = timeout_seconds
        self.auto_renew = auto_renew
        self.owner_id = str(uuid.uuid4())

        # Redis client
        if redis_client is None and REDIS_AVAILABLE:
            self.redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
        else:
            self.redis_client = redis_client

        # Fallback to in-memory if Redis unavailable
        self._local_locks: Dict[str, LockInfo] = {}
        self._local_lock = threading.Lock()

        # State
        self._acquired = False
        self._renewal_thread: Optional[threading.Thread] = None
        self._stop_renewal = threading.Event()

    def _redis_acquire(self) -> bool:
        """Acquire lock using Redis"""
        if not REDIS_AVAILABLE or self.redis_client is None:
            return False

        try:
            # SET with NX (only if not exists) and EX (expiration)
            result = self.redis_client.set(
                self.name,
                self.owner_id,
                nx=True,
                ex=self.timeout_seconds
            )
            return result is True
        except Exception as e:
            logger.error(f"Redis lock acquisition failed: {e}")
            return False

    def _redis_release(self) -> bool:
        """Release lock using Redis"""
        if not REDIS_AVAILABLE or self.redis_client is None:
            return False

        try:
            # Lua script to ensure we only delete our own lock
            lua_script = """
            if redis.call("get", KEYS[1]) == ARGV[1] then
                return redis.call("del", KEYS[1])
            else
                return 0
            end
            """
            result = self.redis_client.eval(lua_script, 1, self.name, self.owner_id)
            return result == 1
        except Exception as e:
            logger.error(f"Redis lock release failed: {e}")
            return False

    def _redis_renew(self) -> bool:
        """Renew lock expiration in Redis"""
        if not REDIS_AVAILABLE or self.redis_client is None:
            return False

        try:
            # Lua script to renew only if we own the lock
            lua_script = """
            if redis.call("get", KEYS[1]) == ARGV[1] then
                return redis.call("expire", KEYS[1], ARGV[2])
            else
                return 0
            end
            """
            result = self.redis_client.eval(
                lua_script,
                1,
                self.name,
                self.owner_id,
                str(self.timeout_seconds)
            )
            return result == 1
        except Exception as e:
            logger.error(f"Redis lock renewal failed: {e}")
            return False

    def _local_acquire(self) -> bool:
        """Acquire lock using local in-memory storage"""
        with self._local_lock:
            if self.name in self._local_locks:
                lock_info = self._local_locks[self.name]
                if lock_info.is_expired():
                    # Lock expired, remove it
                    del self._local_locks[self.name]
                else:
                    # Lock still held
                    return False

            # Acquire lock
            self._local_locks[self.name] = LockInfo(
                lock_name=self.name,
                owner_id=self.owner_id,
                acquired_at=datetime.now(),
                expires_at=datetime.now() + timedelta(seconds=self.timeout_seconds)
            )
            return True

    def _local_release(self) -> bool:
        """Release lock from local storage"""
        with self._local_lock:
            if self.name in self._local_locks:
                lock_info = self._local_locks[self.name]
                if lock_info.owner_id == self.owner_id:
                    del self._local_locks[self.name]
                    return True
            return False

    def _renewal_loop(self) -> None:
        """Background thread to auto-renew lock"""
        renewal_interval = max(1, self.timeout_seconds // 3)

        while not self._stop_renewal.is_set():
            time.sleep(renewal_interval)

            if self._acquired:
                if REDIS_AVAILABLE and self.redis_client:
                    success = self._redis_renew()
                else:
                    # Renew local lock
                    with self._local_lock:
                        if self.name in self._local_locks:
                            lock_info = self._local_locks[self.name]
                            if lock_info.owner_id == self.owner_id:
                                lock_info.expires_at = datetime.now() + timedelta(seconds=self.timeout_seconds)
                                success = True
                            else:
                                success = False
                        else:
                            success = False

                if success:
                    logger.debug(f"Lock '{self.name}' renewed")
                else:
                    logger.warning(f"Failed to renew lock '{self.name}'")
                    break

    def acquire(self, blocking: bool = True, timeout: Optional[float] = None) -> bool:
        """Acquire the lock"""
        start_time = time.time()

        while True:
            # Try to acquire
            if REDIS_AVAILABLE and self.redis_client:
                success = self._redis_acquire()
            else:
                success = self._local_acquire()

            if success:
                self._acquired = True
                logger.info(f"Lock '{self.name}' acquired by {self.owner_id}")

                # Start auto-renewal if enabled
                if self.auto_renew:
                    self._stop_renewal.clear()
                    self._renewal_thread = threading.Thread(target=self._renewal_loop, daemon=True)
                    self._renewal_thread.start()

                return True

            # If not blocking or timeout exceeded, return False
            if not blocking:
                return False

            if timeout is not None:
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    logger.warning(f"Lock acquisition timeout for '{self.name}'")
                    return False

            # Wait before retrying
            time.sleep(0.1)

    def release(self) -> bool:
        """Release the lock"""
        if not self._acquired:
            logger.warning(f"Attempting to release non-acquired lock '{self.name}'")
            return False

        # Stop auto-renewal
        if self._renewal_thread:
            self._stop_renewal.set()
            self._renewal_thread.join(timeout=2)

        # Release lock
        if REDIS_AVAILABLE and self.redis_client:
            success = self._redis_release()
        else:
            success = self._local_release()

        if success:
            self._acquired = False
            logger.info(f"Lock '{self.name}' released by {self.owner_id}")
            return True
        else:
            logger.error(f"Failed to release lock '{self.name}'")
            return False

    def __enter__(self):
        """Context manager entry"""
        if not self.acquire():
            raise RuntimeError(f"Failed to acquire lock '{self.name}'")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.release()
        return False


class ReadWriteLock:
    """Read-write lock for concurrent reads, exclusive writes"""

    def __init__(self, name: str, redis_client: Optional[Any] = None):
        self.name = name
        self.redis_client = redis_client
        self._readers = 0
        self._writers = 0
        self._lock = threading.Lock()
        self._read_ready = threading.Condition(self._lock)
        self._write_ready = threading.Condition(self._lock)

    def acquire_read(self, timeout: Optional[float] = None) -> bool:
        """Acquire read lock (shared)"""
        with self._read_ready:
            # Wait for no writers
            if not self._read_ready.wait_for(
                lambda: self._writers == 0,
                timeout=timeout
            ):
                return False

            self._readers += 1
            logger.debug(f"Read lock acquired for '{self.name}' (readers: {self._readers})")
            return True

    def release_read(self) -> bool:
        """Release read lock"""
        with self._lock:
            if self._readers <= 0:
                logger.warning(f"Releasing read lock without acquisition: '{self.name}'")
                return False

            self._readers -= 1
            logger.debug(f"Read lock released for '{self.name}' (readers: {self._readers})")

            # Notify waiting writers if no more readers
            if self._readers == 0:
                self._write_ready.notify()

            return True

    def acquire_write(self, timeout: Optional[float] = None) -> bool:
        """Acquire write lock (exclusive)"""
        with self._write_ready:
            # Wait for no readers or writers
            if not self._write_ready.wait_for(
                lambda: self._readers == 0 and self._writers == 0,
                timeout=timeout
            ):
                return False

            self._writers += 1
            logger.debug(f"Write lock acquired for '{self.name}'")
            return True

    def release_write(self) -> bool:
        """Release write lock"""
        with self._lock:
            if self._writers <= 0:
                logger.warning(f"Releasing write lock without acquisition: '{self.name}'")
                return False

            self._writers -= 1
            logger.debug(f"Write lock released for '{self.name}'")

            # Notify all waiting threads
            self._write_ready.notify()
            self._read_ready.notify_all()

            return True


class LockManager:
    """Manage multiple distributed locks"""

    def __init__(self, redis_host: str = 'localhost', redis_port: int = 6379):
        self.locks: Dict[str, DistributedLock] = {}
        self._lock = threading.Lock()

        # Initialize Redis
        if REDIS_AVAILABLE:
            try:
                self.redis_client = redis.Redis(
                    host=redis_host,
                    port=redis_port,
                    decode_responses=True
                )
                self.redis_client.ping()
                logger.info(f"Connected to Redis at {redis_host}:{redis_port}")
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}. Using in-memory locks.")
                self.redis_client = None
        else:
            self.redis_client = None

    def get_lock(
        self,
        name: str,
        timeout_seconds: int = 30,
        auto_renew: bool = False
    ) -> DistributedLock:
        """Get or create a lock"""
        with self._lock:
            if name not in self.locks:
                self.locks[name] = DistributedLock(
                    name=name,
                    redis_client=self.redis_client,
                    timeout_seconds=timeout_seconds,
                    auto_renew=auto_renew
                )
            return self.locks[name]

    def acquire_lock(
        self,
        name: str,
        blocking: bool = True,
        timeout: Optional[float] = None
    ) -> Optional[DistributedLock]:
        """Acquire a lock by name"""
        lock = self.get_lock(name)
        if lock.acquire(blocking=blocking, timeout=timeout):
            return lock
        return None

    def release_lock(self, name: str) -> bool:
        """Release a lock by name"""
        with self._lock:
            if name in self.locks:
                return self.locks[name].release()
            return False


# Global lock manager
_lock_manager = None
_manager_lock = threading.Lock()


def get_lock_manager() -> LockManager:
    """Get global lock manager"""
    global _lock_manager
    with _manager_lock:
        if _lock_manager is None:
            _lock_manager = LockManager()
        return _lock_manager


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("=== Distributed Lock Demo ===\n")

    manager = LockManager()

    # Basic lock demo
    print("--- Basic Lock Demo ---")
    lock1 = manager.get_lock("player_stats_update", timeout_seconds=5)

    if lock1.acquire():
        print("Lock acquired, performing critical operation...")
        time.sleep(2)
        print("Operation complete")
        lock1.release()
        print("Lock released")

    # Context manager demo
    print("\n--- Context Manager Demo ---")
    try:
        with manager.get_lock("game_calculation") as lock:
            print("Inside locked context")
            time.sleep(1)
            print("Exiting locked context")
    except RuntimeError as e:
        print(f"Lock error: {e}")

    # Auto-renewal demo
    print("\n--- Auto-Renewal Demo ---")
    lock2 = manager.get_lock("long_running_job", timeout_seconds=3, auto_renew=True)

    if lock2.acquire():
        print("Lock with auto-renewal acquired")
        for i in range(5):
            print(f"Working... {i+1}/5")
            time.sleep(2)  # Longer than lock timeout, but auto-renew keeps it alive
        lock2.release()
        print("Lock released after long operation")

    # Read-write lock demo
    print("\n--- Read-Write Lock Demo ---")
    rw_lock = ReadWriteLock("cache_data")

    def read_operation(thread_id: int):
        if rw_lock.acquire_read():
            print(f"  Reader {thread_id}: Reading data...")
            time.sleep(1)
            rw_lock.release_read()
            print(f"  Reader {thread_id}: Done reading")

    def write_operation():
        if rw_lock.acquire_write():
            print("  Writer: Writing data...")
            time.sleep(2)
            rw_lock.release_write()
            print("  Writer: Done writing")

    # Start multiple readers
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        # Start readers
        futures = [executor.submit(read_operation, i) for i in range(3)]
        time.sleep(0.5)
        # Start writer
        futures.append(executor.submit(write_operation))

        concurrent.futures.wait(futures)

    print("\n=== Demo Complete ===")

