"""
Caching Manager

Intelligent caching system for IFC data and processing results with memory management.
"""

import json
import os
import pickle
import hashlib
import time
from typing import Dict, List, Any, Optional, Union, Callable
from pathlib import Path
from datetime import datetime, timedelta
import threading
import weakref
import gc


class CacheConfig:
    """Configuration for caching system."""
    
    def __init__(self, 
                 max_memory_mb: int = 512,
                 max_disk_mb: int = 1024,
                 cache_ttl_seconds: int = 3600,
                 enable_disk_cache: bool = True,
                 enable_memory_cache: bool = True,
                 cache_directory: Optional[str] = None):
        """
        Initialize cache configuration.
        
        Args:
            max_memory_mb: Maximum memory cache size in MB
            max_disk_mb: Maximum disk cache size in MB
            cache_ttl_seconds: Cache time-to-live in seconds
            enable_disk_cache: Enable disk-based caching
            enable_memory_cache: Enable memory-based caching
            cache_directory: Directory for disk cache (default: temp)
        """
        self.max_memory_mb = max_memory_mb
        self.max_disk_mb = max_disk_mb
        self.cache_ttl_seconds = cache_ttl_seconds
        self.enable_disk_cache = enable_disk_cache
        self.enable_memory_cache = enable_memory_cache
        self.cache_directory = cache_directory or os.path.join(os.path.expanduser("~"), ".romskjema_cache")
        
        # Create cache directory if it doesn't exist
        if self.enable_disk_cache:
            os.makedirs(self.cache_directory, exist_ok=True)


class CacheEntry:
    """Individual cache entry."""
    
    def __init__(self, key: str, value: Any, ttl_seconds: int = 3600):
        """
        Initialize cache entry.
        
        Args:
            key: Cache key
            value: Cached value
            ttl_seconds: Time-to-live in seconds
        """
        self.key = key
        self.value = value
        self.created_at = time.time()
        self.last_accessed = time.time()
        self.ttl_seconds = ttl_seconds
        self.access_count = 0
        self.size_bytes = self._estimate_size()
    
    def _estimate_size(self) -> int:
        """Estimate size of cached value in bytes."""
        try:
            if isinstance(self.value, (str, bytes)):
                return len(self.value)
            elif isinstance(self.value, (dict, list)):
                return len(json.dumps(self.value, default=str).encode('utf-8'))
            else:
                return len(pickle.dumps(self.value))
        except:
            return 1024  # Default estimate
    
    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        return time.time() - self.created_at > self.ttl_seconds
    
    def touch(self):
        """Update last accessed time and access count."""
        self.last_accessed = time.time()
        self.access_count += 1
    
    def get_value(self) -> Any:
        """Get cached value and update access info."""
        if self.is_expired():
            return None
        self.touch()
        return self.value


