#!/usr/bin/env python3
"""
Simple debug script to analyze current geometry extraction results
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ifc_room_schedule.parser.ifc_file_reader import IfcFileReader
from ifc_room_schedule.parser.ifc_space_extractor import IfcSpaceExtractor
from ifc_room_schedule.visualization.geometry_extractor import GeometryExtractor

def debug_geometry_simple():
    """Debug the current geometry extraction with text output."""
    
    print("Debugging current geometry extraction...")
    print("=" * 60)
    
    # Load IFC file
    ifc_file_path = "tesfiler/DEICH_Test.ifc"
    reader = IfcFileReader()
    ifc_file = reader.load_file(ifc_file_path)
    
    if not ifc_file:
        print("❌ Failed to load IFC file")
        return
    
    print("✓ IFC file loaded")
    
    # Extract spaces
    extractor = IfcSpaceExtractor(ifc_file)
    spaces = extractor.extract_spaces()
    print(f"✓ Found {len(spaces)} spaces")
    
    # Extract geometry
    geom_extractor = GeometryExtractor()
    
    # Process first 15 spaces for detailed analysis
    sample_spaces = spaces[:15]
    
    print(f"\nAnalyzing first {len(sample_spaces)} spaces:")
    print("-" * 60)
    
    all_centers = []
    valid_geometries = 0
    
    for i, space in enumerate(sample_spaces):
        space_name = getattr(space, 'Name', f'Space_{i}') or f'Space_{i}'
        space_guid = getattr(space, 'GlobalId', f'guid_{i}')
        
        print(f"\n{i+1:2d}. {space_name}")
        print(f"     GUID: {space_guid}")
        
        # Extract polygons
        polygons = geom_extractor.extract_space_boundaries(space)
        
        if polygons:
            polygon = polygons[0]  # Use first polygon
            points = polygon.points
            
            # Get bounds
            x_coords = [p.x for p in points]
            y_coords = [p.y for p in points]
            min_x, max_x = min(x_coords), max(x_coords)
            min_y, max_y = min(y_coords), max(y_coords)
            center_x = (min_x + max_x) / 2
            center_y = (min_y + max_y) / 2
            
            print(f"     Points: {len(points)}")
            print(f"     Area: {polygon.get_area():.1f} m²")
            print(f"     Bounds: ({min_x:.1f}, {min_y:.1f}) to ({max_x:.1f}, {max_y:.1f})")
            print(f"     Dimensions: {max_x-min_x:.1f} x {max_y-min_y:.1f} m")
            print(f"     Center: ({center_x:.1f}, {center_y:.1f})")
            
            all_centers.append((space_name, center_x, center_y, polygon.get_area()))
            valid_geometries += 1
            
            # Show first few points for shape analysis
            if len(points) <= 6:
                print(f"     Shape points:")
                for j, point in enumerate(points):
                    print(f"       {j+1}: ({point.x:.1f}, {point.y:.1f})")
        else:
            print(f"     ❌ No geometry extracted")
    
    print(f"\n" + "=" * 60)
    print(f"SUMMARY:")
    print(f"- Valid geometries: {valid_geometries}/{len(sample_spaces)}")
    print(f"- Success rate: {valid_geometries/len(sample_spaces)*100:.1f}%")
    
    if all_centers:
        # Calculate overall bounds
        all_x = [c[1] for c in all_centers]
        all_y = [c[2] for c in all_centers]
        all_areas = [c[3] for c in all_centers]
        
        print(f"- Overall bounds: ({min(all_x):.1f}, {min(all_y):.1f}) to ({max(all_x):.1f}, {max(all_y):.1f})")
        print(f"- Total span: {max(all_x)-min(all_x):.1f} x {max(all_y)-min(all_y):.1f} m")
        print(f"- Area range: {min(all_areas):.1f} - {max(all_areas):.1f} m²")
        print(f"- Average area: {sum(all_areas)/len(all_areas):.1f} m²")
        
        # Check for potential overlaps
        print(f"\nChecking for overlaps (centers within 10m):")
        overlaps = []
        
        for i, (name1, x1, y1, area1) in enumerate(all_centers):
            for j, (name2, x2, y2, area2) in enumerate(all_centers[i+1:], i+1):
                distance = ((x1 - x2)**2 + (y1 - y2)**2)**0.5
                if distance < 10.0:  # Less than 10 meters apart
                    overlaps.append((name1, name2, distance))
        
        if overlaps:
            print(f"⚠️  Found {len(overlaps)} potential overlaps:")
            for name1, name2, dist in overlaps[:10]:  # Show first 10
                print(f"   - {name1} ↔ {name2}: {dist:.1f}m apart")
            if len(overlaps) > 10:
                print(f"   ... and {len(overlaps)-10} more")
        else:
            print("✓ No obvious overlaps detected")
        
        # Show room distribution
        print(f"\nRoom centers (sorted by X coordinate):")
        sorted_centers = sorted(all_centers, key=lambda c: c[1])
        for name, x, y, area in sorted_centers:
            print(f"   {name:12s}: ({x:6.1f}, {y:6.1f}) - {area:5.1f} m²")

if __name__ == "__main__":
    debug_geometry_simple()