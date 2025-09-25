"""
Main Window for IFC Room Schedule Application

Main window with file dialog functionality for IFC file loading.
"""

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QPushButton, QFileDialog, QMessageBox, 
                            QMenuBar, QStatusBar, QProgressBar)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction
import os

from ..parser.ifc_file_reader import IfcFileReader


class MainWindow(QMainWindow):
    """Main application window with IFC file loading functionality."""
    
    # Signals
    ifc_file_loaded = pyqtSignal(str)  # Emitted when IFC file is successfully loaded
    
    def __init__(self):
        super().__init__()
        self.ifc_reader = IfcFileReader()
        self.current_file_path = None
        
        self.setup_ui()
        self.setup_menu()
        self.setup_status_bar()
        
    def setup_ui(self):
        """Set up the main user interface."""
        self.setWindowTitle("IFC Room Schedule")
        self.setGeometry(100, 100, 1000, 700)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Title section
        title_label = QLabel("IFC Room Schedule Application")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 20px;")
        main_layout.addWidget(title_label)
        
        # File loading section
        file_section = QWidget()
        file_layout = QHBoxLayout()
        file_section.setLayout(file_layout)
        
        self.file_label = QLabel("No IFC file loaded")
        self.file_label.setStyleSheet("padding: 10px; border: 1px solid #ccc; border-radius: 4px;")
        file_layout.addWidget(self.file_label)
        
        self.load_button = QPushButton("Load IFC File")
        self.load_button.clicked.connect(self.load_ifc_file)
        self.load_button.setStyleSheet("padding: 10px; font-weight: bold;")
        file_layout.addWidget(self.load_button)
        
        main_layout.addWidget(file_section)
        
        # File info section
        self.info_label = QLabel("Select an IFC file to begin...")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_label.setStyleSheet("padding: 20px; color: #666;")
        main_layout.addWidget(self.info_label)
        
        # Progress bar (initially hidden)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        # Spacer
        main_layout.addStretch()
        
    def setup_menu(self):
        """Set up the application menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        # Open action
        open_action = QAction('Open IFC File...', self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.load_ifc_file)
        file_menu.addAction(open_action)
        
        # Close action
        close_action = QAction('Close File', self)
        close_action.setShortcut('Ctrl+W')
        close_action.triggered.connect(self.close_file)
        file_menu.addAction(close_action)
        
        file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction('Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
    def setup_status_bar(self):
        """Set up the status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready to load IFC file...")
        
    def load_ifc_file(self):
        """Open file dialog and load selected IFC file."""
        file_dialog = QFileDialog(self)
        file_dialog.setWindowTitle("Select IFC File")
        file_dialog.setNameFilter("IFC Files (*.ifc *.ifcxml);;All Files (*)")
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        
        if file_dialog.exec():
            file_paths = file_dialog.selectedFiles()
            if file_paths:
                self.process_ifc_file(file_paths[0])
    
    def process_ifc_file(self, file_path: str):
        """Process the selected IFC file."""
        self.status_bar.showMessage("Loading IFC file...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        
        try:
            # First validate the file
            is_valid, validation_message = self.ifc_reader.validate_file(file_path)
            
            if not is_valid:
                self.show_error_message("File Validation Error", validation_message)
                self.progress_bar.setVisible(False)
                self.status_bar.showMessage("File validation failed")
                return
            
            # Load the file
            success, load_message = self.ifc_reader.load_file(file_path)
            
            if success:
                self.current_file_path = file_path
                self.update_file_info()
                self.status_bar.showMessage(load_message)
                self.ifc_file_loaded.emit(file_path)
            else:
                self.show_error_message("File Loading Error", load_message)
                self.status_bar.showMessage("File loading failed")
                
        except Exception as e:
            self.show_error_message("Unexpected Error", f"An unexpected error occurred: {str(e)}")
            self.status_bar.showMessage("Error loading file")
        
        finally:
            self.progress_bar.setVisible(False)
    
    def update_file_info(self):
        """Update the UI with information about the loaded file."""
        if not self.ifc_reader.is_loaded():
            self.file_label.setText("No IFC file loaded")
            self.info_label.setText("Select an IFC file to begin...")
            return
        
        # Update file path display
        file_name = os.path.basename(self.current_file_path)
        self.file_label.setText(f"Loaded: {file_name}")
        
        # Get and display file information
        file_info = self.ifc_reader.get_file_info()
        if file_info and 'error' not in file_info:
            info_text = f"""
            <b>File Information:</b><br>
            Schema: {file_info.get('schema', 'Unknown')}<br>
            Spaces Found: {file_info.get('spaces_count', 0)}<br>
            Total Entities: {file_info.get('total_entities', 0)}<br>
            Building Elements: {file_info.get('building_elements', 0)}
            """
            
            if 'project_name' in file_info:
                info_text += f"<br>Project: {file_info['project_name']}"
            
            if 'created_by' in file_info:
                info_text += f"<br>Created by: {file_info['created_by']}"
                
            self.info_label.setText(info_text)
        else:
            error_msg = file_info.get('error', 'Unknown error') if file_info else 'Could not get file information'
            self.info_label.setText(f"Error getting file information: {error_msg}")
    
    def close_file(self):
        """Close the currently loaded IFC file."""
        if self.ifc_reader.is_loaded():
            self.ifc_reader.close_file()
            self.current_file_path = None
            self.update_file_info()
            self.status_bar.showMessage("File closed")
    
    def show_error_message(self, title: str, message: str):
        """Show an error message dialog."""
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.exec()
    
    def show_info_message(self, title: str, message: str):
        """Show an information message dialog."""
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.exec()
    
    def get_ifc_reader(self) -> IfcFileReader:
        """Get the IFC file reader instance."""
        return self.ifc_reader