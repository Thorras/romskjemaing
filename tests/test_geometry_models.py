"""
Unit tests for geometric data models used in 2D floor plan visualization.
"""

import pytest
import math
from ifc_room_schedule.visualization.geometry_models import (
    Point2D, Polygon2D, FloorLevel, FloorGeometry, FloorPlanState
)


class TestPoint2D:
    """Test Point2D class functionality."""
    
    def test_point_creation(self):
        """Test basic point creation."""
        point = Point2D(1.0, 2.0)
        assert point.x == 1.0
        assert point.y == 2.0
    
    def test_point_validation(self):
        """Test point validation."""
        # Valid points
        Point2D(0, 0)
        Point2D(-1.5, 2.7)
        Point2D(1e6, -1e6)
        
        # Invalid points
        with pytest.raises(ValueError):
            Point2D("invalid", 1.0)
        
        with pytest.raises(ValueError):
            Point2D(float('nan'), 1.0)
        
        with pytest.raises(ValueError):
            Point2D(1.0, float('inf'))
    
    def test_distance_calculation(self):
        """Test distance calculation between points."""
        p1 = Point2D(0, 0)
        p2 = Point2D(3, 4)
        
        distance = p1.distance_to(p2)
        assert abs(distance - 5.0) < 1e-10
    
    def test_point_translation(self):
        """Test point translation."""
        point = Point2D(1, 2)
        translated = point.translate(3, 4)
        
        assert translated.x == 4
        assert translated.y == 6
        assert point.x == 1  # Original unchanged
        assert point.y == 2
    
    def test_point_scaling(self):
        """Test point scaling."""
        point = Point2D(2, 4)
        scaled = point.scale(2.0)
        
        assert scaled.x == 4
        assert scaled.y == 8
        
        # Scale around custom origin
        origin = Point2D(1, 1)
        scaled_custom = point.scale(2.0, origin)
        assert scaled_custom.x == 3  # 1 + (2-1)*2
        assert scaled_custom.y == 7  # 1 + (4-1)*2
    
    def test_to_tuple(self):
        """Test tuple conversion."""
        point = Point2D(1.5, 2.7)
        assert point.to_tuple() == (1.5, 2.7)


