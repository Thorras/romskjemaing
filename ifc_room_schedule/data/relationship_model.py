"""
Relationship Model

Data model for representing IFC entity relationships.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class RelationshipData:
    """Data model for relationships between IFC entities."""
    
    related_entity_guid: str
    related_entity_name: str
    related_entity_description: str
    relationship_type: str  # "Contains", "Adjacent", "Serves", etc.
    ifc_relationship_type: str
    
    def __post_init__(self):
        """Validate relationship data after initialization."""
        if not self.related_entity_guid:
            raise ValueError("Related entity GUID is required")
        if not isinstance(self.related_entity_guid, str):
            raise TypeError("Related entity GUID must be a string")
        if not self.related_entity_name:
            raise ValueError("Related entity name is required")
        if not isinstance(self.related_entity_name, str):
            raise TypeError("Related entity name must be a string")
        if not self.relationship_type:
            raise ValueError("Relationship type is required")
        if not isinstance(self.relationship_type, str):
            raise TypeError("Relationship type must be a string")
        if not self.ifc_relationship_type:
            raise ValueError("IFC relationship type is required")
        if not isinstance(self.ifc_relationship_type, str):
            raise TypeError("IFC relationship type must be a string")
    
    def get_display_name(self) -> str:
        """Get a display-friendly name for this relationship."""
        if self.related_entity_description:
            return f"{self.related_entity_name} - {self.related_entity_description}"
        return self.related_entity_name
    
    def is_spatial_relationship(self) -> bool:
        """Check if this is a spatial relationship (contains, adjacent, etc.)."""
        spatial_types = ["Contains", "Adjacent", "Serves", "ConnectedTo", "ReferencedBy"]
        return self.relationship_type in spatial_types
    
    def __eq__(self, other) -> bool:
        """Check equality based on GUID and relationship type."""
        if not isinstance(other, RelationshipData):
            return False
        return (self.related_entity_guid == other.related_entity_guid and 
                self.relationship_type == other.relationship_type)
    
    def __hash__(self) -> int:
        """Hash based on GUID and relationship type for set operations."""
        return hash((self.related_entity_guid, self.relationship_type))