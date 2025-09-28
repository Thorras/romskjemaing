#!/usr/bin/env python3
"""
Test script for Task 8: Test with existing test files

This script tests that both AkkordSvingen 23_ARK.ifc and DEICH_Test.ifc
load without freezing and within reasonable time limits.

Requirements tested:
- 4.1: AkkordSvingen 23_ARK.ifc loads without problems
- 4.2: DEICH_Test.ifc loads without problems  
- 4.3: All spaces and surfaces are available for editing
"""

import sys
import os
import time
import threading
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from ifc_room_schedule.parser.ifc_file_reader import IfcFileReader
from ifc_room_schedule.parser.ifc_space_extractor import IfcSpaceExtractor
from ifc_room_schedule.parser.ifc_surface_extractor import IfcSurfaceExtractor

class TestResult:
    def __init__(self, test_name):
        self.test_name = test_name
        self.success = False
        self.error_message = ""
        self.load_time = 0
        self.spaces_count = 0
        self.surfaces_count = 0
        
    def __str__(self):
        status = "✅ PASS" if self.success else "❌ FAIL"
        result = f"{status} {self.test_name}\n"
        if self.success:
            result += f"  Load time: {self.load_time:.2f}s\n"
            result += f"  Spaces found: {self.spaces_count}\n"
            result += f"  Surfaces found: {self.surfaces_count}\n"
        else:
            result += f"  Error: {self.error_message}\n"
        return result

def test_file_loading_with_timeout(file_path, timeout_seconds=30):
    """Test file loading with timeout to prevent freezing"""
    result = TestResult(f"Loading {os.path.basename(file_path)}")
    
    # Use threading to implement timeout
    loading_complete = threading.Event()
    loading_error = None
    ifc_file = None
    spaces = []
    surfaces = []
    
    def load_file():
        nonlocal loading_error, ifc_file, spaces, surfaces
        try:
            print(f"  Starting to load {os.path.basename(file_path)}...")
            
            # Load IFC file
            reader = IfcFileReader()
            success, message = reader.load_file(file_path)
            
            if not success:
                loading_error = f"Failed to load file: {message}"
                loading_complete.set()
                return
                
            ifc_file = reader.ifc_file
            print(f"  IFC file loaded successfully")
            
            # Extract spaces
            space_extractor = IfcSpaceExtractor(ifc_file)
            spaces = space_extractor.extract_spaces()
            print(f"  Extracted {len(spaces)} spaces")
            
            # Extract surfaces for each space
            surface_extractor = IfcSurfaceExtractor(ifc_file)
            all_surfaces = []
            for space in spaces:
                space_surfaces = surface_extractor.extract_surfaces_for_space(space.guid)
                all_surfaces.extend(space_surfaces)
            
            surfaces = all_surfaces
            print(f"  Extracted {len(surfaces)} surfaces")
            
        except Exception as e:
            loading_error = str(e)
        finally:
            loading_complete.set()
    
    # Start loading in separate thread
    start_time = time.time()
    loading_thread = threading.Thread(target=load_file)
    loading_thread.daemon = True
    loading_thread.start()
    
    # Wait for completion or timeout
    if loading_complete.wait(timeout_seconds):
        end_time = time.time()
        result.load_time = end_time - start_time
        
        if loading_error:
            result.error_message = loading_error
        else:
            result.success = True
            result.spaces_count = len(spaces)
            result.surfaces_count = len(surfaces)
            
            # Verify we have meaningful data
            if result.spaces_count == 0:
                result.success = False
                result.error_message = "No spaces found in IFC file"
            elif result.surfaces_count == 0:
                result.success = False
                result.error_message = "No surfaces found in IFC file"
    else:
        result.error_message = f"Loading timed out after {timeout_seconds} seconds"
        # Try to stop the thread (though this is not guaranteed)
        loading_complete.set()
    
    return result

def test_reasonable_time_limits(results):
    """Test that files load within reasonable time limits"""
    time_test = TestResult("Reasonable time limits")
    
    max_reasonable_time = 15.0  # 15 seconds should be more than enough for small files
    
    for result in results:
        if result.success and result.load_time > max_reasonable_time:
            time_test.error_message = f"{result.test_name} took {result.load_time:.2f}s (> {max_reasonable_time}s)"
            return time_test
    
    time_test.success = True
    return time_test

def main():
    print("=" * 60)
    print("Task 8: Testing existing test files")
    print("=" * 60)
    
    # Test file paths
    test_files = [
        "tesfiler/AkkordSvingen 23_ARK.ifc",
        "tesfiler/DEICH_Test.ifc"
    ]
    
    # Check that test files exist
    for file_path in test_files:
        if not os.path.exists(file_path):
            print(f"❌ FAIL: Test file not found: {file_path}")
            return False
    
    print(f"Found {len(test_files)} test files to process\n")
    
    # Test each file
    results = []
    for file_path in test_files:
        print(f"Testing {os.path.basename(file_path)}:")
        result = test_file_loading_with_timeout(file_path, timeout_seconds=30)
        results.append(result)
        print(f"  {result}")
    
    # Test time limits
    print("Testing reasonable time limits:")
    time_result = test_reasonable_time_limits(results)
    results.append(time_result)
    print(f"  {time_result}")
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for r in results if r.success)
    total = len(results)
    
    for result in results:
        print(result)
    
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests PASSED! Both test files load successfully without freezing.")
        return True
    else:
        print("❌ Some tests FAILED. Check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)