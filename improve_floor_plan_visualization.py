#!/usr/bin/env python3
"""
Script to improve the floor plan visualization by modifying the existing FloorPlanCanvas
to show zones as separate, non-overlapping rooms like on architectural drawings.
"""

import sys
import os

# Add project root to path
sys.path.append('.')

from ifc_room_schedule.visualization.floor_plan_canvas import FloorPlanCanvas


def patch_floor_plan_canvas():
    """
    Patch the existing FloorPlanCanvas to improve zone visualization.
    """
    
    # Store original methods
    original_draw_room_polygons = FloorPlanCanvas._draw_room_polygons
    original_draw_room_labels = FloorPlanCanvas._draw_room_labels
    original_get_space_label_text = FloorPlanCanvas._get_space_label_text
    
    def enhanced_draw_room_polygons(self, painter):
        """Enhanced room polygon drawing with clearer boundaries."""
        from PyQt6.QtGui import QPen, QBrush, QColor
        from PyQt6.QtCore import Qt
        
        # Enhanced visual constants
        ENHANCED_BORDER_WIDTH = 2.0  # Thicker borders
        ENHANCED_SELECTED_WIDTH = 3.5
        
        # Enhanced colors
        ENHANCED_BORDER_COLOR = QColor(40, 40, 40)  # Darker borders
        ENHANCED_SELECTED_COLOR = QColor(0, 120, 215)
        
        # Draw visible rooms with enhanced styling
        for polygon in self.visible_rooms:
            # Determine if room is selected
            is_selected = polygon.space_guid in self.selected_rooms
            is_hovered = polygon.space_guid == self.hovered_room
            
            # Set border style
            if is_selected:
                border_width = ENHANCED_SELECTED_WIDTH / max(0.5, self.zoom_level)
                border_color = ENHANCED_SELECTED_COLOR
            elif is_hovered:
                border_width = (ENHANCED_BORDER_WIDTH + 1.0) / max(0.5, self.zoom_level)
                border_color = QColor(0, 150, 255)
            else:
                border_width = ENHANCED_BORDER_WIDTH / max(0.5, self.zoom_level)
                border_color = ENHANCED_BORDER_COLOR
            
            # Set up pen with enhanced styling
            pen = QPen(border_color, border_width)
            pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
            painter.setPen(pen)
            
            # Get fill color with better contrast
            if self.use_color_coding:
                fill_color = self.get_space_color(polygon.space_guid)
                # Make fill more opaque for better visibility
                fill_color.setAlpha(150 if is_selected else 100)
            else:
                fill_color = QColor(245, 245, 245, 150 if is_selected else 100)
            
            brush = QBrush(fill_color)
            painter.setBrush(brush)
            
            # Draw the polygon
            qt_polygon = self._polygon_to_qt(polygon)
            painter.drawPolygon(qt_polygon)
    
    def enhanced_get_space_label_text(self, polygon, detailed=False):
        """Enhanced space label text with room number, name, and area."""
        parts = []
        
        # Get room number from name if possible
        room_number = None
        if polygon.space_name and polygon.space_name.strip():
            name_parts = polygon.space_name.strip().split()
            if name_parts:
                first_part = name_parts[0]
                # Check if first part looks like a room number
                if first_part.replace('.', '').replace('-', '').isdigit():
                    room_number = first_part
        
        # Add room number (prominent)
        if room_number:
            parts.append(room_number)
        
        # Add zone/room name
        if polygon.space_name and polygon.space_name.strip():
            name = polygon.space_name.strip()
            # Remove room number from name if it's at the beginning
            if room_number and name.startswith(room_number):
                name = name[len(room_number):].strip()
                if name.startswith('-') or name.startswith('.'):
                    name = name[1:].strip()
            
            if name:
                # Limit length for display
                if len(name) > 15 and not detailed:
                    name = name[:12] + "..."
                parts.append(name)
        
        # Add area information
        area = polygon.get_area()
        if area > 0:
            parts.append(f"{area:.1f} m²")
        
        # Fallback to GUID if no other info
        if not parts:
            parts.append(polygon.space_guid[:8])
        
        return "\n".join(parts)
    
    def enhanced_draw_room_labels(self, painter):
        """Enhanced room label drawing with better visibility."""
        if not self._should_show_labels():
            return
        
        from PyQt6.QtGui import QFont, QPen, QColor, QFontMetrics
        from PyQt6.QtCore import QPointF, QRectF
        
        # Enhanced label colors
        LABEL_TEXT_COLOR = QColor(20, 20, 20)  # Very dark text
        LABEL_BG_COLOR = QColor(255, 255, 255, 230)  # More opaque background
        LABEL_BORDER_COLOR = QColor(180, 180, 180)
        
        # Check if we should show detailed labels
        detailed = self._should_show_detailed_labels()
        
        # Draw labels for visible rooms
        for polygon in self.visible_rooms:
            centroid = polygon.get_centroid()
            label_point = QPointF(centroid.x, centroid.y)
            
            # Get enhanced label text
            label_text = self._get_space_label_text(polygon, detailed)
            
            if label_text:
                # Set up font (larger for better visibility)
                font_size = max(8, int(12 / max(0.7, self.zoom_level)))
                font = QFont("Arial", font_size)
                font.setBold(True)  # Bold for better visibility
                painter.setFont(font)
                
                # Calculate text dimensions
                font_metrics = QFontMetrics(font)
                lines = label_text.split('\n')
                line_height = font_metrics.height()
                max_width = max(font_metrics.horizontalAdvance(line) for line in lines)
                total_height = line_height * len(lines)
                
                # Create background rectangle with more padding
                padding = 8
                bg_rect = QRectF(
                    label_point.x() - max_width / 2 - padding,
                    label_point.y() - total_height / 2 - padding,
                    max_width + 2 * padding,
                    total_height + 2 * padding
                )
                
                # Draw enhanced background
                painter.fillRect(bg_rect, LABEL_BG_COLOR)
                
                # Draw border around background
                border_pen = QPen(LABEL_BORDER_COLOR, 1.5)
                painter.setPen(border_pen)
                painter.drawRect(bg_rect)
                
                # Draw text with enhanced styling
                painter.setPen(QPen(LABEL_TEXT_COLOR))
                
                # Draw each line
                for i, line in enumerate(lines):
                    line_y = label_point.y() - total_height / 2 + (i + 0.8) * line_height
                    line_x = label_point.x() - font_metrics.horizontalAdvance(line) / 2
                    painter.drawText(QPointF(line_x, line_y), line)
    
    # Apply patches
    FloorPlanCanvas._draw_room_polygons = enhanced_draw_room_polygons
    FloorPlanCanvas._draw_room_labels = enhanced_draw_room_labels
    FloorPlanCanvas._get_space_label_text = enhanced_get_space_label_text
    
    print("✓ FloorPlanCanvas patched with enhanced visualization")


