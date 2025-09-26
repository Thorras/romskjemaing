"""
Integration Tests for Enhanced MainWindow UI Components

Tests the enhanced UI functionality including navigation, validation, and improved styling.
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


class TestEnhancedMainWindow:
    """Test cases for enhanced MainWindow functionality."""

    def test_enhanced_ui_initialization(self, qapp):
        """Test enhanced UI initialization."""
        window = MainWindow()
        
        # Check enhanced UI components exist
        assert window.toolbar_status_label is not None
        assert window.next_space_action is not None
        assert window.prev_space_action is not None
        assert window.goto_space_action is not None
        assert window.validate_action is not None
        
        # Check initial state of new actions
        assert not window.next_space_action.isEnabled()
        assert not window.prev_space_action.isEnabled()
        assert not window.goto_space_action.isEnabled()
        assert not window.validate_action.isEnabled()

    def test_navigation_functionality(self, qapp, sample_spaces):
        """Test space navigation functionality."""
        window = MainWindow()
        window.spaces = sample_spaces
        window.space_list_widget.load_spaces(sample_spaces)
        window.update_ui_state(True)
        
        # Test next space navigation
        window.navigate_next_space()
        selected_space = window.space_list_widget.get_selected_space()
        assert selected_space is not None
        assert selected_space.guid == sample_spaces[0].guid
        
        # Navigate to next
        window.navigate_next_space()
        selected_space = window.space_list_widget.get_selected_space()
        assert selected_space.guid == sample_spaces[1].guid
        
        # Test previous space navigation
        window.navigate_previous_space()
        selected_space = window.space_list_widget.get_selected_space()
        assert selected_space.guid == sample_spaces[0].guid

    def test_goto_space_dialog(self, qapp, sample_spaces):
        """Test go to space dialog functionality."""
        window = MainWindow()
        window.spaces = sample_spaces
        window.space_list_widget.load_spaces(sample_spaces)
        
        # Mock the input dialog
        with patch('PyQt6.QtWidgets.QInputDialog.getItem') as mock_dialog:
            mock_dialog.return_value = ("102", True)  # Use just the number since name == number
            
            window.show_goto_space_dialog()
            
            # Check that dialog was called
            mock_dialog.assert_called_once()
            
            # Check that correct space is selected
            selected_space = window.space_list_widget.get_selected_space()
            assert selected_space.guid == sample_spaces[1].guid

    def test_data_validation(self, qapp, sample_spaces):
        """Test data validation functionality."""
        window = MainWindow()
        window.spaces = sample_spaces
        
        # Mock the info message dialog
        with patch.object(window, 'show_info_message') as mock_info:
            window.validate_data()
            
            # Check that validation dialog was shown
            mock_info.assert_called_once()
            assert "Data Validation Results" in mock_info.call_args[0][0]

    def test_enhanced_file_info_display(self, qapp):
        """Test enhanced file information display."""
        window = MainWindow()
        
        # Test with no file loaded
        window.update_file_info()
        assert "Welcome to IFC Room Schedule" in window.welcome_label.text()
        assert not window.main_splitter.isVisible()
        
        # Test with file loaded
        window.current_file_path = "/fake/path/test.ifc"
        with patch.object(window.ifc_reader, 'is_loaded', return_value=True):
            with patch.object(window, 'get_file_size_string', return_value="1.2 MB"):
                window.update_file_info()
                assert "📄 test.ifc (1.2 MB)" in window.file_label.text()

    def test_toolbar_status_updates(self, qapp, sample_spaces):
        """Test toolbar status label updates."""
        window = MainWindow()
        
        # Test initial state
        window.update_ui_state(False)
        assert window.toolbar_status_label.text() == "Ready"
        
        # Test with file loaded but no spaces
        window.spaces = []
        window.update_ui_state(True)
        assert "File loaded, no spaces found" in window.toolbar_status_label.text()
        
        # Test with spaces loaded
        window.spaces = sample_spaces
        window.update_ui_state(True)
        assert "3 spaces loaded" in window.toolbar_status_label.text()

    def test_user_guide_display(self, qapp):
        """Test user guide display."""
        window = MainWindow()
        
        with patch('PyQt6.QtWidgets.QMessageBox.exec') as mock_exec:
            window.show_user_guide()
            mock_exec.assert_called_once()

    def test_enhanced_menu_structure(self, qapp):
        """Test enhanced menu structure."""
        window = MainWindow()
        menubar = window.menuBar()
        
        # Check that all expected menus exist
        menu_titles = [action.text() for action in menubar.actions()]
        assert "&File" in menu_titles
        assert "&View" in menu_titles
        assert "&Navigate" in menu_titles
        assert "&Tools" in menu_titles
        assert "&Help" in menu_titles

    def test_keyboard_shortcuts(self, qapp, sample_spaces):
        """Test keyboard shortcuts functionality."""
        window = MainWindow()
        window.spaces = sample_spaces
        window.space_list_widget.load_spaces(sample_spaces)
        window.update_ui_state(True)
        
        # Test navigation shortcuts
        # Select first space
        window.space_list_widget.select_space_by_index(0)
        
        # Simulate Ctrl+Right (next space)
        QTest.keySequence(window, "Ctrl+Right")
        # Note: In a real test, we'd need to check if the action was triggered
        # For now, we just verify the action exists and is enabled
        assert window.next_space_action.isEnabled()
        
        # Simulate Ctrl+Left (previous space)
        QTest.keySequence(window, "Ctrl+Left")
        assert window.prev_space_action.isEnabled()


class TestEnhancedSpaceListWidget:
    """Test cases for enhanced SpaceListWidget functionality."""

    def test_enhanced_styling_initialization(self, qapp):
        """Test enhanced styling initialization."""
        from ifc_room_schedule.ui.space_list_widget import SpaceListWidget
        
        widget = SpaceListWidget()
        
        # Check that enhanced UI components exist
        assert widget.clear_search_button is not None
        assert widget.count_label is not None
        assert not widget.clear_search_button.isVisible()  # Initially hidden

    def test_search_functionality_enhanced(self, qapp, sample_spaces):
        """Test enhanced search functionality."""
        from ifc_room_schedule.ui.space_list_widget import SpaceListWidget
        
        widget = SpaceListWidget()
        widget.show()
        qapp.processEvents()
        widget.load_spaces(sample_spaces)
        
        # Test search with results
        widget.filter_spaces("office")
        assert widget.clear_search_button.isVisible()
        
        # Test clear search
        widget.clear_search()
        assert widget.search_input.text() == ""
        assert not widget.clear_search_button.isVisible()

    def test_space_type_icons(self, qapp):
        """Test space type icon functionality."""
        from ifc_room_schedule.ui.space_list_widget import SpaceListWidget
        
        widget = SpaceListWidget()
        
        # Test various space type icons
        assert widget.get_space_type_icon("Office") == "🏢"
        assert widget.get_space_type_icon("Meeting Room") == "🤝"
        assert widget.get_space_type_icon("Corridor") == "🚶"
        assert widget.get_space_type_icon("Unknown Type") == "🏠"  # Default

    def test_count_label_updates(self, qapp, sample_spaces):
        """Test count label updates."""
        from ifc_room_schedule.ui.space_list_widget import SpaceListWidget
        
        widget = SpaceListWidget()
        
        # Test with no spaces
        widget.update_count_label(0)
        assert "0 spaces" in widget.count_label.text()
        
        # Test with spaces
        widget.update_count_label(3)
        assert "3 spaces" in widget.count_label.text()
        
        # Test with filtered results
        widget.update_count_label(3, 1)
        assert "Showing 1 of 3 spaces" in widget.count_label.text()

    def test_enhanced_space_info_display(self, qapp, sample_spaces):
        """Test enhanced space information display."""
        from ifc_room_schedule.ui.space_list_widget import SpaceListWidget
        
        widget = SpaceListWidget()
        widget.update_space_info(sample_spaces[0])
        
        info_text = widget.info_label.text()
        assert "🏢" in info_text  # Office icon
        assert "101" in info_text
        assert "Office 101" in info_text
        assert "Height: 3.00" in info_text
        assert "Area: 25.50" in info_text


if __name__ == "__main__":
    pytest.main([__file__])