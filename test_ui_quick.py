#!/usr/bin/env python3
"""
Quick test to verify space boundary UI improvements
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from ifc_room_schedule.parser.ifc_file_reader import IfcFileReader
from ifc_room_schedule.parser.ifc_space_extractor import IfcSpaceExtractor
from ifc_room_schedule.parser.ifc_space_boundary_parser import IfcSpaceBoundaryParser
from ifc_room_schedule.ui.space_detail_widget import SpaceDetailWidget
from PyQt6.QtWidgets import QApplication

def test_ui_quick():
    """Quick test of the UI improvements."""
    
    app = QApplication(sys.argv)
    
    # Load test data
    test_file = "tesfiler/AkkordSvingen 23_ARK.ifc"
    
    if not os.path.exists(test_file):
        print(f"Test file not found: {test_file}")
        return
    
    # Load IFC file
    reader = IfcFileReader()
    success, message = reader.load_file(test_file)
    
    if not success:
        print(f"Failed to load IFC file: {message}")
        return
    
    # Extract spaces
    space_extractor = IfcSpaceExtractor()
    space_extractor.set_ifc_file(reader.get_ifc_file())
    spaces = space_extractor.extract_spaces()
    
    if not spaces:
        print("No spaces found")
        return
    
    # Extract boundaries for first space
    boundary_parser = IfcSpaceBoundaryParser()
    boundary_parser.set_ifc_file(reader.get_ifc_file())
    
    first_space = spaces[0]
    boundaries = boundary_parser.get_boundaries_for_space(first_space.guid)
    
    # Add boundaries to space
    for boundary in boundaries:
        first_space.add_space_boundary(boundary)
    
    # Create and show space detail widget
    detail_widget = SpaceDetailWidget()
    detail_widget.display_space(first_space)
    detail_widget.show()
    
    print(f"Showing space details for: {first_space.number} with {len(boundaries)} boundaries")
    
    # Run the application
    sys.exit(app.exec())

if __name__ == "__main__":
    test_ui_quick()