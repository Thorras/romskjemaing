"""
Unit tests for geometry generation functionality.

Tests shape generation with different IFC elements, geometry caching,
and error handling for failed shape generation.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime, timedelta

from ifc_floor_plan_generator.geometry.engine import GeometryEngine
from ifc_floor_plan_generator.models import GeometryConfig, BoundingBox
from ifc_floor_plan_generator.errors.handler import ErrorHandler
from ifc_floor_plan_generator.errors.exceptions import GeometryShapeError


class MockIfcElement:
    """Mock IFC element for testing."""
    def __init__(self, guid: str, ifc_class: str = "IfcWall", has_geometry: bool = True):
        self.GlobalId = guid
        self._ifc_class = ifc_class
        self._has_geometry = has_geometry
    
    def is_a(self):
        return self._ifc_class


class MockShape:
    """Mock TopoDS_Shape for testing without IfcOpenShell dependency."""
    def __init__(self, name: str = "test_shape", is_valid: bool = True):
        self.name = name
        self._is_valid = is_valid
    
    def __eq__(self, other):
        return isinstance(other, MockShape) and self.name == other.name
    
    def __sizeof__(self):
        return 45000  # Mock size for memory estimation


class MockShapeData:
    """Mock shape data returned by IfcOpenShell."""
    def __init__(self, shape: MockShape):
        self.geometry = shape


class TestGeometryEngineInitialization:
    """Test cases for GeometryEngine initialization."""
    
    def test_initialization_with_ifcopenshell_available(self):
        """Test successful initialization when IfcOpenShell is available."""
        config = GeometryConfig(cache_geometry=True)
        error_handler = ErrorHandler()
        
        with patch('ifc_floor_plan_generator.geometry.engine.HAS_IFCOPENSHELL', True):
            with patch('ifc_floor_plan_generator.geometry.engine.ifcopenshell'):
                engine = GeometryEngine(config, error_handler)
        
        assert engine.config == config
        assert engine.error_handler == error_handler
        assert engine._geometry_cache is not None
    
    def test_initialization_without_ifcopenshell(self):
        """Test initialization failure when IfcOpenShell is not available."""
        config = GeometryConfig()
        
        with patch('ifc_floor_plan_generator.geometry.engine.HAS_IFCOPENSHELL', False):
            with pytest.raises(ImportError) as exc_info:
                GeometryEngine(config)
            
            assert "IfcOpenShell is required" in str(exc_info.value)
    
    def test_initialization_with_cache_disabled(self):
        """Test initialization with geometry caching disabled."""
        config = GeometryConfig(cache_geometry=False)
        
        with patch('ifc_floor_plan_generator.geometry.engine.HAS_IFCOPENSHELL', True):
            with patch('ifc_floor_plan_generator.geometry.engine.ifcopenshell'):
                engine = GeometryEngine(config)
        
        assert engine._geometry_cache is None
    
    def test_initialization_with_custom_cache_config(self):
        """Test initialization with custom cache configuration."""
        config = GeometryConfig(cache_geometry=True)
        cache_config = {
            'max_memory_mb': 100.0,
            'max_entries': 500,
            'ttl_hours': 12.0,
            'enable_disk_cache': True
        }
        
        with patch('ifc_floor_plan_generator.geometry.engine.HAS_IFCOPENSHELL', True):
            with patch('ifc_floor_plan_generator.geometry.engine.ifcopenshell'):
                with patch('ifc_floor_plan_generator.geometry.engine.GeometryCache') as mock_cache_class:
                    engine = GeometryEngine(config, cache_config=cache_config)
                    
                    # Verify cache was initialized with correct parameters
                    mock_cache_class.assert_called_once_with(
                        max_memory_mb=100.0,
                        max_entries=500,
                        ttl_hours=12.0,
                        enable_disk_cache=True,
                        disk_cache_dir=None
                    )


class TestGeometryEngineShapeGeneration:
    """Test cases for shape generation with different IFC elements."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = GeometryConfig(
            use_world_coords=True,
            subtract_openings=True,
            sew_shells=True,
            cache_geometry=True
        )
        self.error_handler = ErrorHandler()
        
        with patch('ifc_floor_plan_generator.geometry.engine.HAS_IFCOPENSHELL', True):
            with patch('ifc_floor_plan_generator.geometry.engine.ifcopenshell'):
                self.engine = GeometryEngine(self.config, self.error_handler)
    
    @patch('ifc_floor_plan_generator.geometry.engine.ifcopenshell.geom.create_shape')
    def test_generate_shape_success_wall(self, mock_create_shape):
        """Test successful shape generation for IfcWall element."""
        # Setup
        element = MockIfcElement("wall-guid-123", "IfcWall")
        mock_shape = MockShape("wall_shape")
        mock_create_shape.return_value = MockShapeData(mock_shape)
        
        with patch.object(self.engine, '_is_valid_shape', return_value=True):
            # Execute
            result = self.engine.generate_shape(element)
        
        # Verify
        assert result == mock_shape
        mock_create_shape.assert_called_once_with(self.engine._geometry_settings, element)
    
    @patch('ifc_floor_plan_generator.geometry.engine.ifcopenshell.geom.create_shape')
    def test_generate_shape_success_door(self, mock_create_shape):
        """Test successful shape generation for IfcDoor element."""
        # Setup
        element = MockIfcElement("door-guid-456", "IfcDoor")
        mock_shape = MockShape("door_shape")
        mock_create_shape.return_value = MockShapeData(mock_shape)
        
        with patch.object(self.engine, '_is_valid_shape', return_value=True):
            # Execute
            result = self.engine.generate_shape(element)
        
        # Verify
        assert result == mock_shape
        assert mock_create_shape.called
    
    @patch('ifc_floor_plan_generator.geometry.engine.ifcopenshell.geom.create_shape')
    def test_generate_shape_success_window(self, mock_create_shape):
        """Test successful shape generation for IfcWindow element."""
        # Setup
        element = MockIfcElement("window-guid-789", "IfcWindow")
        mock_shape = MockShape("window_shape")
        mock_create_shape.return_value = MockShapeData(mock_shape)
        
        with patch.object(self.engine, '_is_valid_shape', return_value=True):
            # Execute
            result = self.engine.generate_shape(element)
        
        # Verify
        assert result == mock_shape
        assert mock_create_shape.called
    
    @patch('ifc_floor_plan_generator.geometry.engine.ifcopenshell.geom.create_shape')
    def test_generate_shape_success_slab(self, mock_create_shape):
        """Test successful shape generation for IfcSlab element."""
        # Setup
        element = MockIfcElement("slab-guid-101", "IfcSlab")
        mock_shape = MockShape("slab_shape")
        mock_create_shape.return_value = MockShapeData(mock_shape)
        
        with patch.object(self.engine, '_is_valid_shape', return_value=True):
            # Execute
            result = self.engine.generate_shape(element)
        
        # Verify
        assert result == mock_shape
        assert mock_create_shape.called
    
    @patch('ifc_floor_plan_generator.geometry.engine.ifcopenshell.geom.create_shape')
    def test_generate_shape_success_beam(self, mock_create_shape):
        """Test successful shape generation for IfcBeam element."""
        # Setup
        element = MockIfcElement("beam-guid-202", "IfcBeam")
        mock_shape = MockShape("beam_shape")
        mock_create_shape.return_value = MockShapeData(mock_shape)
        
        with patch.object(self.engine, '_is_valid_shape', return_value=True):
            # Execute
            result = self.engine.generate_shape(element)
        
        # Verify
        assert result == mock_shape
        assert mock_create_shape.called
    
    def test_generate_shape_element_without_guid(self):
        """Test shape generation with element missing GlobalId."""
        # Setup
        element = Mock()
        del element.GlobalId  # Remove GlobalId attribute
        
        # Execute
        result = self.engine.generate_shape(element)
        
        # Verify
        assert result is None
    
    @patch('ifc_floor_plan_generator.geometry.engine.ifcopenshell.geom.create_shape')
    def test_generate_shape_ifcopenshell_returns_none(self, mock_create_shape):
        """Test shape generation when IfcOpenShell returns None."""
        # Setup
        element = MockIfcElement("test-guid", "IfcWall")
        mock_create_shape.return_value = None
        
        # Execute
        result = self.engine.generate_shape(element)
        
        # Verify
        assert result is None
        mock_create_shape.assert_called_once()
    
    @patch('ifc_floor_plan_generator.geometry.engine.ifcopenshell.geom.create_shape')
    def test_generate_shape_invalid_shape(self, mock_create_shape):
        """Test shape generation when generated shape is invalid."""
        # Setup
        element = MockIfcElement("test-guid", "IfcWall")
        mock_shape = MockShape("invalid_shape", is_valid=False)
        mock_create_shape.return_value = MockShapeData(mock_shape)
        
        with patch.object(self.engine, '_is_valid_shape', return_value=False):
            # Execute
            result = self.engine.generate_shape(element)
        
        # Verify
        assert result is None
    
    @patch('ifc_floor_plan_generator.geometry.engine.ifcopenshell.geom.create_shape')
    def test_generate_shape_fallback_shape_data(self, mock_create_shape):
        """Test shape generation with fallback shape data format."""
        # Setup
        element = MockIfcElement("test-guid", "IfcWall")
        mock_shape = MockShape("fallback_shape")
        # Return shape directly (not wrapped in shape data object)
        mock_create_shape.return_value = mock_shape
        
        with patch.object(self.engine, '_is_valid_shape', return_value=True):
            # Execute
            result = self.engine.generate_shape(element)
        
        # Verify
        assert result == mock_shape


