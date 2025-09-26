"""
JSON Builder

Handles building JSON export structure for room schedule data.
"""

import json
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional
from pathlib import Path

from ..data.space_model import SpaceData
from ..data.surface_model import SurfaceData
from ..data.space_boundary_model import SpaceBoundaryData
from ..data.relationship_model import RelationshipData


class JsonBuilder:
    """Builds JSON export structure from room schedule data."""
    
    def __init__(self):
        """Initialize the JSON builder."""
        self.source_file_path: Optional[str] = None
        self.ifc_version: Optional[str] = None
        self.application_version: str = "1.0.0"
    
    def set_source_file(self, file_path: str) -> None:
        """Set the source IFC file path."""
        self.source_file_path = file_path
    
    def set_ifc_version(self, version: str) -> None:
        """Set the IFC version."""
        self.ifc_version = version
    
    def build_json_structure(self, spaces: List[SpaceData], metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Build complete JSON structure from space data.
        
        Args:
            spaces: List of SpaceData objects to export
            metadata: Optional additional metadata
            
        Returns:
            Complete JSON structure ready for export
        """
        # Generate metadata
        export_metadata = self.generate_metadata(metadata)
        
        # Build spaces data
        spaces_data = []
        for space in spaces:
            space_dict = self._build_space_dict(space)
            spaces_data.append(space_dict)
        
        # Generate summary statistics
        summary = self._generate_summary(spaces)
        
        # Build complete structure
        json_structure = {
            "metadata": export_metadata,
            "spaces": spaces_data,
            "summary": summary
        }
        
        return json_structure
    
    def generate_metadata(self, additional_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate metadata for the export.
        
        Args:
            additional_metadata: Optional additional metadata to include
            
        Returns:
            Metadata dictionary
        """
        metadata = {
            "export_date": datetime.now().isoformat(),
            "application_version": self.application_version
        }
        
        if self.source_file_path:
            metadata["source_file"] = str(Path(self.source_file_path).name)
            metadata["source_file_path"] = str(self.source_file_path)
        
        if self.ifc_version:
            metadata["ifc_version"] = self.ifc_version
        
        if additional_metadata:
            metadata.update(additional_metadata)
        
        return metadata
    
    def _build_space_dict(self, space: SpaceData) -> Dict[str, Any]:
        """
        Build dictionary representation of a space.
        
        Args:
            space: SpaceData object to convert
            
        Returns:
            Dictionary representation of the space
        """
        space_dict = {
            "guid": space.guid,
            "properties": {
                "name": space.name,
                "long_name": space.long_name,
                "description": space.description,
                "object_type": space.object_type,
                "zone_category": space.zone_category,
                "number": space.number,
                "elevation": space.elevation,
                "quantities": space.quantities,
                "processed": space.processed,
                "user_descriptions": space.user_descriptions
            },
            "surfaces": [self._build_surface_dict(surface) for surface in space.surfaces],
            "space_boundaries": [self._build_space_boundary_dict(boundary) for boundary in space.space_boundaries],
            "relationships": [self._build_relationship_dict(relationship) for relationship in space.relationships]
        }
        
        return space_dict
    
    def _build_surface_dict(self, surface: SurfaceData) -> Dict[str, Any]:
        """
        Build dictionary representation of a surface.
        
        Args:
            surface: SurfaceData object to convert
            
        Returns:
            Dictionary representation of the surface
        """
        return {
            "id": surface.id,
            "type": surface.type,
            "area": surface.area,
            "material": surface.material,
            "ifc_type": surface.ifc_type,
            "related_space_guid": surface.related_space_guid,
            "user_description": surface.user_description,
            "properties": surface.properties
        }
    
    def _build_space_boundary_dict(self, boundary: SpaceBoundaryData) -> Dict[str, Any]:
        """
        Build dictionary representation of a space boundary.
        
        Args:
            boundary: SpaceBoundaryData object to convert
            
        Returns:
            Dictionary representation of the space boundary
        """
        return boundary.to_dict()
    
    def _build_relationship_dict(self, relationship: RelationshipData) -> Dict[str, Any]:
        """
        Build dictionary representation of a relationship.
        
        Args:
            relationship: RelationshipData object to convert
            
        Returns:
            Dictionary representation of the relationship
        """
        return {
            "related_entity_guid": relationship.related_entity_guid,
            "related_entity_name": relationship.related_entity_name,
            "related_entity_description": relationship.related_entity_description,
            "relationship_type": relationship.relationship_type,
            "ifc_relationship_type": relationship.ifc_relationship_type
        }
    
    def _generate_summary(self, spaces: List[SpaceData]) -> Dict[str, Any]:
        """
        Generate summary statistics for the export.
        
        Args:
            spaces: List of SpaceData objects
            
        Returns:
            Summary statistics dictionary
        """
        total_spaces = len(spaces)
        processed_spaces = sum(1 for space in spaces if space.processed)
        
        # Calculate total surface areas
        total_surface_area = 0.0
        surface_area_by_type = {}
        
        for space in spaces:
            total_surface_area += space.get_total_surface_area()
            space_areas_by_type = space.get_surface_area_by_type()
            for surface_type, area in space_areas_by_type.items():
                if surface_type not in surface_area_by_type:
                    surface_area_by_type[surface_type] = 0.0
                surface_area_by_type[surface_type] += area
        
        # Calculate total boundary areas
        total_boundary_area = 0.0
        boundary_area_by_type = {}
        boundary_area_by_orientation = {}
        
        for space in spaces:
            total_boundary_area += space.get_total_boundary_area()
            
            # By surface type
            space_boundary_areas_by_type = space.get_boundary_area_by_type()
            for boundary_type, area in space_boundary_areas_by_type.items():
                if boundary_type not in boundary_area_by_type:
                    boundary_area_by_type[boundary_type] = 0.0
                boundary_area_by_type[boundary_type] += area
            
            # By orientation
            space_boundary_areas_by_orientation = space.get_boundary_area_by_orientation()
            for orientation, area in space_boundary_areas_by_orientation.items():
                if orientation not in boundary_area_by_orientation:
                    boundary_area_by_orientation[orientation] = 0.0
                boundary_area_by_orientation[orientation] += area
        
        # Count boundaries by type
        physical_boundaries = 0
        virtual_boundaries = 0
        external_boundaries = 0
        internal_boundaries = 0
        first_level_boundaries = 0
        second_level_boundaries = 0
        
        for space in spaces:
            physical_boundaries += len(space.get_physical_boundaries())
            virtual_boundaries += len(space.get_virtual_boundaries())
            external_boundaries += len(space.get_external_boundaries())
            internal_boundaries += len(space.get_internal_boundaries())
            
            for boundary in space.space_boundaries:
                if boundary.is_first_level_boundary():
                    first_level_boundaries += 1
                elif boundary.is_second_level_boundary():
                    second_level_boundaries += 1
        
        summary = {
            "total_spaces": total_spaces,
            "processed_spaces": processed_spaces,
            "total_surface_area": round(total_surface_area, 2),
            "surface_area_by_type": {k: round(v, 2) for k, v in surface_area_by_type.items()},
            "total_boundary_area": round(total_boundary_area, 2),
            "boundary_area_by_type": {k: round(v, 2) for k, v in boundary_area_by_type.items()},
            "boundary_area_by_orientation": {k: round(v, 2) for k, v in boundary_area_by_orientation.items()},
            "boundary_counts": {
                "physical_boundaries": physical_boundaries,
                "virtual_boundaries": virtual_boundaries,
                "external_boundaries": external_boundaries,
                "internal_boundaries": internal_boundaries,
                "first_level_boundaries": first_level_boundaries,
                "second_level_boundaries": second_level_boundaries
            }
        }
        
        return summary
    
    def validate_export_data(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate export data for completeness and correctness.
        
        Args:
            data: JSON data structure to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Check required top-level keys
        required_keys = ["metadata", "spaces", "summary"]
        for key in required_keys:
            if key not in data:
                errors.append(f"Missing required key: {key}")
        
        if "metadata" in data:
            metadata = data["metadata"]
            if "export_date" not in metadata:
                errors.append("Missing export_date in metadata")
            if "application_version" not in metadata:
                errors.append("Missing application_version in metadata")
        
        if "spaces" in data:
            spaces = data["spaces"]
            if not isinstance(spaces, list):
                errors.append("Spaces must be a list")
            else:
                for i, space in enumerate(spaces):
                    space_errors = self._validate_space_data(space, i)
                    errors.extend(space_errors)
        
        if "summary" in data:
            summary = data["summary"]
            required_summary_keys = ["total_spaces", "processed_spaces", "total_surface_area"]
            for key in required_summary_keys:
                if key not in summary:
                    errors.append(f"Missing required summary key: {key}")
        
        return len(errors) == 0, errors
    
    def _validate_space_data(self, space_data: Dict[str, Any], space_index: int) -> List[str]:
        """
        Validate individual space data.
        
        Args:
            space_data: Space data dictionary
            space_index: Index of space for error reporting
            
        Returns:
            List of validation errors
        """
        errors = []
        prefix = f"Space {space_index}"
        
        # Check required keys
        if "guid" not in space_data:
            errors.append(f"{prefix}: Missing GUID")
        
        if "properties" not in space_data:
            errors.append(f"{prefix}: Missing properties")
        else:
            properties = space_data["properties"]
            required_props = ["name", "long_name", "object_type"]
            for prop in required_props:
                if prop not in properties:
                    errors.append(f"{prefix}: Missing property {prop}")
        
        # Check data types
        if "surfaces" in space_data and not isinstance(space_data["surfaces"], list):
            errors.append(f"{prefix}: Surfaces must be a list")
        
        if "space_boundaries" in space_data and not isinstance(space_data["space_boundaries"], list):
            errors.append(f"{prefix}: Space boundaries must be a list")
        
        if "relationships" in space_data and not isinstance(space_data["relationships"], list):
            errors.append(f"{prefix}: Relationships must be a list")
        
        return errors
    
    def write_json_file(self, filename: str, data: Dict[str, Any], indent: int = 2) -> bool:
        """
        Write JSON data to file.
        
        Args:
            filename: Output filename
            data: JSON data to write
            indent: JSON indentation level
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=indent, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error writing JSON file: {e}")
            return False
    
    def export_to_json(self, spaces: List[SpaceData], filename: str, 
                      metadata: Optional[Dict[str, Any]] = None, 
                      validate: bool = True) -> Tuple[bool, List[str]]:
        """
        Complete export workflow: build, validate, and write JSON.
        
        Args:
            spaces: List of SpaceData objects to export
            filename: Output filename
            metadata: Optional additional metadata
            validate: Whether to validate data before export
            
        Returns:
            Tuple of (success, list_of_errors_or_messages)
        """
        try:
            # Build JSON structure
            json_data = self.build_json_structure(spaces, metadata)
            
            # Validate if requested
            if validate:
                is_valid, validation_errors = self.validate_export_data(json_data)
                if not is_valid:
                    return False, validation_errors
            
            # Write to file
            success = self.write_json_file(filename, json_data)
            if success:
                return True, [f"Successfully exported {len(spaces)} spaces to {filename}"]
            else:
                return False, ["Failed to write JSON file"]
                
        except Exception as e:
            return False, [f"Export failed: {str(e)}"]