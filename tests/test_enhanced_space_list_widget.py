"""
Unit Tests for Enhanced SpaceListWidget

Tests the enhanced floor filtering and synchronization functionality added to SpaceListWidget
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

from ifc_room_schedule.ui.space_list_widget import SpaceListWidget
from ifc_room_schedule.data.space_model import SpaceData
from ifc_room_schedule.visualization.geometry_models import FloorLevel


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
    return [
        SpaceData(
            guid="SPACE001",
            name="101",
            long_name="Office 101",
            description="Main office space",
            object_type="Office",
            zone_category="Office",
            number="101",
            elevation=0.0,
            quantities={"Height": 3.0, "Area": 25.5},
            floor_id="FLOOR001"
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
            quantities={"Height": 3.2, "Area": 18.0},
            floor_id="FLOOR001"
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
            quantities={"Height": 3.0, "Area": 22.0},
            floor_id="FLOOR002"
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
            quantities={"Height": 2.8, "Area": 12.0},
            floor_id="FLOOR002"
        )
    ]


@pytest.fixture
def sample_floor_levels():
    """Create sample floor level data for testing."""
    return [
        FloorLevel(
            id="FLOOR001",
            name="Ground Floor",
            elevation=0.0,
            spaces=["SPACE001", "SPACE002"],
            has_geometry=True,
            space_count=2,
            total_area=43.5
        ),
        FloorLevel(
            id="FLOOR002",
            name="First Floor",
            elevation=3.5,
            spaces=["SPACE003", "SPACE004"],
            has_geometry=True,
            space_count=2,
            total_area=34.0
        )
    ]


class TestEnhancedSpaceListWidget:
    """Test cases for enhanced SpaceListWidget functionality."""

    def test_initialization_with_floor_filter(self, qapp):
        """Test initialization includes floor filtering components."""
        widget = SpaceListWidget()
        
        # Check that floor filter components exist
        assert hasattr(widget, 'floor_filter_combo')
        assert hasattr(widget, 'floor_filter_label')
        
        # Check initial state
        assert widget.get_current_floor_filter() is None

    def test_set_floor_filter_options(self, qapp, sample_floor_levels):
        """Test setting floor filter options."""
        widget = SpaceListWidget()
        
        widget.set_floor_filter_options(sample_floor_levels)
        
        # Check that floor options were added
        # Should have "All Floors" plus the two sample floors
        assert widget.floor_filter_combo.count() == 3
        
        # Check first item is "All Floors"
        assert widget.floor_filter_combo.itemText(0) == "All Floors"
        assert widget.floor_filter_combo.itemData(0) is None
        
        # Check floor options
        assert "Ground Floor" in widget.floor_filter_combo.itemText(1)
        assert widget.floor_filter_combo.itemData(1) == "FLOOR001"
        assert "First Floor" in widget.floor_filter_combo.itemText(2)
        assert widget.floor_filter_combo.itemData(2) == "FLOOR002"

    def test_set_floor_filter(self, qapp, sample_floor_levels, sample_spaces):
        """Test setting specific floor filter."""
        widget = SpaceListWidget()
        widget.load_spaces(sample_spaces)
        widget.set_floor_filter_options(sample_floor_levels)
        
        # Set up signal spy
        spy = QSignalSpy(widget.floor_filter_changed)
        
        # Set filter to first floor
        widget.set_floor_filter("FLOOR001")
        
        # Check filter was set
        assert widget.get_current_floor_filter() == "FLOOR001"
        
        # Check signal was emitted
        assert len(spy) == 1
        assert spy[0][0] == "FLOOR001"
        
        # Check that only ground floor spaces are visible
        visible_spaces = widget.get_visible_spaces()
        visible_guids = [space.guid for space in visible_spaces]
        assert "SPACE001" in visible_guids
        assert "SPACE002" in visible_guids
        assert "SPACE003" not in visible_guids
        assert "SPACE004" not in visible_guids

    def test_clear_floor_filter(self, qapp, sample_floor_levels, sample_spaces):
        """Test clearing floor filter to show all spaces."""
        widget = SpaceListWidget()
        widget.load_spaces(sample_spaces)
        widget.set_floor_filter_options(sample_floor_levels)
        
        # First set a filter
        widget.set_floor_filter("FLOOR001")
        assert widget.get_current_floor_filter() == "FLOOR001"
        
        # Then clear it
        widget.set_floor_filter(None)
        
        # Check filter was cleared
        assert widget.get_current_floor_filter() is None
        
        # Check that all spaces are visible again
        visible_spaces = widget.get_visible_spaces()
        assert len(visible_spaces) == 4

    def test_floor_filter_with_search(self, qapp, sample_floor_levels, sample_spaces):
        """Test floor filter combined with search functionality."""
        widget = SpaceListWidget()
        widget.load_spaces(sample_spaces)
        widget.set_floor_filter_options(sample_floor_levels)
        
        # Set floor filter to first floor
        widget.set_floor_filter("FLOOR001")
        
        # Apply search filter
        widget.filter_spaces("office")
        
        # Should only show office spaces on first floor
        visible_spaces = widget.get_visible_spaces()
        assert len(visible_spaces) == 1
        assert visible_spaces[0].guid == "SPACE001"  # Office 101

    def test_geometry_indicators(self, qapp, sample_spaces):
        """Test visual indicators for spaces with/without geometry."""
        widget = SpaceListWidget()
        
        # Mock some spaces to have geometry and others not
        sample_spaces[0].has_geometry = True
        sample_spaces[1].has_geometry = False
        sample_spaces[2].has_geometry = True
        sample_spaces[3].has_geometry = False
        
        widget.load_spaces(sample_spaces)
        
        # Check that geometry indicators are displayed
        # This would test the visual representation in the list items
        for i in range(widget.space_list.count()):
            item = widget.space_list.item(i)
            item_widget = widget.space_list.itemWidget(item)
            
            # Check that geometry indicator is present
            assert hasattr(item_widget, 'geometry_indicator') or "📐" in item.text() or "❌" in item.text()

    def test_highlight_spaces_on_floor_plan(self, qapp, sample_spaces):
        """Test highlighting spaces on floor plan."""
        widget = SpaceListWidget()
        widget.load_spaces(sample_spaces)
        
        # Set up signal spy
        spy = QSignalSpy(widget.spaces_highlight_requested)
        
        # Select multiple spaces
        space_guids = ["SPACE001", "SPACE003"]
        widget.select_spaces_by_guids(space_guids)
        
        # Trigger highlight request
        widget.highlight_spaces_on_floor_plan(space_guids)
        
        # Check signal was emitted
        assert len(spy) == 1
        assert spy[0][0] == space_guids

    def test_sync_with_floor_plan_selection(self, qapp, sample_spaces):
        """Test synchronization with floor plan selection."""
        widget = SpaceListWidget()
        widget.load_spaces(sample_spaces)
        
        # Simulate floor plan selection
        selected_guids = ["SPACE002", "SPACE004"]
        widget.sync_with_floor_plan_selection(selected_guids)
        
        # Check that spaces are selected in the list
        selected_spaces = widget.get_selected_spaces()
        selected_space_guids = [space.guid for space in selected_spaces]
        
        assert "SPACE002" in selected_space_guids
        assert "SPACE004" in selected_space_guids

    def test_floor_context_in_search(self, qapp, sample_floor_levels, sample_spaces):
        """Test that search includes floor context information."""
        widget = SpaceListWidget()
        widget.load_spaces(sample_spaces)
        widget.set_floor_filter_options(sample_floor_levels)
        
        # Search for "ground" should find spaces on ground floor
        widget.filter_spaces("ground")
        
        visible_spaces = widget.get_visible_spaces()
        # Should find spaces on ground floor based on floor context
        ground_floor_spaces = [space for space in visible_spaces if space.floor_id == "FLOOR001"]
        assert len(ground_floor_spaces) > 0

    def test_multi_selection_with_ctrl(self, qapp, sample_spaces):
        """Test multi-selection functionality with Ctrl key."""
        widget = SpaceListWidget()
        widget.load_spaces(sample_spaces)
        
        # Simulate Ctrl+click selection
        widget.select_space_by_guid("SPACE001", extend_selection=True)
        widget.select_space_by_guid("SPACE003", extend_selection=True)
        
        selected_spaces = widget.get_selected_spaces()
        selected_guids = [space.guid for space in selected_spaces]
        
        assert len(selected_spaces) == 2
        assert "SPACE001" in selected_guids
        assert "SPACE003" in selected_guids

    def test_floor_filter_signal_emission(self, qapp, sample_floor_levels):
        """Test floor filter change signal emission."""
        widget = SpaceListWidget()
        widget.set_floor_filter_options(sample_floor_levels)
        
        # Set up signal spy
        spy = QSignalSpy(widget.floor_filter_changed)
        
        # Change floor filter via combo box
        widget.floor_filter_combo.setCurrentIndex(1)  # Ground Floor
        
        # Check signal was emitted
        assert len(spy) == 1
        assert spy[0][0] == "FLOOR001"

    def test_space_count_with_floor_filter(self, qapp, sample_floor_levels, sample_spaces):
        """Test space count display with floor filtering."""
        widget = SpaceListWidget()
        widget.load_spaces(sample_spaces)
        widget.set_floor_filter_options(sample_floor_levels)
        
        # Initially should show all spaces
        assert "4 spaces" in widget.count_label.text()
        
        # Filter to first floor
        widget.set_floor_filter("FLOOR001")
        
        # Should show filtered count
        assert "Showing 2 of 4 spaces" in widget.count_label.text()

    def test_get_spaces_by_floor(self, qapp, sample_spaces):
        """Test getting spaces grouped by floor."""
        widget = SpaceListWidget()
        widget.load_spaces(sample_spaces)
        
        spaces_by_floor = widget.get_spaces_by_floor()
        
        assert "FLOOR001" in spaces_by_floor
        assert "FLOOR002" in spaces_by_floor
        assert len(spaces_by_floor["FLOOR001"]) == 2
        assert len(spaces_by_floor["FLOOR002"]) == 2

    def test_zoom_to_spaces_request(self, qapp, sample_spaces):
        """Test zoom to spaces request functionality."""
        widget = SpaceListWidget()
        widget.load_spaces(sample_spaces)
        
        # Set up signal spy
        spy = QSignalSpy(widget.zoom_to_spaces_requested)
        
        # Select spaces and request zoom
        space_guids = ["SPACE001", "SPACE002"]
        widget.select_spaces_by_guids(space_guids)
        widget.request_zoom_to_selected_spaces()
        
        # Check signal was emitted
        assert len(spy) == 1
        assert spy[0][0] == space_guids

    def test_floor_aware_space_navigation(self, qapp, sample_spaces, sample_floor_levels):
        """Test floor-aware space navigation."""
        widget = SpaceListWidget()
        widget.load_spaces(sample_spaces)
        widget.set_floor_filter_options(sample_floor_levels)
        
        # Set floor filter
        widget.set_floor_filter("FLOOR001")
        
        # Navigate through spaces on current floor only
        widget.select_next_space()
        selected_space = widget.get_selected_space()
        assert selected_space.floor_id == "FLOOR001"
        
        widget.select_next_space()
        selected_space = widget.get_selected_space()
        assert selected_space.floor_id == "FLOOR001"
        
        # Should wrap around within the same floor
        widget.select_next_space()
        selected_space = widget.get_selected_space()
        assert selected_space.floor_id == "FLOOR001"

    def test_enhanced_space_info_with_floor(self, qapp, sample_spaces):
        """Test enhanced space information display including floor context."""
        widget = SpaceListWidget()
        widget.load_spaces(sample_spaces)
        
        # Select a space
        widget.select_space_by_guid("SPACE003")
        
        # Check that space info includes floor information
        info_text = widget.info_label.text()
        assert "201" in info_text  # Space number
        assert "Office 201" in info_text  # Space name
        # Floor information should be included in context
        assert "Floor" in info_text or "Level" in info_text or "3.5" in info_text

    def test_clear_selection_with_floor_plan_sync(self, qapp, sample_spaces):
        """Test clearing selection synchronizes with floor plan."""
        widget = SpaceListWidget()
        widget.load_spaces(sample_spaces)
        
        # Set up signal spy
        spy = QSignalSpy(widget.selection_cleared)
        
        # Select some spaces first
        widget.select_spaces_by_guids(["SPACE001", "SPACE002"])
        
        # Clear selection
        widget.clear_selection()
        
        # Check selection was cleared
        assert len(widget.get_selected_spaces()) == 0
        
        # Check signal was emitted
        assert len(spy) == 1

    def test_floor_metadata_display(self, qapp, sample_floor_levels):
        """Test floor metadata display in filter options."""
        widget = SpaceListWidget()
        widget.set_floor_filter_options(sample_floor_levels)
        
        # Check that floor options include metadata
        for i in range(1, widget.floor_filter_combo.count()):  # Skip "All Floors"
            item_text = widget.floor_filter_combo.itemText(i)
            # Should include elevation and space count
            assert "Elev:" in item_text or "m" in item_text
            assert "spaces" in item_text or "2" in item_text


class TestSpaceListWidgetSignals:
    """Test cases for enhanced signal handling in SpaceListWidget."""

    def test_floor_filter_changed_signal(self, qapp, sample_floor_levels):
        """Test floor_filter_changed signal emission."""
        widget = SpaceListWidget()
        widget.set_floor_filter_options(sample_floor_levels)
        
        spy = QSignalSpy(widget.floor_filter_changed)
        
        # Change filter
        widget.set_floor_filter("FLOOR002")
        
        assert len(spy) == 1
        assert spy[0][0] == "FLOOR002"

    def test_spaces_highlight_requested_signal(self, qapp, sample_spaces):
        """Test spaces_highlight_requested signal emission."""
        widget = SpaceListWidget()
        widget.load_spaces(sample_spaces)
        
        spy = QSignalSpy(widget.spaces_highlight_requested)
        
        # Request highlight
        space_guids = ["SPACE001", "SPACE003"]
        widget.highlight_spaces_on_floor_plan(space_guids)
        
        assert len(spy) == 1
        assert spy[0][0] == space_guids

    def test_zoom_to_spaces_requested_signal(self, qapp, sample_spaces):
        """Test zoom_to_spaces_requested signal emission."""
        widget = SpaceListWidget()
        widget.load_spaces(sample_spaces)
        
        spy = QSignalSpy(widget.zoom_to_spaces_requested)
        
        # Request zoom
        space_guids = ["SPACE002"]
        widget.select_spaces_by_guids(space_guids)
        widget.request_zoom_to_selected_spaces()
        
        assert len(spy) == 1
        assert spy[0][0] == space_guids

    def test_selection_cleared_signal(self, qapp, sample_spaces):
        """Test selection_cleared signal emission."""
        widget = SpaceListWidget()
        widget.load_spaces(sample_spaces)
        
        spy = QSignalSpy(widget.selection_cleared)
        
        # Select and then clear
        widget.select_space_by_guid("SPACE001")
        widget.clear_selection()
        
        assert len(spy) == 1


if __name__ == "__main__":
    pytest.main([__file__])