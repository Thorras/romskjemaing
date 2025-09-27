"""
Export Dialog Widget

PyQt6 dialog for configuring and executing data export operations.
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QFileDialog, QMessageBox, QGroupBox,
                            QCheckBox, QComboBox, QTextEdit, QProgressBar,
                            QFormLayout, QSpinBox, QLineEdit, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QObject
from PyQt6.QtGui import QFont, QIcon

from ..data.space_model import SpaceData
from ..export.json_builder import JsonBuilder
from ..export.csv_exporter import CsvExporter
from ..export.excel_exporter import ExcelExporter
from ..export.pdf_exporter import PdfExporter


class ExportWorker(QObject):
    """Worker thread for export operations to prevent UI freezing."""
    
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    export_completed = pyqtSignal(bool, str)  # success, message
    
    def __init__(self, spaces: List[SpaceData], export_path: str, 
                 export_options: Dict[str, Any]):
        super().__init__()
        self.spaces = spaces
        self.export_path = export_path
        self.export_options = export_options
        
        # Initialize exporters
        self.json_builder = JsonBuilder()
        self.csv_exporter = CsvExporter()
        self.excel_exporter = ExcelExporter()
        self.pdf_exporter = PdfExporter()
    
    def run_export(self):
        """Execute the export operation."""
        try:
            format_name = self.export_options.get('format', 'JSON')
            
            self.status_updated.emit("Preparing export data...")
            self.progress_updated.emit(10)
            
            # Set source file information if available
            source_file = self.export_options.get('source_file')
            if source_file:
                self.json_builder.set_source_file(source_file)
                self.csv_exporter.set_source_file(source_file)
                self.excel_exporter.set_source_file(source_file)
                self.pdf_exporter.set_source_file(source_file)
            
            ifc_version = self.export_options.get('ifc_version')
            if ifc_version:
                self.json_builder.set_ifc_version(ifc_version)
            
            self.status_updated.emit(f"Building {format_name} export...")
            self.progress_updated.emit(30)
            
            # Export based on format
            if format_name == "JSON":
                success, message = self._export_json()
            elif format_name == "CSV":
                success, message = self._export_csv()
            elif format_name == "Excel":
                success, message = self._export_excel()
            elif format_name == "PDF":
                success, message = self._export_pdf()
            else:
                success, message = False, f"Unsupported export format: {format_name}"
            
            self.progress_updated.emit(100)
            
            if success:
                file_size = os.path.getsize(self.export_path)
                size_str = self._format_file_size(file_size)
                success_msg = f"{message} ({size_str})"
                self.export_completed.emit(True, success_msg)
            else:
                self.export_completed.emit(False, message)
                
        except Exception as e:
            self.export_completed.emit(False, f"Export failed: {str(e)}")
    
    def _export_json(self) -> Tuple[bool, str]:
        """Export to JSON format."""
        self.status_updated.emit("Building JSON structure...")
        self.progress_updated.emit(40)
        
        # Build JSON structure
        metadata = self.export_options.get('metadata', {})
        json_data = self.json_builder.build_json_structure(self.spaces, metadata)
        
        self.status_updated.emit("Validating export data...")
        self.progress_updated.emit(60)
        
        # Validate data if requested
        if self.export_options.get('validate', True):
            is_valid, validation_errors = self.json_builder.validate_export_data(json_data)
            if not is_valid:
                error_msg = "Data validation failed:\n" + "\n".join(validation_errors)
                return False, error_msg
        
        self.status_updated.emit("Writing JSON file...")
        self.progress_updated.emit(80)
        
        # Write to file
        indent = self.export_options.get('indent', 2)
        success = self.json_builder.write_json_file(self.export_path, json_data, indent)
        
        if success:
            return True, f"Successfully exported {len(self.spaces)} spaces to {Path(self.export_path).name}"
        else:
            return False, "Failed to write JSON file"
    
    def _export_csv(self) -> Tuple[bool, str]:
        """Export to CSV format."""
        self.status_updated.emit("Writing CSV file...")
        self.progress_updated.emit(60)
        
        include_surfaces = self.export_options.get('include_surfaces', True)
        include_boundaries = self.export_options.get('include_boundaries', True)
        include_relationships = self.export_options.get('include_relationships', True)
        
        return self.csv_exporter.export_to_csv(
            self.spaces, 
            self.export_path,
            include_surfaces=include_surfaces,
            include_boundaries=include_boundaries,
            include_relationships=include_relationships
        )
    
    def _export_excel(self) -> Tuple[bool, str]:
        """Export to Excel format."""
        self.status_updated.emit("Writing Excel file...")
        self.progress_updated.emit(60)
        
        include_surfaces = self.export_options.get('include_surfaces', True)
        include_boundaries = self.export_options.get('include_boundaries', True)
        include_relationships = self.export_options.get('include_relationships', True)
        
        return self.excel_exporter.export_to_excel(
            self.spaces,
            self.export_path,
            include_surfaces=include_surfaces,
            include_boundaries=include_boundaries,
            include_relationships=include_relationships
        )
    
    def _export_pdf(self) -> Tuple[bool, str]:
        """Export to PDF format."""
        self.status_updated.emit("Writing PDF file...")
        self.progress_updated.emit(60)
        
        include_surfaces = self.export_options.get('include_surfaces', True)
        include_boundaries = self.export_options.get('include_boundaries', True)
        include_relationships = self.export_options.get('include_relationships', True)
        
        return self.pdf_exporter.export_to_pdf(
            self.spaces,
            self.export_path,
            include_surfaces=include_surfaces,
            include_boundaries=include_boundaries,
            include_relationships=include_relationships
        )
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"


class ExportDialogWidget(QDialog):
    """Dialog for configuring and executing JSON export operations."""
    
    export_completed = pyqtSignal(bool, str)  # success, message
    
    def __init__(self, spaces: List[SpaceData], source_file_path: Optional[str] = None, parent=None):
        super().__init__(parent)
        self.spaces = spaces
        self.source_file_path = source_file_path
        self.export_worker = None
        self.export_thread = None
        
        self.setup_ui()
        self.connect_signals()
        self.validate_data_completeness()
        
    def setup_ui(self):
        """Set up the dialog user interface."""
        self.setWindowTitle("Export Room Schedule Data")
        self.setModal(True)
        self.resize(600, 700)
        
        # Main layout
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Title and description
        title_label = QLabel("Export Room Schedule Data")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        description_label = QLabel("Configure export options and generate JSON file containing all space data.")
        description_label.setWordWrap(True)
        description_label.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(description_label)
        
        # Data summary section
        self.create_data_summary_section(layout)
        
        # Export options section
        self.create_export_options_section(layout)
        
        # File selection section
        self.create_file_selection_section(layout)
        
        # Progress section (initially hidden)
        self.create_progress_section(layout)
        
        # Buttons
        self.create_button_section(layout)
        
        # Apply styling
        self.setStyleSheet("""
            QDialog {
                background-color: #f8f9fa;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #dee2e6;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                background-color: #f8f9fa;
            }
            QLabel {
                color: #495057;
            }
            QLineEdit, QComboBox, QSpinBox {
                padding: 6px;
                border: 1px solid #ced4da;
                border-radius: 4px;
                background-color: white;
            }
            QTextEdit {
                border: 1px solid #ced4da;
                border-radius: 4px;
                background-color: white;
            }
            QPushButton {
                padding: 8px 16px;
                border: 1px solid #ced4da;
                border-radius: 4px;
                background-color: white;
            }
            QPushButton:hover {
                background-color: #e9ecef;
            }
            QPushButton:pressed {
                background-color: #dee2e6;
            }
        """)
    
    def create_data_summary_section(self, layout: QVBoxLayout):
        """Create the data summary section."""
        summary_group = QGroupBox("Data Summary")
        summary_layout = QFormLayout()
        summary_group.setLayout(summary_layout)
        
        # Calculate summary statistics
        total_spaces = len(self.spaces)
        processed_spaces = sum(1 for space in self.spaces if space.processed)
        total_surfaces = sum(len(space.surfaces) for space in self.spaces)
        total_boundaries = sum(len(space.space_boundaries) for space in self.spaces)
        total_relationships = sum(len(space.relationships) for space in self.spaces)
        
        # Calculate total areas
        total_surface_area = sum(space.get_total_surface_area() for space in self.spaces)
        total_boundary_area = sum(space.get_total_boundary_area() for space in self.spaces)
        
        # Create summary labels
        summary_layout.addRow("Total Spaces:", QLabel(f"{total_spaces}"))
        summary_layout.addRow("Processed Spaces:", QLabel(f"{processed_spaces}"))
        summary_layout.addRow("Total Surfaces:", QLabel(f"{total_surfaces}"))
        summary_layout.addRow("Total Boundaries:", QLabel(f"{total_boundaries}"))
        summary_layout.addRow("Total Relationships:", QLabel(f"{total_relationships}"))
        summary_layout.addRow("Total Surface Area:", QLabel(f"{total_surface_area:.2f} m²"))
        summary_layout.addRow("Total Boundary Area:", QLabel(f"{total_boundary_area:.2f} m²"))
        
        # Data completeness warning
        if processed_spaces < total_spaces:
            warning_label = QLabel(f"⚠️ Warning: {total_spaces - processed_spaces} spaces have not been processed")
            warning_label.setStyleSheet("color: #dc3545; font-weight: bold;")
            summary_layout.addRow("", warning_label)
        
        layout.addWidget(summary_group)
    
    def create_export_options_section(self, layout: QVBoxLayout):
        """Create the export options section."""
        options_group = QGroupBox("Export Options")
        options_layout = QFormLayout()
        options_group.setLayout(options_layout)
        
        # Export format selection
        self.format_combo = QComboBox()
        self.format_combo.addItems(["JSON", "CSV", "Excel", "PDF"])
        self.format_combo.setCurrentText("JSON")
        self.format_combo.setToolTip("Select export format")
        self.format_combo.currentTextChanged.connect(self.on_format_changed)
        options_layout.addRow("Export Format:", self.format_combo)
        
        # JSON formatting options (initially visible)
        self.json_options_frame = QFrame()
        json_options_layout = QFormLayout()
        self.json_options_frame.setLayout(json_options_layout)
        
        self.indent_spinbox = QSpinBox()
        self.indent_spinbox.setRange(0, 8)
        self.indent_spinbox.setValue(2)
        self.indent_spinbox.setToolTip("Number of spaces for JSON indentation (0 for compact)")
        json_options_layout.addRow("JSON Indentation:", self.indent_spinbox)
        
        options_layout.addRow("", self.json_options_frame)
        
        # Data inclusion options
        self.include_surfaces_checkbox = QCheckBox("Include surfaces data")
        self.include_surfaces_checkbox.setChecked(True)
        self.include_surfaces_checkbox.setToolTip("Include surface information in export")
        options_layout.addRow("", self.include_surfaces_checkbox)
        
        self.include_boundaries_checkbox = QCheckBox("Include space boundaries data")
        self.include_boundaries_checkbox.setChecked(True)
        self.include_boundaries_checkbox.setToolTip("Include space boundary information in export")
        options_layout.addRow("", self.include_boundaries_checkbox)
        
        self.include_relationships_checkbox = QCheckBox("Include relationships data")
        self.include_relationships_checkbox.setChecked(True)
        self.include_relationships_checkbox.setToolTip("Include relationship information in export")
        options_layout.addRow("", self.include_relationships_checkbox)
        
        # Validation option
        self.validate_checkbox = QCheckBox("Validate data before export")
        self.validate_checkbox.setChecked(True)
        self.validate_checkbox.setToolTip("Perform data validation before export")
        options_layout.addRow("", self.validate_checkbox)
        
        # Include metadata option
        self.include_metadata_checkbox = QCheckBox("Include detailed metadata")
        self.include_metadata_checkbox.setChecked(True)
        self.include_metadata_checkbox.setToolTip("Include export timestamp and source file information")
        options_layout.addRow("", self.include_metadata_checkbox)
        
        # Include summary statistics
        self.include_summary_checkbox = QCheckBox("Include summary statistics")
        self.include_summary_checkbox.setChecked(True)
        self.include_summary_checkbox.setToolTip("Include calculated summary statistics in export")
        options_layout.addRow("", self.include_summary_checkbox)
        
        layout.addWidget(options_group)
    
    def create_file_selection_section(self, layout: QVBoxLayout):
        """Create the file selection section."""
        file_group = QGroupBox("Export File")
        file_layout = QVBoxLayout()
        file_group.setLayout(file_layout)
        
        # File path selection
        path_layout = QHBoxLayout()
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setPlaceholderText("Select export file location...")
        self.file_path_edit.setReadOnly(True)
        path_layout.addWidget(self.file_path_edit)
        
        self.browse_button = QPushButton("Browse...")
        self.browse_button.clicked.connect(self.browse_export_file)
        path_layout.addWidget(self.browse_button)
        
        file_layout.addLayout(path_layout)
        
        # File info
        self.file_info_label = QLabel("No file selected")
        self.file_info_label.setStyleSheet("color: #6c757d; font-size: 12px;")
        file_layout.addWidget(self.file_info_label)
        
        layout.addWidget(file_group)
    
    def create_progress_section(self, layout: QVBoxLayout):
        """Create the progress section."""
        self.progress_frame = QFrame()
        progress_layout = QVBoxLayout()
        self.progress_frame.setLayout(progress_layout)
        
        self.progress_label = QLabel("Export in progress...")
        progress_layout.addWidget(self.progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        progress_layout.addWidget(self.progress_bar)
        
        self.progress_frame.setVisible(False)
        layout.addWidget(self.progress_frame)
    
    def create_button_section(self, layout: QVBoxLayout):
        """Create the button section."""
        button_layout = QHBoxLayout()
        
        # Export button
        self.export_button = QPushButton("Export JSON")
        self.export_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        self.export_button.clicked.connect(self.start_export)
        self.export_button.setEnabled(False)  # Initially disabled
        button_layout.addWidget(self.export_button)
        
        button_layout.addStretch()
        
        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
    
    def connect_signals(self):
        """Connect widget signals."""
        self.file_path_edit.textChanged.connect(self.update_export_button_state)
    
    def on_format_changed(self, format_name: str):
        """Handle export format change."""
        # Show/hide JSON-specific options
        self.json_options_frame.setVisible(format_name == "JSON")
        
        # Update export button text
        self.export_button.setText(f"Export {format_name}")
        
        # Clear current file path to force user to select new file
        current_path = self.file_path_edit.text()
        if current_path:
            # Update extension based on format
            path_obj = Path(current_path)
            base_name = path_obj.stem
            
            extension_map = {
                "JSON": ".json",
                "CSV": ".csv", 
                "Excel": ".xlsx",
                "PDF": ".pdf"
            }
            
            new_extension = extension_map.get(format_name, ".json")
            new_path = path_obj.parent / (base_name + new_extension)
            self.file_path_edit.setText(str(new_path))
            self.update_file_info(str(new_path))
    
    def validate_data_completeness(self):
        """Validate data completeness and show warnings if needed."""
        if not self.spaces:
            QMessageBox.warning(self, "No Data", 
                              "No space data available for export. Please load an IFC file first.")
            return
        
        # Check for incomplete data
        incomplete_spaces = [space for space in self.spaces if not space.processed]
        if incomplete_spaces:
            reply = QMessageBox.question(
                self, "Incomplete Data",
                f"{len(incomplete_spaces)} spaces have not been fully processed. "
                f"Do you want to continue with the export?\n\n"
                f"Unprocessed spaces may have missing surface descriptions or other data.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                self.reject()
                return
    
    def browse_export_file(self):
        """Open file dialog to select export file location."""
        format_name = self.format_combo.currentText()
        
        # Define file filters and extensions for each format
        format_config = {
            "JSON": {
                "extension": ".json",
                "filter": "JSON Files (*.json);;All Files (*)",
                "default_name": "room_schedule_export.json"
            },
            "CSV": {
                "extension": ".csv",
                "filter": "CSV Files (*.csv);;All Files (*)",
                "default_name": "room_schedule_export.csv"
            },
            "Excel": {
                "extension": ".xlsx",
                "filter": "Excel Files (*.xlsx);;All Files (*)",
                "default_name": "room_schedule_export.xlsx"
            },
            "PDF": {
                "extension": ".pdf",
                "filter": "PDF Files (*.pdf);;All Files (*)",
                "default_name": "room_schedule_export.pdf"
            }
        }
        
        config = format_config.get(format_name, format_config["JSON"])
        
        default_filename = config["default_name"]
        if self.source_file_path:
            source_name = Path(self.source_file_path).stem
            default_filename = f"{source_name}_room_schedule{config['extension']}"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            f"Save {format_name} Export File",
            default_filename,
            config["filter"]
        )
        
        if file_path:
            # Ensure correct extension
            if not file_path.lower().endswith(config['extension']):
                file_path += config['extension']
            
            self.file_path_edit.setText(file_path)
            self.update_file_info(file_path)
    
    def update_file_info(self, file_path: str):
        """Update file information display."""
        path_obj = Path(file_path)
        directory = path_obj.parent
        filename = path_obj.name
        
        # Check if directory is writable
        if directory.exists() and os.access(directory, os.W_OK):
            self.file_info_label.setText(f"📁 {directory} | 📄 {filename}")
            self.file_info_label.setStyleSheet("color: #28a745; font-size: 12px;")
        else:
            self.file_info_label.setText(f"⚠️ Directory not writable: {directory}")
            self.file_info_label.setStyleSheet("color: #dc3545; font-size: 12px;")
    
    def update_export_button_state(self):
        """Update the export button enabled state."""
        has_file_path = bool(self.file_path_edit.text().strip())
        has_spaces = bool(self.spaces)
        self.export_button.setEnabled(has_file_path and has_spaces)
    
    def start_export(self):
        """Start the export process."""
        export_path = self.file_path_edit.text().strip()
        if not export_path:
            QMessageBox.warning(self, "No File Selected", 
                              "Please select a file location for the export.")
            return
        
        # Check if file already exists
        if os.path.exists(export_path):
            reply = QMessageBox.question(
                self, "File Exists",
                f"The file '{Path(export_path).name}' already exists. Do you want to overwrite it?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return
        
        # Prepare export options
        export_options = {
            'format': self.format_combo.currentText(),
            'indent': self.indent_spinbox.value(),
            'validate': self.validate_checkbox.isChecked(),
            'include_metadata': self.include_metadata_checkbox.isChecked(),
            'include_summary': self.include_summary_checkbox.isChecked(),
            'include_surfaces': self.include_surfaces_checkbox.isChecked(),
            'include_boundaries': self.include_boundaries_checkbox.isChecked(),
            'include_relationships': self.include_relationships_checkbox.isChecked()
        }
        
        if self.source_file_path:
            export_options['source_file'] = self.source_file_path
        
        # Show progress and disable controls
        self.progress_frame.setVisible(True)
        self.export_button.setEnabled(False)
        self.browse_button.setEnabled(False)
        
        # Create and start export worker thread
        self.export_thread = QThread()
        self.export_worker = ExportWorker(self.spaces, export_path, export_options)
        self.export_worker.moveToThread(self.export_thread)
        
        # Connect worker signals
        self.export_worker.progress_updated.connect(self.progress_bar.setValue)
        self.export_worker.status_updated.connect(self.progress_label.setText)
        self.export_worker.export_completed.connect(self.on_export_completed)
        
        # Connect thread signals
        self.export_thread.started.connect(self.export_worker.run_export)
        self.export_thread.finished.connect(self.export_thread.deleteLater)
        
        # Start the thread
        self.export_thread.start()
    
    def on_export_completed(self, success: bool, message: str):
        """Handle export completion."""
        # Hide progress
        self.progress_frame.setVisible(False)
        
        # Re-enable controls
        self.export_button.setEnabled(True)
        self.browse_button.setEnabled(True)
        
        # Clean up thread
        if self.export_thread:
            self.export_thread.quit()
            self.export_thread.wait()
            self.export_thread = None
        self.export_worker = None
        
        # Show result message
        if success:
            QMessageBox.information(self, "Export Successful", message)
            self.export_completed.emit(True, message)
            self.accept()
        else:
            QMessageBox.critical(self, "Export Failed", message)
            self.export_completed.emit(False, message)
    
    def get_export_summary(self) -> Dict[str, Any]:
        """Get summary of export configuration."""
        return {
            'total_spaces': len(self.spaces),
            'processed_spaces': sum(1 for space in self.spaces if space.processed),
            'export_path': self.file_path_edit.text(),
            'options': {
                'indent': self.indent_spinbox.value(),
                'validate': self.validate_checkbox.isChecked(),
                'include_metadata': self.include_metadata_checkbox.isChecked(),
                'include_summary': self.include_summary_checkbox.isChecked()
            }
        }