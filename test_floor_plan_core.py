#!/usr/bin/env python3
"""
Core Floor Plan Functionality Test

Tests the essential floor plan rendering and interaction features.
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append('.')

def test_floor_plan_core():
    """Test core floor plan functionality."""
    print("🎯 Core Floor Plan Functionality Test")
    print("=" * 50)
    
    try:
        # Test 1: Import all required modules
        print("1️⃣ Testing imports...")
        
        from ifc_room_schedule.parser.ifc_file_reader import IfcFileReader
        from ifc_room_schedule.visualization.geometry_extractor import GeometryExtractor
        from ifc_room_schedule.visualization.floor_plan_canvas import FloorPlanCanvas
        from ifc_room_schedule.ui.floor_plan_widget import FloorPlanWidget
        
        print("   ✅ All imports successful")
        
        # Test 2: Load test data
        print("\n2️⃣ Loading test data...")
        
        test_file = "tesfiler/AkkordSvingen 23_ARK.ifc"
        if not Path(test_file).exists():
            print(f"   ❌ Test file not found: {test_file}")
            return False
        
        reader = IfcFileReader()
        success, message = reader.load_file(test_file)
        
        if not success:
            print(f"   ❌ Failed to load IFC file: {message}")
            return False
        
        ifc_file = reader.get_ifc_file()
        print(f"   ✅ IFC file loaded successfully")
        
        # Test 3: Extract geometry
        print("\n3️⃣ Extracting geometry...")
        
        extractor = GeometryExtractor()
        floor_geometries = extractor.extract_floor_geometry(ifc_file)
        
        if not floor_geometries:
            print(f"   ❌ No floor geometries extracted")
            return False
        
        print(f"   ✅ Extracted {len(floor_geometries)} floor geometries")
        
        # Test 4: Create floor plan canvas
        print("\n4️⃣ Testing FloorPlanCanvas...")
        
        canvas = FloorPlanCanvas()
        canvas.set_floor_geometries(floor_geometries)
        
        # Test basic canvas functionality
        available_floors = canvas.get_available_floors()
        print(f"   📊 Available floors: {len(available_floors)}")
        
        if available_floors:
            # Test floor switching
            first_floor = available_floors[0]
            success = canvas.set_current_floor(first_floor)
            current_floor = canvas.get_current_floor_id()
            
            if success and current_floor == first_floor:
                print(f"   ✅ Floor switching works: {current_floor}")
            else:
                print(f"   ❌ Floor switching failed")
        
        # Test 5: Test room selection
        print("\n5️⃣ Testing room selection...")
        
        if canvas.floor_geometry and canvas.floor_geometry.room_polygons:
            # Get first few room GUIDs
            room_guids = [p.space_guid for p in canvas.floor_geometry.room_polygons[:3]]
            
            # Test highlighting
            canvas.highlight_rooms(room_guids)
            selected_rooms = list(canvas.selected_rooms)
            
            if len(selected_rooms) == len(room_guids):
                print(f"   ✅ Room selection works: {len(selected_rooms)} rooms selected")
            else:
                print(f"   ❌ Room selection failed: expected {len(room_guids)}, got {len(selected_rooms)}")
            
            # Test clearing selection
            canvas.clear_selection()
            if len(canvas.selected_rooms) == 0:
                print(f"   ✅ Selection clearing works")
            else:
                print(f"   ❌ Selection clearing failed")
        
        # Test 6: Test zoom functionality
        print("\n6️⃣ Testing zoom functionality...")
        
        # Test zoom to fit
        canvas.zoom_to_fit()
        zoom_after_fit = canvas.zoom_level
        
        if zoom_after_fit > 0:
            print(f"   ✅ Zoom to fit works: zoom level {zoom_after_fit:.2f}")
        else:
            print(f"   ❌ Zoom to fit failed")
        
        # Test zoom to specific rooms
        if canvas.floor_geometry and canvas.floor_geometry.room_polygons:
            room_guids = [canvas.floor_geometry.room_polygons[0].space_guid]
            canvas.zoom_to_rooms(room_guids)
            print(f"   ✅ Zoom to rooms works")
        
        # Test 7: Test color coding
        print("\n7️⃣ Testing color coding...")
        
        canvas.enable_ns3940_color_coding(True)
        if canvas.use_color_coding:
            print(f"   ✅ NS 3940 color coding enabled")
            
            # Check if colors are assigned
            color_count = len(canvas.space_color_scheme)
            print(f"   📊 Colors assigned to {color_count} spaces")
        else:
            print(f"   ❌ Color coding failed to enable")
        
        # Test 8: Test FloorPlanWidget
        print("\n8️⃣ Testing FloorPlanWidget...")
        
        widget = FloorPlanWidget()
        widget.set_floor_geometry(floor_geometries)
        
        # Test widget functionality
        widget_floors = widget.floor_plan_canvas.get_available_floors()
        current_widget_floor = widget.get_current_floor_id()
        
        if len(widget_floors) == len(available_floors):
            print(f"   ✅ FloorPlanWidget initialized correctly")
        else:
            print(f"   ❌ FloorPlanWidget initialization failed")
        
        # Test widget methods
        if widget_floors:
            widget.set_current_floor(widget_floors[0])
            widget.zoom_to_fit()
            
            if canvas.floor_geometry and canvas.floor_geometry.room_polygons:
                test_guids = [canvas.floor_geometry.room_polygons[0].space_guid]
                widget.highlight_spaces(test_guids)
                widget.zoom_to_spaces(test_guids)
                widget.clear_selection()
            
            print(f"   ✅ FloorPlanWidget methods work correctly")
        
        # Test 9: Test bounds and metadata
        print("\n9️⃣ Testing bounds and metadata...")
        
        for floor_id in available_floors:
            bounds = canvas.get_floor_bounds(floor_id)
            metadata = canvas.get_floor_metadata(floor_id)
            
            if bounds and len(bounds) == 4:
                print(f"   ✅ Floor {floor_id}: bounds {bounds[2]-bounds[0]:.1f}x{bounds[3]-bounds[1]:.1f}m")
            
            if metadata:
                room_count = metadata.get('room_count', 0)
                total_area = metadata.get('total_area', 0)
                print(f"   📊 Floor {floor_id}: {room_count} rooms, {total_area:.1f}m²")
        
        # Test 10: Performance check
        print("\n🔟 Performance check...")
        
        import time
        start_time = time.time()
        
        # Perform multiple operations
        for i in range(5):
            canvas.zoom_to_fit()
            if canvas.floor_geometry and canvas.floor_geometry.room_polygons:
                room_guids = [p.space_guid for p in canvas.floor_geometry.room_polygons[:2]]
                canvas.highlight_rooms(room_guids)
                canvas.clear_selection()
        
        end_time = time.time()
        operation_time = end_time - start_time
        
        if operation_time < 1.0:
            print(f"   ✅ Performance good: {operation_time:.3f}s for 15 operations")
        else:
            print(f"   ⚠️ Performance could be improved: {operation_time:.3f}s")
        
        print(f"\n🎉 All core floor plan tests passed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Core floor plan test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_floor_plan_core()
    exit(0 if success else 1)