"""
Tests for geometry caching system.

Tests GUID-based caching, memory management, configuration invalidation,
and performance monitoring.
"""

import pytest
import tempfile
import time
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from ifc_floor_plan_generator.geometry.cache import GeometryCache, CacheEntry, CacheStats

# Mock TopoDS_Shape for testing
class MockShape:
    """Mock shape for testing without IfcOpenShell dependency."""
    def __init__(self, name: str = "test_shape"):
        self.name = name
    
    def __eq__(self, other):
        return isinstance(other, MockShape) and self.name == other.name


class TestGeometryCache:
    """Test cases for GeometryCache."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.cache = GeometryCache(
            max_memory_mb=10.0,
            max_entries=100,
            ttl_hours=1.0,
            enable_disk_cache=False
        )
        self.test_guid = "test-guid-123"
        self.test_shape = MockShape("test_shape")
    
    def test_cache_initialization(self):
        """Test cache initialization with different parameters."""
        cache = GeometryCache(
            max_memory_mb=50.0,
            max_entries=500,
            ttl_hours=12.0,
            enable_disk_cache=True
        )
        
        assert cache.max_memory_mb == 50.0
        assert cache.max_entries == 500
        assert cache.ttl == timedelta(hours=12.0)
        assert cache.enable_disk_cache == True
        assert len(cache) == 0
    
    def test_basic_cache_operations(self):
        """Test basic put/get operations."""
        # Initially empty
        assert len(self.cache) == 0
        assert self.cache.get(self.test_guid) is None
        
        # Store shape
        self.cache.put(self.test_guid, self.test_shape)
        assert len(self.cache) == 1
        assert self.test_guid in self.cache
        
        # Retrieve shape
        cached_shape = self.cache.get(self.test_guid)
        assert cached_shape == self.test_shape
        
        # Check statistics
        stats = self.cache.get_stats()
        assert stats.cached_items == 1
        assert stats.total_requests == 2  # One miss, one hit
        assert stats.cache_hits == 1
        assert stats.cache_misses == 1
        assert stats.hit_rate == 50.0
    
    def test_cache_miss_scenarios(self):
        """Test various cache miss scenarios."""
        # Non-existent GUID
        assert self.cache.get("non-existent") is None
        
        # Store and clear
        self.cache.put(self.test_guid, self.test_shape)
        self.cache.clear()
        assert self.cache.get(self.test_guid) is None
        assert len(self.cache) == 0
    
    def test_configuration_invalidation(self):
        """Test cache invalidation when configuration changes."""
        # Store shape with initial config
        config1 = {
            'use_world_coords': True,
            'subtract_openings': True,
            'sew_shells': True
        }
        self.cache.update_configuration(config1)
        self.cache.put(self.test_guid, self.test_shape)
        
        # Verify shape is cached
        assert self.cache.get(self.test_guid) == self.test_shape
        
        # Change configuration
        config2 = {
            'use_world_coords': False,  # Changed
            'subtract_openings': True,
            'sew_shells': True
        }
        self.cache.update_configuration(config2)
        
        # Shape should be invalidated
        assert self.cache.get(self.test_guid) is None
        assert len(self.cache) == 0
        
        # Check invalidation count
        stats = self.cache.get_stats()
        assert stats.invalidations == 1
    
    def test_ttl_expiration(self):
        """Test time-to-live expiration."""
        # Create cache with very short TTL
        short_ttl_cache = GeometryCache(ttl_hours=0.001)  # ~3.6 seconds
        
        # Store shape
        short_ttl_cache.put(self.test_guid, self.test_shape)
        assert short_ttl_cache.get(self.test_guid) == self.test_shape
        
        # Mock time passage
        with patch('ifc_floor_plan_generator.geometry.cache.datetime') as mock_datetime:
            # Set current time to 1 hour in the future
            future_time = datetime.now() + timedelta(hours=1)
            mock_datetime.now.return_value = future_time
            
            # Shape should be expired
            assert short_ttl_cache.get(self.test_guid) is None
    
    def test_max_entries_eviction(self):
        """Test LRU eviction when max entries exceeded."""
        # Create cache with small max entries
        small_cache = GeometryCache(max_entries=3)
        
        # Fill cache to capacity
        shapes = [MockShape(f"shape_{i}") for i in range(3)]
        guids = [f"guid_{i}" for i in range(3)]
        
        for guid, shape in zip(guids, shapes):
            small_cache.put(guid, shape)
        
        assert len(small_cache) == 3
        
        # Add one more - should evict oldest
        small_cache.put("guid_3", MockShape("shape_3"))
        assert len(small_cache) == 3
        
        # First entry should be evicted (LRU)
        assert small_cache.get("guid_0") is None
        assert small_cache.get("guid_1") is not None
        assert small_cache.get("guid_2") is not None
        assert small_cache.get("guid_3") is not None
    
    def test_cleanup_expired(self):
        """Test cleanup of expired entries."""
        # Store multiple shapes
        shapes = [MockShape(f"shape_{i}") for i in range(3)]
        guids = [f"guid_{i}" for i in range(3)]
        
        for guid, shape in zip(guids, shapes):
            self.cache.put(guid, shape)
        
        assert len(self.cache) == 3
        
        # Mock expiration for some entries
        with patch('ifc_floor_plan_generator.geometry.cache.datetime') as mock_datetime:
            future_time = datetime.now() + timedelta(hours=2)
            mock_datetime.now.return_value = future_time
            
            # Cleanup expired entries
            expired_count = self.cache.cleanup_expired()
            assert expired_count == 3  # All should be expired
            assert len(self.cache) == 0
    
    def test_cache_stats_tracking(self):
        """Test comprehensive statistics tracking."""
        # Perform various operations
        self.cache.get("non-existent")  # Miss
        self.cache.put(self.test_guid, self.test_shape)  # Store
        self.cache.get(self.test_guid)  # Hit
        self.cache.get(self.test_guid)  # Hit
        self.cache.get("another-non-existent")  # Miss
        
        stats = self.cache.get_stats()
        assert stats.total_requests == 4
        assert stats.cache_hits == 2
        assert stats.cache_misses == 2
        assert stats.hit_rate == 50.0
        assert stats.cached_items == 1
    
    def test_preload_shapes(self):
        """Test bulk preloading of shapes into cache."""
        # Create test data
        shapes = [MockShape(f"shape_{i}") for i in range(5)]
        guids = [f"guid_{i}" for i in range(5)]
        guid_shape_pairs = list(zip(guids, shapes))
        
        # Preload shapes
        preloaded_count = self.cache.preload_shapes(guid_shape_pairs)
        assert preloaded_count == 5
        assert len(self.cache) == 5
        
        # Verify all shapes are cached
        for guid, expected_shape in guid_shape_pairs:
            cached_shape = self.cache.get(guid)
            assert cached_shape == expected_shape
    
    def test_cache_efficiency_metrics(self):
        """Test cache efficiency metrics calculation."""
        # Add some test data
        for i in range(3):
            guid = f"test_guid_{i}"
            shape = MockShape(f"shape_{i}")
            self.cache.put(guid, shape)
            
            # Simulate different access patterns
            for _ in range(i + 1):
                self.cache.get(guid)
        
        # Get efficiency metrics
        metrics = self.cache.get_cache_efficiency_metrics()
        
        # Verify metrics structure
        expected_keys = [
            'hit_rate_percent', 'memory_efficiency', 'eviction_rate',
            'avg_access_count', 'cache_utilization'
        ]
        for key in expected_keys:
            assert key in metrics
            assert isinstance(metrics[key], (int, float))
        
        # Verify some basic metric values
        assert metrics['cache_utilization'] > 0
        assert metrics['avg_access_count'] > 0
    
    def test_thread_safety_basic(self):
        """Test basic thread safety of cache operations."""
        import threading
        
        results = []
        
        def cache_worker(worker_id: int):
            """Worker function for threading test."""
            guid = f"worker_{worker_id}"
            shape = MockShape(f"shape_{worker_id}")
            
            # Store and retrieve
            self.cache.put(guid, shape)
            retrieved = self.cache.get(guid)
            results.append(retrieved == shape)
        
        # Create and start threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=cache_worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # All operations should succeed
        assert all(results)
        assert len(self.cache) == 5


class TestGeometryCacheWithDisk:
    """Test cases for GeometryCache with disk caching enabled."""
    
    def setup_method(self):
        """Set up test fixtures with temporary directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.cache_dir = Path(self.temp_dir) / "cache"
        
        self.cache = GeometryCache(
            max_memory_mb=10.0,
            max_entries=100,
            ttl_hours=1.0,
            enable_disk_cache=True,
            disk_cache_dir=self.cache_dir
        )
        
        self.test_guid = "test-guid-123"
        self.test_shape = MockShape("test_shape")
    
    def teardown_method(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_disk_cache_initialization(self):
        """Test disk cache directory creation."""
        assert self.cache_dir.exists()
        assert self.cache_dir.is_dir()
    
    @patch('ifc_floor_plan_generator.geometry.cache.pickle')
    def test_disk_cache_operations(self, mock_pickle):
        """Test disk cache save/load operations."""
        # Mock pickle operations
        mock_pickle.dump = Mock()
        mock_pickle.load = Mock(return_value=CacheEntry(
            shape=self.test_shape,
            timestamp=datetime.now(),
            config_hash="test_hash"
        ))
        
        # Store shape (should save to disk)
        self.cache.put(self.test_guid, self.test_shape)
        
        # Verify pickle.dump was called
        assert mock_pickle.dump.called
        
        # Clear memory cache
        self.cache._cache.clear()
        
        # Mock file existence
        with patch.object(Path, 'exists', return_value=True):
            with patch('builtins.open', create=True):
                # Retrieve should load from disk
                retrieved = self.cache.get(self.test_guid)
                assert mock_pickle.load.called


class TestCacheEntry:
    """Test cases for CacheEntry dataclass."""
    
    def test_cache_entry_creation(self):
        """Test CacheEntry creation and properties."""
        shape = MockShape("test")
        timestamp = datetime.now()
        
        entry = CacheEntry(
            shape=shape,
            timestamp=timestamp,
            config_hash="test_hash"
        )
        
        assert entry.shape == shape
        assert entry.timestamp == timestamp
        assert entry.access_count == 0
        assert entry.last_accessed == timestamp
        assert entry.config_hash == "test_hash"
    
    def test_cache_entry_post_init(self):
        """Test CacheEntry post-initialization logic."""
        shape = MockShape("test")
        timestamp = datetime.now()
        
        # Without last_accessed
        entry = CacheEntry(shape=shape, timestamp=timestamp)
        assert entry.last_accessed == timestamp
        
        # With explicit last_accessed
        last_accessed = timestamp + timedelta(minutes=5)
        entry = CacheEntry(
            shape=shape,
            timestamp=timestamp,
            last_accessed=last_accessed
        )
        assert entry.last_accessed == last_accessed


class TestCacheStats:
    """Test cases for CacheStats dataclass."""
    
    def test_cache_stats_creation(self):
        """Test CacheStats creation and default values."""
        stats = CacheStats()
        
        assert stats.total_requests == 0
        assert stats.cache_hits == 0
        assert stats.cache_misses == 0
        assert stats.cached_items == 0
        assert stats.memory_usage_mb == 0.0
        assert stats.invalidations == 0
        assert stats.hit_rate == 0.0
    
    def test_hit_rate_calculation(self):
        """Test hit rate calculation."""
        stats = CacheStats(total_requests=100, cache_hits=75)
        assert stats.hit_rate == 75.0
        
        stats = CacheStats(total_requests=0, cache_hits=0)
        assert stats.hit_rate == 0.0
        
        stats = CacheStats(total_requests=50, cache_hits=50)
        assert stats.hit_rate == 100.0


if __name__ == "__main__":
    pytest.main([__file__])