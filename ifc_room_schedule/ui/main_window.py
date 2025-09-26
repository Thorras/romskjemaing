"""
Main Window for IFC Room Schedule Application

Main window with file dialog functionality for IFC file loading.
"""

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QPushButton, QFileDialog, QMessageBox, 
                            QMenuBar, QStatusBar, QProgressBar, QSplitter,
                            QTabWidget, QToolBar)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QObject
from PyQt6.QtGui import QAction, QIcon
import os
import logging

from ..parser.ifc_file_reader import IfcFileReader
from ..parser.ifc_space_extractor import IfcSpaceExtractor
from ..parser.ifc_surface_extractor import IfcSurfaceExtractor
from .space_list_widget import SpaceListWidget
from .space_detail_widget import SpaceDetailWidget
from .surface_editor_widget import SurfaceEditorWidget


class MainWindow(QMainWindow):
    """Main application window with IFC file loading functionality."""
    
    # Signals
    ifc_file_loaded = pyqtSignal(str)  # Emitted when IFC file is successfully loaded
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.ifc_reader = IfcFileReader()
        self.space_extractor = IfcSpaceExtractor()
        self.surface_extractor = IfcSurfaceExtractor()
        self.current_file_path = None
        self.spaces = []
        
        self.setup_ui()
        self.setup_menu()
        self.setup_toolbar()
        self.setup_status_bar()
        self.connect_signals()
        
        # Ensure initial state is correct
        self.update_file_info()
        
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
        
        # File loading section with enhanced styling
        file_section = QWidget()
        file_section.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                margin: 5px;
            }
        """)
        file_layout = QHBoxLayout()
        file_section.setLayout(file_layout)
        
        # File info with icon-like styling
        self.file_label = QLabel("No IFC file loaded")
        self.file_label.setStyleSheet("""
            QLabel {
                padding: 12px 16px;
                background-color: white;
                border: 1px solid #ced4da;
                border-radius: 4px;
                color: #495057;
                font-size: 13px;
            }
        """)
        file_layout.addWidget(self.file_label, 1)  # Give it more space
        
        self.load_button = QPushButton("Load IFC File")
        self.load_button.clicked.connect(self.load_ifc_file)
        self.load_button.setStyleSheet("""
            QPushButton {
                padding: 12px 24px;
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #004085;
            }
        """)
        file_layout.addWidget(self.load_button)
        
        main_layout.addWidget(file_section)
        
        # Progress bar with enhanced styling
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ced4da;
                border-radius: 4px;
                text-align: center;
                background-color: #f8f9fa;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #28a745;
                border-radius: 3px;
            }
        """)
        main_layout.addWidget(self.progress_bar)
        
        # Create splitter for main content
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #dee2e6;
                width: 2px;
            }
            QSplitter::handle:hover {
                background-color: #adb5bd;
            }
        """)
        main_layout.addWidget(self.main_splitter)
        
        # Left panel: Space list with enhanced container
        left_panel = QWidget()
        left_panel.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border-right: 1px solid #dee2e6;
            }
        """)
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(8, 8, 8, 8)
        left_panel.setLayout(left_layout)
        
        self.space_list_widget = SpaceListWidget()
        left_layout.addWidget(self.space_list_widget)
        
        left_panel.setMinimumWidth(320)
        left_panel.setMaximumWidth(450)
        self.main_splitter.addWidget(left_panel)
        
        # Right panel: Space details and editor with enhanced container
        right_panel = QWidget()
        right_panel.setStyleSheet("""
            QWidget {
                background-color: white;
            }
        """)
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(8, 8, 8, 8)
        right_panel.setLayout(right_layout)
        
        # Create horizontal splitter for details and editor
        self.details_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.details_splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #dee2e6;
                width: 2px;
            }
            QSplitter::handle:hover {
                background-color: #adb5bd;
            }
        """)
        
        # Space details widget
        self.space_detail_widget = SpaceDetailWidget()
        self.details_splitter.addWidget(self.space_detail_widget)
        
        # Surface editor widget
        self.surface_editor_widget = SurfaceEditorWidget()
        self.details_splitter.addWidget(self.surface_editor_widget)
        
        # Set proportions (60% details, 40% editor)
        self.details_splitter.setSizes([600, 400])
        
        right_layout.addWidget(self.details_splitter)
        self.main_splitter.addWidget(right_panel)
        
        # Set splitter proportions (30% left, 70% right)
        self.main_splitter.setSizes([320, 800])
        
        # Initially hide the main content until file is loaded
        self.main_splitter.setVisible(False)
        
        # Enhanced welcome message
        self.welcome_label = QLabel("Welcome to IFC Room Schedule\n\nSelect an IFC file to begin analyzing spaces...")
        self.welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.welcome_label.setStyleSheet("""
            QLabel {
                padding: 60px;
                color: #6c757d;
                font-size: 16px;
                line-height: 1.5;
                background-color: #f8f9fa;
                border: 2px dashed #dee2e6;
                border-radius: 8px;
                margin: 20px;
            }
        """)
        self.welcome_label.setVisible(True)  # Ensure it's visible initially
        main_layout.addWidget(self.welcome_label)
        
    def setup_menu(self):
        """Set up the application menu bar with comprehensive options."""
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar {
                background-color: #f8f9fa;
                border-bottom: 1px solid #dee2e6;
                padding: 4px;
            }
            QMenuBar::item {
                padding: 6px 12px;
                background-color: transparent;
                border-radius: 4px;
            }
            QMenuBar::item:selected {
                background-color: #e9ecef;
            }
        """)
        
        # File menu
        file_menu = menubar.addMenu('&File')
        
        # Open action with enhanced properties
        open_action = QAction('&Open IFC File...', self)
        open_action.setShortcut('Ctrl+O')
        open_action.setStatusTip('Open an IFC file for processing')
        open_action.triggered.connect(self.load_ifc_file)
        file_menu.addAction(open_action)
        
        # Recent files submenu (enhanced for future implementation)
        recent_menu = file_menu.addMenu('&Recent Files')
        recent_menu.setEnabled(False)  # Disabled for now
        recent_menu.setStatusTip('Recently opened IFC files')
        
        file_menu.addSeparator()
        
        # Close action
        close_action = QAction('&Close File', self)
        close_action.setShortcut('Ctrl+W')
        close_action.setStatusTip('Close the current IFC file')
        close_action.triggered.connect(self.close_file)
        close_action.setEnabled(False)  # Initially disabled
        file_menu.addAction(close_action)
        self.close_action = close_action
        
        file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction('E&xit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.setStatusTip('Exit the application')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu with enhanced options
        view_menu = menubar.addMenu('&View')
        
        # Refresh action
        refresh_action = QAction('&Refresh', self)
        refresh_action.setShortcut('F5')
        refresh_action.setStatusTip('Refresh the current view and reload space data')
        refresh_action.triggered.connect(self.refresh_view)
        refresh_action.setEnabled(False)
        view_menu.addAction(refresh_action)
        self.refresh_action = refresh_action
        
        view_menu.addSeparator()
        
        # Panel visibility actions
        show_spaces_action = QAction('Show &Spaces Panel', self)
        show_spaces_action.setCheckable(True)
        show_spaces_action.setChecked(True)
        show_spaces_action.setStatusTip('Show or hide the spaces navigation panel')
        show_spaces_action.triggered.connect(self.toggle_spaces_panel)
        view_menu.addAction(show_spaces_action)
        self.show_spaces_action = show_spaces_action
        
        # Zoom actions for future implementation
        view_menu.addSeparator()
        zoom_in_action = QAction('Zoom &In', self)
        zoom_in_action.setShortcut('Ctrl++')
        zoom_in_action.setEnabled(False)  # Future implementation
        view_menu.addAction(zoom_in_action)
        
        zoom_out_action = QAction('Zoom &Out', self)
        zoom_out_action.setShortcut('Ctrl+-')
        zoom_out_action.setEnabled(False)  # Future implementation
        view_menu.addAction(zoom_out_action)
        
        # Navigation menu
        nav_menu = menubar.addMenu('&Navigate')
        
        # Space navigation actions
        next_space_action = QAction('&Next Space', self)
        next_space_action.setShortcut('Ctrl+Right')
        next_space_action.setStatusTip('Navigate to the next space')
        next_space_action.triggered.connect(self.navigate_next_space)
        next_space_action.setEnabled(False)
        nav_menu.addAction(next_space_action)
        self.next_space_action = next_space_action
        
        prev_space_action = QAction('&Previous Space', self)
        prev_space_action.setShortcut('Ctrl+Left')
        prev_space_action.setStatusTip('Navigate to the previous space')
        prev_space_action.triggered.connect(self.navigate_previous_space)
        prev_space_action.setEnabled(False)
        nav_menu.addAction(prev_space_action)
        self.prev_space_action = prev_space_action
        
        nav_menu.addSeparator()
        
        # Go to space action
        goto_space_action = QAction('&Go to Space...', self)
        goto_space_action.setShortcut('Ctrl+G')
        goto_space_action.setStatusTip('Go to a specific space by number or name')
        goto_space_action.triggered.connect(self.show_goto_space_dialog)
        goto_space_action.setEnabled(False)
        nav_menu.addAction(goto_space_action)
        self.goto_space_action = goto_space_action
        
        # Tools menu with enhanced export options
        tools_menu = menubar.addMenu('&Tools')
        
        # Export submenu
        export_menu = tools_menu.addMenu('&Export')
        
        # JSON export
        export_json_action = QAction('Export as &JSON...', self)
        export_json_action.setShortcut('Ctrl+E')
        export_json_action.setStatusTip('Export space data to JSON file')
        export_json_action.setEnabled(False)
        export_json_action.triggered.connect(self.export_json)
        export_menu.addAction(export_json_action)
        self.export_action = export_json_action
        
        # Additional export formats (for future implementation)
        export_csv_action = QAction('Export as &CSV...', self)
        export_csv_action.setStatusTip('Export space data to CSV file')
        export_csv_action.setEnabled(False)
        export_menu.addAction(export_csv_action)
        
        export_excel_action = QAction('Export as &Excel...', self)
        export_excel_action.setStatusTip('Export space data to Excel file')
        export_excel_action.setEnabled(False)
        export_menu.addAction(export_excel_action)
        
        tools_menu.addSeparator()
        
        # Validation tools
        validate_action = QAction('&Validate Data', self)
        validate_action.setShortcut('Ctrl+Shift+V')
        validate_action.setStatusTip('Validate current space data for completeness')
        validate_action.triggered.connect(self.validate_data)
        validate_action.setEnabled(False)
        tools_menu.addAction(validate_action)
        self.validate_action = validate_action
        
        # Help menu
        help_menu = menubar.addMenu('&Help')
        
        # User guide action
        user_guide_action = QAction('&User Guide', self)
        user_guide_action.setShortcut('F1')
        user_guide_action.setStatusTip('Open the user guide')
        user_guide_action.triggered.connect(self.show_user_guide)
        help_menu.addAction(user_guide_action)
        
        help_menu.addSeparator()
        
        # About action
        about_action = QAction('&About', self)
        about_action.setStatusTip('About IFC Room Schedule application')
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def setup_toolbar(self):
        """Set up the application toolbar with comprehensive tools."""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        toolbar.setStyleSheet("""
            QToolBar {
                background-color: #f8f9fa;
                border-bottom: 1px solid #dee2e6;
                spacing: 4px;
                padding: 4px;
            }
            QToolButton {
                background-color: transparent;
                border: 1px solid transparent;
                border-radius: 4px;
                padding: 6px;
                margin: 2px;
                min-width: 60px;
            }
            QToolButton:hover {
                background-color: #e9ecef;
                border-color: #adb5bd;
            }
            QToolButton:pressed {
                background-color: #dee2e6;
            }
            QToolButton:disabled {
                color: #6c757d;
                background-color: transparent;
            }
        """)
        self.addToolBar(toolbar)
        
        # File operations section
        open_action = QAction('📁\nOpen', self)
        open_action.setStatusTip('Open an IFC file for processing')
        open_action.triggered.connect(self.load_ifc_file)
        toolbar.addAction(open_action)
        
        close_action = QAction('❌\nClose', self)
        close_action.setStatusTip('Close the current IFC file')
        close_action.triggered.connect(self.close_file)
        close_action.setEnabled(False)
        toolbar.addAction(close_action)
        self.toolbar_close_action = close_action
        
        toolbar.addSeparator()
        
        # View operations section
        refresh_action = QAction('🔄\nRefresh', self)
        refresh_action.setStatusTip('Refresh the current view and reload space data')
        refresh_action.triggered.connect(self.refresh_view)
        refresh_action.setEnabled(False)
        toolbar.addAction(refresh_action)
        self.toolbar_refresh_action = refresh_action
        
        # Navigation section
        toolbar.addSeparator()
        
        prev_action = QAction('⬅️\nPrevious', self)
        prev_action.setStatusTip('Navigate to the previous space')
        prev_action.triggered.connect(self.navigate_previous_space)
        prev_action.setEnabled(False)
        toolbar.addAction(prev_action)
        self.toolbar_prev_action = prev_action
        
        next_action = QAction('➡️\nNext', self)
        next_action.setStatusTip('Navigate to the next space')
        next_action.triggered.connect(self.navigate_next_space)
        next_action.setEnabled(False)
        toolbar.addAction(next_action)
        self.toolbar_next_action = next_action
        
        # Tools section
        toolbar.addSeparator()
        
        validate_action = QAction('✅\nValidate', self)
        validate_action.setStatusTip('Validate current space data for completeness')
        validate_action.triggered.connect(self.validate_data)
        validate_action.setEnabled(False)
        toolbar.addAction(validate_action)
        self.toolbar_validate_action = validate_action
        
        export_action = QAction('💾\nExport', self)
        export_action.setStatusTip('Export space data to JSON file')
        export_action.triggered.connect(self.export_json)
        export_action.setEnabled(False)
        toolbar.addAction(export_action)
        self.toolbar_export_action = export_action
        
        # Add spacer to push status info to the right
        spacer = QWidget()
        from PyQt6.QtWidgets import QSizePolicy
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar.addWidget(spacer)
        
        # Status information in toolbar
        self.toolbar_status_label = QLabel("Ready")
        self.toolbar_status_label.setStyleSheet("""
            QLabel {
                color: #495057;
                font-size: 12px;
                padding: 4px 8px;
                background-color: #e9ecef;
                border-radius: 4px;
                margin: 2px;
            }
        """)
        toolbar.addWidget(self.toolbar_status_label)
        
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
        
        # Connect surface editor signals
        self.surface_editor_widget.surface_description_changed.connect(self.on_surface_description_changed)
        self.surface_editor_widget.boundary_description_changed.connect(self.on_boundary_description_changed)
        
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
                self.update_ui_state(True)  # Enable file-related actions
                self.status_bar.showMessage("File loaded successfully. Extracting spaces...")
                
                # Extract spaces
                self.extract_spaces()
                
                self.ifc_file_loaded.emit(file_path)
            else:
                self.show_error_message("File Loading Error", load_message)
                self.status_bar.showMessage("File loading failed")
                self.update_ui_state(False)  # Keep actions disabled
                
        except Exception as e:
            self.show_error_message("Unexpected Error", f"An unexpected error occurred: {str(e)}")
            self.status_bar.showMessage("Error loading file")
        
        finally:
            self.progress_bar.setVisible(False)
    
    def update_file_info(self):
        """Update the UI with information about the loaded file."""
        if not self.ifc_reader.is_loaded() or not self.current_file_path:
            self.file_label.setText("No IFC file loaded")
            self.welcome_label.setText("Welcome to IFC Room Schedule\n\nSelect an IFC file to begin analyzing spaces...")
            self.main_splitter.setVisible(False)
            self.welcome_label.setVisible(True)
            self.update_ui_state(False)
            return
        
        # Update file path display
        file_name = os.path.basename(self.current_file_path)
        file_size = self.get_file_size_string(self.current_file_path)
        self.file_label.setText(f"📄 {file_name} ({file_size})")
        self.update_ui_state(True)
        
    def get_file_size_string(self, file_path: str) -> str:
        """Get human-readable file size string."""
        try:
            size_bytes = os.path.getsize(file_path)
            if size_bytes < 1024:
                return f"{size_bytes} B"
            elif size_bytes < 1024 * 1024:
                return f"{size_bytes / 1024:.1f} KB"
            else:
                return f"{size_bytes / (1024 * 1024):.1f} MB"
        except:
            return "Unknown size"
        
    def extract_spaces(self):
        """Extract spaces from the loaded IFC file."""
        try:
            # Set the IFC file for the space extractor
            self.space_extractor.set_ifc_file(self.ifc_reader.get_ifc_file())
            self.surface_extractor.set_ifc_file(self.ifc_reader.get_ifc_file())
            
            # Extract spaces
            self.spaces = self.space_extractor.extract_spaces()
            
            if self.spaces:
                # Extract surfaces for each space
                self.status_bar.showMessage("Extracting surface data...")
                self.extract_surfaces_for_spaces()
                
                # Load spaces into the list widget
                self.space_list_widget.load_spaces(self.spaces)
                
                # Show the main interface
                self.main_splitter.setVisible(True)
                self.welcome_label.setVisible(False)
                
                # Update UI state with spaces loaded
                self.update_ui_state(True)
                
                total_surfaces = sum(len(space.surfaces) for space in self.spaces)
                self.status_bar.showMessage(f"Successfully loaded {len(self.spaces)} spaces with {total_surfaces} surfaces")
            else:
                self.show_info_message("No Spaces Found", 
                                     "No spaces were found in the IFC file. The file may not contain space data.")
                self.status_bar.showMessage("No spaces found in file")
                # Update UI state - file loaded but no spaces
                self.update_ui_state(True)
                
        except Exception as e:
            self.show_error_message("Space Extraction Error", 
                                  f"Error extracting spaces from IFC file: {str(e)}")
            self.status_bar.showMessage("Space extraction failed")
            self.update_ui_state(False)
    
    def extract_surfaces_for_spaces(self):
        """Extract surface data for all loaded spaces."""
        try:
            for i, space in enumerate(self.spaces):
                try:
                    # Update progress
                    self.status_bar.showMessage(f"Extracting surfaces for space {i+1}/{len(self.spaces)}: {space.number}")
                    
                    # Extract surfaces for this space
                    surfaces = self.surface_extractor.extract_surfaces_for_space(space.guid)
                    
                    # Add surfaces to the space
                    for surface in surfaces:
                        space.add_surface(surface)
                    
                    # Validate surfaces
                    if surfaces:
                        is_valid, messages = self.surface_extractor.validate_surfaces(surfaces)
                        if not is_valid:
                            self.logger.warning(f"Surface validation issues for space {space.guid}: {messages}")
                    
                except Exception as e:
                    self.logger.error(f"Error extracting surfaces for space {space.guid}: {e}")
                    # Continue with other spaces
                    continue
                    
        except Exception as e:
            self.logger.error(f"Error in surface extraction process: {e}")
            raise
    
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
            
            # Set space context in surface editor and show empty state
            self.surface_editor_widget.set_space_context(selected_space.guid)
            self.surface_editor_widget.show_empty_state()
            
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
        
        # Find the surface data
        current_space = self.space_detail_widget.get_current_space()
        if current_space:
            for surface in current_space.surfaces:
                if surface.id == surface_id:
                    # Prepare surface data for editor
                    surface_data = {
                        'type': surface.type,
                        'area': surface.area,
                        'material': surface.material,
                        'user_description': surface.user_description
                    }
                    
                    # Set space context and start editing
                    self.surface_editor_widget.set_space_context(current_space.guid)
                    self.surface_editor_widget.edit_surface(surface_id, surface_data)
                    break
        
    def on_boundary_selected(self, boundary_guid: str):
        """Handle space boundary selection from space details."""
        self.status_bar.showMessage(f"Selected boundary: {boundary_guid}")
        
        # Find the boundary data
        current_space = self.space_detail_widget.get_current_space()
        if current_space and hasattr(current_space, 'space_boundaries'):
            for boundary in current_space.space_boundaries:
                if boundary.guid == boundary_guid:
                    # Prepare boundary data for editor
                    boundary_data = {
                        'display_label': boundary.display_label,
                        'physical_or_virtual_boundary': boundary.physical_or_virtual_boundary,
                        'boundary_orientation': boundary.boundary_orientation,
                        'calculated_area': boundary.calculated_area,
                        'related_building_element_type': boundary.related_building_element_type,
                        'user_description': boundary.user_description
                    }
                    
                    # Set space context and start editing
                    self.surface_editor_widget.set_space_context(current_space.guid)
                    self.surface_editor_widget.edit_boundary(boundary_guid, boundary_data)
                    break
                    
    def on_surface_description_changed(self, surface_id: str, description: str):
        """Handle surface description changes from the editor."""
        # Find and update the surface
        current_space = self.space_detail_widget.get_current_space()
        if current_space:
            for surface in current_space.surfaces:
                if surface.id == surface_id:
                    surface.user_description = description
                    # Mark space as processed
                    current_space.processed = True
                    # Refresh the space details view
                    self.space_detail_widget.update_surfaces_tab()
                    self.logger.info(f"Updated surface description for {surface_id}")
                    break
                    
    def on_boundary_description_changed(self, boundary_guid: str, description: str):
        """Handle boundary description changes from the editor."""
        # Find and update the boundary
        current_space = self.space_detail_widget.get_current_space()
        if current_space and hasattr(current_space, 'space_boundaries'):
            for boundary in current_space.space_boundaries:
                if boundary.guid == boundary_guid:
                    boundary.user_description = description
                    # Mark space as processed
                    current_space.processed = True
                    # Refresh the space details view
                    self.space_detail_widget.update_boundaries_tab()
                    self.logger.info(f"Updated boundary description for {boundary_guid}")
                    break
        
    def get_current_spaces(self):
        """Get the currently loaded spaces."""
        return self.spaces
        
    def refresh_view(self):
        """Refresh the current view."""
        if self.ifc_reader.is_loaded():
            # Refresh space list
            self.space_list_widget.refresh_spaces()
            
            # Refresh current space details if one is selected
            current_space = self.space_list_widget.get_selected_space()
            if current_space:
                self.space_detail_widget.display_space(current_space)
                
            self.status_bar.showMessage("View refreshed")
        else:
            self.status_bar.showMessage("No file loaded to refresh")
            
    def toggle_spaces_panel(self, checked: bool):
        """Toggle the visibility of the spaces panel."""
        self.space_list_widget.setVisible(checked)
        if checked:
            self.status_bar.showMessage("Spaces panel shown")
        else:
            self.status_bar.showMessage("Spaces panel hidden")
            
    def show_about(self):
        """Show the about dialog."""
        about_text = """
        <h3>IFC Room Schedule Application</h3>
        <p>Version 1.0</p>
        <p>A desktop application for importing IFC files, analyzing spatial data, 
        and generating structured room schedules.</p>
        <p>Built with Python and PyQt6</p>
        <p>Uses IfcOpenShell for IFC file processing</p>
        """
        
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.setWindowTitle("About IFC Room Schedule")
        msg_box.setText(about_text)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.exec()
        
    def navigate_next_space(self):
        """Navigate to the next space in the list."""
        if not self.spaces:
            return
            
        current_guid = self.space_list_widget.get_selected_space_guid()
        if not current_guid:
            # Select first space if none selected
            if self.spaces:
                self.space_list_widget.select_space_by_index(0)
            return
            
        # Find current space index
        current_index = -1
        for i, space in enumerate(self.spaces):
            if space.guid == current_guid:
                current_index = i
                break
                
        # Navigate to next space
        if current_index >= 0 and current_index < len(self.spaces) - 1:
            self.space_list_widget.select_space_by_index(current_index + 1)
            self.status_bar.showMessage(f"Navigated to next space")
        else:
            self.status_bar.showMessage("Already at last space")
            
    def navigate_previous_space(self):
        """Navigate to the previous space in the list."""
        if not self.spaces:
            return
            
        current_guid = self.space_list_widget.get_selected_space_guid()
        if not current_guid:
            # Select last space if none selected
            if self.spaces:
                self.space_list_widget.select_space_by_index(len(self.spaces) - 1)
            return
            
        # Find current space index
        current_index = -1
        for i, space in enumerate(self.spaces):
            if space.guid == current_guid:
                current_index = i
                break
                
        # Navigate to previous space
        if current_index > 0:
            self.space_list_widget.select_space_by_index(current_index - 1)
            self.status_bar.showMessage(f"Navigated to previous space")
        else:
            self.status_bar.showMessage("Already at first space")
            
    def show_goto_space_dialog(self):
        """Show dialog to go to a specific space."""
        from PyQt6.QtWidgets import QInputDialog
        
        if not self.spaces:
            self.show_info_message("No Spaces", "No spaces are currently loaded.")
            return
            
        # Create list of space identifiers
        space_options = []
        for space in self.spaces:
            identifier = f"{space.number} - {space.name}" if space.name != space.number else space.number
            space_options.append(identifier)
            
        # Show selection dialog
        item, ok = QInputDialog.getItem(
            self, 
            "Go to Space", 
            "Select a space to navigate to:",
            space_options,
            0,
            False
        )
        
        if ok and item:
            # Find the selected space
            selected_index = space_options.index(item)
            self.space_list_widget.select_space_by_index(selected_index)
            self.status_bar.showMessage(f"Navigated to space: {item}")
            
    def validate_data(self):
        """Validate current space data for completeness."""
        if not self.spaces:
            self.show_info_message("No Data", "No spaces are currently loaded to validate.")
            return
            
        # Perform validation checks
        validation_results = []
        total_spaces = len(self.spaces)
        spaces_with_surfaces = 0
        spaces_with_boundaries = 0
        spaces_with_descriptions = 0
        
        for space in self.spaces:
            if space.surfaces:
                spaces_with_surfaces += 1
            if hasattr(space, 'space_boundaries') and space.space_boundaries:
                spaces_with_boundaries += 1
            if any(surface.user_description for surface in space.surfaces):
                spaces_with_descriptions += 1
                
        # Generate validation report
        validation_results.append(f"Total Spaces: {total_spaces}")
        validation_results.append(f"Spaces with Surfaces: {spaces_with_surfaces}")
        validation_results.append(f"Spaces with Boundaries: {spaces_with_boundaries}")
        validation_results.append(f"Spaces with Descriptions: {spaces_with_descriptions}")
        
        # Calculate completeness percentage
        completeness = (spaces_with_descriptions / total_spaces * 100) if total_spaces > 0 else 0
        validation_results.append(f"\nData Completeness: {completeness:.1f}%")
        
        # Show validation results
        self.show_info_message("Data Validation Results", "\n".join(validation_results))
        
    def export_json(self):
        """Export space data to JSON file."""
        # This will be implemented in a future task
        self.show_info_message("Export", "JSON export functionality will be implemented in task 9.")
        
    def show_user_guide(self):
        """Show the user guide."""
        guide_text = """
        <h3>IFC Room Schedule - User Guide</h3>
        
        <h4>Getting Started:</h4>
        <ol>
        <li><b>Load IFC File:</b> Use File → Open IFC File or click the Load button</li>
        <li><b>Navigate Spaces:</b> Select spaces from the left panel or use navigation buttons</li>
        <li><b>View Details:</b> Space properties, surfaces, and boundaries appear in the right panel</li>
        <li><b>Add Descriptions:</b> Click on surfaces or boundaries to add custom descriptions</li>
        <li><b>Export Data:</b> Use Tools → Export to save your work</li>
        </ol>
        
        <h4>Keyboard Shortcuts:</h4>
        <ul>
        <li><b>Ctrl+O:</b> Open IFC file</li>
        <li><b>Ctrl+W:</b> Close current file</li>
        <li><b>F5:</b> Refresh view</li>
        <li><b>Ctrl+Left/Right:</b> Navigate between spaces</li>
        <li><b>Ctrl+G:</b> Go to specific space</li>
        <li><b>Ctrl+E:</b> Export data</li>
        </ul>
        
        <h4>Tips:</h4>
        <ul>
        <li>Use the search box to filter spaces by name or type</li>
        <li>Validate your data before exporting to ensure completeness</li>
        <li>Space boundaries provide detailed geometric information</li>
        </ul>
        """
        
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.setWindowTitle("User Guide")
        msg_box.setText(guide_text)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.exec()
        
    def update_ui_state(self, file_loaded: bool):
        """Update UI state based on whether a file is loaded."""
        has_spaces = file_loaded and len(self.spaces) > 0
        
        # Update menu actions
        self.close_action.setEnabled(file_loaded)
        self.refresh_action.setEnabled(file_loaded)
        self.export_action.setEnabled(has_spaces)
        self.next_space_action.setEnabled(has_spaces)
        self.prev_space_action.setEnabled(has_spaces)
        self.goto_space_action.setEnabled(has_spaces)
        self.validate_action.setEnabled(has_spaces)
        
        # Update toolbar actions
        self.toolbar_close_action.setEnabled(file_loaded)
        self.toolbar_refresh_action.setEnabled(file_loaded)
        self.toolbar_export_action.setEnabled(has_spaces)
        self.toolbar_next_action.setEnabled(has_spaces)
        self.toolbar_prev_action.setEnabled(has_spaces)
        self.toolbar_validate_action.setEnabled(has_spaces)
        
        # Update toolbar status
        if file_loaded:
            if has_spaces:
                self.toolbar_status_label.setText(f"{len(self.spaces)} spaces loaded")
            else:
                self.toolbar_status_label.setText("File loaded, no spaces found")
        else:
            self.toolbar_status_label.setText("Ready")