class MemoryCache:
    """In-memory cache with LRU eviction."""
    
    def __init__(self, max_memory_mb: int = 512):
        """
        Initialize memory cache.
        
        Args:
            max_memory_mb: Maximum memory usage in MB
        """
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.cache: Dict[str, CacheEntry] = {}
        self.current_memory_bytes = 0
        self.lock = threading.RLock()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        with self.lock:
            if key not in self.cache:
                return None
            
            entry = self.cache[key]
            if entry.is_expired():
                del self.cache[key]
                self.current_memory_bytes -= entry.size_bytes
                return None
            
            return entry.get_value()
    
    def set(self, key: str, value: Any, ttl_seconds: int = 3600) -> bool:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Time-to-live in seconds
            
        Returns:
            True if successfully cached, False otherwise
        """
        with self.lock:
            # Remove existing entry if it exists
            if key in self.cache:
                old_entry = self.cache[key]
                self.current_memory_bytes -= old_entry.size_bytes
                del self.cache[key]
            
            # Create new entry
            entry = CacheEntry(key, value, ttl_seconds)
            
            # Check if we have enough space
            if entry.size_bytes > self.max_memory_bytes:
                return False
            
            # Evict entries if necessary
            while (self.current_memory_bytes + entry.size_bytes > self.max_memory_bytes 
                   and self.cache):
                self._evict_lru()
            
            # Add new entry
            self.cache[key] = entry
            self.current_memory_bytes += entry.size_bytes
            
            return True
    
    def _evict_lru(self):
        """Evict least recently used entry."""
        if not self.cache:
            return
        
        lru_key = min(self.cache.keys(), 
                     key=lambda k: self.cache[k].last_accessed)
        
        entry = self.cache[lru_key]
        del self.cache[lru_key]
        self.current_memory_bytes -= entry.size_bytes
    
    def clear(self):
        """Clear all cache entries."""
        with self.lock:
            self.cache.clear()
            self.current_memory_bytes = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self.lock:
            return {
                "entries": len(self.cache),
                "memory_bytes": self.current_memory_bytes,
                "memory_mb": self.current_memory_bytes / (1024 * 1024),
                "max_memory_mb": self.max_memory_bytes / (1024 * 1024)
            }


class DiskCache:
    """Disk-based cache with file system storage."""
    
    def __init__(self, cache_directory: str, max_disk_mb: int = 1024):
        """
        Initialize disk cache.
        
        Args:
            cache_directory: Directory for cache files
            max_disk_mb: Maximum disk usage in MB
        """
        self.cache_directory = Path(cache_directory)
        self.max_disk_mb = max_disk_mb
        self.max_disk_bytes = max_disk_mb * 1024 * 1024
        self.lock = threading.RLock()
        
        # Create cache directory
        self.cache_directory.mkdir(parents=True, exist_ok=True)
    
    def _get_cache_path(self, key: str) -> Path:
        """Get cache file path for key."""
        # Use hash to avoid filesystem issues with special characters
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return self.cache_directory / f"{key_hash}.cache"
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from disk cache."""
        with self.lock:
            cache_path = self._get_cache_path(key)
            
            if not cache_path.exists():
                return None
            
            try:
                with open(cache_path, 'rb') as f:
                    entry = pickle.load(f)
                
                if entry.is_expired():
                    cache_path.unlink()
                    return None
                
                entry.touch()
                return entry.get_value()
                
            except (pickle.PickleError, IOError):
                # Remove corrupted cache file
                if cache_path.exists():
                    cache_path.unlink()
                return None
    
    def set(self, key: str, value: Any, ttl_seconds: int = 3600) -> bool:
        """
        Set value in disk cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Time-to-live in seconds
            
        Returns:
            True if successfully cached, False otherwise
        """
        with self.lock:
            try:
                # Check disk space
                if self._get_disk_usage() > self.max_disk_bytes:
                    self._cleanup_old_entries()
                
                # Create cache entry
                entry = CacheEntry(key, value, ttl_seconds)
                
                # Write to disk
                cache_path = self._get_cache_path(key)
                with open(cache_path, 'wb') as f:
                    pickle.dump(entry, f)
                
                return True
                
            except (IOError, OSError):
                return False
    
    def _get_disk_usage(self) -> int:
        """Get current disk cache usage in bytes."""
        total_size = 0
        for cache_file in self.cache_directory.glob("*.cache"):
            total_size += cache_file.stat().st_size
        return total_size
    
    def _cleanup_old_entries(self):
        """Remove old cache entries."""
        current_time = time.time()
        
        for cache_file in self.cache_directory.glob("*.cache"):
            try:
                with open(cache_file, 'rb') as f:
                    entry = pickle.load(f)
                
                if entry.is_expired() or current_time - entry.last_accessed > 86400:  # 24 hours
                    cache_file.unlink()
                    
            except (pickle.PickleError, IOError):
                cache_file.unlink()
    
    def clear(self):
        """Clear all disk cache entries."""
        with self.lock:
            for cache_file in self.cache_directory.glob("*.cache"):
                cache_file.unlink()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get disk cache statistics."""
        with self.lock:
            files = list(self.cache_directory.glob("*.cache"))
            total_size = sum(f.stat().st_size for f in files)
            
            return {
                "files": len(files),
                "disk_bytes": total_size,
                "disk_mb": total_size / (1024 * 1024),
                "max_disk_mb": self.max_disk_mb / (1024 * 1024)
            }


class CachingManager:
    """Main caching manager with memory and disk cache."""
    
    def __init__(self, config: Optional[CacheConfig] = None):
        """
        Initialize caching manager.
        
        Args:
            config: Cache configuration
        """
        self.config = config or CacheConfig()
        
        # Initialize caches
        self.memory_cache = MemoryCache(self.config.max_memory_mb) if self.config.enable_memory_cache else None
        self.disk_cache = DiskCache(self.config.cache_directory, self.config.max_disk_mb) if self.config.enable_disk_cache else None
        
        # Statistics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "memory_hits": 0,
            "disk_hits": 0,
            "evictions": 0
        }
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        # Try memory cache first
        if self.memory_cache:
            value = self.memory_cache.get(key)
            if value is not None:
                self.stats["hits"] += 1
                self.stats["memory_hits"] += 1
                return value
        
        # Try disk cache
        if self.disk_cache:
            value = self.disk_cache.get(key)
            if value is not None:
                self.stats["hits"] += 1
                self.stats["disk_hits"] += 1
                
                # Promote to memory cache
                if self.memory_cache:
                    self.memory_cache.set(key, value, self.config.cache_ttl_seconds)
                
                return value
        
        self.stats["misses"] += 1
        return None
    
    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> bool:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Time-to-live in seconds (uses config default if None)
            
        Returns:
            True if successfully cached
        """
        ttl = ttl_seconds or self.config.cache_ttl_seconds
        success = True
        
        # Set in memory cache
        if self.memory_cache:
            success &= self.memory_cache.set(key, value, ttl)
        
        # Set in disk cache
        if self.disk_cache:
            success &= self.disk_cache.set(key, value, ttl)
        
        return success
    
    def get_or_set(self, key: str, factory: Callable[[], Any], ttl_seconds: Optional[int] = None) -> Any:
        """
        Get value from cache or set it using factory function.
        
        Args:
            key: Cache key
            factory: Function to create value if not in cache
            ttl_seconds: Time-to-live in seconds
            
        Returns:
            Cached or newly created value
        """
        value = self.get(key)
        if value is not None:
            return value
        
        # Create value using factory
        value = factory()
        self.set(key, value, ttl_seconds)
        return value
    
    def clear(self):
        """Clear all caches."""
        if self.memory_cache:
            self.memory_cache.clear()
        if self.disk_cache:
            self.disk_cache.clear()
    
    def cleanup(self):
        """Clean up expired entries and optimize memory."""
        if self.memory_cache:
            # Memory cache cleanup is handled automatically
            pass
        
        if self.disk_cache:
            self.disk_cache._cleanup_old_entries()
        
        # Force garbage collection
        gc.collect()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        stats = self.stats.copy()
        
        if self.memory_cache:
            memory_stats = self.memory_cache.get_stats()
            stats.update({f"memory_{k}": v for k, v in memory_stats.items()})
        
        if self.disk_cache:
            disk_stats = self.disk_cache.get_stats()
            stats.update({f"disk_{k}": v for k, v in disk_stats.items()})
        
        # Calculate hit rate
        total_requests = stats["hits"] + stats["misses"]
        stats["hit_rate"] = stats["hits"] / total_requests if total_requests > 0 else 0.0
        
        return stats


