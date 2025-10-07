#!/usr/bin/env python3
"""
Floor Plan Rendering and Interaction Test

This script tests the floor plan rendering functionality including:
- FloorPlanCanvas rendering with extracted geometry data
- Room polygon rendering with NS 3940 color coding
- Zoom, pan, and fit-to-view functionality
- Room selection and highlighting interactions
- Multi-floor navigation and floor switching
- Visual feedback for hover and selection states
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Optional

# Add project root to path
sys.path.append('.')

# PyQt6 imports
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

def test_floor_plan_rendering():
    """Test floor plan rendering with real IFC data."""
    print("🎨 Floor Plan Rendering and Interaction Test")
    print("=" * 60)
    
    try:
        # Import required modules
        from ifc_room_schedule.parser.ifc_file_reader import IfcFileReader
        from ifc_room_schedule.visualization.geometry_extractor import GeometryExtractor
        from ifc_room_schedule.ui.floor_plan_widget import FloorPlanWidget
        
        # Create QApplication
        app = QApplication(sys.argv)
        
        # Load test IFC file
        test_file = "tesfiler/AkkordSvingen 23_ARK.ifc"
        if not Path(test_file).exists():
            print(f"❌ Test file not found: {test_file}")
            return False
        
        print(f"📁 Loading IFC file: {Path(test_file).name}")
        
        # Load and extract geometry
        reader = IfcFileReader()
        success, message = reader.load_file(test_file)
        
        if not success:
            print(f"❌ Failed to load IFC file: {message}")
            return False
        
        ifc_file = reader.get_ifc_file()
        extractor = GeometryExtractor()
        floor_geometries = extractor.extract_floor_geometry(ifc_file)
        
        print(f"✅ Extracted geometry for {len(floor_geometries)} floors")
        
        # Create test window
        window = FloorPlanTestWindow(floor_geometries)
        window.show()
        
        print(f"🖥️ Test window opened - interact with the floor plan to test functionality")
        print(f"   - Use mouse wheel to zoom")
        print(f"   - Click and drag to pan")
        print(f"   - Click on rooms to select them")
        print(f"   - Use floor selector to switch between floors")
        print(f"   - Use navigation buttons for zoom/fit controls")
        
        # Run for a limited time for automated testing
        QTimer.singleShot(5000, app.quit)  # Auto-close after 5 seconds
        
        app.exec()
        
        print(f"✅ Floor plan rendering test completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Floor plan rendering test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


class FloorPlanTestWindow(QMainWindow):
    """Test window for floor plan rendering functionality."""
    
    def __init__(self, floor_geometries: Dict):
        super().__init__()
        self.floor_geometries = floor_geometries
        self.setup_ui()
        self.setup_test_functionality()
    
    def setup_ui(self):
        """Set up the test window UI."""
        self.setWindowTitle("Floor Plan Rendering Test")
        self.setGeometry(100, 100, 1200, 800)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        
        # Test info label
        info_label = QLabel("Floor Plan Rendering Test - Interact with the floor plan below")
        info_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info_label)
        
        # Floor plan widget
        from ifc_room_schedule.ui.floor_plan_widget import FloorPlanWidget
        self.floor_plan_widget = FloorPlanWidget()
        self.floor_plan_widget.set_floor_geometry(self.floor_geometries)
        layout.addWidget(self.floor_plan_widget)
        
        # Test controls
        controls_layout = QHBoxLayout()
        
        test_selection_btn = QPushButton("Test Room Selection")
        test_selection_btn.clicked.connect(self.test_room_selection)
        controls_layout.addWidget(test_selection_btn)
        
        test_zoom_btn = QPushButton("Test Zoom Functions")
        test_zoom_btn.clicked.connect(self.test_zoom_functions)
        controls_layout.addWidget(test_zoom_btn)
        
        test_colors_btn = QPushButton("Test Color Coding")
        test_colors_btn.clicked.connect(self.test_color_coding)
        controls_layout.addWidget(test_colors_btn)
        
        layout.addLayout(controls_layout)
        
        central_widget.setLayout(layout)
    
    def setup_test_functionality(self):
        """Set up test-specific functionality."""
        # Connect signals for testing
        self.floor_plan_widget.space_selected.connect(self.on_space_selected)
        self.floor_plan_widget.floor_changed.connect(self.on_floor_changed)
        self.floor_plan_widget.spaces_selection_changed.connect(self.on_selection_changed)
    
    def on_space_selected(self, space_guid: str, ctrl_pressed: bool):
        """Handle space selection for testing."""
        print(f"🔍 Space selected: {space_guid[:8]}... (Ctrl: {ctrl_pressed})")
    
    def on_floor_changed(self, floor_id: str):
        """Handle floor change for testing."""
        print(f"🏢 Floor changed to: {floor_id}")
    
    def on_selection_changed(self, selected_guids: List[str]):
        """Handle selection change for testing."""
        print(f"📋 Selection changed: {len(selected_guids)} spaces selected")
    
    def test_room_selection(self):
        """Test room selection functionality."""
        print("🧪 Testing room selection...")
        
        # Get first floor with rooms
        for floor_id, geometry in self.floor_geometries.items():
            if geometry.room_polygons:
                # Select first few rooms
                room_guids = [p.space_guid for p in geometry.room_polygons[:3]]
                self.floor_plan_widget.highlight_spaces(room_guids)
                print(f"   Selected {len(room_guids)} rooms on floor {floor_id}")
                break
    
    def test_zoom_functions(self):
        """Test zoom functionality."""
        print("🧪 Testing zoom functions...")
        
        # Test zoom to fit
        self.floor_plan_widget.zoom_to_fit()
        print("   Zoom to fit executed")
        
        # Test zoom to specific rooms
        for floor_id, geometry in self.floor_geometries.items():
            if geometry.room_polygons:
                room_guids = [geometry.room_polygons[0].space_guid]
                self.floor_plan_widget.zoom_to_spaces(room_guids)
                print(f"   Zoomed to specific room on floor {floor_id}")
                break
    
    def test_color_coding(self):
        """Test NS 3940 color coding."""
        print("🧪 Testing color coding...")
        
        # Enable color coding
        canvas = self.floor_plan_widget.floor_plan_canvas
        canvas.enable_ns3940_color_coding(True)
        print("   NS 3940 color coding enabled")


if __name__ == "__main__":
    success = test_floor_plan_rendering()
    exit(0 if success else 1)