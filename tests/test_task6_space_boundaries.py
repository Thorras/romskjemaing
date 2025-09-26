"""
Unit tests for Task 6.1: Space boundary data extraction and display
"""

import pytest
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ifc_room_schedule.data.space_boundary_model import SpaceBoundaryData
from ifc_room_schedule.data.space_model import SpaceData


class TestSpaceBoundaryModel:
    """Test the SpaceBoundaryData model."""
    
    def test_space_boundary_creation(self):
        """Test creating a space boundary."""
        boundary = SpaceBoundaryData(
            id="test_boundary_1",
            guid="test-guid-123",
            name="Test Boundary",
            description="A test boundary",
            physical_or_virtual_boundary="PHYSICAL",
            internal_or_external_boundary="INTERNAL",
            related_building_element_guid="element-guid-456",
            related_building_element_name="Test Wall",
            related_building_element_type="IfcWall",
            related_space_guid="space-guid-789",
            boundary_surface_type="Wall",
            boundary_orientation="North",
            calculated_area=10.5,
            boundary_level=1
        )
        
        assert boundary.id == "test_boundary_1"
        assert boundary.guid == "test-guid-123"
        assert boundary.is_physical_boundary()
        assert not boundary.is_virtual_boundary()
        assert boundary.is_internal_boundary()
        assert not boundary.is_external_boundary()
        assert boundary.is_first_level_boundary()
        assert not boundary.is_second_level_boundary()
    
    def test_boundary_validation(self):
        """Test boundary data validation."""
        # Test missing GUID
        with pytest.raises(ValueError, match="GUID is required"):
            SpaceBoundaryData(
                id="test",
                guid="",
                name="Test",
                description="Test",
                physical_or_virtual_boundary="PHYSICAL",
                internal_or_external_boundary="INTERNAL",
                related_building_element_guid="",
                related_building_element_name="",
                related_building_element_type="",
                related_space_guid=""
            )
        
        # Test negative area
        with pytest.raises(ValueError, match="Calculated area cannot be negative"):
            SpaceBoundaryData(
                id="test",
                guid="test-guid",
                name="Test",
                description="Test",
                physical_or_virtual_boundary="PHYSICAL",
                internal_or_external_boundary="INTERNAL",
                related_building_element_guid="",
                related_building_element_name="",
                related_building_element_type="",
                related_space_guid="",
                calculated_area=-5.0
            )
    
    def test_display_label_generation(self):
        """Test display label generation."""
        # Test with orientation and surface type
        boundary = SpaceBoundaryData(
            id="test_boundary_1",
            guid="test-guid-123",
            name="Test Boundary",
            description="A test boundary",
            physical_or_virtual_boundary="PHYSICAL",
            internal_or_external_boundary="INTERNAL",
            related_building_element_guid="element-guid-456",
            related_building_element_name="Wall-001",
            related_building_element_type="IfcWall",
            related_space_guid="space-guid-789",
            boundary_surface_type="Wall",
            boundary_orientation="North",
            calculated_area=10.5,
            boundary_level=1
        )
        
        label = boundary.generate_display_label()
        assert "North" in label
        assert "Wall" in label
        assert "Wall-001" in label
        
        # Test virtual boundary
        virtual_boundary = SpaceBoundaryData(
            id="test_boundary_2",
            guid="test-guid-456",
            name="Virtual Test",
            description="A virtual boundary",
            physical_or_virtual_boundary="VIRTUAL",
            internal_or_external_boundary="INTERNAL",
            related_building_element_guid="",
            related_building_element_name="",
            related_building_element_type="IfcVirtualElement",
            related_space_guid="space-guid-789",
            boundary_surface_type="Other",
            calculated_area=0.0,
            boundary_level=2
        )
        
        label = virtual_boundary.generate_display_label()
        assert "Virtual" in label
        
        # Test fallback label
        minimal_boundary = SpaceBoundaryData(
            id="test_boundary_3",
            guid="test-guid-789",
            name="",
            description="",
            physical_or_virtual_boundary="Undefined",
            internal_or_external_boundary="Undefined",
            related_building_element_guid="",
            related_building_element_name="",
            related_building_element_type="",
            related_space_guid=""
        )
        
        label = minimal_boundary.generate_display_label()
        assert "Boundary" in label
        assert "test-guid-789"[-8:] in label
    
    def test_boundary_properties(self):
        """Test boundary property methods."""
        boundary = SpaceBoundaryData(
            id="test_boundary_1",
            guid="test-guid-123",
            name="Test Boundary",
            description="A test boundary",
            physical_or_virtual_boundary="PHYSICAL",
            internal_or_external_boundary="EXTERNAL",
            related_building_element_guid="element-guid-456",
            related_building_element_name="Test Wall",
            related_building_element_type="IfcWall",
            related_space_guid="space-guid-789",
            calculated_area=10.5,
            boundary_level=2
        )
        
        # Test thermal properties
        boundary.set_thermal_property("U-value", 0.25)
        assert boundary.get_thermal_property("U-value") == 0.25
        assert boundary.get_thermal_property("non-existent") is None
        
        # Test material properties
        boundary.set_material_property("density", 2400)
        assert boundary.get_material_property("density") == 2400
        assert boundary.get_material_property("non-existent") is None
        
        # Test to_dict method
        boundary_dict = boundary.to_dict()
        assert boundary_dict["guid"] == "test-guid-123"
        assert boundary_dict["calculated_area"] == 10.5
        assert boundary_dict["thermal_properties"]["U-value"] == 0.25
        assert boundary_dict["material_properties"]["density"] == 2400


