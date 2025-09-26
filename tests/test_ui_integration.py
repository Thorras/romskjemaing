"""
Integration Tests for PyQt UI Components

Tests the integration between UI components and IFC data processing.
"""

import pytest
import sys
import os
from unittest.mock import Mock, MagicMock, patch
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ifc_room_schedule.ui.main_window import MainWindow
from ifc_room_schedule.ui.space_list_widget import SpaceListWidget
from ifc_room_schedule.ui.space_detail_widget import SpaceDetailWidget
from ifc_room_schedule.data.space_model import SpaceData


@pytest.fixture(scope="session")
def qapp():
    """Create QApplication instance for testing."""
    if not QApplication.instance():
        app = QApplication([])
    else:
        app = QApplication.instance()
    yield app
    app.quit()


@pytest.fixture
def sample_spaces():
    """Create sample space data for testing."""
    spaces = [
        SpaceData(
            guid="SPACE001",
            name="101",
            long_name="Office 101",
            description="Main office space",
            object_type="Office",
            zone_category="Office",
            number="101",
            elevation=0.0,
            quantities={"Height": 3.0, "Area": 25.5}
        ),
        SpaceData(
            guid="SPACE002",
            name="102",
            long_name="Meeting Room 102",
            description="Conference room",
            object_type="Meeting Room",
            zone_category="Meeting Room",
            number="102",
            elevation=0.0,
            quantities={"Height": 3.2, "Area": 18.0}
        ),
        SpaceData(
            guid="SPACE003",
            name="Corridor",
            long_name="Main Corridor",
            description="Main hallway",
            object_type="Corridor",
            zone_category="Corridor",
            number="C01",
            elevation=0.0,
            quantities={"Height": 2.8, "Area": 45.0}
        )
    ]
    return spaces


class TestMainWindow:
    """Test cases for MainWindow integration."""

    def test_main_window_initialization(self, qapp):
        """Test main window initialization."""
        window = MainWindow()
        
        assert window.windowTitle() == "IFC Room Schedule"
        assert window.ifc_reader is not None
        assert window.space_extractor is not None
        assert window.current_file_path is None
        assert window.spaces == []
        
        # Check UI components exist
        assert window.space_list_widget is not None
        assert window.space_detail_widget is not None
        assert window.main_splitter is not None
        
        # Show window to make visibility checks work properly
        window.show()
        qapp.processEvents()
        
        # Check initial state
        assert not window.main_splitter.isVisible()
        assert window.welcome_label.isVisible()

    def test_file_loading_ui_updates(self, qapp):
        """Test UI updates during file loading process."""
        window = MainWindow()
        
        # Mock successful file loading
        with patch.object(window.ifc_reader, 'validate_file', return_value=(True, "Valid file")):
            with patch.object(window.ifc_reader, 'load_file', return_value=(True, "File loaded")):
                with patch.object(window, 'extract_spaces') as mock_extract:
                    
                    # Simulate file loading
                    window.process_ifc_file("/fake/path/test.ifc")
                    
                    # Check that extract_spaces was called
                    mock_extract.assert_called_once()
                    
                    # Check file path is set
                    assert window.current_file_path == "/fake/path/test.ifc"

    def test_space_extraction_and_ui_update(self, qapp, sample_spaces):
        """Test space extraction and UI updates."""
        window = MainWindow()
        window.show()
        qapp.processEvents()
        
        # Mock the space extractor
        with patch.object(window.space_extractor, 'extract_spaces', return_value=sample_spaces):
            with patch.object(window.ifc_reader, 'get_ifc_file', return_value=Mock()):
                
                # Extract spaces
                window.extract_spaces()
                
                # Check spaces are loaded
                assert len(window.spaces) == 3
                assert window.main_splitter.isVisible()
                assert not window.welcome_label.isVisible()

    def test_space_selection_integration(self, qapp, sample_spaces):
        """Test space selection between list and detail widgets."""
        window = MainWindow()
        window.spaces = sample_spaces
        
        # Load spaces into list widget
        window.space_list_widget.load_spaces(sample_spaces)
        
        # Simulate space selection
        window.on_space_selected("SPACE001")
        
        # Check that space detail widget is updated
        current_space = window.space_detail_widget.get_current_space()
        assert current_space is not None
        assert current_space.guid == "SPACE001"
        assert current_space.name == "101"

    def test_file_close_clears_ui(self, qapp, sample_spaces):
        """Test that closing file clears UI properly."""
        window = MainWindow()
        window.spaces = sample_spaces
        window.current_file_path = "/fake/path/test.ifc"
        
        # Load spaces
        window.space_list_widget.load_spaces(sample_spaces)
        window.space_detail_widget.display_space(sample_spaces[0])
        
        # Mock file reader
        with patch.object(window.ifc_reader, 'is_loaded', return_value=True):
            with patch.object(window.ifc_reader, 'close_file'):
                
                # Close file
                window.close_file()
                
                # Check UI is cleared
                assert window.current_file_path is None
                assert window.spaces == []
                assert window.space_list_widget.get_space_count() == 0
                assert window.space_detail_widget.get_current_space() is None


