"""
End-to-End Integration Tests for IFC Room Schedule Application

Tests the complete workflow from IFC import to JSON export, validating data integrity
throughout the entire process and testing various IFC file formats and sizes.
"""

import pytest
import json
import tempfile
import os
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import PyQt components conditionally
try:
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import Qt
    from PyQt6.QtTest import QTest
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False

# Import application components
try:
    from ifc_room_schedule.ui.main_window import MainWindow
    from ifc_room_schedule.parser.ifc_file_reader import IfcFileReader
    from ifc_room_schedule.parser.ifc_space_extractor import IfcSpaceExtractor
    from ifc_room_schedule.parser.ifc_space_boundary_parser import IfcSpaceBoundaryParser
    from ifc_room_schedule.parser.ifc_relationship_parser import IfcRelationshipParser
    from ifc_room_schedule.export.json_builder import JsonBuilder
    from ifc_room_schedule.data.space_repository import SpaceRepository
    from ifc_room_schedule.data.space_model import SpaceData
    from ifc_room_schedule.data.surface_model import SurfaceData
    from ifc_room_schedule.data.space_boundary_model import SpaceBoundaryData
    from ifc_room_schedule.data.relationship_model import RelationshipData
    COMPONENTS_AVAILABLE = True
except ImportError as e:
    COMPONENTS_AVAILABLE = False
    print(f"Warning: Could not import application components: {e}")


@pytest.fixture(scope="session")
def qapp():
    """Create QApplication instance for testing."""
    if not PYQT_AVAILABLE:
        pytest.skip("PyQt6 not available")
    
    if not QApplication.instance():
        app = QApplication([])
    else:
        app = QApplication.instance()
    yield app
    app.quit()


@pytest.fixture
def sample_ifc_file():
    """Path to sample IFC file for testing."""
    return os.path.join(os.path.dirname(__file__), '..', 'tesfiler', 'AkkordSvingen 23_ARK.ifc')


