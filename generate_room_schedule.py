#!/usr/bin/env python3
"""
Generate Room Schedule from IFC File

Creates a comprehensive room schedule from the reference IFC file.
"""

import sys
import os
from pathlib import Path
import json

# Add project root to path
sys.path.insert(0, '.')

try:
    import ifcopenshell
    from ifc_room_schedule.parser.ifc_relationship_parser import IfcRelationshipParser
    from ifc_room_schedule.parser.ifc_space_extractor import IfcSpaceExtractor
    from ifc_room_schedule.parser.ifc_space_boundary_parser import IfcSpaceBoundaryParser
    print("✓ All required modules imported successfully")
except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)

def generate_room_schedule():
    """Generate a comprehensive room schedule from the IFC file."""
    
    # Path to the test IFC file
    ifc_file_path = Path("tesfiler/AkkordSvingen 23_ARK.ifc")
    
    if not ifc_file_path.exists():
        print(f"✗ IFC file not found: {ifc_file_path}")
        return False
    
    print(f"=== Generating Room Schedule from {ifc_file_path.name} ===\n")
    
    try:
        # Load IFC file
        ifc_file = ifcopenshell.open(str(ifc_file_path))
        print(f"✓ IFC file loaded (Schema: {ifc_file.schema})")
        
        # Initialize parsers
        space_extractor = IfcSpaceExtractor(ifc_file)
        rel_parser = IfcRelationshipParser(ifc_file)
        boundary_parser = IfcSpaceBoundaryParser(ifc_file)
        
        # Extract all spaces
        print("\n--- Extracting Spaces ---")
        spaces = space_extractor.extract_spaces()
        print(f"✓ Found {len(spaces)} spaces")
        
        # Generate room schedule
        room_schedule = []
        
        for i, space in enumerate(spaces, 1):
            print(f"\nProcessing space {i}/{len(spaces)}: {space.name}")
            
            # Get relationships
            relationships = rel_parser.get_space_relationships(space.guid)
            rel_summary = rel_parser.get_relationship_summary(space.guid)
            
            # Get space boundaries
            try:
                boundaries = boundary_parser.get_space_boundaries(space.guid)
                boundary_count = len(boundaries)
            except:
                boundary_count = 0
            
            # Create room entry
            room_entry = {
                'number': i,
                'guid': space.guid,
                'name': space.name,
                'long_name': space.long_name,
                'description': space.description,
                'object_type': space.object_type,
                'zone_category': space.zone_category,
                'room_number': space.number,
                'elevation': space.elevation,
                'quantities': space.quantities,
                'area_m2': space.quantities.get('NetFloorArea', 0),
                'volume_m3': space.quantities.get('NetVolume', 0),
                'height_mm': space.quantities.get('Height', 0),
                'perimeter_mm': space.quantities.get('NetPerimeter', 0),
                'relationships': {
                    'total': len(relationships),
                    'summary': rel_summary
                },
                'boundaries': boundary_count
            }
            
            room_schedule.append(room_entry)
        
        # Sort by area (largest first)
        room_schedule.sort(key=lambda x: x['area_m2'], reverse=True)
        
        # Display room schedule
        print("\n" + "="*120)
        print("ROOM SCHEDULE - AkkordSvingen 23_ARK")
        print("="*120)
        print(f"{'No.':<4} {'Name':<15} {'Long Name':<20} {'Description':<15} {'Area (m²)':<12} {'Volume (m³)':<12} {'Height (mm)':<12} {'Relationships':<12}")
        print("-"*120)
        
        total_area = 0
        total_volume = 0
        
        for room in room_schedule:
            area = room['area_m2']
            volume = room['volume_m3']
            height = room['height_mm']
            rel_count = room['relationships']['total']
            
            total_area += area
            total_volume += volume
            
            print(f"{room['number']:<4} {room['name']:<15} {room['long_name']:<20} {room['description']:<15} "
                  f"{area:<12.2f} {volume:<12.2f} {height:<12.0f} {rel_count:<12}")
        
        print("-"*120)
        print(f"{'TOTAL':<56} {total_area:<12.2f} {total_volume:<12.2f}")
        print("="*120)
        
        # Show relationship summary
        print("\n--- Relationship Summary ---")
        all_rel_types = set()
        for room in room_schedule:
            all_rel_types.update(room['relationships']['summary'].keys())
        
        for rel_type in sorted(all_rel_types):
            total_count = sum(room['relationships']['summary'].get(rel_type, 0) for room in room_schedule)
            print(f"{rel_type}: {total_count} total relationships")
        
        # Show largest rooms
        print("\n--- Top 10 Largest Rooms ---")
        for i, room in enumerate(room_schedule[:10], 1):
            print(f"{i:2}. {room['name']} ({room['long_name']}) - {room['area_m2']:.2f} m²")
        
        # Save to JSON file
        output_file = Path("room_schedule_output.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(room_schedule, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Room schedule saved to: {output_file}")
        
        # Show building statistics
        print("\n--- Building Statistics ---")
        print(f"Total rooms: {len(room_schedule)}")
        print(f"Total floor area: {total_area:.2f} m²")
        print(f"Total volume: {total_volume:.2f} m³")
        print(f"Average room size: {total_area/len(room_schedule):.2f} m²")
        
        # Show room types
        room_types = {}
        for room in room_schedule:
            desc = room['description'] or 'Unknown'
            room_types[desc] = room_types.get(desc, 0) + 1
        
        print("\n--- Room Types ---")
        for room_type, count in sorted(room_types.items()):
            print(f"{room_type}: {count} rooms")
        
        return True
        
    except Exception as e:
        print(f"✗ Error generating room schedule: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function."""
    success = generate_room_schedule()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())