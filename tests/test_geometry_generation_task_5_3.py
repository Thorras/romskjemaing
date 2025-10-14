"""
Unit tests for geometry generation functionality - Task 5.3 Implementation.

This test file specifically addresses the requirements for Task 5.3:
- Test shape generation with different IFC elements
- Test geometry caching functionality  
- Test error handling for failed shape generation
- Requirements: 4.1, 4.2, 4.3, 4.4, 8.3
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
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


class TestGeometryGenerationTask53:
    """Test cases for Task 5.3 - Geometry Generation with different IFC elements."""
    
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
    def test_shape_generation_wall_element(self, mock_create_shape):
        """Test shape generation with IfcWall element - Requirement 4.1."""
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
    def test_shape_generation_door_element(self, mock_create_shape):
        """Test shape generation with IfcDoor element - Requirement 4.2."""
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
    def test_shape_generation_slab_element(self, mock_create_shape):
        """Test shape generation with IfcSlab element - Requirement 4.3."""
        # Setup
        element = MockIfcElement("slab-guid-789", "IfcSlab")
        mock_shape = MockShape("slab_shape")
        mock_create_shape.return_value = MockShapeData(mock_shape)
        
        with patch.object(self.engine, '_is_valid_shape', return_value=True):
            # Execute
            result = self.engine.generate_shape(element)
        
        # Verify
        assert result == mock_shape
        assert mock_create_shape.called
    
    @patch('ifc_floor_plan_generator.geometry.engine.ifcopenshell.geom.create_shape')
    def test_geometry_caching_functionality(self, mock_create_shape):
        """Test geometry caching functionality - Requirement 8.3."""
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
        # IfcOpenShell should only be called once due to caching
        mock_create_shape.assert_called_once()
    
    def test_cache_statistics_tracking(self):
        """Test cache statistics tracking - Requirement 8.3."""
        # Get initial stats
        stats = self.engine.get_cache_stats()
        assert stats['cache_enabled'] is True
        assert stats['cached_items'] == 0
        
        # Verify cache type
        assert stats['cache_type'] == 'sophisticated'
    
    @patch('ifc_floor_plan_generator.geometry.engine.ifcopenshell.geom.create_shape')
    def test_error_handling_geometry_failure(self, mock_create_shape):
        """Test error handling for failed shape generation - Requirement 4.4."""
        # Setup
        element = MockIfcElement("error-guid", "IfcWall")
        original_error = RuntimeError("Geometry generation failed")
        mock_create_shape.side_effect = original_error
        
        with patch.object(self.error_handler, 'handle_recoverable_error', return_value=True) as mock_handle:
            # Execute
            result = self.engine.generate_shape(element)
        
        # Verify
        assert result is None
        mock_handle.assert_called_once()
        
        # Verify error context
        call_args = mock_handle.call_args
        assert call_args[0][0] == "GEOMETRY_SHAPE_FAILED"
        context = call_args[0][1]
        assert context['element_guid'] == "error-guid"
        assert context['ifc_class'] == "IfcWall"
    
    @patch('ifc_floor_plan_generator.geometry.engine.ifcopenshell.geom.create_shape')
    def test_error_handling_critical_failure(self, mock_create_shape):
        """Test error handling for critical geometry failures - Requirement 4.4."""
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
    
    @patch('ifc_floor_plan_generator.geometry.engine.ifcopenshell.geom.create_shape')
    def test_batch_processing_with_cache(self, mock_create_shape):
        """Test batch processing with geometry caching."""
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
    
    def test_cache_efficiency_report(self):
        """Test cache efficiency reporting functionality."""
        # Get efficiency report
        report = self.engine.get_cache_efficiency_report()
        
        assert report['cache_enabled'] is True
        assert 'basic_stats' in report
        assert 'efficiency_metrics' in report
        assert 'recommendations' in report
        
        # Verify recommendations are provided
        assert isinstance(report['recommendations'], list)
        assert len(report['recommendations']) > 0


if __name__ == "__main__":
    pytest.main([__file__])