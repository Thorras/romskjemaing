"""
Integration Tests for Export Functionality

Tests the complete export workflow from UI to file generation.
"""

import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest

from ifc_room_schedule.ui.export_dialog_widget import ExportDialogWidget, ExportWorker
from ifc_room_schedule.ui.main_window import MainWindow
from ifc_room_schedule.data.space_model import SpaceData
from ifc_room_schedule.data.surface_model import SurfaceData
from ifc_room_schedule.data.space_boundary_model import SpaceBoundaryData
from ifc_room_schedule.data.relationship_model import RelationshipData
from ifc_room_schedule.export.json_builder import JsonBuilder


@pytest.fixture
def app():
    """Create QApplication instance for testing."""
    if not QApplication.instance():
        return QApplication([])
    return QApplication.instance()


@pytest.fixture
def sample_spaces():
    """Create sample space data for testing."""
    # Create sample surfaces
    surface1 = SurfaceData(
        id="surface_1",
        type="Wall",
        area=25.5,
        material="Concrete",
        ifc_type="IfcWall",
        related_space_guid="space_1",
        user_description="North wall"
    )
    
    surface2 = SurfaceData(
        id="surface_2", 
        type="Floor",
        area=50.0,
        material="Concrete",
        ifc_type="IfcSlab",
        related_space_guid="space_1",
        user_description="Main floor"
    )
    
    # Create sample space boundary
    boundary1 = SpaceBoundaryData(
        id="boundary_1",
        guid="boundary_guid_1",
        name="North Wall Boundary",
        description="Boundary to exterior",
        physical_or_virtual_boundary="Physical",
        internal_or_external_boundary="External",
        related_building_element_guid="wall_guid_1",
        related_building_element_name="Exterior Wall",
        related_building_element_type="IfcWall",
        related_space_guid="space_1",
        boundary_surface_type="Wall",
        boundary_orientation="North",
        connection_geometry={},
        calculated_area=25.5,
        display_label="North Wall to Exterior"
    )
    
    # Create sample relationship
    relationship1 = RelationshipData(
        related_entity_guid="building_guid_1",
        related_entity_name="Main Building",
        related_entity_description="Primary building structure",
        relationship_type="Contains",
        ifc_relationship_type="IfcRelContainedInSpatialStructure"
    )
    
    # Create sample space
    space1 = SpaceData(
        guid="space_1",
        name="101",
        long_name="Office 101",
        description="Main office space",
        object_type="Office",
        zone_category="Work",
        number="101",
        elevation=0.0,
        quantities={"Height": 3.0, "Area": 50.0},
        processed=True
    )
    
    # Add data to space
    space1.add_surface(surface1)
    space1.add_surface(surface2)
    space1.add_space_boundary(boundary1)
    space1.add_relationship(relationship1)
    
    # Create second space with minimal data
    space2 = SpaceData(
        guid="space_2",
        name="102",
        long_name="Office 102",
        description="Secondary office space",
        object_type="Office",
        zone_category="Work",
        number="102",
        elevation=0.0,
        quantities={"Height": 3.0, "Area": 40.0},
        processed=False  # Not processed
    )
    
    return [space1, space2]