class CacheKeyGenerator:
    """Utility for generating consistent cache keys."""
    
    @staticmethod
    def generate_key(prefix: str, *args, **kwargs) -> str:
        """
        Generate a cache key from prefix and arguments.
        
        Args:
            prefix: Key prefix
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Generated cache key
        """
        # Convert args and kwargs to string representation
        args_str = "_".join(str(arg) for arg in args)
        kwargs_str = "_".join(f"{k}={v}" for k, v in sorted(kwargs.items()))
        
        # Combine all parts
        key_parts = [prefix]
        if args_str:
            key_parts.append(args_str)
        if kwargs_str:
            key_parts.append(kwargs_str)
        
        return "_".join(key_parts)
    
    @staticmethod
    def generate_file_key(file_path: str, operation: str, **kwargs) -> str:
        """
        Generate cache key for file operations.
        
        Args:
            file_path: Path to file
            operation: Operation type
            **kwargs: Additional parameters
            
        Returns:
            Generated cache key
        """
        # Include file modification time for cache invalidation
        try:
            mtime = os.path.getmtime(file_path)
            kwargs["mtime"] = int(mtime)
        except OSError:
            pass
        
        return CacheKeyGenerator.generate_key("file", file_path, operation, **kwargs)
    
    @staticmethod
    def generate_space_key(space_guid: str, export_profile: str, **kwargs) -> str:
        """
        Generate cache key for space processing.
        
        Args:
            space_guid: Space GUID
            export_profile: Export profile
            **kwargs: Additional parameters
            
        Returns:
            Generated cache key
        """
        return CacheKeyGenerator.generate_key("space", space_guid, export_profile, **kwargs)


# Global cache manager instance
_global_cache_manager: Optional[CachingManager] = None


def get_cache_manager() -> CachingManager:
    """Get global cache manager instance."""
    global _global_cache_manager
    if _global_cache_manager is None:
        _global_cache_manager = CachingManager()
    return _global_cache_manager


def set_cache_manager(cache_manager: CachingManager):
    """Set global cache manager instance."""
    global _global_cache_manager
    _global_cache_manager = cache_manager


# Example usage
if __name__ == "__main__":
    # Test caching manager
    config = CacheConfig(max_memory_mb=64, max_disk_mb=128)
    cache = CachingManager(config)
    
    # Test basic operations
    cache.set("test_key", {"data": "test_value"}, ttl_seconds=60)
    value = cache.get("test_key")
    print(f"Retrieved value: {value}")
    
    # Test get_or_set
    def expensive_operation():
        print("Performing expensive operation...")
        time.sleep(0.1)
        return {"result": "expensive_data"}
    
    result = cache.get_or_set("expensive_key", expensive_operation)
    print(f"Result: {result}")
    
    # Test cache again (should be cached)
    result2 = cache.get_or_set("expensive_key", expensive_operation)
    print(f"Cached result: {result2}")
    
    # Print statistics
    stats = cache.get_stats()
    print(f"Cache stats: {stats}")
