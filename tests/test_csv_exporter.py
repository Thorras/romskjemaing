"""
Test cases for CSV exporter functionality.
"""

import os
import csv
import tempfile
from pathlib import Path

import pytest

from ifc_room_schedule.export.csv_exporter import CsvExporter
from ifc_room_schedule.data.space_model import SpaceData
from ifc_room_schedule.data.surface_model import SurfaceData
from ifc_room_schedule.data.space_boundary_model import SpaceBoundaryData
from ifc_room_schedule.data.relationship_model import RelationshipData


@pytest.fixture
def sample_spaces():
    """Create sample space data for testing."""
    # Create surfaces
    surface1 = SurfaceData(
        id="surface_1",
        type="Wall",
        area=25.5,
        material="Concrete",
        ifc_type="IfcWall",
        related_space_guid="space_guid_1",
        user_description="North wall"
    )
    
    surface2 = SurfaceData(
        id="surface_2", 
        type="Floor",
        area=50.0,
        material="Concrete Slab",
        ifc_type="IfcSlab",
        related_space_guid="space_guid_1",
        user_description="Main floor"
    )
    
    # Create space boundaries
    boundary1 = SpaceBoundaryData(
        id="boundary_1",
        guid="boundary_guid_1",
        name="North Wall Boundary",
        description="Boundary to exterior",
        physical_or_virtual_boundary="Physical",
        internal_or_external_boundary="External",
        related_building_element_guid="wall_guid_1",
        related_building_element_name="North Wall",
        related_building_element_type="IfcWall",
        related_space_guid="space_guid_1",
        boundary_surface_type="Wall",
        boundary_orientation="North",
        connection_geometry={},
        calculated_area=25.5,
        boundary_level=1,
        display_label="North Wall to Exterior"
    )
    
    # Create relationships
    relationship1 = RelationshipData(
        related_entity_guid="zone_guid_1",
        related_entity_name="Office Zone",
        related_entity_description="Main office zone",
        relationship_type="Contains",
        ifc_relationship_type="IfcRelContainedInSpatialStructure"
    )
    
    # Create space
    space1 = SpaceData(
        guid="space_guid_1",
        name="Office 101",
        long_name="Main Office Room 101",
        description="Primary office space",
        object_type="Office",
        zone_category="Work",
        number="101",
        elevation=0.0,
        quantities={"Height": 3.0, "FinishFloorHeight": 0.1},
        surfaces=[surface1, surface2],
        space_boundaries=[boundary1],
        relationships=[relationship1],
        user_descriptions={"space": "Main office room"},
        processed=True
    )
    
    return [space1]


