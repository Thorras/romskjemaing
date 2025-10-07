#!/usr/bin/env python3
"""
Test both IFC files to verify geometry extraction works with different formats
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append('.')

def test_ifc_file(file_path: str):
    """Test geometry extraction on a single IFC file."""
    print(f"\n📁 Testing: {Path(file_path).name}")
    print("-" * 50)
    
    try:
        from ifc_room_schedule.parser.ifc_file_reader import IfcFileReader
        from ifc_room_schedule.visualization.geometry_extractor import GeometryExtractor
        
        if not Path(file_path).exists():
            print(f"   ❌ File not found: {file_path}")
            return False
        
        # Load file
        reader = IfcFileReader()
        success, message = reader.load_file(file_path)
        
        if not success:
            print(f"   ❌ File loading failed: {message}")
            return False
        
        ifc_file = reader.get_ifc_file()
        spaces = ifc_file.by_type("IfcSpace")
        storeys = ifc_file.by_type("IfcBuildingStorey")
        
        print(f"   ✅ File loaded: {len(spaces)} spaces, {len(storeys)} storeys")
        
        # Test geometry extraction
        extractor = GeometryExtractor()
        
        # Test floor levels
        floor_levels = extractor.get_floor_levels(ifc_file)
        print(f"   📊 Floor levels: {len(floor_levels)}")
        
        for floor in floor_levels:
            print(f"      - {floor.name}: {len(floor.spaces)} spaces at {floor.elevation:.2f}m")
        
        # Test complete extraction
        floor_geometries = extractor.extract_floor_geometry(ifc_file)
        total_rooms = sum(fg.get_room_count() for fg in floor_geometries.values())
        total_area = sum(fg.get_total_area() for fg in floor_geometries.values())
        
        print(f"   🏗️ Geometry extraction: {len(floor_geometries)} floors")
        print(f"      - Total rooms with geometry: {total_rooms}")
        print(f"      - Total area: {total_area:.2f} m²")
        
        # Test space boundary extraction on sample
        if spaces:
            sample_space = spaces[0]
            space_name = getattr(sample_space, 'Name', 'Unknown')
            polygons = extractor.extract_space_boundaries(sample_space)
            print(f"   🔍 Sample space '{space_name}': {len(polygons)} polygons")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Test both IFC files."""
    print("🧪 IFC Geometry Extraction - Multiple File Test")
    print("=" * 60)
    
    test_files = [
        "tesfiler/AkkordSvingen 23_ARK.ifc",
        "tesfiler/DEICH_Test.ifc"
    ]
    
    results = {}
    
    for file_path in test_files:
        results[file_path] = test_ifc_file(file_path)
    
    # Summary
    print(f"\n📊 Test Summary")
    print("=" * 60)
    
    passed = sum(1 for success in results.values() if success)
    total = len(results)
    
    print(f"Files tested: {total}")
    print(f"Successful: {passed}")
    print(f"Failed: {total - passed}")
    
    for file_path, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status} {Path(file_path).name}")
    
    if passed == total:
        print(f"\n🎉 All tests passed! IFC geometry extraction works with multiple file formats.")
        return True
    else:
        print(f"\n⚠️ Some tests failed. Check the output above for details.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)