class TestGeometryEngineCaching:
    """Test cases for geometry caching functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = GeometryConfig(cache_geometry=True)
        self.error_handler = ErrorHandler()
        
        with patch('ifc_floor_plan_generator.geometry.engine.HAS_IFCOPENSHELL', True):
            with patch('ifc_floor_plan_generator.geometry.engine.ifcopenshell'):
                with patch('ifc_floor_plan_generator.geometry.engine.GeometryCache') as mock_cache_class:
                    mock_cache = Mock()
                    mock_cache_class.return_value = mock_cache
                    self.engine = GeometryEngine(self.config, self.error_handler)
                    # Store reference to mock cache for tests
                    self.engine._geometry_cache = mock_cache
    
    @patch('ifc_floor_plan_generator.geometry.engine.ifcopenshell.geom.create_shape')
    def test_cache_hit_on_second_request(self, mock_create_shape):
        """Test that second request for same element hits cache."""
        # Setup
        element = MockIfcElement("cache-test-guid", "IfcWall")
        mock_shape = MockShape("cached_shape")
        mock_create_shape.return_value = MockShapeData(mock_shape)
        
        with patch.object(self.engine, '_is_valid_shape', return_value=True):
            # First request - should generate and cache
            result1 = self.engine.generate_shape(element)
            
            # Second request - should hit cache
            result2 = self.engine.generate_shape(element)
        
        # Verify
        assert result1 == mock_shape
        assert result2 == mock_shape
        # IfcOpenShell should only be called once
        mock_create_shape.assert_called_once()
    
    def test_cache_stats_tracking(self):
        """Test cache statistics tracking."""
        # Initial stats
        stats = self.engine.get_cache_stats()
        assert stats['cache_enabled'] is True
        assert stats['cached_items'] == 0
        
        # Add some cached items
        with patch.object(self.engine._geometry_cache, 'get_stats') as mock_get_stats:
            mock_stats = Mock()
            mock_stats.cached_items = 5
            mock_stats.hit_rate = 75.0
            mock_stats.total_requests = 20
            mock_stats.cache_hits = 15
            mock_stats.cache_misses = 5
            mock_stats.memory_usage_mb = 25.5
            mock_stats.invalidations = 1
            mock_get_stats.return_value = mock_stats
            
            stats = self.engine.get_cache_stats()
            
            assert stats['cached_items'] == 5
            assert stats['hit_rate_percent'] == 75.0
            assert stats['total_requests'] == 20
            assert stats['cache_hits'] == 15
            assert stats['cache_misses'] == 5
            assert stats['memory_usage_mb'] == 25.5
            assert stats['invalidations'] == 1
    
    def test_cache_disabled_stats(self):
        """Test cache statistics when caching is disabled."""
        config_no_cache = GeometryConfig(cache_geometry=False)
        
        with patch('ifc_floor_plan_generator.geometry.engine.HAS_IFCOPENSHELL', True):
            with patch('ifc_floor_plan_generator.geometry.engine.ifcopenshell'):
                engine_no_cache = GeometryEngine(config_no_cache)
        
        stats = engine_no_cache.get_cache_stats()
        assert stats['cache_enabled'] is False
        assert stats['cached_items'] == 0
        assert stats['cache_type'] == 'disabled'
    
    def test_clear_cache(self):
        """Test cache clearing functionality."""
        with patch.object(self.engine._geometry_cache, 'clear') as mock_clear:
            self.engine.clear_cache()
            mock_clear.assert_called_once()
    
    def test_clear_cache_when_disabled(self):
        """Test cache clearing when cache is disabled."""
        config_no_cache = GeometryConfig(cache_geometry=False)
        
        with patch('ifc_floor_plan_generator.geometry.engine.HAS_IFCOPENSHELL', True):
            with patch('ifc_floor_plan_generator.geometry.engine.ifcopenshell'):
                engine_no_cache = GeometryEngine(config_no_cache)
        
        # Should not raise error
        engine_no_cache.clear_cache()
    
    def test_is_cached_functionality(self):
        """Test checking if geometry is cached."""
        guid = "test-cached-guid"
        
        # Ensure cache is properly initialized
        assert self.engine.config.cache_geometry is True
        assert self.engine._geometry_cache is not None
        
        # Test when cache is enabled and item is cached
        self.engine._geometry_cache.__contains__ = Mock(return_value=True)
        result = self.engine.is_cached(guid)
        assert result is True
        
        # Test when cache is enabled and item is not cached
        self.engine._geometry_cache.__contains__ = Mock(return_value=False)
        result = self.engine.is_cached(guid)
        assert result is False
    
    def test_is_cached_when_disabled(self):
        """Test is_cached when caching is disabled."""
        config_no_cache = GeometryConfig(cache_geometry=False)
        
        with patch('ifc_floor_plan_generator.geometry.engine.HAS_IFCOPENSHELL', True):
            with patch('ifc_floor_plan_generator.geometry.engine.ifcopenshell'):
                engine_no_cache = GeometryEngine(config_no_cache)
        
        assert engine_no_cache.is_cached("any-guid") is False
    
    def test_cleanup_expired_cache(self):
        """Test cleanup of expired cache entries."""
        with patch.object(self.engine._geometry_cache, 'cleanup_expired', return_value=3) as mock_cleanup:
            expired_count = self.engine.cleanup_expired_cache()
            
            assert expired_count == 3
            mock_cleanup.assert_called_once()
    
    def test_cleanup_expired_cache_when_disabled(self):
        """Test cleanup when cache is disabled."""
        config_no_cache = GeometryConfig(cache_geometry=False)
        
        with patch('ifc_floor_plan_generator.geometry.engine.HAS_IFCOPENSHELL', True):
            with patch('ifc_floor_plan_generator.geometry.engine.ifcopenshell'):
                engine_no_cache = GeometryEngine(config_no_cache)
        
        expired_count = engine_no_cache.cleanup_expired_cache()
        assert expired_count == 0
    
    def test_update_cache_configuration(self):
        """Test updating cache configuration."""
        config_dict = {
            'use_world_coords': False,
            'subtract_openings': False,
            'sew_shells': False
        }
        
        with patch.object(self.engine._geometry_cache, 'update_configuration') as mock_update:
            self.engine.update_cache_configuration(config_dict)
            mock_update.assert_called_once_with(config_dict)


class TestGeometryEngineErrorHandling:
    """Test cases for error handling in shape generation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = GeometryConfig(cache_geometry=True)
        self.error_handler = ErrorHandler()
        
        with patch('ifc_floor_plan_generator.geometry.engine.HAS_IFCOPENSHELL', True):
            with patch('ifc_floor_plan_generator.geometry.engine.ifcopenshell'):
                self.engine = GeometryEngine(self.config, self.error_handler)
    
    @patch('ifc_floor_plan_generator.geometry.engine.ifcopenshell.geom.create_shape')
    def test_recoverable_geometry_error(self, mock_create_shape):
        """Test handling of recoverable geometry generation errors."""
        # Setup
        element = MockIfcElement("error-guid", "IfcWall")
        mock_create_shape.side_effect = RuntimeError("Geometry generation failed")
        
        with patch.object(self.error_handler, 'handle_recoverable_error', return_value=True) as mock_handle:
            # Execute
            result = self.engine.generate_shape(element)
        
        # Verify
        assert result is None
        mock_handle.assert_called_once()
    
    @patch('ifc_floor_plan_generator.geometry.engine.ifcopenshell.geom.create_shape')
    def test_critical_geometry_error(self, mock_create_shape):
        """Test handling of critical geometry generation errors."""
        # Setup
        element = MockIfcElement("critical-error-guid", "IfcWall")
        original_error = RuntimeError("Critical geometry error")
        mock_create_shape.side_effect = original_error
        
        with patch.object(self.error_handler, 'handle_recoverable_error', return_value=False):
            # Execute and verify exception is raised
            with pytest.raises(GeometryShapeError) as exc_info:
                self.engine.generate_shape(element)
            
            # Verify exception details
            error = exc_info.value
            assert error.error_code == "GEOMETRY_SHAPE_FAILED"
            assert error.context['element_guid'] == "critical-error-guid"
            assert error.context['ifc_class'] == "IfcWall"
            assert error.context['original_error'] == str(original_error)
    
    @patch('ifc_floor_plan_generator.geometry.engine.ifcopenshell.geom.create_shape')
    def test_various_exception_types(self, mock_create_shape):
        """Test handling of various exception types during shape generation."""
        element = MockIfcElement("exception-test-guid", "IfcWall")
        
        # Test different exception types
        exceptions_to_test = [
            ValueError("Invalid parameter"),
            TypeError("Type error"),
            AttributeError("Attribute error"),
            Exception("Generic exception")
        ]
        
        for original_exception in exceptions_to_test:
            mock_create_shape.side_effect = original_exception
            
            with patch.object(self.error_handler, 'handle_recoverable_error', return_value=True):
                result = self.engine.generate_shape(element)
                assert result is None
    
    def test_shape_validation_error_handling(self):
        """Test error handling in shape validation."""
        # Test with None shape
        assert self.engine._is_valid_shape(None) is False
        
        # Test with valid mock shape
        mock_shape = MockShape("valid_shape")
        result = self.engine._is_valid_shape(mock_shape)
        assert result is True


