#!/usr/bin/env python3
"""
Test ArchiCAD-style features in floor plan canvas
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ifc_room_schedule.visualization.floor_plan_canvas import FloorPlanCanvas
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
def sample_floor_geometry():
    """Create sample floor geometry for testing."""
    floor_level = FloorLevel(
        id="test_floor",
        name="Test Floor",
        elevation=0.0,
        spaces=["room1", "room2"]
    )
    
    room1 = Polygon2D(
        points=[
            Point2D(0, 0),
            Point2D(10, 0),
            Point2D(10, 8),
            Point2D(0, 8)
        ],
        space_guid="room1",
        space_name="Stue"
    )
    
    room2 = Polygon2D(
        points=[
            Point2D(12, 0),
            Point2D(20, 0),
            Point2D(20, 6),
            Point2D(12, 6)
        ],
        space_guid="room2",
        space_name="Soverom"
    )
    
    return FloorGeometry(
        level=floor_level,
        room_polygons=[room1, room2],
        bounds=(0, 0, 20, 8)
    )


class TestArchiCADStyleFeatures:
    """Test ArchiCAD-style features."""

    def test_professional_style_toggle(self, qapp, sample_floor_geometry):
        """Test professional style toggle functionality."""
        canvas = FloorPlanCanvas()
        canvas.set_floor_geometry(sample_floor_geometry)
        
        # Initially should be in professional style
        assert canvas.use_professional_style == True
        assert canvas.use_color_coding == False
        
        # Toggle to colored style
        canvas.set_professional_style(False)
        assert canvas.use_professional_style == False
        
        # Toggle back to professional style
        canvas.set_professional_style(True)
        assert canvas.use_professional_style == True
        assert canvas.use_color_coding == False

    def test_room_areas_toggle(self, qapp, sample_floor_geometry):
        """Test room areas display toggle."""
        canvas = FloorPlanCanvas()
        canvas.set_floor_geometry(sample_floor_geometry)
        
        # Initially should show areas
        assert canvas.show_room_areas == True
        
        # Toggle off
        canvas.set_show_room_areas(False)
        assert canvas.show_room_areas == False
        
        # Toggle back on
        canvas.set_show_room_areas(True)
        assert canvas.show_room_areas == True

    def test_archicad_style_colors(self, qapp):
        """Test ArchiCAD-style color scheme."""
        canvas = FloorPlanCanvas()
        
        # Professional style should use specific colors
        assert canvas.COLOR_BACKGROUND == QColor(255, 255, 255)  # Pure white
        assert canvas.COLOR_ROOM_BORDER == QColor(0, 0, 0)       # Black borders
        assert canvas.COLOR_ROOM_TEXT == QColor(0, 0, 0)         # Black text

    def test_label_formatting(self, qapp, sample_floor_geometry):
        """Test ArchiCAD-style label formatting."""
        canvas = FloorPlanCanvas()
        canvas.set_floor_geometry(sample_floor_geometry)
        
        # Test room label formatting
        room_polygon = sample_floor_geometry.room_polygons[0]  # "Stue"
        
        # Test basic label
        label = canvas._get_space_label_text(room_polygon, detailed=False)
        assert "Stue" in label
        
        # Test detailed label with area
        detailed_label = canvas._get_space_label_text(room_polygon, detailed=True)
        assert "Stue" in detailed_label
        assert "m²" in detailed_label

    def test_font_types(self, qapp):
        """Test different font types for different label elements."""
        canvas = FloorPlanCanvas()
        
        # Test different font types
        room_number_font = canvas._get_label_font("room_number")
        room_name_font = canvas._get_label_font("room_name")
        area_font = canvas._get_label_font("area")
        
        # Room number should be bold
        assert room_number_font.bold() == True
        
        # Room name should be normal weight
        assert room_name_font.bold() == False
        
        # Area font should be smaller
        assert area_font.pointSize() <= room_name_font.pointSize()

    def test_norwegian_room_name_mapping(self, qapp):
        """Test Norwegian room name mapping."""
        canvas = FloorPlanCanvas()
        
        # Create test polygon with Norwegian room name
        room_polygon = Polygon2D(
            points=[Point2D(0, 0), Point2D(5, 0), Point2D(5, 5), Point2D(0, 5)],
            space_guid="test",
            space_name="soverom"
        )
        
        label = canvas._get_space_label_text(room_polygon, detailed=False)
        
        # Should be mapped to "Sov" (ArchiCAD style abbreviation)
        assert "Sov" in label

    def test_grid_overlay_zoom_levels(self, qapp, sample_floor_geometry):
        """Test grid overlay adapts to zoom levels."""
        canvas = FloorPlanCanvas()
        canvas.set_floor_geometry(sample_floor_geometry)
        
        # Mock painter for testing
        with patch('ifc_room_schedule.visualization.floor_plan_canvas.QPainter') as mock_painter:
            painter = mock_painter.return_value
            
            # Test high zoom - should use 1m grid
            canvas.zoom_level = 2.0
            canvas._draw_grid_overlay(painter)
            
            # Test medium zoom - should use 2.5m grid
            canvas.zoom_level = 0.8
            canvas._draw_grid_overlay(painter)
            
            # Test low zoom - should use larger grid
            canvas.zoom_level = 0.3
            canvas._draw_grid_overlay(painter)
            
            # Verify painter methods were called
            assert painter.setPen.called
            assert painter.drawLine.called

    def test_scale_indicator_zoom_adaptation(self, qapp, sample_floor_geometry):
        """Test scale indicator adapts to zoom level."""
        canvas = FloorPlanCanvas()
        canvas.set_floor_geometry(sample_floor_geometry)
        
        # Mock painter
        with patch('ifc_room_schedule.visualization.floor_plan_canvas.QPainter') as mock_painter:
            painter = mock_painter.return_value
            
            # Test different zoom levels
            zoom_levels = [0.1, 0.5, 1.0, 2.5]
            
            for zoom in zoom_levels:
                canvas.zoom_level = zoom
                canvas._draw_scale_indicator(painter)
                
                # Verify drawing methods were called
                assert painter.fillRect.called
                assert painter.drawLine.called
                assert painter.drawText.called

    def test_professional_vs_colored_rendering(self, qapp, sample_floor_geometry):
        """Test difference between professional and colored rendering."""
        canvas = FloorPlanCanvas()
        canvas.set_floor_geometry(sample_floor_geometry)
        
        # Test that professional style is enabled by default
        assert canvas.use_professional_style == True
        
        # Test that colored style can be enabled
        canvas.enable_ns3940_color_coding(True)
        assert canvas.use_color_coding == True
        assert canvas.use_professional_style == False
        
        # Test that professional style disables color coding
        canvas.set_professional_style(True)
        assert canvas.use_professional_style == True
        assert canvas.use_color_coding == False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])