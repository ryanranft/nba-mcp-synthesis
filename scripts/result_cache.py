#!/usr/bin/env python3
"""
Result Cache - Content-based caching for expensive AI operations.

Avoids redundant work by caching:
- Book analysis results (by content hash)
- Synthesis results (by recommendation set hash)
- Plan generation results (by synthesis hash)

Benefits:
- 80-90% cost reduction on re-runs
- Faster iteration cycles
- Consistent results

Cache Strategy:
- Content-addressable: Hash book content, not filename
- TTL: 7 days default (configurable)
- Automatic invalidation on content changes
- Size management: LRU eviction when >5GB

Usage:
    cache = ResultCache()
    
    # Check cache
    cached = cache.get_cached('book_analysis', content_hash)
    if cached:
        return cached
    
    # Do expensive operation
    result = await expensive_analysis(content)
    
    # Save to cache
    cache.save_to_cache('book_analysis', content_hash, result)
"""

import hashlib
import json
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, List, Any

logger = logging.getLogger(__name__)


class ResultCache:
    """
    Content-addressable cache for AI operation results.
    
    Cache Directory Structure:
        cache/
        ├── book_analysis/
        │   ├── abc123_metadata.json
        │   └── abc123_result.json
        ├── synthesis/
        │   ├── def456_metadata.json
        │   └── def456_result.json
        └── cache_index.json
    """
    
    def __init__(self, cache_dir: Path = Path("cache"), ttl_hours: int = 168):
        """
        Initialize cache manager.
        
        Args:
            cache_dir: Root directory for cache storage
            ttl_hours: Time-to-live in hours (default: 168 = 7 days)
        """
        self.cache_dir = Path(cache_dir)
        self.ttl_hours = ttl_hours
        self.max_cache_size_gb = 5.0
        
        # Create cache directories
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        (self.cache_dir / "book_analysis").mkdir(exist_ok=True)
        (self.cache_dir / "synthesis").mkdir(exist_ok=True)
        (self.cache_dir / "plan_generation").mkdir(exist_ok=True)
        
        # Load or create cache index
        self.index_file = self.cache_dir / "cache_index.json"
        self.index = self._load_index()
        
        # Clean expired entries on init
        self._cleanup_expired()
    
    def get_content_hash(self, content: str) -> str:
        """
        Generate SHA-256 hash for content.
        
        Args:
            content: Content to hash (book text, recommendation set, etc.)
        
        Returns:
            16-character hex hash (first 16 chars of SHA-256)
        """
        return hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]
    
    def is_cached(self, operation: str, content_hash: str) -> bool:
        """
        Check if result is cached and not expired.
        
        Args:
            operation: Operation type (book_analysis, synthesis, plan_generation)
            content_hash: Content hash to check
        
        Returns:
            True if valid cache entry exists, False otherwise
        """
        cache_key = f"{operation}:{content_hash}"
        
        if cache_key not in self.index:
            return False
        
        # Check if expired
        entry = self.index[cache_key]
        cached_at = datetime.fromisoformat(entry['cached_at'])
        expires_at = cached_at + timedelta(hours=self.ttl_hours)
        
        if datetime.now() > expires_at:
            logger.debug(f"Cache entry expired: {cache_key}")
            self._remove_cache_entry(operation, content_hash)
            return False
        
        # Check if file exists
        result_file = self.cache_dir / operation / f"{content_hash}_result.json"
        if not result_file.exists():
            logger.warning(f"Cache index has entry but file missing: {result_file}")
            self._remove_cache_entry(operation, content_hash)
            return False
        
        return True
    
    def get_cached(self, operation: str, content_hash: str) -> Optional[Dict]:
        """
        Retrieve cached result.
        
        Args:
            operation: Operation type
            content_hash: Content hash
        
        Returns:
            Cached result dict, or None if not found/expired
        """
        if not self.is_cached(operation, content_hash):
            return None
        
        result_file = self.cache_dir / operation / f"{content_hash}_result.json"
        
        try:
            result = json.loads(result_file.read_text())
            
            # Update hit count and last accessed
            cache_key = f"{operation}:{content_hash}"
            self.index[cache_key]['hit_count'] = self.index[cache_key].get('hit_count', 0) + 1
            self.index[cache_key]['last_accessed'] = datetime.now().isoformat()
            self._save_index()
            
            logger.info(f"💾 Cache HIT: {operation} ({content_hash})")
            logger.info(f"   Cached at: {self.index[cache_key]['cached_at']}")
            logger.info(f"   Hit count: {self.index[cache_key]['hit_count']}")
            
            return result
        
        except Exception as e:
            logger.error(f"Failed to read cache: {e}")
            self._remove_cache_entry(operation, content_hash)
            return None
    
    def save_to_cache(
        self,
        operation: str,
        content_hash: str,
        result: Dict,
        metadata: Optional[Dict] = None
    ):
        """
        Save result to cache.
        
        Args:
            operation: Operation type
            content_hash: Content hash
            result: Result to cache
            metadata: Optional metadata (book title, model used, etc.)
        """
        result_file = self.cache_dir / operation / f"{content_hash}_result.json"
        metadata_file = self.cache_dir / operation / f"{content_hash}_metadata.json"
        
        try:
            # Save result
            result_file.write_text(json.dumps(result, indent=2))
            
            # Save metadata
            cache_metadata = {
                'content_hash': content_hash,
                'operation': operation,
                'cached_at': datetime.now().isoformat(),
                'size_bytes': len(json.dumps(result)),
                'hit_count': 0,
                **(metadata or {})
            }
            metadata_file.write_text(json.dumps(cache_metadata, indent=2))
            
            # Update index
            cache_key = f"{operation}:{content_hash}"
            self.index[cache_key] = cache_metadata
            self._save_index()
            
            logger.info(f"💾 Cached: {operation} ({content_hash})")
            logger.info(f"   Size: {cache_metadata['size_bytes'] / 1024:.1f} KB")
            
            # Check cache size and evict if needed
            self._check_cache_size()
        
        except Exception as e:
            logger.error(f"Failed to save to cache: {e}")
    
    def invalidate(self, operation: str, content_hash: str):
        """
        Manually invalidate a cache entry.
        
        Args:
            operation: Operation type
            content_hash: Content hash to invalidate
        """
        logger.info(f"🗑️  Invalidating cache: {operation} ({content_hash})")
        self._remove_cache_entry(operation, content_hash)
    
    def clear_all(self, operation: Optional[str] = None):
        """
        Clear all cache entries (or all for specific operation).
        
        Args:
            operation: Optional operation type to clear (clears all if None)
        """
        if operation:
            logger.warning(f"🗑️  Clearing all {operation} cache entries...")
            keys_to_remove = [k for k in self.index.keys() if k.startswith(f"{operation}:")]
        else:
            logger.warning("🗑️  Clearing entire cache...")
            keys_to_remove = list(self.index.keys())
        
        for cache_key in keys_to_remove:
            op, content_hash = cache_key.split(':', 1)
            self._remove_cache_entry(op, content_hash)
        
        logger.info(f"✅ Cleared {len(keys_to_remove)} cache entries")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dict with cache stats (size, hit rates, entry counts, etc.)
        """
        stats = {
            'total_entries': len(self.index),
            'by_operation': {},
            'total_size_mb': 0,
            'oldest_entry': None,
            'newest_entry': None,
            'total_hits': 0
        }
        
        for cache_key, entry in self.index.items():
            operation = cache_key.split(':', 1)[0]
            
            if operation not in stats['by_operation']:
                stats['by_operation'][operation] = {
                    'count': 0,
                    'size_mb': 0,
                    'hits': 0
                }
            
            stats['by_operation'][operation]['count'] += 1
            stats['by_operation'][operation]['size_mb'] += entry.get('size_bytes', 0) / (1024 * 1024)
            stats['by_operation'][operation]['hits'] += entry.get('hit_count', 0)
            
            stats['total_size_mb'] += entry.get('size_bytes', 0) / (1024 * 1024)
            stats['total_hits'] += entry.get('hit_count', 0)
            
            # Track oldest/newest
            cached_at = datetime.fromisoformat(entry['cached_at'])
            if not stats['oldest_entry'] or cached_at < datetime.fromisoformat(stats['oldest_entry']):
                stats['oldest_entry'] = entry['cached_at']
            if not stats['newest_entry'] or cached_at > datetime.fromisoformat(stats['newest_entry']):
                stats['newest_entry'] = entry['cached_at']
        
        return stats
    
    def print_stats(self):
        """Print cache statistics to console."""
        stats = self.get_stats()
        
        logger.info("\n" + "="*60)
        logger.info("📊 Cache Statistics")
        logger.info("="*60)
        logger.info(f"Total entries: {stats['total_entries']}")
        logger.info(f"Total size: {stats['total_size_mb']:.2f} MB / {self.max_cache_size_gb * 1024:.0f} MB")
        logger.info(f"Total hits: {stats['total_hits']}")
        
        if stats['oldest_entry']:
            logger.info(f"Oldest entry: {stats['oldest_entry']}")
        if stats['newest_entry']:
            logger.info(f"Newest entry: {stats['newest_entry']}")
        
        logger.info("\nBy operation:")
        for operation, op_stats in stats['by_operation'].items():
            hit_rate = (op_stats['hits'] / op_stats['count']) if op_stats['count'] > 0 else 0
            logger.info(f"  {operation}:")
            logger.info(f"    Entries: {op_stats['count']}")
            logger.info(f"    Size: {op_stats['size_mb']:.2f} MB")
            logger.info(f"    Hits: {op_stats['hits']} (avg {hit_rate:.1f} per entry)")
        
        logger.info("="*60 + "\n")
    
    # =========================================================================
    # Private methods
    # =========================================================================
    
    def _load_index(self) -> Dict:
        """Load cache index from disk."""
        if self.index_file.exists():
            try:
                return json.loads(self.index_file.read_text())
            except Exception as e:
                logger.warning(f"Failed to load cache index: {e}")
                return {}
        return {}
    
    def _save_index(self):
        """Save cache index to disk."""
        try:
            self.index_file.write_text(json.dumps(self.index, indent=2))
        except Exception as e:
            logger.error(f"Failed to save cache index: {e}")
    
    def _remove_cache_entry(self, operation: str, content_hash: str):
        """Remove cache entry from index and disk."""
        cache_key = f"{operation}:{content_hash}"
        
        if cache_key in self.index:
            del self.index[cache_key]
            self._save_index()
        
        # Remove files
        result_file = self.cache_dir / operation / f"{content_hash}_result.json"
        metadata_file = self.cache_dir / operation / f"{content_hash}_metadata.json"
        
        if result_file.exists():
            result_file.unlink()
        if metadata_file.exists():
            metadata_file.unlink()
    
    def _cleanup_expired(self):
        """Remove expired cache entries."""
        now = datetime.now()
        expired_keys = []
        
        for cache_key, entry in self.index.items():
            cached_at = datetime.fromisoformat(entry['cached_at'])
            expires_at = cached_at + timedelta(hours=self.ttl_hours)
            
            if now > expires_at:
                expired_keys.append(cache_key)
        
        if expired_keys:
            logger.info(f"🗑️  Cleaning up {len(expired_keys)} expired cache entries...")
            for cache_key in expired_keys:
                operation, content_hash = cache_key.split(':', 1)
                self._remove_cache_entry(operation, content_hash)
    
    def _check_cache_size(self):
        """Check cache size and evict LRU entries if needed."""
        stats = self.get_stats()
        
        if stats['total_size_mb'] > self.max_cache_size_gb * 1024:
            logger.warning(f"⚠️  Cache size {stats['total_size_mb']:.2f} MB exceeds limit {self.max_cache_size_gb * 1024:.0f} MB")
            logger.warning("   Evicting least-recently-used entries...")
            
            # Sort by last accessed (or cached_at if never accessed)
            entries = []
            for cache_key, entry in self.index.items():
                last_accessed = entry.get('last_accessed', entry['cached_at'])
                entries.append((cache_key, last_accessed, entry.get('size_bytes', 0)))
            
            entries.sort(key=lambda x: x[1])  # Sort by timestamp
            
            # Evict oldest until under 80% of limit
            target_size = self.max_cache_size_gb * 1024 * 0.8
            current_size = stats['total_size_mb']
            evicted = 0
            
            for cache_key, _, size_bytes in entries:
                if current_size <= target_size:
                    break
                
                operation, content_hash = cache_key.split(':', 1)
                self._remove_cache_entry(operation, content_hash)
                current_size -= size_bytes / (1024 * 1024)
                evicted += 1
            
            logger.info(f"✅ Evicted {evicted} entries, cache now {current_size:.2f} MB")


if __name__ == "__main__":
    """Test cache functionality."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    cache = ResultCache()
    
    # Test 1: Save and retrieve
    print("\n=== Test 1: Save and Retrieve ===")
    test_content = "This is a test book content"
    content_hash = cache.get_content_hash(test_content)
    
    test_result = {
        'recommendations': [
            {'title': 'Test Rec 1', 'priority': 'critical'},
            {'title': 'Test Rec 2', 'priority': 'important'}
        ],
        'analysis_metadata': {
            'model': 'gemini-2.0-flash-exp',
            'tokens': 12345,
            'cost': 0.25
        }
    }
    
    # Save to cache
    cache.save_to_cache(
        'book_analysis',
        content_hash,
        test_result,
        metadata={'book_title': 'Test Book'}
    )
    
    # Retrieve from cache
    cached_result = cache.get_cached('book_analysis', content_hash)
    assert cached_result == test_result, "Cache retrieval failed"
    print("✅ Save and retrieve successful")
    
    # Test 2: Cache stats
    print("\n=== Test 2: Cache Statistics ===")
    cache.print_stats()
    
    # Test 3: Cache miss
    print("\n=== Test 3: Cache Miss ===")
    fake_hash = "nonexistent_hash"
    result = cache.get_cached('book_analysis', fake_hash)
    assert result is None, "Should return None for cache miss"
    print("✅ Cache miss handled correctly")
    
    print("\n✅ All cache tests passed!")

