"""
Space List Widget

Widget for displaying and navigating through IFC spaces.
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QListWidget,
                             QListWidgetItem, QLabel, QPushButton, QLineEdit,
                             QGroupBox, QComboBox, QCheckBox, QMenu)
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtGui import QFont, QIcon, QAction
from typing import List, Optional, Dict

from ..data.space_model import SpaceData
from ..visualization.geometry_models import FloorLevel


class SpaceListWidget(QWidget):
    """Widget for displaying and navigating through IFC spaces."""

    # Signals
    space_selected = pyqtSignal(str)  # Emitted when a space is selected (GUID)
    spaces_loaded = pyqtSignal(int)   # Emitted when spaces are loaded (count)
    floor_filter_changed = pyqtSignal(str)  # Emitted when floor filter changes (floor_id or "all")
    spaces_selection_changed = pyqtSignal(list)  # Emitted when multiple spaces are selected
    zoom_to_spaces_requested = pyqtSignal(list)  # Emitted when zoom to spaces is requested

    def __init__(self, parent=None):
        super().__init__(parent)
        self.spaces = []  # List of SpaceData objects
        self.current_space_guid = None
        self.floors: List[FloorLevel] = []  # Available floors
        self.current_floor_filter: Optional[str] = None  # Current floor filter ("all" or floor_id)
        self.spaces_with_geometry: set = set()  # Set of space GUIDs that have geometry
        self.selected_space_guids: List[str] = []  # Multiple selection support

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

        # Floor filter section
        floor_filter_container = QWidget()
        floor_filter_container.setStyleSheet("""
            QWidget {
                background-color: white;
                color: black;
                border: 1px solid #ced4da;
                border-radius: 6px;
                padding: 4px;
                margin-bottom: 4px;
            }
        """)
        floor_filter_layout = QHBoxLayout()
        floor_filter_layout.setContentsMargins(8, 4, 8, 4)
        floor_filter_container.setLayout(floor_filter_layout)

        floor_label = QLabel("🏢")
        floor_label.setStyleSheet("border: none; background: transparent; color: #6c757d;")
        
        self.floor_filter_combo = QComboBox()
        self.floor_filter_combo.setStyleSheet("""
            QComboBox {
                border: none;
                background: transparent;
                font-size: 13px;
                padding: 4px;
                min-width: 120px;
            }
            QComboBox:focus {
                background-color: #f8f9fa;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: none;
                border: none;
            }
        """)
        self.floor_filter_combo.addItem("All Floors", "all")
        self.floor_filter_combo.currentTextChanged.connect(self.on_floor_filter_changed)

        # Show geometry indicator checkbox
        self.show_geometry_only = QCheckBox("📐 With geometry only")
        self.show_geometry_only.setStyleSheet("""
            QCheckBox {
                border: none;
                background: transparent;
                color: #6c757d;
                font-size: 12px;
            }
            QCheckBox:hover {
                color: #495057;
            }
        """)
        self.show_geometry_only.stateChanged.connect(self.filter_spaces_by_current_criteria)

        floor_filter_layout.addWidget(floor_label)
        floor_filter_layout.addWidget(self.floor_filter_combo, 1)
        floor_filter_layout.addWidget(self.show_geometry_only)
        layout.addWidget(floor_filter_container)

        # Search/filter section with enhanced styling
        search_container = QWidget()
        search_container.setStyleSheet("""
            QWidget {
                background-color: white;
                color: black;
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
        self.search_input.textChanged.connect(self.filter_spaces_by_current_criteria)

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

        # Space list with enhanced styling and multi-selection support
        self.space_list = QListWidget()
        self.space_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)  # Enable multi-selection
        self.space_list.setStyleSheet("""
            QListWidget {
                background-color: white;
                color: black;
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
                color: black;
            }
            QListWidget::item:hover {
                background-color: #f8f9fa;
                color: black;
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
        self.space_list.itemSelectionChanged.connect(self.on_selection_changed)
        self.space_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.space_list.customContextMenuRequested.connect(self.show_context_menu)
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
                color: black;
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

        # Get filtered spaces using all current criteria
        filtered_spaces = self.get_filtered_spaces(filter_text)

        # Update count label
        total_spaces = len(self.spaces)
        filtered_count = len(filtered_spaces)
        
        if self.current_floor_filter or self.show_geometry_only.isChecked() or filter_text:
            self.update_count_label(total_spaces, filtered_count)
        else:
            self.update_count_label(total_spaces)

        # Add spaces to list
        for space in filtered_spaces:
            item_text = self.format_space_display_text_with_indicators(space)
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, space.guid)  # Store GUID

            # Add tooltip with more details
            tooltip = self.format_space_tooltip_with_floor_info(space)
            item.setToolTip(tooltip)

            # Add icon based on space type and geometry availability
            icon = self.get_space_type_icon_with_geometry(space)
            if icon:
                item.setText(f"{icon} {item_text}")

            # Style item based on geometry availability
            if space.guid not in self.spaces_with_geometry:
                item.setForeground(Qt.GlobalColor.gray)

            self.space_list.addItem(item)

        # Show "no results" message if filtered and empty
        if filtered_count == 0:
            if filter_text:
                message = "🔍 No spaces match your search criteria"
            elif self.current_floor_filter:
                message = "🏢 No spaces found on selected floor"
            elif self.show_geometry_only.isChecked():
                message = "📐 No spaces with geometry found"
            else:
                message = "📭 No spaces found"
                
            item = QListWidgetItem(message)
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

    def get_space_type_icon_with_geometry(self, space: SpaceData) -> str:
        """Get an icon for the space type with geometry indicator."""
        base_icon = self.get_space_type_icon(space.object_type)
        
        # Add geometry indicator
        has_geometry = space.guid in self.spaces_with_geometry
        if has_geometry:
            return f"📐{base_icon}"  # Geometry available
        else:
            return f"📋{base_icon}"  # No geometry

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

    def format_space_display_text_with_indicators(self, space: SpaceData) -> str:
        """Format the display text for a space with geometry and floor indicators."""
        base_text = self.format_space_display_text(space)
        
        # Add geometry indicator
        has_geometry = space.guid in self.spaces_with_geometry
        geometry_indicator = "📐" if has_geometry else "📋"
        
        # Add floor information if multiple floors exist
        floor_info = ""
        if len(self.floors) > 1:
            space_floor = self.get_floor_for_space(space.guid)
            if space_floor:
                floor_info = f" [{space_floor.name}]"
        
        return f"{base_text}{floor_info}"

    def get_floor_for_space(self, space_guid: str) -> Optional[FloorLevel]:
        """Get the floor that contains the given space."""
        for floor in self.floors:
            if space_guid in floor.spaces:
                return floor
        return None

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

    def format_space_tooltip_with_floor_info(self, space: SpaceData) -> str:
        """Format the tooltip text for a space with floor and geometry information."""
        base_tooltip = self.format_space_tooltip(space)
        
        # Add floor information
        space_floor = self.get_floor_for_space(space.guid)
        if space_floor:
            base_tooltip += f"\nFloor: {space_floor.name} (Elevation: {space_floor.elevation}m)"
        
        # Add geometry availability
        has_geometry = space.guid in self.spaces_with_geometry
        geometry_status = "Available" if has_geometry else "Not available"
        base_tooltip += f"\nGeometry: {geometry_status}"
        
        return base_tooltip

    def filter_spaces(self, text: str):
        """Filter spaces based on search text (legacy method)."""
        self.filter_spaces_by_current_criteria()
        
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

    # Floor filtering and geometry support methods

    def set_floors(self, floors: List[FloorLevel]):
        """Set available floors for filtering."""
        self.floors = floors
        self.update_floor_filter_combo()

    def update_floor_filter_combo(self):
        """Update the floor filter combo box with available floors."""
        # Clear existing items except "All Floors"
        self.floor_filter_combo.clear()
        self.floor_filter_combo.addItem("All Floors", "all")
        
        # Add floors sorted by elevation
        sorted_floors = sorted(self.floors, key=lambda f: f.elevation)
        for floor in sorted_floors:
            space_count = len(floor.spaces)
            display_text = f"{floor.name} ({space_count} spaces)"
            self.floor_filter_combo.addItem(display_text, floor.id)

    def set_spaces_with_geometry(self, space_guids: set):
        """Set which spaces have geometry data available."""
        self.spaces_with_geometry = space_guids
        self.refresh_spaces()

    def set_floor_filter(self, floor_id: Optional[str]):
        """Set the current floor filter."""
        if floor_id is None or floor_id == "all":
            self.current_floor_filter = None
            self.floor_filter_combo.setCurrentIndex(0)  # "All Floors"
        else:
            self.current_floor_filter = floor_id
            # Find and select the floor in combo box
            for i in range(self.floor_filter_combo.count()):
                if self.floor_filter_combo.itemData(i) == floor_id:
                    self.floor_filter_combo.setCurrentIndex(i)
                    break
        
        self.filter_spaces_by_current_criteria()

    def on_floor_filter_changed(self):
        """Handle floor filter combo box changes."""
        current_data = self.floor_filter_combo.currentData()
        if current_data == "all":
            self.current_floor_filter = None
        else:
            self.current_floor_filter = current_data
        
        self.filter_spaces_by_current_criteria()
        self.floor_filter_changed.emit(current_data or "all")

    def filter_spaces_by_current_criteria(self):
        """Filter spaces based on current search text, floor filter, and geometry filter."""
        search_text = self.search_input.text()
        self.populate_space_list(search_text)

    def get_filtered_spaces(self, search_text: str = "") -> List[SpaceData]:
        """Get spaces filtered by current criteria."""
        filtered_spaces = self.spaces

        # Apply floor filter
        if self.current_floor_filter:
            floor_space_guids = set()
            for floor in self.floors:
                if floor.id == self.current_floor_filter:
                    floor_space_guids = set(floor.spaces)
                    break
            
            filtered_spaces = [
                space for space in filtered_spaces
                if space.guid in floor_space_guids
            ]

        # Apply geometry filter
        if self.show_geometry_only.isChecked():
            filtered_spaces = [
                space for space in filtered_spaces
                if space.guid in self.spaces_with_geometry
            ]

        # Apply search filter
        if search_text:
            search_lower = search_text.lower()
            filtered_spaces = [
                space for space in filtered_spaces
                if (search_lower in space.name.lower() or
                    search_lower in space.long_name.lower() or
                    search_lower in space.object_type.lower() or
                    search_lower in space.zone_category.lower() or
                    search_lower in space.number.lower())
            ]

        return filtered_spaces

    def on_selection_changed(self):
        """Handle selection changes in the space list."""
        selected_items = self.space_list.selectedItems()
        selected_guids = []
        
        for item in selected_items:
            guid = item.data(Qt.ItemDataRole.UserRole)
            if guid:  # Only include items with valid GUIDs
                selected_guids.append(guid)
        
        self.selected_space_guids = selected_guids
        
        # Update single selection for backward compatibility
        if selected_guids:
            self.current_space_guid = selected_guids[0]
            space = self.get_space_by_guid(selected_guids[0])
            if space:
                self.update_space_info(space)
                self.clear_button.setEnabled(True)
        else:
            self.current_space_guid = None
            self.info_label.setText("No space selected")
            self.clear_button.setEnabled(False)
        
        # Emit selection change signal
        self.spaces_selection_changed.emit(selected_guids)
        
        # Emit single selection signal for backward compatibility
        if selected_guids:
            self.space_selected.emit(selected_guids[0])

    def highlight_spaces_on_floor_plan(self, space_guids: List[str]):
        """Highlight spaces in the list that are selected on the floor plan."""
        # Clear current selection
        self.space_list.clearSelection()
        
        # Select items corresponding to the space GUIDs
        for i in range(self.space_list.count()):
            item = self.space_list.item(i)
            guid = item.data(Qt.ItemDataRole.UserRole)
            if guid and guid in space_guids:
                item.setSelected(True)

    def sync_with_floor_plan_selection(self, space_guids: List[str]):
        """Synchronize selection with floor plan selection."""
        self.highlight_spaces_on_floor_plan(space_guids)

    def get_selected_space_guids(self) -> List[str]:
        """Get all currently selected space GUIDs."""
        return self.selected_space_guids.copy()

    def select_spaces_by_guids(self, space_guids: List[str]):
        """Select spaces by their GUIDs."""
        self.space_list.clearSelection()
        
        for i in range(self.space_list.count()):
            item = self.space_list.item(i)
            guid = item.data(Qt.ItemDataRole.UserRole)
            if guid and guid in space_guids:
                item.setSelected(True)

    def get_current_floor_filter(self) -> Optional[str]:
        """Get the current floor filter."""
        return self.current_floor_filter

    # Floor-aware navigation methods

    def zoom_to_selected_spaces(self):
        """Request zoom to currently selected spaces."""
        if self.selected_space_guids:
            self.zoom_to_spaces_requested.emit(self.selected_space_guids)

    def switch_to_space_floor(self, space_guid: str):
        """Switch to the floor containing the specified space."""
        space_floor = self.get_floor_for_space(space_guid)
        if space_floor and space_floor.id != self.current_floor_filter:
            self.set_floor_filter(space_floor.id)
            return True
        return False

    def navigate_to_space(self, space_guid: str, zoom_to_space: bool = True):
        """Navigate to a specific space (switch floor if needed and optionally zoom)."""
        # Switch to the floor containing this space
        floor_switched = self.switch_to_space_floor(space_guid)
        
        # Select the space
        self.select_spaces_by_guids([space_guid])
        
        # Request zoom if requested
        if zoom_to_space:
            self.zoom_to_spaces_requested.emit([space_guid])
        
        return floor_switched

    def get_spaces_on_floor(self, floor_id: str) -> List[SpaceData]:
        """Get all spaces on a specific floor."""
        floor_space_guids = set()
        for floor in self.floors:
            if floor.id == floor_id:
                floor_space_guids = set(floor.spaces)
                break
        
        return [
            space for space in self.spaces
            if space.guid in floor_space_guids
        ]

    def get_related_spaces(self, space_guid: str) -> List[str]:
        """Get spaces related to the given space (placeholder for future relationship support)."""
        # This is a placeholder for future implementation of space relationships
        # Could include adjacent spaces, spaces in same zone, etc.
        return []

    def navigate_to_related_spaces(self, space_guid: str):
        """Navigate to spaces related to the given space."""
        related_guids = self.get_related_spaces(space_guid)
        if related_guids:
            # Switch to appropriate floor if needed
            primary_space_floor = self.get_floor_for_space(space_guid)
            if primary_space_floor:
                self.set_floor_filter(primary_space_floor.id)
            
            # Select all related spaces
            all_guids = [space_guid] + related_guids
            self.select_spaces_by_guids(all_guids)
            
            # Request zoom to all related spaces
            self.zoom_to_spaces_requested.emit(all_guids)

    def show_context_menu(self, position: QPoint):
        """Show context menu for space list items."""
        item = self.space_list.itemAt(position)
        if not item:
            return
        
        space_guid = item.data(Qt.ItemDataRole.UserRole)
        if not space_guid:
            return
        
        menu = QMenu(self)
        
        # Zoom to space action
        zoom_action = QAction("🔍 Zoom to Space", self)
        zoom_action.triggered.connect(lambda: self.zoom_to_spaces_requested.emit([space_guid]))
        menu.addAction(zoom_action)
        
        # Navigate to space action (switch floor + zoom)
        navigate_action = QAction("🧭 Navigate to Space", self)
        navigate_action.triggered.connect(lambda: self.navigate_to_space(space_guid, True))
        menu.addAction(navigate_action)
        
        menu.addSeparator()
        
        # Switch to space floor action
        space_floor = self.get_floor_for_space(space_guid)
        if space_floor and space_floor.id != self.current_floor_filter:
            switch_floor_action = QAction(f"🏢 Switch to {space_floor.name}", self)
            switch_floor_action.triggered.connect(lambda: self.set_floor_filter(space_floor.id))
            menu.addAction(switch_floor_action)
        
        # Show related spaces (if any)
        related_spaces = self.get_related_spaces(space_guid)
        if related_spaces:
            related_action = QAction(f"🔗 Show Related Spaces ({len(related_spaces)})", self)
            related_action.triggered.connect(lambda: self.navigate_to_related_spaces(space_guid))
            menu.addAction(related_action)
        
        # Show context menu
        menu.exec(self.space_list.mapToGlobal(position))
