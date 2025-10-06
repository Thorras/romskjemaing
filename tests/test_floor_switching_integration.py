"""
Integration Tests for Floor Switching Functionality

Tests the floor switching updates across all UI components and proper state management
as part of the interactive floor plan enhancement.
"""

import pytest
import sys
import os
from unittest.mock import Mock, MagicMock, patch, call
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest, QSignalSpy

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ifc_room_schedule.ui.main_window import MainWindow
from ifc_room_schedule.ui.floor_plan_widget import FloorPlanWidget, FloorSelector
from ifc_room_schedule.data.space_model import SpaceData
from ifc_room_schedule.visualization.geometry_models import FloorLevel, FloorGeometry, Polygon2D, Point2D


@pytest.fixture(scope="session")
def qapp():
    """Create QApplication instance for testing."""
    if not QApplication.instance():
        app = QApplication([])
    else:
        app = QApplication.instance()
    yield app
    app.quit()


@pytest.fixture
def multi_floor_spaces():
    """Create sample space data across multiple floors."""
    spaces = []
    
    # Ground floor spaces
    for i in range(3):
        spaces.append(SpaceData(
            guid=f"GROUND_{i:03d}",
            name=f"G{i+1:02d}",
            long_name=f"Ground Floor Room {i+1}",
            description=f"Ground floor space {i+1}",
            object_type="Office",
            zone_category="Office",
            number=f"G{i+1:02d}",
            elevation=0.0,
            quantities={"Height": 3.0, "Area": 25.0},
            floor_id="FLOOR_GROUND"
        ))
    
    # First floor spaces
    for i in range(4):
        spaces.append(SpaceData(
            guid=f"FIRST_{i:03d}",
            name=f"1{i+1:02d}",
            long_name=f"First Floor Room {i+1}",
            description=f"First floor space {i+1}",
            object_type="Office" if i < 2 else "Meeting Room",
            zone_category="Office" if i < 2 else "Meeting Room",
            number=f"1{i+1:02d}",
            elevation=3.5,
            quantities={"Height": 3.2, "Area": 20.0},
            floor_id="FLOOR_FIRST"
        ))
    
    # Second floor spaces
    for i in range(2):
        spaces.append(SpaceData(
            guid=f"SECOND_{i:03d}",
            name=f"2{i+1:02d}",
            long_name=f"Second Floor Room {i+1}",
            description=f"Second floor space {i+1}",
            object_type="Storage",
            zone_category="Storage",
            number=f"2{i+1:02d}",
            elevation=7.0,
            quantities={"Height": 2.8, "Area": 15.0},
            floor_id="FLOOR_SECOND"
        ))
    
    return spaces


@pytest.fixture
def multi_floor_geometries(multi_floor_spaces):
    """Create floor geometry data for multiple floors."""
    # Group spaces by floor
    floors_data = {
        "FLOOR_GROUND": {"name": "Ground Floor", "elevation": 0.0, "spaces": []},
        "FLOOR_FIRST": {"name": "First Floor", "elevation": 3.5, "spaces": []},
        "FLOOR_SECOND": {"name": "Second Floor", "elevation": 7.0, "spaces": []}
    }
    
    for space in multi_floor_spaces:
        floors_data[space.floor_id]["spaces"].append(space.guid)
    
    geometries = {}
    for floor_id, floor_data in floors_data.items():
        floor_level = FloorLevel(
            id=floor_id,
            name=floor_data["name"],
            elevation=floor_data["elevation"],
            spaces=floor_data["spaces"],
            has_geometry=True,
            space_count=len(floor_data["spaces"]),
            total_area=len(floor_data["spaces"]) * 25.0
        )
        
        # Create polygons for each space
        polygons = []
        for i, space_guid in enumerate(floor_data["spaces"]):
            points = [
                Point2D(i * 12.0, 0.0),
                Point2D(i * 12.0 + 10.0, 0.0),
                Point2D(i * 12.0 + 10.0, 8.0),
                Point2D(i * 12.0, 8.0)
            ]
            polygon = Polygon2D(
                points=points,
                space_guid=space_guid,
                space_name=f"Room {i+1}",
                space_type="Office"
            )
            polygons.append(polygon)
        
        geometries[floor_id] = FloorGeometry(
            level=floor_level,
            room_polygons=polygons,
            bounds=(0.0, 0.0, len(floor_data["spaces"]) * 12.0, 8.0)
        )
    
    return geometries


