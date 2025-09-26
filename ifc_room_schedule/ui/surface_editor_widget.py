"""
Surface Editor Widget

Widget for editing surface and space boundary descriptions with tabbed interface.
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
                             QTextEdit, QLabel, QPushButton, QGroupBox,
                             QFormLayout, QMessageBox, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QValidator
from typing import Dict, Any
import logging


class DescriptionValidator(QValidator):
    """Validator for description text input."""

    def __init__(self, max_length: int = 1000):
        super().__init__()
        self.max_length = max_length

    def validate(self, input_text: str, pos: int) -> tuple:
        """Validate the input text."""
        if len(input_text) > self.max_length:
            return (QValidator.State.Invalid, input_text, pos)
        return (QValidator.State.Acceptable, input_text, pos)


class SurfaceEditorWidget(QWidget):
    """Widget for editing surface and space boundary descriptions."""

    # Signals
    surface_description_changed = pyqtSignal(str, str)  # surface_id, description
    boundary_description_changed = pyqtSignal(str, str)  # boundary_guid, description

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)

        # Current editing state
        self.current_surface_id = None
        self.current_boundary_guid = None
        self.current_space_guid = None

        # Auto-save timer
        self.save_timer = QTimer()
        self.save_timer.setSingleShot(True)
        self.save_timer.timeout.connect(self.auto_save)
        self.auto_save_delay = 2000  # 2 seconds

        # Data storage for descriptions
        self.surface_descriptions: Dict[str, str] = {}
        self.boundary_descriptions: Dict[str, str] = {}

        self.setup_ui()
        self.show_empty_state()

    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Title
        self.title_label = QLabel("Description Editor")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        self.title_label.setFont(title_font)
        layout.addWidget(self.title_label)

        # Create tab widget for surfaces and boundaries
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # Surface editor tab
        self.surface_tab = self.create_surface_editor_tab()
        self.tab_widget.addTab(self.surface_tab, "Surface Descriptions")

        # Boundary editor tab
        self.boundary_tab = self.create_boundary_editor_tab()
        self.tab_widget.addTab(self.boundary_tab, "Boundary Descriptions")

        # Status and actions
        self.create_status_section(layout)

    def create_surface_editor_tab(self) -> QWidget:
        """Create the surface editor tab."""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)

        # Surface info section
        info_group = QGroupBox("Surface Information")
        info_layout = QFormLayout()
        info_group.setLayout(info_layout)

        self.surface_type_label = QLabel("No surface selected")
        self.surface_area_label = QLabel("-")
        self.surface_material_label = QLabel("-")

        info_layout.addRow("Type:", self.surface_type_label)
        info_layout.addRow("Area:", self.surface_area_label)
        info_layout.addRow("Material:", self.surface_material_label)

        layout.addWidget(info_group)

        # Description editor section
        editor_group = QGroupBox("Description")
        editor_layout = QVBoxLayout()
        editor_group.setLayout(editor_layout)

        # Character count label
        self.surface_char_count_label = QLabel("0 / 1000 characters")
        self.surface_char_count_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        editor_layout.addWidget(self.surface_char_count_label)

        # Text editor
        self.surface_description_edit = QTextEdit()
        self.surface_description_edit.setPlaceholderText(
            "Enter a description for this surface...\n\n"
            "You can include:\n"
            "• Material specifications\n"
            "• Finish details\n"
            "• Special requirements\n"
            "• Maintenance notes"
        )
        self.surface_description_edit.textChanged.connect(self.on_surface_text_changed)
        self.surface_description_edit.setMaximumHeight(200)
        editor_layout.addWidget(self.surface_description_edit)

        layout.addWidget(editor_group)

        # Add stretch to push content to top
        layout.addStretch()

        return tab

    def create_boundary_editor_tab(self) -> QWidget:
        """Create the boundary editor tab."""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)

        # Boundary info section
        info_group = QGroupBox("Space Boundary Information")
        info_layout = QFormLayout()
        info_group.setLayout(info_layout)

        self.boundary_label_label = QLabel("No boundary selected")
        self.boundary_type_label = QLabel("-")
        self.boundary_orientation_label = QLabel("-")
        self.boundary_area_label = QLabel("-")
        self.boundary_element_label = QLabel("-")

        info_layout.addRow("Label:", self.boundary_label_label)
        info_layout.addRow("Type:", self.boundary_type_label)
        info_layout.addRow("Orientation:", self.boundary_orientation_label)
        info_layout.addRow("Area:", self.boundary_area_label)
        info_layout.addRow("Element:", self.boundary_element_label)

        layout.addWidget(info_group)

        # Description editor section
        editor_group = QGroupBox("Description")
        editor_layout = QVBoxLayout()
        editor_group.setLayout(editor_layout)

        # Character count label
        self.boundary_char_count_label = QLabel("0 / 1000 characters")
        self.boundary_char_count_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        editor_layout.addWidget(self.boundary_char_count_label)

        # Text editor
        self.boundary_description_edit = QTextEdit()
        self.boundary_description_edit.setPlaceholderText(
            "Enter a description for this space boundary...\n\n"
            "You can include:\n"
            "• Thermal properties\n"
            "• Construction details\n"
            "• Performance requirements\n"
            "• Connection specifications"
        )
        self.boundary_description_edit.textChanged.connect(self.on_boundary_text_changed)
        self.boundary_description_edit.setMaximumHeight(200)
        editor_layout.addWidget(self.boundary_description_edit)

        layout.addWidget(editor_group)

        # Add stretch to push content to top
        layout.addStretch()

        return tab

    def create_status_section(self, parent_layout):
        """Create the status and action section."""
        status_frame = QFrame()
        status_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        status_layout = QHBoxLayout()
        status_frame.setLayout(status_layout)

        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #6c757d; font-style: italic;")
        status_layout.addWidget(self.status_label)

        status_layout.addStretch()

        # Clear button
        self.clear_button = QPushButton("Clear All")
        self.clear_button.clicked.connect(self.clear_all_descriptions)
        self.clear_button.setEnabled(False)
        status_layout.addWidget(self.clear_button)

        parent_layout.addWidget(status_frame)

    def edit_surface(self, surface_id: str, surface_data: Dict[str, Any]):
        """Start editing a surface description."""
        self.current_surface_id = surface_id
        self.current_boundary_guid = None  # Clear boundary selection

        # Switch to surface tab
        self.tab_widget.setCurrentIndex(0)

        # Update surface information
        self.surface_type_label.setText(surface_data.get('type', 'Unknown'))
        self.surface_area_label.setText(f"{surface_data.get('area', 0):.2f} m²")
        self.surface_material_label.setText(surface_data.get('material', 'Unknown'))

        # Load existing description
        existing_description = self.surface_descriptions.get(
            surface_id, surface_data.get('user_description', ''))

        # Temporarily disconnect signal to avoid triggering save
        self.surface_description_edit.textChanged.disconnect()
        self.surface_description_edit.setPlainText(existing_description)
        self.surface_description_edit.textChanged.connect(self.on_surface_text_changed)

        # Update character count
        self.update_surface_char_count()

        # Update title and status
        self.title_label.setText(f"Editing Surface: {surface_data.get('type', 'Unknown')}")
        self.status_label.setText(f"Editing surface {surface_id}")

        # Enable controls
        self.surface_description_edit.setEnabled(True)
        self.clear_button.setEnabled(True)

        self.logger.info(f"Started editing surface: {surface_id}")

    def edit_boundary(self, boundary_guid: str, boundary_data: Dict[str, Any]):
        """Start editing a space boundary description."""
        self.current_boundary_guid = boundary_guid
        self.current_surface_id = None  # Clear surface selection

        # Switch to boundary tab
        self.tab_widget.setCurrentIndex(1)

        # Update boundary information
        self.boundary_label_label.setText(boundary_data.get('display_label', 'Unknown'))
        self.boundary_type_label.setText(
            boundary_data.get('physical_or_virtual_boundary', 'Unknown'))
        self.boundary_orientation_label.setText(
            boundary_data.get('boundary_orientation', 'Unknown'))
        self.boundary_area_label.setText(f"{boundary_data.get('calculated_area', 0):.2f} m²")
        self.boundary_element_label.setText(
            boundary_data.get('related_building_element_type', 'Unknown'))

        # Load existing description
        existing_description = self.boundary_descriptions.get(
            boundary_guid, boundary_data.get('user_description', ''))

        # Temporarily disconnect signal to avoid triggering save
        self.boundary_description_edit.textChanged.disconnect()
        self.boundary_description_edit.setPlainText(existing_description)
        self.boundary_description_edit.textChanged.connect(self.on_boundary_text_changed)

        # Update character count
        self.update_boundary_char_count()

        # Update title and status
        self.title_label.setText(
            f"Editing Boundary: {boundary_data.get('display_label', 'Unknown')}")
        self.status_label.setText(f"Editing boundary {boundary_guid}")

        # Enable controls
        self.boundary_description_edit.setEnabled(True)
        self.clear_button.setEnabled(True)

        self.logger.info(f"Started editing boundary: {boundary_guid}")

    def on_surface_text_changed(self):
        """Handle surface description text changes."""
        if not self.current_surface_id:
            return

        # Update character count
        self.update_surface_char_count()

        # Start auto-save timer
        self.save_timer.stop()
        self.save_timer.start(self.auto_save_delay)

        # Update status
        self.status_label.setText("Unsaved changes...")

    def on_boundary_text_changed(self):
        """Handle boundary description text changes."""
        if not self.current_boundary_guid:
            return

        # Update character count
        self.update_boundary_char_count()

        # Start auto-save timer
        self.save_timer.stop()
        self.save_timer.start(self.auto_save_delay)

        # Update status
        self.status_label.setText("Unsaved changes...")

    def update_surface_char_count(self):
        """Update the surface character count display."""
        text = self.surface_description_edit.toPlainText()
        char_count = len(text)
        max_chars = 1000

        self.surface_char_count_label.setText(f"{char_count} / {max_chars} characters")

        # Change color if approaching limit
        if char_count > max_chars * 0.9:
            self.surface_char_count_label.setStyleSheet("color: #dc3545; font-weight: bold;")
        elif char_count > max_chars * 0.8:
            self.surface_char_count_label.setStyleSheet("color: #fd7e14; font-weight: bold;")
        else:
            self.surface_char_count_label.setStyleSheet("color: #6c757d;")

        # Validate length
        if char_count > max_chars:
            # Truncate text
            cursor = self.surface_description_edit.textCursor()
            self.surface_description_edit.textChanged.disconnect()
            self.surface_description_edit.setPlainText(text[:max_chars])
            self.surface_description_edit.textChanged.connect(self.on_surface_text_changed)
            cursor.setPosition(max_chars)
            self.surface_description_edit.setTextCursor(cursor)

    def update_boundary_char_count(self):
        """Update the boundary character count display."""
        text = self.boundary_description_edit.toPlainText()
        char_count = len(text)
        max_chars = 1000

        self.boundary_char_count_label.setText(f"{char_count} / {max_chars} characters")

        # Change color if approaching limit
        if char_count > max_chars * 0.9:
            self.boundary_char_count_label.setStyleSheet("color: #dc3545; font-weight: bold;")
        elif char_count > max_chars * 0.8:
            self.boundary_char_count_label.setStyleSheet("color: #fd7e14; font-weight: bold;")
        else:
            self.boundary_char_count_label.setStyleSheet("color: #6c757d;")

        # Validate length
        if char_count > max_chars:
            # Truncate text
            cursor = self.boundary_description_edit.textCursor()
            self.boundary_description_edit.textChanged.disconnect()
            self.boundary_description_edit.setPlainText(text[:max_chars])
            self.boundary_description_edit.textChanged.connect(self.on_boundary_text_changed)
            cursor.setPosition(max_chars)
            self.boundary_description_edit.setTextCursor(cursor)

    def auto_save(self):
        """Auto-save the current description."""
        if self.current_surface_id:
            description = self.surface_description_edit.toPlainText()
            self.surface_descriptions[self.current_surface_id] = description
            self.surface_description_changed.emit(self.current_surface_id, description)
            self.status_label.setText("Surface description saved")
            self.logger.debug(f"Auto-saved surface description for {self.current_surface_id}")

        elif self.current_boundary_guid:
            description = self.boundary_description_edit.toPlainText()
            self.boundary_descriptions[self.current_boundary_guid] = description
            self.boundary_description_changed.emit(self.current_boundary_guid, description)
            self.status_label.setText("Boundary description saved")
            self.logger.debug(f"Auto-saved boundary description for {self.current_boundary_guid}")

    def clear_all_descriptions(self):
        """Clear all descriptions after confirmation."""
        reply = QMessageBox.question(
            self,
            "Clear All Descriptions",
            "Are you sure you want to clear all descriptions?\n\nThis action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Clear text editors
            self.surface_description_edit.clear()
            self.boundary_description_edit.clear()

            # Clear stored descriptions
            if self.current_surface_id:
                self.surface_descriptions[self.current_surface_id] = ""
                self.surface_description_changed.emit(self.current_surface_id, "")

            if self.current_boundary_guid:
                self.boundary_descriptions[self.current_boundary_guid] = ""
                self.boundary_description_changed.emit(self.current_boundary_guid, "")

            self.status_label.setText("All descriptions cleared")
            self.logger.info("Cleared all descriptions")

    def set_space_context(self, space_guid: str):
        """Set the current space context for description persistence."""
        self.current_space_guid = space_guid

    def get_surface_description(self, surface_id: str) -> str:
        """Get the stored description for a surface."""
        return self.surface_descriptions.get(surface_id, "")

    def get_boundary_description(self, boundary_guid: str) -> str:
        """Get the stored description for a boundary."""
        return self.boundary_descriptions.get(boundary_guid, "")

    def update_surface_description(self, surface_id: str, description: str):
        """Update a surface description externally."""
        self.surface_descriptions[surface_id] = description

        # Update UI if this surface is currently being edited
        if self.current_surface_id == surface_id:
            self.surface_description_edit.textChanged.disconnect()
            self.surface_description_edit.setPlainText(description)
            self.surface_description_edit.textChanged.connect(self.on_surface_text_changed)
            self.update_surface_char_count()

    def update_boundary_description(self, boundary_guid: str, description: str):
        """Update a boundary description externally."""
        self.boundary_descriptions[boundary_guid] = description

        # Update UI if this boundary is currently being edited
        if self.current_boundary_guid == boundary_guid:
            self.boundary_description_edit.textChanged.disconnect()
            self.boundary_description_edit.setPlainText(description)
            self.boundary_description_edit.textChanged.connect(self.on_boundary_text_changed)
            self.update_boundary_char_count()

    def show_empty_state(self):
        """Show empty state when no surface or boundary is selected."""
        self.title_label.setText("Description Editor")
        self.status_label.setText("Select a surface or boundary to edit")

        # Clear current selections
        self.current_surface_id = None
        self.current_boundary_guid = None

        # Clear and disable editors
        self.surface_description_edit.clear()
        self.surface_description_edit.setEnabled(False)
        self.boundary_description_edit.clear()
        self.boundary_description_edit.setEnabled(False)

        # Reset info labels
        self.surface_type_label.setText("No surface selected")
        self.surface_area_label.setText("-")
        self.surface_material_label.setText("-")

        self.boundary_label_label.setText("No boundary selected")
        self.boundary_type_label.setText("-")
        self.boundary_orientation_label.setText("-")
        self.boundary_area_label.setText("-")
        self.boundary_element_label.setText("-")

        # Reset character counts
        self.surface_char_count_label.setText("0 / 1000 characters")
        self.boundary_char_count_label.setText("0 / 1000 characters")

        # Disable clear button
        self.clear_button.setEnabled(False)

    def has_unsaved_changes(self) -> bool:
        """Check if there are unsaved changes."""
        return self.save_timer.isActive()

    def force_save(self):
        """Force save any pending changes."""
        if self.save_timer.isActive():
            self.save_timer.stop()
            self.auto_save()
