"""
Demo script to test geometry extraction with real IFC file.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from ifc_room_schedule.parser.ifc_file_reader import IfcFileReader
from ifc_room_schedule.visualization.geometry_extractor import GeometryExtractor, GeometryExtractionError


def test_geometry_extraction():
    """Test geometry extraction with real IFC file."""
    
    # Test file path
    ifc_file_path = "tesfiler/AkkordSvingen 23_ARK.ifc"
    
    if not Path(ifc_file_path).exists():
        print(f"❌ IFC file not found: {ifc_file_path}")
        return
    
    print("🚀 Testing Geometry Extraction")
    print("=" * 50)
    
    try:
        # Load IFC file
        print(f"📂 Loading IFC file: {ifc_file_path}")
        reader = IfcFileReader()
        success, message = reader.load_file(ifc_file_path)
        
        if not success:
            print(f"❌ Failed to load IFC file: {message}")
            return
        
        ifc_file = reader.get_ifc_file()
        print(f"✅ IFC file loaded successfully")
        
        # Initialize geometry extractor
        print("\n🔧 Initializing GeometryExtractor...")
        extractor = GeometryExtractor()
        
        # Extract floor levels
        print("\n🏢 Extracting floor levels...")
        floor_levels = extractor.get_floor_levels(ifc_file)
        print(f"✅ Found {len(floor_levels)} floor levels:")
        
        for floor in floor_levels:
            print(f"  📏 {floor.name} (ID: {floor.id[:8]}...)")
            print(f"      Elevation: {floor.elevation:.2f}m")
            print(f"      Spaces: {len(floor.spaces)}")
        
        # Extract complete floor geometry
        print(f"\n🗺️ Extracting floor geometry...")
        try:
            floor_geometries = extractor.extract_floor_geometry(ifc_file)
            print(f"✅ Successfully extracted geometry for {len(floor_geometries)} floors:")
            
            for floor_id, geometry in floor_geometries.items():
                print(f"\n  🏗️ Floor: {geometry.level.name}")
                print(f"      Rooms with geometry: {geometry.get_room_count()}")
                print(f"      Total area: {geometry.get_total_area():.2f} m²")
                
                if geometry.bounds:
                    width = geometry.get_bounds_width()
                    height = geometry.get_bounds_height()
                    print(f"      Bounds: {width:.1f}m × {height:.1f}m")
                
                # Show first few rooms
                print(f"      Sample rooms:")
                for i, polygon in enumerate(geometry.room_polygons[:3]):
                    area = polygon.get_area()
                    print(f"        • {polygon.space_name}: {area:.1f} m²")
                
                if len(geometry.room_polygons) > 3:
                    remaining = len(geometry.room_polygons) - 3
                    print(f"        ... and {remaining} more rooms")
        
        except GeometryExtractionError as e:
            print(f"⚠️ Geometry extraction error: {e}")
            print(f"   Error type: {e.error_type}")
            if e.affected_spaces:
                print(f"   Affected spaces: {len(e.affected_spaces)}")
        
        print(f"\n🎉 Geometry extraction test completed!")
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_geometry_extraction()