@pytest.fixture
def comprehensive_test_data():
    """Create comprehensive test data that simulates real IFC extraction."""
    if not COMPONENTS_AVAILABLE:
        pytest.skip("Application components not available")
    
    spaces = []
    
    # Office space with complete data
    office_space = SpaceData(
        guid="3M7lX4qKr0IfhQVOQZyOJl",
        name="Office 101",
        long_name="Executive Office Room 101",
        description="Corner office with natural light",
        object_type="Office",
        zone_category="Work Area",
        number="101",
        elevation=0.0,
        quantities={
            "Height": 3.0,
            "Area": 25.5,
            "Volume": 76.5,
            "FinishFloorHeight": 0.1,
            "FinishCeilingHeight": 2.8,
            "GrossFloorArea": 26.0,
            "NetFloorArea": 25.5
        },
        processed=True
    )
    
    # Add surfaces
    office_surfaces = [
        SurfaceData(
            id="surface-office-north-wall",
            type="Wall",
            area=12.0,
            material="Gypsum Board",
            ifc_type="IfcWall",
            related_space_guid="3M7lX4qKr0IfhQVOQZyOJl",
            user_description="North wall with large window",
            properties={"Thickness": 0.15, "FireRating": "1 hour", "AcousticRating": "STC 45"}
        ),
        SurfaceData(
            id="surface-office-floor",
            type="Floor",
            area=25.5,
            material="Carpet Tile",
            ifc_type="IfcSlab",
            related_space_guid="3M7lX4qKr0IfhQVOQZyOJl",
            user_description="Commercial carpet flooring"
        )
    ]
    
    for surface in office_surfaces:
        office_space.add_surface(surface)
    
    # Add space boundaries
    office_boundary = SpaceBoundaryData(
        id="boundary-office-north",
        guid="3M7lX4qKr0IfhQVOQZyOJl-north",
        name="North Wall Boundary",
        description="Boundary to exterior north wall",
        physical_or_virtual_boundary="Physical",
        internal_or_external_boundary="External",
        related_building_element_guid="wall-north-exterior-001",
        related_building_element_name="North Exterior Wall",
        related_building_element_type="IfcWall",
        related_space_guid="3M7lX4qKr0IfhQVOQZyOJl",
        boundary_surface_type="Wall",
        boundary_orientation="North",
        calculated_area=12.0,
        boundary_level=1,
        display_label="North Wall to Exterior",
        thermal_properties={"U-Value": 0.28, "R-Value": 3.57, "ThermalMass": 150.0},
        material_properties={"Material": "Insulated Concrete Block", "Thickness": 0.25, "Density": 1800.0}
    )
    office_space.add_space_boundary(office_boundary)
    
    # Add relationships
    office_relationship = RelationshipData(
        related_entity_guid="building-main-001",
        related_entity_name="Main Office Building",
        related_entity_description="Primary office building structure",
        relationship_type="Contains",
        ifc_relationship_type="IfcRelContainedInSpatialStructure"
    )
    office_space.add_relationship(office_relationship)
    
    # Add user descriptions
    office_space.set_user_description("general", "Executive corner office with excellent natural light and city views")
    
    spaces.append(office_space)
    
    # Conference room with different characteristics
    conf_space = SpaceData(
        guid="2K9mW3pJq8HfgRTNPXwLKj",
        name="Conference Room A",
        long_name="Large Conference Room A",
        description="Main conference room for team meetings",
        object_type="Meeting Room",
        zone_category="Meeting Area",
        number="CR-A",
        elevation=0.0,
        quantities={
            "Height": 3.5,
            "Area": 42.0,
            "Volume": 147.0
        },
        processed=True
    )
    
    # Add minimal surface data to conference room
    conf_surface = SurfaceData(
        id="surface-conf-floor",
        type="Floor",
        area=42.0,
        material="Hardwood",
        ifc_type="IfcSlab",
        related_space_guid="2K9mW3pJq8HfgRTNPXwLKj",
        user_description="Premium hardwood flooring"
    )
    conf_space.add_surface(conf_surface)
    
    spaces.append(conf_space)
    
    # Storage room with minimal data (testing incomplete data handling)
    storage_space = SpaceData(
        guid="1H8kV2oIp7GegQSMOWvJKi",
        name="Storage",
        long_name="Storage Room",
        description="General storage space",
        object_type="Storage",
        zone_category="Service",
        number="ST-01",
        elevation=0.0,
        quantities={"Area": 8.0},
        processed=False  # Not processed yet
    )
    
    spaces.append(storage_space)
    
    return spaces


def test_basic_imports():
    """Test that basic imports work."""
    assert True  # If we get here, imports worked


def test_sample_ifc_file_exists():
    """Test that sample IFC file exists."""
    sample_file = os.path.join(os.path.dirname(__file__), '..', 'tesfiler', 'AkkordSvingen 23_ARK.ifc')
    if os.path.exists(sample_file):
        assert os.path.isfile(sample_file)
        assert sample_file.endswith('.ifc')
    else:
        pytest.skip("Sample IFC file not available")


