"""
Space Model

Data model for representing spatial information.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from .surface_model import SurfaceData
from .relationship_model import RelationshipData
from .space_boundary_model import SpaceBoundaryData


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
    space_boundaries: List['SpaceBoundaryData'] = field(default_factory=list)
    relationships: List['RelationshipData'] = field(default_factory=list)
    user_descriptions: Dict[str, str] = field(default_factory=dict)
    processed: bool = False

    def __post_init__(self):
        """Validate space data after initialization."""
        if not self.guid:
            raise ValueError("GUID is required for space data")
        if not isinstance(self.guid, str):
            raise TypeError("GUID must be a string")
        # Allow empty names during creation, validation happens later
        # if not self.name and not self.long_name:
        #     raise ValueError("Either name or long_name is required")
        if not isinstance(self.elevation, (int, float)):
            raise TypeError("Elevation must be a number")

    def add_surface(self, surface: 'SurfaceData') -> None:
        """Add a surface to this space."""
        if not isinstance(surface, SurfaceData):
            raise TypeError("Surface must be a SurfaceData instance")
        if surface not in self.surfaces:
            self.surfaces.append(surface)

    def add_space_boundary(self, space_boundary: 'SpaceBoundaryData') -> None:
        """Add a space boundary to this space."""
        if not isinstance(space_boundary, SpaceBoundaryData):
            raise TypeError("Space boundary must be a SpaceBoundaryData instance")
        if space_boundary not in self.space_boundaries:
            self.space_boundaries.append(space_boundary)

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

    def get_total_boundary_area(self) -> float:
        """Calculate total space boundary area for this space."""
        return sum(boundary.calculated_area for boundary in self.space_boundaries if boundary.calculated_area > 0)

    def get_boundary_area_by_type(self) -> Dict[str, float]:
        """Get space boundary areas grouped by surface type."""
        areas_by_type = {}
        for boundary in self.space_boundaries:
            boundary_type = boundary.boundary_surface_type or "Unknown"
            if boundary_type not in areas_by_type:
                areas_by_type[boundary_type] = 0
            areas_by_type[boundary_type] += boundary.calculated_area
        return areas_by_type

    def get_boundary_area_by_orientation(self) -> Dict[str, float]:
        """Get space boundary areas grouped by orientation."""
        areas_by_orientation = {}
        for boundary in self.space_boundaries:
            orientation = boundary.boundary_orientation or "Unknown"
            if orientation not in areas_by_orientation:
                areas_by_orientation[orientation] = 0
            areas_by_orientation[orientation] += boundary.calculated_area
        return areas_by_orientation

    def get_physical_boundaries(self) -> List['SpaceBoundaryData']:
        """Get all physical boundaries for this space."""
        return [boundary for boundary in self.space_boundaries if boundary.is_physical_boundary()]

    def get_virtual_boundaries(self) -> List['SpaceBoundaryData']:
        """Get all virtual boundaries for this space."""
        return [boundary for boundary in self.space_boundaries if boundary.is_virtual_boundary()]

    def get_external_boundaries(self) -> List['SpaceBoundaryData']:
        """Get all external boundaries for this space."""
        return [boundary for boundary in self.space_boundaries if boundary.is_external_boundary()]

    def get_internal_boundaries(self) -> List['SpaceBoundaryData']:
        """Get all internal boundaries for this space."""
        return [boundary for boundary in self.space_boundaries if boundary.is_internal_boundary()]

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