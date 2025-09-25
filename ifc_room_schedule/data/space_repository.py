"""
Space Repository

In-memory data management for IFC space data.
"""

from typing import Dict, List, Optional, Set
from .space_model import SpaceData
from .surface_model import SurfaceData
from .relationship_model import RelationshipData


class SpaceRepository:
    """Repository for managing space data in memory."""
    
    def __init__(self):
        """Initialize the repository with empty data structures."""
        self._spaces: Dict[str, SpaceData] = {}
        self._surfaces_by_space: Dict[str, List[SurfaceData]] = {}
        self._relationships_by_space: Dict[str, List[RelationshipData]] = {}
    
    def add_space(self, space_data: SpaceData) -> None:
        """Add a space to the repository."""
        if not isinstance(space_data, SpaceData):
            raise TypeError("space_data must be a SpaceData instance")
        
        self._spaces[space_data.guid] = space_data
        
        # Initialize collections for this space if not exists
        if space_data.guid not in self._surfaces_by_space:
            self._surfaces_by_space[space_data.guid] = []
        if space_data.guid not in self._relationships_by_space:
            self._relationships_by_space[space_data.guid] = []
    
    def get_space(self, guid: str) -> Optional[SpaceData]:
        """Get a space by its GUID."""
        if not isinstance(guid, str):
            raise TypeError("GUID must be a string")
        return self._spaces.get(guid)
    
    def get_all_spaces(self) -> List[SpaceData]:
        """Get all spaces in the repository."""
        return list(self._spaces.values())
    
    def update_space(self, space_data: SpaceData) -> None:
        """Update an existing space in the repository."""
        if not isinstance(space_data, SpaceData):
            raise TypeError("space_data must be a SpaceData instance")
        
        if space_data.guid not in self._spaces:
            raise ValueError(f"Space with GUID {space_data.guid} not found")
        
        self._spaces[space_data.guid] = space_data
    
    def remove_space(self, guid: str) -> bool:
        """Remove a space from the repository."""
        if not isinstance(guid, str):
            raise TypeError("GUID must be a string")
        
        if guid in self._spaces:
            del self._spaces[guid]
            # Clean up related data
            if guid in self._surfaces_by_space:
                del self._surfaces_by_space[guid]
            if guid in self._relationships_by_space:
                del self._relationships_by_space[guid]
            return True
        return False
    
    def add_surface_to_space(self, space_guid: str, surface: SurfaceData) -> None:
        """Add a surface to a specific space."""
        if not isinstance(space_guid, str):
            raise TypeError("Space GUID must be a string")
        if not isinstance(surface, SurfaceData):
            raise TypeError("surface must be a SurfaceData instance")
        
        if space_guid not in self._spaces:
            raise ValueError(f"Space with GUID {space_guid} not found")
        
        # Ensure surface is associated with the correct space
        if surface.related_space_guid != space_guid:
            raise ValueError("Surface is not associated with the specified space")
        
        if space_guid not in self._surfaces_by_space:
            self._surfaces_by_space[space_guid] = []
        
        # Avoid duplicates
        if surface not in self._surfaces_by_space[space_guid]:
            self._surfaces_by_space[space_guid].append(surface)
            # Also add to the space object
            self._spaces[space_guid].add_surface(surface)
    
    def get_surfaces_by_space(self, space_guid: str) -> List[SurfaceData]:
        """Get all surfaces for a specific space."""
        if not isinstance(space_guid, str):
            raise TypeError("Space GUID must be a string")
        return self._surfaces_by_space.get(space_guid, [])
    
    def add_relationship_to_space(self, space_guid: str, relationship: RelationshipData) -> None:
        """Add a relationship to a specific space."""
        if not isinstance(space_guid, str):
            raise TypeError("Space GUID must be a string")
        if not isinstance(relationship, RelationshipData):
            raise TypeError("relationship must be a RelationshipData instance")
        
        if space_guid not in self._spaces:
            raise ValueError(f"Space with GUID {space_guid} not found")
        
        if space_guid not in self._relationships_by_space:
            self._relationships_by_space[space_guid] = []
        
        # Avoid duplicates
        if relationship not in self._relationships_by_space[space_guid]:
            self._relationships_by_space[space_guid].append(relationship)
            # Also add to the space object
            self._spaces[space_guid].add_relationship(relationship)
    
    def get_relationships_by_space(self, space_guid: str) -> List[RelationshipData]:
        """Get all relationships for a specific space."""
        if not isinstance(space_guid, str):
            raise TypeError("Space GUID must be a string")
        return self._relationships_by_space.get(space_guid, [])
    
    def update_space_description(self, space_guid: str, key: str, description: str) -> None:
        """Update a user description for a space."""
        if not isinstance(space_guid, str):
            raise TypeError("Space GUID must be a string")
        
        space = self.get_space(space_guid)
        if not space:
            raise ValueError(f"Space with GUID {space_guid} not found")
        
        space.set_user_description(key, description)
    
    def update_surface_description(self, space_guid: str, surface_id: str, description: str) -> None:
        """Update the description of a surface."""
        if not isinstance(space_guid, str):
            raise TypeError("Space GUID must be a string")
        if not isinstance(surface_id, str):
            raise TypeError("Surface ID must be a string")
        if not isinstance(description, str):
            raise TypeError("Description must be a string")
        
        surfaces = self.get_surfaces_by_space(space_guid)
        for surface in surfaces:
            if surface.id == surface_id:
                surface.set_user_description(description)
                return
        
        raise ValueError(f"Surface with ID {surface_id} not found in space {space_guid}")
    
    def get_space_count(self) -> int:
        """Get the total number of spaces in the repository."""
        return len(self._spaces)
    
    def get_processed_space_count(self) -> int:
        """Get the number of processed spaces."""
        return sum(1 for space in self._spaces.values() if space.processed)
    
    def mark_space_processed(self, space_guid: str) -> None:
        """Mark a space as processed."""
        space = self.get_space(space_guid)
        if not space:
            raise ValueError(f"Space with GUID {space_guid} not found")
        space.processed = True
    
    def get_total_surface_area(self) -> float:
        """Get total surface area across all spaces."""
        total_area = 0.0
        for space in self._spaces.values():
            total_area += space.get_total_surface_area()
        return total_area
    
    def get_surface_area_by_type(self) -> Dict[str, float]:
        """Get surface areas grouped by type across all spaces."""
        areas_by_type = {}
        for space in self._spaces.values():
            space_areas = space.get_surface_area_by_type()
            for surface_type, area in space_areas.items():
                if surface_type not in areas_by_type:
                    areas_by_type[surface_type] = 0
                areas_by_type[surface_type] += area
        return areas_by_type
    
    def validate_data_integrity(self) -> List[str]:
        """Validate data integrity and return list of issues found."""
        issues = []
        
        for space_guid, space in self._spaces.items():
            # Check if space has surfaces
            space_surfaces = self.get_surfaces_by_space(space_guid)
            if len(space_surfaces) != len(space.surfaces):
                issues.append(f"Surface count mismatch for space {space_guid}")
            
            # Check if all surfaces reference the correct space
            for surface in space_surfaces:
                if surface.related_space_guid != space_guid:
                    issues.append(f"Surface {surface.id} references wrong space GUID")
            
            # Check if space has relationships
            space_relationships = self.get_relationships_by_space(space_guid)
            if len(space_relationships) != len(space.relationships):
                issues.append(f"Relationship count mismatch for space {space_guid}")
        
        return issues
    
    def clear(self) -> None:
        """Clear all data from the repository."""
        self._spaces.clear()
        self._surfaces_by_space.clear()
        self._relationships_by_space.clear()
    
    def get_spaces_by_type(self, object_type: str) -> List[SpaceData]:
        """Get all spaces of a specific object type."""
        if not isinstance(object_type, str):
            raise TypeError("Object type must be a string")
        
        return [space for space in self._spaces.values() 
                if space.object_type == object_type]
    
    def search_spaces_by_name(self, name_pattern: str) -> List[SpaceData]:
        """Search spaces by name pattern (case-insensitive)."""
        if not isinstance(name_pattern, str):
            raise TypeError("Name pattern must be a string")
        
        pattern_lower = name_pattern.lower()
        return [space for space in self._spaces.values() 
                if (pattern_lower in space.name.lower() or 
                    pattern_lower in space.long_name.lower())]