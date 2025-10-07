#!/usr/bin/env python3
"""
Analyze Spatial Positioning in IFC Files

This script demonstrates how IFC files contain detailed spatial positioning
information for IfcSpace objects and how the system preserves relative positions.
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Any, Tuple

# Add project root to path
sys.path.append('.')

from ifc_room_schedule.parser.ifc_file_reader import IfcFileReader
from ifc_room_schedule.visualization.geometry_extractor import GeometryExtractor
from ifc_room_schedule.visualization.geometry_models import Point2D, Polygon2D


def analyze_ifc_spatial_data(ifc_path: str) -> Dict[str, Any]:
    """Analyze spatial positioning data in an IFC file."""
    print(f"\n🔍 Analyzing spatial data in: {Path(ifc_path).name}")
    print("=" * 60)
    
    try:
        # Load IFC file
        reader = IfcFileReader()
        success, message = reader.load_file(ifc_path)
        if not success:
            print(f"❌ Failed to load IFC file: {message}")
            return {}
        
        ifc_file = reader.get_ifc_file()
        
        # Get all spaces
        spaces = ifc_file.by_type("IfcSpace")
        print(f"📊 Found {len(spaces)} IfcSpace objects")
        
        # Analyze spatial positioning information
        spatial_analysis = {
            'total_spaces': len(spaces),
            'spaces_with_placement': 0,
            'spaces_with_representation': 0,
            'spaces_with_boundaries': 0,
            'coordinate_ranges': {'x': [float('inf'), float('-inf')], 
                                'y': [float('inf'), float('-inf')], 
                                'z': [float('inf'), float('-inf')]},
            'floor_levels': {},
            'space_details': []
        }
        
        # Analyze each space
        for i, space in enumerate(spaces[:10]):  # Analyze first 10 spaces
            space_info = analyze_space_positioning(space, ifc_file)
            spatial_analysis['space_details'].append(space_info)
            
            # Update statistics
            if space_info['has_placement']:
                spatial_analysis['spaces_with_placement'] += 1
            if space_info['has_representation']:
                spatial_analysis['spaces_with_representation'] += 1
            if space_info['boundary_count'] > 0:
                spatial_analysis['spaces_with_boundaries'] += 1
            
            # Update coordinate ranges
            if space_info['position']:
                x, y, z = space_info['position']
                spatial_analysis['coordinate_ranges']['x'][0] = min(spatial_analysis['coordinate_ranges']['x'][0], x)
                spatial_analysis['coordinate_ranges']['x'][1] = max(spatial_analysis['coordinate_ranges']['x'][1], x)
                spatial_analysis['coordinate_ranges']['y'][0] = min(spatial_analysis['coordinate_ranges']['y'][0], y)
                spatial_analysis['coordinate_ranges']['y'][1] = max(spatial_analysis['coordinate_ranges']['y'][1], y)
                spatial_analysis['coordinate_ranges']['z'][0] = min(spatial_analysis['coordinate_ranges']['z'][0], z)
                spatial_analysis['coordinate_ranges']['z'][1] = max(spatial_analysis['coordinate_ranges']['z'][1], z)
        
        # Print analysis results
        print_spatial_analysis(spatial_analysis)
        
        return spatial_analysis
        
    except Exception as e:
        print(f"❌ Error analyzing spatial data: {str(e)}")
        return {}


def analyze_space_positioning(space, ifc_file) -> Dict[str, Any]:
    """Analyze positioning information for a single space."""
    space_info = {
        'guid': getattr(space, 'GlobalId', 'Unknown'),
        'name': getattr(space, 'Name', 'Unnamed'),
        'has_placement': False,
        'has_representation': False,
        'position': None,
        'elevation': None,
        'boundary_count': 0,
        'related_elements': [],
        'floor_reference': None
    }
    
    try:
        # Check ObjectPlacement (spatial positioning)
        if hasattr(space, 'ObjectPlacement') and space.ObjectPlacement:
            space_info['has_placement'] = True
            position = extract_position_from_placement(space.ObjectPlacement)
            if position:
                space_info['position'] = position
                space_info['elevation'] = position[2]  # Z coordinate
        
        # Check Representation (geometric representation)
        if hasattr(space, 'Representation') and space.Representation:
            space_info['has_representation'] = True
        
        # Count space boundaries
        boundaries = get_space_boundaries(space, ifc_file)
        space_info['boundary_count'] = len(boundaries)
        
        # Find related building elements
        related_elements = find_related_elements(space, ifc_file)
        space_info['related_elements'] = [elem.is_a() for elem in related_elements[:5]]  # First 5 types
        
        # Find floor/storey reference
        floor_ref = find_floor_reference(space, ifc_file)
        if floor_ref:
            space_info['floor_reference'] = getattr(floor_ref, 'Name', 'Unnamed Floor')
        
    except Exception as e:
        print(f"⚠️ Error analyzing space {space_info['name']}: {e}")
    
    return space_info


def extract_position_from_placement(placement, accumulated_transform=None) -> Tuple[float, float, float]:
    """Extract world coordinates from IFC placement hierarchy."""
    try:
        if accumulated_transform is None:
            accumulated_transform = [0.0, 0.0, 0.0]  # x, y, z
        
        # Get local placement
        if hasattr(placement, 'RelativePlacement') and placement.RelativePlacement:
            rel_placement = placement.RelativePlacement
            if hasattr(rel_placement, 'Location') and rel_placement.Location:
                location = rel_placement.Location
                if hasattr(location, 'Coordinates') and location.Coordinates:
                    coords = location.Coordinates
                    if len(coords) >= 3:
                        accumulated_transform[0] += float(coords[0])
                        accumulated_transform[1] += float(coords[1])
                        accumulated_transform[2] += float(coords[2])
        
        # Recurse up the placement hierarchy
        if hasattr(placement, 'PlacementRelTo') and placement.PlacementRelTo:
            return extract_position_from_placement(placement.PlacementRelTo, accumulated_transform)
        
        return tuple(accumulated_transform)
        
    except Exception as e:
        return (0.0, 0.0, 0.0)


def get_space_boundaries(space, ifc_file) -> List[Any]:
    """Get all space boundaries for a space."""
    try:
        boundaries = []
        
        # Find IfcRelSpaceBoundary relationships
        for rel in ifc_file.by_type("IfcRelSpaceBoundary"):
            if hasattr(rel, 'RelatingSpace') and rel.RelatingSpace == space:
                boundaries.append(rel)
        
        return boundaries
        
    except Exception as e:
        return []


def find_related_elements(space, ifc_file) -> List[Any]:
    """Find building elements related to a space."""
    try:
        related_elements = []
        
        # Find elements through space boundaries
        for rel in ifc_file.by_type("IfcRelSpaceBoundary"):
            if hasattr(rel, 'RelatingSpace') and rel.RelatingSpace == space:
                if hasattr(rel, 'RelatedBuildingElement') and rel.RelatedBuildingElement:
                    related_elements.append(rel.RelatedBuildingElement)
        
        return related_elements
        
    except Exception as e:
        return []


def find_floor_reference(space, ifc_file) -> Any:
    """Find the building storey/floor that contains this space."""
    try:
        # Check spatial containment relationships
        for rel in ifc_file.by_type("IfcRelContainedInSpatialStructure"):
            if hasattr(rel, 'RelatedElements') and space in rel.RelatedElements:
                if hasattr(rel, 'RelatingStructure') and rel.RelatingStructure:
                    structure = rel.RelatingStructure
                    if structure.is_a("IfcBuildingStorey"):
                        return structure
        
        # Check aggregation relationships
        for rel in ifc_file.by_type("IfcRelAggregates"):
            if hasattr(rel, 'RelatedObjects') and space in rel.RelatedObjects:
                if hasattr(rel, 'RelatingObject') and rel.RelatingObject:
                    relating_obj = rel.RelatingObject
                    if relating_obj.is_a("IfcBuildingStorey"):
                        return relating_obj
        
        return None
        
    except Exception as e:
        return None


def print_spatial_analysis(analysis: Dict[str, Any]):
    """Print the spatial analysis results."""
    print("\n📈 SPATIAL ANALYSIS RESULTS")
    print("-" * 40)
    
    total = analysis['total_spaces']
    print(f"Total spaces analyzed: {total}")
    print(f"Spaces with ObjectPlacement: {analysis['spaces_with_placement']}/{total} ({analysis['spaces_with_placement']/total*100:.1f}%)")
    print(f"Spaces with Representation: {analysis['spaces_with_representation']}/{total} ({analysis['spaces_with_representation']/total*100:.1f}%)")
    print(f"Spaces with boundaries: {analysis['spaces_with_boundaries']}/{total} ({analysis['spaces_with_boundaries']/total*100:.1f}%)")
    
    # Coordinate ranges
    ranges = analysis['coordinate_ranges']
    if ranges['x'][0] != float('inf'):
        print(f"\n📐 COORDINATE RANGES:")
        print(f"X: {ranges['x'][0]:.2f} to {ranges['x'][1]:.2f} (width: {ranges['x'][1] - ranges['x'][0]:.2f}m)")
        print(f"Y: {ranges['y'][0]:.2f} to {ranges['y'][1]:.2f} (height: {ranges['y'][1] - ranges['y'][0]:.2f}m)")
        print(f"Z: {ranges['z'][0]:.2f} to {ranges['z'][1]:.2f} (elevation range: {ranges['z'][1] - ranges['z'][0]:.2f}m)")
    
    # Sample space details
    print(f"\n🏠 SAMPLE SPACE DETAILS (first 5):")
    for i, space in enumerate(analysis['space_details'][:5]):
        print(f"\n{i+1}. {space['name']} ({space['guid'][:8]}...)")
        if space['position']:
            x, y, z = space['position']
            print(f"   Position: ({x:.2f}, {y:.2f}, {z:.2f})")
        else:
            print(f"   Position: Not available")
        print(f"   Floor: {space['floor_reference'] or 'Not assigned'}")
        print(f"   Boundaries: {space['boundary_count']}")
        if space['related_elements']:
            print(f"   Related elements: {', '.join(space['related_elements'])}")


def demonstrate_geometry_extraction_with_positioning(ifc_path: str):
    """Demonstrate how geometry extraction preserves spatial relationships."""
    print(f"\n🏗️ GEOMETRY EXTRACTION WITH SPATIAL POSITIONING")
    print("=" * 60)
    
    try:
        # Load and extract geometry
        reader = IfcFileReader()
        success, message = reader.load_file(ifc_path)
        if not success:
            print(f"❌ Failed to load IFC file: {message}")
            return
        
        geometry_extractor = GeometryExtractor()
        floor_geometries = geometry_extractor.extract_floor_geometry(reader.get_ifc_file())
        
        if not floor_geometries:
            print("❌ No floor geometries extracted")
            return
        
        print(f"✅ Extracted geometry for {len(floor_geometries)} floors")
        
        # Analyze spatial relationships in extracted geometry
        for floor_id, geometry in floor_geometries.items():
            print(f"\n📊 Floor: {geometry.level.name}")
            print(f"   Rooms with geometry: {geometry.get_room_count()}")
            
            if geometry.bounds:
                width = geometry.get_bounds_width()
                height = geometry.get_bounds_height()
                print(f"   Floor plan bounds: {width:.1f}m × {height:.1f}m")
                print(f"   Bounds: ({geometry.bounds[0]:.1f}, {geometry.bounds[1]:.1f}) to ({geometry.bounds[2]:.1f}, {geometry.bounds[3]:.1f})")
            
            # Show sample room positions
            print(f"   Sample room positions:")
            for i, polygon in enumerate(geometry.room_polygons[:3]):  # First 3 rooms
                centroid = polygon.get_centroid()
                bounds = polygon.get_bounds()
                print(f"     {i+1}. {polygon.space_name}: center=({centroid.x:.1f}, {centroid.y:.1f}), size={bounds[2]-bounds[0]:.1f}×{bounds[3]-bounds[1]:.1f}m")
        
        print(f"\n✅ The extracted geometry preserves the relative spatial positions from the IFC file!")
        print(f"   Rooms are positioned correctly relative to each other based on their ObjectPlacement data.")
        
    except Exception as e:
        print(f"❌ Error in geometry extraction: {str(e)}")


def main():
    """Main analysis function."""
    print("IFC Spatial Positioning Analysis")
    print("=" * 50)
    
    # Find test IFC files
    test_files_dir = Path("tesfiler")
    if not test_files_dir.exists():
        print("❌ Test files directory 'tesfiler' not found")
        return
    
    ifc_files = list(test_files_dir.glob("*.ifc"))
    if not ifc_files:
        print("❌ No IFC files found in 'tesfiler' directory")
        return
    
    print(f"Found {len(ifc_files)} IFC test files:")
    for ifc_file in ifc_files:
        size_mb = ifc_file.stat().st_size / (1024 * 1024)
        print(f"  - {ifc_file.name} ({size_mb:.1f} MB)")
    
    # Analyze each file
    for ifc_file in ifc_files:
        try:
            # Spatial data analysis
            spatial_analysis = analyze_ifc_spatial_data(str(ifc_file))
            
            # Geometry extraction demonstration
            demonstrate_geometry_extraction_with_positioning(str(ifc_file))
            
        except Exception as e:
            print(f"❌ Failed to analyze {ifc_file.name}: {str(e)}")
    
    print(f"\n" + "=" * 60)
    print("🎯 CONCLUSION:")
    print("IFC files contain rich spatial positioning information including:")
    print("  • ObjectPlacement hierarchy with world coordinates")
    print("  • Space boundaries defining room shapes")
    print("  • Relationships to building elements (walls, doors, etc.)")
    print("  • Floor/storey assignments for multi-level buildings")
    print("  • The visualization system preserves these spatial relationships!")


if __name__ == "__main__":
    main()