class TestSpaceListWidget:
    """Test cases for SpaceListWidget."""

    def test_space_list_initialization(self, qapp):
        """Test space list widget initialization."""
        widget = SpaceListWidget()
        
        assert widget.spaces == []
        assert widget.current_space_guid is None
        assert widget.space_list is not None
        assert widget.search_input is not None

    def test_load_spaces(self, qapp, sample_spaces):
        """Test loading spaces into the list widget."""
        widget = SpaceListWidget()
        
        # Load spaces
        widget.load_spaces(sample_spaces)
        
        assert len(widget.spaces) == 3
        assert widget.space_list.count() == 3  # Should have 3 space items
        assert widget.refresh_button.isEnabled()

    def test_space_filtering(self, qapp, sample_spaces):
        """Test space filtering functionality."""
        widget = SpaceListWidget()
        widget.load_spaces(sample_spaces)
        
        # Filter by "office"
        widget.filter_spaces("office")
        
        # Should show office and meeting room (both contain office-related terms)
        # Plus potentially a filter info item
        assert widget.space_list.count() >= 1

    def test_space_selection(self, qapp, sample_spaces):
        """Test space selection functionality."""
        widget = SpaceListWidget()
        widget.load_spaces(sample_spaces)
        
        # Select first space
        success = widget.select_space_by_index(0)
        
        assert success
        assert widget.current_space_guid == sample_spaces[0].guid
        assert widget.clear_button.isEnabled()

    def test_space_selection_signal(self, qapp, sample_spaces):
        """Test space selection signal emission."""
        widget = SpaceListWidget()
        widget.load_spaces(sample_spaces)
        
        # Connect signal to mock
        signal_received = []
        widget.space_selected.connect(lambda guid: signal_received.append(guid))
        
        # Select space
        widget.select_space(sample_spaces[0].guid)
        
        assert len(signal_received) == 1
        assert signal_received[0] == sample_spaces[0].guid


class TestSpaceDetailWidget:
    """Test cases for SpaceDetailWidget."""

    def test_space_detail_initialization(self, qapp):
        """Test space detail widget initialization."""
        widget = SpaceDetailWidget()
        
        assert widget.current_space is None
        assert widget.tab_widget is not None
        assert not widget.isEnabled()  # Should be disabled initially

    def test_display_space(self, qapp, sample_spaces):
        """Test displaying space details."""
        widget = SpaceDetailWidget()
        
        # Display first space
        widget.display_space(sample_spaces[0])
        
        assert widget.current_space == sample_spaces[0]
        assert widget.isEnabled()
        assert "Space Details: 101" in widget.title_label.text()

    def test_properties_tab_update(self, qapp, sample_spaces):
        """Test properties tab updates with space data."""
        widget = SpaceDetailWidget()
        widget.display_space(sample_spaces[0])
        
        # Check basic properties are displayed
        properties_text = widget.basic_properties_label.text()
        assert "SPACE001" in properties_text
        assert "101" in properties_text
        assert "Office 101" in properties_text

    def test_quantities_table_update(self, qapp, sample_spaces):
        """Test quantities table updates with space data."""
        widget = SpaceDetailWidget()
        widget.display_space(sample_spaces[0])
        
        # Check quantities table
        assert widget.quantities_table.rowCount() == 2  # Height and Area
        
        # Check table content
        height_found = False
        area_found = False
        
        for row in range(widget.quantities_table.rowCount()):
            name_item = widget.quantities_table.item(row, 0)
            value_item = widget.quantities_table.item(row, 1)
            
            if name_item and name_item.text() == "Height":
                height_found = True
                assert value_item.text() == "3.0"
            elif name_item and name_item.text() == "Area":
                area_found = True
                assert value_item.text() == "25.5"
        
        assert height_found and area_found

    def test_clear_selection(self, qapp, sample_spaces):
        """Test clearing space selection."""
        widget = SpaceDetailWidget()
        
        # Display space then clear
        widget.display_space(sample_spaces[0])
        widget.clear_selection()
        
        assert widget.current_space is None
        assert not widget.isEnabled()
        assert widget.quantities_table.rowCount() == 0


class TestUIIntegration:
    """Test cases for overall UI integration."""

    def test_complete_workflow(self, qapp, sample_spaces):
        """Test complete workflow from file loading to space selection."""
        window = MainWindow()
        window.show()
        qapp.processEvents()
        
        # Mock file operations
        with patch.object(window.ifc_reader, 'validate_file', return_value=(True, "Valid")):
            with patch.object(window.ifc_reader, 'load_file', return_value=(True, "Loaded")):
                with patch.object(window.space_extractor, 'extract_spaces', return_value=sample_spaces):
                    with patch.object(window.ifc_reader, 'get_ifc_file', return_value=Mock()):
                        
                        # Simulate file loading
                        window.process_ifc_file("/fake/test.ifc")
                        
                        # Check file is loaded and spaces extracted
                        assert len(window.spaces) == 3
                        assert window.main_splitter.isVisible()
                        
                        # Simulate space selection
                        window.on_space_selected("SPACE001")
                        
                        # Check space is displayed in detail widget
                        current_space = window.space_detail_widget.get_current_space()
                        assert current_space.guid == "SPACE001"

    def test_error_handling_in_ui(self, qapp):
        """Test error handling in UI components."""
        window = MainWindow()
        
        # Mock file validation failure
        with patch.object(window.ifc_reader, 'validate_file', return_value=(False, "Invalid file")):
            with patch.object(window, 'show_error_message') as mock_error:
                
                # Try to process invalid file
                window.process_ifc_file("/fake/invalid.ifc")
                
                # Check error message is shown
                mock_error.assert_called_once()
                assert "File Validation Error" in mock_error.call_args[0][0]

    def test_signal_connections(self, qapp):
        """Test that signals are properly connected."""
        window = MainWindow()
        
        # Check that signals are connected by verifying signal emission doesn't cause errors
        try:
            window.space_list_widget.space_selected.emit("TEST_GUID")
            window.space_list_widget.spaces_loaded.emit(5)
            window.space_detail_widget.surface_selected.emit("TEST_SURFACE")
            window.space_detail_widget.boundary_selected.emit("TEST_BOUNDARY")
        except Exception as e:
            pytest.fail(f"Signal connection failed: {e}")


if __name__ == "__main__":
    pytest.main([__file__])