"""
Main Window for IFC Room Schedule Application

Main window with file dialog functionality for IFC file loading.
"""

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QPushButton, QFileDialog, QMessageBox, 
                            QMenuBar, QStatusBar, QProgressBar, QSplitter,
                            QTabWidget)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QObject
from PyQt6.QtGui import QAction
import os

from ..parser.ifc_file_reader import IfcFileReader
from ..parser.ifc_space_extractor import IfcSpaceExtractor
from .space_list_widget import SpaceListWidget
from .space_detail_widget import SpaceDetailWidget


class MainWindow(QMainWindow):
    """Main application window with IFC file loading functionality."""
    
    # Signals
    ifc_file_loaded = pyqtSignal(str)  # Emitted when IFC file is successfully loaded
    
    def __init__(self):
        super().__init__()
        self.ifc_reader = IfcFileReader()
        self.space_extractor = IfcSpaceExtractor()
        self.current_file_path = None
        self.spaces = []
        
        self.setup_ui()
        self.setup_menu()
        self.setup_status_bar()
        self.connect_signals()
        
    def setup_ui(self):
        """Set up the main user interface."""
        self.setWindowTitle("IFC Room Schedule")
        self.setGeometry(100, 100, 1400, 800)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
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
        
        # Progress bar (initially hidden)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        # Create splitter for main content
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(self.main_splitter)
        
        # Left panel: Space list
        self.space_list_widget = SpaceListWidget()
        self.space_list_widget.setMinimumWidth(300)
        self.space_list_widget.setMaximumWidth(400)
        self.main_splitter.addWidget(self.space_list_widget)
        
        # Right panel: Space details
        self.space_detail_widget = SpaceDetailWidget()
        self.main_splitter.addWidget(self.space_detail_widget)
        
        # Set splitter proportions
        self.main_splitter.setSizes([300, 800])
        
        # Initially hide the main content until file is loaded
        self.main_splitter.setVisible(False)
        
        # Welcome message
        self.welcome_label = QLabel("Select an IFC file to begin...")
        self.welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.welcome_label.setStyleSheet("padding: 40px; color: #666; font-size: 14px;")
        main_layout.addWidget(self.welcome_label)
        
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
        
    def connect_signals(self):
        """Connect widget signals."""
        # Connect space list signals
        self.space_list_widget.space_selected.connect(self.on_space_selected)
        self.space_list_widget.spaces_loaded.connect(self.on_spaces_loaded)
        
        # Connect space detail signals
        self.space_detail_widget.surface_selected.connect(self.on_surface_selected)
        self.space_detail_widget.boundary_selected.connect(self.on_boundary_selected)
        
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
                self.status_bar.showMessage("File loaded successfully. Extracting spaces...")
                
                # Extract spaces
                self.extract_spaces()
                
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
            self.welcome_label.setText("Select an IFC file to begin...")
            self.main_splitter.setVisible(False)
            self.welcome_label.setVisible(True)
            return
        
        # Update file path display
        file_name = os.path.basename(self.current_file_path)
        self.file_label.setText(f"Loaded: {file_name}")
        
    def extract_spaces(self):
        """Extract spaces from the loaded IFC file."""
        try:
            # Set the IFC file for the space extractor
            self.space_extractor.set_ifc_file(self.ifc_reader.get_ifc_file())
            
            # Extract spaces
            self.spaces = self.space_extractor.extract_spaces()
            
            if self.spaces:
                # Load spaces into the list widget
                self.space_list_widget.load_spaces(self.spaces)
                
                # Show the main interface
                self.main_splitter.setVisible(True)
                self.welcome_label.setVisible(False)
                
                self.status_bar.showMessage(f"Successfully loaded {len(self.spaces)} spaces")
            else:
                self.show_info_message("No Spaces Found", 
                                     "No spaces were found in the IFC file. The file may not contain space data.")
                self.status_bar.showMessage("No spaces found in file")
                
        except Exception as e:
            self.show_error_message("Space Extraction Error", 
                                  f"Error extracting spaces from IFC file: {str(e)}")
            self.status_bar.showMessage("Space extraction failed")
    
    def close_file(self):
        """Close the currently loaded IFC file."""
        if self.ifc_reader.is_loaded():
            self.ifc_reader.close_file()
            self.current_file_path = None
            self.spaces = []
            
            # Clear UI
            self.space_list_widget.load_spaces([])
            self.space_detail_widget.clear_selection()
            
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
        
    def get_space_extractor(self) -> IfcSpaceExtractor:
        """Get the space extractor instance."""
        return self.space_extractor
        
    def on_space_selected(self, space_guid: str):
        """Handle space selection from the space list."""
        # Find the space by GUID
        selected_space = None
        for space in self.spaces:
            if space.guid == space_guid:
                selected_space = space
                break
                
        if selected_space:
            # Display space details
            self.space_detail_widget.display_space(selected_space)
            self.status_bar.showMessage(f"Selected space: {selected_space.number} - {selected_space.name}")
        else:
            self.status_bar.showMessage("Space not found")
            
    def on_spaces_loaded(self, count: int):
        """Handle spaces loaded event."""
        if count > 0:
            self.status_bar.showMessage(f"Loaded {count} spaces")
        else:
            self.status_bar.showMessage("No spaces loaded")
            
    def on_surface_selected(self, surface_id: str):
        """Handle surface selection from space details."""
        self.status_bar.showMessage(f"Selected surface: {surface_id}")
        # TODO: Implement surface editing functionality
        
    def on_boundary_selected(self, boundary_guid: str):
        """Handle space boundary selection from space details."""
        self.status_bar.showMessage(f"Selected boundary: {boundary_guid}")
        # TODO: Implement boundary editing functionality
        
    def get_current_spaces(self):
        """Get the currently loaded spaces."""
        return self.spaces