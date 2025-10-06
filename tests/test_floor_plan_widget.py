"""
Unit Tests for FloorPlanWidget Components

Tests the FloorPlanWidget, FloorSelector, and NavigationControls components
that were added as part of the interactive floor plan enhancement.
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

from ifc_room_schedule.ui.floor_plan_widget import FloorPlanWidget, FloorSelector, NavigationControls
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
def sample_floor_levels():
    """Create sample floor level data for testing."""
    return [
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
            spaces=["SPACE003", "SPACE004", "SPACE005"]
        ),
        FloorLevel(
            id="FLOOR003",
            name="Second Floor", 
            elevation=7.0,
            spaces=["SPACE006"]
        )
    ]


@pytest.fixture
def sample_floor_geometries(sample_floor_levels):
    """Create sample floor geometry data for testing."""
    geometries = {}
    
    # Only create geometries for FLOOR001 and FLOOR002 (FLOOR003 has no geometry)
    floors_with_geometry = ["FLOOR001", "FLOOR002"]
    
    for floor_level in sample_floor_levels:
        if floor_level.id in floors_with_geometry:
            # Create simple rectangular polygons for testing
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


class TestFloorSelector:
    """Test cases for FloorSelector component."""

    def test_initialization(self, qapp):
        """Test FloorSelector initialization."""
        selector = FloorSelector()
        
        # Check UI components exist
        assert selector.floor_label is not None
        assert selector.floor_combo is not None
        assert selector.metadata_label is not None
        
        # Check initial state
        assert selector.floor_combo.count() == 0
        assert selector.get_current_floor() is None

    def test_set_floors_empty(self, qapp):
        """Test setting empty floor list."""
        selector = FloorSelector()
        selector.set_floors([])
        
        assert selector.floor_combo.count() == 1
        assert selector.floor_combo.itemText(0) == "No floors available"
        assert not selector.floor_combo.isEnabled()
        assert selector.metadata_label.text() == ""

    def test_set_floors_with_data(self, qapp, sample_floor_levels):
        """Test setting floors with valid data."""
        selector = FloorSelector()
        selector.set_floors(sample_floor_levels)
        
        # Should have 3 floors
        assert selector.floor_combo.count() == 3
        assert selector.floor_combo.isEnabled()
        
        # Check floors are sorted by elevation (lowest first)
        assert selector.floor_combo.itemData(0) == "FLOOR001"  # Ground Floor (0.0m)
        assert selector.floor_combo.itemData(1) == "FLOOR002"  # First Floor (3.5m)
        assert selector.floor_combo.itemData(2) == "FLOOR003"  # Second Floor (7.0m)
        
        # Check display text includes elevation
        assert "Ground Floor (Elev: 0.0m)" in selector.floor_combo.itemText(0)
        assert "First Floor (Elev: 3.5m)" in selector.floor_combo.itemText(1)

    def test_set_current_floor(self, qapp, sample_floor_levels):
        """Test setting current floor selection."""
        selector = FloorSelector()
        selector.set_floors(sample_floor_levels)
        
        # Set to second floor
        selector.set_current_floor("FLOOR002")
        
        assert selector.get_current_floor() == "FLOOR002"
        assert selector.floor_combo.currentData() == "FLOOR002"

    def test_floor_selection_signal(self, qapp, sample_floor_levels):
        """Test floor selection signal emission."""
        selector = FloorSelector()
        selector.set_floors(sample_floor_levels)
        
        # Set up signal spy
        spy = QSignalSpy(selector.floor_selected)
        
        # Change selection programmatically
        selector.floor_combo.setCurrentIndex(1)  # First Floor
        
        # Check signal was emitted
        assert len(spy) == 1
        assert spy[0][0] == "FLOOR002"

    def test_metadata_display(self, qapp, sample_floor_levels):
        """Test metadata display updates."""
        selector = FloorSelector()
        selector.set_floors(sample_floor_levels)
        
        # Set to ground floor
        selector.set_current_floor("FLOOR001")
        
        # Check metadata shows space count (FloorLevel has get_space_count method)
        metadata_text = selector.metadata_label.text()
        assert "2 spaces" in metadata_text


class TestNavigationControls:
    """Test cases for NavigationControls component."""

    def test_initialization(self, qapp):
        """Test NavigationControls initialization."""
        controls = NavigationControls()
        
        # Check UI components exist
        assert controls.zoom_in_btn is not None
        assert controls.zoom_out_btn is not None
        assert controls.fit_view_btn is not None
        assert controls.reset_pan_btn is not None
        
        # Check button properties
        assert controls.zoom_in_btn.text() == "🔍+"
        assert controls.zoom_out_btn.text() == "🔍-"
        assert controls.fit_view_btn.text() == "⌂"
        assert controls.reset_pan_btn.text() == "⌖"

    def test_zoom_in_signal(self, qapp):
        """Test zoom in signal emission."""
        controls = NavigationControls()
        spy = QSignalSpy(controls.zoom_in_requested)
        
        # Click zoom in button
        controls.zoom_in_btn.click()
        
        assert len(spy) == 1

    def test_zoom_out_signal(self, qapp):
        """Test zoom out signal emission."""
        controls = NavigationControls()
        spy = QSignalSpy(controls.zoom_out_requested)
        
        # Click zoom out button
        controls.zoom_out_btn.click()
        
        assert len(spy) == 1

    def test_zoom_fit_signal(self, qapp):
        """Test zoom fit signal emission."""
        controls = NavigationControls()
        spy = QSignalSpy(controls.zoom_fit_requested)
        
        # Click fit view button
        controls.fit_view_btn.click()
        
        assert len(spy) == 1

    def test_pan_reset_signal(self, qapp):
        """Test pan reset signal emission."""
        controls = NavigationControls()
        spy = QSignalSpy(controls.pan_reset_requested)
        
        # Click reset pan button
        controls.reset_pan_btn.click()
        
        assert len(spy) == 1

    def test_button_tooltips(self, qapp):
        """Test button tooltips are set correctly."""
        controls = NavigationControls()
        
        assert controls.zoom_in_btn.toolTip() == "Zoom In"
        assert controls.zoom_out_btn.toolTip() == "Zoom Out"
        assert controls.fit_view_btn.toolTip() == "Fit to View"
        assert controls.reset_pan_btn.toolTip() == "Reset View"


class TestFloorPlanWidget:
    """Test cases for FloorPlanWidget main component."""

    def test_initialization(self, qapp):
        """Test FloorPlanWidget initialization."""
        widget = FloorPlanWidget()
        
        # Check main components exist
        assert widget.floor_selector is not None
        assert widget.navigation_controls is not None
        assert widget.floor_plan_canvas is not None
        
        # Check initial state
        assert widget.current_floor_id is None
        assert len(widget.floor_geometries) == 0

    def test_set_floor_geometry(self, qapp, sample_floor_geometries):
        """Test setting floor geometry data."""
        widget = FloorPlanWidget()
        
        # Mock the canvas method
        widget.floor_plan_canvas.set_floor_geometries = Mock()
        
        widget.set_floor_geometry(sample_floor_geometries)
        
        # Check geometry data was stored
        assert len(widget.floor_geometries) == 2  # Only floors with geometry
        assert "FLOOR001" in widget.floor_geometries
        assert "FLOOR002" in widget.floor_geometries
        
        # Check canvas was updated
        widget.floor_plan_canvas.set_floor_geometries.assert_called_once()
        
        # Check current floor was set to first floor (by elevation)
        assert widget.current_floor_id == "FLOOR001"

    def test_set_current_floor(self, qapp, sample_floor_geometries):
        """Test setting current floor."""
        widget = FloorPlanWidget()
        widget.floor_geometries = sample_floor_geometries
        
        # Mock canvas methods
        widget.floor_plan_canvas.set_current_floor = Mock()
        
        # Set up signal spy
        spy = QSignalSpy(widget.floor_changed)
        
        widget.set_current_floor("FLOOR002")
        
        # Check floor was set
        assert widget.current_floor_id == "FLOOR002"
        
        # Check canvas was updated
        widget.floor_plan_canvas.set_current_floor.assert_called_once_with("FLOOR002")
        
        # Check signal was emitted
        assert len(spy) == 1
        assert spy[0][0] == "FLOOR002"

    def test_highlight_spaces(self, qapp, sample_floor_geometries):
        """Test highlighting spaces."""
        widget = FloorPlanWidget()
        widget.floor_geometries = sample_floor_geometries
        
        # Mock canvas method
        widget.floor_plan_canvas.highlight_rooms = Mock()
        
        space_guids = ["SPACE001", "SPACE002"]
        widget.highlight_spaces(space_guids)
        
        # Check canvas method was called
        widget.floor_plan_canvas.highlight_rooms.assert_called_once_with(space_guids)

    def test_zoom_to_spaces(self, qapp, sample_floor_geometries):
        """Test zooming to specific spaces."""
        widget = FloorPlanWidget()
        widget.floor_geometries = sample_floor_geometries
        
        # Mock canvas method
        widget.floor_plan_canvas.zoom_to_rooms = Mock()
        
        space_guids = ["SPACE001"]
        widget.zoom_to_spaces(space_guids)
        
        # Check canvas method was called
        widget.floor_plan_canvas.zoom_to_rooms.assert_called_once_with(space_guids)

    def test_zoom_to_fit(self, qapp):
        """Test zoom to fit functionality."""
        widget = FloorPlanWidget()
        
        # Mock canvas method
        widget.floor_plan_canvas.zoom_to_fit = Mock()
        
        widget.zoom_to_fit()
        
        # Check canvas method was called
        widget.floor_plan_canvas.zoom_to_fit.assert_called_once()

    def test_clear_selection(self, qapp):
        """Test clearing selection."""
        widget = FloorPlanWidget()
        
        # Mock canvas method
        widget.floor_plan_canvas.clear_selection = Mock()
        
        widget.clear_selection()
        
        # Check canvas method was called
        widget.floor_plan_canvas.clear_selection.assert_called_once()

    def test_navigation_controls_integration(self, qapp):
        """Test integration with navigation controls."""
        widget = FloorPlanWidget()
        
        # Mock canvas properties and methods
        widget.floor_plan_canvas.zoom_level = 1.0
        widget.floor_plan_canvas.max_zoom = 5.0
        widget.floor_plan_canvas.min_zoom = 0.1
        widget.floor_plan_canvas._update_view_transform = Mock()
        widget.floor_plan_canvas.update = Mock()
        widget.floor_plan_canvas.zoom_to_fit = Mock()
        
        # Test zoom in
        widget._zoom_in()
        assert widget.floor_plan_canvas.zoom_level == 1.2
        widget.floor_plan_canvas._update_view_transform.assert_called()
        widget.floor_plan_canvas.update.assert_called()
        
        # Test zoom out
        widget._zoom_out()
        assert widget.floor_plan_canvas.zoom_level == 1.0
        
        # Test zoom to fit
        widget._zoom_to_fit()
        widget.floor_plan_canvas.zoom_to_fit.assert_called()
        
        # Test reset view
        widget._reset_view()
        assert widget.floor_plan_canvas.zoom_to_fit.call_count == 2

    def test_space_clicked_signal_forwarding(self, qapp):
        """Test that space clicked signals are forwarded correctly."""
        widget = FloorPlanWidget()
        
        # Set up signal spy
        spy = QSignalSpy(widget.space_selected)
        
        # Simulate space click from canvas
        widget._on_space_clicked("SPACE001", True)
        
        # Check signal was forwarded
        assert len(spy) == 1
        assert spy[0][0] == "SPACE001"
        assert spy[0][1] == True

    def test_floor_selector_integration(self, qapp, sample_floor_geometries):
        """Test integration with floor selector."""
        widget = FloorPlanWidget()
        widget.floor_geometries = sample_floor_geometries
        
        # Mock canvas method
        widget.floor_plan_canvas.set_current_floor = Mock()
        
        # Simulate floor selection
        widget._on_floor_selected("FLOOR002")
        
        # Check current floor was updated
        assert widget.current_floor_id == "FLOOR002"
        widget.floor_plan_canvas.set_current_floor.assert_called_with("FLOOR002")

    def test_get_current_floor_id(self, qapp, sample_floor_geometries):
        """Test getting current floor ID."""
        widget = FloorPlanWidget()
        widget.floor_geometries = sample_floor_geometries
        
        # Initially should be None
        assert widget.get_current_floor_id() is None
        
        # Set a floor
        widget.set_current_floor("FLOOR001")
        assert widget.get_current_floor_id() == "FLOOR001"

    def test_zoom_limits(self, qapp):
        """Test zoom limits are respected."""
        widget = FloorPlanWidget()
        
        # Mock canvas properties
        widget.floor_plan_canvas.zoom_level = 4.5
        widget.floor_plan_canvas.max_zoom = 5.0
        widget.floor_plan_canvas.min_zoom = 0.1
        widget.floor_plan_canvas._update_view_transform = Mock()
        widget.floor_plan_canvas.update = Mock()
        
        # Test zoom in at near max
        widget._zoom_in()
        assert widget.floor_plan_canvas.zoom_level == 5.0  # Should be clamped to max
        
        # Test zoom out at near min
        widget.floor_plan_canvas.zoom_level = 0.12
        widget._zoom_out()
        assert widget.floor_plan_canvas.zoom_level == 0.1  # Should be clamped to min


if __name__ == "__main__":
    pytest.main([__file__])