class TestSpaceModelBoundaryIntegration:
    """Test space model integration with boundaries."""
    
    def test_space_boundary_integration(self):
        """Test adding boundaries to spaces."""
        space = SpaceData(
            guid="space-guid-123",
            name="Test Space",
            long_name="Test Space Long Name",
            description="A test space",
            object_type="Room",
            zone_category="Office",
            number="101",
            elevation=0.0
        )
        
        boundary = SpaceBoundaryData(
            id="boundary_1",
            guid="boundary-guid-123",
            name="Test Boundary",
            description="A test boundary",
            physical_or_virtual_boundary="PHYSICAL",
            internal_or_external_boundary="INTERNAL",
            related_building_element_guid="element-guid-456",
            related_building_element_name="Test Wall",
            related_building_element_type="IfcWall",
            related_space_guid="space-guid-123",
            boundary_surface_type="Wall",
            calculated_area=15.0,
            boundary_level=1
        )
        
        # Add boundary to space
        space.add_space_boundary(boundary)
        
        assert len(space.space_boundaries) == 1
        assert space.space_boundaries[0] == boundary
        
        # Test boundary area calculations
        total_area = space.get_total_boundary_area()
        assert total_area == 15.0
        
        # Test boundary area by type
        areas_by_type = space.get_boundary_area_by_type()
        assert areas_by_type["Wall"] == 15.0
        
        # Test physical/virtual boundary filtering
        physical_boundaries = space.get_physical_boundaries()
        assert len(physical_boundaries) == 1
        
        virtual_boundaries = space.get_virtual_boundaries()
        assert len(virtual_boundaries) == 0
        
        # Test internal/external boundary filtering
        internal_boundaries = space.get_internal_boundaries()
        assert len(internal_boundaries) == 1
        
        external_boundaries = space.get_external_boundaries()
        assert len(external_boundaries) == 0
    
    def test_multiple_boundaries(self):
        """Test space with multiple boundaries."""
        space = SpaceData(
            guid="space-guid-456",
            name="Multi Boundary Space",
            long_name="Space with Multiple Boundaries",
            description="A test space with multiple boundaries",
            object_type="Room",
            zone_category="Office",
            number="102",
            elevation=0.0
        )
        
        # Add multiple boundaries
        boundaries = [
            SpaceBoundaryData(
                id="boundary_1",
                guid="boundary-guid-1",
                name="North Wall",
                description="North wall boundary",
                physical_or_virtual_boundary="PHYSICAL",
                internal_or_external_boundary="EXTERNAL",
                related_building_element_guid="wall-1",
                related_building_element_name="North Wall",
                related_building_element_type="IfcWall",
                related_space_guid="space-guid-456",
                boundary_surface_type="Wall",
                calculated_area=20.0,
                boundary_level=1
            ),
            SpaceBoundaryData(
                id="boundary_2",
                guid="boundary-guid-2",
                name="Floor",
                description="Floor boundary",
                physical_or_virtual_boundary="PHYSICAL",
                internal_or_external_boundary="EXTERNAL",
                related_building_element_guid="floor-1",
                related_building_element_name="Floor Slab",
                related_building_element_type="IfcSlab",
                related_space_guid="space-guid-456",
                boundary_surface_type="Floor",
                calculated_area=50.0,
                boundary_level=1
            ),
            SpaceBoundaryData(
                id="boundary_3",
                guid="boundary-guid-3",
                name="Virtual Boundary",
                description="Virtual space boundary",
                physical_or_virtual_boundary="VIRTUAL",
                internal_or_external_boundary="INTERNAL",
                related_building_element_guid="",
                related_building_element_name="",
                related_building_element_type="IfcVirtualElement",
                related_space_guid="space-guid-456",
                boundary_surface_type="Other",
                calculated_area=0.0,
                boundary_level=2
            )
        ]
        
        for boundary in boundaries:
            space.add_space_boundary(boundary)
        
        assert len(space.space_boundaries) == 3
        
        # Test area calculations
        total_area = space.get_total_boundary_area()
        assert total_area == 70.0  # 20 + 50 + 0
        
        areas_by_type = space.get_boundary_area_by_type()
        assert areas_by_type["Wall"] == 20.0
        assert areas_by_type["Floor"] == 50.0
        assert areas_by_type["Other"] == 0.0
        
        # Test filtering
        physical_boundaries = space.get_physical_boundaries()
        assert len(physical_boundaries) == 2
        
        virtual_boundaries = space.get_virtual_boundaries()
        assert len(virtual_boundaries) == 1
        
        external_boundaries = space.get_external_boundaries()
        assert len(external_boundaries) == 2
        
        internal_boundaries = space.get_internal_boundaries()
        assert len(internal_boundaries) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])