class TestGeometryEngineBoundingBox:
    """Test cases for bounding box calculation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = GeometryConfig()
        
        with patch('ifc_floor_plan_generator.geometry.engine.HAS_IFCOPENSHELL', True):
            with patch('ifc_floor_plan_generator.geometry.engine.ifcopenshell'):
                self.engine = GeometryEngine(self.config)
    
    def test_get_element_bounds_success(self):
        """Test successful bounding box calculation."""
        # Setup
        mock_shape = MockShape("test_shape")
        
        with patch('ifc_floor_plan_generator.geometry.engine.Bnd_Box') as mock_bnd_box_class, \
             patch('ifc_floor_plan_generator.geometry.engine.BRepBndLib_Add') as mock_brep_add:
            
            mock_bbox = Mock()
            mock_bbox.IsVoid.return_value = False
            mock_bbox.Get.return_value = (0.0, 0.0, 0.0, 10.0, 5.0, 3.0)
            mock_bnd_box_class.return_value = mock_bbox
            
            # Execute
            result = self.engine.get_element_bounds(mock_shape)
            
            # Verify
            assert isinstance(result, BoundingBox)
            assert result.min_x == 0.0
            assert result.min_y == 0.0
            assert result.max_x == 10.0
            assert result.max_y == 5.0
    
    def test_get_element_bounds_none_shape(self):
        """Test bounding box calculation with None shape."""
        result = self.engine.get_element_bounds(None)
        assert result is None
    
    def test_get_element_bounds_void_bbox(self):
        """Test bounding box calculation with void bounding box."""
        # Setup
        mock_shape = MockShape("test_shape")
        
        with patch('ifc_floor_plan_generator.geometry.engine.Bnd_Box') as mock_bnd_box_class, \
             patch('ifc_floor_plan_generator.geometry.engine.BRepBndLib_Add') as mock_brep_add:
            
            mock_bbox = Mock()
            mock_bbox.IsVoid.return_value = True
            mock_bnd_box_class.return_value = mock_bbox
            
            # Execute
            result = self.engine.get_element_bounds(mock_shape)
            
            # Verify
            assert result is None
    
    def test_get_element_bounds_exception(self):
        """Test bounding box calculation with exception."""
        # Setup
        mock_shape = MockShape("test_shape")
        
        with patch('ifc_floor_plan_generator.geometry.engine.BRepBndLib_Add') as mock_brep_add:
            mock_brep_add.side_effect = Exception("Bounding box calculation failed")
            
            # Execute
            result = self.engine.get_element_bounds(mock_shape)
            
            # Verify
            assert result is None


class TestGeometryEngineBatchProcessing:
    """Test cases for batch processing functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = GeometryConfig(cache_geometry=True)
        
        with patch('ifc_floor_plan_generator.geometry.engine.HAS_IFCOPENSHELL', True):
            with patch('ifc_floor_plan_generator.geometry.engine.ifcopenshell'):
                self.engine = GeometryEngine(self.config)
    
    @patch('ifc_floor_plan_generator.geometry.engine.ifcopenshell.geom.create_shape')
    def test_generate_shapes_batch_all_cache_misses(self, mock_create_shape):
        """Test batch processing with all cache misses."""
        # Setup
        elements = [
            MockIfcElement("batch-1", "IfcWall"),
            MockIfcElement("batch-2", "IfcDoor"),
            MockIfcElement("batch-3", "IfcWindow")
        ]
        
        mock_shapes = [MockShape(f"shape_{i}") for i in range(3)]
        mock_create_shape.side_effect = [MockShapeData(shape) for shape in mock_shapes]
        
        with patch.object(self.engine, '_is_valid_shape', return_value=True):
            # Execute
            results = self.engine.generate_shapes_batch(elements)
        
        # Verify
        assert len(results) == 3
        assert results["batch-1"] == mock_shapes[0]
        assert results["batch-2"] == mock_shapes[1]
        assert results["batch-3"] == mock_shapes[2]
        assert mock_create_shape.call_count == 3
    
    @patch('ifc_floor_plan_generator.geometry.engine.ifcopenshell.geom.create_shape')
    def test_generate_shapes_batch_with_cache_hits(self, mock_create_shape):
        """Test batch processing with some cache hits."""
        # Setup
        elements = [
            MockIfcElement("cached-1", "IfcWall"),
            MockIfcElement("cached-2", "IfcDoor")
        ]
        
        # Pre-populate cache for first element
        cached_shape = MockShape("cached_shape")
        new_shape = MockShape("new_shape")
        
        with patch.object(self.engine._geometry_cache, 'get', side_effect=[cached_shape, None]):
            with patch.object(self.engine, '_is_valid_shape', return_value=True):
                with patch.object(self.engine, 'generate_shape', side_effect=[cached_shape, new_shape]):
                    # Execute
                    results = self.engine.generate_shapes_batch(elements)
        
        # Verify
        assert len(results) == 2
        assert results["cached-1"] == cached_shape  # From cache
        assert results["cached-2"] == new_shape  # Newly generated
    
    def test_generate_shapes_batch_elements_without_guid(self):
        """Test batch processing with elements missing GlobalId."""
        # Setup
        elements = [
            MockIfcElement("valid-guid", "IfcWall"),
            Mock()  # Element without GlobalId
        ]
        delattr(elements[1], 'GlobalId')
        
        with patch.object(self.engine, 'generate_shape', return_value=MockShape("test")):
            # Execute
            results = self.engine.generate_shapes_batch(elements)
        
        # Verify - only valid element should be processed
        assert len(results) == 1
        assert "valid-guid" in results
    
    @patch('ifc_floor_plan_generator.geometry.engine.ifcopenshell.geom.create_shape')
    def test_preload_geometry_cache(self, mock_create_shape):
        """Test preloading geometry cache."""
        # Setup
        elements = [
            MockIfcElement("preload-1", "IfcWall"),
            MockIfcElement("preload-2", "IfcSlab")
        ]
        
        mock_shapes = [MockShape(f"preload_shape_{i}") for i in range(2)]
        mock_create_shape.side_effect = [MockShapeData(shape) for shape in mock_shapes]
        
        with patch.object(self.engine, '_is_valid_shape', return_value=True):
            with patch.object(self.engine._geometry_cache, 'preload_shapes', return_value=2) as mock_preload:
                # Execute
                preloaded_count = self.engine.preload_geometry_cache(elements)
        
        # Verify
        assert preloaded_count == 2
        mock_preload.assert_called_once()
    
    def test_preload_geometry_cache_disabled(self):
        """Test preloading when cache is disabled."""
        config_no_cache = GeometryConfig(cache_geometry=False)
        
        with patch('ifc_floor_plan_generator.geometry.engine.HAS_IFCOPENSHELL', True):
            with patch('ifc_floor_plan_generator.geometry.engine.ifcopenshell'):
                engine_no_cache = GeometryEngine(config_no_cache)
        
        elements = [MockIfcElement("test-guid", "IfcWall")]
        preloaded_count = engine_no_cache.preload_geometry_cache(elements)
        
        assert preloaded_count == 0


