#!/usr/bin/env python3
"""
Debug script for testing 2D floor plan visualization
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from ifc_room_schedule.parser.ifc_file_reader import IfcFileReader
from ifc_room_schedule.parser.ifc_space_extractor import IfcSpaceExtractor
from ifc_room_schedule.visualization.geometry_extractor import GeometryExtractor

def debug_floor_plan_geometry(ifc_path: str):
    """Debug floor plan geometry extraction."""
    print(f"Debugging floor plan geometry for: {ifc_path}")
    print("=" * 60)
    
    # Load IFC file
    ifc_reader = IfcFileReader()
    success, message = ifc_reader.load_file(ifc_path)
    if not success:
        print(f"Failed to load IFC file: {message}")
        return
    
    print(f"✓ IFC file loaded successfully")
    
    # Extract spaces
    space_extractor = IfcSpaceExtractor()
    space_extractor.set_ifc_file(ifc_reader.get_ifc_file())
    spaces = space_extractor.extract_spaces()
    print(f"✓ Found {len(spaces)} spaces")
    
    # Extract geometry
    geometry_extractor = GeometryExtractor()
    floor_geometries = geometry_extractor.extract_floor_geometry(ifc_reader.get_ifc_file())
    
    print(f"✓ Extracted geometry for {len(floor_geometries)} floors")
    print()
    
    # Analyze each floor
    for floor_id, floor_geometry in floor_geometries.items():
        print(f"Floor: {floor_geometry.level.name} (ID: {floor_id})")
        print(f"  - Spaces: {len(floor_geometry.level.spaces)}")
        print(f"  - Room polygons: {len(floor_geometry.room_polygons)}")
        
        if floor_geometry.bounds:
            bounds = floor_geometry.bounds
            width = bounds[2] - bounds[0]
            height = bounds[3] - bounds[1]
            print(f"  - Bounds: ({bounds[0]:.1f}, {bounds[1]:.1f}) to ({bounds[2]:.1f}, {bounds[3]:.1f})")
            print(f"  - Dimensions: {width:.1f} x {height:.1f} m")
        
        print(f"  - Total area: {floor_geometry.get_total_area():.1f} m²")
        print()
        
        # Analyze individual rooms
        print("  Room details:")
        for i, polygon in enumerate(floor_geometry.room_polygons[:5]):  # Show first 5 rooms
            bounds = polygon.get_bounds()
            area = polygon.get_area()
            print(f"    {i+1}. {polygon.space_name[:30]}")
            print(f"       GUID: {polygon.space_guid}")
            print(f"       Points: {len(polygon.points)}")
            print(f"       Area: {area:.1f} m²")
            print(f"       Bounds: ({bounds[0]:.1f}, {bounds[1]:.1f}) to ({bounds[2]:.1f}, {bounds[3]:.1f})")
            
            # Check for potential overlaps
            center = polygon.get_centroid()
            print(f"       Center: ({center.x:.1f}, {center.y:.1f})")
            print()
        
        if len(floor_geometry.room_polygons) > 5:
            print(f"    ... and {len(floor_geometry.room_polygons) - 5} more rooms")
        print()
        
        # Check for overlapping rooms
        overlaps = 0
        for i, poly1 in enumerate(floor_geometry.room_polygons):
            bounds1 = poly1.get_bounds()
            center1 = poly1.get_centroid()
            
            for j, poly2 in enumerate(floor_geometry.room_polygons[i+1:], i+1):
                bounds2 = poly2.get_bounds()
                center2 = poly2.get_centroid()
                
                # Simple overlap check - if centers are very close
                distance = ((center1.x - center2.x)**2 + (center1.y - center2.y)**2)**0.5
                if distance < 1.0:  # Less than 1 meter apart
                    overlaps += 1
                    if overlaps <= 3:  # Show first 3 overlaps
                        print(f"  ⚠️  Potential overlap between:")
                        print(f"      - {poly1.space_name} (center: {center1.x:.1f}, {center1.y:.1f})")
                        print(f"      - {poly2.space_name} (center: {center2.x:.1f}, {center2.y:.1f})")
                        print(f"      - Distance: {distance:.2f} m")
                        print()
        
        if overlaps > 0:
            print(f"  ⚠️  Found {overlaps} potential overlapping room pairs")
        else:
            print(f"  ✓ No obvious overlaps detected")
        
        print("-" * 40)

if __name__ == "__main__":
    # Test with available IFC files
    test_files = [
        "tesfiler/AkkordSvingen 23_ARK.ifc",
        "tesfiler/DEICH_Test.ifc"
    ]
    
    for test_file in test_files:
        if os.path.exists(test_file):
            debug_floor_plan_geometry(test_file)
            break
    else:
        print("No test IFC files found!")