#!/usr/bin/env python3
"""
Test script for floor plan rendering and interaction.

This script tests the FloorPlanCanvas and FloorPlanWidget components
to verify that 2D floor plan rendering and user interactions work correctly.
"""

import sys
import os
import time
from pathlib import Path
from typing import Dict, List, Any

# Add project root to path
sys.path.append('.')

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QPainter

from ifc_room_schedule.parser.ifc_file_reader import IfcFileReader
from ifc_room_schedule.visualization.geometry_extractor import GeometryExtractor
from ifc_room_schedule.visualization.floor_plan_canvas import FloorPlanCanvas
from ifc_room_schedule.ui.floor_plan_widget import FloorPlanWidget


class FloorPlanTestWindow(QMainWindow):
    """Test window for floor plan rendering and interaction."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Floor Plan Rendering Test")
        self.setGeometry(100, 100, 1200, 800)
        
        # Test data
        self.floor_geometries = {}
        self.current_test_file = None
        
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the test UI."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        # Status label
        self.status_label = QLabel("Ready to test floor plan rendering...")
        layout.addWidget(self.status_label)
        
        # Test buttons
        button_layout = QVBoxLayout()
        
        self.load_akkord_btn = QPushButton("Load AkkordSvingen 23_ARK.ifc")
        self.load_akkord_btn.clicked.connect(lambda: self.load_test_file("tesfiler/AkkordSvingen 23_ARK.ifc"))
        button_layout.addWidget(self.load_akkord_btn)
        
        self.load_deich_btn = QPushButton("Load DEICH_Test.ifc")
        self.load_deich_btn.clicked.connect(lambda: self.load_test_file("tesfiler/DEICH_Test.ifc"))
        button_layout.addWidget(self.load_deich_btn)
        
        self.test_rendering_btn = QPushButton("Test Floor Plan Rendering")
        self.test_rendering_btn.clicked.connect(self.test_rendering)
        self.test_rendering_btn.setEnabled(False)
        button_layout.addWidget(self.test_rendering_btn)
        
        self.test_interaction_btn = QPushButton("Test User Interactions")
        self.test_interaction_btn.clicked.connect(self.test_interactions)
        self.test_interaction_btn.setEnabled(False)
        button_layout.addWidget(self.test_interaction_btn)
        
        layout.addLayout(button_layout)
        
        # Floor plan widget
        self.floor_plan_widget = FloorPlanWidget()
        layout.addWidget(self.floor_plan_widget, 1)  # Give it stretch
        
        # Connect signals
        self.floor_plan_widget.space_selected.connect(self.on_space_selected)
        self.floor_plan_widget.floor_changed.connect(self.on_floor_changed)
        self.floor_plan_widget.spaces_selection_changed.connect(self.on_spaces_selection_changed)
    
    def load_test_file(self, file_path: str):
        """Load a test IFC file and extract geometry."""
        try:
            self.status_label.setText(f"Loading {Path(file_path).name}...")
            QApplication.processEvents()
            
            # Load IFC file
            reader = IfcFileReader()
            success, message = reader.load_file(file_path)
            if not success:
                self.status_label.setText(f"Failed to load IFC file: {message}")
                return
            
            # Extract geometry
            geometry_extractor = GeometryExtractor()
            
            def progress_callback(status: str, progress: int):
                self.status_label.setText(f"{status} ({progress}%)")
                QApplication.processEvents()
            
            self.floor_geometries = geometry_extractor.extract_floor_geometry(
                reader.get_ifc_file(), 
                progress_callback=progress_callback
            )
            
            if not self.floor_geometries:
                self.status_label.setText("No floor geometry extracted")
                return
            
            # Set geometry in floor plan widget
            self.floor_plan_widget.set_floor_geometry(self.floor_geometries)
            
            self.current_test_file = file_path
            self.test_rendering_btn.setEnabled(True)
            self.test_interaction_btn.setEnabled(True)
            
            # Show summary
            total_rooms = sum(geom.get_room_count() for geom in self.floor_geometries.values())
            self.status_label.setText(
                f"Loaded {Path(file_path).name}: {len(self.floor_geometries)} floors, {total_rooms} rooms"
            )
            
        except Exception as e:
            self.status_label.setText(f"Error loading file: {str(e)}")
    
    def test_rendering(self):
        """Test floor plan rendering functionality."""
        if not self.floor_geometries:
            self.status_label.setText("No geometry data loaded")
            return
        
        try:
            self.status_label.setText("Testing floor plan rendering...")
            
            # Test 1: Basic rendering
            canvas = self.floor_plan_widget.floor_plan_canvas
            
            # Check if canvas has geometry
            if not canvas.floor_geometries:
                self.status_label.setText("❌ Canvas has no geometry data")
                return
            
            # Test 2: Color coding
            canvas.enable_ns3940_color_coding(True)
            self.status_label.setText("✓ NS 3940 color coding enabled")
            QApplication.processEvents()
            time.sleep(1)
            
            # Test 3: Label visibility
            canvas.set_label_visibility(True, True)
            self.status_label.setText("✓ Room labels enabled")
            QApplication.processEvents()
            time.sleep(1)
            
            # Test 4: Zoom to fit
            canvas.zoom_to_fit()
            self.status_label.setText("✓ Zoom to fit tested")
            QApplication.processEvents()
            time.sleep(1)
            
            # Test 5: Floor switching (if multiple floors)
            available_floors = canvas.get_available_floors()
            if len(available_floors) > 1:
                for floor_id in available_floors[:2]:  # Test first 2 floors
                    canvas.set_current_floor(floor_id)
                    self.status_label.setText(f"✓ Switched to floor: {floor_id}")
                    QApplication.processEvents()
                    time.sleep(1)
            
            self.status_label.setText("✅ Floor plan rendering tests completed successfully!")
            
        except Exception as e:
            self.status_label.setText(f"❌ Rendering test failed: {str(e)}")
    
    def test_interactions(self):
        """Test user interaction functionality."""
        if not self.floor_geometries:
            self.status_label.setText("No geometry data loaded")
            return
        
        try:
            self.status_label.setText("Testing user interactions...")
            
            canvas = self.floor_plan_widget.floor_plan_canvas
            
            # Test 1: Room selection
            if canvas.floor_geometry and canvas.floor_geometry.room_polygons:
                # Select first room
                first_room = canvas.floor_geometry.room_polygons[0]
                canvas.highlight_rooms([first_room.space_guid])
                self.status_label.setText(f"✓ Selected room: {first_room.space_name}")
                QApplication.processEvents()
                time.sleep(1)
                
                # Test multi-selection
                if len(canvas.floor_geometry.room_polygons) > 1:
                    second_room = canvas.floor_geometry.room_polygons[1]
                    canvas.highlight_rooms([first_room.space_guid, second_room.space_guid])
                    self.status_label.setText("✓ Multi-room selection tested")
                    QApplication.processEvents()
                    time.sleep(1)
                
                # Clear selection
                canvas.clear_selection()
                self.status_label.setText("✓ Selection cleared")
                QApplication.processEvents()
                time.sleep(1)
            
            # Test 2: Zoom operations
            canvas.zoom_level = 2.0
            canvas._update_view_transform()
            canvas.update()
            self.status_label.setText("✓ Zoom in tested")
            QApplication.processEvents()
            time.sleep(1)
            
            canvas.zoom_level = 0.5
            canvas._update_view_transform()
            canvas.update()
            self.status_label.setText("✓ Zoom out tested")
            QApplication.processEvents()
            time.sleep(1)
            
            # Test 3: Zoom to specific rooms
            if canvas.floor_geometry and canvas.floor_geometry.room_polygons:
                test_rooms = canvas.floor_geometry.room_polygons[:3]  # First 3 rooms
                room_guids = [room.space_guid for room in test_rooms]
                canvas.zoom_to_rooms(room_guids)
                self.status_label.setText("✓ Zoom to specific rooms tested")
                QApplication.processEvents()
                time.sleep(1)
            
            # Test 4: Reset view
            canvas.zoom_to_fit()
            self.status_label.setText("✓ Reset view tested")
            QApplication.processEvents()
            time.sleep(1)
            
            self.status_label.setText("✅ User interaction tests completed successfully!")
            
        except Exception as e:
            self.status_label.setText(f"❌ Interaction test failed: {str(e)}")
    
    def on_space_selected(self, space_guid: str, ctrl_pressed: bool):
        """Handle space selection from floor plan."""
        modifier = " (Ctrl)" if ctrl_pressed else ""
        self.status_label.setText(f"Space selected: {space_guid[:8]}...{modifier}")
    
    def on_floor_changed(self, floor_id: str):
        """Handle floor change."""
        self.status_label.setText(f"Floor changed to: {floor_id}")
    
    def on_spaces_selection_changed(self, space_guids: List[str]):
        """Handle selection change."""
        count = len(space_guids)
        if count == 0:
            self.status_label.setText("Selection cleared")
        elif count == 1:
            self.status_label.setText(f"1 space selected: {space_guids[0][:8]}...")
        else:
            self.status_label.setText(f"{count} spaces selected")


def test_floor_plan_canvas_basic():
    """Test basic FloorPlanCanvas functionality without GUI."""
    print("Testing FloorPlanCanvas basic functionality...")
    
    try:
        # Create QApplication
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        # Create canvas
        canvas = FloorPlanCanvas()
        print("✓ FloorPlanCanvas created successfully")
        
        # Test basic properties
        assert canvas.zoom_level == 1.0
        assert canvas.min_zoom == 0.1
        assert canvas.max_zoom == 10.0
        print("✓ Basic properties are correct")
        
        # Test color scheme
        canvas.enable_ns3940_color_coding(True)
        print("✓ NS 3940 color coding enabled")
        
        # Test label settings
        canvas.set_label_visibility(True, True)
        canvas.set_label_font_size(12)
        print("✓ Label settings configured")
        
        print("✅ FloorPlanCanvas basic tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ FloorPlanCanvas basic test failed: {str(e)}")
        return False


def test_floor_plan_widget_basic():
    """Test basic FloorPlanWidget functionality without GUI."""
    print("Testing FloorPlanWidget basic functionality...")
    
    try:
        # Create QApplication
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        # Create widget
        widget = FloorPlanWidget()
        print("✓ FloorPlanWidget created successfully")
        
        # Test basic properties
        assert widget.floor_plan_canvas is not None
        assert widget.floor_selector is not None
        assert widget.navigation_controls is not None
        print("✓ All sub-components exist")
        
        # Test empty state
        assert widget.get_current_floor_id() is None
        print("✓ Empty state is correct")
        
        print("✅ FloorPlanWidget basic tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ FloorPlanWidget basic test failed: {str(e)}")
        return False


def main():
    """Main test function."""
    print("Floor Plan Rendering and Interaction Test Suite")
    print("=" * 60)
    
    # Test 1: Basic component tests (no GUI)
    print("\n1. Testing basic component functionality...")
    canvas_test = test_floor_plan_canvas_basic()
    widget_test = test_floor_plan_widget_basic()
    
    if not (canvas_test and widget_test):
        print("❌ Basic component tests failed!")
        return False
    
    # Test 2: Interactive GUI tests
    print("\n2. Starting interactive GUI tests...")
    print("   - A test window will open")
    print("   - Click 'Load AkkordSvingen 23_ARK.ifc' or 'Load DEICH_Test.ifc'")
    print("   - Then click 'Test Floor Plan Rendering' and 'Test User Interactions'")
    print("   - Close the window when done")
    
    try:
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # Create test window
        window = FloorPlanTestWindow()
        window.show()
        
        # Set up auto-close timer (optional, for automated testing)
        if "--auto-close" in sys.argv:
            timer = QTimer()
            timer.timeout.connect(window.close)
            timer.start(10000)  # Close after 10 seconds
        
        # Run the application
        app.exec()
        
        print("✅ Interactive GUI tests completed!")
        return True
        
    except Exception as e:
        print(f"❌ Interactive GUI test failed: {str(e)}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)