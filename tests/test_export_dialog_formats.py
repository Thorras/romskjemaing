"""
Test cases for export dialog widget with multiple format support.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest

from ifc_room_schedule.ui.export_dialog_widget import ExportDialogWidget, ExportWorker
from ifc_room_schedule.data.space_model import SpaceData
from ifc_room_schedule.data.surface_model import SurfaceData


@pytest.fixture
def app():
    """Create QApplication instance for testing."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def sample_spaces():
    """Create sample space data for testing."""
    surface1 = SurfaceData(
        id="surface_1",
        type="Wall",
        area=25.5,
        material="Concrete",
        ifc_type="IfcWall",
        related_space_guid="space_guid_1",
        user_description="Test wall"
    )
    
    space1 = SpaceData(
        guid="space_guid_1",
        name="Office 101",
        long_name="Main Office Room 101",
        description="Primary office space",
        object_type="Office",
        zone_category="Work",
        number="101",
        elevation=0.0,
        quantities={"Height": 3.0},
        surfaces=[surface1],
        space_boundaries=[],
        relationships=[],
        user_descriptions={"space": "Test office"},
        processed=True
    )
    
    return [space1]


class TestExportDialogFormats:
    """Test cases for ExportDialogWidget format selection."""
    
    def test_format_combo_initialization(self, app, sample_spaces):
        """Test format combo box initializes with correct options."""
        dialog = ExportDialogWidget(sample_spaces)
        
        # Check format combo box has all expected formats
        format_combo = dialog.format_combo
        assert format_combo.count() == 5
        assert format_combo.itemText(0) == "JSON"
        assert format_combo.itemText(1) == "CSV"
        assert format_combo.itemText(2) == "Excel"
        assert format_combo.itemText(3) == "PDF"
        assert format_combo.itemText(4) == "Azure SQL"
        
        # Check default selection
        assert format_combo.currentText() == "JSON"
    
    def test_format_change_updates_ui(self, app, sample_spaces):
        """Test format change updates UI elements."""
        dialog = ExportDialogWidget(sample_spaces)
        
        # Initially JSON options should be visible (after dialog is shown)
        dialog.show()
        assert dialog.json_options_frame.isVisible() is True
        assert dialog.export_button.text() == "Export JSON"
        
        # Change to CSV
        dialog.format_combo.setCurrentText("CSV")
        dialog.on_format_changed("CSV")
        
        assert dialog.json_options_frame.isVisible() is False
        assert dialog.export_button.text() == "Export CSV"
        
        # Change to Excel
        dialog.format_combo.setCurrentText("Excel")
        dialog.on_format_changed("Excel")
        
        assert dialog.json_options_frame.isVisible() is False
        assert dialog.export_button.text() == "Export Excel"
        
        # Change to PDF
        dialog.format_combo.setCurrentText("PDF")
        dialog.on_format_changed("PDF")
        
        assert dialog.json_options_frame.isVisible() is False
        assert dialog.export_button.text() == "Export PDF"
        
        # Change back to JSON
        dialog.format_combo.setCurrentText("JSON")
        dialog.on_format_changed("JSON")
        
        assert dialog.json_options_frame.isVisible() is True
        assert dialog.export_button.text() == "Export JSON"
    
    def test_format_change_updates_file_extension(self, app, sample_spaces):
        """Test format change updates file path extension."""
        dialog = ExportDialogWidget(sample_spaces)
        
        # Set initial file path
        dialog.file_path_edit.setText("/test/export.json")
        
        # Change to CSV
        dialog.on_format_changed("CSV")
        assert dialog.file_path_edit.text().endswith("export.csv")
        
        # Change to Excel
        dialog.on_format_changed("Excel")
        assert dialog.file_path_edit.text().endswith("export.xlsx")
        
        # Change to PDF
        dialog.on_format_changed("PDF")
        assert dialog.file_path_edit.text().endswith("export.pdf")
        
        # Change back to JSON
        dialog.on_format_changed("JSON")
        assert dialog.file_path_edit.text().endswith("export.json")
    
    def test_data_inclusion_checkboxes(self, app, sample_spaces):
        """Test data inclusion checkboxes are present and functional."""
        dialog = ExportDialogWidget(sample_spaces)
        
        # Check checkboxes exist and are checked by default
        assert dialog.include_surfaces_checkbox.isChecked() is True
        assert dialog.include_boundaries_checkbox.isChecked() is True
        assert dialog.include_relationships_checkbox.isChecked() is True
        
        # Test unchecking
        dialog.include_surfaces_checkbox.setChecked(False)
        dialog.include_boundaries_checkbox.setChecked(False)
        dialog.include_relationships_checkbox.setChecked(False)
        
        assert dialog.include_surfaces_checkbox.isChecked() is False
        assert dialog.include_boundaries_checkbox.isChecked() is False
        assert dialog.include_relationships_checkbox.isChecked() is False
    
    def test_browse_file_dialog_filters(self, app, sample_spaces):
        """Test browse file dialog uses correct filters for each format."""
        dialog = ExportDialogWidget(sample_spaces)
        
        with patch('ifc_room_schedule.ui.export_dialog_widget.QFileDialog.getSaveFileName') as mock_dialog:
            mock_dialog.return_value = ("/test/export.json", "JSON Files (*.json)")
            
            # Test JSON filter
            dialog.format_combo.setCurrentText("JSON")
            dialog.browse_export_file()
            
            args, kwargs = mock_dialog.call_args
            assert "JSON Files (*.json)" in args[3]
            
            # Test CSV filter
            mock_dialog.return_value = ("/test/export.csv", "CSV Files (*.csv)")
            dialog.format_combo.setCurrentText("CSV")
            dialog.browse_export_file()
            
            args, kwargs = mock_dialog.call_args
            assert "CSV Files (*.csv)" in args[3]
            
            # Test Excel filter
            mock_dialog.return_value = ("/test/export.xlsx", "Excel Files (*.xlsx)")
            dialog.format_combo.setCurrentText("Excel")
            dialog.browse_export_file()
            
            args, kwargs = mock_dialog.call_args
            assert "Excel Files (*.xlsx)" in args[3]
            
            # Test PDF filter
            mock_dialog.return_value = ("/test/export.pdf", "PDF Files (*.pdf)")
            dialog.format_combo.setCurrentText("PDF")
            dialog.browse_export_file()
            
            args, kwargs = mock_dialog.call_args
            assert "PDF Files (*.pdf)" in args[3]


