"""
Space Detail Widget

Widget for displaying detailed space information including surfaces and boundaries.
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
                            QTableWidget, QTableWidgetItem, QLabel, QPushButton,
                            QGroupBox, QScrollArea, QTextEdit, QHeaderView)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from typing import Optional

from ..data.space_model import SpaceData


class SpaceDetailWidget(QWidget):
    """Widget for displaying detailed space information."""
    
    # Signals
    surface_selected = pyqtSignal(str)  # Emitted when a surface is selected
    boundary_selected = pyqtSignal(str)  # Emitted when a boundary is selected
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_space = None
        
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Title
        self.title_label = QLabel("Space Details")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        self.title_label.setFont(title_font)
        layout.addWidget(self.title_label)
        
        # Create tab widget for different views
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Properties tab
        self.properties_tab = self.create_properties_tab()
        self.tab_widget.addTab(self.properties_tab, "Properties")
        
        # Surfaces tab
        self.surfaces_tab = self.create_surfaces_tab()
        self.tab_widget.addTab(self.surfaces_tab, "Surfaces")
        
        # Space Boundaries tab
        self.boundaries_tab = self.create_boundaries_tab()
        self.tab_widget.addTab(self.boundaries_tab, "Space Boundaries")
        
        # Relationships tab
        self.relationships_tab = self.create_relationships_tab()
        self.tab_widget.addTab(self.relationships_tab, "Relationships")
        
        # Initially show empty state
        self.show_empty_state()
        
    def create_properties_tab(self) -> QWidget:
        """Create the properties tab."""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)
        
        # Basic properties group
        basic_group = QGroupBox("Basic Properties")
        basic_layout = QVBoxLayout()
        basic_group.setLayout(basic_layout)
        
        self.basic_properties_label = QLabel("No space selected")
        self.basic_properties_label.setWordWrap(True)
        self.basic_properties_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        basic_layout.addWidget(self.basic_properties_label)
        
        layout.addWidget(basic_group)
        
        # Quantities group
        quantities_group = QGroupBox("Quantities")
        quantities_layout = QVBoxLayout()
        quantities_group.setLayout(quantities_layout)
        
        self.quantities_table = QTableWidget()
        self.quantities_table.setColumnCount(2)
        self.quantities_table.setHorizontalHeaderLabels(["Property", "Value"])
        self.quantities_table.horizontalHeader().setStretchLastSection(True)
        quantities_layout.addWidget(self.quantities_table)
        
        layout.addWidget(quantities_group)
        
        layout.addStretch()
        return tab
        
    def create_surfaces_tab(self) -> QWidget:
        """Create the surfaces tab."""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)
        
        # Surfaces table
        self.surfaces_table = QTableWidget()
        self.surfaces_table.setColumnCount(4)
        self.surfaces_table.setHorizontalHeaderLabels(["Type", "Area (m²)", "Material", "Description"])
        self.surfaces_table.horizontalHeader().setStretchLastSection(True)
        self.surfaces_table.itemClicked.connect(self.on_surface_clicked)
        layout.addWidget(self.surfaces_table)
        
        # Surface summary
        self.surface_summary_label = QLabel("No surfaces data")
        layout.addWidget(self.surface_summary_label)
        
        return tab
        
    def create_boundaries_tab(self) -> QWidget:
        """Create the space boundaries tab."""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)
        
        # Boundaries table
        self.boundaries_table = QTableWidget()
        self.boundaries_table.setColumnCount(6)
        self.boundaries_table.setHorizontalHeaderLabels([
            "Display Label", "Type", "Orientation", "Area (m²)", "Element Type", "Level"
        ])
        self.boundaries_table.horizontalHeader().setStretchLastSection(True)
        self.boundaries_table.itemClicked.connect(self.on_boundary_clicked)
        layout.addWidget(self.boundaries_table)
        
        # Boundary summary
        self.boundary_summary_label = QLabel("No space boundaries data")
        layout.addWidget(self.boundary_summary_label)
        
        return tab
        
    def create_relationships_tab(self) -> QWidget:
        """Create the relationships tab."""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)
        
        # Relationships table
        self.relationships_table = QTableWidget()
        self.relationships_table.setColumnCount(3)
        self.relationships_table.setHorizontalHeaderLabels(["Type", "Related Entity", "Description"])
        self.relationships_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.relationships_table)
        
        # Relationships summary
        self.relationships_summary_label = QLabel("No relationships data")
        layout.addWidget(self.relationships_summary_label)
        
        return tab
        
    def display_space(self, space: SpaceData):
        """Display space details."""
        self.current_space = space
        self.title_label.setText(f"Space Details: {space.number}")
        
        self.update_properties_tab()
        self.update_surfaces_tab()
        self.update_boundaries_tab()
        self.update_relationships_tab()
        
        # Enable the widget
        self.setEnabled(True)
        
    def update_properties_tab(self):
        """Update the properties tab with current space data."""
        if not self.current_space:
            return
            
        space = self.current_space
        
        # Basic properties
        properties_text = f"""
        <b>GUID:</b> {space.guid}<br>
        <b>Number:</b> {space.number}<br>
        <b>Name:</b> {space.name}<br>
        <b>Long Name:</b> {space.long_name}<br>
        <b>Object Type:</b> {space.object_type}<br>
        <b>Zone Category:</b> {space.zone_category}<br>
        <b>Elevation:</b> {space.elevation} m<br>
        <b>Description:</b> {space.description or 'None'}<br>
        <b>Processed:</b> {'Yes' if space.processed else 'No'}
        """
        
        self.basic_properties_label.setText(properties_text)
        
        # Quantities table
        self.quantities_table.setRowCount(len(space.quantities))
        for row, (name, value) in enumerate(space.quantities.items()):
            name_item = QTableWidgetItem(name)
            value_item = QTableWidgetItem(str(value))
            
            self.quantities_table.setItem(row, 0, name_item)
            self.quantities_table.setItem(row, 1, value_item)
            
    def update_surfaces_tab(self):
        """Update the surfaces tab with current space data."""
        if not self.current_space:
            return
            
        surfaces = self.current_space.surfaces
        
        # Update table
        self.surfaces_table.setRowCount(len(surfaces))
        total_area = 0.0
        
        for row, surface in enumerate(surfaces):
            type_item = QTableWidgetItem(surface.type)
            area_item = QTableWidgetItem(f"{surface.area:.2f}")
            material_item = QTableWidgetItem(surface.material or "Unknown")
            description_item = QTableWidgetItem(surface.user_description or "")
            
            # Store surface ID for selection
            type_item.setData(Qt.ItemDataRole.UserRole, surface.id)
            
            self.surfaces_table.setItem(row, 0, type_item)
            self.surfaces_table.setItem(row, 1, area_item)
            self.surfaces_table.setItem(row, 2, material_item)
            self.surfaces_table.setItem(row, 3, description_item)
            
            total_area += surface.area
            
        # Update summary
        surface_areas = self.current_space.get_surface_area_by_type()
        summary_parts = [f"Total Surfaces: {len(surfaces)}", f"Total Area: {total_area:.2f} m²"]
        
        if surface_areas:
            summary_parts.append("Areas by Type:")
            for surface_type, area in surface_areas.items():
                summary_parts.append(f"  {surface_type}: {area:.2f} m²")
                
        self.surface_summary_label.setText(" | ".join(summary_parts))
        
    def update_boundaries_tab(self):
        """Update the space boundaries tab with current space data."""
        if not self.current_space or not hasattr(self.current_space, 'space_boundaries'):
            self.boundaries_table.setRowCount(0)
            self.boundary_summary_label.setText("No space boundaries data")
            return
            
        boundaries = self.current_space.space_boundaries
        
        # Update table
        self.boundaries_table.setRowCount(len(boundaries))
        total_area = 0.0
        physical_count = 0
        virtual_count = 0
        
        for row, boundary in enumerate(boundaries):
            label_item = QTableWidgetItem(boundary.display_label or boundary.name)
            type_item = QTableWidgetItem(boundary.physical_or_virtual_boundary)
            orientation_item = QTableWidgetItem(boundary.boundary_orientation or "Unknown")
            area_item = QTableWidgetItem(f"{boundary.calculated_area:.2f}")
            element_type_item = QTableWidgetItem(boundary.related_building_element_type or "None")
            level_item = QTableWidgetItem(f"Level {boundary.boundary_level}")
            
            # Store boundary GUID for selection
            label_item.setData(Qt.ItemDataRole.UserRole, boundary.guid)
            
            self.boundaries_table.setItem(row, 0, label_item)
            self.boundaries_table.setItem(row, 1, type_item)
            self.boundaries_table.setItem(row, 2, orientation_item)
            self.boundaries_table.setItem(row, 3, area_item)
            self.boundaries_table.setItem(row, 4, element_type_item)
            self.boundaries_table.setItem(row, 5, level_item)
            
            total_area += boundary.calculated_area
            
            if boundary.is_physical_boundary():
                physical_count += 1
            elif boundary.is_virtual_boundary():
                virtual_count += 1
                
        # Update summary
        summary_parts = [
            f"Total Boundaries: {len(boundaries)}",
            f"Total Area: {total_area:.2f} m²",
            f"Physical: {physical_count}",
            f"Virtual: {virtual_count}"
        ]
        
        self.boundary_summary_label.setText(" | ".join(summary_parts))
        
    def update_relationships_tab(self):
        """Update the relationships tab with current space data."""
        if not self.current_space:
            return
            
        relationships = self.current_space.relationships
        
        # Update table
        self.relationships_table.setRowCount(len(relationships))
        
        for row, relationship in enumerate(relationships):
            type_item = QTableWidgetItem(relationship.relationship_type)
            entity_item = QTableWidgetItem(relationship.related_entity_name or relationship.related_entity_guid)
            description_item = QTableWidgetItem(relationship.related_entity_description or "")
            
            self.relationships_table.setItem(row, 0, type_item)
            self.relationships_table.setItem(row, 1, entity_item)
            self.relationships_table.setItem(row, 2, description_item)
            
        # Update summary
        if relationships:
            relationship_types = {}
            for rel in relationships:
                rel_type = rel.relationship_type
                relationship_types[rel_type] = relationship_types.get(rel_type, 0) + 1
                
            summary_parts = [f"Total: {len(relationships)}"]
            for rel_type, count in relationship_types.items():
                summary_parts.append(f"{rel_type}: {count}")
                
            self.relationships_summary_label.setText(" | ".join(summary_parts))
        else:
            self.relationships_summary_label.setText("No relationships found")
            
    def on_surface_clicked(self, item: QTableWidgetItem):
        """Handle surface table item click."""
        surface_id = item.data(Qt.ItemDataRole.UserRole)
        if surface_id:
            self.surface_selected.emit(surface_id)
            
    def on_boundary_clicked(self, item: QTableWidgetItem):
        """Handle boundary table item click."""
        boundary_guid = item.data(Qt.ItemDataRole.UserRole)
        if boundary_guid:
            self.boundary_selected.emit(boundary_guid)
            
    def show_empty_state(self):
        """Show empty state when no space is selected."""
        self.title_label.setText("Space Details")
        self.basic_properties_label.setText("No space selected")
        
        # Clear all tables
        self.quantities_table.setRowCount(0)
        self.surfaces_table.setRowCount(0)
        self.boundaries_table.setRowCount(0)
        self.relationships_table.setRowCount(0)
        
        # Clear summaries
        self.surface_summary_label.setText("No surfaces data")
        self.boundary_summary_label.setText("No space boundaries data")
        self.relationships_summary_label.setText("No relationships data")
        
        # Disable the widget
        self.setEnabled(False)
        
    def clear_selection(self):
        """Clear current space selection."""
        self.current_space = None
        self.show_empty_state()
        
    def get_current_space(self) -> Optional[SpaceData]:
        """Get the currently displayed space."""
        return self.current_space