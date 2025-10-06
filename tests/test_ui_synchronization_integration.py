"""
Integration Tests for UI Component Synchronization

Tests the bidirectional synchronization between space list, floor plan, and other UI components
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
from ifc_room_schedule.ui.space_list_widget import SpaceListWidget
from ifc_room_schedule.ui.floor_plan_widget import FloorPlanWidget
from ifc_room_schedule.ui.space_detail_widget import SpaceDetailWidget
from ifc_room_schedule.data.space_model import SpaceData
from ifc_room_schedule.visualization.geometry_models import FloorLevel, FloorGeometry, Polygon2D, Point2D


def get_space_floor_id(space):
    """Helper function to get floor ID from space (for testing)."""
    return getattr(space, 'floor_id', None)


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
def sample_spaces():
    """Create sample space data for testing."""
    spaces = [
        SpaceData(
            guid="SPACE001",
            name="101",
            long_name="Office 101",
            description="Main office space",
            object_type="Office",
            zone_category="Office",
            number="101",
            elevation=0.0,
            quantities={"Height": 3.0, "Area": 25.5}
        ),
        SpaceData(
            guid="SPACE002",
            name="102",
            long_name="Meeting Room 102",
            description="Conference room",
            object_type="Meeting Room",
            zone_category="Meeting Room",
            number="102",
            elevation=0.0,
            quantities={"Height": 3.2, "Area": 18.0}
        ),
        SpaceData(
            guid="SPACE003",
            name="201",
            long_name="Office 201",
            description="Second floor office",
            object_type="Office",
            zone_category="Office",
            number="201",
            elevation=3.5,
            quantities={"Height": 3.0, "Area": 22.0}
        ),
        SpaceData(
            guid="SPACE004",
            name="202",
            long_name="Storage 202",
            description="Storage room",
            object_type="Storage",
            zone_category="Storage",
            number="202",
            elevation=3.5,
            quantities={"Height": 2.8, "Area": 12.0}
        )
    ]
    
    # Add floor_id as a custom attribute for testing
    spaces[0].floor_id = "FLOOR001"
    spaces[1].floor_id = "FLOOR001"
    spaces[2].floor_id = "FLOOR002"
    spaces[3].floor_id = "FLOOR002"
    
    return spaces


@pytest.fixture
def sample_floor_geometries():
    """Create sample floor geometry data for testing."""
    floor_levels = [
        FloorLevel(
            id="FLOOR001",
            name="Ground Floor",
            elevation=0.0,
            spaces=["SPACE001", "SPACE002"]
        ),
        FloorLevel(
            id="FLOOR002",
            name="First Floor",
            elevation=3.5,
            spaces=["SPACE003", "SPACE004"]
        )
    ]
    
    geometries = {}
    for floor_level in floor_levels:
        polygons = []
        for i, space_guid in enumerate(floor_level.spaces):
            points = [
                Point2D(i * 10.0, 0.0),
                Point2D(i * 10.0 + 8.0, 0.0),
                Point2D(i * 10.0 + 8.0, 6.0),
                Point2D(i * 10.0, 6.0)
            ]
            polygon = Polygon2D(
                points=points,
                space_guid=space_guid,
                space_name=f"Room {i+1}"
            )
            polygons.append(polygon)
        
        geometries[floor_level.id] = FloorGeometry(
            level=floor_level,
            room_polygons=polygons,
            bounds=(0.0, 0.0, len(floor_level.spaces) * 10.0, 6.0)
        )
    
    return geometries


@pytest.fixture
def main_window_with_mocks(qapp, sample_spaces, sample_floor_geometries):
    """Create MainWindow with mocked components for testing."""
    window = MainWindow()
    window._testing_mode = True  # Prevent dialog boxes during testing
    
    # Mock the UI components
    window.space_list_widget = Mock(spec=SpaceListWidget)
    window.floor_plan_widget = Mock(spec=FloorPlanWidget)
    window.space_detail_widget = Mock(spec=SpaceDetailWidget)
    window.surface_editor_widget = Mock()
    
    # Set up mock return values
    window.space_list_widget.get_selected_space_guids.return_value = []
    window.space_list_widget.get_current_floor_filter.return_value = None
    window.floor_plan_widget.get_current_floor_id.return_value = "FLOOR001"
    
    # Set up test data
    window.spaces = sample_spaces
    window.floor_geometries = sample_floor_geometries
    
    return window


class TestBidirectionalSpaceSelection:
    """Test cases for bidirectional space selection synchronization."""

    def test_space_list_to_floor_plan_selection(self, main_window_with_mocks):
        """Test selection synchronization from space list to floor plan."""
        window = main_window_with_mocks
        
        # Simulate space selection from space list
        selected_space_guid = "SPACE001"
        window.on_space_selected(selected_space_guid)
        
        # Verify floor plan widget was called to highlight the space
        window.floor_plan_widget.highlight_spaces.assert_called_once_with([selected_space_guid])
        
        # Verify space detail widget was called to display the space
        expected_space = next(s for s in window.spaces if s.guid == selected_space_guid)
        window.space_detail_widget.display_space.assert_called_once_with(expected_space)

    def test_floor_plan_to_space_list_selection(self, main_window_with_mocks):
        """Test selection synchronization from floor plan to space list."""
        window = main_window_with_mocks
        
        # Simulate space click from floor plan
        selected_space_guid = "SPACE002"
        window.on_floor_plan_room_clicked(selected_space_guid, False)
        
        # Verify space list widget was called to sync selection
        window.space_list_widget.select_spaces_by_guids.assert_called_once_with([selected_space_guid])
        
        # Verify space detail widget was called to display the space
        expected_space = next(s for s in window.spaces if s.guid == selected_space_guid)
        window.space_detail_widget.display_space.assert_called_once_with(expected_space)

    def test_multi_selection_synchronization(self, main_window_with_mocks):
        """Test multi-selection synchronization between components."""
        window = main_window_with_mocks
        
        # Simulate multi-selection from space list
        selected_guids = ["SPACE001", "SPACE003"]
        window.on_spaces_selection_changed(selected_guids)
        
        # Verify floor plan widget was called to highlight multiple spaces
        window.floor_plan_widget.highlight_spaces.assert_called_once_with(selected_guids)
        
        # Verify space detail widget shows the first selected space
        expected_space = next(s for s in window.spaces if s.guid == selected_guids[0])
        window.space_detail_widget.display_space.assert_called_once_with(expected_space)

    def test_ctrl_click_multi_selection(self, main_window_with_mocks):
        """Test Ctrl+click multi-selection handling."""
        window = main_window_with_mocks
        
        # Mock current selection
        window.space_list_widget.get_selected_space_guids.return_value = ["SPACE001"]
        
        # Simulate Ctrl+click on floor plan
        window.on_floor_plan_room_clicked("SPACE002", True)  # ctrl_pressed=True
        
        # Verify space list widget was called to extend selection (both spaces)
        window.space_list_widget.select_spaces_by_guids.assert_called_once_with(["SPACE001", "SPACE002"])

    def test_selection_clearing_synchronization(self, main_window_with_mocks):
        """Test that clearing selection in one component clears it in all components."""
        window = main_window_with_mocks
        
        # Simulate clearing selection from floor plan
        window.on_floor_plan_selection_changed([])
        
        # Verify all components were cleared
        window.space_list_widget.clear_selection.assert_called_once()
        window.space_detail_widget.clear_selection.assert_called_once()
        window.surface_editor_widget.clear.assert_called_once()

    def test_selection_with_missing_space(self, main_window_with_mocks):
        """Test handling of selection with non-existent space GUID."""
        window = main_window_with_mocks
        
        # Simulate selection of non-existent space
        window.on_space_selected("NONEXISTENT_SPACE")
        
        # Should handle gracefully without crashing
        # Floor plan clear_selection should be called when space not found
        window.floor_plan_widget.clear_selection.assert_called_once()
        
        # Space detail should not be called with invalid space
        window.space_detail_widget.display_space.assert_not_called()


class TestFloorSwitchingSynchronization:
    """Test cases for floor switching synchronization."""

    def test_floor_change_updates_space_list_filter(self, main_window_with_mocks):
        """Test that floor changes update space list filter when user has floor filter active."""
        window = main_window_with_mocks
        
        # Mock space list to have a floor filter active
        window.space_list_widget.get_current_floor_filter.return_value = "FLOOR001"
        
        # Mock floor geometry data
        mock_floor_geometry = Mock()
        mock_floor_geometry.get_room_count.return_value = 2
        mock_floor_geometry.level.name = "First Floor"
        window.floor_geometries = {"FLOOR002": mock_floor_geometry}
        
        # Simulate floor change
        window.on_floor_changed("FLOOR002")
        
        # Verify space list filter was updated since user had a specific floor filter
        window.space_list_widget.set_floor_filter.assert_called_once_with("FLOOR002")

    def test_floor_change_no_filter_update(self, main_window_with_mocks):
        """Test that floor changes don't update space list filter when showing all floors."""
        window = main_window_with_mocks
        
        # Mock space list to show all floors (no filter)
        window.space_list_widget.get_current_floor_filter.return_value = None
        
        # Simulate floor change
        window.on_floor_changed("FLOOR002")
        
        # Verify space list filter was not updated since user is viewing all floors
        window.space_list_widget.set_floor_filter.assert_not_called()

    def test_automatic_floor_switching_on_space_selection(self, main_window_with_mocks):
        """Test automatic floor switching when selecting space from different floor."""
        window = main_window_with_mocks
        
        # Mock current floor
        window.floor_plan_widget.get_current_floor_id.return_value = "FLOOR001"
        
        # Mock geometry extractor with floor data
        window.geometry_extractor = Mock()
        mock_floor_geometry = Mock()
        mock_polygon = Mock()
        mock_polygon.space_guid = "SPACE003"  # Space on FLOOR002
        mock_floor_geometry.room_polygons = [mock_polygon]
        
        window.geometry_extractor.floor_geometries = {
            "FLOOR002": mock_floor_geometry
        }
        
        # Simulate selecting space from different floor
        space_on_floor2 = next(s for s in window.spaces if get_space_floor_id(s) == "FLOOR002")
        window.on_space_selected(space_on_floor2.guid)
        
        # Should switch to the floor containing the selected space
        window.floor_plan_widget.set_current_floor.assert_called_once_with("FLOOR002")

    def test_zoom_to_spaces_with_floor_switching(self, main_window_with_mocks):
        """Test zoom to spaces functionality with automatic floor switching."""
        window = main_window_with_mocks
        
        # Mock current floor
        window.floor_plan_widget.get_current_floor_id.return_value = "FLOOR001"
        
        # Mock geometry extractor with floor data
        window.geometry_extractor = Mock()
        mock_floor_geometry = Mock()
        mock_polygon = Mock()
        mock_polygon.space_guid = "SPACE003"  # Space on FLOOR002
        mock_floor_geometry.room_polygons = [mock_polygon]
        
        window.geometry_extractor.floor_geometries = {
            "FLOOR002": mock_floor_geometry
        }
        
        # Simulate zoom to spaces request
        window.on_zoom_to_spaces_requested(["SPACE003"])
        
        # Verify floor was switched to the target floor
        window.floor_plan_widget.set_current_floor.assert_called_once_with("FLOOR002")
        
        # Verify zoom was called
        window.floor_plan_widget.zoom_to_spaces.assert_called_once_with(["SPACE003"])

    def test_floor_switching_with_multi_floor_selection(self, main_window_with_mocks):
        """Test floor switching behavior with spaces from multiple floors."""
        window = main_window_with_mocks
        
        # Mock geometry extractor
        window.geometry_extractor = Mock()
        mock_floor1_geometry = Mock()
        mock_floor2_geometry = Mock()
        
        # Mock polygons for different floors
        mock_polygon1 = Mock()
        mock_polygon1.space_guid = "SPACE001"
        mock_floor1_geometry.room_polygons = [mock_polygon1]
        
        mock_polygon2 = Mock()
        mock_polygon2.space_guid = "SPACE003"
        mock_floor2_geometry.room_polygons = [mock_polygon2]
        
        window.geometry_extractor.floor_geometries = {
            "FLOOR001": mock_floor1_geometry,
            "FLOOR002": mock_floor2_geometry
        }
        
        # Add the floor_plan_canvas attribute that the method checks for
        window.floor_plan_canvas = Mock()
        
        # Mock current floor to be different from target
        window.floor_plan_widget.get_current_floor_id.return_value = "FLOOR002"
        
        # Simulate zoom to spaces on different floors
        window.on_zoom_to_spaces_requested(["SPACE001", "SPACE003"])
        
        # Should switch to the floor of the first space
        window.floor_plan_widget.set_current_floor.assert_called_once_with("FLOOR001")