class TestPolygon2D:
    """Test Polygon2D class functionality."""
    
    def test_polygon_creation(self):
        """Test basic polygon creation."""
        points = [Point2D(0, 0), Point2D(1, 0), Point2D(1, 1), Point2D(0, 1)]
        polygon = Polygon2D(points, "test_guid", "Test Room")
        
        assert len(polygon.points) == 5  # Auto-closed
        assert polygon.space_guid == "test_guid"
        assert polygon.space_name == "Test Room"
    
    def test_polygon_validation(self):
        """Test polygon validation."""
        # Valid polygon
        points = [Point2D(0, 0), Point2D(1, 0), Point2D(1, 1)]
        Polygon2D(points, "guid", "name")
        
        # Invalid polygons
        with pytest.raises(ValueError):
            Polygon2D([], "guid", "name")  # Empty
        
        with pytest.raises(ValueError):
            Polygon2D([Point2D(0, 0)], "guid", "name")  # Too few points
        
        with pytest.raises(ValueError):
            Polygon2D([Point2D(0, 0), Point2D(1, 0)], "", "name")  # No GUID
    
    def test_bounds_calculation(self):
        """Test bounding box calculation."""
        points = [Point2D(1, 2), Point2D(4, 2), Point2D(4, 5), Point2D(1, 5)]
        polygon = Polygon2D(points, "guid", "name")
        
        bounds = polygon.get_bounds()
        assert bounds == (1, 2, 4, 5)  # min_x, min_y, max_x, max_y
    
    def test_area_calculation(self):
        """Test polygon area calculation."""
        # Unit square
        points = [Point2D(0, 0), Point2D(1, 0), Point2D(1, 1), Point2D(0, 1)]
        polygon = Polygon2D(points, "guid", "name")
        
        area = polygon.get_area()
        assert abs(area - 1.0) < 1e-10
        
        # Rectangle 3x2
        points = [Point2D(0, 0), Point2D(3, 0), Point2D(3, 2), Point2D(0, 2)]
        polygon = Polygon2D(points, "guid", "name")
        
        area = polygon.get_area()
        assert abs(area - 6.0) < 1e-10
    
    def test_centroid_calculation(self):
        """Test polygon centroid calculation."""
        # Unit square centered at origin
        points = [Point2D(-0.5, -0.5), Point2D(0.5, -0.5), Point2D(0.5, 0.5), Point2D(-0.5, 0.5)]
        polygon = Polygon2D(points, "guid", "name")
        
        centroid = polygon.get_centroid()
        assert abs(centroid.x) < 1e-10
        assert abs(centroid.y) < 1e-10
    
    def test_point_in_polygon(self):
        """Test point-in-polygon detection."""
        # Unit square
        points = [Point2D(0, 0), Point2D(1, 0), Point2D(1, 1), Point2D(0, 1)]
        polygon = Polygon2D(points, "guid", "name")
        
        # Points inside
        assert polygon.contains_point(Point2D(0.5, 0.5))
        assert polygon.contains_point(Point2D(0.1, 0.1))
        
        # Points outside
        assert not polygon.contains_point(Point2D(-0.1, 0.5))
        assert not polygon.contains_point(Point2D(1.1, 0.5))
        assert not polygon.contains_point(Point2D(0.5, -0.1))
        assert not polygon.contains_point(Point2D(0.5, 1.1))
    
    def test_polygon_translation(self):
        """Test polygon translation."""
        points = [Point2D(0, 0), Point2D(1, 0), Point2D(1, 1), Point2D(0, 1)]
        polygon = Polygon2D(points, "guid", "name")
        
        translated = polygon.translate(2, 3)
        
        assert translated.points[0].x == 2
        assert translated.points[0].y == 3
        assert translated.space_guid == "guid"
        
        # Original unchanged
        assert polygon.points[0].x == 0
        assert polygon.points[0].y == 0


class TestFloorLevel:
    """Test FloorLevel class functionality."""
    
    def test_floor_level_creation(self):
        """Test basic floor level creation."""
        floor = FloorLevel("level_1", "Ground Floor", 0.0, ["space1", "space2"])
        
        assert floor.id == "level_1"
        assert floor.name == "Ground Floor"
        assert floor.elevation == 0.0
        assert len(floor.spaces) == 2
    
    def test_floor_level_validation(self):
        """Test floor level validation."""
        # Valid floor
        FloorLevel("id", "name", 0.0)
        
        # Invalid floors
        with pytest.raises(ValueError):
            FloorLevel("", "name", 0.0)  # Empty ID
        
        with pytest.raises(ValueError):
            FloorLevel("id", "name", float('nan'))  # Invalid elevation
    
    def test_space_management(self):
        """Test space addition and removal."""
        floor = FloorLevel("id", "name", 0.0)
        
        # Add spaces
        floor.add_space("space1")
        floor.add_space("space2")
        assert floor.get_space_count() == 2
        
        # Add duplicate (should be ignored)
        floor.add_space("space1")
        assert floor.get_space_count() == 2
        
        # Remove space
        floor.remove_space("space1")
        assert floor.get_space_count() == 1
        assert "space1" not in floor.spaces


