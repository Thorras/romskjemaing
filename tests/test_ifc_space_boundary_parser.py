"""
Tests for IFC Space Boundary Parser

Tests the extraction and processing of IfcSpaceBoundary entities.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from ifc_room_schedule.parser.ifc_space_boundary_parser import IfcSpaceBoundaryParser
from ifc_room_schedule.data.space_boundary_model import SpaceBoundaryData


class TestIfcSpaceBoundaryParser:
    """Test cases for IfcSpaceBoundaryParser class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.parser = IfcSpaceBoundaryParser()

    def test_init_without_file(self):
        """Test initialization without IFC file."""
        parser = IfcSpaceBoundaryParser()
        assert parser.ifc_file is None
        assert parser._boundaries_cache is None

    def test_init_with_file(self):
        """Test initialization with IFC file."""
        mock_file = Mock()
        parser = IfcSpaceBoundaryParser(mock_file)
        assert parser.ifc_file == mock_file

    def test_set_ifc_file(self):
        """Test setting IFC file."""
        mock_file = Mock()
        self.parser.set_ifc_file(mock_file)
        assert self.parser.ifc_file == mock_file
        assert self.parser._boundaries_cache is None

    def test_extract_space_boundaries_no_file(self):
        """Test extracting boundaries without loaded file."""
        with pytest.raises(ValueError, match="No IFC file loaded"):
            self.parser.extract_space_boundaries()

    def test_extract_space_boundaries_no_boundaries_found(self):
        """Test extracting boundaries when no IfcSpaceBoundary entities exist."""
        mock_file = Mock()
        mock_file.by_type.return_value = []
        
        self.parser.set_ifc_file(mock_file)
        boundaries = self.parser.extract_space_boundaries()
        
        assert boundaries == []
        mock_file.by_type.assert_called_once_with("IfcSpaceBoundary")

    def test_extract_space_boundaries_success(self):
        """Test successful space boundary extraction."""
        # Create mock IfcSpaceBoundary entity
        mock_boundary = Mock()
        mock_boundary.GlobalId = "BOUNDARY123456789"
        mock_boundary.Name = "Wall Boundary"
        mock_boundary.Description = "North wall boundary"
        mock_boundary.PhysicalOrVirtualBoundary = "Physical"
        mock_boundary.InternalOrExternalBoundary = "External"
        
        # Mock related building element
        mock_element = Mock()
        mock_element.GlobalId = "WALL123456789ABC"
        mock_element.Name = "External Wall"
        mock_element.is_a.return_value = "IfcWall"
        mock_boundary.RelatedBuildingElement = mock_element
        
        # Mock related space
        mock_space = Mock()
        mock_space.GlobalId = "SPACE123456789AB"
        mock_space.Name = "Office 101"
        mock_boundary.RelatingSpace = mock_space
        
        # Mock connection geometry
        mock_boundary.ConnectionGeometry = None

        mock_file = Mock()
        mock_file.by_type.return_value = [mock_boundary]
        
        self.parser.set_ifc_file(mock_file)
        boundaries = self.parser.extract_space_boundaries()
        
        assert len(boundaries) == 1
        boundary = boundaries[0]
        assert isinstance(boundary, SpaceBoundaryData)
        assert boundary.guid == "BOUNDARY123456789"
        assert boundary.name == "Wall Boundary"
        assert boundary.physical_or_virtual_boundary == "Physical"
        assert boundary.internal_or_external_boundary == "External"

    def test_extract_space_boundaries_with_space_filter(self):
        """Test extracting boundaries filtered by space GUID."""
        # Create mock boundaries for different spaces
        mock_boundary1 = Mock()
        mock_boundary1.GlobalId = "BOUNDARY1"
        mock_boundary1.Name = "Boundary 1"
        mock_boundary1.Description = ""
        mock_boundary1.PhysicalOrVirtualBoundary = "Physical"
        mock_boundary1.InternalOrExternalBoundary = "Internal"
        mock_boundary1.RelatedBuildingElement = None
        mock_boundary1.ConnectionGeometry = None
        
        mock_space1 = Mock()
        mock_space1.GlobalId = "SPACE1"
        mock_space1.Name = "Office 101"
        mock_boundary1.RelatingSpace = mock_space1
        
        mock_boundary2 = Mock()
        mock_boundary2.GlobalId = "BOUNDARY2"
        mock_boundary2.Name = "Boundary 2"
        mock_boundary2.Description = ""
        mock_boundary2.PhysicalOrVirtualBoundary = "Physical"
        mock_boundary2.InternalOrExternalBoundary = "Internal"
        mock_boundary2.RelatedBuildingElement = None
        mock_boundary2.ConnectionGeometry = None
        
        mock_space2 = Mock()
        mock_space2.GlobalId = "SPACE2"
        mock_space2.Name = "Office 102"
        mock_boundary2.RelatingSpace = mock_space2

        mock_file = Mock()
        mock_file.by_type.return_value = [mock_boundary1, mock_boundary2]
        
        self.parser.set_ifc_file(mock_file)
        boundaries = self.parser.extract_space_boundaries("SPACE1")
        
        assert len(boundaries) == 1
        assert boundaries[0].guid == "BOUNDARY1"

    def test_classify_boundary_surface_type(self):
        """Test boundary surface type classification."""
        # Test wall
        result = self.parser._classify_boundary_surface_type("IfcWall")
        assert result == "Wall"

        # Test slab/floor
        result = self.parser._classify_boundary_surface_type("IfcSlab")
        assert result == "Floor"

        # Test window
        result = self.parser._classify_boundary_surface_type("IfcWindow")
        assert result == "Window"

        # Test door
        result = self.parser._classify_boundary_surface_type("IfcDoor")
        assert result == "Door"

        # Test unknown type
        result = self.parser._classify_boundary_surface_type("IfcUnknown")
        assert result == "Other"

        # Test empty type
        result = self.parser._classify_boundary_surface_type("")
        assert result == "Unknown"

    def test_determine_boundary_level(self):
        """Test boundary level determination."""
        # Test 1st level boundary (with building element)
        mock_element = Mock()
        mock_boundary = Mock()
        mock_boundary.RelatedBuildingElement = mock_element
        
        result = self.parser._determine_boundary_level(mock_boundary)
        assert result == 1

        # Test 2nd level boundary (no building element)
        mock_boundary = Mock()
        mock_boundary.RelatedBuildingElement = None
        
        result = self.parser._determine_boundary_level(mock_boundary)
        assert result == 2

    def test_get_boundary_count(self):
        """Test getting boundary count."""
        # Test with no file
        count = self.parser.get_boundary_count()
        assert count == 0

        # Test with file
        mock_file = Mock()
        mock_file.by_type.return_value = [Mock(), Mock(), Mock()]
        
        self.parser.set_ifc_file(mock_file)
        count = self.parser.get_boundary_count()
        assert count == 3

    def test_validate_boundaries_success(self):
        """Test successful boundary validation."""
        boundary = SpaceBoundaryData(
            id="boundary1",
            guid="VALID123456789ABC",
            name="Valid Boundary",
            description="Valid description",
            physical_or_virtual_boundary="Physical",
            internal_or_external_boundary="Internal",
            related_building_element_guid="ELEMENT123",
            related_building_element_name="Valid Element",
            related_building_element_type="IfcWall",
            related_space_guid="SPACE123",
            calculated_area=10.5
        )
        
        is_valid, errors = self.parser.validate_boundaries([boundary])
        assert is_valid
        assert len(errors) == 0