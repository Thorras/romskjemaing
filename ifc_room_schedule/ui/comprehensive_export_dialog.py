"""
Comprehensive Export Dialog

Enhanced export dialog that supports the comprehensive room schedule structure
with user data input capabilities.
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QFileDialog, QMessageBox, QGroupBox,
                            QCheckBox, QComboBox, QTextEdit, QProgressBar,
                            QFormLayout, QSpinBox, QLineEdit, QFrame, QTabWidget,
                            QTableWidget, QTableWidgetItem, QHeaderView, QWidget)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QObject
from PyQt6.QtGui import QFont, QIcon

from ..data.space_model import SpaceData
from ..export.comprehensive_json_builder import ComprehensiveJsonBuilder


class ComprehensiveExportWorker(QObject):
    """Worker thread for comprehensive export operations."""
    
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    export_completed = pyqtSignal(bool, str)  # success, message
    
    def __init__(self, spaces: List[SpaceData], export_path: str, 
                 export_options: Dict[str, Any]):
        super().__init__()
        self.spaces = spaces
        self.export_path = export_path
        self.export_options = export_options
        self.json_builder = ComprehensiveJsonBuilder()
    
    def run_export(self):
        """Execute the comprehensive export operation."""
        try:
            self.status_updated.emit("Preparing comprehensive export...")
            self.progress_updated.emit(10)
            
            # Set source file information
            source_file = self.export_options.get('source_file')
            if source_file:
                self.json_builder.set_source_file(source_file)
            
            ifc_version = self.export_options.get('ifc_version', 'IFC4')
            self.json_builder.set_ifc_version(ifc_version)
            
            # Get project information
            project_info = self.export_options.get('project_info', {})
            
            # Get user data
            user_data_per_space = self.export_options.get('user_data_per_space', {})
            
            self.status_updated.emit("Building comprehensive JSON structure...")
            self.progress_updated.emit(30)
            
            # Export format
            export_format = self.export_options.get('format', 'comprehensive_json')
            
            if export_format == 'comprehensive_json':
                success, message = self._export_comprehensive_json(project_info, user_data_per_space)
            elif export_format == 'user_templates':
                success, message = self._export_user_templates()
            else:
                success, message = False, f"Unsupported export format: {export_format}"
            
            self.progress_updated.emit(100)
            self.export_completed.emit(success, message)
                
        except Exception as e:
            self.export_completed.emit(False, f"Export failed: {str(e)}")
    
    def _export_comprehensive_json(self, project_info: Dict[str, Any], 
                                 user_data_per_space: Dict[str, Dict[str, Any]]) -> Tuple[bool, str]:
        """Export comprehensive JSON format."""
        self.status_updated.emit("Writing comprehensive JSON file...")
        self.progress_updated.emit(60)
        
        success = self.json_builder.write_comprehensive_json_file(
            self.export_path,
            self.spaces,
            project_info,
            user_data_per_space,
            indent=self.export_options.get('indent', 2)
        )
        
        if success:
            file_size = os.path.getsize(self.export_path)
            size_str = self._format_file_size(file_size)
            return True, f"Successfully exported {len(self.spaces)} rooms to comprehensive format ({size_str})"
        else:
            return False, "Failed to write comprehensive JSON file"
    
    def _export_user_templates(self) -> Tuple[bool, str]:
        """Export user input templates."""
        self.status_updated.emit("Creating user input templates...")
        self.progress_updated.emit(60)
        
        # Create templates directory
        templates_dir = Path(self.export_path).parent / "user_input_templates"
        
        created_files = self.json_builder.create_user_input_templates(
            self.spaces, str(templates_dir)
        )
        
        if created_files:
            return True, f"Created {len(created_files)} user input templates in {templates_dir}"
        else:
            return False, "Failed to create user input templates"
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} MB"


class ProjectInfoWidget(QWidget):
    """Widget for entering project information."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the project info UI."""
        layout = QFormLayout(self)
        
        # Project information
        self.project_id_edit = QLineEdit()
        self.project_id_edit.setPlaceholderText("e.g., PRJ-2024-001")
        layout.addRow("Project ID:", self.project_id_edit)
        
        self.project_name_edit = QLineEdit()
        self.project_name_edit.setPlaceholderText("e.g., Boligblokk Sentrum")
        layout.addRow("Project Name:", self.project_name_edit)
        
        self.building_id_edit = QLineEdit()
        self.building_id_edit.setPlaceholderText("e.g., BLD-A")
        layout.addRow("Building ID:", self.building_id_edit)
        
        self.building_name_edit = QLineEdit()
        self.building_name_edit.setPlaceholderText("e.g., Blokk A")
        layout.addRow("Building Name:", self.building_name_edit)
        
        # Phase and state
        self.phase_combo = QComboBox()
        self.phase_combo.addItems([
            "Forprosjekt", "Detaljprosjektering", "Utførelse", "Ferdigstillelse"
        ])
        layout.addRow("Phase:", self.phase_combo)
        
        self.state_combo = QComboBox()
        self.state_combo.addItems([
            "Utkast", "Til godkjenning", "Godkjent", "Endret", "Låst"
        ])
        layout.addRow("State:", self.state_combo)
        
        # Created by
        self.created_by_edit = QLineEdit()
        self.created_by_edit.setPlaceholderText("e.g., John Doe")
        layout.addRow("Created By:", self.created_by_edit)
    
    def get_project_info(self) -> Dict[str, Any]:
        """Get project information from the form."""
        return {
            "project_id": self.project_id_edit.text().strip() or None,
            "project_name": self.project_name_edit.text().strip() or None,
            "building_id": self.building_id_edit.text().strip() or None,
            "building_name": self.building_name_edit.text().strip() or None,
            "phase": self.phase_combo.currentText(),
            "state": self.state_combo.currentText(),
            "created_by": self.created_by_edit.text().strip() or None
        }