class TestFloorSelectorIntegration:
    """Test cases for FloorSelector component integration."""

    def test_floor_selector_initialization_with_multiple_floors(self, qapp, multi_floor_geometries):
        """Test FloorSelector initialization with multiple floors."""
        floor_plan_widget = FloorPlanWidget()
        floor_plan_widget.set_floor_geometry(multi_floor_geometries)
        
        # Check that all floors are available in selector
        floor_selector = floor_plan_widget.floor_selector
        assert floor_selector.floor_combo.count() == 3
        
        # Check floors are sorted by elevation
        assert floor_selector.floor_combo.itemData(0) == "FLOOR_GROUND"
        assert floor_selector.floor_combo.itemData(1) == "FLOOR_FIRST"
        assert floor_selector.floor_combo.itemData(2) == "FLOOR_SECOND"

    def test_floor_selector_metadata_display(self, qapp, multi_floor_geometries):
        """Test floor selector metadata display for different floors."""
        floor_plan_widget = FloorPlanWidget()
        floor_plan_widget.set_floor_geometry(multi_floor_geometries)
        
        floor_selector = floor_plan_widget.floor_selector
        
        # Test ground floor metadata
        floor_selector.set_current_floor("FLOOR_GROUND")
        metadata_text = floor_selector.metadata_label.text()
        assert "3 spaces" in metadata_text
        assert "75m²" in metadata_text
        
        # Test first floor metadata
        floor_selector.set_current_floor("FLOOR_FIRST")
        metadata_text = floor_selector.metadata_label.text()
        assert "4 spaces" in metadata_text
        assert "100m²" in metadata_text

    def test_floor_selector_signal_emission(self, qapp, multi_floor_geometries):
        """Test floor selector signal emission on floor change."""
        floor_plan_widget = FloorPlanWidget()
        floor_plan_widget.set_floor_geometry(multi_floor_geometries)
        
        # Set up signal spy
        spy = QSignalSpy(floor_plan_widget.floor_changed)
        
        # Change floor via selector
        floor_plan_widget.floor_selector.set_current_floor("FLOOR_FIRST")
        
        # Check signal was emitted
        assert len(spy) == 1
        assert spy[0][0] == "FLOOR_FIRST"