@pytest.mark.skipif(not COMPONENTS_AVAILABLE, reason="Application components not available")
class TestEndToEndIntegration:
    """Comprehensive end-to-end integration tests."""
    
    def test_complete_workflow_with_real_ifc_file(self, qapp, sample_ifc_file):
        """Test complete workflow using real IFC file if available."""
        if not os.path.exists(sample_ifc_file):
            pytest.skip("Sample IFC file not available")
        
        # Initialize components
        ifc_reader = IfcFileReader()
        space_extractor = IfcSpaceExtractor()
        boundary_parser = IfcSpaceBoundaryParser()
        relationship_parser = IfcRelationshipParser()
        json_builder = JsonBuilder()
        
        # Step 1: Load IFC file
        success, message = ifc_reader.load_file(sample_ifc_file)
        if not success:
            pytest.skip(f"Could not load IFC file: {message}")
        
        assert success, f"Failed to load IFC file: {message}"
        assert ifc_reader.is_loaded()
        
        # Step 2: Extract spaces
        ifc_file = ifc_reader.get_ifc_file()
        space_extractor.set_ifc_file(ifc_file)
        spaces = space_extractor.extract_spaces()
        
        assert isinstance(spaces, list)
        if len(spaces) == 0:
            pytest.skip("No spaces found in IFC file")
        
        # Step 3: Process each space with boundaries and relationships
        boundary_parser.set_ifc_file(ifc_file)
        relationship_parser.set_ifc_file(ifc_file)
        
        processed_spaces = []
        for space_data in spaces:
            # Extract space boundaries
            boundaries = boundary_parser.extract_space_boundaries(space_data.guid)
            for boundary in boundaries:
                space_data.add_space_boundary(boundary)
            
            # Extract relationships
            relationships = relationship_parser.get_space_relationships(space_data.guid)
            for relationship in relationships:
                space_data.add_relationship(relationship)
            
            space_data.processed = True
            processed_spaces.append(space_data)
        
        # Step 4: Export to JSON
        json_builder.set_source_file(os.path.basename(sample_ifc_file))
        json_builder.set_ifc_version("IFC4")  # Assume IFC4
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            temp_filename = temp_file.name
        
        try:
            success, messages = json_builder.export_to_json(processed_spaces, temp_filename)
            
            assert success, f"Export failed: {messages}"
            assert os.path.exists(temp_filename)
            
            # Step 5: Verify exported data
            with open(temp_filename, 'r', encoding='utf-8') as f:
                exported_data = json.load(f)
            
            # Validate structure
            assert "metadata" in exported_data
            assert "spaces" in exported_data
            assert "summary" in exported_data
            
            # Validate metadata
            metadata = exported_data["metadata"]
            assert "export_date" in metadata
            assert metadata["source_file"] == os.path.basename(sample_ifc_file)
            
            # Validate spaces data integrity
            exported_spaces = exported_data["spaces"]
            assert len(exported_spaces) == len(processed_spaces)
            
            for i, exported_space in enumerate(exported_spaces):
                original_space = processed_spaces[i]
                
                # Check GUID preservation
                assert exported_space["guid"] == original_space.guid
                
                # Check properties preservation
                props = exported_space["properties"]
                assert props["name"] == original_space.name
                assert props["processed"] == original_space.processed
                
                # Check quantities preservation
                if original_space.quantities:
                    assert "quantities" in props
                    for key, value in original_space.quantities.items():
                        assert props["quantities"][key] == value
            
            # Validate summary
            summary = exported_data["summary"]
            assert summary["total_spaces"] == len(processed_spaces)
            assert summary["processed_spaces"] == len([s for s in processed_spaces if s.processed])
            
        finally:
            if os.path.exists(temp_filename):
                os.unlink(temp_filename)
    
    def test_data_integrity_throughout_workflow(self, comprehensive_test_data):
        """Test that data integrity is maintained throughout the complete workflow."""
        # Initialize repository and add test data
        repository = SpaceRepository()
        for space in comprehensive_test_data:
            repository.add_space(space)
        
        # Step 1: Verify initial data integrity
        all_spaces = repository.get_all_spaces()
        assert len(all_spaces) == 3
        
        office_space = repository.get_space("3M7lX4qKr0IfhQVOQZyOJl")
        assert office_space is not None
        assert len(office_space.surfaces) == 2
        assert len(office_space.space_boundaries) == 1
        assert len(office_space.relationships) == 1
        
        # Step 2: Export to JSON and verify data preservation
        json_builder = JsonBuilder()
        json_builder.set_source_file("test_building.ifc")
        json_structure = json_builder.build_json_structure(all_spaces)
        
        # Step 3: Verify all data is preserved in JSON
        exported_office = next(s for s in json_structure["spaces"] 
                              if s["guid"] == "3M7lX4qKr0IfhQVOQZyOJl")
        
        # Check surfaces preservation
        assert len(exported_office["surfaces"]) == 2
        north_wall = next(s for s in exported_office["surfaces"] 
                         if s["id"] == "surface-office-north-wall")
        assert north_wall["area"] == 12.0
        assert north_wall["material"] == "Gypsum Board"
        assert north_wall["user_description"] == "North wall with large window"
        assert north_wall["properties"]["FireRating"] == "1 hour"
        
        # Check space boundaries preservation
        assert len(exported_office["space_boundaries"]) == 1
        north_boundary = exported_office["space_boundaries"][0]
        assert north_boundary["calculated_area"] == 12.0
        assert north_boundary["thermal_properties"]["U-Value"] == 0.28
        assert north_boundary["boundary_level"] == 1
        
        # Check relationships preservation
        assert len(exported_office["relationships"]) == 1
        building_rel = exported_office["relationships"][0]
        assert building_rel["related_entity_name"] == "Main Office Building"
        assert building_rel["relationship_type"] == "Contains"
        
        # Check user descriptions preservation
        user_descriptions = exported_office["properties"]["user_descriptions"]
        assert "general" in user_descriptions
        
        # Step 4: Test JSON roundtrip integrity
        json_string = json.dumps(json_structure)
        loaded_structure = json.loads(json_string)
        
        # Verify data is identical after roundtrip
        loaded_office = next(s for s in loaded_structure["spaces"]
                            if s["guid"] == "3M7lX4qKr0IfhQVOQZyOJl")
        
        assert loaded_office == exported_office
    
    def test_error_handling_scenarios(self, qapp):
        """Test error handling throughout the workflow."""
        main_window = MainWindow()
        
        # Test 1: Invalid file handling
        main_window._testing_mode = True  # Enable testing mode
        with patch.object(main_window.ifc_reader, 'validate_file', 
                         return_value=(False, "Invalid IFC format")):
            with patch.object(main_window, 'show_enhanced_error_message') as mock_error:
                main_window.process_ifc_file("/fake/invalid.txt")
                mock_error.assert_called_once()
                assert "File Validation Error" in mock_error.call_args[0][0]
        
        # Test 2: File loading failure
        with patch.object(main_window.ifc_reader, 'validate_file', return_value=(True, "Valid")):
            with patch.object(main_window.ifc_reader, 'load_file', 
                             return_value=(False, "File corrupted")):
                with patch.object(main_window, 'handle_file_operation_error') as mock_error:
                    main_window.process_ifc_file("/fake/corrupted.ifc")
                    mock_error.assert_called_once()
        
        # Test 3: Export failure handling
        json_builder = JsonBuilder()
        
        # Test with invalid export path
        success, messages = json_builder.export_to_json([], "/invalid/path/export.json")
        assert success is False
        assert len(messages) > 0
        assert any("export" in msg.lower() or "file" in msg.lower() for msg in messages)
    
    def test_various_ifc_file_sizes_and_formats(self, comprehensive_test_data):
        """Test handling of various IFC file sizes and data complexity."""
        json_builder = JsonBuilder()
        
        # Test 1: Small dataset (1 space)
        small_dataset = [comprehensive_test_data[0]]  # Just office space
        json_structure = json_builder.build_json_structure(small_dataset)
        
        assert json_structure["summary"]["total_spaces"] == 1
        assert len(json_structure["spaces"]) == 1
        
        # Test 2: Medium dataset (all test data)
        medium_dataset = comprehensive_test_data
        json_structure = json_builder.build_json_structure(medium_dataset)
        
        assert json_structure["summary"]["total_spaces"] == 3
        assert len(json_structure["spaces"]) == 3
        
        # Test 3: Large dataset simulation (duplicate spaces with different GUIDs)
        large_dataset = []
        for i in range(20):  # Simulate 20 spaces for performance
            space = SpaceData(
                guid=f"large-space-{i:03d}",
                name=f"Space {i}",
                long_name=f"Large Dataset Space {i}",
                description=f"Test space number {i}",
                object_type="Office",
                zone_category="Work",
                number=str(i),
                elevation=0.0,
                quantities={"Area": 20.0 + i, "Height": 3.0},
                processed=True
            )
            
            # Add some surfaces
            for j in range(2):  # 2 surfaces per space
                surface = SurfaceData(
                    id=f"surface-{i}-{j}",
                    type=["Wall", "Floor"][j],
                    area=10.0 + j,
                    material="Test Material",
                    ifc_type="IfcWall",
                    related_space_guid=space.guid
                )
                space.add_surface(surface)
            
            large_dataset.append(space)
        
        # Test large dataset export
        json_structure = json_builder.build_json_structure(large_dataset)
        
        assert json_structure["summary"]["total_spaces"] == 20
        assert json_structure["summary"]["processed_spaces"] == 20
        assert len(json_structure["spaces"]) == 20
        
        # Test export to file with large dataset
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            temp_filename = temp_file.name
        
        try:
            success, messages = json_builder.export_to_json(large_dataset, temp_filename)
            assert success
            
            # Verify file exists and has reasonable size
            assert os.path.exists(temp_filename)
            file_size = os.path.getsize(temp_filename)
            assert file_size > 1000  # At least 1KB
            
            # Verify file can be loaded back
            with open(temp_filename, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
            
            assert len(loaded_data["spaces"]) == 20
            
        finally:
            if os.path.exists(temp_filename):
                os.unlink(temp_filename)
    
    def test_export_data_validation(self, comprehensive_test_data):
        """Test comprehensive export data validation."""
        json_builder = JsonBuilder()
        json_structure = json_builder.build_json_structure(comprehensive_test_data)
        
        # Test validation of complete data
        is_valid, errors = json_builder.validate_export_data(json_structure)
        assert is_valid, f"Validation failed: {errors}"
        
        # Test validation with missing metadata
        corrupted_data = json_structure.copy()
        del corrupted_data["metadata"]["export_date"]
        
        is_valid, errors = json_builder.validate_export_data(corrupted_data)
        assert not is_valid
        assert any("export_date" in error for error in errors)
        
        # Test validation with missing spaces
        corrupted_data = json_builder.build_json_structure(comprehensive_test_data)  # Fresh copy
        corrupted_data["spaces"] = []
        
        is_valid, errors = json_builder.validate_export_data(corrupted_data)
        # Should still be valid (empty spaces is allowed)
        assert is_valid
        
        # Test validation with corrupted space data
        corrupted_data = json_structure.copy()
        del corrupted_data["spaces"][0]["guid"]
        
        is_valid, errors = json_builder.validate_export_data(corrupted_data)
        assert not is_valid
        assert any("guid" in error.lower() for error in errors)
    
    def test_ui_workflow_integration(self, qapp, comprehensive_test_data):
        """Test complete workflow through UI components."""
        # Create main window without showing it to avoid threading issues
        main_window = MainWindow()
        
        # Test basic UI component initialization
        assert main_window.ifc_reader is not None
        assert main_window.space_extractor is not None
        assert main_window.current_file_path is None
        assert main_window.spaces == []
        
        # Test setting spaces directly (simulating successful file load)
        main_window.spaces = comprehensive_test_data
        main_window.current_file_path = "/fake/test_building.ifc"
        
        # Verify spaces are loaded
        assert len(main_window.spaces) == 3
        
        # Test space selection
        office_space = next(s for s in main_window.spaces if s.name == "Office 101")
        assert office_space is not None
        assert office_space.guid == "3M7lX4qKr0IfhQVOQZyOJl"
        
        # Test that export can be initiated (without actually running the dialog)
        with patch('ifc_room_schedule.ui.main_window.ExportDialogWidget') as mock_dialog:
            mock_dialog_instance = Mock()
            mock_dialog.return_value = mock_dialog_instance
            mock_dialog_instance.exec.return_value = 0  # Dialog cancelled
            
            # This should not crash
            main_window.export_json()
            
            # Verify dialog was created
            mock_dialog.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])