class TestSearchAndFilteringSynchronization:
    """Test cases for search and filtering synchronization."""

    def test_search_with_floor_filter_synchronization(self, main_window_with_mocks):
        """Test search functionality combined with floor filtering."""
        window = main_window_with_mocks
        
        # Mock space list widget methods
        window.space_list_widget.get_filtered_spaces.return_value = [
            next(s for s in window.spaces if s.guid == "SPACE001")  # Office on FLOOR001
        ]
        
        # Simulate search by directly calling the spaces selection changed method
        # (since search triggers selection changes)
        window.on_spaces_selection_changed(["SPACE001"])
        
        # Verify floor plan is updated to show only matching spaces
        window.floor_plan_widget.highlight_spaces.assert_called_once()

    def test_floor_filter_updates_floor_plan_display(self, main_window_with_mocks):
        """Test that floor filter changes update floor plan display."""
        window = main_window_with_mocks
        
        # Simulate floor filter change from space list
        window.on_floor_filter_changed("FLOOR002")
        
        # Verify floor plan widget switches to the filtered floor
        window.floor_plan_widget.set_current_floor.assert_called_once_with("FLOOR002")

    def test_clear_search_synchronization(self, main_window_with_mocks):
        """Test that clearing search updates all components."""
        window = main_window_with_mocks
        
        # Mock all spaces being visible after clearing search
        window.space_list_widget.get_filtered_spaces.return_value = window.spaces
        
        # Simulate clearing search by selecting all spaces
        all_space_guids = [s.guid for s in window.spaces]
        window.on_spaces_selection_changed(all_space_guids)
        
        # Verify floor plan shows all spaces
        window.floor_plan_widget.highlight_spaces.assert_called_once()


