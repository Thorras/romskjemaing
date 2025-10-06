#!/usr/bin/env python3
"""
Test script for IFC geometry extraction functionality.

This script tests the GeometryExtractor with real IFC files to verify
that 2D floor plan geometry can be extracted correctly.
"""

import sys
import os
import time
from pathlib import Path
from typing import Dict, List, Any

# Add project root to path
sys.path.append('.')

from ifc_room_schedule.parser.ifc_file_reader import IfcFileReader
from ifc_room_schedule.parser.ifc_space_extractor import IfcSpaceExtractor
from ifc_room_schedule.visualization.geometry_extractor import GeometryExtractor, GeometryExtractionError
from ifc_room_schedule.visualization.geometry_models import FloorGeometry, FloorLevel


def test_ifc_file_loading(ifc_path: str) -> bool:
    """Test basic IFC file loading."""
    print(f"\n📁 Testing IFC file loading: {Path(ifc_path).name}")
    
    try:
        reader = IfcFileReader()
        success, message = reader.load_file(ifc_path)
        
        if success:
            ifc_file = reader.get_ifc_file()
            print(f"✓ IFC file loaded successfully")
            
            # Get basic file info
            spaces = ifc_file.by_type("IfcSpace")
            storeys = ifc_file.by_type("IfcBuildingStorey")
            
            print(f"  - Spaces found: {len(spaces)}")
            print(f"  - Building storeys found: {len(storeys)}")
            
            return True
        else:
            print(f"✗ Failed to load IFC file: {message}")
            return False
            
    except Exception as e:
        print(f"✗ Exception during IFC loading: {str(e)}")
        return False


def test_space_extraction(ifc_path: str) -> List[Any]:
    """Test space extraction from IFC file."""
    print(f"\n🏠 Testing space extraction: {Path(ifc_path).name}")
    
    try:
        # Load IFC file
        reader = IfcFileReader()
        success, message = reader.load_file(ifc_path)
        if not success:
            print(f"✗ Failed to load IFC file: {message}")
            return []
        
        # Extract spaces
        extractor = IfcSpaceExtractor()
        extractor.set_ifc_file(reader.get_ifc_file())
        spaces = extractor.extract_spaces()
        
        print(f"✓ Extracted {len(spaces)} spaces")
        
        if spaces:
            # Show sample space info
            sample_space = spaces[0]
            print(f"  Sample space: {sample_space.name} (GUID: {sample_space.guid[:8]}...)")
            
            # Get area from quantities if available
            area = sample_space.quantities.get('NetFloorArea', 0) or sample_space.quantities.get('GrossFloorArea', 0)
            print(f"  Area: {area}m²")
            print(f"  Object type: {sample_space.object_type}")
        
        return spaces
        
    except Exception as e:
        print(f"✗ Exception during space extraction: {str(e)}")
        return []


def test_geometry_extraction(ifc_path: str) -> Dict[str, FloorGeometry]:
    """Test geometry extraction from IFC file."""
    print(f"\n🏗️ Testing geometry extraction: {Path(ifc_path).name}")
    
    try:
        # Load IFC file
        reader = IfcFileReader()
        success, message = reader.load_file(ifc_path)
        if not success:
            print(f"✗ Failed to load IFC file: {message}")
            return {}
        
        # Extract geometry
        geometry_extractor = GeometryExtractor()
        
        def progress_callback(status: str, progress: int):
            print(f"  Progress: {status} ({progress}%)")
        
        start_time = time.time()
        floor_geometries = geometry_extractor.extract_floor_geometry(
            reader.get_ifc_file(), 
            progress_callback=progress_callback
        )
        extraction_time = time.time() - start_time
        
        print(f"✓ Geometry extraction completed in {extraction_time:.2f} seconds")
        print(f"✓ Extracted geometry for {len(floor_geometries)} floors")
        
        # Analyze extracted geometry
        total_rooms = 0
        for floor_id, geometry in floor_geometries.items():
            room_count = geometry.get_room_count()
            total_rooms += room_count
            
            print(f"  Floor {geometry.level.name}: {room_count} rooms")
            if geometry.bounds:
                width = geometry.get_bounds_width()
                height = geometry.get_bounds_height()
                print(f"    Bounds: {width:.1f}m × {height:.1f}m")
        
        print(f"  Total rooms with geometry: {total_rooms}")
        
        return floor_geometries
        
    except GeometryExtractionError as e:
        print(f"✗ Geometry extraction error ({e.error_type}): {str(e)}")
        if e.affected_spaces:
            print(f"  Affected spaces: {len(e.affected_spaces)}")
        return {}
    except Exception as e:
        print(f"✗ Unexpected exception during geometry extraction: {str(e)}")
        return {}


