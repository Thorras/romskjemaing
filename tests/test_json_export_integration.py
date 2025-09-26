"""
Integration tests for JSON export functionality.
"""

import pytest
import json
import tempfile
import os
from pathlib import Path

from ifc_room_schedule.export.json_builder import JsonBuilder
from ifc_room_schedule.data.space_repository import SpaceRepository
from ifc_room_schedule.data.space_model import SpaceData
from ifc_room_schedule.data.surface_model import SurfaceData
from ifc_room_schedule.data.space_boundary_model import SpaceBoundaryData
from ifc_room_schedule.data.relationship_model import RelationshipData


class TestJsonExportIntegration:
    """Integration tests for JSON export with SpaceRepository."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.space_repository = SpaceRepository()
        self.json_builder = JsonBuilder()
        
        # Create comprehensive test data
        self.setup_test_spaces()
    
    def setup_test_spaces(self):
        """Set up test spaces with comprehensive data."""
        # Space 1: Office with surfaces and boundaries
        space1 = SpaceData(
            guid="space-guid-001",
            name="Office 101",
            long_name="Executive Office 101",
            description="Corner office with windows",
            object_type="Office",
            zone_category="Work",
            number="101",
            elevation=0.0,
            quantities={
                "Height": 3.0,
                "Area": 25.0,
                "Volume": 75.0,
                "FinishFloorHeight": 0.1,
                "FinishCeilingHeight": 2.8
            },
            processed=True
        )
        
        # Add surfaces to space 1
        surfaces1 = [
            SurfaceData(
                id="surface-001-wall-north",
                type="Wall",
                area=12.0,
                material="Gypsum Board",
                ifc_type="IfcWall",
                related_space_guid="space-guid-001",
                user_description="North wall with window",
                properties={"Thickness": 0.15, "FireRating": "1 hour"}
            ),
            SurfaceData(
                id="surface-001-wall-south",
                type="Wall",
                area=12.0,
                material="Gypsum Board",
                ifc_type="IfcWall",
                related_space_guid="space-guid-001",
                user_description="South wall to corridor"
            ),
            SurfaceData(
                id="surface-001-floor",
                type="Floor",
                area=25.0,
                material="Carpet",
                ifc_type="IfcSlab",
                related_space_guid="space-guid-001",
                user_description="Carpeted floor"
            ),
            SurfaceData(
                id="surface-001-ceiling",
                type="Ceiling",
                area=25.0,
                material="Acoustic Tile",
                ifc_type="IfcSlab",
                related_space_guid="space-guid-001",
                user_description="Drop ceiling with acoustic tiles"
            )
        ]
        
        for surface in surfaces1:
            space1.add_surface(surface)
        
        # Add space boundaries to space 1
        boundaries1 = [
            SpaceBoundaryData(
                id="boundary-001-north",
                guid="boundary-guid-001-north",
                name="North Wall Boundary",
                description="Boundary to exterior north wall",
                physical_or_virtual_boundary="Physical",
                internal_or_external_boundary="External",
                related_building_element_guid="wall-guid-north-001",
                related_building_element_name="North Exterior Wall",
                related_building_element_type="IfcWall",
                related_space_guid="space-guid-001",
                boundary_surface_type="Wall",
                boundary_orientation="North",
                calculated_area=12.0,
                boundary_level=1,
                display_label="North Wall to Exterior",
                thermal_properties={"U-Value": 0.25, "R-Value": 4.0},
                material_properties={"Material": "Concrete Block", "Thickness": 0.20}
            ),
            SpaceBoundaryData(
                id="boundary-001-south",
                guid="boundary-guid-001-south",
                name="South Wall Boundary",
                description="Boundary to corridor",
                physical_or_virtual_boundary="Physical",
                internal_or_external_boundary="Internal",
                related_building_element_guid="wall-guid-south-001",
                related_building_element_name="Interior Partition",
                related_building_element_type="IfcWall",
                related_space_guid="space-guid-001",
                adjacent_space_guid="space-guid-corridor",
                adjacent_space_name="Main Corridor",
                boundary_surface_type="Wall",
                boundary_orientation="South",
                calculated_area=12.0,
                boundary_level=2,
                display_label="South Wall to Main Corridor"
            )
        ]
        
        for boundary in boundaries1:
            space1.add_space_boundary(boundary)
        
        # Add relationships to space 1
        relationships1 = [
            RelationshipData(
                related_entity_guid="building-guid-main",
                related_entity_name="Main Building",
                related_entity_description="Primary office building",
                relationship_type="Contains",
                ifc_relationship_type="IfcRelContainedInSpatialStructure"
            ),
            RelationshipData(
                related_entity_guid="floor-guid-001",
                related_entity_name="First Floor",
                related_entity_description="Ground floor level",
                relationship_type="Contains",
                ifc_relationship_type="IfcRelContainedInSpatialStructure"
            )
        ]
        
        for relationship in relationships1:
            space1.add_relationship(relationship)
        
        # Add user descriptions
        space1.set_user_description("general", "Executive corner office with excellent natural light")
        space1.set_user_description("usage", "Primary workspace for department head")
        
        # Space 2: Conference room
        space2 = SpaceData(
            guid="space-guid-002",
            name="Conference Room A",
            long_name="Large Conference Room A",
            description="Main conference room for meetings",
            object_type="Meeting",
            zone_category="Meeting",
            number="A",
            elevation=0.0,
            quantities={
                "Height": 3.5,
                "Area": 40.0,
                "Volume": 140.0
            },
            processed=False  # Not yet processed
        )
        
        # Add minimal surface data to space 2
        surface2 = SurfaceData(
            id="surface-002-floor",
            type="Floor",
            area=40.0,
            material="Hardwood",
            ifc_type="IfcSlab",
            related_space_guid="space-guid-002"
        )
        space2.add_surface(surface2)
        
        # Add spaces to repository
        self.space_repository.add_space(space1)
        self.space_repository.add_space(space2)
    
    def test_export_from_repository(self):
        """Test exporting data from SpaceRepository."""
        # Get all spaces from repository
        all_spaces = self.space_repository.get_all_spaces()
        
        # Set up JSON builder with metadata
        self.json_builder.set_source_file("/path/to/test_building.ifc")
        self.json_builder.set_ifc_version("IFC4")
        
        # Build JSON structure
        json_structure = self.json_builder.build_json_structure(all_spaces)
        
        # Verify structure
        assert "metadata" in json_structure
        assert "spaces" in json_structure
        assert "summary" in json_structure
        
        # Verify metadata
        metadata = json_structure["metadata"]
        assert metadata["source_file"] == "test_building.ifc"
        assert metadata["ifc_version"] == "IFC4"
        assert "export_date" in metadata
        
        # Verify spaces
        spaces = json_structure["spaces"]
        assert len(spaces) == 2
        
        # Find office space
        office_space = next(s for s in spaces if s["properties"]["name"] == "Office 101")
        assert office_space["guid"] == "space-guid-001"
        assert len(office_space["surfaces"]) == 4
        assert len(office_space["space_boundaries"]) == 2
        assert len(office_space["relationships"]) == 2
        
        # Verify user descriptions
        user_descriptions = office_space["properties"]["user_descriptions"]
        assert "general" in user_descriptions
        assert "usage" in user_descriptions
        
        # Find conference room
        conf_space = next(s for s in spaces if s["properties"]["name"] == "Conference Room A")
        assert conf_space["guid"] == "space-guid-002"
        assert len(conf_space["surfaces"]) == 1
        assert conf_space["properties"]["processed"] is False
        
        # Verify summary
        summary = json_structure["summary"]
        assert summary["total_spaces"] == 2
        assert summary["processed_spaces"] == 1
        assert summary["total_surface_area"] == 114.0  # 74 + 40
        
        # Verify surface areas by type
        surface_areas = summary["surface_area_by_type"]
        assert surface_areas["Wall"] == 24.0
        assert surface_areas["Floor"] == 65.0  # 25 + 40
        assert surface_areas["Ceiling"] == 25.0
        
        # Verify boundary areas
        assert summary["total_boundary_area"] == 24.0
        boundary_areas = summary["boundary_area_by_type"]
        assert boundary_areas["Wall"] == 24.0
        
        # Verify boundary counts
        boundary_counts = summary["boundary_counts"]
        assert boundary_counts["physical_boundaries"] == 2
        assert boundary_counts["virtual_boundaries"] == 0
        assert boundary_counts["external_boundaries"] == 1
        assert boundary_counts["internal_boundaries"] == 1
        assert boundary_counts["first_level_boundaries"] == 1
        assert boundary_counts["second_level_boundaries"] == 1
    
    def test_complete_export_workflow(self):
        """Test complete export workflow from repository to file."""
        # Get spaces from repository
        all_spaces = self.space_repository.get_all_spaces()
        
        # Set up JSON builder
        self.json_builder.set_source_file("/path/to/test_building.ifc")
        self.json_builder.set_ifc_version("IFC4")
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            temp_filename = temp_file.name
        
        try:
            # Export to JSON
            success, messages = self.json_builder.export_to_json(
                all_spaces, 
                temp_filename,
                metadata={"project_name": "Test Building Project"}
            )
            
            assert success is True
            assert len(messages) == 1
            assert "Successfully exported 2 spaces" in messages[0]
            
            # Verify file exists
            assert os.path.exists(temp_filename)
            
            # Load and verify JSON content
            with open(temp_filename, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
            
            # Verify loaded data structure
            assert "metadata" in loaded_data
            assert "spaces" in loaded_data
            assert "summary" in loaded_data
            
            # Verify custom metadata was included
            assert loaded_data["metadata"]["project_name"] == "Test Building Project"
            
            # Verify data integrity
            assert len(loaded_data["spaces"]) == 2
            assert loaded_data["summary"]["total_spaces"] == 2
            
            # Verify specific space data
            office_space = next(s for s in loaded_data["spaces"] 
                              if s["properties"]["name"] == "Office 101")
            
            # Check that all data types are preserved
            assert isinstance(office_space["properties"]["elevation"], (int, float))
            assert isinstance(office_space["properties"]["quantities"], dict)
            assert isinstance(office_space["surfaces"], list)
            assert isinstance(office_space["space_boundaries"], list)
            assert isinstance(office_space["relationships"], list)
            
            # Verify space boundary data integrity
            north_boundary = next(b for b in office_space["space_boundaries"] 
                                if b["boundary_orientation"] == "North")
            assert north_boundary["calculated_area"] == 12.0
            assert north_boundary["thermal_properties"]["U-Value"] == 0.25
            assert north_boundary["boundary_level"] == 1
            
        finally:
            if os.path.exists(temp_filename):
                os.unlink(temp_filename)
    
    def test_export_with_validation_errors(self):
        """Test export behavior when validation finds issues."""
        # Create spaces with some missing data
        all_spaces = self.space_repository.get_all_spaces()
        
        # Build JSON structure
        json_structure = self.json_builder.build_json_structure(all_spaces)
        
        # Manually corrupt the data to test validation
        corrupted_data = json_structure.copy()
        del corrupted_data["metadata"]["export_date"]  # Remove required field
        
        # Test validation
        is_valid, errors = self.json_builder.validate_export_data(corrupted_data)
        
        assert is_valid is False
        assert "Missing export_date in metadata" in errors
    
    def test_export_empty_repository(self):
        """Test exporting from empty repository."""
        empty_repository = SpaceRepository()
        empty_spaces = empty_repository.get_all_spaces()
        
        json_structure = self.json_builder.build_json_structure(empty_spaces)
        
        assert json_structure["summary"]["total_spaces"] == 0
        assert json_structure["summary"]["processed_spaces"] == 0
        assert json_structure["summary"]["total_surface_area"] == 0.0
        assert len(json_structure["spaces"]) == 0
    
    def test_json_roundtrip_integrity(self):
        """Test that exported JSON can be loaded and maintains data integrity."""
        all_spaces = self.space_repository.get_all_spaces()
        
        # Export to JSON structure
        original_structure = self.json_builder.build_json_structure(all_spaces)
        
        # Convert to JSON string and back
        json_string = json.dumps(original_structure)
        loaded_structure = json.loads(json_string)
        
        # Verify data integrity after roundtrip
        assert loaded_structure == original_structure
        
        # Verify specific data types are preserved
        office_space = next(s for s in loaded_structure["spaces"] 
                          if s["properties"]["name"] == "Office 101")
        
        assert isinstance(office_space["properties"]["elevation"], (int, float))
        assert isinstance(office_space["properties"]["quantities"]["Height"], (int, float))
        assert isinstance(office_space["properties"]["processed"], bool)
        
        # Verify nested data structures
        north_boundary = next(b for b in office_space["space_boundaries"] 
                            if b["boundary_orientation"] == "North")
        assert isinstance(north_boundary["thermal_properties"], dict)
        assert isinstance(north_boundary["material_properties"], dict)
        assert isinstance(north_boundary["calculated_area"], (int, float))