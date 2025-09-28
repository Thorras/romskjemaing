"""
Unit tests for IFC File Reader functionality.
"""

import pytest
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock

from ifc_room_schedule.parser.ifc_file_reader import IfcFileReader


class TestIfcFileReader:
    """Test cases for IfcFileReader class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.reader = IfcFileReader()
    
    def test_init(self):
        """Test IfcFileReader initialization."""
        assert self.reader.ifc_file is None
        assert self.reader.file_path is None
        assert not self.reader.is_loaded()
    
    def test_validate_file_nonexistent(self):
        """Test validation of non-existent file."""
        is_valid, message = self.reader.validate_file("nonexistent.ifc")
        assert not is_valid
        assert "does not exist" in message.lower()
    
    def test_validate_file_wrong_extension(self):
        """Test validation of file with wrong extension."""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
            tmp.write(b"test content")
            tmp_path = tmp.name
        
        try:
            is_valid, message = self.reader.validate_file(tmp_path)
            assert not is_valid
            assert "not an ifc file" in message.lower()
        finally:
            os.unlink(tmp_path)
    
    @patch('ifcopenshell.open')
    def test_validate_file_valid_ifc(self, mock_open):
        """Test validation of valid IFC file."""
        # Mock IfcOpenShell file object
        mock_file = Mock()
        mock_file.schema = 'IFC4'
        mock_file.by_type.return_value = [Mock()]  # Mock IfcSpace entities
        mock_open.return_value = mock_file
        
        with tempfile.NamedTemporaryFile(suffix=".ifc", delete=False) as tmp:
            tmp.write(b"ISO-10303-21;")
            tmp_path = tmp.name
        
        try:
            is_valid, message = self.reader.validate_file(tmp_path)
            assert is_valid
            assert "valid ifc file" in message.lower()
            assert "IFC4" in message
        finally:
            os.unlink(tmp_path)
    
    @patch('ifcopenshell.open')
    def test_validate_file_no_spaces(self, mock_open):
        """Test validation of IFC file with no spaces."""
        mock_file = Mock()
        mock_file.schema = 'IFC4'
        mock_file.by_type.return_value = []  # No IfcSpace entities
        mock_open.return_value = mock_file
        
        with tempfile.NamedTemporaryFile(suffix=".ifc", delete=False) as tmp:
            tmp.write(b"ISO-10303-21;")
            tmp_path = tmp.name
        
        try:
            is_valid, message = self.reader.validate_file(tmp_path)
            assert not is_valid
            assert "no ifcspace entities" in message.lower()
        finally:
            os.unlink(tmp_path)
    
    @patch('ifcopenshell.open')
    def test_validate_file_unsupported_schema(self, mock_open):
        """Test validation of IFC file with unsupported schema."""
        mock_file = Mock()
        mock_file.schema = 'IFC2X2'  # Unsupported schema
        mock_open.return_value = mock_file
        
        with tempfile.NamedTemporaryFile(suffix=".ifc", delete=False) as tmp:
            tmp.write(b"ISO-10303-21;")
            tmp_path = tmp.name
        
        try:
            is_valid, message = self.reader.validate_file(tmp_path)
            assert not is_valid
            assert "unsupported ifc schema" in message.lower()
        finally:
            os.unlink(tmp_path)
    
    def test_load_file_nonexistent(self):
        """Test loading non-existent file."""
        success, message = self.reader.load_file("nonexistent.ifc")
        assert not success
        assert "not found" in message.lower()
        assert not self.reader.is_loaded()
    
    def test_load_file_wrong_extension(self):
        """Test loading file with wrong extension."""
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
            tmp.write(b"test content")
            tmp_path = tmp.name
        
        try:
            success, message = self.reader.load_file(tmp_path)
            assert not success
            assert "invalid file format" in message.lower()
            assert not self.reader.is_loaded()
        finally:
            os.unlink(tmp_path)
    
    @patch('os.path.getsize')
    def test_load_file_too_large(self, mock_getsize):
        """Test loading very large file."""
        mock_getsize.return_value = 250 * 1024 * 1024  # 250MB - above the 200MB threshold
        
        with tempfile.NamedTemporaryFile(suffix=".ifc", delete=False) as tmp:
            tmp.write(b"ISO-10303-21;")
            tmp_path = tmp.name
        
        try:
            success, message = self.reader.load_file(tmp_path)
            assert not success
            assert "very large" in message.lower()
            assert not self.reader.is_loaded()
        finally:
            os.unlink(tmp_path)
    
    @patch('ifcopenshell.open')
    def test_load_file_success(self, mock_open):
        """Test successful file loading."""
        # Mock IfcOpenShell file object
        mock_file = Mock()
        mock_file.by_type.side_effect = lambda entity_type: {
            "IfcProduct": [Mock(), Mock()],
            "IfcSpace": [Mock(), Mock(), Mock()]
        }.get(entity_type, [])
        mock_open.return_value = mock_file
        
        with tempfile.NamedTemporaryFile(suffix=".ifc", delete=False) as tmp:
            tmp.write(b"ISO-10303-21;")
            tmp_path = tmp.name
        
        try:
            success, message = self.reader.load_file(tmp_path)
            assert success
            assert "successfully loaded" in message.lower()
            assert "3 spaces" in message
            assert self.reader.is_loaded()
            assert self.reader.file_path == tmp_path
            assert self.reader.get_ifc_file() == mock_file
        finally:
            os.unlink(tmp_path)
    
    @patch('ifcopenshell.open')
    def test_load_file_empty(self, mock_open):
        """Test loading empty IFC file."""
        mock_file = Mock()
        mock_file.by_type.return_value = []  # No entities
        mock_open.return_value = mock_file
        
        with tempfile.NamedTemporaryFile(suffix=".ifc", delete=False) as tmp:
            tmp.write(b"ISO-10303-21;")
            tmp_path = tmp.name
        
        try:
            success, message = self.reader.load_file(tmp_path)
            assert not success
            assert "empty" in message.lower()
            assert not self.reader.is_loaded()
        finally:
            os.unlink(tmp_path)
    
    @patch('ifcopenshell.open')
    def test_load_file_no_spaces(self, mock_open):
        """Test loading IFC file with no spaces."""
        mock_file = Mock()
        mock_file.by_type.side_effect = lambda entity_type: {
            "IfcProduct": [Mock(), Mock()],
            "IfcSpace": []
        }.get(entity_type, [])
        mock_open.return_value = mock_file
        
        with tempfile.NamedTemporaryFile(suffix=".ifc", delete=False) as tmp:
            tmp.write(b"ISO-10303-21;")
            tmp_path = tmp.name
        
        try:
            success, message = self.reader.load_file(tmp_path)
            assert not success
            assert "no ifcspace entities" in message.lower()
            assert not self.reader.is_loaded()
        finally:
            os.unlink(tmp_path)
    
    @patch('ifcopenshell.open')
    def test_get_file_info_success(self, mock_open):
        """Test getting file information."""
        # Mock IfcOpenShell file object with detailed info
        mock_file = Mock()
        mock_file.schema = 'IFC4'
        mock_file.__len__ = Mock(return_value=1000)
        mock_file.by_type.side_effect = lambda entity_type: {
            "IfcProduct": [Mock() for _ in range(10)],  # Need this for load_file to succeed
            "IfcSpace": [Mock(), Mock()],
            "IfcBuildingElement": [Mock() for _ in range(50)],
            "IfcProject": [Mock(Name="Test Project", Description="Test Description")],
            "IfcApplication": [Mock(ApplicationFullName="Test App", Version="1.0")]
        }.get(entity_type, [])
        mock_open.return_value = mock_file
        
        with tempfile.NamedTemporaryFile(suffix=".ifc", delete=False) as tmp:
            tmp.write(b"ISO-10303-21;")
            tmp_path = tmp.name
        
        try:
            # Load file first
            self.reader.load_file(tmp_path)
            
            info = self.reader.get_file_info()
            assert info is not None
            assert info['schema'] == 'IFC4'
            assert info['spaces_count'] == 2
            assert info['total_entities'] == 1000
            assert info['building_elements'] == 50
            assert info['project_name'] == "Test Project"
            assert info['created_by'] == "Test App"
        finally:
            os.unlink(tmp_path)
    
    def test_get_file_info_no_file(self):
        """Test getting file info when no file is loaded."""
        info = self.reader.get_file_info()
        assert info is None
    
    def test_close_file(self):
        """Test closing loaded file."""
        # Mock a loaded state
        self.reader.ifc_file = Mock()
        self.reader.file_path = "test.ifc"
        
        assert self.reader.is_loaded()
        
        self.reader.close_file()
        
        assert not self.reader.is_loaded()
        assert self.reader.ifc_file is None
        assert self.reader.file_path is None
    
    @patch('ifcopenshell.open')
    def test_load_file_exception_handling(self, mock_open):
        """Test exception handling during file loading."""
        mock_open.side_effect = Exception("Test exception")
        
        with tempfile.NamedTemporaryFile(suffix=".ifc", delete=False) as tmp:
            tmp.write(b"ISO-10303-21;")
            tmp_path = tmp.name
        
        try:
            success, message = self.reader.load_file(tmp_path)
            assert not success
            assert "error loading ifc file" in message.lower()
            assert "Test exception" in message
            assert not self.reader.is_loaded()
        finally:
            os.unlink(tmp_path)


if __name__ == "__main__":
    pytest.main([__file__])