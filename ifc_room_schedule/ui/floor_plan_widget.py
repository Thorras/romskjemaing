"""
Floor Plan Widget Container Component

Main container widget that manages floor plan display and controls,
integrating FloorPlanCanvas with navigation controls and floor selection.
"""

import logging
from typing import Optional, List, Dict, Any
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QComboBox, QToolButton, QFrame, QSizePolicy, QSpacerItem, QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QFont

from ..visualization.floor_plan_canvas import FloorPlanCanvas
from ..visualization.geometry_models import FloorGeometry, FloorLevel


class FloorSelector(QWidget):
    """Floor selection component with metadata display."""
    
    floor_selected = pyqtSignal(str)  # floor_id
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.floors: List[FloorLevel] = []
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the floor selector UI."""
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Floor label
        self.floor_label = QLabel("Floor:")
        self.floor_label.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        layout.addWidget(self.floor_label)
        
        # Floor selection dropdown
        self.floor_combo = QComboBox()
        self.floor_combo.setMinimumWidth(200)
        self.floor_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.floor_combo.currentTextChanged.connect(self._on_floor_selection_changed)
        layout.addWidget(self.floor_combo)
        
        # Floor metadata display
        self.metadata_label = QLabel()
        self.metadata_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(self.metadata_label)
        
        # Spacer to push everything to the left
        layout.addItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        
        self.setLayout(layout)
    
    def set_floors(self, floors: List[FloorLevel]):
        """
        Set available floors for selection.
        
        Args:
            floors: List of FloorLevel objects
        """
        self.floors = floors
        self.floor_combo.clear()
        
        if not floors:
            self.floor_combo.addItem("No floors available")
            self.floor_combo.setEnabled(False)
            self.metadata_label.setText("")
            return
        
        self.floor_combo.setEnabled(True)
        
        # Sort floors by elevation (lowest first)
        sorted_floors = sorted(floors, key=lambda f: f.elevation)
        
        for floor in sorted_floors:
            # Create display text with floor name and elevation
            display_text = f"{floor.name} (Elev: {floor.elevation:.1f}m)"
            self.floor_combo.addItem(display_text, floor.id)
        
        # Select first floor by default
        if sorted_floors:
            self.set_current_floor(sorted_floors[0].id)
        
        self.logger.debug(f"Set {len(floors)} floors in selector")
    
    def set_current_floor(self, floor_id: str):
        """
        Set the currently selected floor.
        
        Args:
            floor_id: ID of the floor to select
        """
        for i in range(self.floor_combo.count()):
            if self.floor_combo.itemData(i) == floor_id:
                self.floor_combo.setCurrentIndex(i)
                self._update_metadata_display(floor_id)
                break
    
    def get_current_floor(self) -> Optional[str]:
        """Get the ID of the currently selected floor."""
        current_data = self.floor_combo.currentData()
        return current_data if current_data else None
    
    def _on_floor_selection_changed(self, text: str):
        """Handle floor selection change."""
        floor_id = self.floor_combo.currentData()
        if floor_id:
            self._update_metadata_display(floor_id)
            self.floor_selected.emit(floor_id)
            self.logger.debug(f"Floor selection changed to: {floor_id}")
    
    def _update_metadata_display(self, floor_id: str):
        """Update the metadata display for the selected floor."""
        floor = next((f for f in self.floors if f.id == floor_id), None)
        if floor:
            space_count = len(floor.spaces) if floor.spaces else 0
            metadata_text = f"{space_count} spaces"
            if hasattr(floor, 'total_area') and floor.total_area > 0:
                metadata_text += f" • {floor.total_area:.0f}m²"
            self.metadata_label.setText(metadata_text)
        else:
            self.metadata_label.setText("")


class NavigationControls(QWidget):
    """Navigation controls for zoom, pan, and fit-to-view operations."""
    
    zoom_in_requested = pyqtSignal()
    zoom_out_requested = pyqtSignal()
    zoom_fit_requested = pyqtSignal()
    pan_reset_requested = pyqtSignal()
    professional_style_toggled = pyqtSignal(bool)
    show_areas_toggled = pyqtSignal(bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the navigation controls UI."""
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        # Zoom controls
        self.zoom_in_btn = self._create_tool_button("🔍+", "Zoom In")
        self.zoom_in_btn.clicked.connect(self.zoom_in_requested.emit)
        layout.addWidget(self.zoom_in_btn)
        
        self.zoom_out_btn = self._create_tool_button("🔍-", "Zoom Out")
        self.zoom_out_btn.clicked.connect(self.zoom_out_requested.emit)
        layout.addWidget(self.zoom_out_btn)
        
        # Separator
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.Shape.VLine)
        separator1.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator1)
        
        # Fit to view control
        self.fit_view_btn = self._create_tool_button("⌂", "Fit to View")
        self.fit_view_btn.clicked.connect(self.zoom_fit_requested.emit)
        layout.addWidget(self.fit_view_btn)
        
        # Pan reset control
        self.reset_pan_btn = self._create_tool_button("⌖", "Reset View")
        self.reset_pan_btn.clicked.connect(self.pan_reset_requested.emit)
        layout.addWidget(self.reset_pan_btn)
        
        # Separator
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.Shape.VLine)
        separator2.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator2)
        
        # Professional style toggle
        self.professional_style_cb = QCheckBox("ArchiCAD Style")
        self.professional_style_cb.setToolTip("Toggle professional architectural drawing style")
        self.professional_style_cb.setChecked(True)  # Default to professional style
        self.professional_style_cb.toggled.connect(self.professional_style_toggled.emit)
        layout.addWidget(self.professional_style_cb)
        
        # Show areas toggle
        self.show_areas_cb = QCheckBox("Show Areas")
        self.show_areas_cb.setToolTip("Show room areas in labels")
        self.show_areas_cb.setChecked(True)
        self.show_areas_cb.toggled.connect(self.show_areas_toggled.emit)
        layout.addWidget(self.show_areas_cb)
        
        # Spacer to push controls to the left
        layout.addItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        
        self.setLayout(layout)
    
    def _create_tool_button(self, text: str, tooltip: str) -> QToolButton:
        """Create a styled tool button."""
        button = QToolButton()
        button.setText(text)
        button.setToolTip(tooltip)
        button.setFixedSize(QSize(32, 32))
        button.setStyleSheet("""
            QToolButton {
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: #f8f9fa;
                font-size: 14px;
                font-weight: bold;
            }
            QToolButton:hover {
                background-color: #e9ecef;
                border-color: #adb5bd;
            }
            QToolButton:pressed {
                background-color: #dee2e6;
                border-color: #6c757d;
            }
        """)
        return button


