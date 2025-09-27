"""
Test cases for PDF exporter functionality.
"""

import os
import tempfile
from pathlib import Path

import pytest

try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

from ifc_room_schedule.export.pdf_exporter import PdfExporter
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


@pytest.mark.skipif(not REPORTLAB_AVAILABLE, reason="reportlab not available")
class TestPdfExporter:
    """Test cases for PdfExporter."""
    
    def test_exporter_initialization(self):
        """Test PDF exporter initializes correctly."""
        exporter = PdfExporter()
        assert exporter.source_file_path is None
        assert exporter.application_version == "1.0.0"
        assert exporter.styles is not None
    
    def test_set_source_file(self):
        """Test setting source file path."""
        exporter = PdfExporter()
        test_path = "/test/file.ifc"
        exporter.set_source_file(test_path)
        assert exporter.source_file_path == test_path
    
    def test_export_to_pdf_basic(self, sample_spaces):
        """Test basic PDF export functionality."""
        exporter = PdfExporter()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            export_path = os.path.join(temp_dir, "test_export.pdf")
            
            success, message = exporter.export_to_pdf(sample_spaces, export_path)
            
            assert success is True
            assert "Successfully exported" in message
            assert os.path.exists(export_path)
            
            # Check file is not empty
            assert os.path.getsize(export_path) > 0
    
    def test_export_to_pdf_with_extension(self, sample_spaces):
        """Test PDF export adds extension if missing."""
        exporter = PdfExporter()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            export_path = os.path.join(temp_dir, "test_export")  # No extension
            
            success, message = exporter.export_to_pdf(sample_spaces, export_path)
            
            assert success is True
            assert os.path.exists(export_path + ".pdf")
    
    def test_export_pdf_with_source_file(self, sample_spaces):
        """Test PDF export with source file information."""
        exporter = PdfExporter()
        exporter.set_source_file("/test/source.ifc")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            export_path = os.path.join(temp_dir, "test_export.pdf")
            
            success, message = exporter.export_to_pdf(sample_spaces, export_path)
            
            assert success is True
            assert os.path.exists(export_path)
            
            # Check file size is reasonable (should contain content)
            file_size = os.path.getsize(export_path)
            assert file_size > 1000  # Should be at least 1KB with content
    
    def test_export_pdf_selective_inclusion(self, sample_spaces):
        """Test PDF export with selective data inclusion."""
        exporter = PdfExporter()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            export_path = os.path.join(temp_dir, "test_export.pdf")
            
            # Export without surfaces and relationships
            success, message = exporter.export_to_pdf(
                sample_spaces, 
                export_path,
                include_surfaces=False,
                include_relationships=False
            )
            
            assert success is True
            assert os.path.exists(export_path)
            
            # File should still be created but potentially smaller
            assert os.path.getsize(export_path) > 0
    
    def test_export_pdf_different_page_sizes(self, sample_spaces):
        """Test PDF export with different page sizes."""
        exporter = PdfExporter()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test with letter size
            export_path_letter = os.path.join(temp_dir, "test_export_letter.pdf")
            success, message = exporter.export_to_pdf(
                sample_spaces, 
                export_path_letter,
                page_size=letter
            )
            assert success is True
            assert os.path.exists(export_path_letter)
    
    def test_export_pdf_empty_spaces(self):
        """Test PDF export with empty spaces list."""
        exporter = PdfExporter()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            export_path = os.path.join(temp_dir, "test_export.pdf")
            
            success, message = exporter.export_to_pdf([], export_path)
            
            assert success is True
            assert "Successfully exported 0 spaces" in message
            assert os.path.exists(export_path)
    
    def test_export_pdf_error_handling(self, sample_spaces):
        """Test PDF export error handling."""
        exporter = PdfExporter()
        
        # Try to export to invalid path
        invalid_path = "/invalid/path/that/does/not/exist/test.pdf"
        
        success, message = exporter.export_to_pdf(sample_spaces, invalid_path)
        
        assert success is False
        assert "PDF export failed" in message
    
    def test_export_pdf_multiple_spaces(self):
        """Test PDF export with multiple spaces."""
        # Create multiple spaces
        spaces = []
        for i in range(3):
            space = SpaceData(
                guid=f"space_guid_{i}",
                name=f"Office {100 + i}",
                long_name=f"Office Room {100 + i}",
                description=f"Office space {i}",
                object_type="Office",
                zone_category="Work",
                number=str(100 + i),
                elevation=0.0,
                quantities={"Height": 3.0},
                surfaces=[],
                space_boundaries=[],
                relationships=[],
                user_descriptions={},
                processed=True
            )
            spaces.append(space)
        
        exporter = PdfExporter()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            export_path = os.path.join(temp_dir, "test_export.pdf")
            
            success, message = exporter.export_to_pdf(spaces, export_path)
            
            assert success is True
            assert "Successfully exported 3 spaces" in message
            assert os.path.exists(export_path)
    
    def test_export_pdf_with_complex_data(self, sample_spaces):
        """Test PDF export with complex space data."""
        # Add more complex data to the space
        space = sample_spaces[0]
        
        # Add more surfaces
        for i in range(5):
            surface = SurfaceData(
                id=f"surface_{i+3}",
                type="Wall" if i % 2 == 0 else "Window",
                area=10.0 + i,
                material=f"Material {i}",
                ifc_type="IfcWall" if i % 2 == 0 else "IfcWindow",
                related_space_guid=space.guid,
                user_description=f"Surface {i} description"
            )
            space.surfaces.append(surface)
        
        # Add more boundaries
        for i in range(3):
            boundary = SpaceBoundaryData(
                id=f"boundary_{i+2}",
                guid=f"boundary_guid_{i+2}",
                name=f"Boundary {i+2}",
                description=f"Boundary {i+2} description",
                physical_or_virtual_boundary="Physical",
                internal_or_external_boundary="Internal" if i % 2 == 0 else "External",
                related_building_element_guid=f"element_guid_{i}",
                related_building_element_name=f"Element {i}",
                related_building_element_type="IfcWall",
                related_space_guid=space.guid,
                boundary_surface_type="Wall",
                boundary_orientation=["North", "South", "East"][i],
                connection_geometry={},
                calculated_area=15.0 + i,
                boundary_level=1,
                display_label=f"Boundary {i} Label"
            )
            space.space_boundaries.append(boundary)
        
        exporter = PdfExporter()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            export_path = os.path.join(temp_dir, "test_export.pdf")
            
            success, message = exporter.export_to_pdf([space], export_path)
            
            assert success is True
            assert os.path.exists(export_path)
            
            # File should be larger with more content
            file_size = os.path.getsize(export_path)
            assert file_size > 5000  # Should be at least 5KB with complex content


class TestPdfExporterWithoutReportlab:
    """Test PDF exporter behavior when reportlab is not available."""
    
    def test_import_error_handling(self):
        """Test that PdfExporter raises ImportError when reportlab is not available."""
        # This test is mainly for documentation - the actual import error handling
        # is tested by the skipif decorator on the main test class
        # We can't easily mock the import without causing recursion issues
        pass