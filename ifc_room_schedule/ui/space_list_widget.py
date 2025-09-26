"""
Space List Widget

Widget for displaying and navigating through IFC spaces.
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QListWidget,
                             QListWidgetItem, QLabel, QPushButton, QLineEdit,
                             QGroupBox)
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
        """Set up the user interface with enhanced styling."""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        self.setLayout(layout)

        # Title with enhanced styling
        title_label = QLabel("🏢 Spaces")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(13)
        title_label.setFont(title_font)
        title_label.setStyleSheet("""
            QLabel {
                color: #495057;
                padding: 8px 12px;
                background-color: #e9ecef;
                border-radius: 6px;
                margin-bottom: 4px;
            }
        """)
        layout.addWidget(title_label)

        # Search/filter section with enhanced styling
        search_container = QWidget()
        search_container.setStyleSheet("""
            QWidget {
                background-color: white;
                border: 1px solid #ced4da;
                border-radius: 6px;
                padding: 4px;
            }
        """)
        search_layout = QHBoxLayout()
        search_layout.setContentsMargins(8, 4, 8, 4)
        search_container.setLayout(search_layout)

        search_label = QLabel("🔍")
        search_label.setStyleSheet("border: none; background: transparent; color: #6c757d;")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search spaces by name, type, or number...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                border: none;
                background: transparent;
                font-size: 13px;
                padding: 4px;
            }
            QLineEdit:focus {
                background-color: #f8f9fa;
            }
        """)
        self.search_input.textChanged.connect(self.filter_spaces)

        # Clear search button
        self.clear_search_button = QPushButton("✕")
        self.clear_search_button.setFixedSize(24, 24)
        self.clear_search_button.setStyleSheet("""
            QPushButton {
                border: none;
                background: transparent;
                color: #6c757d;
                border-radius: 12px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #e9ecef;
                color: #495057;
            }
        """)
        self.clear_search_button.clicked.connect(self.clear_search)
        self.clear_search_button.setVisible(False)

        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input, 1)
        search_layout.addWidget(self.clear_search_button)
        layout.addWidget(search_container)

        # Space list with enhanced styling
        self.space_list = QListWidget()
        self.space_list.setStyleSheet("""
            QListWidget {
                background-color: white;
                border: 1px solid #ced4da;
                border-radius: 6px;
                padding: 4px;
                outline: none;
            }
            QListWidget::item {
                padding: 8px 12px;
                border-bottom: 1px solid #f1f3f4;
                border-radius: 4px;
                margin: 1px;
            }
            QListWidget::item:hover {
                background-color: #f8f9fa;
            }
            QListWidget::item:selected {
                background-color: #007bff;
                color: white;
            }
            QListWidget::item:selected:hover {
                background-color: #0056b3;
            }
        """)
        self.space_list.itemClicked.connect(self.on_space_clicked)
        self.space_list.itemDoubleClicked.connect(self.on_space_double_clicked)
        layout.addWidget(self.space_list, 1)  # Give it most of the space

        # Space count label
        self.count_label = QLabel("0 spaces")
        self.count_label.setStyleSheet("""
            QLabel {
                color: #6c757d;
                font-size: 12px;
                padding: 4px 8px;
                background-color: #f8f9fa;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.count_label)

        # Info section with enhanced styling
        info_group = QGroupBox("📋 Selected Space")
        info_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                color: #495057;
                border: 1px solid #ced4da;
                border-radius: 6px;
                margin-top: 8px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 8px 0 8px;
                background-color: white;
            }
        """)
        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(8, 8, 8, 8)
        info_group.setLayout(info_layout)

        self.info_label = QLabel("No space selected")
        self.info_label.setWordWrap(True)
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.info_label.setStyleSheet("""
            QLabel {
                color: #495057;
                font-size: 12px;
                line-height: 1.4;
                padding: 4px;
                background-color: #f8f9fa;
                border-radius: 4px;
            }
        """)
        info_layout.addWidget(self.info_label)

        layout.addWidget(info_group)

        # Action buttons with enhanced styling
        button_layout = QHBoxLayout()
        button_layout.setSpacing(4)

        self.refresh_button = QPushButton("🔄 Refresh")
        self.refresh_button.clicked.connect(self.refresh_spaces)
        self.refresh_button.setEnabled(False)
        self.refresh_button.setStyleSheet("""
            QPushButton {
                padding: 6px 12px;
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover:enabled {
                background-color: #218838;
            }
            QPushButton:disabled {
                background-color: #6c757d;
                color: #adb5bd;
            }
        """)

        self.clear_button = QPushButton("✕ Clear")
        self.clear_button.clicked.connect(self.clear_selection)
        self.clear_button.setEnabled(False)
        self.clear_button.setStyleSheet("""
            QPushButton {
                padding: 6px 12px;
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 12px;
            }
            QPushButton:hover:enabled {
                background-color: #c82333;
            }
            QPushButton:disabled {
                background-color: #6c757d;
                color: #adb5bd;
            }
        """)

        button_layout.addWidget(self.refresh_button)
        button_layout.addWidget(self.clear_button)
        button_layout.addStretch()

        layout.addLayout(button_layout)

    def load_spaces(self, spaces: List[SpaceData]):
        """Load spaces into the list widget."""
        self.spaces = spaces
        self.populate_space_list()
        self.spaces_loaded.emit(len(spaces))

        # Update count label
        self.update_count_label(len(spaces))

        # Enable buttons if we have spaces
        has_spaces = len(spaces) > 0
        self.refresh_button.setEnabled(has_spaces)

        if not has_spaces:
            self.clear_selection()
            
    def update_count_label(self, count: int, filtered_count: int = None):
        """Update the space count label."""
        if filtered_count is not None and filtered_count != count:
            self.count_label.setText(f"Showing {filtered_count} of {count} spaces")
        else:
            space_text = "space" if count == 1 else "spaces"
            self.count_label.setText(f"{count} {space_text}")
            
    def clear_search(self):
        """Clear the search input."""
        self.search_input.clear()
        self.clear_search_button.setVisible(False)

    def populate_space_list(self, filter_text: str = ""):
        """Populate the space list with spaces, optionally filtered."""
        self.space_list.clear()

        if not self.spaces:
            item = QListWidgetItem("📭 No spaces found")
            item.setFlags(Qt.ItemFlag.NoItemFlags)  # Make it non-selectable
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.space_list.addItem(item)
            self.update_count_label(0)
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

        # Update count label
        if filter_text:
            self.update_count_label(len(self.spaces), len(filtered_spaces))
        else:
            self.update_count_label(len(self.spaces))

        # Add spaces to list
        for space in filtered_spaces:
            item_text = self.format_space_display_text(space)
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, space.guid)  # Store GUID

            # Add tooltip with more details
            tooltip = self.format_space_tooltip(space)
            item.setToolTip(tooltip)

            # Add icon based on space type
            icon = self.get_space_type_icon(space.object_type)
            if icon:
                item.setText(f"{icon} {item_text}")

            self.space_list.addItem(item)

        # Show "no results" message if filtered and empty
        if filter_text and len(filtered_spaces) == 0:
            item = QListWidgetItem("🔍 No spaces match your search")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.space_list.addItem(item)
            
    def get_space_type_icon(self, object_type: str) -> str:
        """Get an icon for the space type."""
        type_icons = {
            "Office": "🏢",
            "Meeting Room": "🤝",
            "Conference Room": "🤝",
            "Corridor": "🚶",
            "Hallway": "🚶",
            "Bathroom": "🚿",
            "Restroom": "🚿",
            "Kitchen": "🍽️",
            "Storage": "📦",
            "Utility": "🔧",
            "Lobby": "🏛️",
            "Reception": "🏛️",
            "Stairway": "🪜",
            "Elevator": "🛗",
            "Parking": "🚗"
        }
        return type_icons.get(object_type, "🏠")

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
        
        # Show/hide clear search button
        self.clear_search_button.setVisible(bool(text))

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
        """Update the space information display with enhanced formatting."""
        icon = self.get_space_type_icon(space.object_type)
        
        info_parts = [
            f"<b>{icon} {space.number}</b>",
            f"<b>Name:</b> {space.name}",
            f"<b>Long Name:</b> {space.long_name}",
            f"<b>Type:</b> {space.object_type}",
            f"<b>Category:</b> {space.zone_category}",
            f"<b>Elevation:</b> {space.elevation}m"
        ]

        if space.description:
            info_parts.append(f"<b>Description:</b> {space.description}")

        # Add quantities in a more compact format
        if space.quantities:
            quantities_text = []
            for name, value in space.quantities.items():
                if isinstance(value, float):
                    quantities_text.append(f"{name}: {value:.2f}")
                else:
                    quantities_text.append(f"{name}: {value}")
            if quantities_text:
                info_parts.append(f"<b>Quantities:</b> {', '.join(quantities_text)}")

        # Add data availability indicators
        data_indicators = []
        if space.surfaces:
            data_indicators.append(f"📐 {len(space.surfaces)} surfaces")
        if hasattr(space, 'space_boundaries') and space.space_boundaries:
            data_indicators.append(f"🔗 {len(space.space_boundaries)} boundaries")
        if hasattr(space, 'relationships') and space.relationships:
            data_indicators.append(f"🔄 {len(space.relationships)} relationships")
            
        if data_indicators:
            info_parts.append("<br><b>Available Data:</b><br>" + "<br>".join(data_indicators))

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
