#!/usr/bin/env python3
"""
Enhanced Floor Plan Canvas with improved zone boundaries, names, and area display.

This enhanced version provides:
- Clearer zone boundaries with thicker, more visible borders
- Prominent zone names and room numbers
- Floor area information displayed for each room
- Better visual hierarchy and readability
- Enhanced color coding and contrast
"""

import sys
import os
from typing import Optional, List, Dict, Any
from PyQt6.QtWidgets import QWidget, QApplication, QVBoxLayout, QMainWindow, QPushButton, QLabel
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPolygonF, QFontMetrics

# Add project root to path
sys.path.append('.')

from ifc_room_schedule.visualization.floor_plan_canvas import FloorPlanCanvas
from ifc_room_schedule.visualization.geometry_models import Polygon2D, FloorGeometry


class EnhancedFloorPlanCanvas(FloorPlanCanvas):
    """Enhanced floor plan canvas with improved zone visualization."""
    
    # Enhanced visual constants
    ZONE_BORDER_WIDTH = 2.5  # Thicker borders for better visibility
    ZONE_SELECTED_WIDTH = 4.0  # Even thicker for selected zones
    ZONE_HOVER_WIDTH = 3.0  # Medium thickness for hover
    
    # Enhanced colors for better contrast
    COLOR_ZONE_BORDER = QColor(60, 60, 60)  # Darker border
    COLOR_ZONE_SELECTED_BORDER = QColor(0, 100, 200)  # Blue for selection
    COLOR_ZONE_HOVER_BORDER = QColor(0, 150, 255)  # Lighter blue for hover
    COLOR_ZONE_TEXT = QColor(20, 20, 20)  # Very dark text
    COLOR_ZONE_TEXT_BACKGROUND = QColor(255, 255, 255, 220)  # More opaque background
    COLOR_AREA_TEXT = QColor(80, 80, 80)  # Slightly lighter for area text
    
    def __init__(self, parent=None):
        """Initialize enhanced floor plan canvas."""
        super().__init__(parent)
        
        # Enhanced label settings
        self.show_zone_names = True
        self.show_room_numbers = True
        self.show_floor_areas = True
        self.zone_name_font_size = 12
        self.area_font_size = 10
        
        # Enhanced visual settings
        self.use_enhanced_borders = True
        self.use_enhanced_labels = True
        
    def set_enhanced_display_options(self, 
                                   show_zone_names: bool = True,
                                   show_room_numbers: bool = True, 
                                   show_floor_areas: bool = True,
                                   zone_name_font_size: int = 12,
                                   area_font_size: int = 10):
        """
        Configure enhanced display options.
        
        Args:
            show_zone_names: Whether to show zone/room names
            show_room_numbers: Whether to show room numbers
            show_floor_areas: Whether to show floor area information
            zone_name_font_size: Font size for zone names
            area_font_size: Font size for area text
        """
        self.show_zone_names = show_zone_names
        self.show_room_numbers = show_room_numbers
        self.show_floor_areas = show_floor_areas
        self.zone_name_font_size = zone_name_font_size
        self.area_font_size = area_font_size
        self.update()
    
    def _draw_room_polygons(self, painter: QPainter) -> None:
        """Draw enhanced room polygons with improved borders and fills."""
        # Draw visible rooms with enhanced styling
        for polygon in self.visible_rooms:
            self._draw_enhanced_zone_polygon(painter, polygon)
    
    def _draw_enhanced_zone_polygon(self, painter: QPainter, polygon: Polygon2D) -> None:
        """
        Draw a single zone polygon with enhanced styling.
        
        Args:
            painter: QPainter instance
            polygon: Polygon to draw
        """
        # Determine border style based on state
        is_selected = polygon.space_guid in self.selected_rooms
        is_hovered = polygon.space_guid == self.hovered_room
        
        if is_selected:
            border_width = self.ZONE_SELECTED_WIDTH / max(0.5, self.zoom_level)
            border_color = self.COLOR_ZONE_SELECTED_BORDER
        elif is_hovered:
            border_width = self.ZONE_HOVER_WIDTH / max(0.5, self.zoom_level)
            border_color = self.COLOR_ZONE_HOVER_BORDER
        else:
            border_width = self.ZONE_BORDER_WIDTH / max(0.5, self.zoom_level)
            border_color = self.COLOR_ZONE_BORDER
        
        # Set up pen for borders
        pen = QPen(border_color, border_width)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        
        # Get fill color
        if self.use_color_coding:
            fill_color = self.get_space_color(polygon.space_guid)
            # Adjust alpha for better visibility
            fill_color.setAlpha(120 if is_selected else 80)
        else:
            fill_color = QColor(240, 240, 240, 120 if is_selected else 80)
        
        brush = QBrush(fill_color)
        painter.setBrush(brush)
        
        # Draw the polygon
        qt_polygon = self._polygon_to_qt(polygon)
        painter.drawPolygon(qt_polygon)
        
        # Add subtle inner shadow for depth
        if is_selected or is_hovered:
            self._draw_zone_inner_shadow(painter, qt_polygon)
    
    def _draw_zone_inner_shadow(self, painter: QPainter, qt_polygon: QPolygonF) -> None:
        """
        Draw a subtle inner shadow for selected/hovered zones.
        
        Args:
            painter: QPainter instance
            qt_polygon: Qt polygon to add shadow to
        """
        # Create a slightly smaller polygon for inner shadow
        center = qt_polygon.boundingRect().center()
        shadow_polygon = QPolygonF()
        
        shadow_offset = 2.0 / max(0.5, self.zoom_level)
        
        for i in range(qt_polygon.size()):
            point = qt_polygon.at(i)
            # Move point slightly toward center
            dx = center.x() - point.x()
            dy = center.y() - point.y()
            
            # Normalize and scale
            length = (dx * dx + dy * dy) ** 0.5
            if length > 0:
                dx = (dx / length) * shadow_offset
                dy = (dy / length) * shadow_offset
            
            shadow_point = QPointF(point.x() + dx, point.y() + dy)
            shadow_polygon.append(shadow_point)
        
        # Draw inner shadow
        shadow_pen = QPen(QColor(0, 0, 0, 30), 1.0 / max(0.5, self.zoom_level))
        painter.setPen(shadow_pen)
        painter.setBrush(QBrush())  # No fill
        painter.drawPolygon(shadow_polygon)
    
    def _draw_room_labels(self, painter: QPainter) -> None:
        """Draw enhanced room labels with zone names and area information."""
        if not self._should_show_labels():
            return
        
        # Draw labels for visible rooms
        for polygon in self.visible_rooms:
            self._draw_enhanced_zone_label(painter, polygon)
    
    def _draw_enhanced_zone_label(self, painter: QPainter, polygon: Polygon2D) -> None:
        """
        Draw enhanced label for a zone with name, number, and area.
        
        Args:
            painter: QPainter instance
            polygon: Polygon to label
        """
        centroid = polygon.get_centroid()
        label_point = QPointF(centroid.x, centroid.y)
        
        # Get zone information
        zone_info = self._get_enhanced_zone_info(polygon)
        
        if not zone_info:
            return
        
        # Calculate label layout
        label_lines = []
        
        # Add room number if available and enabled
        if self.show_room_numbers and zone_info.get('room_number'):
            label_lines.append({
                'text': zone_info['room_number'],
                'font_size': self.zone_name_font_size + 2,
                'bold': True,
                'color': self.COLOR_ZONE_TEXT
            })
        
        # Add zone name if available and enabled
        if self.show_zone_names and zone_info.get('zone_name'):
            label_lines.append({
                'text': zone_info['zone_name'],
                'font_size': self.zone_name_font_size,
                'bold': False,
                'color': self.COLOR_ZONE_TEXT
            })
        
        # Add floor area if available and enabled
        if self.show_floor_areas and zone_info.get('floor_area'):
            area_text = f"{zone_info['floor_area']:.1f} m²"
            label_lines.append({
                'text': area_text,
                'font_size': self.area_font_size,
                'bold': False,
                'color': self.COLOR_AREA_TEXT
            })
        
        if label_lines:
            self._draw_multi_line_label_with_background(painter, label_point, label_lines)
    
    def _get_enhanced_zone_info(self, polygon: Polygon2D) -> Dict[str, Any]:
        """
        Get enhanced information for a zone.
        
        Args:
            polygon: Polygon to get info for
            
        Returns:
            Dictionary with zone information
        """
        info = {}
        
        # Get room number (try different sources)
        room_number = None
        if hasattr(polygon, 'room_number') and polygon.room_number:
            room_number = str(polygon.room_number)
        elif polygon.space_name and polygon.space_name.strip():
            # Try to extract number from name
            name_parts = polygon.space_name.strip().split()
            if name_parts and name_parts[0].replace('.', '').replace('-', '').isdigit():
                room_number = name_parts[0]
        
        if room_number:
            info['room_number'] = room_number
        
        # Get zone name
        zone_name = polygon.space_name
        if zone_name and zone_name.strip():
            # Clean up the name
            zone_name = zone_name.strip()
            # If name starts with number, remove it for display
            if room_number and zone_name.startswith(room_number):
                zone_name = zone_name[len(room_number):].strip()
                if zone_name.startswith('-') or zone_name.startswith('.'):
                    zone_name = zone_name[1:].strip()
            
            # Limit length for display
            if len(zone_name) > 20:
                zone_name = zone_name[:17] + "..."
            
            if zone_name:
                info['zone_name'] = zone_name
        
        # Get floor area
        area = polygon.get_area()
        if area > 0:
            info['floor_area'] = area
        
        return info
    
    def _draw_multi_line_label_with_background(self, painter: QPainter, position: QPointF, label_lines: List[Dict[str, Any]]) -> None:
        """
        Draw multi-line label with enhanced background and styling.
        
        Args:
            painter: QPainter instance
            position: Position to draw label
            label_lines: List of line dictionaries with text, font_size, bold, color
        """
        if not label_lines:
            return
        
        # Calculate total dimensions
        total_height = 0
        max_width = 0
        line_heights = []
        
        for line_info in label_lines:
            font = QFont("Arial", line_info['font_size'])
            font.setBold(line_info.get('bold', False))
            
            metrics = QFontMetrics(font)
            line_height = metrics.height()
            line_width = metrics.horizontalAdvance(line_info['text'])
            
            line_heights.append(line_height)
            total_height += line_height
            max_width = max(max_width, line_width)
        
        # Add spacing between lines
        line_spacing = 2
        total_height += line_spacing * (len(label_lines) - 1)
        
        # Create enhanced background
        padding = 6
        bg_rect = QRectF(
            position.x() - max_width / 2 - padding,
            position.y() - total_height / 2 - padding,
            max_width + 2 * padding,
            total_height + 2 * padding
        )
        
        # Draw background with subtle gradient effect
        bg_color = self.COLOR_ZONE_TEXT_BACKGROUND
        painter.fillRect(bg_rect, bg_color)
        
        # Draw enhanced border
        border_pen = QPen(QColor(150, 150, 150), 1.5 / max(0.5, self.zoom_level))
        painter.setPen(border_pen)
        painter.drawRect(bg_rect)
        
        # Draw each line
        current_y = position.y() - total_height / 2
        
        for i, line_info in enumerate(label_lines):
            font = QFont("Arial", line_info['font_size'])
            font.setBold(line_info.get('bold', False))
            painter.setFont(font)
            
            # Set text color
            text_color = line_info.get('color', self.COLOR_ZONE_TEXT)
            painter.setPen(QPen(text_color))
            
            # Calculate line position
            metrics = QFontMetrics(font)
            line_width = metrics.horizontalAdvance(line_info['text'])
            line_height = line_heights[i]
            
            line_x = position.x() - line_width / 2
            line_y = current_y + line_height * 0.8  # Adjust for baseline
            
            # Draw text
            painter.drawText(QPointF(line_x, line_y), line_info['text'])
            
            # Move to next line
            current_y += line_height + line_spacing
    
    def _should_show_labels(self) -> bool:
        """Enhanced label visibility logic."""
        # Show labels at lower zoom levels than default
        min_zoom_for_labels = 0.2
        return (self.show_zone_names or self.show_room_numbers or self.show_floor_areas) and \
               self.zoom_level >= min_zoom_for_labels
    
    def _should_show_detailed_labels(self) -> bool:
        """Check if detailed labels should be shown."""
        return self.zoom_level >= 0.6