def test_enhanced_visualization():
    """Test the enhanced visualization."""
    from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel
    from ifc_room_schedule.ui.floor_plan_widget import FloorPlanWidget
    from ifc_room_schedule.parser.ifc_file_reader import IfcFileReader
    from ifc_room_schedule.visualization.geometry_extractor import GeometryExtractor
    
    class TestWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("Enhanced Floor Plan Visualization Test")
            self.setGeometry(100, 100, 1400, 900)
            
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            
            layout = QVBoxLayout()
            central_widget.setLayout(layout)
            
            # Status
            self.status_label = QLabel("Enhanced visualization ready - Load an IFC file")
            layout.addWidget(self.status_label)
            
            # Load button
            load_btn = QPushButton("Load AkkordSvingen 23_ARK.ifc (Enhanced)")
            load_btn.clicked.connect(self.load_file)
            layout.addWidget(load_btn)
            
            # Floor plan widget
            self.floor_plan_widget = FloorPlanWidget()
            layout.addWidget(self.floor_plan_widget, 1)
            
            # Connect signals
            self.floor_plan_widget.space_selected.connect(self.on_space_selected)
        
        def load_file(self):
            try:
                self.status_label.setText("Loading with enhanced visualization...")
                QApplication.processEvents()
                
                # Load IFC file
                reader = IfcFileReader()
                success, message = reader.load_file("tesfiler/AkkordSvingen 23_ARK.ifc")
                if not success:
                    self.status_label.setText(f"Failed: {message}")
                    return
                
                # Extract geometry
                extractor = GeometryExtractor()
                floor_geometries = extractor.extract_floor_geometry(reader.get_ifc_file())
                
                if not floor_geometries:
                    self.status_label.setText("No geometry extracted")
                    return
                
                # Set in floor plan widget
                self.floor_plan_widget.set_floor_geometry(floor_geometries)
                
                # Enable enhanced features
                canvas = self.floor_plan_widget.floor_plan_canvas
                canvas.enable_ns3940_color_coding(True)
                canvas.set_label_visibility(True, True)
                canvas.zoom_to_fit()
                
                total_rooms = sum(geom.get_room_count() for geom in floor_geometries.values())
                self.status_label.setText(
                    f"Enhanced visualization: {len(floor_geometries)} floors, {total_rooms} rooms"
                )
                
            except Exception as e:
                self.status_label.setText(f"Error: {str(e)}")
        
        def on_space_selected(self, space_guid: str, ctrl_pressed: bool):
            self.status_label.setText(f"Selected room: {space_guid[:8]}...")
    
    # Apply patches first
    patch_floor_plan_canvas()
    
    # Create and run test
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    window = TestWindow()
    window.show()
    
    app.exec()


if __name__ == "__main__":
    test_enhanced_visualization()