class TestExportWorkerFormats:
    """Test cases for ExportWorker with multiple formats."""
    
    def test_export_worker_initialization(self, sample_spaces):
        """Test ExportWorker initializes with all exporters."""
        export_options = {
            'format': 'JSON',
            'include_surfaces': True,
            'include_boundaries': True,
            'include_relationships': True
        }
        
        worker = ExportWorker(sample_spaces, "/test/export.json", export_options)
        
        assert worker.json_builder is not None
        assert worker.csv_exporter is not None
        assert worker.excel_exporter is not None
        assert worker.pdf_exporter is not None
    
    def test_export_worker_json_format(self, sample_spaces):
        """Test ExportWorker handles JSON format."""
        export_options = {
            'format': 'JSON',
            'indent': 2,
            'validate': True,
            'include_surfaces': True,
            'include_boundaries': True,
            'include_relationships': True
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            export_path = os.path.join(temp_dir, "test_export.json")
            worker = ExportWorker(sample_spaces, export_path, export_options)
            
            # Mock the JSON builder methods
            with patch.object(worker.json_builder, 'build_json_structure') as mock_build, \
                 patch.object(worker.json_builder, 'validate_export_data') as mock_validate, \
                 patch.object(worker.json_builder, 'write_json_file') as mock_write:
                
                mock_build.return_value = {"test": "data"}
                mock_validate.return_value = (True, [])
                mock_write.return_value = True
                
                success, message = worker._export_json()
                
                assert success is True
                assert "Successfully exported" in message
                mock_build.assert_called_once()
                mock_validate.assert_called_once()
                mock_write.assert_called_once()
    
    def test_export_worker_csv_format(self, sample_spaces):
        """Test ExportWorker handles CSV format."""
        export_options = {
            'format': 'CSV',
            'include_surfaces': True,
            'include_boundaries': False,
            'include_relationships': True
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            export_path = os.path.join(temp_dir, "test_export.csv")
            worker = ExportWorker(sample_spaces, export_path, export_options)
            
            # Mock the CSV exporter method
            with patch.object(worker.csv_exporter, 'export_to_csv') as mock_export:
                mock_export.return_value = (True, "CSV export successful")
                
                success, message = worker._export_csv()
                
                assert success is True
                assert message == "CSV export successful"
                mock_export.assert_called_once_with(
                    sample_spaces,
                    export_path,
                    include_surfaces=True,
                    include_boundaries=False,
                    include_relationships=True
                )
    
    def test_export_worker_excel_format(self, sample_spaces):
        """Test ExportWorker handles Excel format."""
        export_options = {
            'format': 'Excel',
            'include_surfaces': False,
            'include_boundaries': True,
            'include_relationships': False
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            export_path = os.path.join(temp_dir, "test_export.xlsx")
            worker = ExportWorker(sample_spaces, export_path, export_options)
            
            # Mock the Excel exporter method
            with patch.object(worker.excel_exporter, 'export_to_excel') as mock_export:
                mock_export.return_value = (True, "Excel export successful")
                
                success, message = worker._export_excel()
                
                assert success is True
                assert message == "Excel export successful"
                mock_export.assert_called_once_with(
                    sample_spaces,
                    export_path,
                    include_surfaces=False,
                    include_boundaries=True,
                    include_relationships=False
                )
    
    def test_export_worker_pdf_format(self, sample_spaces):
        """Test ExportWorker handles PDF format."""
        export_options = {
            'format': 'PDF',
            'include_surfaces': True,
            'include_boundaries': True,
            'include_relationships': True
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            export_path = os.path.join(temp_dir, "test_export.pdf")
            worker = ExportWorker(sample_spaces, export_path, export_options)
            
            # Mock the PDF exporter method
            with patch.object(worker.pdf_exporter, 'export_to_pdf') as mock_export:
                mock_export.return_value = (True, "PDF export successful")
                
                success, message = worker._export_pdf()
                
                assert success is True
                assert message == "PDF export successful"
                mock_export.assert_called_once_with(
                    sample_spaces,
                    export_path,
                    include_surfaces=True,
                    include_boundaries=True,
                    include_relationships=True
                )
    
    def test_export_worker_unsupported_format(self, sample_spaces):
        """Test ExportWorker handles unsupported format."""
        export_options = {
            'format': 'UNSUPPORTED',
            'include_surfaces': True,
            'include_boundaries': True,
            'include_relationships': True
        }
        
        worker = ExportWorker(sample_spaces, "/test/export.txt", export_options)
        
        # Mock the run_export method to test format handling
        with patch.object(worker, 'export_completed') as mock_signal:
            worker.run_export()
            
            # Should emit failure signal
            mock_signal.emit.assert_called_once()
            args = mock_signal.emit.call_args[0]
            assert args[0] is False  # success = False
            assert "Unsupported export format" in args[1]  # error message
    
    def test_export_worker_source_file_setting(self, sample_spaces):
        """Test ExportWorker sets source file on all exporters."""
        export_options = {
            'format': 'JSON',
            'source_file': '/test/source.ifc',
            'ifc_version': 'IFC4'
        }
        
        worker = ExportWorker(sample_spaces, "/test/export.json", export_options)
        
        # Mock all exporter set_source_file methods
        with patch.object(worker.json_builder, 'set_source_file') as mock_json_source, \
             patch.object(worker.csv_exporter, 'set_source_file') as mock_csv_source, \
             patch.object(worker.excel_exporter, 'set_source_file') as mock_excel_source, \
             patch.object(worker.pdf_exporter, 'set_source_file') as mock_pdf_source, \
             patch.object(worker.json_builder, 'set_ifc_version') as mock_ifc_version, \
             patch.object(worker, '_export_json') as mock_export:
            
            mock_export.return_value = (True, "Success")
            
            worker.run_export()
            
            # Verify all exporters had source file set
            mock_json_source.assert_called_once_with('/test/source.ifc')
            mock_csv_source.assert_called_once_with('/test/source.ifc')
            mock_excel_source.assert_called_once_with('/test/source.ifc')
            mock_pdf_source.assert_called_once_with('/test/source.ifc')
            mock_ifc_version.assert_called_once_with('IFC4')