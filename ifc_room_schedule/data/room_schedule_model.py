"""
Room Schedule Model

Data model for representing room schedule information.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from .space_model import SpaceData


@dataclass
class RoomScheduleMetadata:
    """Metadata for room schedule export."""
    
    export_date: datetime = field(default_factory=datetime.now)
    source_file: str = ""
    application_name: str = "IFC Room Schedule"
    application_version: str = "1.0.0"
    total_spaces: int = 0
    processed_spaces: int = 0
    total_surface_area: float = 0.0
    ifc_schema: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary for export."""
        return {
            "export_date": self.export_date.isoformat(),
            "source_file": self.source_file,
            "application_name": self.application_name,
            "application_version": self.application_version,
            "total_spaces": self.total_spaces,
            "processed_spaces": self.processed_spaces,
            "total_surface_area": self.total_surface_area,
            "ifc_schema": self.ifc_schema
        }


@dataclass
class RoomSchedule:
    """Complete room schedule data model for export."""
    
    metadata: RoomScheduleMetadata = field(default_factory=RoomScheduleMetadata)
    spaces: List[SpaceData] = field(default_factory=list)
    summary_statistics: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize summary statistics after creation."""
        self._update_summary_statistics()
    
    def add_space(self, space: SpaceData) -> None:
        """Add a space to the room schedule."""
        if not isinstance(space, SpaceData):
            raise TypeError("space must be a SpaceData instance")
        
        if space not in self.spaces:
            self.spaces.append(space)
            self._update_summary_statistics()
    
    def remove_space(self, space_guid: str) -> bool:
        """Remove a space from the room schedule."""
        if not isinstance(space_guid, str):
            raise TypeError("space_guid must be a string")
        
        for i, space in enumerate(self.spaces):
            if space.guid == space_guid:
                del self.spaces[i]
                self._update_summary_statistics()
                return True
        return False
    
    def get_space(self, space_guid: str) -> Optional[SpaceData]:
        """Get a space by GUID."""
        if not isinstance(space_guid, str):
            raise TypeError("space_guid must be a string")
        
        for space in self.spaces:
            if space.guid == space_guid:
                return space
        return None
    
    def get_spaces_by_type(self, object_type: str) -> List[SpaceData]:
        """Get all spaces of a specific object type."""
        if not isinstance(object_type, str):
            raise TypeError("object_type must be a string")
        
        return [space for space in self.spaces if space.object_type == object_type]
    
    def get_spaces_by_zone(self, zone_category: str) -> List[SpaceData]:
        """Get all spaces in a specific zone category."""
        if not isinstance(zone_category, str):
            raise TypeError("zone_category must be a string")
        
        return [space for space in self.spaces if space.zone_category == zone_category]
    
    def _update_summary_statistics(self) -> None:
        """Update summary statistics based on current spaces."""
        if not self.spaces:
            self.summary_statistics = {
                "total_spaces": 0,
                "processed_spaces": 0,
                "total_surface_area": 0.0,
                "surface_area_by_type": {},
                "spaces_by_type": {},
                "spaces_by_zone": {},
                "average_space_area": 0.0
            }
            return
        
        # Basic counts
        total_spaces = len(self.spaces)
        processed_spaces = sum(1 for space in self.spaces if space.processed)
        
        # Surface area calculations
        total_surface_area = sum(space.get_total_surface_area() for space in self.spaces)
        surface_area_by_type = {}
        
        for space in self.spaces:
            space_areas = space.get_surface_area_by_type()
            for surface_type, area in space_areas.items():
                if surface_type not in surface_area_by_type:
                    surface_area_by_type[surface_type] = 0
                surface_area_by_type[surface_type] += area
        
        # Space categorization
        spaces_by_type = {}
        spaces_by_zone = {}
        
        for space in self.spaces:
            # Count by object type
            if space.object_type not in spaces_by_type:
                spaces_by_type[space.object_type] = 0
            spaces_by_type[space.object_type] += 1
            
            # Count by zone category
            if space.zone_category not in spaces_by_zone:
                spaces_by_zone[space.zone_category] = 0
            spaces_by_zone[space.zone_category] += 1
        
        # Calculate average space area
        space_areas = [space.get_total_surface_area() for space in self.spaces]
        average_space_area = sum(space_areas) / len(space_areas) if space_areas else 0.0
        
        self.summary_statistics = {
            "total_spaces": total_spaces,
            "processed_spaces": processed_spaces,
            "total_surface_area": total_surface_area,
            "surface_area_by_type": surface_area_by_type,
            "spaces_by_type": spaces_by_type,
            "spaces_by_zone": spaces_by_zone,
            "average_space_area": average_space_area
        }
        
        # Update metadata
        self.metadata.total_spaces = total_spaces
        self.metadata.processed_spaces = processed_spaces
        self.metadata.total_surface_area = total_surface_area
    
    def validate_completeness(self) -> List[str]:
        """Validate data completeness and return list of issues."""
        issues = []
        
        if not self.spaces:
            issues.append("No spaces in room schedule")
            return issues
        
        for space in self.spaces:
            # Check for required space data
            if not space.name:
                issues.append(f"Space {space.guid} missing name")
            
            if not space.surfaces:
                issues.append(f"Space {space.guid} has no surfaces")
            
            # Check for surface data completeness
            for surface in space.surfaces:
                if surface.area <= 0:
                    issues.append(f"Surface {surface.id} in space {space.guid} has invalid area")
                
                if not surface.type:
                    issues.append(f"Surface {surface.id} in space {space.guid} missing type")
        
        return issues
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert room schedule to dictionary for export."""
        return {
            "metadata": self.metadata.to_dict(),
            "summary_statistics": self.summary_statistics,
            "spaces": [self._space_to_dict(space) for space in self.spaces]
        }
    
    def _space_to_dict(self, space: SpaceData) -> Dict[str, Any]:
        """Convert a space to dictionary format."""
        return {
            "guid": space.guid,
            "name": space.name,
            "long_name": space.long_name,
            "description": space.description,
            "object_type": space.object_type,
            "zone_category": space.zone_category,
            "number": space.number,
            "elevation": space.elevation,
            "quantities": space.quantities,
            "processed": space.processed,
            "user_descriptions": space.user_descriptions,
            "surfaces": [self._surface_to_dict(surface) for surface in space.surfaces],
            "relationships": [self._relationship_to_dict(rel) for rel in space.relationships],
            "total_surface_area": space.get_total_surface_area(),
            "surface_area_by_type": space.get_surface_area_by_type()
        }
    
    def _surface_to_dict(self, surface) -> Dict[str, Any]:
        """Convert a surface to dictionary format."""
        return {
            "id": surface.id,
            "type": surface.type,
            "area": surface.area,
            "material": surface.material,
            "ifc_type": surface.ifc_type,
            "user_description": surface.user_description,
            "properties": surface.properties
        }
    
    def _relationship_to_dict(self, relationship) -> Dict[str, Any]:
        """Convert a relationship to dictionary format."""
        return {
            "related_entity_guid": relationship.related_entity_guid,
            "related_entity_name": relationship.related_entity_name,
            "related_entity_description": relationship.related_entity_description,
            "relationship_type": relationship.relationship_type,
            "ifc_relationship_type": relationship.ifc_relationship_type,
            "display_name": relationship.get_display_name(),
            "is_spatial": relationship.is_spatial_relationship()
        }
    
    def get_completion_percentage(self) -> float:
        """Get completion percentage of processed spaces."""
        if not self.spaces:
            return 0.0
        return (self.summary_statistics["processed_spaces"] / 
                self.summary_statistics["total_spaces"]) * 100.0