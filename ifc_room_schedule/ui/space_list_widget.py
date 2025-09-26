"""
Space List Widget

Widget for displaying and navigating through IFC spaces.
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QListWidget, 
                            QListWidgetItem, QLabel, QPushButton, QLineEdit,
                            QGroupBox, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from typing import List, Optional

from ..data.space_model import SpaceData


class SpaceListWidget(QWidget):
    """Widget for displaying and navigating through IFC spaces."""
    
    # Signals
    space_selected = pyqtSignal(str)  # Emitted when a space is selected (GUID)
    spaces_loaded = pyqtSignal(int)   # Emitted when spaces are loaded (count)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.spaces = []  # List of SpaceData objects
        self.current_space_guid = None
        
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Title
        title_label = QLabel("Spaces")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Search/filter section
        search_layout = QHBoxLayout()
        search_label = QLabel("Filter:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search spaces...")
        self.search_input.textChanged.connect(self.filter_spaces)
        
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)
        
        # Space list
        self.space_list = QListWidget()
        self.space_list.itemClicked.connect(self.on_space_clicked)
        self.space_list.itemDoubleClicked.connect(self.on_space_double_clicked)
        layout.addWidget(self.space_list)
        
        # Info section
        info_group = QGroupBox("Space Information")
        info_layout = QVBoxLayout()
        info_group.setLayout(info_layout)
        
        self.info_label = QLabel("No space selected")
        self.info_label.setWordWrap(True)
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        info_layout.addWidget(self.info_label)
        
        layout.addWidget(info_group)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh_spaces)
        self.refresh_button.setEnabled(False)
        
        self.clear_button = QPushButton("Clear Selection")
        self.clear_button.clicked.connect(self.clear_selection)
        self.clear_button.setEnabled(False)
        
        button_layout.addWidget(self.refresh_button)
        button_layout.addWidget(self.clear_button)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
    def load_spaces(self, spaces: List[SpaceData]):
        """Load spaces into the list widget."""
        self.spaces = spaces
        self.populate_space_list()
        self.spaces_loaded.emit(len(spaces))
        
        # Enable buttons if we have spaces
        has_spaces = len(spaces) > 0
        self.refresh_button.setEnabled(has_spaces)
        
        if not has_spaces:
            self.clear_selection()
        
    def populate_space_list(self, filter_text: str = ""):
        """Populate the space list with spaces, optionally filtered."""
        self.space_list.clear()
        
        if not self.spaces:
            item = QListWidgetItem("No spaces found")
            item.setFlags(Qt.ItemFlag.NoItemFlags)  # Make it non-selectable
            self.space_list.addItem(item)
            return
        
        # Filter spaces if filter text is provided
        filtered_spaces = self.spaces
        if filter_text:
            filter_lower = filter_text.lower()
            filtered_spaces = [
                space for space in self.spaces
                if (filter_lower in space.name.lower() or
                    filter_lower in space.long_name.lower() or
                    filter_lower in space.object_type.lower() or
                    filter_lower in space.zone_category.lower() or
                    filter_lower in space.number.lower())
            ]
        
        # Add spaces to list
        for space in filtered_spaces:
            item_text = self.format_space_display_text(space)
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, space.guid)  # Store GUID
            
            # Add tooltip with more details
            tooltip = self.format_space_tooltip(space)
            item.setToolTip(tooltip)
            
            self.space_list.addItem(item)
        
        # Show filter results info
        if filter_text and len(filtered_spaces) != len(self.spaces):
            info_item = QListWidgetItem(f"Showing {len(filtered_spaces)} of {len(self.spaces)} spaces")
            info_item.setFlags(Qt.ItemFlag.NoItemFlags)
            info_item.setBackground(self.palette().alternateBase())
            self.space_list.insertItem(0, info_item)
    
    def format_space_display_text(self, space: SpaceData) -> str:
        """Format the display text for a space in the list."""
        # Primary text: number and name
        primary = space.number if space.number != "Unknown" else space.guid[-8:]
        if space.name and space.name != space.number:
            primary += f" - {space.name}"
        
        # Secondary text: long name or object type
        secondary = ""
        if space.long_name and space.long_name != space.name:
            secondary = space.long_name
        elif space.object_type:
            secondary = f"({space.object_type})"
        
        if secondary:
            return f"{primary}\n{secondary}"
        else:
            return primary
    
    def format_space_tooltip(self, space: SpaceData) -> str:
        """Format the tooltip text for a space."""
        tooltip_parts = [
            f"GUID: {space.guid}",
            f"Number: {space.number}",
            f"Name: {space.name}",
            f"Long Name: {space.long_name}",
            f"Type: {space.object_type}",
            f"Category: {space.zone_category}",
            f"Elevation: {space.elevation}m"
        ]
        
        if space.quantities:
            tooltip_parts.append("Quantities:")
            for name, value in space.quantities.items():
                tooltip_parts.append(f"  {name}: {value}")
        
        return "\n".join(tooltip_parts)
    
    def filter_spaces(self, text: str):
        """Filter spaces based on search text."""
        self.populate_space_list(text)
    
    def on_space_clicked(self, item: QListWidgetItem):
        """Handle space item click."""
        guid = item.data(Qt.ItemDataRole.UserRole)
        if guid:  # Only process if item has GUID (not info items)
            self.select_space(guid)
    
    def on_space_double_clicked(self, item: QListWidgetItem):
        """Handle space item double click."""
        guid = item.data(Qt.ItemDataRole.UserRole)
        if guid:
            self.select_space(guid)
            # Could emit additional signal for double-click action
    
    def select_space(self, guid: str):
        """Select a space by GUID."""
        space = self.get_space_by_guid(guid)
        if space:
            self.current_space_guid = guid
            self.update_space_info(space)
            self.clear_button.setEnabled(True)
            self.space_selected.emit(guid)
    
    def get_space_by_guid(self, guid: str) -> Optional[SpaceData]:
        """Get a space by its GUID."""
        for space in self.spaces:
            if space.guid == guid:
                return space
        return None
    
    def update_space_info(self, space: SpaceData):
        """Update the space information display."""
        info_parts = [
            f"<b>Space: {space.number}</b>",
            f"Name: {space.name}",
            f"Long Name: {space.long_name}",
            f"Type: {space.object_type}",
            f"Category: {space.zone_category}",
            f"Elevation: {space.elevation}m",
            f"GUID: {space.guid}"
        ]
        
        if space.description:
            info_parts.append(f"Description: {space.description}")
        
        if space.quantities:
            info_parts.append("<b>Quantities:</b>")
            for name, value in space.quantities.items():
                info_parts.append(f"• {name}: {value}")
        
        if space.surfaces:
            info_parts.append(f"<b>Surfaces:</b> {len(space.surfaces)} found")
        
        if hasattr(space, 'space_boundaries') and space.space_boundaries:
            info_parts.append(f"<b>Space Boundaries:</b> {len(space.space_boundaries)} found")
        
        self.info_label.setText("<br>".join(info_parts))
    
    def clear_selection(self):
        """Clear the current space selection."""
        self.space_list.clearSelection()
        self.current_space_guid = None
        self.info_label.setText("No space selected")
        self.clear_button.setEnabled(False)
    
    def refresh_spaces(self):
        """Refresh the space list display."""
        current_filter = self.search_input.text()
        self.populate_space_list(current_filter)
    
    def get_selected_space_guid(self) -> Optional[str]:
        """Get the GUID of the currently selected space."""
        return self.current_space_guid
    
    def get_selected_space(self) -> Optional[SpaceData]:
        """Get the currently selected space data."""
        if self.current_space_guid:
            return self.get_space_by_guid(self.current_space_guid)
        return None
    
    def get_space_count(self) -> int:
        """Get the total number of spaces."""
        return len(self.spaces)
    
    def select_space_by_index(self, index: int) -> bool:
        """Select a space by its index in the list."""
        if 0 <= index < len(self.spaces):
            space = self.spaces[index]
            self.select_space(space.guid)
            
            # Also select in the list widget
            for i in range(self.space_list.count()):
                item = self.space_list.item(i)
                if item.data(Qt.ItemDataRole.UserRole) == space.guid:
                    self.space_list.setCurrentItem(item)
                    break
            
            return True
        return False