class TestCsvExporter:
    """Test cases for CsvExporter."""
    
    def test_exporter_initialization(self):
        """Test CSV exporter initializes correctly."""
        exporter = CsvExporter()
        assert exporter.source_file_path is None
        assert exporter.application_version == "1.0.0"
    
    def test_set_source_file(self):
        """Test setting source file path."""
        exporter = CsvExporter()
        test_path = "/test/file.ifc"
        exporter.set_source_file(test_path)
        assert exporter.source_file_path == test_path
    
    def test_export_to_csv_basic(self, sample_spaces):
        """Test basic CSV export functionality."""
        exporter = CsvExporter()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            export_path = os.path.join(temp_dir, "test_export.csv")
            
            success, message = exporter.export_to_csv(sample_spaces, export_path)
            
            assert success is True
            assert "Successfully exported" in message
            assert os.path.exists(export_path)
    
    def test_export_to_csv_with_extension(self, sample_spaces):
        """Test CSV export adds extension if missing."""
        exporter = CsvExporter()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            export_path = os.path.join(temp_dir, "test_export")  # No extension
            
            success, message = exporter.export_to_csv(sample_spaces, export_path)
            
            assert success is True
            assert os.path.exists(export_path + ".csv")
    
    def test_export_csv_content_structure(self, sample_spaces):
        """Test CSV export content structure."""
        exporter = CsvExporter()
        exporter.set_source_file("/test/source.ifc")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            export_path = os.path.join(temp_dir, "test_export.csv")
            
            success, message = exporter.export_to_csv(sample_spaces, export_path)
            assert success is True
            
            # Read and verify CSV content
            with open(export_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Check for main sections
                assert "=== SPACES DATA ===" in content
                assert "=== SURFACES DATA ===" in content
                assert "=== SPACE BOUNDARIES DATA ===" in content
                assert "=== RELATIONSHIPS DATA ===" in content
                assert "=== SUMMARY STATISTICS ===" in content
                
                # Check for metadata
                assert "# Room Schedule Export - CSV Format" in content
                assert "# Source File:,source.ifc" in content
    
    def test_export_csv_spaces_data(self, sample_spaces):
        """Test CSV export spaces data section."""
        exporter = CsvExporter()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            export_path = os.path.join(temp_dir, "test_export.csv")
            
            success, message = exporter.export_to_csv(sample_spaces, export_path)
            assert success is True
            
            # Read CSV and find spaces section
            with open(export_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                rows = list(reader)
                
                # Find spaces data section
                spaces_start = None
                for i, row in enumerate(rows):
                    if row and row[0] == "=== SPACES DATA ===":
                        spaces_start = i
                        break
                
                assert spaces_start is not None
                
                # Check header row
                header_row = rows[spaces_start + 1]
                assert "GUID" in header_row
                assert "Name" in header_row
                assert "Long Name" in header_row
                
                # Check data row
                data_row = rows[spaces_start + 2]
                assert data_row[0] == "space_guid_1"  # GUID
                assert data_row[1] == "Office 101"    # Name
                assert data_row[2] == "Main Office Room 101"  # Long Name
    
    def test_export_csv_selective_inclusion(self, sample_spaces):
        """Test CSV export with selective data inclusion."""
        exporter = CsvExporter()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            export_path = os.path.join(temp_dir, "test_export.csv")
            
            # Export without surfaces and relationships
            success, message = exporter.export_to_csv(
                sample_spaces, 
                export_path,
                include_surfaces=False,
                include_relationships=False
            )
            assert success is True
            
            with open(export_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Should have spaces and boundaries but not surfaces or relationships
                assert "=== SPACES DATA ===" in content
                assert "=== SPACE BOUNDARIES DATA ===" in content
                assert "=== SURFACES DATA ===" not in content
                assert "=== RELATIONSHIPS DATA ===" not in content
    
    def test_export_csv_empty_spaces(self):
        """Test CSV export with empty spaces list."""
        exporter = CsvExporter()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            export_path = os.path.join(temp_dir, "test_export.csv")
            
            success, message = exporter.export_to_csv([], export_path)
            
            assert success is True
            assert "Successfully exported 0 spaces" in message
            assert os.path.exists(export_path)
    
    def test_export_csv_error_handling(self, sample_spaces):
        """Test CSV export error handling."""
        exporter = CsvExporter()
        
        # Try to export to invalid path (Windows drive that doesn't exist)
        invalid_path = "Z:\\invalid\\path\\that\\does\\not\\exist\\test.csv"
        
        success, message = exporter.export_to_csv(sample_spaces, invalid_path)
        
        assert success is False
        assert "File system error" in message
    
    def test_export_csv_summary_statistics(self, sample_spaces):
        """Test CSV export summary statistics section."""
        exporter = CsvExporter()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            export_path = os.path.join(temp_dir, "test_export.csv")
            
            success, message = exporter.export_to_csv(sample_spaces, export_path)
            assert success is True
            
            # Read CSV and find summary section
            with open(export_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                rows = list(reader)
                
                # Find summary section
                summary_start = None
                for i, row in enumerate(rows):
                    if row and row[0] == "=== SUMMARY STATISTICS ===":
                        summary_start = i
                        break
                
                assert summary_start is not None
                
                # Check for summary metrics
                summary_content = []
                for i in range(summary_start, len(rows)):
                    if rows[i]:
                        summary_content.extend(rows[i])
                
                summary_text = " ".join(summary_content)
                assert "Total Spaces" in summary_text
                assert "Processed Spaces" in summary_text
                assert "Total Surface Area" in summary_text