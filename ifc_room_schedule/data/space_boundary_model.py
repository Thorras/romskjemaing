"""
Space Boundary Model

Data model for representing IFC space boundary information.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional


@dataclass
class SpaceBoundaryData:
    """Data model for IFC space boundary information."""

    id: str
    guid: str
    name: str
    description: str
    physical_or_virtual_boundary: str  # "Physical", "Virtual", "Undefined"
    internal_or_external_boundary: str  # "Internal", "External", "Undefined"
    related_building_element_guid: str
    related_building_element_name: str
    related_building_element_type: str  # "IfcWall", "IfcSlab", "IfcWindow", etc.
    related_space_guid: str
    adjacent_space_guid: str = ""  # For 2nd level boundaries
    adjacent_space_name: str = ""
    boundary_surface_type: str = ""  # "Wall", "Floor", "Ceiling", "Opening"
    boundary_orientation: str = ""  # "North", "South", "East", "West", "Horizontal"
    connection_geometry: Dict[str, Any] = field(default_factory=dict)  # IFC geometric representation
    calculated_area: float = 0.0
    thermal_properties: Dict[str, Any] = field(default_factory=dict)
    material_properties: Dict[str, Any] = field(default_factory=dict)
    user_description: str = ""
    boundary_level: int = 1  # 1st level (space-to-element) or 2nd level (space-to-space)
    display_label: str = ""  # Human-readable identification like "North Wall to Office 101"

    def __post_init__(self):
        """Validate space boundary data after initialization."""
        if not self.guid:
            raise ValueError("GUID is required for space boundary data")
        if not isinstance(self.guid, str):
            raise TypeError("GUID must be a string")
        if not isinstance(self.calculated_area, (int, float)):
            raise TypeError("Calculated area must be a number")
        if self.calculated_area < 0:
            raise ValueError("Calculated area cannot be negative")
        if self.boundary_level not in [1, 2]:
            raise ValueError("Boundary level must be 1 or 2")

    def is_physical_boundary(self) -> bool:
        """Check if this is a physical boundary."""
        return self.physical_or_virtual_boundary.lower() == "physical"

    def is_virtual_boundary(self) -> bool:
        """Check if this is a virtual boundary."""
        return self.physical_or_virtual_boundary.lower() == "virtual"

    def is_internal_boundary(self) -> bool:
        """Check if this is an internal boundary."""
        return self.internal_or_external_boundary.lower() == "internal"

    def is_external_boundary(self) -> bool:
        """Check if this is an external boundary."""
        return self.internal_or_external_boundary.lower() == "external"

    def is_first_level_boundary(self) -> bool:
        """Check if this is a 1st level boundary (space-to-element)."""
        return self.boundary_level == 1

    def is_second_level_boundary(self) -> bool:
        """Check if this is a 2nd level boundary (space-to-space)."""
        return self.boundary_level == 2

    def get_thermal_property(self, property_name: str) -> Optional[Any]:
        """Get a thermal property by name."""
        return self.thermal_properties.get(property_name)

    def set_thermal_property(self, property_name: str, value: Any) -> None:
        """Set a thermal property."""
        if not isinstance(property_name, str):
            raise TypeError("Property name must be a string")
        self.thermal_properties[property_name] = value

    def get_material_property(self, property_name: str) -> Optional[Any]:
        """Get a material property by name."""
        return self.material_properties.get(property_name)

    def set_material_property(self, property_name: str, value: Any) -> None:
        """Set a material property."""
        if not isinstance(property_name, str):
            raise TypeError("Property name must be a string")
        self.material_properties[property_name] = value

    def generate_display_label(self) -> str:
        """
        Generate a human-readable display label for this boundary.
        
        Returns:
            Human-readable label like "North Wall to Office 101"
        """
        # Start with orientation if available
        label_parts = []
        
        if self.boundary_orientation:
            label_parts.append(self.boundary_orientation)
        
        # Add surface type
        if self.boundary_surface_type:
            label_parts.append(self.boundary_surface_type)
        elif self.related_building_element_type:
            # Convert IFC type to readable format
            element_type = self.related_building_element_type.replace("Ifc", "")
            if element_type.lower() == "wall":
                label_parts.append("Wall")
            elif element_type.lower() == "slab":
                label_parts.append("Floor/Ceiling")
            elif element_type.lower() in ["window", "door"]:
                label_parts.append(element_type)
            else:
                label_parts.append(element_type)
        
        # Add connection information
        if self.is_second_level_boundary() and self.adjacent_space_name:
            label_parts.append(f"to {self.adjacent_space_name}")
        elif self.related_building_element_name:
            label_parts.append(f"({self.related_building_element_name})")
        
        # Fallback to basic information if no specific parts
        if not label_parts:
            if self.name:
                return self.name
            else:
                return f"Boundary {self.guid[-8:]}"
        
        return " ".join(label_parts)

    def update_display_label(self) -> None:
        """Update the display label based on current properties."""
        self.display_label = self.generate_display_label()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'guid': self.guid,
            'name': self.name,
            'description': self.description,
            'physical_or_virtual_boundary': self.physical_or_virtual_boundary,
            'internal_or_external_boundary': self.internal_or_external_boundary,
            'related_building_element_guid': self.related_building_element_guid,
            'related_building_element_name': self.related_building_element_name,
            'related_building_element_type': self.related_building_element_type,
            'related_space_guid': self.related_space_guid,
            'adjacent_space_guid': self.adjacent_space_guid,
            'adjacent_space_name': self.adjacent_space_name,
            'boundary_surface_type': self.boundary_surface_type,
            'boundary_orientation': self.boundary_orientation,
            'connection_geometry': self.connection_geometry,
            'calculated_area': self.calculated_area,
            'thermal_properties': self.thermal_properties,
            'material_properties': self.material_properties,
            'user_description': self.user_description,
            'boundary_level': self.boundary_level,
            'display_label': self.display_label
        }