class TestGeometryEnginePerformanceReporting:
    """Test cases for performance reporting functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = GeometryConfig(cache_geometry=True)
        
        with patch('ifc_floor_plan_generator.geometry.engine.HAS_IFCOPENSHELL', True):
            with patch('ifc_floor_plan_generator.geometry.engine.ifcopenshell'):
                self.engine = GeometryEngine(self.config)
    
    def test_get_cache_efficiency_report_enabled(self):
        """Test cache efficiency report when cache is enabled."""
        # Mock cache stats and efficiency metrics
        mock_basic_stats = {
            'cache_enabled': True,
            'cached_items': 100,
            'hit_rate_percent': 85.0
        }
        
        mock_efficiency_metrics = {
            'hit_rate_percent': 85.0,
            'memory_efficiency': 15.5,
            'cache_utilization': 0.8,
            'eviction_rate': 0.05
        }
        
        with patch.object(self.engine, 'get_cache_stats', return_value=mock_basic_stats):
            with patch.object(self.engine._geometry_cache, 'get_cache_efficiency_metrics', 
                            return_value=mock_efficiency_metrics):
                # Execute
                report = self.engine.get_cache_efficiency_report()
        
        # Verify
        assert report['cache_enabled'] is True
        assert 'basic_stats' in report
        assert 'efficiency_metrics' in report
        assert 'recommendations' in report
        assert isinstance(report['recommendations'], list)
    
    def test_get_cache_efficiency_report_disabled(self):
        """Test cache efficiency report when cache is disabled."""
        config_no_cache = GeometryConfig(cache_geometry=False)
        
        with patch('ifc_floor_plan_generator.geometry.engine.HAS_IFCOPENSHELL', True):
            with patch('ifc_floor_plan_generator.geometry.engine.ifcopenshell'):
                engine_no_cache = GeometryEngine(config_no_cache)
        
        # Execute
        report = engine_no_cache.get_cache_efficiency_report()
        
        # Verify
        assert report['cache_enabled'] is False
        assert 'message' in report
    
    def test_generate_cache_recommendations_low_hit_rate(self):
        """Test cache recommendations for low hit rate."""
        metrics = {
            'hit_rate_percent': 30.0,
            'memory_efficiency': 15.0,
            'cache_utilization': 0.5,
            'eviction_rate': 0.05
        }
        
        recommendations = self.engine._generate_cache_recommendations(metrics)
        
        assert any("Low cache hit rate" in rec for rec in recommendations)
    
    def test_generate_cache_recommendations_high_hit_rate(self):
        """Test cache recommendations for high hit rate."""
        metrics = {
            'hit_rate_percent': 95.0,
            'memory_efficiency': 15.0,
            'cache_utilization': 0.5,
            'eviction_rate': 0.02
        }
        
        recommendations = self.engine._generate_cache_recommendations(metrics)
        
        assert any("Excellent cache hit rate" in rec for rec in recommendations)
    
    def test_generate_cache_recommendations_optimal(self):
        """Test cache recommendations for optimal performance."""
        metrics = {
            'hit_rate_percent': 75.0,
            'memory_efficiency': 15.0,
            'cache_utilization': 0.6,
            'eviction_rate': 0.05
        }
        
        recommendations = self.engine._generate_cache_recommendations(metrics)
        
        assert any("optimal parameters" in rec for rec in recommendations)


if __name__ == "__main__":
    pytest.main([__file__])