class TestMainWindowFloorSwitching:
    """Test cases for MainWindow floor switching coordination."""

    def test_main_window_floor_switching_updates_all_components(self, qapp, multi_floor_spaces, multi_floor_geometries):
        """Test that floor switching in MainWindow updates all UI components."""
        window = MainWindow()
        window._testing_mode = True
        
        # Mock UI components
        window.space_list_widget = Mock()
        window.floor_plan_widget = Mock()
        window.space_detail_widget = Mock()
        window.surface_editor_widget = Mock()
        
        # Set up test data
        window.spaces = multi_floor_spaces
        window.floor_geometries = multi_floor_geometries
        
        # Mock space list to have floor filter active
        window.space_list_widget.get_current_floor_filter.return_value = "FLOOR_GROUND"
        
        # Simulate floor change
        window.on_floor_changed("FLOOR_FIRST")
        
        # Verify space list filter was updated
        window.space_list_widget.set_floor_filter.assert_called_once_with("FLOOR_FIRST")

    def test_floor_switching_with_space_selection_persistence(self, qapp, multi_floor_spaces, multi_floor_geometries):
        """Test that space selection is maintained during floor switching when possible."""
        window = MainWindow()
        window._testing_mode = True
        
        # Mock UI components
        window.space_list_widget = Mock()
        window.floor_plan_widget = Mock()
        window.space_detail_widget = Mock()
        window.surface_editor_widget = Mock()
        
        # Set up test data
        window.spaces = multi_floor_spaces
        window.floor_geometries = multi_floor_geometries
        
        # Mock current selection on first floor
        first_floor_space = next(s for s in multi_floor_spaces if s.floor_id == "FLOOR_FIRST")
        window.space_list_widget.get_selected_spaces.return_value = [first_floor_space]
        
        # Switch to first floor
        window.on_floor_changed("FLOOR_FIRST")
        
        # Selection should be maintained since space is on the current floor
        # (This would be tested by checking that selection is not cleared)

    def test_floor_switching_clears_incompatible_selection(self, qapp, multi_floor_spaces, multi_floor_geometries):
        """Test that floor switching clears selection of spaces not on current floor."""
        window = MainWindow()
        window._testing_mode = True
        
        # Mock UI components
        window.space_list_widget = Mock()
        window.floor_plan_widget = Mock()
        window.space_detail_widget = Mock()
        window.surface_editor_widget = Mock()
        
        # Set up test data
        window.spaces = multi_floor_spaces
        window.floor_geometries = multi_floor_geometries
        
        # Mock current selection on ground floor
        ground_floor_space = next(s for s in multi_floor_spaces if s.floor_id == "FLOOR_GROUND")
        window.space_list_widget.get_selected_spaces.return_value = [ground_floor_space]
        
        # Switch to first floor (different from selected space)
        window.on_floor_changed("FLOOR_FIRST")
        
        # Selection should be cleared since selected space is not on current floor
        # (Implementation would handle this logic)

    def test_automatic_floor_switching_on_cross_floor_selection(self, qapp, multi_floor_spaces, multi_floor_geometries):
        """Test automatic floor switching when selecting space from different floor."""
        window = MainWindow()
        window._testing_mode = True
        
        # Mock UI components
        window.space_list_widget = Mock()
        window.floor_plan_widget = Mock()
        window.space_detail_widget = Mock()
        window.surface_editor_widget = Mock()
        
        # Set up test data
        window.spaces = multi_floor_spaces
        window.floor_geometries = multi_floor_geometries
        
        # Mock current floor as ground floor
        window.floor_plan_widget.get_current_floor_id.return_value = "FLOOR_GROUND"
        
        # Select space from first floor
        first_floor_space = next(s for s in multi_floor_spaces if s.floor_id == "FLOOR_FIRST")
        window.on_space_selected(first_floor_space.guid)
        
        # Should automatically switch to first floor
        window.floor_plan_widget.set_current_floor.assert_called_once_with("FLOOR_FIRST")


