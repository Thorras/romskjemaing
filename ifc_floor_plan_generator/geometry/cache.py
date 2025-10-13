"""
Geometry caching system for IFC Floor Plan Generator.

Provides GUID-based geometry caching with memory-efficient storage,
cache invalidation, and performance monitoring.
"""

import logging
import hashlib
import pickle
import weakref
from typing import Any, Optional, Dict, Set, Tuple, List
from pathlib import Path
from threading import RLock
from dataclasses import dataclass
from datetime import datetime, timedelta

# IfcOpenShell imports with error handling
try:
    from OCC.Core import TopoDS_Shape
    HAS_IFCOPENSHELL = True
except ImportError:
    HAS_IFCOPENSHELL = False
    # Create placeholder class for type hints when IfcOpenShell is not available
    class TopoDS_Shape:
        pass


@dataclass
class CacheEntry:
    """Represents a cached geometry entry with metadata."""
    shape: TopoDS_Shape
    timestamp: datetime
    access_count: int = 0
    last_accessed: datetime = None
    config_hash: str = ""
    
    def __post_init__(self):
        if self.last_accessed is None:
            self.last_accessed = self.timestamp


@dataclass
class CacheStats:
    """Statistics about cache performance."""
    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    cached_items: int = 0
    memory_usage_mb: float = 0.0
    invalidations: int = 0
    
    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate as percentage."""
        if self.total_requests == 0:
            return 0.0
        return (self.cache_hits / self.total_requests) * 100.0


class GeometryCache:
    """
    GUID-based geometry cache with memory-efficient storage and invalidation logic.
    
    Features:
    - Thread-safe operations
    - Memory usage monitoring
    - LRU-style eviction
    - Configuration-based invalidation
    - Performance statistics
    """
    
    def __init__(self, 
                 max_memory_mb: float = 500.0,
                 max_entries: int = 10000,
                 ttl_hours: float = 24.0,
                 enable_disk_cache: bool = False,
                 disk_cache_dir: Optional[Path] = None):
        """
        Initialize geometry cache.
        
        Args:
            max_memory_mb: Maximum memory usage in MB before eviction
            max_entries: Maximum number of cached entries
            ttl_hours: Time-to-live for cache entries in hours
            enable_disk_cache: Whether to enable disk-based caching
            disk_cache_dir: Directory for disk cache (if enabled)
        """
        self.max_memory_mb = max_memory_mb
        self.max_entries = max_entries
        self.ttl = timedelta(hours=ttl_hours)
        self.enable_disk_cache = enable_disk_cache
        self.disk_cache_dir = disk_cache_dir
        
        # Thread-safe cache storage
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = RLock()
        
        # Statistics tracking
        self._stats = CacheStats()
        
        # Configuration tracking for invalidation
        self._current_config_hash: str = ""
        self._invalidated_guids: Set[str] = set()
        
        # Logger
        self.logger = logging.getLogger(__name__)
        
        # Initialize disk cache if enabled
        if self.enable_disk_cache:
            self._init_disk_cache()
        
        self.logger.info(f"GeometryCache initialized: max_memory={max_memory_mb}MB, "
                        f"max_entries={max_entries}, ttl={ttl_hours}h, "
                        f"disk_cache={enable_disk_cache}")
    
    def _init_disk_cache(self) -> None:
        """Initialize disk cache directory."""
        if self.disk_cache_dir is None:
            self.disk_cache_dir = Path.cwd() / ".cache" / "geometry"
        
        try:
            self.disk_cache_dir.mkdir(parents=True, exist_ok=True)
            self.logger.debug(f"Disk cache directory: {self.disk_cache_dir}")
        except Exception as e:
            self.logger.warning(f"Failed to create disk cache directory: {e}")
            self.enable_disk_cache = False
    
    def _calculate_config_hash(self, config_dict: Dict[str, Any]) -> str:
        """
        Calculate hash of configuration that affects geometry generation.
        
        Args:
            config_dict: Configuration dictionary
            
        Returns:
            str: Hash string representing the configuration
        """
        # Extract only geometry-relevant configuration
        relevant_config = {
            'use_world_coords': config_dict.get('use_world_coords', True),
            'subtract_openings': config_dict.get('subtract_openings', True),
            'sew_shells': config_dict.get('sew_shells', True),
            'unit_scale_to_m': config_dict.get('unit_scale_to_m'),
            'slice_tol': config_dict.get('slice_tol', 1e-6),
        }
        
        # Create deterministic hash
        config_str = str(sorted(relevant_config.items()))
        return hashlib.md5(config_str.encode()).hexdigest()
    
    def update_configuration(self, config_dict: Dict[str, Any]) -> None:
        """
        Update configuration and invalidate cache if necessary.
        
        Args:
            config_dict: New configuration dictionary
        """
        new_config_hash = self._calculate_config_hash(config_dict)
        
        with self._lock:
            if new_config_hash != self._current_config_hash:
                self.logger.info("Configuration changed, invalidating geometry cache")
                self._invalidate_all()
                self._current_config_hash = new_config_hash
                self._stats.invalidations += 1
    
    def get(self, guid: str) -> Optional[TopoDS_Shape]:
        """
        Retrieve cached geometry by GUID.
        
        Args:
            guid: Element GUID to look up
            
        Returns:
            TopoDS_Shape or None: Cached shape if found and valid, None otherwise
        """
        with self._lock:
            self._stats.total_requests += 1
            
            # Check if GUID was invalidated
            if guid in self._invalidated_guids:
                self._stats.cache_misses += 1
                return None
            
            # Check memory cache
            entry = self._cache.get(guid)
            if entry is None:
                # Try disk cache if enabled
                if self.enable_disk_cache:
                    entry = self._load_from_disk(guid)
                    if entry is not None:
                        # Move back to memory cache
                        self._cache[guid] = entry
            
            if entry is None:
                self._stats.cache_misses += 1
                return None
            
            # Check if entry is expired
            if self._is_expired(entry):
                self._remove_entry(guid)
                self._stats.cache_misses += 1
                return None
            
            # Check if entry is from old configuration
            if entry.config_hash != self._current_config_hash:
                self._remove_entry(guid)
                self._invalidated_guids.add(guid)
                self._stats.cache_misses += 1
                return None
            
            # Update access statistics
            entry.access_count += 1
            entry.last_accessed = datetime.now()
            
            self._stats.cache_hits += 1
            self.logger.debug(f"Cache hit for {guid}")
            return entry.shape
    
    def put(self, guid: str, shape: TopoDS_Shape) -> None:
        """
        Store geometry in cache.
        
        Args:
            guid: Element GUID to use as key
            shape: Geometry shape to cache
        """
        if shape is None:
            return
        
        with self._lock:
            # Remove from invalidated set if present
            self._invalidated_guids.discard(guid)
            
            # Create cache entry
            entry = CacheEntry(
                shape=shape,
                timestamp=datetime.now(),
                config_hash=self._current_config_hash
            )
            
            # Store in memory cache
            self._cache[guid] = entry
            
            # Store in disk cache if enabled
            if self.enable_disk_cache:
                self._save_to_disk(guid, entry)
            
            # Update statistics
            self._stats.cached_items = len(self._cache)
            
            # Check if eviction is needed
            self._maybe_evict()
            
            self.logger.debug(f"Cached geometry for {guid}")
    
    def _is_expired(self, entry: CacheEntry) -> bool:
        """Check if a cache entry is expired."""
        return datetime.now() - entry.timestamp > self.ttl
    
    def _remove_entry(self, guid: str) -> None:
        """Remove entry from cache."""
        if guid in self._cache:
            del self._cache[guid]
            self._stats.cached_items = len(self._cache)
        
        # Remove from disk cache if enabled
        if self.enable_disk_cache:
            self._remove_from_disk(guid)
    
    def _maybe_evict(self) -> None:
        """Evict entries if cache limits are exceeded."""
        # Check entry count limit
        if len(self._cache) > self.max_entries:
            self._evict_lru_entries(len(self._cache) - self.max_entries)
        
        # Check memory limit
        memory_usage = self._estimate_memory_usage()
        if memory_usage > self.max_memory_mb:
            # Evict 20% of entries to provide some headroom
            entries_to_evict = max(1, len(self._cache) // 5)
            self._evict_lru_entries(entries_to_evict)
    
    def _evict_lru_entries(self, count: int) -> None:
        """Evict least recently used entries."""
        if count <= 0 or not self._cache:
            return
        
        # Sort by last accessed time (oldest first)
        sorted_entries = sorted(
            self._cache.items(),
            key=lambda x: x[1].last_accessed
        )
        
        # Remove oldest entries
        for i in range(min(count, len(sorted_entries))):
            guid = sorted_entries[i][0]
            self._remove_entry(guid)
            self.logger.debug(f"Evicted cache entry for {guid}")
    
    def _estimate_memory_usage(self) -> float:
        """Estimate memory usage of cache in MB."""
        if not self._cache:
            return 0.0
        
        # More accurate memory estimation based on actual shape data
        total_bytes = 0
        
        try:
            # Sample a few entries to get average size
            sample_size = min(10, len(self._cache))
            if sample_size > 0:
                sample_entries = list(self._cache.values())[:sample_size]
                
                # Estimate size per entry (including shape data and metadata)
                avg_entry_size = 0
                for entry in sample_entries:
                    # Base size for entry metadata
                    entry_size = 1000  # Base overhead
                    
                    # Estimate shape size (rough approximation)
                    if hasattr(entry.shape, '__sizeof__'):
                        entry_size += entry.shape.__sizeof__()
                    else:
                        # Fallback estimate for complex shapes
                        entry_size += 45000  # Conservative estimate
                    
                    avg_entry_size += entry_size
                
                avg_entry_size = avg_entry_size / sample_size
                total_bytes = avg_entry_size * len(self._cache)
            else:
                # Fallback to conservative estimate
                total_bytes = len(self._cache) * 50000
                
        except Exception as e:
            self.logger.debug(f"Memory estimation failed, using fallback: {e}")
            # Fallback to conservative estimate
            total_bytes = len(self._cache) * 50000
        
        return total_bytes / (1024 * 1024)  # Convert to MB
    
    def _invalidate_all(self) -> None:
        """Invalidate all cached entries."""
        self._cache.clear()
        self._invalidated_guids.clear()
        self._stats.cached_items = 0
        
        # Clear disk cache if enabled
        if self.enable_disk_cache:
            self._clear_disk_cache()
    
    def _load_from_disk(self, guid: str) -> Optional[CacheEntry]:
        """Load cache entry from disk."""
        if not self.enable_disk_cache:
            return None
        
        try:
            cache_file = self.disk_cache_dir / f"{guid}.cache"
            if not cache_file.exists():
                return None
            
            with open(cache_file, 'rb') as f:
                entry = pickle.load(f)
                
            # Validate entry
            if self._is_expired(entry) or entry.config_hash != self._current_config_hash:
                cache_file.unlink(missing_ok=True)
                return None
            
            return entry
            
        except Exception as e:
            self.logger.debug(f"Failed to load cache entry from disk for {guid}: {e}")
            return None
    
    def _save_to_disk(self, guid: str, entry: CacheEntry) -> None:
        """Save cache entry to disk."""
        if not self.enable_disk_cache:
            return
        
        try:
            cache_file = self.disk_cache_dir / f"{guid}.cache"
            with open(cache_file, 'wb') as f:
                pickle.dump(entry, f)
                
        except Exception as e:
            self.logger.debug(f"Failed to save cache entry to disk for {guid}: {e}")
    
    def _remove_from_disk(self, guid: str) -> None:
        """Remove cache entry from disk."""
        if not self.enable_disk_cache:
            return
        
        try:
            cache_file = self.disk_cache_dir / f"{guid}.cache"
            cache_file.unlink(missing_ok=True)
        except Exception as e:
            self.logger.debug(f"Failed to remove cache entry from disk for {guid}: {e}")
    
    def _clear_disk_cache(self) -> None:
        """Clear all disk cache files."""
        if not self.enable_disk_cache or not self.disk_cache_dir.exists():
            return
        
        try:
            for cache_file in self.disk_cache_dir.glob("*.cache"):
                cache_file.unlink(missing_ok=True)
        except Exception as e:
            self.logger.warning(f"Failed to clear disk cache: {e}")
    
    def clear(self) -> None:
        """Clear all cached entries."""
        with self._lock:
            self._invalidate_all()
            self.logger.info("Geometry cache cleared")
    
    def get_stats(self) -> CacheStats:
        """Get cache performance statistics."""
        with self._lock:
            # Update current memory usage estimate
            self._stats.memory_usage_mb = self._estimate_memory_usage()
            self._stats.cached_items = len(self._cache)
            return self._stats
    
    def cleanup_expired(self) -> int:
        """Remove expired entries and return count of removed entries."""
        with self._lock:
            expired_guids = []
            
            for guid, entry in self._cache.items():
                if self._is_expired(entry):
                    expired_guids.append(guid)
            
            for guid in expired_guids:
                self._remove_entry(guid)
            
            if expired_guids:
                self.logger.info(f"Cleaned up {len(expired_guids)} expired cache entries")
            
            return len(expired_guids)
    
    def __len__(self) -> int:
        """Return number of cached entries."""
        return len(self._cache)
    
    def __contains__(self, guid: str) -> bool:
        """Check if GUID is in cache."""
        with self._lock:
            return guid in self._cache and guid not in self._invalidated_guids
    
    def preload_shapes(self, guid_shape_pairs: List[Tuple[str, TopoDS_Shape]]) -> int:
        """
        Preload multiple shapes into cache for performance optimization.
        
        Args:
            guid_shape_pairs: List of (GUID, shape) tuples to preload
            
        Returns:
            int: Number of shapes successfully preloaded
        """
        preloaded_count = 0
        
        with self._lock:
            for guid, shape in guid_shape_pairs:
                if shape is not None and guid not in self._invalidated_guids:
                    try:
                        # Create cache entry
                        entry = CacheEntry(
                            shape=shape,
                            timestamp=datetime.now(),
                            config_hash=self._current_config_hash
                        )
                        
                        # Store in memory cache
                        self._cache[guid] = entry
                        preloaded_count += 1
                        
                        # Store in disk cache if enabled
                        if self.enable_disk_cache:
                            self._save_to_disk(guid, entry)
                            
                    except Exception as e:
                        self.logger.debug(f"Failed to preload shape for {guid}: {e}")
            
            # Update statistics
            self._stats.cached_items = len(self._cache)
            
            # Check if eviction is needed after bulk loading
            self._maybe_evict()
        
        if preloaded_count > 0:
            self.logger.info(f"Preloaded {preloaded_count} shapes into cache")
        
        return preloaded_count
    
    def get_cache_efficiency_metrics(self) -> Dict[str, float]:
        """
        Get detailed cache efficiency metrics for performance monitoring.
        
        Returns:
            Dict with efficiency metrics
        """
        with self._lock:
            stats = self.get_stats()
            
            # Calculate additional efficiency metrics
            metrics = {
                'hit_rate_percent': stats.hit_rate,
                'memory_efficiency': 0.0,
                'eviction_rate': 0.0,
                'avg_access_count': 0.0,
                'cache_utilization': 0.0
            }
            
            if len(self._cache) > 0:
                # Memory efficiency (cached items per MB)
                if stats.memory_usage_mb > 0:
                    metrics['memory_efficiency'] = stats.cached_items / stats.memory_usage_mb
                
                # Cache utilization (current items / max items)
                metrics['cache_utilization'] = len(self._cache) / self.max_entries
                
                # Average access count
                total_access = sum(entry.access_count for entry in self._cache.values())
                metrics['avg_access_count'] = total_access / len(self._cache)
            
            # Eviction rate (approximation based on invalidations)
            if stats.total_requests > 0:
                metrics['eviction_rate'] = stats.invalidations / stats.total_requests
            
            return metrics