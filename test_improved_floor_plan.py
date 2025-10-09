#!/usr/bin/env python3
"""
Test script for improved 2D floor plan visualization
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QHBoxLayout, QPushButton
from PyQt6.QtCore import Qt

from ifc_room_schedule.ui.floor_plan_widget import FloorPlanWidget
from ifc_room_schedule.parser.ifc_file_reader import IfcFileReader
from ifc_room_schedule.visualization.geometry_extractor import GeometryExtractor


class ImprovedFloorPlanTestWindow(QMainWindow):
    """Test window for improved floor plan visualization."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Improved 2D Floor Plan - ArchiCAD Style")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        # Add control buttons
        controls_layout = QHBoxLayout()
        
        self.load_btn = QPushButton("Load IFC File")
        self.load_btn.clicked.connect(self.load_ifc_file)
        controls_layout.addWidget(self.load_btn)
        
        self.style_btn = QPushButton("Toggle Style")
        self.style_btn.clicked.connect(self.toggle_style)
        controls_layout.addWidget(self.style_btn)
        
        self.areas_btn = QPushButton("Toggle Areas")
        self.areas_btn.clicked.connect(self.toggle_areas)
        controls_layout.addWidget(self.areas_btn)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        # Add floor plan widget
        self.floor_plan_widget = FloorPlanWidget()
        layout.addWidget(self.floor_plan_widget, 1)
        
        # Load test file automatically
        self.load_ifc_file()
    
    def load_ifc_file(self):
        """Load test IFC file."""
        test_file = "tesfiler/AkkordSvingen 23_ARK.ifc"
        
        if not os.path.exists(test_file):
            print(f"Test file not found: {test_file}")
            return
        
        print(f"Loading IFC file: {test_file}")
        
        # Load IFC file
        ifc_reader = IfcFileReader()
        success, message = ifc_reader.load_file(test_file)
        
        if not success:
            print(f"Failed to load IFC file: {message}")
            return
        
        print("✓ IFC file loaded successfully")
        
        # Extract geometry
        geometry_extractor = GeometryExtractor()
        floor_geometries = geometry_extractor.extract_floor_geometry(ifc_reader.get_ifc_file())
        
        print(f"✓ Extracted geometry for {len(floor_geometries)} floors")
        
        # Set geometry in floor plan widget
        self.floor_plan_widget.set_floor_geometry(floor_geometries)
        
        print("✓ Floor plan updated with new geometry")
    
    def toggle_style(self):
        """Toggle between professional and colored style."""
        canvas = self.floor_plan_widget.floor_plan_canvas
        current_style = canvas.use_professional_style
        canvas.set_professional_style(not current_style)
        
        style_name = "Colored" if current_style else "Professional"
        print(f"Switched to {style_name} style")
    
    def toggle_areas(self):
        """Toggle room area display."""
        canvas = self.floor_plan_widget.floor_plan_canvas
        current_areas = canvas.show_room_areas
        canvas.set_show_room_areas(not current_areas)
        
        areas_status = "hidden" if current_areas else "shown"
        print(f"Room areas {areas_status}")


def main():
    """Run the improved floor plan test."""
    app = QApplication(sys.argv)
    
    window = ImprovedFloorPlanTestWindow()
    window.show()
    
    print("\n" + "="*60)
    print("IMPROVED 2D FLOOR PLAN TEST")
    print("="*60)
    print("Features:")
    print("- Professional ArchiCAD-style drawing")
    print("- Clean black borders, no fill by default")
    print("- Professional grid overlay")
    print("- Room numbers, names, and areas")
    print("- Scale indicator and north arrow")
    print("- Toggle between professional and colored styles")
    print("- Enhanced typography and labeling")
    print("\nControls:")
    print("- Mouse wheel: Zoom")
    print("- Left click + drag: Pan")
    print("- Left click on room: Select")
    print("- Ctrl+Left click: Multi-select")
    print("- Ctrl+0: Zoom to fit")
    print("- Escape: Clear selection")
    print("="*60)
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())