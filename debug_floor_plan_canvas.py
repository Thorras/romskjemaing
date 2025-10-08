#!/usr/bin/env python3
"""
Debug version of floor plan canvas to identify rendering issues
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QPolygonF

from ifc_room_schedule.visualization.geometry_models import Point2D, Polygon2D, FloorGeometry, FloorLevel

class DebugFloorPlanCanvas(QWidget):
    """Simplified floor plan canvas for debugging."""
    
    def __init__(self):
        super().__init__()
        self.floor_geometry = None
        self.setMinimumSize(400, 300)
        
    def set_floor_geometry(self, geometry):
        """Set floor geometry."""
        self.floor_geometry = geometry
        print(f"Set floor geometry with {len(geometry.room_polygons)} rooms")
        for i, room in enumerate(geometry.room_polygons):
            bounds = room.get_bounds()
            print(f"  Room {i}: {room.space_name} - bounds: {bounds}")
        self.update()
    
    def paintEvent(self, event):
        """Paint the floor plan."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Clear background
        painter.fillRect(self.rect(), QColor(250, 250, 250))
        
        print(f"Paint event called - widget size: {self.width()}x{self.height()}")
        
        if not self.floor_geometry:
            painter.setPen(QPen(QColor(100, 100, 100)))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "No floor geometry")
            print("No floor geometry to draw")
            return
        
        print(f"Drawing {len(self.floor_geometry.room_polygons)} rooms")
        
        # Calculate bounds and scaling
        if self.floor_geometry.bounds:
            bounds = self.floor_geometry.bounds
            floor_width = bounds[2] - bounds[0]
            floor_height = bounds[3] - bounds[1]
            
            # Calculate scale to fit in widget
            margin = 50
            scale_x = (self.width() - 2 * margin) / floor_width if floor_width > 0 else 1
            scale_y = (self.height() - 2 * margin) / floor_height if floor_height > 0 else 1
            scale = min(scale_x, scale_y)
            
            # Calculate offset to center
            offset_x = margin + (self.width() - 2 * margin - floor_width * scale) / 2
            offset_y = margin + (self.height() - 2 * margin - floor_height * scale) / 2
            
            print(f"Floor bounds: {bounds}")
            print(f"Scale: {scale}, Offset: ({offset_x}, {offset_y})")
            
            # Draw rooms
            colors = [
                QColor(173, 216, 230, 180),  # Light blue
                QColor(144, 238, 144, 180),  # Light green
                QColor(255, 218, 185, 180),  # Peach
                QColor(221, 160, 221, 180),  # Plum
                QColor(255, 255, 224, 180),  # Light yellow
            ]
            
            for i, room in enumerate(self.floor_geometry.room_polygons):
                # Create Qt polygon
                qt_polygon = QPolygonF()
                for point in room.points:
                    # Transform coordinates
                    x = (point.x - bounds[0]) * scale + offset_x
                    y = (point.y - bounds[1]) * scale + offset_y
                    qt_polygon.append(QPointF(x, y))
                
                # Draw room
                color = colors[i % len(colors)]
                painter.setBrush(QBrush(color))
                painter.setPen(QPen(QColor(0, 0, 0), 2))
                painter.drawPolygon(qt_polygon)
                
                # Draw room label
                centroid = room.get_centroid()
                label_x = (centroid.x - bounds[0]) * scale + offset_x
                label_y = (centroid.y - bounds[1]) * scale + offset_y
                
                painter.setPen(QPen(QColor(0, 0, 0)))
                painter.drawText(QPointF(label_x, label_y), room.space_name)
                
                print(f"Drew room {i}: {room.space_name} at polygon with {qt_polygon.size()} points")
        
        # Draw coordinate system for reference
        painter.setPen(QPen(QColor(255, 0, 0), 2))
        painter.drawLine(10, 10, 60, 10)  # X axis
        painter.drawLine(10, 10, 10, 60)  # Y axis
        painter.drawText(65, 15, "X")
        painter.drawText(15, 75, "Y")

def create_test_geometry():
    """Create simple test geometry."""
    floor_level = FloorLevel(
        id="test_floor",
        name="Test Floor", 
        elevation=0.0,
        spaces=["room1", "room2", "room3"]
    )
    
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
    
    return FloorGeometry(
        level=floor_level,
        room_polygons=[room1, room2, room3]
    )

class DebugWindow(QMainWindow):
    """Debug window."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Debug Floor Plan Canvas")
        self.setGeometry(100, 100, 800, 600)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        self.canvas = DebugFloorPlanCanvas()
        layout.addWidget(self.canvas)
        
        # Set test geometry
        test_geometry = create_test_geometry()
        self.canvas.set_floor_geometry(test_geometry)

def main():
    """Run debug test."""
    app = QApplication(sys.argv)
    
    window = DebugWindow()
    window.show()
    
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())