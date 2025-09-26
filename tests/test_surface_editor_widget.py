"""
Tests for SurfaceEditorWidget

Tests the surface and boundary description editor functionality.
"""

import pytest
import sys
from unittest.mock import Mock, patch
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest

from ifc_room_schedule.ui.surface_editor_widget import SurfaceEditorWidget


@pytest.fixture(scope="module")
def qapp():
    """Create QApplication instance for testing."""
    if not QApplication.instance():
        app = QApplication(sys.argv)
    else:
        app = QApplication.instance()
    yield app


@pytest.fixture
def surface_editor(qapp):
    """Create SurfaceEditorWidget instance for testing."""
    widget = SurfaceEditorWidget()
    return widget


class TestSurfaceEditorWidget:
    """Test cases for SurfaceEditorWidget."""
    
    def test_widget_initialization(self, surface_editor):
        """Test that the widget initializes correctly."""
        assert surface_editor is not None
        assert surface_editor.current_surface_id is None
        assert surface_editor.current_boundary_guid is None
        assert surface_editor.current_space_guid is None
        assert len(surface_editor.surface_descriptions) == 0
        assert len(surface_editor.boundary_descriptions) == 0
        
    def test_empty_state(self, surface_editor):
        """Test the empty state display."""
        surface_editor.show_empty_state()
        
        assert surface_editor.current_surface_id is None
        assert surface_editor.current_boundary_guid is None
        assert not surface_editor.surface_description_edit.isEnabled()
        assert not surface_editor.boundary_description_edit.isEnabled()
        assert not surface_editor.clear_button.isEnabled()
        
    def test_surface_editing(self, surface_editor):
        """Test surface editing functionality."""
        surface_id = "test_surface_001"
        surface_data = {
            'type': 'Wall',
            'area': 25.5,
            'material': 'Concrete',
            'user_description': 'Test description'
        }
        
        # Start editing surface
        surface_editor.edit_surface(surface_id, surface_data)
        
        assert surface_editor.current_surface_id == surface_id
        assert surface_editor.current_boundary_guid is None
        assert surface_editor.surface_description_edit.isEnabled()
        assert surface_editor.tab_widget.currentIndex() == 0  # Surface tab
        
        # Check that surface info is displayed
        assert surface_editor.surface_type_label.text() == 'Wall'
        assert surface_editor.surface_area_label.text() == '25.50 m²'
        assert surface_editor.surface_material_label.text() == 'Concrete'
        assert surface_editor.surface_description_edit.toPlainText() == 'Test description'
        
    def test_boundary_editing(self, surface_editor):
        """Test boundary editing functionality."""
        boundary_guid = "test_boundary_001"
        boundary_data = {
            'display_label': 'North Wall to Office 101',
            'physical_or_virtual_boundary': 'Physical',
            'boundary_orientation': 'North',
            'calculated_area': 15.2,
            'related_building_element_type': 'IfcWall',
            'user_description': 'Thermal boundary'
        }
        
        # Start editing boundary
        surface_editor.edit_boundary(boundary_guid, boundary_data)
        
        assert surface_editor.current_boundary_guid == boundary_guid
        assert surface_editor.current_surface_id is None
        assert surface_editor.boundary_description_edit.isEnabled()
        assert surface_editor.tab_widget.currentIndex() == 1  # Boundary tab
        
        # Check that boundary info is displayed
        assert surface_editor.boundary_label_label.text() == 'North Wall to Office 101'
        assert surface_editor.boundary_type_label.text() == 'Physical'
        assert surface_editor.boundary_orientation_label.text() == 'North'
        assert surface_editor.boundary_area_label.text() == '15.20 m²'
        assert surface_editor.boundary_element_label.text() == 'IfcWall'
        assert surface_editor.boundary_description_edit.toPlainText() == 'Thermal boundary'
        
    def test_character_count_validation(self, surface_editor):
        """Test character count validation."""
        surface_id = "test_surface_001"
        surface_data = {
            'type': 'Wall',
            'area': 25.5,
            'material': 'Concrete',
            'user_description': ''
        }
        
        surface_editor.edit_surface(surface_id, surface_data)
        
        # Test normal text
        test_text = "This is a test description"
        surface_editor.surface_description_edit.setPlainText(test_text)
        surface_editor.update_surface_char_count()
        
        expected_count = f"{len(test_text)} / 1000 characters"
        assert surface_editor.surface_char_count_label.text() == expected_count
        
        # Test text at limit
        long_text = "x" * 1000
        surface_editor.surface_description_edit.setPlainText(long_text)
        surface_editor.update_surface_char_count()
        
        assert surface_editor.surface_char_count_label.text() == "1000 / 1000 characters"
        
    def test_description_persistence(self, surface_editor):
        """Test that descriptions are stored and retrieved correctly."""
        surface_id = "test_surface_001"
        description = "Persistent description"
        
        # Update description
        surface_editor.update_surface_description(surface_id, description)
        
        # Retrieve description
        retrieved = surface_editor.get_surface_description(surface_id)
        assert retrieved == description
        
        # Test boundary description persistence
        boundary_guid = "test_boundary_001"
        boundary_description = "Persistent boundary description"
        
        surface_editor.update_boundary_description(boundary_guid, boundary_description)
        retrieved_boundary = surface_editor.get_boundary_description(boundary_guid)
        assert retrieved_boundary == boundary_description
        
    def test_space_context(self, surface_editor):
        """Test space context setting."""
        space_guid = "test_space_001"
        surface_editor.set_space_context(space_guid)
        
        assert surface_editor.current_space_guid == space_guid
        
    def test_signal_emission(self, surface_editor):
        """Test that signals are emitted correctly."""
        # Mock signal connections
        surface_signal_mock = Mock()
        boundary_signal_mock = Mock()
        
        surface_editor.surface_description_changed.connect(surface_signal_mock)
        surface_editor.boundary_description_changed.connect(boundary_signal_mock)
        
        # Test surface description change signal
        surface_id = "test_surface_001"
        surface_data = {
            'type': 'Wall',
            'area': 25.5,
            'material': 'Concrete',
            'user_description': ''
        }
        
        surface_editor.edit_surface(surface_id, surface_data)
        
        # Simulate text change and auto-save
        surface_editor.surface_description_edit.setPlainText("New description")
        surface_editor.auto_save()
        
        # Check that signal was emitted
        surface_signal_mock.assert_called_once_with(surface_id, "New description")
        
    def test_clear_functionality(self, surface_editor):
        """Test the clear all descriptions functionality."""
        # Set up some data
        surface_id = "test_surface_001"
        surface_data = {
            'type': 'Wall',
            'area': 25.5,
            'material': 'Concrete',
            'user_description': 'Test description'
        }
        
        surface_editor.edit_surface(surface_id, surface_data)
        surface_editor.surface_description_edit.setPlainText("Some text")
        
        # Mock the message box to always return Yes
        with patch('PyQt6.QtWidgets.QMessageBox.question', return_value=16384):  # Yes button
            surface_editor.clear_all_descriptions()
            
        # Check that text is cleared
        assert surface_editor.surface_description_edit.toPlainText() == ""
        
    def test_tab_switching(self, surface_editor):
        """Test tab switching functionality."""
        # Start with surface editing
        surface_id = "test_surface_001"
        surface_data = {
            'type': 'Wall',
            'area': 25.5,
            'material': 'Concrete',
            'user_description': ''
        }
        
        surface_editor.edit_surface(surface_id, surface_data)
        assert surface_editor.tab_widget.currentIndex() == 0  # Surface tab
        
        # Switch to boundary editing
        boundary_guid = "test_boundary_001"
        boundary_data = {
            'display_label': 'North Wall',
            'physical_or_virtual_boundary': 'Physical',
            'boundary_orientation': 'North',
            'calculated_area': 15.2,
            'related_building_element_type': 'IfcWall',
            'user_description': ''
        }
        
        surface_editor.edit_boundary(boundary_guid, boundary_data)
        assert surface_editor.tab_widget.currentIndex() == 1  # Boundary tab
        
    def test_unsaved_changes_detection(self, surface_editor):
        """Test detection of unsaved changes."""
        # Initially no unsaved changes
        assert not surface_editor.has_unsaved_changes()
        
        # Start editing
        surface_id = "test_surface_001"
        surface_data = {
            'type': 'Wall',
            'area': 25.5,
            'material': 'Concrete',
            'user_description': ''
        }
        
        surface_editor.edit_surface(surface_id, surface_data)
        
        # Simulate text change
        surface_editor.surface_description_edit.setPlainText("New text")
        surface_editor.on_surface_text_changed()
        
        # Should have unsaved changes
        assert surface_editor.has_unsaved_changes()
        
        # Force save
        surface_editor.force_save()
        
        # Should no longer have unsaved changes
        assert not surface_editor.has_unsaved_changes()


if __name__ == "__main__":
    pytest.main([__file__])