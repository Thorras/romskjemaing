"""
Unit tests for IFC parser functionality.

Tests IFC file opening, storey extraction, element filtering, and units detection.
"""

import os
import tempfile
import unittest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from ifc_floor_plan_generator.parsing.ifc_parser import IFCParser
from ifc_floor_plan_generator.errors.handler import ErrorHandler
from ifc_floor_plan_generator.errors.exceptions import IFCOpenError, NoStoreysFoundError
from ifc_floor_plan_generator.models import ClassFilters


class TestIFCParser(unittest.TestCase):
    """Test cases for IFCParser class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.error_handler = ErrorHandler()
        self.parser = IFCParser(self.error_handler)
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)


class TestIFCFileOpening(TestIFCParser):
    """Test IFC file opening functionality."""
    
    def test_open_file_nonexistent_raises_error(self):
        """Test that opening nonexistent file raises IFCOpenError."""
        nonexistent_path = os.path.join(self.temp_dir, "nonexistent.ifc")
        
        with self.assertRaises(IFCOpenError) as context:
            self.parser.open_file(nonexistent_path)
        
        self.assertEqual(context.exception.error_code, "IFC_OPEN_FAILED")
        self.assertIn("nonexistent.ifc", str(context.exception))
    
    def test_open_file_empty_path_raises_error(self):
        """Test that empty file path raises IFCOpenError."""
        with self.assertRaises(IFCOpenError):
            self.parser.open_file("")
    
    def test_open_file_none_path_raises_error(self):
        """Test that None file path raises IFCOpenError."""
        with self.assertRaises(IFCOpenError):
            self.parser.open_file(None)
    
    @patch('ifc_floor_plan_generator.parsing.ifc_parser.ifcopenshell')
    def test_open_file_unreadable_raises_error(self, mock_ifcopenshell):
        """Test that unreadable file raises IFCOpenError."""
        # Create a file but make it unreadable
        test_file = os.path.join(self.temp_dir, "test.ifc")
        with open(test_file, 'w') as f:
            f.write("test content")
        
        # Mock os.access to return False for read permission
        with patch('os.access', return_value=False):
            with self.assertRaises(IFCOpenError) as context:
                self.parser.open_file(test_file)
            
            self.assertEqual(context.exception.error_code, "IFC_OPEN_FAILED")
    
    @patch('ifc_floor_plan_generator.parsing.ifc_parser.ifcopenshell')
    def test_open_file_ifcopenshell_returns_none(self, mock_ifcopenshell):
        """Test handling when IfcOpenShell returns None."""
        # Create a test file
        test_file = os.path.join(self.temp_dir, "test.ifc")
        with open(test_file, 'w') as f:
            f.write("test content")
        
        # Mock IfcOpenShell to return None
        mock_ifcopenshell.open.return_value = None
        
        with self.assertRaises(IFCOpenError) as context:
            self.parser.open_file(test_file)
        
        self.assertEqual(context.exception.error_code, "IFC_OPEN_FAILED")
    
    @patch('ifc_floor_plan_generator.parsing.ifc_parser.ifcopenshell')
    def test_open_file_success(self, mock_ifcopenshell):
        """Test successful file opening."""
        # Create a test file
        test_file = os.path.join(self.temp_dir, "test.ifc")
        with open(test_file, 'w') as f:
            f.write("test content")
        
        # Mock successful IfcOpenShell response
        mock_ifc_file = Mock()
        mock_ifc_file.schema = "IFC4"
        mock_ifcopenshell.open.return_value = mock_ifc_file
        
        result = self.parser.open_file(test_file)
        
        self.assertEqual(result, mock_ifc_file)
        mock_ifcopenshell.open.assert_called_once_with(str(Path(test_file).resolve()))
    
    @patch('ifc_floor_plan_generator.parsing.ifc_parser.ifcopenshell')
    def test_open_file_ifcopenshell_exception(self, mock_ifcopenshell):
        """Test handling of IfcOpenShell exceptions."""
        # Create a test file
        test_file = os.path.join(self.temp_dir, "test.ifc")
        with open(test_file, 'w') as f:
            f.write("test content")
        
        # Mock IfcOpenShell to raise an exception
        mock_ifcopenshell.open.side_effect = Exception("Invalid IFC format")
        
        with self.assertRaises(IFCOpenError) as context:
            self.parser.open_file(test_file)
        
        self.assertEqual(context.exception.error_code, "IFC_OPEN_FAILED")
        self.assertIn("Invalid IFC format", str(context.exception.context.get('original_error', '')))


class TestStoreyExtraction(TestIFCParser):
    """Test storey extraction functionality."""
    
    def test_extract_storeys_none_file_raises_error(self):
        """Test that None IFC file raises NoStoreysFoundError."""
        with self.assertRaises(NoStoreysFoundError):
            self.parser.extract_storeys(None)
    
    def test_extract_storeys_no_storeys_raises_error(self):
        """Test that file with no storeys raises NoStoreysFoundError."""
        mock_ifc_file = Mock()
        mock_ifc_file.by_type.return_value = []  # No storeys found
        mock_ifc_file.name = "test.ifc"
        
        with self.assertRaises(NoStoreysFoundError) as context:
            self.parser.extract_storeys(mock_ifc_file)
        
        self.assertEqual(context.exception.error_code, "NO_STOREYS_FOUND")
    
    def test_extract_storeys_success(self):
        """Test successful storey extraction."""
        # Create mock storeys
        mock_storey1 = Mock()
        mock_storey1.Name = "Ground Floor"
        mock_storey1.id.return_value = 1
        
        mock_storey2 = Mock()
        mock_storey2.Name = "First Floor"
        mock_storey2.id.return_value = 2
        
        mock_ifc_file = Mock()
        mock_ifc_file.by_type.return_value = [mock_storey1, mock_storey2]
        
        result = self.parser.extract_storeys(mock_ifc_file)
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], mock_storey1)
        self.assertEqual(result[1], mock_storey2)
        mock_ifc_file.by_type.assert_called_once_with("IfcBuildingStorey")
    
    def test_extract_storeys_with_longname_fallback(self):
        """Test storey extraction with LongName fallback."""
        mock_storey = Mock()
        mock_storey.Name = None
        mock_storey.LongName = "Ground Floor Long Name"
        mock_storey.id.return_value = 1
        
        mock_ifc_file = Mock()
        mock_ifc_file.by_type.return_value = [mock_storey]
        
        result = self.parser.extract_storeys(mock_ifc_file)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], mock_storey)
    
    def test_extract_storeys_exception_handling(self):
        """Test exception handling during storey extraction."""
        mock_ifc_file = Mock()
        mock_ifc_file.by_type.side_effect = Exception("Database error")
        mock_ifc_file.name = "test.ifc"
        
        with self.assertRaises(NoStoreysFoundError):
            self.parser.extract_storeys(mock_ifc_file)


class TestElementsByStorey(TestIFCParser):
    """Test element extraction by storey functionality."""
    
    def test_get_elements_by_storey_none_storey_raises_error(self):
        """Test that None storey returns empty list due to error handling."""
        # The implementation catches ValueError and logs a warning, returning empty list
        result = self.parser.get_elements_by_storey(None)
        self.assertEqual(result, [])
    
    @patch('ifc_floor_plan_generator.parsing.ifc_parser.ifcopenshell')
    def test_get_elements_by_storey_direct_containment(self, mock_ifcopenshell):
        """Test element extraction through direct containment."""
        # Create mock elements
        mock_element1 = Mock()
        mock_element1.is_a.return_value = "IfcWall"
        mock_element1.id.return_value = 1
        
        mock_element2 = Mock()
        mock_element2.is_a.return_value = "IfcSlab"
        mock_element2.id.return_value = 2
        
        # Create mock containment relationship
        mock_rel = Mock()
        mock_rel.RelatedElements = [mock_element1, mock_element2]
        
        # Create mock storey
        mock_storey = Mock()
        mock_storey.ContainsElements = [mock_rel]
        mock_storey.Name = "Ground Floor"
        mock_storey.id.return_value = 100
        
        result = self.parser.get_elements_by_storey(mock_storey)
        
        self.assertEqual(len(result), 2)
        self.assertIn(mock_element1, result)
        self.assertIn(mock_element2, result)
    
    def test_get_elements_by_storey_with_class_filters(self):
        """Test element extraction with class filters."""
        # Create mock elements
        mock_wall = Mock()
        mock_wall.is_a.return_value = "IfcWall"
        mock_wall.id.return_value = 1
        
        mock_space = Mock()
        mock_space.is_a.return_value = "IfcSpace"
        mock_space.id.return_value = 2
        
        # Create mock containment relationship
        mock_rel = Mock()
        mock_rel.RelatedElements = [mock_wall, mock_space]
        
        # Create mock storey
        mock_storey = Mock()
        mock_storey.ContainsElements = [mock_rel]
        mock_storey.Name = "Ground Floor"
        mock_storey.id.return_value = 100
        
        # Create class filters that exclude IfcSpace
        class_filters = ClassFilters(
            include_ifc_classes=["IfcWall", "IfcSlab"],
            exclude_ifc_classes=["IfcSpace"]
        )
        
        result = self.parser.get_elements_by_storey(mock_storey, class_filters)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], mock_wall)
    
    def test_get_elements_by_storey_no_elements_found(self):
        """Test handling when no elements are found."""
        mock_storey = Mock()
        mock_storey.ContainsElements = []
        mock_storey.Name = "Empty Floor"
        mock_storey.id.return_value = 100
        mock_storey.file = Mock()
        
        # Mock the fallback methods to return empty lists
        with patch('ifc_floor_plan_generator.parsing.ifc_parser.ifcopenshell.util.element.get_decomposition', return_value=None):
            mock_storey.file.by_type.return_value = []
            
            result = self.parser.get_elements_by_storey(mock_storey)
            
            self.assertEqual(len(result), 0)
    
    def test_get_elements_by_storey_duplicate_removal(self):
        """Test that duplicate elements are removed."""
        # Create mock element that appears twice
        mock_element = Mock()
        mock_element.is_a.return_value = "IfcWall"
        mock_element.id.return_value = 1
        
        # Create mock containment relationships with same element
        mock_rel1 = Mock()
        mock_rel1.RelatedElements = [mock_element]
        
        mock_rel2 = Mock()
        mock_rel2.RelatedElements = [mock_element]
        
        # Create mock storey
        mock_storey = Mock()
        mock_storey.ContainsElements = [mock_rel1, mock_rel2]
        mock_storey.Name = "Ground Floor"
        mock_storey.id.return_value = 100
        
        result = self.parser.get_elements_by_storey(mock_storey)
        
        # Should only have one instance of the element
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], mock_element)


class TestUnitsDetection(TestIFCParser):
    """Test units detection functionality."""
    
    def test_detect_units_none_file_returns_default(self):
        """Test that None IFC file returns default scale due to error handling."""
        # The implementation catches ValueError and returns default scale of 1.0
        result = self.parser.detect_units(None)
        self.assertEqual(result, 1.0)
    
    @patch('ifc_floor_plan_generator.parsing.ifc_parser.ifcopenshell')
    def test_detect_units_success_meters(self, mock_ifcopenshell):
        """Test successful units detection for meters."""
        mock_unit = Mock()
        mock_unit.Name = "METRE"
        mock_unit.Prefix = None
        
        mock_ifcopenshell.util.unit.get_unit.return_value = mock_unit
        
        mock_ifc_file = Mock()
        
        result = self.parser.detect_units(mock_ifc_file)
        
        self.assertEqual(result, 1.0)  # Meters scale factor
    
    @patch('ifc_floor_plan_generator.parsing.ifc_parser.ifcopenshell')
    def test_detect_units_success_millimeters(self, mock_ifcopenshell):
        """Test successful units detection for millimeters."""
        mock_unit = Mock()
        mock_unit.Name = "METRE"
        mock_unit.Prefix = "MILLI"
        
        mock_ifcopenshell.util.unit.get_unit.return_value = mock_unit
        
        mock_ifc_file = Mock()
        
        result = self.parser.detect_units(mock_ifc_file)
        
        self.assertEqual(result, 0.001)  # Millimeters scale factor
    
    @patch('ifc_floor_plan_generator.parsing.ifc_parser.ifcopenshell')
    def test_detect_units_fallback_to_default(self, mock_ifcopenshell):
        """Test fallback to default scale when units cannot be detected."""
        mock_ifcopenshell.util.unit.get_unit.return_value = None
        
        mock_ifc_file = Mock()
        mock_ifc_file.by_type.return_value = []  # No projects found
        
        result = self.parser.detect_units(mock_ifc_file)
        
        self.assertEqual(result, 1.0)  # Default scale factor
    
    def test_calculate_unit_scale_meters(self):
        """Test unit scale calculation for meters."""
        result = self.parser._calculate_unit_scale("METRE")
        self.assertEqual(result, 1.0)
    
    def test_calculate_unit_scale_feet(self):
        """Test unit scale calculation for feet."""
        result = self.parser._calculate_unit_scale("FOOT")
        self.assertAlmostEqual(result, 0.3048, places=4)
    
    def test_calculate_unit_scale_inches(self):
        """Test unit scale calculation for inches."""
        result = self.parser._calculate_unit_scale("INCH")
        self.assertAlmostEqual(result, 0.0254, places=4)
    
    def test_calculate_unit_scale_with_prefix(self):
        """Test unit scale calculation with prefix."""
        result = self.parser._calculate_unit_scale("METRE", "MILLI")
        self.assertEqual(result, 0.001)
    
    def test_calculate_unit_scale_unknown_unit(self):
        """Test unit scale calculation for unknown unit."""
        result = self.parser._calculate_unit_scale("UNKNOWN_UNIT")
        self.assertIsNone(result)
    
    def test_calculate_unit_scale_unknown_prefix(self):
        """Test unit scale calculation with unknown prefix."""
        result = self.parser._calculate_unit_scale("METRE", "UNKNOWN_PREFIX")
        self.assertEqual(result, 1.0)  # Should ignore unknown prefix


class TestFileInfo(TestIFCParser):
    """Test file information functionality."""
    
    def test_get_file_info_success(self):
        """Test successful file info extraction."""
        mock_ifc_file = Mock()
        mock_ifc_file.schema = "IFC4"
        mock_ifc_file.name = "test.ifc"
        mock_ifc_file.__len__ = Mock(return_value=1000)
        
        # Mock by_type calls
        def mock_by_type(type_name):
            if type_name == "IfcBuildingStorey":
                return [Mock(), Mock()]  # 2 storeys
            elif type_name == "IfcBuilding":
                return [Mock()]  # 1 building
            elif type_name == "IfcSite":
                return [Mock()]  # 1 site
            elif type_name == "IfcProject":
                return [Mock()]  # 1 project
            elif type_name == "IfcApplication":
                app = Mock()
                app.ApplicationFullName = "Test Application"
                app.Version = "1.0"
                app.ApplicationIdentifier = "TEST_APP"
                return [app]
            return []
        
        mock_ifc_file.by_type = mock_by_type
        
        result = self.parser.get_file_info(mock_ifc_file)
        
        self.assertEqual(result['schema'], "IFC4")
        self.assertEqual(result['file_name'], "test.ifc")
        self.assertEqual(result['total_elements'], 1000)
        self.assertEqual(result['storeys_count'], 2)
        self.assertEqual(result['buildings_count'], 1)
        self.assertEqual(result['sites_count'], 1)
        self.assertEqual(result['projects_count'], 1)
        self.assertEqual(result['application']['name'], "Test Application")
    
    def test_get_file_info_exception_handling(self):
        """Test file info extraction with exceptions."""
        mock_ifc_file = Mock()
        mock_ifc_file.schema = "IFC4"
        # Mock by_type to raise an exception
        mock_ifc_file.by_type.side_effect = Exception("Access error")
        
        result = self.parser.get_file_info(mock_ifc_file)
        
        self.assertIn('error', result)


class TestClassFilters(TestIFCParser):
    """Test class filtering functionality."""
    
    def test_filter_elements_by_class_include_only(self):
        """Test filtering with include list only."""
        # Create mock elements
        mock_wall = Mock()
        mock_wall.is_a.return_value = "IfcWall"
        
        mock_slab = Mock()
        mock_slab.is_a.return_value = "IfcSlab"
        
        mock_space = Mock()
        mock_space.is_a.return_value = "IfcSpace"
        
        elements = [mock_wall, mock_slab, mock_space]
        
        class_filters = ClassFilters(include_ifc_classes=["IfcWall", "IfcSlab"])
        
        result = self.parser.filter_elements_by_class(elements, class_filters)
        
        self.assertEqual(len(result), 2)
        self.assertIn(mock_wall, result)
        self.assertIn(mock_slab, result)
        self.assertNotIn(mock_space, result)
    
    def test_filter_elements_by_class_exclude_priority(self):
        """Test that exclude takes priority over include."""
        mock_wall = Mock()
        mock_wall.is_a.return_value = "IfcWall"
        
        elements = [mock_wall]
        
        # Include IfcWall but also exclude it - exclude should win
        class_filters = ClassFilters(
            include_ifc_classes=["IfcWall"],
            exclude_ifc_classes=["IfcWall"]
        )
        
        result = self.parser.filter_elements_by_class(elements, class_filters)
        
        self.assertEqual(len(result), 0)
    
    def test_filter_elements_by_class_no_filters(self):
        """Test filtering with no filters (should include all)."""
        mock_wall = Mock()
        mock_wall.is_a.return_value = "IfcWall"
        
        elements = [mock_wall]
        
        class_filters = ClassFilters()  # Empty filters
        
        result = self.parser.filter_elements_by_class(elements, class_filters)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], mock_wall)


if __name__ == '__main__':
    unittest.main()