"""
Surface Model

Data model for representing surface information.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional


@dataclass
class SurfaceData:
    """Data model for surface information associated with IFC spaces."""
    
    id: str
    type: str  # "Wall", "Floor", "Ceiling", "Opening"
    area: float
    material: str
    ifc_type: str
    related_space_guid: str
    user_description: str = ""
    properties: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate surface data after initialization."""
        if not self.id:
            raise ValueError("Surface ID is required")
        if not isinstance(self.id, str):
            raise TypeError("Surface ID must be a string")
        if not self.type:
            raise ValueError("Surface type is required")
        if not isinstance(self.area, (int, float)):
            raise TypeError("Surface area must be a number")
        if self.area < 0:
            raise ValueError("Surface area cannot be negative")
        if not self.related_space_guid:
            raise ValueError("Related space GUID is required")
        if not isinstance(self.related_space_guid, str):
            raise TypeError("Related space GUID must be a string")
    
    def set_user_description(self, description: str) -> None:
        """Set user description for this surface."""
        if not isinstance(description, str):
            raise TypeError("Description must be a string")
        self.user_description = description
    
    def add_property(self, key: str, value: Any) -> None:
        """Add a property to this surface."""
        if not isinstance(key, str):
            raise TypeError("Property key must be a string")
        self.properties[key] = value
    
    def get_property(self, key: str, default: Any = None) -> Any:
        """Get a property value for this surface."""
        return self.properties.get(key, default)
    
    def has_material(self) -> bool:
        """Check if surface has material information."""
        return bool(self.material and self.material.strip())
    
    def is_valid_area(self) -> bool:
        """Check if surface has a valid area value."""
        return isinstance(self.area, (int, float)) and self.area > 0


# Legacy class for backward compatibility
class Surface(SurfaceData):
    """Legacy Surface class - use SurfaceData instead."""
    pass