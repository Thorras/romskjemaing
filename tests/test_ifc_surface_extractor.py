"""
Tests for IFC Surface Extractor

Unit tests for surface extraction functionality.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from ifc_room_schedule.parser.ifc_surface_extractor import IfcSurfaceExtractor
from ifc_room_schedule.data.surface_model import SurfaceData


class TestIfcSurfaceExtractor:
    """Test cases for IfcSurfaceExtractor."""

    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = IfcSurfaceExtractor()
        self.mock_ifc_file = Mock()
        self.extractor.set_ifc_file(self.mock_ifc_file)

    def test_initialization(self):
        """Test extractor initialization."""
        extractor = IfcSurfaceExtractor()
        assert extractor.ifc_file is None
        
        extractor_with_file = IfcSurfaceExtractor(self.mock_ifc_file)
        assert extractor_with_file.ifc_file == self.mock_ifc_file

    def test_set_ifc_file(self):
        """Test setting IFC file."""
        new_file = Mock()
        self.extractor.set_ifc_file(new_file)
        assert self.extractor.ifc_file == new_file

    def test_extract_surfaces_no_file(self):
        """Test surface extraction without IFC file."""
        extractor = IfcSurfaceExtractor()
        
        with pytest.raises(ValueError, match="No IFC file loaded"):
            extractor.extract_surfaces_for_space("test-guid")

    def test_extract_surfaces_space_not_found(self):
        """Test surface extraction for non-existent space."""
        self.mock_ifc_file.by_guid.side_effect = Exception("Not found")
        
        surfaces = self.extractor.extract_surfaces_for_space("non-existent-guid")
        assert surfaces == []

    def test_extract_surfaces_from_boundaries(self):
        """Test surface extraction from space boundaries."""
        # Create mock space
        mock_space = Mock()
        mock_space.GlobalId = "space-guid"
        
        # Create mock boundary relationship
        mock_boundary_rel = Mock()
        mock_boundary_rel.is_a.return_value = True
        mock_boundary_rel.is_a = lambda x: x == 'IfcRelSpaceBoundary'
        
        # Create mock building element
        mock_element = Mock()
        mock_element.GlobalId = "element-guid"
        mock_element.Name = "Test Wall"
        mock_element.is_a.return_value = "IfcWall"
        mock_element.Description = "Test wall description"
        mock_boundary_rel.RelatedBuildingElement = mock_element
        
        mock_space.BoundedBy = [mock_boundary_rel]
        
        # Mock the file lookup
        self.mock_ifc_file.by_guid.return_value = mock_space
        
        # Mock area calculation
        with patch.object(self.extractor, '_calculate_element_area', return_value=10.5):
            with patch.object(self.extractor, '_extract_material', return_value="Concrete"):
                surfaces = self.extractor.extract_surfaces_for_space("space-guid")
        
        assert len(surfaces) == 1
        surface = surfaces[0]
        assert surface.id == "element-guid"
        assert surface.type == "Wall"
        assert surface.area == 10.5
        assert surface.material == "Concrete"
        assert surface.related_space_guid == "space-guid"

    def test_determine_surface_type(self):
        """Test surface type determination."""
        # Test wall types
        mock_wall = Mock()
        mock_wall.is_a.return_value = "IfcWall"
        assert self.extractor._determine_surface_type(mock_wall) == "Wall"
        
        # Test slab with floor predefined type
        mock_floor_slab = Mock()
        mock_floor_slab.is_a.return_value = "IfcSlab"
        mock_floor_slab.PredefinedType = "FLOOR"
        assert self.extractor._determine_surface_type(mock_floor_slab) == "Floor"
        
        # Test slab with roof predefined type
        mock_roof_slab = Mock()
        mock_roof_slab.is_a.return_value = "IfcSlab"
        mock_roof_slab.PredefinedType = "ROOF"
        assert self.extractor._determine_surface_type(mock_roof_slab) == "Ceiling"
        
        # Test window
        mock_window = Mock()
        mock_window.is_a.return_value = "IfcWindow"
        assert self.extractor._determine_surface_type(mock_window) == "Opening"
        
        # Test unknown type
        mock_unknown = Mock()
        mock_unknown.is_a.return_value = "IfcUnknownType"
        assert self.extractor._determine_surface_type(mock_unknown) == "Unknown"

    def test_calculate_element_area_from_quantities(self):
        """Test area calculation from IFC quantities."""
        mock_element = Mock()
        
        # Create mock quantity
        mock_quantity = Mock()
        mock_quantity.is_a.return_value = True
        mock_quantity.is_a = lambda x: x == 'IfcQuantityArea'
        mock_quantity.Name = "NetSideArea"
        mock_quantity.AreaValue = 15.75
        
        # Create mock quantity set
        mock_quantity_set = Mock()
        mock_quantity_set.is_a.return_value = True
        mock_quantity_set.is_a = lambda x: x == 'IfcElementQuantity'
        mock_quantity_set.Quantities = [mock_quantity]
        
        # Create mock relationship
        mock_rel = Mock()
        mock_rel.is_a.return_value = True
        mock_rel.is_a = lambda x: x == 'IfcRelDefinesByProperties'
        mock_rel.RelatingPropertyDefinition = mock_quantity_set
        
        mock_element.IsDefinedBy = [mock_rel]
        
        area = self.extractor._get_area_from_quantities(mock_element)
        assert area == 15.75

    def test_calculate_element_area_no_quantities(self):
        """Test area calculation when no quantities available."""
        mock_element = Mock()
        mock_element.IsDefinedBy = []
        
        area = self.extractor._get_area_from_quantities(mock_element)
        assert area == 0.0

    def test_extract_material(self):
        """Test material extraction."""
        mock_element = Mock()
        
        # Create mock material
        mock_material = Mock()
        mock_material.is_a.return_value = True
        mock_material.is_a = lambda x: x == 'IfcMaterial'
        mock_material.Name = "Concrete"
        
        # Create mock material association
        mock_rel = Mock()
        mock_rel.is_a.return_value = True
        mock_rel.is_a = lambda x: x == 'IfcRelAssociatesMaterial'
        mock_rel.RelatingMaterial = mock_material
        
        mock_element.HasAssociations = [mock_rel]
        
        material = self.extractor._extract_material(mock_element)
        assert material == "Concrete"

    def test_extract_material_no_associations(self):
        """Test material extraction when no associations exist."""
        mock_element = Mock()
        mock_element.HasAssociations = []
        
        material = self.extractor._extract_material(mock_element)
        assert material == "Unknown"

    def test_calculate_surface_areas_by_type(self):
        """Test surface area calculation by type."""
        surfaces = [
            SurfaceData("1", "Wall", 10.0, "Concrete", "IfcWall", "space-1"),
            SurfaceData("2", "Wall", 15.0, "Concrete", "IfcWall", "space-1"),
            SurfaceData("3", "Floor", 25.0, "Wood", "IfcSlab", "space-1"),
            SurfaceData("4", "Ceiling", 25.0, "Plaster", "IfcSlab", "space-1"),
        ]
        
        areas_by_type = self.extractor.calculate_surface_areas_by_type(surfaces)
        
        assert areas_by_type["Wall"] == 25.0
        assert areas_by_type["Floor"] == 25.0
        assert areas_by_type["Ceiling"] == 25.0

    def test_validate_surfaces_valid(self):
        """Test surface validation with valid data."""
        surfaces = [
            SurfaceData("1", "Wall", 10.0, "Concrete", "IfcWall", "space-1"),
            SurfaceData("2", "Floor", 25.0, "Wood", "IfcSlab", "space-1"),
        ]
        
        is_valid, messages = self.extractor.validate_surfaces(surfaces)
        assert is_valid is True
        assert len(messages) == 0

    def test_validate_surfaces_duplicate_ids(self):
        """Test surface validation with duplicate IDs."""
        surfaces = [
            SurfaceData("1", "Wall", 10.0, "Concrete", "IfcWall", "space-1"),
            SurfaceData("1", "Floor", 25.0, "Wood", "IfcSlab", "space-1"),  # Duplicate ID
        ]
        
        is_valid, messages = self.extractor.validate_surfaces(surfaces)
        assert is_valid is False
        assert any("Duplicate surface IDs" in msg for msg in messages)

    def test_validate_surfaces_zero_area(self):
        """Test surface validation with zero area surfaces."""
        surfaces = [
            SurfaceData("1", "Wall", 0.0, "Concrete", "IfcWall", "space-1"),  # Zero area
            SurfaceData("2", "Floor", 25.0, "Wood", "IfcSlab", "space-1"),
        ]
        
        is_valid, messages = self.extractor.validate_surfaces(surfaces)
        assert is_valid is True  # Zero area is a warning, not an error
        assert any("zero or invalid area" in msg for msg in messages)

    def test_validate_surfaces_no_material(self):
        """Test surface validation with missing materials."""
        surfaces = [
            SurfaceData("1", "Wall", 10.0, "", "IfcWall", "space-1"),  # No material
            SurfaceData("2", "Floor", 25.0, "Wood", "IfcSlab", "space-1"),
        ]
        
        is_valid, messages = self.extractor.validate_surfaces(surfaces)
        assert is_valid is True  # No material is a warning, not an error
        assert any("no material information" in msg for msg in messages)

    def test_validate_surfaces_empty_list(self):
        """Test surface validation with empty list."""
        surfaces = []
        
        is_valid, messages = self.extractor.validate_surfaces(surfaces)
        assert is_valid is True  # Empty list is valid but generates warning
        assert any("No surfaces found" in msg for msg in messages)

    def test_is_surface_element(self):
        """Test surface element identification."""
        # Test wall element
        mock_wall = Mock()
        mock_wall.is_a = lambda x: x == 'IfcWall'
        assert self.extractor._is_surface_element(mock_wall) is True
        
        # Test slab element
        mock_slab = Mock()
        mock_slab.is_a = lambda x: x == 'IfcSlab'
        assert self.extractor._is_surface_element(mock_slab) is True
        
        # Test window element
        mock_window = Mock()
        mock_window.is_a = lambda x: x == 'IfcWindow'
        assert self.extractor._is_surface_element(mock_window) is True
        
        # Test non-surface element
        mock_beam = Mock()
        mock_beam.is_a = lambda x: x == 'IfcBeam'
        assert self.extractor._is_surface_element(mock_beam) is False

    def test_estimate_area_from_properties_wall(self):
        """Test area estimation for wall elements."""
        mock_wall = Mock()
        mock_wall.is_a.return_value = "IfcWall"
        
        # Create mock height quantity
        mock_height_quantity = Mock()
        mock_height_quantity.is_a.return_value = True
        mock_height_quantity.is_a = lambda x: x == 'IfcQuantityLength'
        mock_height_quantity.Name = "Height"
        mock_height_quantity.LengthValue = 3.0
        
        # Create mock length quantity
        mock_length_quantity = Mock()
        mock_length_quantity.is_a.return_value = True
        mock_length_quantity.is_a = lambda x: x == 'IfcQuantityLength'
        mock_length_quantity.Name = "Length"
        mock_length_quantity.LengthValue = 5.0
        
        # Create mock quantity set
        mock_quantity_set = Mock()
        mock_quantity_set.is_a.return_value = True
        mock_quantity_set.is_a = lambda x: x == 'IfcElementQuantity'
        mock_quantity_set.Quantities = [mock_height_quantity, mock_length_quantity]
        
        # Create mock relationship
        mock_rel = Mock()
        mock_rel.is_a.return_value = True
        mock_rel.is_a = lambda x: x == 'IfcRelDefinesByProperties'
        mock_rel.RelatingPropertyDefinition = mock_quantity_set
        
        mock_wall.IsDefinedBy = [mock_rel]
        
        area = self.extractor._estimate_area_from_properties(mock_wall)
        assert area == 15.0  # height * length = 3.0 * 5.0

    def test_estimate_area_from_properties_slab(self):
        """Test area estimation for slab elements."""
        mock_slab = Mock()
        mock_slab.is_a.return_value = "IfcSlab"
        
        # Create mock length quantity
        mock_length_quantity = Mock()
        mock_length_quantity.is_a.return_value = True
        mock_length_quantity.is_a = lambda x: x == 'IfcQuantityLength'
        mock_length_quantity.Name = "Length"
        mock_length_quantity.LengthValue = 4.0
        
        # Create mock width quantity
        mock_width_quantity = Mock()
        mock_width_quantity.is_a.return_value = True
        mock_width_quantity.is_a = lambda x: x == 'IfcQuantityLength'
        mock_width_quantity.Name = "Width"
        mock_width_quantity.LengthValue = 6.0
        
        # Create mock quantity set
        mock_quantity_set = Mock()
        mock_quantity_set.is_a.return_value = True
        mock_quantity_set.is_a = lambda x: x == 'IfcElementQuantity'
        mock_quantity_set.Quantities = [mock_length_quantity, mock_width_quantity]
        
        # Create mock relationship
        mock_rel = Mock()
        mock_rel.is_a.return_value = True
        mock_rel.is_a = lambda x: x == 'IfcRelDefinesByProperties'
        mock_rel.RelatingPropertyDefinition = mock_quantity_set
        
        mock_slab.IsDefinedBy = [mock_rel]
        
        area = self.extractor._estimate_area_from_properties(mock_slab)
        assert area == 24.0  # length * width = 4.0 * 6.0