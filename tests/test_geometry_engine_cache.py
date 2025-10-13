"""
Tests for geometry engine caching functionality.

Tests the integration between GeometryEngine and GeometryCache.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from ifc_floor_plan_generator.geometry.engine import GeometryEngine
from ifc_floor_plan_generator.models import GeometryConfig
from ifc_floor_plan_generator.errors.handler import ErrorHandler


class MockIfcElement:
    """Mock IFC element for testing."""
    def __init__(self, guid: str, ifc_class: str = "IfcWall"):
        self.GlobalId = guid
        self._ifc_class = ifc_class
    
    def is_a(self):
        return self._ifc_class


class MockShape:
    """Mock shape for testing without IfcOpenShell dependency."""
    def __init__(self, name: str = "test_shape"):
        self.name = name
    
    def __eq__(self, other):
        return isinstance(other, MockShape) and self.name == other.name


class TestGeometryEngineCache:
    """Test cases for GeometryEngine caching functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = GeometryConfig(
            use_world_coords=True,
            subtract_openings=True,
            sew_shells=True,
            cache_geometry=True
        )
        self.error_handler = ErrorHandler()
        
        # Mock IfcOpenShell availability
        with patch('ifc_floor_plan_generator.geometry.engine.HAS_IFCOPENSHELL', True):
            with patch('ifc_floor_plan_generator.geometry.engine.ifcopenshell'):
                self.engine = GeometryEngine(
                    config=self.config,
                    error_handler=self.error_handler,
                    cache_config={'max_memory_mb': 10.0, 'max_entries': 100}
                )
    
    def test_cache_initialization(self):
        """Test that cache is properly initialized when enabled."""
        assert self.engine._geometry_cache is not None
        assert self.engine.config.cache_geometry is True
        
        # Test cache stats
        stats = self.engine.get_cache_stats()
        assert stats['cache_enabled'] is True
        assert stats['cached_items'] == 0
    
    def test_cache_disabled_initialization(self):
        """Test engine initialization with caching disabled."""
        config_no_cache = GeometryConfig(cache_geometry=False)
        
        with patch('ifc_floor_plan_generator.geometry.engine.HAS_IFCOPENSHELL', True):
            with patch('ifc_floor_plan_generator.geometry.engine.ifcopenshell'):
                engine_no_cache = GeometryEngine(config=config_no_cache)
        
        assert engine_no_cache._geometry_cache is None
        
        stats = engine_no_cache.get_cache_stats()
        assert stats['cache_enabled'] is False
    
    @patch('ifc_floor_plan_generator.geometry.engine.ifcopenshell.geom.create_shape')
    def test_batch_processing_with_cache(self, mock_create_shape):
        """Test batch processing with cache hits and misses."""
        # Mock shape creation
        mock_shape = MockShape("test_shape")
        mock_create_shape.return_value = MagicMock()
        mock_create_shape.return_value.geometry = mock_shape
        
        # Create test elements
        elements = [
            MockIfcElement("guid_1", "IfcWall"),
            MockIfcElement("guid_2", "IfcDoor"),
            MockIfcElement("guid_3", "IfcWindow")
        ]
        
        # First batch - all cache misses
        with patch.object(self.engine, '_is_valid_shape', return_value=True):
            results1 = self.engine.generate_shapes_batch(elements)
        
        assert len(results1) == 3
        assert all(shape is not None for shape in results1.values())
        
        # Second batch - should have cache hits
        with patch.object(self.engine, '_is_valid_shape', return_value=True):
            results2 = self.engine.generate_shapes_batch(elements)
        
        assert len(results2) == 3
        assert results1.keys() == results2.keys()
    
    @patch('ifc_floor_plan_generator.geometry.engine.ifcopenshell.geom.create_shape')
    def test_preload_geometry_cache(self, mock_create_shape):
        """Test preloading geometry cache."""
        # Mock shape creation
        mock_shape = MockShape("preload_shape")
        mock_create_shape.return_value = MagicMock()
        mock_create_shape.return_value.geometry = mock_shape
        
        # Create test elements
        elements = [
            MockIfcElement("preload_1", "IfcWall"),
            MockIfcElement("preload_2", "IfcSlab")
        ]
        
        # Preload cache
        with patch.object(self.engine, '_is_valid_shape', return_value=True):
            preloaded_count = self.engine.preload_geometry_cache(elements)
        
        assert preloaded_count == 2
        
        # Verify shapes are cached
        assert self.engine.is_cached("preload_1")
        assert self.engine.is_cached("preload_2")
    
    def test_cache_efficiency_report(self):
        """Test cache efficiency reporting."""
        # Get efficiency report
        report = self.engine.get_cache_efficiency_report()
        
        assert report['cache_enabled'] is True
        assert 'basic_stats' in report
        assert 'efficiency_metrics' in report
        assert 'recommendations' in report
        
        # Verify recommendations are provided
        assert isinstance(report['recommendations'], list)
        assert len(report['recommendations']) > 0
    
    def test_cache_efficiency_report_disabled(self):
        """Test efficiency report when cache is disabled."""
        config_no_cache = GeometryConfig(cache_geometry=False)
        
        with patch('ifc_floor_plan_generator.geometry.engine.HAS_IFCOPENSHELL', True):
            with patch('ifc_floor_plan_generator.geometry.engine.ifcopenshell'):
                engine_no_cache = GeometryEngine(config=config_no_cache)
        
        report = engine_no_cache.get_cache_efficiency_report()
        
        assert report['cache_enabled'] is False
        assert 'message' in report
    
    def test_cache_configuration_update(self):
        """Test cache configuration updates and invalidation."""
        # Initial configuration
        config_dict = {
            'use_world_coords': True,
            'subtract_openings': True,
            'sew_shells': True
        }
        
        self.engine.update_cache_configuration(config_dict)
        
        # Add some cached data
        with patch.object(self.engine._geometry_cache, 'put') as mock_put:
            mock_put.return_value = None
            # Simulate adding to cache
            
        # Change configuration - should trigger invalidation
        new_config_dict = {
            'use_world_coords': False,  # Changed
            'subtract_openings': True,
            'sew_shells': True
        }
        
        with patch.object(self.engine._geometry_cache, 'update_configuration') as mock_update:
            self.engine.update_cache_configuration(new_config_dict)
            mock_update.assert_called_once_with(new_config_dict)


if __name__ == "__main__":
    pytest.main([__file__])