class TestExportDialogWidget:
    """Test cases for ExportDialogWidget."""
    
    def test_dialog_initialization(self, app, sample_spaces):
        """Test dialog initializes correctly with space data."""
        dialog = ExportDialogWidget(sample_spaces, "/test/file.ifc")
        
        assert dialog.spaces == sample_spaces
        assert dialog.source_file_path == "/test/file.ifc"
        assert dialog.windowTitle() == "Export Room Schedule Data"
        assert not dialog.export_button.isEnabled()  # No file selected initially
    
    def test_data_summary_display(self, app, sample_spaces):
        """Test data summary section displays correct statistics."""
        dialog = ExportDialogWidget(sample_spaces)
        
        # Check that summary information is displayed
        # The dialog should show 2 total spaces, 1 processed
        assert len(dialog.spaces) == 2
        processed_count = sum(1 for space in dialog.spaces if space.processed)
        assert processed_count == 1
    
    def test_export_options_defaults(self, app, sample_spaces):
        """Test export options have correct default values."""
        dialog = ExportDialogWidget(sample_spaces)
        
        assert dialog.indent_spinbox.value() == 2
        assert dialog.validate_checkbox.isChecked()
        assert dialog.include_metadata_checkbox.isChecked()
        assert dialog.include_summary_checkbox.isChecked()
    
    def test_file_selection_enables_export(self, app, sample_spaces):
        """Test that selecting a file enables the export button."""
        dialog = ExportDialogWidget(sample_spaces)
        
        # Initially disabled
        assert not dialog.export_button.isEnabled()
        
        # Set file path
        dialog.file_path_edit.setText("/test/export.json")
        
        # Should now be enabled
        assert dialog.export_button.isEnabled()
    
    def test_incomplete_data_warning(self, app, sample_spaces):
        """Test warning for incomplete data."""
        # Mock QMessageBox to capture the warning
        with patch('ifc_room_schedule.ui.export_dialog_widget.QMessageBox') as mock_msgbox:
            mock_msgbox.question.return_value = mock_msgbox.StandardButton.Yes
            
            dialog = ExportDialogWidget(sample_spaces)
            
            # Should have shown warning about unprocessed spaces
            mock_msgbox.question.assert_called_once()
            call_args = mock_msgbox.question.call_args[0]
            # Check for the actual message content - it's the 3rd argument (index 2)
            assert "spaces have not been fully processed" in call_args[2]
    
    def test_export_summary_generation(self, app, sample_spaces):
        """Test export summary generation."""
        dialog = ExportDialogWidget(sample_spaces)
        dialog.file_path_edit.setText("/test/export.json")
        dialog.indent_spinbox.setValue(4)
        dialog.validate_checkbox.setChecked(False)
        
        summary = dialog.get_export_summary()
        
        assert summary['total_spaces'] == 2
        assert summary['processed_spaces'] == 1
        assert summary['export_path'] == "/test/export.json"
        assert summary['options']['indent'] == 4
        assert summary['options']['validate'] is False


class TestExportWorker:
    """Test cases for ExportWorker."""
    
    def test_worker_initialization(self, sample_spaces):
        """Test worker initializes correctly."""
        export_options = {'indent': 2, 'validate': True}
        worker = ExportWorker(sample_spaces, "/test/export.json", export_options)
        
        assert worker.spaces == sample_spaces
        assert worker.export_path == "/test/export.json"
        assert worker.export_options == export_options
        assert isinstance(worker.json_builder, JsonBuilder)
    
    def test_file_size_formatting(self, sample_spaces):
        """Test file size formatting utility."""
        export_options = {}
        worker = ExportWorker(sample_spaces, "/test/export.json", export_options)
        
        assert worker._format_file_size(500) == "500 B"
        assert worker._format_file_size(1536) == "1.5 KB"
        assert worker._format_file_size(2097152) == "2.0 MB"