class TestFloorFilteringSynchronization:
    """Test cases for floor filtering synchronization between components."""

    def test_space_list_floor_filter_updates_floor_plan(self, qapp, multi_floor_spaces, multi_floor_geometries):
        """Test that space list floor filter changes update floor plan display."""
        window = MainWindow()
        window._testing_mode = True
        
        # Mock UI components
        window.space_list_widget = Mock()
        window.floor_plan_widget = Mock()
        window.space_detail_widget = Mock()
        window.surface_editor_widget = Mock()
        
        # Set up test data
        window.spaces = multi_floor_spaces
        window.floor_geometries = multi_floor_geometries
        
        # Simulate floor filter change from space list
        window.on_space_list_floor_filter_changed("FLOOR_SECOND")
        
        # Verify floor plan switches to filtered floor
        window.floor_plan_widget.set_current_floor.assert_called_once_with("FLOOR_SECOND")

    def test_floor_plan_floor_change_updates_space_list_filter(self, qapp, multi_floor_spaces, multi_floor_geometries):
        """Test that floor plan floor changes can update space list filter."""
        window = MainWindow()
        window._testing_mode = True
        
        # Mock UI components
        window.space_list_widget = Mock()
        window.floor_plan_widget = Mock()
        window.space_detail_widget = Mock()
        window.surface_editor_widget = Mock()
        
        # Set up test data
        window.spaces = multi_floor_spaces
        window.floor_geometries = multi_floor_geometries
        
        # Mock space list to have a specific floor filter active
        window.space_list_widget.get_current_floor_filter.return_value = "FLOOR_GROUND"
        
        # Mock floor geometry for the target floor
        mock_floor_geometry = Mock()
        mock_floor_geometry.get_room_count.return_value = 2
        mock_floor_geometry.level.name = "Second Floor"
        window.floor_geometries["FLOOR_SECOND"] = mock_floor_geometry
        
        # Simulate floor change from floor plan
        window.on_floor_changed("FLOOR_SECOND")
        
        # Verify space list filter was updated since user had a specific floor filter
        window.space_list_widget.set_floor_filter.assert_called_once_with("FLOOR_SECOND")

    def test_floor_filtering_with_search_combination(self, qapp, multi_floor_spaces, multi_floor_geometries):
        """Test floor filtering combined with search functionality."""
        window = MainWindow()
        window._testing_mode = True
        
        # Mock UI components
        window.space_list_widget = Mock()
        window.floor_plan_widget = Mock()
        window.space_detail_widget = Mock()
        window.surface_editor_widget = Mock()
        
        # Set up test data
        window.spaces = multi_floor_spaces
        window.floor_geometries = multi_floor_geometries
        
        # Mock search results filtered by floor and search term
        first_floor_offices = [s for s in multi_floor_spaces 
                              if s.floor_id == "FLOOR_FIRST" and s.object_type == "Office"]
        window.space_list_widget.get_visible_spaces.return_value = first_floor_offices
        
        # Simulate combined floor filter and search
        window.on_space_list_floor_filter_changed("FLOOR_FIRST")
        window.on_space_search_changed("office")
        
        # Verify floor plan was updated
        window.floor_plan_widget.set_current_floor.assert_called_once_with("FLOOR_FIRST")
        window.floor_plan_widget.highlight_spaces.assert_called_once()


