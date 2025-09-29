"""
Tests for JSON Builder functionality.
"""

import pytest
import json
import tempfile
import os
from datetime import datetime
from pathlib import Path

from ifc_room_schedule.export.json_builder import JsonBuilder
from ifc_room_schedule.data.space_model import SpaceData
from ifc_room_schedule.data.surface_model import SurfaceData
from ifc_room_schedule.data.space_boundary_model import SpaceBoundaryData
from ifc_room_schedule.data.relationship_model import RelationshipData


class TestJsonBuilder:
    """Test cases for JsonBuilder class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.json_builder = JsonBuilder()
        
        # Create test space data
        self.test_space = SpaceData(
            guid="test-guid-123",
            name="Office 101",
            long_name="Office Room 101",
            description="Test office space",
            object_type="Office",
            zone_category="Work",
            number="101",
            elevation=0.0,
            quantities={"Height": 3.0, "Area": 25.0},
            processed=True
        )
        
        # Add test surface
        test_surface = SurfaceData(
            id="surface-1",
            type="Wall",
            area=15.0,
            material="Concrete",
            ifc_type="IfcWall",
            related_space_guid="test-guid-123",
            user_description="North wall"
        )
        self.test_space.add_surface(test_surface)
        
        # Add test space boundary
        test_boundary = SpaceBoundaryData(
            id="boundary-1",
            guid="boundary-guid-123",
            name="North Wall Boundary",
            description="Boundary to north wall",
            physical_or_virtual_boundary="Physical",
            internal_or_external_boundary="External",
            related_building_element_guid="wall-guid-123",
            related_building_element_name="North Wall",
            related_building_element_type="IfcWall",
            related_space_guid="test-guid-123",
            boundary_surface_type="Wall",
            boundary_orientation="North",
            calculated_area=15.0,
            boundary_level=1,
            display_label="North Wall"
        )
        self.test_space.add_space_boundary(test_boundary)
        
        # Add test relationship
        test_relationship = RelationshipData(
            related_entity_guid="building-guid-123",
            related_entity_name="Main Building",
            related_entity_description="Primary building structure",
            relationship_type="Contains",
            ifc_relationship_type="IfcRelContainedInSpatialStructure"
        )
        self.test_space.add_relationship(test_relationship)
    
    def test_json_builder_initialization(self):
        """Test JsonBuilder initialization."""
        builder = JsonBuilder()
        assert builder.source_file_path is None
        assert builder.ifc_version is None
        assert builder.application_version == "1.0.0"
    
    def test_set_source_file(self):
        """Test setting source file path."""
        file_path = "/path/to/test.ifc"
        self.json_builder.set_source_file(file_path)
        assert self.json_builder.source_file_path == file_path
    
    def test_set_ifc_version(self):
        """Test setting IFC version."""
        version = "IFC4"
        self.json_builder.set_ifc_version(version)
        assert self.json_builder.ifc_version == version
    
    def test_generate_metadata_basic(self):
        """Test basic metadata generation."""
        metadata = self.json_builder.generate_metadata()
        
        assert "export_date" in metadata
        assert "application_version" in metadata
        assert metadata["application_version"] == "1.0.0"
        
        # Check that export_date is a valid ISO format
        datetime.fromisoformat(metadata["export_date"])
    
    def test_generate_metadata_with_source_file(self):
        """Test metadata generation with source file."""
        self.json_builder.set_source_file("/path/to/test.ifc")
        metadata = self.json_builder.generate_metadata()
        
        assert metadata["source_file"] == "test.ifc"
        assert metadata["source_file_path"] == "/path/to/test.ifc"
    
    def test_generate_metadata_with_ifc_version(self):
        """Test metadata generation with IFC version."""
        self.json_builder.set_ifc_version("IFC4")
        metadata = self.json_builder.generate_metadata()
        
        assert metadata["ifc_version"] == "IFC4"
    
    def test_generate_metadata_with_additional(self):
        """Test metadata generation with additional metadata."""
        additional = {"custom_field": "custom_value"}
        metadata = self.json_builder.generate_metadata(additional)
        
        assert metadata["custom_field"] == "custom_value"
    
    def test_build_surface_dict(self):
        """Test building surface dictionary."""
        surface = SurfaceData(
            id="surface-1",
            type="Wall",
            area=15.0,
            material="Concrete",
            ifc_type="IfcWall",
            related_space_guid="test-guid-123",
            user_description="Test wall"
        )
        
        surface_dict = self.json_builder._build_surface_dict(surface)
        
        assert surface_dict["id"] == "surface-1"
        assert surface_dict["type"] == "Wall"
        assert surface_dict["area"] == 15.0
        assert surface_dict["material"] == "Concrete"
        assert surface_dict["ifc_type"] == "IfcWall"
        assert surface_dict["related_space_guid"] == "test-guid-123"
        assert surface_dict["user_description"] == "Test wall"
    
    def test_build_space_boundary_dict(self):
        """Test building space boundary dictionary."""
        boundary = SpaceBoundaryData(
            id="boundary-1",
            guid="boundary-guid-123",
            name="Test Boundary",
            description="Test boundary description",
            physical_or_virtual_boundary="Physical",
            internal_or_external_boundary="External",
            related_building_element_guid="wall-guid-123",
            related_building_element_name="Test Wall",
            related_building_element_type="IfcWall",
            related_space_guid="test-guid-123",
            calculated_area=15.0
        )
        
        boundary_dict = self.json_builder._build_space_boundary_dict(boundary)
        
        assert boundary_dict["id"] == "boundary-1"
        assert boundary_dict["guid"] == "boundary-guid-123"
        assert boundary_dict["name"] == "Test Boundary"
        assert boundary_dict["physical_or_virtual_boundary"] == "Physical"
        assert boundary_dict["calculated_area"] == 15.0
    
    def test_build_relationship_dict(self):
        """Test building relationship dictionary."""
        relationship = RelationshipData(
            related_entity_guid="entity-guid-123",
            related_entity_name="Test Entity",
            related_entity_description="Test entity description",
            relationship_type="Contains",
            ifc_relationship_type="IfcRelContainedInSpatialStructure"
        )
        
        relationship_dict = self.json_builder._build_relationship_dict(relationship)
        
        assert relationship_dict["related_entity_guid"] == "entity-guid-123"
        assert relationship_dict["related_entity_name"] == "Test Entity"
        assert relationship_dict["relationship_type"] == "Contains"
        assert relationship_dict["ifc_relationship_type"] == "IfcRelContainedInSpatialStructure"
    
    def test_build_space_dict(self):
        """Test building complete space dictionary."""
        space_dict = self.json_builder._build_space_dict(self.test_space)
        
        assert space_dict["guid"] == "test-guid-123"
        assert space_dict["properties"]["name"] == "Office 101"
        assert space_dict["properties"]["long_name"] == "Office Room 101"
        assert space_dict["properties"]["processed"] is True
        assert len(space_dict["surfaces"]) == 1
        assert len(space_dict["space_boundaries"]) == 1
        assert len(space_dict["relationships"]) == 1
    
    def test_generate_summary(self):
        """Test summary generation."""
        spaces = [self.test_space]
        summary = self.json_builder._generate_summary(spaces)
        
        assert summary["total_spaces"] == 1
        assert summary["processed_spaces"] == 1
        assert summary["total_surface_area"] == 15.0
        assert summary["surface_area_by_type"]["Wall"] == 15.0
        assert summary["total_boundary_area"] == 15.0
        assert summary["boundary_area_by_type"]["Wall"] == 15.0
        assert summary["boundary_area_by_orientation"]["North"] == 15.0
        
        # Check boundary counts
        boundary_counts = summary["boundary_counts"]
        assert boundary_counts["physical_boundaries"] == 1
        assert boundary_counts["virtual_boundaries"] == 0
        assert boundary_counts["external_boundaries"] == 1
        assert boundary_counts["internal_boundaries"] == 0
        assert boundary_counts["first_level_boundaries"] == 1
        assert boundary_counts["second_level_boundaries"] == 0
    
    def test_build_json_structure(self):
        """Test building complete JSON structure."""
        spaces = [self.test_space]
        json_structure = self.json_builder.build_json_structure(spaces)
        
        assert "metadata" in json_structure
        assert "spaces" in json_structure
        assert "summary" in json_structure
        
        assert len(json_structure["spaces"]) == 1
        assert json_structure["summary"]["total_spaces"] == 1
    
    def test_validate_export_data_valid(self):
        """Test validation of valid export data."""
        spaces = [self.test_space]
        json_structure = self.json_builder.build_json_structure(spaces)
        
        is_valid, errors = self.json_builder.validate_export_data(json_structure)
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_export_data_missing_keys(self):
        """Test validation with missing required keys."""
        invalid_data = {"metadata": {}}
        
        is_valid, errors = self.json_builder.validate_export_data(invalid_data)
        
        assert is_valid is False
        assert "Missing required key: spaces" in errors
        assert "Missing required key: summary" in errors
    
    def test_validate_export_data_invalid_metadata(self):
        """Test validation with invalid metadata."""
        invalid_data = {
            "metadata": {},
            "spaces": [],
            "summary": {"total_spaces": 0, "processed_spaces": 0, "total_surface_area": 0.0}
        }
        
        is_valid, errors = self.json_builder.validate_export_data(invalid_data)
        
        assert is_valid is False
        assert "Missing export_date in metadata" in errors
        assert "Missing application_version in metadata" in errors
    
    def test_validate_export_data_invalid_space(self):
        """Test validation with invalid space data."""
        invalid_data = {
            "metadata": {"export_date": "2023-01-01", "application_version": "1.0.0"},
            "spaces": [{"properties": {}}],  # Missing GUID
            "summary": {"total_spaces": 1, "processed_spaces": 0, "total_surface_area": 0.0}
        }
        
        is_valid, errors = self.json_builder.validate_export_data(invalid_data)
        
        assert is_valid is False
        assert "Space 0: Missing GUID" in errors
    
    def test_write_json_file(self):
        """Test writing JSON to file."""
        test_data = {"test": "data"}
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            temp_filename = temp_file.name
        
        try:
            success, message = self.json_builder.write_json_file(temp_filename, test_data)
            assert success is True
            
            # Verify file contents
            with open(temp_filename, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
            
            assert loaded_data == test_data
        finally:
            if os.path.exists(temp_filename):
                os.unlink(temp_filename)
    
    def test_write_json_file_invalid_path(self):
        """Test writing JSON to invalid file path."""
        test_data = {"test": "data"}
        invalid_path = "Z:\\invalid\\path\\file.json"
        
        success, message = self.json_builder.write_json_file(invalid_path, test_data)
        assert success is False
    
    def test_export_to_json_success(self):
        """Test complete export workflow success."""
        spaces = [self.test_space]
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            temp_filename = temp_file.name
        
        try:
            success, messages = self.json_builder.export_to_json(spaces, temp_filename)
            
            assert success is True
            assert len(messages) == 1
            assert "Successfully exported 1 spaces" in messages[0]
            
            # Verify file exists and contains valid JSON
            assert os.path.exists(temp_filename)
            with open(temp_filename, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
            
            assert "metadata" in loaded_data
            assert "spaces" in loaded_data
            assert "summary" in loaded_data
        finally:
            if os.path.exists(temp_filename):
                os.unlink(temp_filename)
    
    def test_export_to_json_validation_failure(self):
        """Test export workflow with validation failure."""
        # This should fail during space creation due to validation in __post_init__
        with pytest.raises(ValueError, match="GUID is required for space data"):
            invalid_space = SpaceData(
                guid="",  # Invalid empty GUID
                name="Test",
                long_name="Test Space",
                description="Test",
                object_type="Office",
                zone_category="Work",
                number="1",
                elevation=0.0
            )
    
    def test_export_to_json_without_validation(self):
        """Test export workflow without validation."""
        spaces = [self.test_space]
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            temp_filename = temp_file.name
        
        try:
            success, messages = self.json_builder.export_to_json(spaces, temp_filename, validate=False)
            
            assert success is True
            assert len(messages) == 1
        finally:
            if os.path.exists(temp_filename):
                os.unlink(temp_filename)
    
    def test_export_multiple_spaces(self):
        """Test exporting multiple spaces."""
        # Create second space
        space2 = SpaceData(
            guid="test-guid-456",
            name="Office 102",
            long_name="Office Room 102",
            description="Second test office space",
            object_type="Office",
            zone_category="Work",
            number="102",
            elevation=0.0,
            quantities={"Height": 3.0, "Area": 30.0},
            processed=False
        )
        
        # Add surface to second space
        surface2 = SurfaceData(
            id="surface-2",
            type="Floor",
            area=30.0,
            material="Carpet",
            ifc_type="IfcSlab",
            related_space_guid="test-guid-456"
        )
        space2.add_surface(surface2)
        
        spaces = [self.test_space, space2]
        json_structure = self.json_builder.build_json_structure(spaces)
        
        assert len(json_structure["spaces"]) == 2
        assert json_structure["summary"]["total_spaces"] == 2
        assert json_structure["summary"]["processed_spaces"] == 1  # Only first space is processed
        assert json_structure["summary"]["total_surface_area"] == 45.0  # 15 + 30
        
        # Check surface areas by type
        surface_areas = json_structure["summary"]["surface_area_by_type"]
        assert surface_areas["Wall"] == 15.0
        assert surface_areas["Floor"] == 30.0
    
    def test_json_structure_serializable(self):
        """Test that generated JSON structure is serializable."""
        spaces = [self.test_space]
        json_structure = self.json_builder.build_json_structure(spaces)
        
        # This should not raise an exception
        json_string = json.dumps(json_structure)
        
        # And we should be able to load it back
        loaded_structure = json.loads(json_string)
        assert loaded_structure == json_structure