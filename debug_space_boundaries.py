#!/usr/bin/env python3
"""
Debug script to investigate space boundary extraction from IFC file
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    import ifcopenshell
    import ifcopenshell.geom
except ImportError:
    print("IfcOpenShell not available")
    sys.exit(1)

from ifc_room_schedule.parser.ifc_file_reader import IfcFileReader


def debug_space_boundaries(ifc_path: str):
    """Debug space boundary extraction from IFC file."""
    print(f"Debugging space boundaries for: {ifc_path}")
    print("=" * 60)
    
    # Load IFC file
    ifc_reader = IfcFileReader()
    success, message = ifc_reader.load_file(ifc_path)
    if not success:
        print(f"Failed to load IFC file: {message}")
        return
    
    ifc_file = ifc_reader.get_ifc_file()
    print(f"✓ IFC file loaded successfully")
    
    # Get all spaces
    spaces = ifc_file.by_type("IfcSpace")
    print(f"✓ Found {len(spaces)} spaces")
    
    # Check for space boundaries
    boundary_types = [
        "IfcRelSpaceBoundary",
        "IfcRelSpaceBoundary1stLevel", 
        "IfcRelSpaceBoundary2ndLevel"
    ]
    
    total_boundaries = 0
    for boundary_type in boundary_types:
        boundaries = ifc_file.by_type(boundary_type)
        print(f"  - {boundary_type}: {len(boundaries)} found")
        total_boundaries += len(boundaries)
    
    print(f"✓ Total space boundaries: {total_boundaries}")
    print()
    
    # Analyze first few spaces in detail
    for i, space in enumerate(spaces[:5]):
        print(f"Space {i+1}: {space.Name} (GUID: {space.GlobalId})")
        
        # Check space properties
        if hasattr(space, 'ObjectType') and space.ObjectType:
            print(f"  - Type: {space.ObjectType}")
        
        # Check for space boundaries
        space_boundaries = []
        for boundary_type in boundary_types:
            try:
                for rel in ifc_file.by_type(boundary_type):
                    if hasattr(rel, 'RelatingSpace') and rel.RelatingSpace == space:
                        space_boundaries.append(rel)
            except:
                continue
        
        print(f"  - Boundaries: {len(space_boundaries)}")
        
        # Analyze boundaries
        for j, boundary in enumerate(space_boundaries[:3]):  # First 3 boundaries
            print(f"    Boundary {j+1}:")
            
            # Check connection geometry
            if hasattr(boundary, 'ConnectionGeometry') and boundary.ConnectionGeometry:
                print(f"      - Has ConnectionGeometry: {type(boundary.ConnectionGeometry)}")
            else:
                print(f"      - No ConnectionGeometry")
            
            # Check related building element
            if hasattr(boundary, 'RelatedBuildingElement') and boundary.RelatedBuildingElement:
                element = boundary.RelatedBuildingElement
                print(f"      - Related element: {element.is_a()} ({element.Name if hasattr(element, 'Name') else 'No name'})")
                
                # Check element geometry
                if hasattr(element, 'Representation') and element.Representation:
                    print(f"      - Element has representation")
                else:
                    print(f"      - Element has no representation")
            else:
                print(f"      - No related building element")
        
        # Try to extract geometry using ifcopenshell
        try:
            settings = ifcopenshell.geom.settings()
            settings.set(settings.USE_WORLD_COORDS, True)
            
            shape = ifcopenshell.geom.create_shape(settings, space)
            if shape:
                print(f"  - IfcOpenShell geometry: Available")
                # Get geometry info
                geometry = shape.geometry
                if hasattr(geometry, 'verts'):
                    verts = geometry.verts
                    print(f"    - Vertices: {len(verts)//3} points")
                if hasattr(geometry, 'faces'):
                    faces = geometry.faces
                    print(f"    - Faces: {len(faces)//3} triangles")
            else:
                print(f"  - IfcOpenShell geometry: Not available")
        except Exception as e:
            print(f"  - IfcOpenShell geometry error: {e}")
        
        print()
    
    # Check for building elements that could define space boundaries
    wall_types = ["IfcWall", "IfcWallStandardCase", "IfcCurtainWall"]
    for wall_type in wall_types:
        walls = ifc_file.by_type(wall_type)
        if walls:
            print(f"Found {len(walls)} {wall_type} elements")
    
    # Check for slabs
    slab_types = ["IfcSlab", "IfcSlabStandardCase"]
    for slab_type in slab_types:
        slabs = ifc_file.by_type(slab_type)
        if slabs:
            print(f"Found {len(slabs)} {slab_type} elements")


if __name__ == "__main__":
    test_file = "tesfiler/AkkordSvingen 23_ARK.ifc"
    
    if os.path.exists(test_file):
        debug_space_boundaries(test_file)
    else:
        print(f"Test file not found: {test_file}")