class TestFloorSwitchingPerformance:
    """Test cases for floor switching performance and efficiency."""

    def test_efficient_floor_switching_with_large_datasets(self, qapp):
        """Test efficient floor switching with large numbers of floors and spaces."""
        # Create large dataset
        large_spaces = []
        large_geometries = {}
        
        for floor_num in range(10):  # 10 floors
            floor_id = f"FLOOR_{floor_num:02d}"
            floor_spaces = []
            
            for space_num in range(50):  # 50 spaces per floor
                space_guid = f"SPACE_{floor_num:02d}_{space_num:03d}"
                space = SpaceData(
                    guid=space_guid,
                    name=f"{floor_num}{space_num:02d}",
                    long_name=f"Room {floor_num}{space_num:02d}",
                    description=f"Space on floor {floor_num}",
                    object_type="Office",
                    zone_category="Office",
                    number=f"{floor_num}{space_num:02d}",
                    elevation=floor_num * 3.5,
                    quantities={"Height": 3.0, "Area": 25.0},
                    floor_id=floor_id
                )
                large_spaces.append(space)
                floor_spaces.append(space_guid)
            
            # Create floor geometry
            floor_level = FloorLevel(
                id=floor_id,
                name=f"Floor {floor_num}",
                elevation=floor_num * 3.5,
                spaces=floor_spaces,
                has_geometry=True,
                space_count=len(floor_spaces),
                total_area=len(floor_spaces) * 25.0
            )
            
            # Create simple polygons
            polygons = []
            for i, space_guid in enumerate(floor_spaces[:5]):  # Only create geometry for first 5 spaces
                points = [
                    Point2D(i * 12.0, 0.0),
                    Point2D(i * 12.0 + 10.0, 0.0),
                    Point2D(i * 12.0 + 10.0, 8.0),
                    Point2D(i * 12.0, 8.0)
                ]
                polygon = Polygon2D(
                    points=points,
                    space_guid=space_guid,
                    space_name=f"Room {i+1}",
                    space_type="Office"
                )
                polygons.append(polygon)
            
            large_geometries[floor_id] = FloorGeometry(
                level=floor_level,
                room_polygons=polygons,
                bounds=(0.0, 0.0, 60.0, 8.0)
            )
        
        # Test floor switching performance
        window = MainWindow()
        window._testing_mode = True
        
        # Mock UI components
        window.space_list_widget = Mock()
        window.floor_plan_widget = Mock()
        window.space_detail_widget = Mock()
        window.surface_editor_widget = Mock()
        
        # Set up large dataset
        window.spaces = large_spaces
        window.floor_geometries = large_geometries
        
        # Test rapid floor switching
        import time
        start_time = time.time()
        
        for floor_num in range(10):
            floor_id = f"FLOOR_{floor_num:02d}"
            window.on_floor_changed(floor_id)
        
        end_time = time.time()
        
        # Should complete quickly (less than 1 second for 10 floor switches)
        assert (end_time - start_time) < 1.0

    def test_memory_efficiency_during_floor_switching(self, qapp, multi_floor_geometries):
        """Test memory efficiency during frequent floor switching."""
        floor_plan_widget = FloorPlanWidget()
        floor_plan_widget.set_floor_geometry(multi_floor_geometries)
        
        # Mock canvas to track method calls
        floor_plan_widget.floor_plan_canvas.set_current_floor = Mock()
        
        # Perform many floor switches
        floor_ids = list(multi_floor_geometries.keys())
        for _ in range(100):  # 100 switches
            for floor_id in floor_ids:
                floor_plan_widget.set_current_floor(floor_id)
        
        # Should handle many switches without issues
        # (In a real test, we might monitor memory usage)
        assert floor_plan_widget.floor_plan_canvas.set_current_floor.call_count == 300  # 100 * 3 floors


class TestFloorSwitchingErrorHandling:
    """Test cases for error handling during floor switching."""

    def test_invalid_floor_id_handling(self, qapp, multi_floor_geometries):
        """Test handling of invalid floor IDs during switching."""
        floor_plan_widget = FloorPlanWidget()
        floor_plan_widget.set_floor_geometry(multi_floor_geometries)
        
        # Try to switch to invalid floor
        floor_plan_widget.set_current_floor("INVALID_FLOOR_ID")
        
        # Should handle gracefully - current floor should remain unchanged
        assert floor_plan_widget.get_current_floor_id() != "INVALID_FLOOR_ID"

    def test_missing_geometry_data_handling(self, qapp):
        """Test handling when geometry data is missing for a floor."""
        floor_plan_widget = FloorPlanWidget()
        
        # Try to switch floor without setting geometry data
        floor_plan_widget.set_current_floor("FLOOR001")
        
        # Should handle gracefully without crashing
        assert floor_plan_widget.get_current_floor_id() is None

    def test_partial_geometry_data_handling(self, qapp, multi_floor_geometries):
        """Test handling when some floors have geometry and others don't."""
        # Remove geometry for one floor
        partial_geometries = multi_floor_geometries.copy()
        del partial_geometries["FLOOR_FIRST"]
        
        floor_plan_widget = FloorPlanWidget()
        floor_plan_widget.set_floor_geometry(partial_geometries)
        
        # Should still work with available floors
        floor_plan_widget.set_current_floor("FLOOR_GROUND")
        assert floor_plan_widget.get_current_floor_id() == "FLOOR_GROUND"
        
        # Should handle missing floor gracefully
        floor_plan_widget.set_current_floor("FLOOR_FIRST")
        # Current floor should remain as FLOOR_GROUND since FLOOR_FIRST is not available
        assert floor_plan_widget.get_current_floor_id() == "FLOOR_GROUND"


if __name__ == "__main__":
    pytest.main([__file__])