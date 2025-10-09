#!/usr/bin/env python3
"""
Test IfcOpenShell geometry extraction directly
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from ifc_room_schedule.parser.ifc_file_reader import IfcFileReader
from ifc_room_schedule.visualization.geometry_extractor import GeometryExtractor


def test_ifcopenshell_extraction():
    """Test IfcOpenShell geometry extraction."""
    test_file = "tesfiler/AkkordSvingen 23_ARK.ifc"
    
    if not os.path.exists(test_file):
        print(f"Test file not found: {test_file}")
        return
    
    print("Testing IfcOpenShell geometry extraction...")
    print("=" * 50)
    
    # Load IFC file
    ifc_reader = IfcFileReader()
    success, message = ifc_reader.load_file(test_file)
    if not success:
        print(f"Failed to load IFC file: {message}")
        return
    
    ifc_file = ifc_reader.get_ifc_file()
    print(f"✓ IFC file loaded")
    
    # Get first few spaces
    spaces = ifc_file.by_type("IfcSpace")[:3]
    print(f"✓ Testing with {len(spaces)} spaces")
    
    # Test geometry extractor
    extractor = GeometryExtractor()
    
    for i, space in enumerate(spaces):
        print(f"\nSpace {i+1}: {space.Name} (GUID: {space.GlobalId})")
        
        # Test IfcOpenShell extraction directly
        try:
            polygon = extractor._extract_polygon_with_ifcopenshell(
                space, space.GlobalId, space.Name
            )
            
            if polygon:
                print(f"  ✓ IfcOpenShell extraction successful!")
                print(f"    - Points: {len(polygon.points)}")
                print(f"    - Area: {polygon.get_area():.2f} m²")
                bounds = polygon.get_bounds()
                print(f"    - Bounds: ({bounds[0]:.1f}, {bounds[1]:.1f}) to ({bounds[2]:.1f}, {bounds[3]:.1f})")
                
                # Print first few points
                print(f"    - First 3 points:")
                for j, point in enumerate(polygon.points[:3]):
                    print(f"      {j+1}: ({point.x:.2f}, {point.y:.2f})")
            else:
                print(f"  ❌ IfcOpenShell extraction failed")
                
        except Exception as e:
            print(f"  ❌ IfcOpenShell extraction error: {e}")


if __name__ == "__main__":
    test_ifcopenshell_extraction()