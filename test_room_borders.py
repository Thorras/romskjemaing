#!/usr/bin/env python3
"""
Test script to verify room borders are drawn correctly
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QPen, QColor

from ifc_room_schedule.visualization.floor_plan_canvas import FloorPlanCanvas
from ifc_room_schedule.visualization.geometry_models import FloorLevel, FloorGeometry, Polygon2D, Point2D


def create_test_geometry():
    """Create simple test geometry with clear room boundaries."""
    floor_level = FloorLevel(
        id="test_floor",
        name="Test Floor", 
        elevation=0.0,
        spaces=["room1", "room2", "room3", "room4"]
    )
    
    # Create 4 rooms in a 2x2 grid pattern
    rooms = []
    
    # Room 1 (top-left)
    room1 = Polygon2D(
        points=[
            Point2D(0, 0),
            Point2D(10, 0),
            Point2D(10, 8),
            Point2D(0, 8),
            Point2D(0, 0)
        ],
        space_guid="room1",
        space_name="01 Stue"
    )
    rooms.append(room1)
    
    # Room 2 (top-right)
    room2 = Polygon2D(
        points=[
            Point2D(12, 0),
            Point2D(22, 0),
            Point2D(22, 8),
            Point2D(12, 8),
            Point2D(12, 0)
        ],
        space_guid="room2", 
        space_name="02 Sov"
    )
    rooms.append(room2)
    
    # Room 3 (bottom-left)
    room3 = Polygon2D(
        points=[
            Point2D(0, 10),
            Point2D(10, 10),
            Point2D(10, 18),
            Point2D(0, 18),
            Point2D(0, 10)
        ],
        space_guid="room3",
        space_name="03 Bad"
    )
    rooms.append(room3)
    
    # Room 4 (bottom-right)
    room4 = Polygon2D(
        points=[
            Point2D(12, 10),
            Point2D(22, 10),
            Point2D(22, 18),
            Point2D(12, 18),
            Point2D(12, 10)
        ],
        space_guid="room4",
        space_name="04 Gang"
    )
    rooms.append(room4)
    
    return FloorGeometry(
        level=floor_level,
        room_polygons=rooms,
        bounds=(0, 0, 22, 18)
    )


class BorderTestWindow(QMainWindow):
    """Test window for room border visualization."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Room Border Test - ArchiCAD Style")
        self.setGeometry(100, 100, 800, 600)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        # Create floor plan canvas
        self.canvas = FloorPlanCanvas()
        layout.addWidget(self.canvas)
        
        # Set test geometry
        test_geometry = create_test_geometry()
        self.canvas.set_floor_geometry(test_geometry)
        
        # Enable professional style to show borders clearly
        self.canvas.set_professional_style(True)
        
        print("Room Border Test:")
        print("- 4 rooms in 2x2 grid")
        print("- Black borders should be clearly visible")
        print("- No fill (transparent rooms)")
        print("- Professional ArchiCAD style")


def main():
    """Run the border test."""
    app = QApplication(sys.argv)
    
    window = BorderTestWindow()
    window.show()
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())