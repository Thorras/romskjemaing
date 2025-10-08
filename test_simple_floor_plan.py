#!/usr/bin/env python3
"""
Simple test for 2D floor plan visualization
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from ifc_room_schedule.visualization.floor_plan_canvas import FloorPlanCanvas
from ifc_room_schedule.visualization.geometry_models import Point2D, Polygon2D, FloorGeometry, FloorLevel

def create_test_geometry():
    """Create simple test geometry for visualization."""
    # Create a simple floor level
    floor_level = FloorLevel(
        id="test_floor",
        name="Test Floor",
        elevation=0.0,
        spaces=["room1", "room2", "room3"]
    )
    
    # Create simple room polygons
    room1 = Polygon2D(
        points=[
            Point2D(0, 0),
            Point2D(10, 0),
            Point2D(10, 8),
            Point2D(0, 8),
            Point2D(0, 0)
        ],
        space_guid="room1",
        space_name="Room 1"
    )
    
    room2 = Polygon2D(
        points=[
            Point2D(12, 0),
            Point2D(20, 0),
            Point2D(20, 6),
            Point2D(12, 6),
            Point2D(12, 0)
        ],
        space_guid="room2",
        space_name="Room 2"
    )
    
    room3 = Polygon2D(
        points=[
            Point2D(0, 10),
            Point2D(15, 10),
            Point2D(15, 15),
            Point2D(0, 15),
            Point2D(0, 10)
        ],
        space_guid="room3",
        space_name="Room 3"
    )
    
    # Create floor geometry
    floor_geometry = FloorGeometry(
        level=floor_level,
        room_polygons=[room1, room2, room3]
    )
    
    return floor_geometry

class SimpleFloorPlanWindow(QMainWindow):
    """Simple window to test floor plan visualization."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simple Floor Plan Test")
        self.setGeometry(100, 100, 800, 600)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create layout
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        # Create floor plan canvas
        self.floor_plan_canvas = FloorPlanCanvas()
        layout.addWidget(self.floor_plan_canvas)
        
        # Set test geometry
        test_geometry = create_test_geometry()
        self.floor_plan_canvas.set_floor_geometry(test_geometry)
        
        print(f"Created test geometry with {len(test_geometry.room_polygons)} rooms")
        print(f"Floor bounds: {test_geometry.bounds}")

def main():
    """Run the simple floor plan test."""
    app = QApplication(sys.argv)
    
    window = SimpleFloorPlanWindow()
    window.show()
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())