class UserDataWidget(QWidget):
    """Widget for managing user data input."""
    
    def __init__(self, spaces: List[SpaceData], parent=None):
        super().__init__(parent)
        self.spaces = spaces
        self.user_data = {}
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the user data UI."""
        layout = QVBoxLayout(self)
        
        # Instructions
        instructions = QLabel(
            "User data allows you to specify information that cannot be extracted from IFC files, "
            "such as performance requirements, finishes, and other project-specific data."
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(instructions)
        
        # Options
        options_layout = QHBoxLayout()
        
        self.create_templates_btn = QPushButton("Create Input Templates")
        self.create_templates_btn.setToolTip("Create JSON templates for user data input")
        self.create_templates_btn.clicked.connect(self.create_templates)
        options_layout.addWidget(self.create_templates_btn)
        
        self.load_user_data_btn = QPushButton("Load User Data")
        self.load_user_data_btn.setToolTip("Load user data from filled templates")
        self.load_user_data_btn.clicked.connect(self.load_user_data)
        options_layout.addWidget(self.load_user_data_btn)
        
        options_layout.addStretch()
        layout.addLayout(options_layout)
        
        # Status
        self.status_label = QLabel("No user data loaded")
        self.status_label.setStyleSheet("color: #6c757d; font-style: italic;")
        layout.addWidget(self.status_label)
        
        # User data table
        self.user_data_table = QTableWidget()
        self.user_data_table.setColumnCount(3)
        self.user_data_table.setHorizontalHeaderLabels(["Room", "Data Sections", "Status"])
        self.user_data_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.user_data_table)
        
        self.update_user_data_table()
    
    def create_templates(self):
        """Create user input templates."""
        # Select output directory
        output_dir = QFileDialog.getExistingDirectory(
            self, "Select Directory for User Input Templates"
        )
        
        if not output_dir:
            return
        
        try:
            json_builder = ComprehensiveJsonBuilder()
            created_files = json_builder.create_user_input_templates(self.spaces, output_dir)
            
            if created_files:
                QMessageBox.information(
                    self, "Templates Created",
                    f"Created {len(created_files)} user input templates in:\n{output_dir}\n\n"
                    f"Fill out these templates and use 'Load User Data' to import them."
                )
                self.status_label.setText(f"Created {len(created_files)} templates in {output_dir}")
            else:
                QMessageBox.warning(self, "No Templates Created", "No templates were created.")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create templates: {str(e)}")
    
    def load_user_data(self):
        """Load user data from template files."""
        # Select template files
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "Select User Data Template Files",
            "", "JSON Files (*.json);;All Files (*)"
        )
        
        if not file_paths:
            return
        
        try:
            json_builder = ComprehensiveJsonBuilder()
            self.user_data = json_builder.load_user_data_from_files(file_paths)
            
            if self.user_data:
                self.status_label.setText(f"Loaded user data for {len(self.user_data)} rooms")
                self.update_user_data_table()
                QMessageBox.information(
                    self, "User Data Loaded",
                    f"Successfully loaded user data for {len(self.user_data)} rooms."
                )
            else:
                QMessageBox.warning(self, "No Data Loaded", "No valid user data was found in the selected files.")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load user data: {str(e)}")
    
    def update_user_data_table(self):
        """Update the user data table."""
        self.user_data_table.setRowCount(len(self.spaces))
        
        for row, space in enumerate(self.spaces):
            # Room name
            room_item = QTableWidgetItem(space.name or space.guid)
            self.user_data_table.setItem(row, 0, room_item)
            
            # Data sections
            if space.guid in self.user_data:
                user_space_data = self.user_data[space.guid]
                sections = list(user_space_data.keys())
                sections_text = ", ".join(sections[:3])  # Show first 3 sections
                if len(sections) > 3:
                    sections_text += f" (+{len(sections) - 3} more)"
            else:
                sections_text = "No data"
            
            sections_item = QTableWidgetItem(sections_text)
            self.user_data_table.setItem(row, 1, sections_item)
            
            # Status
            if space.guid in self.user_data:
                status_item = QTableWidgetItem("✓ Loaded")
                status_item.setBackground(Qt.GlobalColor.lightGreen)
            else:
                status_item = QTableWidgetItem("No data")
                status_item.setBackground(Qt.GlobalColor.lightGray)
            
            self.user_data_table.setItem(row, 2, status_item)
    
    def get_user_data(self) -> Dict[str, Dict[str, Any]]:
        """Get the loaded user data."""
        return self.user_data


class ComprehensiveExportDialog(QDialog):
    """Comprehensive export dialog with project info and user data support."""
    
    export_completed = pyqtSignal(bool, str)  # success, message
    
    def __init__(self, spaces: List[SpaceData], source_file_path: Optional[str] = None, parent=None):
        super().__init__(parent)
        self.spaces = spaces
        self.source_file_path = source_file_path
        self.export_worker = None
        self.export_thread = None
        
        self.setup_ui()
        self.connect_signals()
        
    def setup_ui(self):
        """Set up the dialog user interface."""
        self.setWindowTitle("Comprehensive Room Schedule Export")
        self.setModal(True)
        self.resize(800, 700)
        
        # Main layout
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Title
        title_label = QLabel("Comprehensive Room Schedule Export")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Description
        description_label = QLabel(
            "Export room data using the comprehensive JSON structure with support for "
            "project information, performance requirements, finishes, and other detailed data."
        )
        description_label.setWordWrap(True)
        description_label.setStyleSheet("color: #666; margin-bottom: 10px;")
        layout.addWidget(description_label)
        
        # Tab widget for different sections
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Export options tab
        self.create_export_options_tab()
        
        # Project info tab
        self.create_project_info_tab()
        
        # User data tab
        self.create_user_data_tab()
        
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
                color: black;
            }
            QLineEdit, QComboBox, QSpinBox {
                padding: 6px;
                border: 1px solid #ced4da;
                border-radius: 4px;
                background-color: white;
                color: black;
            }
            QTextEdit {
                border: 1px solid #ced4da;
                border-radius: 4px;
                background-color: white;
                color: black;
            }
            QPushButton {
                padding: 8px 16px;
                border: 1px solid #ced4da;
                border-radius: 4px;
                background-color: white;
                color: black;
            }
            QPushButton:hover {
                background-color: #e9ecef;
            }
            QPushButton:pressed {
                background-color: #dee2e6;
            }
        """)
    
    def create_export_options_tab(self):
        """Create the export options tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Export format
        format_group = QGroupBox("Export Format")
        format_layout = QFormLayout(format_group)
        
        self.format_combo = QComboBox()
        self.format_combo.addItems([
            "Comprehensive JSON", 
            "User Input Templates"
        ])
        self.format_combo.setCurrentText("Comprehensive JSON")
        format_layout.addRow("Format:", self.format_combo)
        
        layout.addWidget(format_group)
        
        # JSON options
        json_group = QGroupBox("JSON Options")
        json_layout = QFormLayout(json_group)
        
        self.indent_spinbox = QSpinBox()
        self.indent_spinbox.setRange(0, 8)
        self.indent_spinbox.setValue(2)
        json_layout.addRow("Indentation:", self.indent_spinbox)
        
        layout.addWidget(json_group)
        
        # File selection
        file_group = QGroupBox("Output File")
        file_layout = QVBoxLayout(file_group)
        
        path_layout = QHBoxLayout()
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setPlaceholderText("Select export file location...")
        self.file_path_edit.setReadOnly(True)
        path_layout.addWidget(self.file_path_edit)
        
        self.browse_button = QPushButton("Browse...")
        self.browse_button.clicked.connect(self.browse_export_file)
        path_layout.addWidget(self.browse_button)
        
        file_layout.addLayout(path_layout)
        layout.addWidget(file_group)
        
        layout.addStretch()
        self.tab_widget.addTab(widget, "Export Options")
    
    def create_project_info_tab(self):
        """Create the project info tab."""
        self.project_info_widget = ProjectInfoWidget()
        self.tab_widget.addTab(self.project_info_widget, "Project Info")
    
    def create_user_data_tab(self):
        """Create the user data tab."""
        self.user_data_widget = UserDataWidget(self.spaces)
        self.tab_widget.addTab(self.user_data_widget, "User Data")
    
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
        self.export_button = QPushButton("Export Comprehensive JSON")
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
        self.export_button.setEnabled(False)
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
        self.format_combo.currentTextChanged.connect(self.on_format_changed)
    
    def on_format_changed(self, format_name: str):
        """Handle export format change."""
        if format_name == "Comprehensive JSON":
            self.export_button.setText("Export Comprehensive JSON")
        elif format_name == "User Input Templates":
            self.export_button.setText("Create User Templates")
        
        self.update_export_button_state()
    
    def browse_export_file(self):
        """Open file dialog to select export file location."""
        format_name = self.format_combo.currentText()
        
        if format_name == "User Input Templates":
            # For templates, select directory
            output_dir = QFileDialog.getExistingDirectory(
                self, "Select Directory for User Input Templates"
            )
            if output_dir:
                self.file_path_edit.setText(output_dir)
        else:
            # For JSON export, select file
            default_filename = "comprehensive_room_schedule.json"
            if self.source_file_path:
                source_name = Path(self.source_file_path).stem
                default_filename = f"{source_name}_comprehensive_room_schedule.json"
            
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Save Comprehensive JSON Export File",
                default_filename,
                "JSON Files (*.json);;All Files (*)"
            )
            
            if file_path:
                if not file_path.lower().endswith('.json'):
                    file_path += '.json'
                self.file_path_edit.setText(file_path)
    
    def update_export_button_state(self):
        """Update the export button enabled state."""
        has_file_path = bool(self.file_path_edit.text().strip())
        has_spaces = bool(self.spaces)
        self.export_button.setEnabled(has_file_path and has_spaces)
    
    def start_export(self):
        """Start the export process."""
        export_path = self.file_path_edit.text().strip()
        if not export_path:
            QMessageBox.warning(self, "No Path Selected", 
                              "Please select an export location.")
            return
        
        # Prepare export options
        export_options = {
            'format': 'comprehensive_json' if self.format_combo.currentText() == "Comprehensive JSON" else 'user_templates',
            'indent': self.indent_spinbox.value(),
            'source_file': self.source_file_path,
            'ifc_version': 'IFC4',
            'project_info': self.project_info_widget.get_project_info(),
            'user_data_per_space': self.user_data_widget.get_user_data()
        }
        
        # Show progress and disable controls
        self.progress_frame.setVisible(True)
        self.export_button.setEnabled(False)
        self.browse_button.setEnabled(False)
        
        # Create and start export worker thread
        self.export_thread = QThread()
        self.export_worker = ComprehensiveExportWorker(self.spaces, export_path, export_options)
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