class TestFloorGeometry:
    """Test FloorGeometry class functionality."""
    
    def test_floor_geometry_creation(self):
        """Test basic floor geometry creation."""
        floor_level = FloorLevel("id", "name", 0.0)
        points = [Point2D(0, 0), Point2D(1, 0), Point2D(1, 1), Point2D(0, 1)]
        polygon = Polygon2D(points, "space1", "Room 1")
        
        geometry = FloorGeometry(floor_level, [polygon])
        
        assert geometry.level == floor_level
        assert len(geometry.room_polygons) == 1
        assert geometry.get_room_count() == 1
    
    def test_bounds_calculation(self):
        """Test automatic bounds calculation."""
        floor_level = FloorLevel("id", "name", 0.0)
        
        # Two rooms
        points1 = [Point2D(0, 0), Point2D(2, 0), Point2D(2, 2), Point2D(0, 2)]
        points2 = [Point2D(3, 1), Point2D(5, 1), Point2D(5, 3), Point2D(3, 3)]
        
        polygon1 = Polygon2D(points1, "space1", "Room 1")
        polygon2 = Polygon2D(points2, "space2", "Room 2")
        
        geometry = FloorGeometry(floor_level, [polygon1, polygon2])
        
        # Bounds should encompass both rooms
        assert geometry.bounds == (0, 0, 5, 3)
        assert geometry.get_bounds_width() == 5
        assert geometry.get_bounds_height() == 3
    
    def test_room_lookup(self):
        """Test room lookup by GUID."""
        floor_level = FloorLevel("id", "name", 0.0)
        points = [Point2D(0, 0), Point2D(1, 0), Point2D(1, 1), Point2D(0, 1)]
        polygon = Polygon2D(points, "space1", "Room 1")
        
        geometry = FloorGeometry(floor_level, [polygon])
        
        # Find existing room
        found = geometry.get_room_by_guid("space1")
        assert found is not None
        assert found.space_guid == "space1"
        
        # Non-existent room
        not_found = geometry.get_room_by_guid("nonexistent")
        assert not_found is None
    
    def test_point_room_detection(self):
        """Test finding room at specific point."""
        floor_level = FloorLevel("id", "name", 0.0)
        points = [Point2D(0, 0), Point2D(2, 0), Point2D(2, 2), Point2D(0, 2)]
        polygon = Polygon2D(points, "space1", "Room 1")
        
        geometry = FloorGeometry(floor_level, [polygon])
        
        # Point inside room
        room = geometry.find_room_at_point(Point2D(1, 1))
        assert room is not None
        assert room.space_guid == "space1"
        
        # Point outside room
        no_room = geometry.find_room_at_point(Point2D(5, 5))
        assert no_room is None


class TestFloorPlanState:
    """Test FloorPlanState class functionality."""
    
    def test_state_creation(self):
        """Test basic state creation."""
        state = FloorPlanState()
        
        assert state.current_floor_id is None
        assert len(state.selected_rooms) == 0
        assert state.zoom_level == 1.0
    
    def test_floor_management(self):
        """Test floor addition and selection."""
        state = FloorPlanState()
        
        # Add floor
        floor_level = FloorLevel("floor1", "Ground Floor", 0.0)
        points = [Point2D(0, 0), Point2D(1, 0), Point2D(1, 1), Point2D(0, 1)]
        polygon = Polygon2D(points, "space1", "Room 1")
        geometry = FloorGeometry(floor_level, [polygon])
        
        state.add_floor(geometry)
        
        assert len(state.available_floors) == 1
        assert "floor1" in state.geometry_data
        
        # Set current floor
        success = state.set_current_floor("floor1")
        assert success
        assert state.current_floor_id == "floor1"
        
        # Try invalid floor
        success = state.set_current_floor("invalid")
        assert not success
    
    def test_room_selection(self):
        """Test room selection management."""
        state = FloorPlanState()
        
        # Add rooms to selection
        state.add_room_to_selection("room1")
        state.add_room_to_selection("room2")
        assert state.get_selected_room_count() == 2
        assert state.is_room_selected("room1")
        
        # Remove room
        state.remove_room_from_selection("room1")
        assert state.get_selected_room_count() == 1
        assert not state.is_room_selected("room1")
        
        # Clear all
        state.clear_selection()
        assert state.get_selected_room_count() == 0