class EnhancedFloorPlanTestWindow(QMainWindow):
    """Test window for enhanced floor plan visualization."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Enhanced 2D Floor Plan Visualization")
        self.setGeometry(100, 100, 1400, 900)
        
        self.floor_geometries = {}
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the test UI."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        # Status and controls
        self.status_label = QLabel("Enhanced 2D Floor Plan - Load an IFC file to begin")
        layout.addWidget(self.status_label)
        
        # Control buttons
        controls_layout = QVBoxLayout()
        
        load_akkord_btn = QPushButton("Load AkkordSvingen 23_ARK.ifc")
        load_akkord_btn.clicked.connect(lambda: self.load_test_file("tesfiler/AkkordSvingen 23_ARK.ifc"))
        controls_layout.addWidget(load_akkord_btn)
        
        load_deich_btn = QPushButton("Load DEICH_Test.ifc")
        load_deich_btn.clicked.connect(lambda: self.load_test_file("tesfiler/DEICH_Test.ifc"))
        controls_layout.addWidget(load_deich_btn)
        
        # Display options
        self.toggle_names_btn = QPushButton("Toggle Zone Names")
        self.toggle_names_btn.clicked.connect(self.toggle_zone_names)
        controls_layout.addWidget(self.toggle_names_btn)
        
        self.toggle_areas_btn = QPushButton("Toggle Floor Areas")
        self.toggle_areas_btn.clicked.connect(self.toggle_floor_areas)
        controls_layout.addWidget(self.toggle_areas_btn)
        
        layout.addLayout(controls_layout)
        
        # Enhanced floor plan canvas
        self.enhanced_canvas = EnhancedFloorPlanCanvas()
        layout.addWidget(self.enhanced_canvas, 1)
        
        # Connect signals
        self.enhanced_canvas.room_clicked.connect(self.on_room_clicked)
        self.enhanced_canvas.rooms_selection_changed.connect(self.on_selection_changed)
    
    def load_test_file(self, file_path: str):
        """Load and display a test IFC file."""
        try:
            self.status_label.setText(f"Loading {os.path.basename(file_path)}...")
            QApplication.processEvents()
            
            # Import here to avoid circular imports
            from ifc_room_schedule.parser.ifc_file_reader import IfcFileReader
            from ifc_room_schedule.visualization.geometry_extractor import GeometryExtractor
            
            # Load IFC file
            reader = IfcFileReader()
            success, message = reader.load_file(file_path)
            if not success:
                self.status_label.setText(f"Failed to load: {message}")
                return
            
            # Extract geometry
            extractor = GeometryExtractor()
            
            def progress_callback(status: str, progress: int):
                self.status_label.setText(f"{status} ({progress}%)")
                QApplication.processEvents()
            
            self.floor_geometries = extractor.extract_floor_geometry(
                reader.get_ifc_file(), 
                progress_callback=progress_callback
            )
            
            if not self.floor_geometries:
                self.status_label.setText("No geometry extracted")
                return
            
            # Set geometry in enhanced canvas
            self.enhanced_canvas.set_floor_geometries(self.floor_geometries)
            
            # Enable enhanced features
            self.enhanced_canvas.enable_ns3940_color_coding(True)
            self.enhanced_canvas.set_enhanced_display_options(
                show_zone_names=True,
                show_room_numbers=True,
                show_floor_areas=True,
                zone_name_font_size=12,
                area_font_size=10
            )
            
            # Zoom to fit
            self.enhanced_canvas.zoom_to_fit()
            
            # Show summary
            total_rooms = sum(geom.get_room_count() for geom in self.floor_geometries.values())
            self.status_label.setText(
                f"Loaded {os.path.basename(file_path)}: {len(self.floor_geometries)} floors, {total_rooms} rooms with enhanced visualization"
            )
            
        except Exception as e:
            self.status_label.setText(f"Error: {str(e)}")
    
    def toggle_zone_names(self):
        """Toggle zone name display."""
        current = self.enhanced_canvas.show_zone_names
        self.enhanced_canvas.set_enhanced_display_options(show_zone_names=not current)
        self.status_label.setText(f"Zone names: {'ON' if not current else 'OFF'}")
    
    def toggle_floor_areas(self):
        """Toggle floor area display."""
        current = self.enhanced_canvas.show_floor_areas
        self.enhanced_canvas.set_enhanced_display_options(show_floor_areas=not current)
        self.status_label.setText(f"Floor areas: {'ON' if not current else 'OFF'}")
    
    def on_room_clicked(self, room_guid: str, ctrl_pressed: bool):
        """Handle room click."""
        modifier = " (Ctrl)" if ctrl_pressed else ""
        self.status_label.setText(f"Room clicked: {room_guid[:8]}...{modifier}")
    
    def on_selection_changed(self, room_guids: List[str]):
        """Handle selection change."""
        count = len(room_guids)
        if count == 0:
            self.status_label.setText("No rooms selected")
        elif count == 1:
            self.status_label.setText(f"1 room selected: {room_guids[0][:8]}...")
        else:
            self.status_label.setText(f"{count} rooms selected")


def main():
    """Main function to run enhanced floor plan test."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    window = EnhancedFloorPlanTestWindow()
    window.show()
    
    app.exec()


if __name__ == "__main__":
    main()