def test_floor_level_detection(ifc_path: str) -> List[FloorLevel]:
    """Test floor level detection."""
    print(f"\n🏢 Testing floor level detection: {Path(ifc_path).name}")
    
    try:
        # Load IFC file
        reader = IfcFileReader()
        success, message = reader.load_file(ifc_path)
        if not success:
            print(f"✗ Failed to load IFC file: {message}")
            return []
        
        # Extract floor levels
        geometry_extractor = GeometryExtractor()
        floor_levels = geometry_extractor.get_floor_levels(reader.get_ifc_file())
        
        print(f"✓ Detected {len(floor_levels)} floor levels")
        
        for floor in floor_levels:
            print(f"  Floor: {floor.name} (Elevation: {floor.elevation:.2f}m, Spaces: {len(floor.spaces)})")
        
        return floor_levels
        
    except Exception as e:
        print(f"✗ Exception during floor level detection: {str(e)}")
        return []


def test_boundary_extraction(ifc_path: str) -> bool:
    """Test space boundary extraction."""
    print(f"\n📐 Testing space boundary extraction: {Path(ifc_path).name}")
    
    try:
        # Load IFC file
        reader = IfcFileReader()
        success, message = reader.load_file(ifc_path)
        if not success:
            print(f"✗ Failed to load IFC file: {message}")
            return False
        
        ifc_file = reader.get_ifc_file()
        spaces = ifc_file.by_type("IfcSpace")
        
        if not spaces:
            print("✗ No spaces found in IFC file")
            return False
        
        # Test boundary extraction on first few spaces
        geometry_extractor = GeometryExtractor()
        successful_extractions = 0
        fallback_extractions = 0
        
        test_count = min(5, len(spaces))  # Test first 5 spaces
        
        for i, space in enumerate(spaces[:test_count]):
            try:
                polygons = geometry_extractor.extract_space_boundaries(space)
                
                if polygons:
                    successful_extractions += 1
                    polygon = polygons[0]  # Take first polygon
                    area = polygon.get_area()
                    bounds = polygon.get_bounds()
                    
                    print(f"  Space {i+1}: {len(polygons)} polygon(s), Area: {area:.2f}m²")
                    
                    # Check if this looks like fallback geometry
                    width = bounds[2] - bounds[0]
                    height = bounds[3] - bounds[1]
                    if abs(width - height) < 0.1 and width in [3.0, 4.0, 5.0]:
                        fallback_extractions += 1
                        print(f"    (Likely fallback geometry: {width:.1f}×{height:.1f})")
                else:
                    print(f"  Space {i+1}: No geometry extracted")
                    
            except Exception as e:
                print(f"  Space {i+1}: Extraction failed - {str(e)}")
        
        print(f"✓ Boundary extraction test completed")
        print(f"  Successful extractions: {successful_extractions}/{test_count}")
        print(f"  Fallback geometries: {fallback_extractions}/{successful_extractions}")
        
        return successful_extractions > 0
        
    except Exception as e:
        print(f"✗ Exception during boundary extraction test: {str(e)}")
        return False


