"""
Space Model

Data model for representing spatial information.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from .surface_model import SurfaceData
from .relationship_model import RelationshipData


@dataclass
class SpaceData:
    """Data model for IFC space information."""

    guid: str
    name: str
    long_name: str
    description: str
    object_type: str
    zone_category: str
    number: str
    elevation: float
    quantities: Dict[str, float] = field(default_factory=dict)
    surfaces: List['SurfaceData'] = field(default_factory=list)
    relationships: List['RelationshipData'] = field(default_factory=list)
    user_descriptions: Dict[str, str] = field(default_factory=dict)
    processed: bool = False

    def __post_init__(self):
        """Validate space data after initialization."""
        if not self.guid:
            raise ValueError("GUID is required for space data")
        if not isinstance(self.guid, str):
            raise TypeError("GUID must be a string")
        if not self.name:
            raise ValueError("Name is required for space data")
        if not isinstance(self.elevation, (int, float)):
            raise TypeError("Elevation must be a number")

    def add_surface(self, surface: 'SurfaceData') -> None:
        """Add a surface to this space."""
        if not isinstance(surface, SurfaceData):
            raise TypeError("Surface must be a SurfaceData instance")
        if surface not in self.surfaces:
            self.surfaces.append(surface)

    def add_relationship(self, relationship: 'RelationshipData') -> None:
        """Add a relationship to this space."""
        if not isinstance(relationship, RelationshipData):
            raise TypeError("Relationship must be a RelationshipData instance")
        if relationship not in self.relationships:
            self.relationships.append(relationship)

    def get_total_surface_area(self) -> float:
        """Calculate total surface area for this space."""
        return sum(surface.area for surface in self.surfaces if surface.area > 0)

    def get_surface_area_by_type(self) -> Dict[str, float]:
        """Get surface areas grouped by type."""
        areas_by_type = {}
        for surface in self.surfaces:
            surface_type = surface.type
            if surface_type not in areas_by_type:
                areas_by_type[surface_type] = 0
            areas_by_type[surface_type] += surface.area
        return areas_by_type

    def set_user_description(self, key: str, description: str) -> None:
        """Set a user description for this space."""
        if not isinstance(key, str) or not isinstance(description, str):
            raise TypeError("Key and description must be strings")
        self.user_descriptions[key] = description

    def get_user_description(self, key: str) -> Optional[str]:
        """Get a user description for this space."""
        return self.user_descriptions.get(key)


# Legacy class for backward compatibility
class Space(SpaceData):
    """Legacy Space class - use SpaceData instead."""
    pass