#!/usr/bin/env python3
"""
Demonstration of JSON Export Engine functionality.

This script demonstrates how to use the JsonBuilder class to export
IFC room schedule data to JSON format.
"""

import json
from datetime import datetime
from pathlib import Path

from ifc_room_schedule.export.json_builder import JsonBuilder
from ifc_room_schedule.data.space_model import SpaceData
from ifc_room_schedule.data.surface_model import SurfaceData
from ifc_room_schedule.data.space_boundary_model import SpaceBoundaryData
from ifc_room_schedule.data.relationship_model import RelationshipData

def create_sample_data():
    """Create sample space data for demonstration."""
    # Create sample surface data
    surface1 = SurfaceData(
        id="surface_1",
        type="Wall",
        area=25.5,
        material="Concrete",
        ifc_type="IfcWall",
        related_space_guid="space_guid_1"
    )
    
    surface2 = SurfaceData(
        id="surface_2", 
        type="Floor",
        area=50.0,
        material="Concrete Slab",
        ifc_type="IfcSlab",
        related_space_guid="space_guid_1"
    )
    
    # Create sample space boundary data
    boundary1 = SpaceBoundaryData(
        id="boundary_1",
        guid="boundary_guid_1",
        name="North Wall Boundary",
        description="Boundary to exterior",
        physical_or_virtual_boundary="Physical",
        internal_or_external_boundary="External",
        related_building_element_guid="wall_guid_1",
        related_building_element_name="North Wall",
        related_building_element_type="IfcWall",
        related_space_guid="space_guid_1",
        boundary_surface_type="Wall",
        boundary_orientation="North",
        calculated_area=25.5
    )
    
    # Create sample relationship data
    relationship1 = RelationshipData(
        related_entity_guid="building_guid_1",
        related_entity_name="Main Building",
        related_entity_description="Primary building structure",
        relationship_type="Contains",
        ifc_relationship_type="IfcRelContainedInSpatialStructure"
    )
    
    # Create sample space data
    space1 = SpaceData(
        guid="space_guid_1",
        name="Office 101",
        long_name="Office Room 101",
        description="Main office space",
        object_type="Office",
        zone_category="Work",
        number="101",
        elevation=0.0
    )
    
    # Add surfaces, boundaries, and relationships to space
    space1.add_surface(surface1)
    space1.add_surface(surface2)
    space1.add_space_boundary(boundary1)
    space1.add_relationship(relationship1)
    
    # Set some quantities
    space1.quantities = {
        "Height": 2700.0,
        "GrossFloorArea": 50.0,
        "NetFloorArea": 48.5,
        "GrossVolume": 135.0,
        "NetVolume": 130.95
    }
    
    return [space1]


def main():
    """Main demonstration function."""
    print("IFC Room Schedule JSON Export Demo")
    print("=" * 40)
    
    # Create JSON builder
    json_builder = JsonBuilder()
    
    # Set source file information
    json_builder.set_source_file("demo_building.ifc")
    json_builder.set_ifc_version("IFC4")
    
    # Create sample data
    print("Creating sample space data...")
    spaces = create_sample_data()
    print(f"Created {len(spaces)} sample spaces")
    
    # Build JSON structure
    print("\nBuilding JSON structure...")
    json_data = json_builder.build_json_structure(spaces)
    
    # Validate the data
    print("Validating export data...")
    is_valid, errors = json_builder.validate_export_data(json_data)
    
    if is_valid:
        print("✓ Data validation passed")
    else:
        print("✗ Data validation failed:")
        for error in errors:
            print(f"  - {error}")
        return
    
    # Export to JSON file
    output_file = "demo_export.json"
    print(f"\nExporting to {output_file}...")
    
    success, messages = json_builder.export_to_json(
        spaces, 
        output_file,
        metadata={"demo_version": "1.0", "created_by": "Demo Script"}
    )
    
    if success:
        print("✓ Export successful!")
        for message in messages:
            print(f"  {message}")
        
        # Display some statistics
        summary = json_data["summary"]
        print(f"\nExport Summary:")
        print(f"  Total spaces: {summary['total_spaces']}")
        print(f"  Total surface area: {summary['total_surface_area']} m²")
        print(f"  Total boundary area: {summary['total_boundary_area']} m²")
        
        # Show file size
        file_path = Path(output_file)
        if file_path.exists():
            file_size = file_path.stat().st_size
            print(f"  Output file size: {file_size} bytes")
            
    else:
        print("✗ Export failed:")
        for message in messages:
            print(f"  - {message}")


if __name__ == "__main__":
    main()