class TestExportIntegration:
    """Integration tests for complete export workflow."""
    
    def test_complete_export_workflow(self, app, sample_spaces):
        """Test complete export workflow from dialog to file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            export_path = os.path.join(temp_dir, "test_export.json")
            
            # Create dialog
            dialog = ExportDialogWidget(sample_spaces, "/test/source.ifc")
            dialog.file_path_edit.setText(export_path)
            
            # Prepare export options
            export_options = {
                'indent': 2,
                'validate': True,
                'include_metadata': True,
                'include_summary': True,
                'source_file': "/test/source.ifc"
            }
            
            # Create worker and run export
            worker = ExportWorker(sample_spaces, export_path, export_options)
            
            # Mock signals to capture progress
            progress_updates = []
            status_updates = []
            
            def capture_progress(value):
                progress_updates.append(value)
            
            def capture_status(status):
                status_updates.append(status)
            
            worker.progress_updated.connect(capture_progress)
            worker.status_updated.connect(capture_status)
            
            # Run export
            worker.run_export()
            
            # Verify file was created
            assert os.path.exists(export_path)
            
            # Verify file content
            with open(export_path, 'r', encoding='utf-8') as f:
                exported_data = json.load(f)
            
            # Verify structure
            assert 'metadata' in exported_data
            assert 'spaces' in exported_data
            assert 'summary' in exported_data
            
            # Verify metadata
            metadata = exported_data['metadata']
            assert 'export_date' in metadata
            assert 'application_version' in metadata
            assert metadata['source_file'] == "source.ifc"
            
            # Verify spaces
            spaces = exported_data['spaces']
            assert len(spaces) == 2
            
            # Verify first space
            space1 = spaces[0]
            assert space1['guid'] == "space_1"
            assert space1['properties']['name'] == "101"
            assert len(space1['surfaces']) == 2
            assert len(space1['space_boundaries']) == 1
            assert len(space1['relationships']) == 1
            
            # Verify summary
            summary = exported_data['summary']
            assert summary['total_spaces'] == 2
            assert summary['processed_spaces'] == 1
            assert 'total_surface_area' in summary
            assert 'boundary_counts' in summary
            
            # Verify progress updates were sent
            assert len(progress_updates) > 0
            assert len(status_updates) > 0
            assert 100 in progress_updates  # Final progress
    
    def test_export_validation_failure(self, app, sample_spaces):
        """Test export with validation failure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            export_path = os.path.join(temp_dir, "test_export.json")
            
            # Create space with valid GUID but create invalid JSON structure manually
            valid_space = SpaceData(
                guid="valid_guid",
                name="Valid",
                long_name="Valid Space",
                description="",
                object_type="",
                zone_category="",
                number="",
                elevation=0.0
            )
            
            export_options = {'validate': True}
            
            # Mock the json_builder to return invalid data
            worker = ExportWorker([valid_space], export_path, export_options)
            
            # Mock the validate_export_data method to return validation failure
            def mock_validate(data):
                return False, ["Test validation error"]
            
            worker.json_builder.validate_export_data = mock_validate
            
            # Capture completion signal
            completion_results = []
            
            def capture_completion(success, message):
                completion_results.append((success, message))
            
            worker.export_completed.connect(capture_completion)
            
            # Run export
            worker.run_export()
            
            # Should have failed validation
            assert len(completion_results) == 1
            success, message = completion_results[0]
            assert not success
            assert "validation failed" in message.lower()
    
    def test_main_window_export_integration(self, app, sample_spaces):
        """Test export integration with MainWindow."""
        # Create main window
        main_window = MainWindow()
        main_window.spaces = sample_spaces
        main_window.current_file_path = "/test/source.ifc"
        
        # Mock the export dialog to avoid actual UI interaction
        with patch('ifc_room_schedule.ui.main_window.ExportDialogWidget') as mock_dialog_class:
            mock_dialog = Mock()
            mock_dialog_class.return_value = mock_dialog
            
            # Call export_json
            main_window.export_json()
            
            # Verify dialog was created with correct parameters
            mock_dialog_class.assert_called_once_with(
                spaces=sample_spaces,
                source_file_path="/test/source.ifc",
                parent=main_window
            )
            
            # Verify dialog was shown
            mock_dialog.exec.assert_called_once()
    
    def test_main_window_export_no_data(self, app):
        """Test export from MainWindow with no data."""
        main_window = MainWindow()
        main_window.spaces = []
        
        # Mock QMessageBox to capture warning
        with patch('ifc_room_schedule.ui.main_window.QMessageBox') as mock_msgbox:
            main_window.export_json()
            
            # Should have shown warning
            mock_msgbox.warning.assert_called_once()
            call_args = mock_msgbox.warning.call_args[0]
            # Check for the actual message content
            assert "No space data available" in call_args[1] or "No Data" in call_args[1]
    
    def test_export_completion_handling(self, app):
        """Test export completion handling in MainWindow."""
        main_window = MainWindow()
        
        # Test successful completion
        main_window.on_export_completed(True, "Export successful")
        assert "Export completed" in main_window.status_bar.currentMessage()
        
        # Test failed completion
        main_window.on_export_completed(False, "Export failed")
        assert "Export failed" in main_window.status_bar.currentMessage()


class TestExportDataValidation:
    """Test cases for export data validation."""
    
    def test_json_structure_validation(self, sample_spaces):
        """Test JSON structure validation."""
        json_builder = JsonBuilder()
        json_data = json_builder.build_json_structure(sample_spaces)
        
        is_valid, errors = json_builder.validate_export_data(json_data)
        
        assert is_valid
        assert len(errors) == 0
    
    def test_invalid_json_structure_validation(self):
        """Test validation with invalid JSON structure."""
        json_builder = JsonBuilder()
        
        # Test missing required keys
        invalid_data = {"spaces": []}  # Missing metadata and summary
        
        is_valid, errors = json_builder.validate_export_data(invalid_data)
        
        assert not is_valid
        assert len(errors) > 0
        assert any("Missing required key: metadata" in error for error in errors)
        assert any("Missing required key: summary" in error for error in errors)
    
    def test_space_data_validation(self):
        """Test individual space data validation."""
        json_builder = JsonBuilder()
        
        # Test invalid space data
        invalid_space_data = {
            "properties": {"name": "Test"},  # Missing GUID
            "surfaces": "not_a_list",  # Should be list
            "space_boundaries": [],
            "relationships": []
        }
        
        errors = json_builder._validate_space_data(invalid_space_data, 0)
        
        assert len(errors) > 0
        assert any("Missing GUID" in error for error in errors)
        assert any("Surfaces must be a list" in error for error in errors)


if __name__ == "__main__":
    pytest.main([__file__])