class FloorPlanWidget(QWidget):
    """
    Main container widget for floor plan display and controls.
    
    Integrates FloorPlanCanvas with floor selection and navigation controls
    to provide a complete floor plan viewing experience.
    """
    
    # Signals
    space_selected = pyqtSignal(str, bool)  # space_guid, ctrl_pressed
    floor_changed = pyqtSignal(str)   # floor_id
    spaces_selection_changed = pyqtSignal(list)  # selected space GUIDs
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
        # Floor data
        self.floor_geometries: Dict[str, FloorGeometry] = {}
        self.current_floor_id: Optional[str] = None
        
        self.setup_ui()
        self.connect_signals()
        
        self.logger.info("FloorPlanWidget initialized")
    
    def setup_ui(self):
        """Set up the widget UI layout."""
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Top controls bar
        controls_frame = QFrame()
        controls_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        controls_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 4px;
            }
        """)
        
        controls_layout = QHBoxLayout()
        controls_layout.setContentsMargins(8, 4, 8, 4)
        controls_layout.setSpacing(16)
        
        # Floor selector
        self.floor_selector = FloorSelector()
        controls_layout.addWidget(self.floor_selector)
        
        # Navigation controls
        self.navigation_controls = NavigationControls()
        controls_layout.addWidget(self.navigation_controls)
        
        controls_frame.setLayout(controls_layout)
        layout.addWidget(controls_frame)
        
        # Floor plan canvas (main content)
        self.floor_plan_canvas = FloorPlanCanvas()
        self.floor_plan_canvas.setSizePolicy(
            QSizePolicy.Policy.Expanding, 
            QSizePolicy.Policy.Expanding
        )
        layout.addWidget(self.floor_plan_canvas, 1)  # Give it stretch factor
        
        self.setLayout(layout)
    
    def connect_signals(self):
        """Connect internal signals between components."""
        # Floor selector signals
        self.floor_selector.floor_selected.connect(self._on_floor_selected)
        
        # Navigation control signals
        self.navigation_controls.zoom_in_requested.connect(self._zoom_in)
        self.navigation_controls.zoom_out_requested.connect(self._zoom_out)
        self.navigation_controls.zoom_fit_requested.connect(self._zoom_to_fit)
        self.navigation_controls.pan_reset_requested.connect(self._reset_view)
        self.navigation_controls.professional_style_toggled.connect(self._toggle_professional_style)
        self.navigation_controls.show_areas_toggled.connect(self._toggle_show_areas)
        
        # Floor plan canvas signals
        self.floor_plan_canvas.room_clicked.connect(self._on_space_clicked)
        self.floor_plan_canvas.rooms_selection_changed.connect(self.spaces_selection_changed.emit)
    
    def set_floor_geometry(self, floor_geometries: Dict[str, FloorGeometry]):
        """
        Set floor geometry data for display.
        
        Args:
            floor_geometries: Dictionary mapping floor_id to FloorGeometry objects
        """
        self.floor_geometries = floor_geometries.copy()
        
        # Update floor selector with available floors
        floors = [geometry.level for geometry in floor_geometries.values()]
        self.floor_selector.set_floors(floors)
        
        # Set floor geometries in canvas
        self.floor_plan_canvas.set_floor_geometries(floor_geometries)
        
        # Set current floor to first available if none set
        if floors and not self.current_floor_id:
            first_floor = sorted(floors, key=lambda f: f.elevation)[0]
            self.set_current_floor(first_floor.id)
        
        self.logger.info(f"Set geometry for {len(floor_geometries)} floors")
    
    def set_current_floor(self, floor_id: str):
        """
        Set the current floor to display.
        
        Args:
            floor_id: ID of the floor to display
        """
        if floor_id in self.floor_geometries:
            self.current_floor_id = floor_id
            
            # Update floor selector
            self.floor_selector.set_current_floor(floor_id)
            
            # Update canvas
            self.floor_plan_canvas.set_current_floor(floor_id)
            
            # Emit floor changed signal
            self.floor_changed.emit(floor_id)
            
            self.logger.debug(f"Current floor set to: {floor_id}")
    
    def get_current_floor_id(self) -> Optional[str]:
        """Get the ID of the currently displayed floor."""
        return self.current_floor_id
    
    def highlight_spaces(self, space_guids: List[str]):
        """
        Highlight specific spaces on the floor plan.
        
        Args:
            space_guids: List of space GUIDs to highlight
        """
        self.floor_plan_canvas.highlight_rooms(space_guids)
    
    def zoom_to_spaces(self, space_guids: List[str]):
        """
        Zoom and pan to focus on specific spaces.
        
        Args:
            space_guids: List of space GUIDs to focus on
        """
        self.floor_plan_canvas.zoom_to_rooms(space_guids)
    
    def zoom_to_fit(self):
        """Zoom and pan to fit the entire floor plan in view."""
        self.floor_plan_canvas.zoom_to_fit()
    
    def clear_selection(self):
        """Clear all space selections."""
        self.floor_plan_canvas.clear_selection()
    
    def _on_floor_selected(self, floor_id: str):
        """Handle floor selection from floor selector."""
        self.set_current_floor(floor_id)
    
    def _on_space_clicked(self, space_guid: str, ctrl_pressed: bool):
        """Handle space click from floor plan canvas."""
        self.space_selected.emit(space_guid, ctrl_pressed)
    
    def _zoom_in(self):
        """Handle zoom in request."""
        current_zoom = self.floor_plan_canvas.zoom_level
        new_zoom = min(current_zoom * 1.2, self.floor_plan_canvas.max_zoom)
        self.floor_plan_canvas.zoom_level = new_zoom
        self.floor_plan_canvas._update_view_transform()
        self.floor_plan_canvas.update()
        self.logger.debug(f"Zoomed in to: {new_zoom:.2f}")
    
    def _zoom_out(self):
        """Handle zoom out request."""
        current_zoom = self.floor_plan_canvas.zoom_level
        new_zoom = max(current_zoom / 1.2, self.floor_plan_canvas.min_zoom)
        self.floor_plan_canvas.zoom_level = new_zoom
        self.floor_plan_canvas._update_view_transform()
        self.floor_plan_canvas.update()
        self.logger.debug(f"Zoomed out to: {new_zoom:.2f}")
    
    def _zoom_to_fit(self):
        """Handle fit to view request."""
        self.floor_plan_canvas.zoom_to_fit()
    
    def _reset_view(self):
        """Handle reset view request."""
        self.floor_plan_canvas.zoom_to_fit()
    
    def _toggle_professional_style(self, enabled: bool):
        """Handle professional style toggle."""
        self.floor_plan_canvas.set_professional_style(enabled)
    
    def _toggle_show_areas(self, enabled: bool):
        """Handle show areas toggle."""
        self.floor_plan_canvas.set_show_room_areas(enabled)