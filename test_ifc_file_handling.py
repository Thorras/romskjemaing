#!/usr/bin/env python3
"""
Test script for handling the IFC reference file in tesfiler folder.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, '.')

try:
    import ifcopenshell
    from ifc_room_schedule.parser.ifc_relationship_parser import IfcRelationshipParser
    from ifc_room_schedule.parser.ifc_space_extractor import IfcSpaceExtractor
    print("✓ All required modules imported successfully")
except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)


def test_ifc_file_handling():
    """Test handling of the IFC reference file."""

    # Path to the test IFC file
    ifc_file_path = Path("tesfiler/AkkordSvingen 23_ARK.ifc")

    if not ifc_file_path.exists():
        print(f"✗ IFC file not found: {ifc_file_path}")
        return False

    print(f"✓ IFC file found: {ifc_file_path}")
    print(f"  File size: {ifc_file_path.stat().st_size / (1024*1024):.2f} MB")

    try:
        # Test loading the IFC file
        print("\n--- Testing IFC File Loading ---")
        ifc_file = ifcopenshell.open(str(ifc_file_path))
        print("✓ IFC file loaded successfully")
        print(f"  Schema: {ifc_file.schema}")

        # Get basic statistics
        all_entities = ifc_file.by_type("IfcRoot")
        spaces = ifc_file.by_type("IfcSpace")
        buildings = ifc_file.by_type("IfcBuilding")
        storeys = ifc_file.by_type("IfcBuildingStorey")

        print(f"  Total entities: {len(all_entities)}")
        print(f"  Spaces: {len(spaces)}")
        print(f"  Buildings: {len(buildings)}")
        print(f"  Building storeys: {len(storeys)}")

        # Test space extractor
        print("\n--- Testing Space Extractor ---")
        space_extractor = IfcSpaceExtractor()
        space_extractor.set_ifc_file(ifc_file)

        if spaces:
            # Test parsing first space
            first_space = spaces[0]
            space_guid = getattr(first_space, 'GlobalId', '')
            print(f"  Testing with space GUID: {space_guid}")

            # Extract all spaces first
            all_spaces = space_extractor.extract_spaces()
            if all_spaces:
                first_space_data = all_spaces[0]
                print(f"  ✓ Space data extracted: {first_space_data.name}")
                print(f"    GUID: {first_space_data.guid}")
                print(f"    Long name: {first_space_data.long_name}")
                print(f"    Description: {first_space_data.description}")
                print(f"    Quantities: {first_space_data.quantities}")
            else:
                print("  ✗ Failed to extract space data")

        # Test relationship parser
        print("\n--- Testing Relationship Parser ---")
        rel_parser = IfcRelationshipParser()
        rel_parser.set_ifc_file(ifc_file)

        if spaces:
            # Test relationships for first space
            relationships = rel_parser.get_space_relationships(space_guid)
            print(f"  ✓ Found {len(relationships)} relationships for space")

            if relationships:
                # Show relationship summary
                summary = rel_parser.get_relationship_summary(space_guid)
                print("  Relationship summary:")
                for rel_type, count in summary.items():
                    print(f"    {rel_type}: {count}")

        # Test getting all spaces
        print("\n--- Testing All Spaces Extraction ---")
        all_spaces = space_extractor.extract_spaces()
        print(f"  ✓ Extracted data for {len(all_spaces)} spaces")

        # Show sample of space names
        if all_spaces:
            print("  Sample space names:")
            for i, space_data in enumerate(all_spaces[:5]):
                area = space_data.quantities.get('NetFloorArea', 'N/A')
                print(f"    {i+1}. {space_data.name} (Area: {area})")

        return True

    except Exception as e:
        print(f"✗ Error processing IFC file: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main test function."""
    print("=== IFC File Handling Test ===")
    print("Testing application's ability to handle the reference IFC file\n")

    success = test_ifc_file_handling()

    if success:
        print("\n✓ All tests passed! Application can handle the IFC reference file.")
    else:
        print("\n✗ Some tests failed. Check the errors above.")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