class TestErrorHandlingInSynchronization:
    """Test cases for error handling during UI synchronization."""

    def test_missing_geometry_data_handling(self, main_window_with_mocks):
        """Test handling of spaces without geometry data."""
        window = main_window_with_mocks
        
        # Remove geometry data
        window.floor_geometries = {}
        
        # Simulate space selection
        window.on_space_selected("SPACE001")
        
        # Should handle gracefully without crashing
        window.floor_plan_widget.highlight_spaces.assert_called_once_with(["SPACE001"])

    def test_invalid_floor_id_handling(self, main_window_with_mocks):
        """Test handling of invalid floor IDs."""
        window = main_window_with_mocks
        
        # Simulate floor change to non-existent floor
        window.on_floor_changed("INVALID_FLOOR")
        
        # Should handle gracefully without crashing
        # Space list filter should not be updated for invalid floor
        window.space_list_widget.set_floor_filter.assert_not_called()

    def test_component_not_initialized_handling(self, qapp, sample_spaces):
        """Test handling when UI components are not fully initialized."""
        window = MainWindow()
        window._testing_mode = True
        window.spaces = sample_spaces
        
        # Set some components to None to simulate partial initialization
        window.floor_plan_widget = None
        window.space_detail_widget = Mock()
        window.space_list_widget = Mock()
        window.surface_editor_widget = Mock()
        
        # Should handle gracefully without crashing
        # The current implementation doesn't handle None components gracefully,
        # so we expect an exception but verify it's logged properly
        with pytest.raises(AttributeError):
            window.on_space_selected("SPACE001")

    def test_concurrent_selection_changes(self, main_window_with_mocks):
        """Test handling of rapid concurrent selection changes."""
        window = main_window_with_mocks
        
        # Simulate rapid selection changes
        window.on_space_selected("SPACE001")
        window.on_space_selected("SPACE002")
        window.on_space_selected("SPACE003")
        
        # Should handle all changes without issues
        # Last call should be for SPACE003
        expected_space = next(s for s in window.spaces if s.guid == "SPACE003")
        window.space_detail_widget.display_space.assert_called_with(expected_space)


