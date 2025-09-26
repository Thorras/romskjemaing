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
        self.json_builder = JsonBuilder()
    
    def run_export(self):
        """Execute the export operation."""
        try:
            self.status_updated.emit("Preparing export data...")
            self.progress_updated.emit(10)
            
            # Set source file information if available
            if 'source_file' in self.export_options:
                self.json_builder.set_source_file(self.export_options['source_file'])
            if 'ifc_version' in self.export_options:
                self.json_builder.set_ifc_version(self.export_options['ifc_version'])
            
            self.status_updated.emit("Building JSON structure...")
            self.progress_updated.emit(30)
            
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
                    self.export_completed.emit(False, error_msg)
                    return
            
            self.status_updated.emit("Writing JSON file...")
            self.progress_updated.emit(80)
            
            # Write to file
            indent = self.export_options.get('indent', 2)
            success = self.json_builder.write_json_file(self.export_path, json_data, indent)
            
            self.progress_updated.emit(100)
            
            if success:
                file_size = os.path.getsize(self.export_path)
                size_str = self._format_file_size(file_size)
                success_msg = f"Successfully exported {len(self.spaces)} spaces to {Path(self.export_path).name} ({size_str})"
                self.export_completed.emit(True, success_msg)
            else:
                self.export_completed.emit(False, "Failed to write JSON file")
                
        except Exception as e:
            self.export_completed.emit(False, f"Export failed: {str(e)}")
    
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
        
        # JSON formatting options
        self.indent_spinbox = QSpinBox()
        self.indent_spinbox.setRange(0, 8)
        self.indent_spinbox.setValue(2)
        self.indent_spinbox.setToolTip("Number of spaces for JSON indentation (0 for compact)")
        options_layout.addRow("JSON Indentation:", self.indent_spinbox)
        
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
        default_filename = "room_schedule_export.json"
        if self.source_file_path:
            source_name = Path(self.source_file_path).stem
            default_filename = f"{source_name}_room_schedule.json"
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Export File",
            default_filename,
            "JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            # Ensure .json extension
            if not file_path.lower().endswith('.json'):
                file_path += '.json'
            
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
            'indent': self.indent_spinbox.value(),
            'validate': self.validate_checkbox.isChecked(),
            'include_metadata': self.include_metadata_checkbox.isChecked(),
            'include_summary': self.include_summary_checkbox.isChecked()
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