def run_comprehensive_test(ifc_path: str) -> Dict[str, Any]:
    """Run comprehensive test on an IFC file."""
    print(f"\n{'='*60}")
    print(f"COMPREHENSIVE TEST: {Path(ifc_path).name}")
    print(f"{'='*60}")
    
    results = {
        'file_path': ifc_path,
        'file_name': Path(ifc_path).name,
        'file_size_mb': os.path.getsize(ifc_path) / (1024 * 1024),
        'tests': {}
    }
    
    # Test 1: IFC file loading
    results['tests']['ifc_loading'] = test_ifc_file_loading(ifc_path)
    
    # Test 2: Space extraction
    spaces = test_space_extraction(ifc_path)
    results['tests']['space_extraction'] = len(spaces) > 0
    results['space_count'] = len(spaces)
    
    # Test 3: Floor level detection
    floor_levels = test_floor_level_detection(ifc_path)
    results['tests']['floor_detection'] = len(floor_levels) > 0
    results['floor_count'] = len(floor_levels)
    
    # Test 4: Boundary extraction
    results['tests']['boundary_extraction'] = test_boundary_extraction(ifc_path)
    
    # Test 5: Full geometry extraction
    floor_geometries = test_geometry_extraction(ifc_path)
    results['tests']['geometry_extraction'] = len(floor_geometries) > 0
    results['geometry_floor_count'] = len(floor_geometries)
    
    # Calculate total rooms with geometry
    total_rooms_with_geometry = sum(
        geom.get_room_count() for geom in floor_geometries.values()
    )
    results['rooms_with_geometry'] = total_rooms_with_geometry
    
    return results


def main():
    """Main test function."""
    print("IFC Geometry Extraction Test Suite")
    print("=" * 50)
    
    # Find test IFC files
    test_files_dir = Path("tesfiler")
    if not test_files_dir.exists():
        print("✗ Test files directory 'tesfiler' not found")
        return False
    
    ifc_files = list(test_files_dir.glob("*.ifc"))
    if not ifc_files:
        print("✗ No IFC files found in 'tesfiler' directory")
        return False
    
    print(f"Found {len(ifc_files)} IFC test files:")
    for ifc_file in ifc_files:
        size_mb = ifc_file.stat().st_size / (1024 * 1024)
        print(f"  - {ifc_file.name} ({size_mb:.1f} MB)")
    
    # Run tests on each file
    all_results = []
    successful_tests = 0
    
    for ifc_file in ifc_files:
        try:
            results = run_comprehensive_test(str(ifc_file))
            all_results.append(results)
            
            # Check if all tests passed
            if all(results['tests'].values()):
                successful_tests += 1
                
        except Exception as e:
            print(f"\n✗ Failed to test {ifc_file.name}: {str(e)}")
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    
    print(f"Files tested: {len(all_results)}")
    print(f"Fully successful: {successful_tests}")
    
    for results in all_results:
        print(f"\n{results['file_name']} ({results['file_size_mb']:.1f} MB):")
        for test_name, success in results['tests'].items():
            status = "✓" if success else "✗"
            print(f"  {status} {test_name.replace('_', ' ').title()}")
        
        if 'space_count' in results:
            print(f"    Spaces: {results['space_count']}")
        if 'floor_count' in results:
            print(f"    Floors: {results['floor_count']}")
        if 'rooms_with_geometry' in results:
            print(f"    Rooms with geometry: {results['rooms_with_geometry']}")
    
    # Overall result
    if successful_tests == len(all_results) and successful_tests > 0:
        print(f"\n✅ ALL TESTS PASSED! IFC geometry extraction is working correctly.")
        return True
    elif successful_tests > 0:
        print(f"\n⚠️ PARTIAL SUCCESS: {successful_tests}/{len(all_results)} files passed all tests.")
        return True
    else:
        print(f"\n❌ ALL TESTS FAILED! IFC geometry extraction needs attention.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)