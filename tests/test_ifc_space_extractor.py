"""
Tests for IFC Space Extractor

Tests the extraction of IfcSpace entities and their properties.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from ifc_room_schedule.parser.ifc_space_extractor import IfcSpaceExtractor
from ifc_room_schedule.data.space_model import SpaceData


class TestIfcSpaceExtractor:
    """Test cases for IfcSpaceExtractor class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = IfcSpaceExtractor()

    def test_init_without_file(self):
        """Test initialization without IFC file."""
        extractor = IfcSpaceExtractor()
        assert extractor.ifc_file is None
        assert extractor._spaces_cache is None

    def test_init_with_file(self):
        """Test initialization with IFC file."""
        mock_file = Mock()
        extractor = IfcSpaceExtractor(mock_file)
        assert extractor.ifc_file == mock_file

    def test_set_ifc_file(self):
        """Test setting IFC file."""
        mock_file = Mock()
        self.extractor.set_ifc_file(mock_file)
        assert self.extractor.ifc_file == mock_file
        assert self.extractor._spaces_cache is None

    def test_extract_spaces_no_file(self):
        """Test extracting spaces without loaded file."""
        with pytest.raises(ValueError, match="No IFC file loaded"):
            self.extractor.extract_spaces()

    def test_extract_spaces_no_spaces_found(self):
        """Test extracting spaces when no IfcSpace entities exist."""
        mock_file = Mock()
        mock_file.by_type.return_value = []
        
        self.extractor.set_ifc_file(mock_file)
        spaces = self.extractor.extract_spaces()
        
        assert spaces == []
        mock_file.by_type.assert_called_once_with("IfcSpace")

    def test_extract_spaces_success(self):
        """Test successful space extraction."""
        # Create mock IfcSpace entity
        mock_space = Mock()
        mock_space.GlobalId = "1234567890ABCDEF"
        mock_space.Name = "Office 101"
        mock_space.LongName = "Main Office Room"
        mock_space.Description = "Primary office space"
        mock_space.ObjectType = "Office"
        mock_space.ElevationWithFlooring = 0.0
        mock_space.IsDefinedBy = []

        mock_file = Mock()
        mock_file.by_type.return_value = [mock_space]
        
        self.extractor.set_ifc_file(mock_file)
        spaces = self.extractor.extract_spaces()
        
        assert len(spaces) == 1
        space = spaces[0]
        assert isinstance(space, SpaceData)
        assert space.guid == "1234567890ABCDEF"
        assert space.name == "Office 101"
        assert space.long_name == "Main Office Room"
        assert space.description == "Primary office space"
        assert space.object_type == "Office"

    def test_extract_spaces_with_error(self):
        """Test space extraction with errors in individual spaces."""
        # Create one good space and one bad space
        good_space = Mock()
        good_space.GlobalId = "GOOD123456789ABC"
        good_space.Name = "Good Room"
        good_space.LongName = "Good Room"
        good_space.Description = ""
        good_space.ObjectType = "Office"
        good_space.ElevationWithFlooring = 0.0
        good_space.IsDefinedBy = []

        bad_space = Mock()
        bad_space.GlobalId = None  # This will cause an error
        
        mock_file = Mock()
        mock_file.by_type.return_value = [good_space, bad_space]
        
        self.extractor.set_ifc_file(mock_file)
        spaces = self.extractor.extract_spaces()
        
        # Should only return the good space
        assert len(spaces) == 1
        assert spaces[0].guid == "GOOD123456789ABC"

    def test_get_space_by_guid(self):
        """Test getting space by GUID."""
        mock_space = Mock()
        mock_space.GlobalId = "TEST123456789ABC"
        mock_space.Name = "Test Room"
        mock_space.LongName = "Test Room"
        mock_space.Description = ""
        mock_space.ObjectType = "Office"
        mock_space.ElevationWithFlooring = 0.0
        mock_space.IsDefinedBy = []

        mock_file = Mock()
        mock_file.by_type.return_value = [mock_space]
        
        self.extractor.set_ifc_file(mock_file)
        
        # Test finding existing space
        space = self.extractor.get_space_by_guid("TEST123456789ABC")
        assert space is not None
        assert space.guid == "TEST123456789ABC"
        
        # Test finding non-existing space
        space = self.extractor.get_space_by_guid("NONEXISTENT")
        assert space is None

    def test_extract_quantities(self):
        """Test quantity extraction from IfcSpace."""
        # Create mock quantity set
        mock_quantity = Mock()
        mock_quantity.is_a.return_value = True
        mock_quantity.Name = "Height"
        mock_quantity.LengthValue = 3.0

        mock_quantity_set = Mock()
        mock_quantity_set.is_a.return_value = True
        mock_quantity_set.Quantities = [mock_quantity]

        mock_relationship = Mock()
        mock_relationship.is_a.return_value = True
        mock_relationship.RelatingPropertyDefinition = mock_quantity_set

        mock_space = Mock()
        mock_space.IsDefinedBy = [mock_relationship]

        # Mock the is_a method calls
        def mock_is_a(type_name):
            if type_name == 'IfcRelDefinesByProperties':
                return True
            elif type_name == 'IfcElementQuantity':
                return True
            elif type_name == 'IfcQuantityLength':
                return True
            return False

        mock_relationship.is_a = mock_is_a
        mock_quantity_set.is_a = mock_is_a
        mock_quantity.is_a = mock_is_a

        quantities = self.extractor._extract_quantities(mock_space)
        assert "Height" in quantities
        assert quantities["Height"] == 3.0

    def test_determine_zone_category(self):
        """Test zone category determination."""
        # Test with ObjectType
        mock_space = Mock()
        mock_space.ObjectType = "Meeting Room"
        mock_space.LongName = ""
        mock_space.Name = ""
        
        category = self.extractor._determine_zone_category(mock_space)
        assert category == "Meeting Room"

        # Test with LongName containing office keyword
        mock_space.ObjectType = ""
        mock_space.LongName = "Main Office Space"
        
        category = self.extractor._determine_zone_category(mock_space)
        assert category == "Office"

        # Test with Name containing office keyword
        mock_space.LongName = ""
        mock_space.Name = "Office 101"
        
        category = self.extractor._determine_zone_category(mock_space)
        assert category == "Office"

        # Test with no recognizable keywords
        mock_space.Name = "Random Room"
        
        category = self.extractor._determine_zone_category(mock_space)
        assert category == "Unspecified"

    def test_extract_space_number(self):
        """Test space number extraction."""
        # Test with Name
        mock_space = Mock()
        mock_space.Name = "101"
        mock_space.LongName = ""
        mock_space.GlobalId = "1234567890ABCDEF"
        
        number = self.extractor._extract_space_number(mock_space)
        assert number == "101"

        # Test with LongName containing number
        mock_space.Name = ""
        mock_space.LongName = "Office 205"
        
        number = self.extractor._extract_space_number(mock_space)
        assert number == "205"

        # Test fallback to GUID
        mock_space.LongName = "No Number Here"
        
        number = self.extractor._extract_space_number(mock_space)
        assert number == "90ABCDEF"  # Last 8 characters of GUID

    def test_get_space_count(self):
        """Test getting space count."""
        # Test with no file
        count = self.extractor.get_space_count()
        assert count == 0

        # Test with file
        mock_file = Mock()
        mock_file.by_type.return_value = [Mock(), Mock(), Mock()]
        
        self.extractor.set_ifc_file(mock_file)
        count = self.extractor.get_space_count()
        assert count == 3

    def test_validate_spaces_empty(self):
        """Test validating empty space list."""
        is_valid, errors = self.extractor.validate_spaces([])
        assert not is_valid
        assert "No spaces found to validate" in errors

    def test_validate_spaces_duplicate_guids(self):
        """Test validating spaces with duplicate GUIDs."""
        space1 = SpaceData(
            guid="DUPLICATE",
            name="Room 1",
            long_name="Room 1",
            description="",
            object_type="Office",
            zone_category="Office",
            number="1",
            elevation=0.0
        )
        space2 = SpaceData(
            guid="DUPLICATE",
            name="Room 2", 
            long_name="Room 2",
            description="",
            object_type="Office",
            zone_category="Office",
            number="2",
            elevation=0.0
        )
        
        is_valid, errors = self.extractor.validate_spaces([space1, space2])
        assert not is_valid
        assert any("Duplicate GUIDs" in error for error in errors)

    def test_validate_spaces_missing_properties(self):
        """Test validating spaces with missing properties."""
        # Create a space with valid GUID but missing names
        space = SpaceData(
            guid="VALID123456789ABC",
            name="",  # Missing name
            long_name="",  # Missing long name
            description="",
            object_type="Office",
            zone_category="Office", 
            number="1",
            elevation=0.0
        )
        
        is_valid, errors = self.extractor.validate_spaces([space])
        assert not is_valid
        assert any("Missing both Name and LongName" in error for error in errors)

    def test_validate_spaces_success(self):
        """Test successful space validation."""
        space = SpaceData(
            guid="VALID123456789ABC",
            name="Valid Room",
            long_name="Valid Room Long Name",
            description="Valid description",
            object_type="Office",
            zone_category="Office",
            number="101",
            elevation=0.0
        )
        
        is_valid, errors = self.extractor.validate_spaces([space])
        assert is_valid
        assert len(errors) == 0

    def test_extract_spaces_runtime_error(self):
        """Test runtime error during space extraction."""
        mock_file = Mock()
        mock_file.by_type.side_effect = Exception("IFC file error")
        
        self.extractor.set_ifc_file(mock_file)
        
        with pytest.raises(RuntimeError, match="Failed to extract spaces"):
            self.extractor.extract_spaces()