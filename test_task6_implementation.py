#!/usr/bin/env python3
"""
Test script for Task 6.1: Space boundary data extraction and display
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from ifc_room_schedule.parser.ifc_file_reader import IfcFileReader
from ifc_room_schedule.parser.ifc_space_extractor import IfcSpaceExtractor
from ifc_room_schedule.parser.ifc_space_boundary_parser import IfcSpaceBoundaryParser

def test_space_boundary_extraction():
    """Test space boundary extraction with real IFC file."""
    
    # Test file path
    test_file = "tesfiler/AkkordSvingen 23_ARK.ifc"
    
    if not os.path.exists(test_file):
        print(f"Test file not found: {test_file}")
        return False
    
    print(f"Testing space boundary extraction with: {test_file}")
    
    # Load IFC file
    reader = IfcFileReader()
    success, message = reader.load_file(test_file)
    
    if not success:
        print(f"Failed to load IFC file: {message}")
        return False
    
    print("✓ IFC file loaded successfully")
    
    # Extract spaces first
    space_extractor = IfcSpaceExtractor()
    space_extractor.set_ifc_file(reader.get_ifc_file())
    spaces = space_extractor.extract_spaces()
    
    print(f"✓ Found {len(spaces)} spaces")
    
    if not spaces:
        print("No spaces found - cannot test boundary extraction")
        return False
    
    # Test space boundary extraction
    boundary_parser = IfcSpaceBoundaryParser()
    boundary_parser.set_ifc_file(reader.get_ifc_file())
    
    # Test extracting all boundaries
    all_boundaries = boundary_parser.extract_space_boundaries()
    print(f"✓ Found {len(all_boundaries)} total space boundaries")
    
    # Test extracting boundaries for specific spaces
    for i, space in enumerate(spaces[:3]):  # Test first 3 spaces
        print(f"\n--- Testing Space {i+1}: {space.number} ({space.name}) ---")
        
        boundaries = boundary_parser.get_boundaries_for_space(space.guid)
        print(f"  Boundaries found: {len(boundaries)}")
        
        if boundaries:
            for j, boundary in enumerate(boundaries[:2]):  # Show first 2 boundaries
                print(f"  Boundary {j+1}:")
                print(f"    GUID: {boundary.guid}")
                print(f"    Name: {boundary.name}")
                print(f"    Display Label: {boundary.display_label}")
                print(f"    Type: {boundary.physical_or_virtual_boundary}")
                print(f"    Internal/External: {boundary.internal_or_external_boundary}")
                print(f"    Surface Type: {boundary.boundary_surface_type}")
                print(f"    Orientation: {boundary.boundary_orientation}")
                print(f"    Area: {boundary.calculated_area:.2f} m²")
                print(f"    Element Type: {boundary.related_building_element_type}")
                print(f"    Level: {boundary.boundary_level}")
                
                # Test boundary classification methods
                print(f"    Is Physical: {boundary.is_physical_boundary()}")
                print(f"    Is Virtual: {boundary.is_virtual_boundary()}")
                print(f"    Is Internal: {boundary.is_internal_boundary()}")
                print(f"    Is External: {boundary.is_external_boundary()}")
        else:
            print("  No boundaries found for this space")
    
    # Test validation
    if all_boundaries:
        is_valid, errors = boundary_parser.validate_boundaries(all_boundaries)
        print(f"\n--- Validation Results ---")
        print(f"Valid: {is_valid}")
        if errors:
            print("Errors found:")
            for error in errors:
                print(f"  - {error}")
        else:
            print("No validation errors")
    
    print("\n✓ Space boundary extraction test completed successfully")
    return True

if __name__ == "__main__":
    success = test_space_boundary_extraction()
    sys.exit(0 if success else 1)