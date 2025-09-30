"""
Test Comprehensive Room Schedule

Tests for the comprehensive room schedule functionality.
"""

import unittest
import json
import tempfile
import os
from pathlib import Path

from ifc_room_schedule.data.space_model import SpaceData
from ifc_room_schedule.data.comprehensive_room_schedule_model import ComprehensiveRoomSchedule
from ifc_room_schedule.mappers.comprehensive_room_mapper import ComprehensiveRoomMapper
from ifc_room_schedule.export.comprehensive_json_builder import ComprehensiveJsonBuilder


class TestComprehensiveRoomSchedule(unittest.TestCase):
    """Test comprehensive room schedule functionality."""
    
    def setUp(self):
        """Set up test data."""
        # Create test space data
        self.test_space = SpaceData(
            guid="test-space-guid-001",
            name="SPC-02-A101-111-003",
            long_name="Stue | 02/A101 | NS3940:111",
            description="Test living room",
            object_type="IfcSpace",
            zone_category="A101",
            number="003",
            elevation=0.0,
            quantities={
                "NetArea": 25.5,
                "GrossArea": 27.0,
                "Height": 2.4,
                "Perimeter": 20.0,
                "Volume": 61.2
            }
        )
        
        self.project_info = {
            "project_id": "PRJ-2024-001",
            "project_name": "Test Building Project",
            "building_id": "BLD-A",
            "building_name": "Building A",
            "phase": "Detaljprosjektering",
            "state": "Utkast",
            "created_by": "Test User"
        }
        
        self.ifc_info = {
            "file_name": "test_building.ifc",
            "ifc_version": "IFC4",
            "discipline": "ARK",
            "site_guid": "site-guid-001",
            "building_guid": "building-guid-001",
            "storey_guid": "storey-guid-001"
        }
        
        self.user_data = {
            "performance_requirements": {
                "fire": {
                    "fire_class": "Standard",
                    "door_rating": "EI30"
                },
                "acoustics": {
                    "class_ns8175": "B",
                    "rw_dB": 45.0
                },
                "lighting": {
                    "task_lux": 200,
                    "emergency_lighting": False
                }
            },
            "finishes": {
                "floor": {
                    "system": "Parkett",
                    "layers": [
                        {
                            "product": "Eik parkett",
                            "thickness_mm": 14,
                            "supplier": "Tarkett"
                        }
                    ]
                }
            },
            "notes": "Test room with comprehensive data"
        }
    
    def test_comprehensive_room_schedule_creation(self):
        """Test creating a comprehensive room schedule."""
        schedule = ComprehensiveRoomSchedule()
        
        # Test default values
        self.assertEqual(schedule.meta.schema_version, "1.1.0")
        self.assertEqual(schedule.meta.locale, "nb-NO")
        self.assertEqual(schedule.identification.project_name, None)
        
        # Test to_dict conversion
        schedule_dict = schedule.to_dict()
        self.assertIn("meta", schedule_dict)
        self.assertIn("identification", schedule_dict)
        self.assertIn("ifc", schedule_dict)
        self.assertIn("geometry", schedule_dict)
    
    def test_comprehensive_room_mapper(self):
        """Test the comprehensive room mapper."""
        mapper = ComprehensiveRoomMapper()
        
        # Map space to comprehensive schedule
        schedule = mapper.map_space_to_comprehensive_schedule(
            self.test_space,
            self.project_info,
            self.ifc_info,
            self.user_data
        )
        
        # Verify basic mapping
        self.assertEqual(schedule.identification.room_name, "SPC-02-A101-111-003")
        self.assertEqual(schedule.identification.project_name, "Test Building Project")
        self.assertEqual(schedule.ifc.space_global_id, "test-space-guid-001")
        self.assertEqual(schedule.geometry.area_nett_m2, 25.5)
        self.assertEqual(schedule.geometry.clear_height_m, 2.4)
        
        # Verify user data integration
        self.assertEqual(schedule.performance_requirements.fire.fire_class, "Standard")
        self.assertEqual(schedule.performance_requirements.acoustics.class_ns8175, "B")
        self.assertEqual(schedule.notes, "Test room with comprehensive data")
    
    def test_comprehensive_json_builder(self):
        """Test the comprehensive JSON builder."""
        builder = ComprehensiveJsonBuilder()
        builder.set_source_file("test_building.ifc")
        builder.set_ifc_version("IFC4")
        
        # Test single room JSON
        json_data = builder.build_single_room_json(
            self.test_space,
            self.project_info,
            self.user_data
        )
        
        # Verify JSON structure
        self.assertIn("meta", json_data)
        self.assertIn("identification", json_data)
        self.assertIn("ifc", json_data)
        self.assertIn("geometry", json_data)
        self.assertIn("performance_requirements", json_data)
        
        # Verify specific values
        self.assertEqual(json_data["identification"]["room_name"], "SPC-02-A101-111-003")
        self.assertEqual(json_data["geometry"]["area_nett_m2"], 25.5)
        self.assertEqual(json_data["performance_requirements"]["fire"]["fire_class"], "Standard")
    
    def test_comprehensive_json_export(self):
        """Test exporting comprehensive JSON to file."""
        builder = ComprehensiveJsonBuilder()
        builder.set_source_file("test_building.ifc")
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # Export single room
            success = builder.write_single_room_json_file(
                temp_path,
                self.test_space,
                self.project_info,
                self.user_data
            )
            
            self.assertTrue(success)
            self.assertTrue(os.path.exists(temp_path))
            
            # Verify file content
            with open(temp_path, 'r', encoding='utf-8') as f:
                exported_data = json.load(f)
            
            self.assertIn("meta", exported_data)
            self.assertIn("identification", exported_data)
            self.assertEqual(exported_data["identification"]["room_name"], "SPC-02-A101-111-003")
            
        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_user_input_template_creation(self):
        """Test creating user input templates."""
        builder = ComprehensiveJsonBuilder()
        
        # Create temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create templates
            created_files = builder.create_user_input_templates([self.test_space], temp_dir)
            
            self.assertEqual(len(created_files), 1)
            self.assertTrue(os.path.exists(created_files[0]))
            
            # Verify template content
            with open(created_files[0], 'r', encoding='utf-8') as f:
                template_data = json.load(f)
            
            self.assertEqual(template_data["space_guid"], "test-space-guid-001")
            self.assertEqual(template_data["space_name"], "SPC-02-A101-111-003")
            self.assertIn("performance_requirements", template_data)
            self.assertIn("finishes", template_data)
    
    def test_multiple_spaces_export(self):
        """Test exporting multiple spaces."""
        # Create additional test space
        test_space_2 = SpaceData(
            guid="test-space-guid-002",
            name="SPC-02-A101-130-001",
            long_name="Bad | 02/A101 | NS3940:130",
            description="Test bathroom",
            object_type="IfcSpace",
            zone_category="A101",
            number="001",
            elevation=0.0,
            quantities={
                "NetArea": 5.2,
                "GrossArea": 5.8,
                "Height": 2.4,
                "Perimeter": 9.4,
                "Volume": 12.5
            }
        )
        
        spaces = [self.test_space, test_space_2]
        
        # User data for multiple spaces
        user_data_per_space = {
            "test-space-guid-001": self.user_data,
            "test-space-guid-002": {
                "performance_requirements": {
                    "fire": {"fire_class": "Standard"},
                    "ventilation": {"airflow_extract_m3h": 108.0}
                },
                "notes": "Bathroom with ventilation"
            }
        }
        
        builder = ComprehensiveJsonBuilder()
        
        # Build JSON for multiple spaces
        json_data = builder.build_comprehensive_json_structure(
            spaces,
            self.project_info,
            user_data_per_space
        )
        
        self.assertEqual(len(json_data), 2)
        
        # Verify first space
        space_1_data = json_data[0]
        self.assertEqual(space_1_data["identification"]["room_name"], "SPC-02-A101-111-003")
        self.assertEqual(space_1_data["notes"], "Test room with comprehensive data")
        
        # Verify second space
        space_2_data = json_data[1]
        self.assertEqual(space_2_data["identification"]["room_name"], "SPC-02-A101-130-001")
        self.assertEqual(space_2_data["notes"], "Bathroom with ventilation")
    
    def test_json_validation(self):
        """Test JSON data validation."""
        builder = ComprehensiveJsonBuilder()
        
        # Create valid JSON data
        json_data = [builder.build_single_room_json(self.test_space, self.project_info, self.user_data)]
        
        # Test validation
        is_valid, errors = builder.validate_comprehensive_data(json_data)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
        
        # Test with invalid data (missing required section)
        invalid_data = [{"meta": {"schema_version": "1.1.0"}}]  # Missing other required sections
        is_valid, errors = builder.validate_comprehensive_data(invalid_data)
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)


if __name__ == '__main__':
    unittest.main()