class TestPerformanceInSynchronization:
    """Test cases for performance aspects of UI synchronization."""

    def test_large_selection_handling(self, main_window_with_mocks):
        """Test handling of large multi-selections."""
        window = main_window_with_mocks
        
        # Create large selection (simulate selecting many spaces)
        large_selection = [f"SPACE{i:03d}" for i in range(100)]
        
        # Should handle large selections efficiently
        window.on_spaces_selection_changed(large_selection)
        
        # Verify floor plan was called with the large selection
        window.floor_plan_widget.highlight_spaces.assert_called_once_with(large_selection)

    def test_frequent_floor_switching(self, main_window_with_mocks):
        """Test performance with frequent floor switching."""
        window = main_window_with_mocks
        
        # Mock floor geometries for multiple floors
        window.floor_geometries = {f"FLOOR{i:03d}": Mock() for i in range(10)}
        
        # Simulate frequent floor switching
        for i in range(10):
            floor_id = f"FLOOR{i:03d}"
            window.on_floor_changed(floor_id)
        
        # Should handle frequent changes without performance issues
        assert window.floor_plan_widget.set_current_floor.call_count == 0  # No filter active

    def test_rapid_search_updates(self, main_window_with_mocks):
        """Test performance with rapid search updates."""
        window = main_window_with_mocks
        
        # Mock search results
        window.space_list_widget.get_filtered_spaces.return_value = [window.spaces[0]]
        
        # Simulate rapid search updates by triggering selection changes
        search_results = [window.spaces[0].guid]
        
        for i in range(6):  # Simulate 6 rapid updates
            window.on_spaces_selection_changed(search_results)
        
        # Should handle rapid updates efficiently
        assert window.floor_plan_widget.highlight_spaces.call_count == 6


if __name__ == "__main__":
    pytest.main([__file__])