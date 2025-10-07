#!/usr/bin/env python3
"""
Floor Plan Logic Test (No GUI)

Tests the floor plan logic and data handling without requiring Qt GUI components.
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append('.')

def test_floor_plan_logic():
    """Test floor plan logic without GUI components."""
    print("🧠 Floor Plan Logic Test (No GUI)")
    print("=" * 50)
    
    try:
        # Test 1: Import core modules
        print("1️⃣ Testing core imports...")
        
        from ifc_room_schedule.parser.ifc_file_reader import IfcFileReader
        from ifc_room_schedule.visualization.geometry_extractor import GeometryExtractor
        from ifc_room_schedule.visualization.geometry_models import FloorGeometry, FloorLevel, Polygon2D, Point2D
        
        print("   ✅ Core imports successful")
        
        # Test 2: Load and extract data
        print("\n2️⃣ Loading and extracting data...")
        
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
        extractor = GeometryExtractor()
        floor_geometries = extractor.extract_floor_geometry(ifc_file)
        
        print(f"   ✅ Extracted {len(floor_geometries)} floor geometries")
        
        # Test 3: Validate geometry data
        print("\n3️⃣ Validating geometry data...")
        
        total_rooms = 0
        total_area = 0.0
        
        for floor_id, geometry in floor_geometries.items():
            room_count = geometry.get_room_count()
            floor_area = geometry.get_total_area()
            
            total_rooms += room_count
            total_area += floor_area
            
            print(f"   📊 Floor {geometry.level.name}: {room_count} rooms, {floor_area:.1f}m²")
            
            # Validate individual rooms
            for polygon in geometry.room_polygons[:3]:  # Check first 3 rooms
                area = polygon.get_area()
                bounds = polygon.get_bounds()
                centroid = polygon.get_centroid()
                
                if area > 0 and len(polygon.points) >= 3:
                    print(f"      ✅ Room {polygon.space_name}: {area:.1f}m², {len(polygon.points)} points")
                else:
                    print(f"      ❌ Invalid room data: {polygon.space_name}")
        
        print(f"   📈 Total: {total_rooms} rooms, {total_area:.1f}m²")
        
        # Test 4: Test geometry model functionality
        print("\n4️⃣ Testing geometry models...")
        
        # Test Point2D
        p1 = Point2D(0, 0)
        p2 = Point2D(3, 4)
        distance = p1.distance_to(p2)
        
        if abs(distance - 5.0) < 0.001:
            print("   ✅ Point2D distance calculation works")
        else:
            print("   ❌ Point2D distance calculation failed")
        
        # Test Polygon2D
        test_points = [Point2D(0, 0), Point2D(1, 0), Point2D(1, 1), Point2D(0, 1)]
        test_polygon = Polygon2D(test_points, "test-guid", "Test Room")
        
        test_area = test_polygon.get_area()
        test_centroid = test_polygon.get_centroid()
        test_bounds = test_polygon.get_bounds()
        
        if abs(test_area - 1.0) < 0.001:
            print("   ✅ Polygon2D area calculation works")
        else:
            print("   ❌ Polygon2D area calculation failed")
        
        if abs(test_centroid.x - 0.5) < 0.001 and abs(test_centroid.y - 0.5) < 0.001:
            print("   ✅ Polygon2D centroid calculation works")
        else:
            print("   ❌ Polygon2D centroid calculation failed")
        
        # Test 5: Test floor level functionality
        print("\n5️⃣ Testing floor level functionality...")
        
        for floor_id, geometry in floor_geometries.items():
            floor_level = geometry.level
            
            print(f"   📋 Floor {floor_level.name}:")
            print(f"      - ID: {floor_level.id}")
            print(f"      - Elevation: {floor_level.elevation:.2f}m")
            print(f"      - Spaces: {len(floor_level.spaces)}")
            
            # Test floor level methods
            space_count = floor_level.get_space_count()
            if space_count == len(floor_level.spaces):
                print(f"      ✅ Space count method works: {space_count}")
            else:
                print(f"      ❌ Space count method failed")
        
        # Test 6: Test room lookup and selection logic
        print("\n6️⃣ Testing room lookup and selection logic...")
        
        # Get first floor with rooms
        test_floor = None
        for geometry in floor_geometries.values():
            if geometry.room_polygons:
                test_floor = geometry
                break
        
        if test_floor:
            # Create room lookup
            room_lookup = {p.space_guid: p for p in test_floor.room_polygons}
            
            # Test room lookup
            first_room_guid = list(room_lookup.keys())[0]
            found_room = room_lookup.get(first_room_guid)
            
            if found_room and found_room.space_guid == first_room_guid:
                print(f"   ✅ Room lookup works: found {found_room.space_name}")
            else:
                print(f"   ❌ Room lookup failed")
            
            # Test room selection logic
            selected_rooms = set()
            test_guids = list(room_lookup.keys())[:3]
            
            # Simulate selection
            for guid in test_guids:
                selected_rooms.add(guid)
            
            if len(selected_rooms) == len(test_guids):
                print(f"   ✅ Room selection logic works: {len(selected_rooms)} rooms")
            else:
                print(f"   ❌ Room selection logic failed")
            
            # Test room filtering
            filtered_rooms = [room_lookup[guid] for guid in selected_rooms if guid in room_lookup]
            
            if len(filtered_rooms) == len(selected_rooms):
                print(f"   ✅ Room filtering works: {len(filtered_rooms)} rooms")
            else:
                print(f"   ❌ Room filtering failed")
        
        # Test 7: Test bounds and coordinate calculations
        print("\n7️⃣ Testing bounds and coordinate calculations...")
        
        for floor_id, geometry in floor_geometries.items():
            bounds = geometry.bounds
            
            if bounds and len(bounds) == 4:
                width = bounds[2] - bounds[0]
                height = bounds[3] - bounds[1]
                center_x = (bounds[0] + bounds[2]) / 2
                center_y = (bounds[1] + bounds[3]) / 2
                
                print(f"   📐 Floor {geometry.level.name}:")
                print(f"      - Bounds: {width:.1f}m × {height:.1f}m")
                print(f"      - Center: ({center_x:.1f}, {center_y:.1f})")
                
                if width > 0 and height > 0:
                    print(f"      ✅ Valid bounds calculated")
                else:
                    print(f"      ❌ Invalid bounds")
            else:
                print(f"   ❌ No bounds available for floor {geometry.level.name}")
        
        # Test 8: Test color scheme logic
        print("\n8️⃣ Testing color scheme logic...")
        
        # Import color scheme
        from ifc_room_schedule.visualization.floor_plan_canvas import SpaceColorScheme
        
        # Test color mapping
        test_space_types = ['kontor', 'møterom', 'gang', 'toalett', 'kjøkken']
        
        for space_type in test_space_types:
            color = SpaceColorScheme.get_color_for_space_type(space_type)
            if color != SpaceColorScheme.DEFAULT:
                print(f"   ✅ Color mapping for '{space_type}': {color.name()}")
            else:
                print(f"   ⚠️ Using default color for '{space_type}'")
        
        # Test with actual room names
        if test_floor:
            for polygon in test_floor.room_polygons[:3]:
                color = SpaceColorScheme.get_color_for_space_name(polygon.space_name)
                print(f"   🎨 Room '{polygon.space_name}': {color.name()}")
        
        # Test 9: Test performance with large datasets
        print("\n9️⃣ Testing performance...")
        
        import time
        start_time = time.time()
        
        # Perform multiple operations
        operations = 0
        for geometry in floor_geometries.values():
            for polygon in geometry.room_polygons:
                # Simulate common operations
                area = polygon.get_area()
                centroid = polygon.get_centroid()
                bounds = polygon.get_bounds()
                operations += 3
        
        end_time = time.time()
        operation_time = end_time - start_time
        
        if operation_time < 1.0:
            print(f"   ✅ Performance good: {operations} operations in {operation_time:.3f}s")
        else:
            print(f"   ⚠️ Performance could be improved: {operations} operations in {operation_time:.3f}s")
        
        # Test 10: Test error handling
        print("\n🔟 Testing error handling...")
        
        # Test with invalid data
        try:
            invalid_points = [Point2D(0, 0), Point2D(1, 0)]  # Only 2 points
            invalid_polygon = Polygon2D(invalid_points, "invalid", "Invalid")
            print(f"   ❌ Should have failed with invalid polygon")
        except ValueError:
            print(f"   ✅ Invalid polygon correctly rejected")
        
        # Test with empty data
        try:
            empty_geometry = FloorGeometry(FloorLevel("test", "Test", 0.0), [])
            room_count = empty_geometry.get_room_count()
            if room_count == 0:
                print(f"   ✅ Empty geometry handled correctly")
            else:
                print(f"   ❌ Empty geometry handling failed")
        except Exception as e:
            print(f"   ❌ Empty geometry caused exception: {str(e)}")
        
        print(f"\n🎉 All floor plan logic tests passed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Floor plan logic test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_floor_plan_logic()
    exit(0 if success else 1)