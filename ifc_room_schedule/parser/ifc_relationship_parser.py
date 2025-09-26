"""
IFC Relationship Parser

Parses relationships between IFC entities using IfcOpenShell.
"""

import logging
from typing import List, Dict, Optional, Any
import ifcopenshell
from ..data.relationship_model import RelationshipData


class IfcRelationshipParser:
    """Extracts relationships between IFC spaces and other entities."""

    def __init__(self, ifc_file=None):
        """
        Initialize the relationship parser.
        
        Args:
            ifc_file: IfcOpenShell file object (optional)
        """
        self.ifc_file = ifc_file
        self.logger = logging.getLogger(__name__)
        self._relationships_cache = {}

    def set_ifc_file(self, ifc_file) -> None:
        """
        Set the IFC file to extract relationships from.
        
        Args:
            ifc_file: IfcOpenShell file object
        """
        self.ifc_file = ifc_file
        self._relationships_cache = {}  # Clear cache when file changes

    def get_space_relationships(self, space_guid: str) -> List[RelationshipData]:
        """
        Get all relationships for a specific space.
        
        Args:
            space_guid: The GlobalId of the space
            
        Returns:
            List of RelationshipData objects
            
        Raises:
            ValueError: If no IFC file is loaded
            RuntimeError: If extraction fails
        """
        if not self.ifc_file:
            raise ValueError("No IFC file loaded. Use set_ifc_file() first.")

        # Check cache first
        if space_guid in self._relationships_cache:
            return self._relationships_cache[space_guid]

        try:
            # Find the space entity
            space_entity = self._find_entity_by_guid(space_guid)
            if not space_entity:
                self.logger.warning(f"Space with GUID {space_guid} not found")
                return []

            relationships = []
            
            # Extract different types of relationships
            relationships.extend(self._extract_containment_relationships(space_entity))
            relationships.extend(self._extract_adjacency_relationships(space_entity))
            relationships.extend(self._extract_service_relationships(space_entity))
            relationships.extend(self._extract_assignment_relationships(space_entity))
            relationships.extend(self._extract_definition_relationships(space_entity))

            # Remove duplicates while preserving order
            unique_relationships = []
            seen = set()
            for rel in relationships:
                rel_key = (rel.related_entity_guid, rel.relationship_type)
                if rel_key not in seen:
                    seen.add(rel_key)
                    unique_relationships.append(rel)

            self.logger.info(f"Found {len(unique_relationships)} relationships for space {space_guid}")
            
            # Cache the results
            self._relationships_cache[space_guid] = unique_relationships
            return unique_relationships

        except Exception as e:
            error_msg = f"Failed to extract relationships for space {space_guid}: {e}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)

    def get_all_relationships(self) -> Dict[str, List[RelationshipData]]:
        """
        Get relationships for all spaces in the IFC file.
        
        Returns:
            Dictionary mapping space GUIDs to their relationships
        """
        if not self.ifc_file:
            raise ValueError("No IFC file loaded. Use set_ifc_file() first.")

        try:
            # Get all spaces
            ifc_spaces = self.ifc_file.by_type("IfcSpace")
            all_relationships = {}

            for space in ifc_spaces:
                space_guid = getattr(space, 'GlobalId', '')
                if space_guid:
                    relationships = self.get_space_relationships(space_guid)
                    all_relationships[space_guid] = relationships

            return all_relationships

        except Exception as e:
            error_msg = f"Failed to extract all relationships: {e}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)

    def _find_entity_by_guid(self, guid: str):
        """Find an IFC entity by its GlobalId."""
        try:
            return self.ifc_file.by_guid(guid)
        except Exception:
            return None

    def _extract_containment_relationships(self, space_entity) -> List[RelationshipData]:
        """Extract containment relationships (IfcRelContainedInSpatialStructure)."""
        relationships = []
        
        try:
            # Check what contains this space
            for rel in getattr(space_entity, 'ContainedInStructure', []):
                if rel.is_a('IfcRelContainedInSpatialStructure'):
                    relating_structure = rel.RelatingStructure
                    if relating_structure:
                        rel_data = self._create_relationship_data(
                            relating_structure,
                            "Contains",
                            "IfcRelContainedInSpatialStructure"
                        )
                        if rel_data:
                            relationships.append(rel_data)

            # Check what this space contains
            for rel in getattr(space_entity, 'ContainsElements', []):
                if rel.is_a('IfcRelContainedInSpatialStructure'):
                    for related_element in rel.RelatedElements:
                        rel_data = self._create_relationship_data(
                            related_element,
                            "Contains",
                            "IfcRelContainedInSpatialStructure"
                        )
                        if rel_data:
                            relationships.append(rel_data)

        except Exception as e:
            self.logger.warning(f"Error extracting containment relationships: {e}")

        return relationships

    def _extract_adjacency_relationships(self, space_entity) -> List[RelationshipData]:
        """Extract adjacency relationships through space boundaries."""
        relationships = []
        
        try:
            # Get space boundaries to find adjacent spaces
            for rel in getattr(space_entity, 'BoundedBy', []):
                if rel.is_a('IfcRelSpaceBoundary'):
                    # Check for 2nd level boundaries (space-to-space)
                    if hasattr(rel, 'CorrespondingBoundary') and rel.CorrespondingBoundary:
                        corresponding_boundary = rel.CorrespondingBoundary
                        if hasattr(corresponding_boundary, 'RelatingSpace'):
                            adjacent_space = corresponding_boundary.RelatingSpace
                            if adjacent_space and adjacent_space != space_entity:
                                rel_data = self._create_relationship_data(
                                    adjacent_space,
                                    "Adjacent",
                                    "IfcRelSpaceBoundary"
                                )
                                if rel_data:
                                    relationships.append(rel_data)

        except Exception as e:
            self.logger.warning(f"Error extracting adjacency relationships: {e}")

        return relationships

    def _extract_service_relationships(self, space_entity) -> List[RelationshipData]:
        """Extract service relationships (IfcRelServicesBuildings)."""
        relationships = []
        
        try:
            # Check what services this space
            for rel in getattr(space_entity, 'ServicedBySystems', []):
                if rel.is_a('IfcRelServicesBuildings'):
                    relating_system = rel.RelatingSystem
                    if relating_system:
                        rel_data = self._create_relationship_data(
                            relating_system,
                            "Serves",
                            "IfcRelServicesBuildings"
                        )
                        if rel_data:
                            relationships.append(rel_data)

        except Exception as e:
            self.logger.warning(f"Error extracting service relationships: {e}")

        return relationships

    def _extract_assignment_relationships(self, space_entity) -> List[RelationshipData]:
        """Extract assignment relationships (IfcRelAssigns)."""
        relationships = []
        
        try:
            # Check assignments to this space
            for rel in getattr(space_entity, 'HasAssignments', []):
                if rel.is_a('IfcRelAssigns'):
                    relating_object = rel.RelatingObject
                    if relating_object:
                        rel_data = self._create_relationship_data(
                            relating_object,
                            "AssignedTo",
                            rel.is_a()
                        )
                        if rel_data:
                            relationships.append(rel_data)

            # Check what this space is assigned to
            for rel in getattr(space_entity, 'IsAssignedTo', []):
                if rel.is_a('IfcRelAssigns'):
                    relating_object = rel.RelatingObject
                    if relating_object:
                        rel_data = self._create_relationship_data(
                            relating_object,
                            "AssignedTo",
                            rel.is_a()
                        )
                        if rel_data:
                            relationships.append(rel_data)

        except Exception as e:
            self.logger.warning(f"Error extracting assignment relationships: {e}")

        return relationships

    def _extract_definition_relationships(self, space_entity) -> List[RelationshipData]:
        """Extract definition relationships (IfcRelDefines)."""
        relationships = []
        
        try:
            # Check what defines this space (property sets, type definitions)
            for rel in getattr(space_entity, 'IsDefinedBy', []):
                if rel.is_a('IfcRelDefinesByProperties'):
                    property_definition = rel.RelatingPropertyDefinition
                    if property_definition:
                        rel_data = self._create_relationship_data(
                            property_definition,
                            "DefinedBy",
                            "IfcRelDefinesByProperties"
                        )
                        if rel_data:
                            relationships.append(rel_data)
                elif rel.is_a('IfcRelDefinesByType'):
                    relating_type = rel.RelatingType
                    if relating_type:
                        rel_data = self._create_relationship_data(
                            relating_type,
                            "DefinedBy",
                            "IfcRelDefinesByType"
                        )
                        if rel_data:
                            relationships.append(rel_data)

        except Exception as e:
            self.logger.warning(f"Error extracting definition relationships: {e}")

        return relationships

    def _create_relationship_data(self, related_entity, relationship_type: str, ifc_relationship_type: str) -> Optional[RelationshipData]:
        """
        Create a RelationshipData object from an IFC entity.
        
        Args:
            related_entity: The related IFC entity
            relationship_type: The categorized relationship type
            ifc_relationship_type: The IFC relationship class name
            
        Returns:
            RelationshipData object or None if creation fails
        """
        try:
            guid = getattr(related_entity, 'GlobalId', '')
            name = getattr(related_entity, 'Name', '') or ''
            description = getattr(related_entity, 'Description', '') or ''
            
            # Skip if no GUID (required field)
            if not guid:
                return None

            # Use entity type as name if no name is provided
            if not name:
                name = related_entity.is_a()

            return RelationshipData(
                related_entity_guid=guid,
                related_entity_name=name,
                related_entity_description=description,
                relationship_type=relationship_type,
                ifc_relationship_type=ifc_relationship_type
            )

        except Exception as e:
            self.logger.warning(f"Error creating relationship data: {e}")
            return None

    def categorize_relationships(self, relationships: List[RelationshipData]) -> Dict[str, List[RelationshipData]]:
        """
        Categorize relationships by type.
        
        Args:
            relationships: List of RelationshipData objects
            
        Returns:
            Dictionary mapping relationship types to lists of relationships
        """
        categorized = {}
        
        for relationship in relationships:
            rel_type = relationship.relationship_type
            if rel_type not in categorized:
                categorized[rel_type] = []
            categorized[rel_type].append(relationship)

        return categorized

    def get_relationship_summary(self, space_guid: str) -> Dict[str, int]:
        """
        Get a summary of relationship counts for a space.
        
        Args:
            space_guid: The GlobalId of the space
            
        Returns:
            Dictionary mapping relationship types to counts
        """
        try:
            relationships = self.get_space_relationships(space_guid)
            categorized = self.categorize_relationships(relationships)
            
            summary = {}
            for rel_type, rel_list in categorized.items():
                summary[rel_type] = len(rel_list)
                
            return summary

        except Exception as e:
            self.logger.error(f"Error getting relationship summary for {space_guid}: {e}")
            return {}

    def get_boundary_level_relationships(self, space_guid: str) -> Dict[str, List[RelationshipData]]:
        """
        Get relationships categorized by boundary level.
        
        Args:
            space_guid: The GlobalId of the space
            
        Returns:
            Dictionary with 'first_level' and 'second_level' keys containing relationship lists
        """
        if not self.ifc_file:
            raise ValueError("No IFC file loaded. Use set_ifc_file() first.")

        try:
            # Find the space entity
            space_entity = self._find_entity_by_guid(space_guid)
            if not space_entity:
                self.logger.warning(f"Space with GUID {space_guid} not found")
                return {'first_level': [], 'second_level': []}

            first_level_relationships = []
            second_level_relationships = []

            # Extract boundary relationships with level differentiation
            for rel in getattr(space_entity, 'BoundedBy', []):
                if rel.is_a('IfcRelSpaceBoundary'):
                    # 1st level: space-to-building-element relationships
                    building_element = rel.RelatedBuildingElement
                    if building_element:
                        rel_data = self._create_relationship_data(
                            building_element,
                            "BoundedBy",
                            "IfcRelSpaceBoundary"
                        )
                        if rel_data:
                            first_level_relationships.append(rel_data)

                    # 2nd level: space-to-space relationships through corresponding boundaries
                    if hasattr(rel, 'CorrespondingBoundary') and rel.CorrespondingBoundary:
                        corresponding_boundary = rel.CorrespondingBoundary
                        if hasattr(corresponding_boundary, 'RelatingSpace'):
                            adjacent_space = corresponding_boundary.RelatingSpace
                            if adjacent_space and adjacent_space != space_entity:
                                rel_data = self._create_relationship_data(
                                    adjacent_space,
                                    "AdjacentSpace",
                                    "IfcRelSpaceBoundary"
                                )
                                if rel_data:
                                    second_level_relationships.append(rel_data)

            return {
                'first_level': first_level_relationships,
                'second_level': second_level_relationships
            }

        except Exception as e:
            error_msg = f"Failed to extract boundary level relationships for space {space_guid}: {e}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)

    def extract_thermal_and_material_properties(self, building_element_guid: str) -> Dict[str, Dict[str, Any]]:
        """
        Extract thermal and material properties from a building element.
        
        Args:
            building_element_guid: The GlobalId of the building element
            
        Returns:
            Dictionary with 'thermal_properties' and 'material_properties' keys
        """
        if not self.ifc_file:
            raise ValueError("No IFC file loaded. Use set_ifc_file() first.")

        thermal_properties = {}
        material_properties = {}

        try:
            # Find the building element
            element = self._find_entity_by_guid(building_element_guid)
            if not element:
                return {'thermal_properties': thermal_properties, 'material_properties': material_properties}

            # Extract properties from property sets
            for rel in getattr(element, 'IsDefinedBy', []):
                if rel.is_a('IfcRelDefinesByProperties'):
                    property_definition = rel.RelatingPropertyDefinition
                    
                    if property_definition.is_a('IfcPropertySet'):
                        property_set_name = getattr(property_definition, 'Name', '')
                        
                        # Check if this is a thermal property set
                        if any(keyword in property_set_name.lower() for keyword in ['thermal', 'heat', 'insulation', 'conductivity']):
                            thermal_props = self._extract_properties_from_set(property_definition)
                            thermal_properties.update(thermal_props)
                        
                        # Check if this is a material property set
                        elif any(keyword in property_set_name.lower() for keyword in ['material', 'surface', 'finish']):
                            material_props = self._extract_properties_from_set(property_definition)
                            material_properties.update(material_props)

            # Extract material information from material associations
            for rel in getattr(element, 'HasAssociations', []):
                if rel.is_a('IfcRelAssociatesMaterial'):
                    material = rel.RelatingMaterial
                    if material:
                        material_info = self._extract_material_info(material)
                        material_properties.update(material_info)

        except Exception as e:
            self.logger.warning(f"Error extracting properties from building element {building_element_guid}: {e}")

        return {
            'thermal_properties': thermal_properties,
            'material_properties': material_properties
        }

    def _extract_properties_from_set(self, property_set) -> Dict[str, Any]:
        """Extract properties from an IfcPropertySet."""
        properties = {}
        
        try:
            for prop in getattr(property_set, 'HasProperties', []):
                prop_name = getattr(prop, 'Name', '')
                
                if prop.is_a('IfcPropertySingleValue'):
                    nominal_value = getattr(prop, 'NominalValue', None)
                    if nominal_value:
                        properties[prop_name] = nominal_value.wrappedValue
                elif prop.is_a('IfcPropertyEnumeratedValue'):
                    enumeration_values = getattr(prop, 'EnumerationValues', [])
                    if enumeration_values:
                        properties[prop_name] = [val.wrappedValue for val in enumeration_values]
                elif prop.is_a('IfcPropertyBoundedValue'):
                    upper_bound = getattr(prop, 'UpperBoundValue', None)
                    lower_bound = getattr(prop, 'LowerBoundValue', None)
                    if upper_bound or lower_bound:
                        properties[prop_name] = {
                            'upper_bound': upper_bound.wrappedValue if upper_bound else None,
                            'lower_bound': lower_bound.wrappedValue if lower_bound else None
                        }

        except Exception as e:
            self.logger.warning(f"Error extracting properties from property set: {e}")

        return properties

    def _extract_material_info(self, material) -> Dict[str, Any]:
        """Extract information from an IFC material."""
        material_info = {}
        
        try:
            # Basic material information
            material_info['name'] = getattr(material, 'Name', '')
            material_info['description'] = getattr(material, 'Description', '')
            material_info['category'] = getattr(material, 'Category', '')

            # Handle different material types
            if material.is_a('IfcMaterial'):
                # Single material
                pass
            elif material.is_a('IfcMaterialLayerSet'):
                # Layered material
                layers = []
                for layer in getattr(material, 'MaterialLayers', []):
                    layer_info = {
                        'thickness': getattr(layer, 'LayerThickness', 0),
                        'material_name': getattr(layer.Material, 'Name', '') if layer.Material else ''
                    }
                    layers.append(layer_info)
                material_info['layers'] = layers
            elif material.is_a('IfcMaterialList'):
                # List of materials
                materials = []
                for mat in getattr(material, 'Materials', []):
                    materials.append(getattr(mat, 'Name', ''))
                material_info['materials'] = materials

        except Exception as e:
            self.logger.warning(f"Error extracting material information: {e}")

        return material_info

    def analyze_boundary_hierarchies(self, space_guid: str) -> Dict[str, Any]:
        """
        Analyze boundary hierarchies and parent-child relationships for a space.
        
        Args:
            space_guid: The GlobalId of the space
            
        Returns:
            Dictionary containing hierarchy analysis
        """
        if not self.ifc_file:
            raise ValueError("No IFC file loaded. Use set_ifc_file() first.")

        try:
            boundary_relationships = self.get_boundary_level_relationships(space_guid)
            
            analysis = {
                'first_level_count': len(boundary_relationships['first_level']),
                'second_level_count': len(boundary_relationships['second_level']),
                'building_elements': {},
                'adjacent_spaces': {},
                'hierarchy_depth': 0
            }

            # Analyze 1st level boundaries (space-to-element)
            for rel in boundary_relationships['first_level']:
                element_type = rel.ifc_relationship_type
                if element_type not in analysis['building_elements']:
                    analysis['building_elements'][element_type] = []
                analysis['building_elements'][element_type].append({
                    'guid': rel.related_entity_guid,
                    'name': rel.related_entity_name,
                    'description': rel.related_entity_description
                })

            # Analyze 2nd level boundaries (space-to-space)
            for rel in boundary_relationships['second_level']:
                analysis['adjacent_spaces'][rel.related_entity_guid] = {
                    'name': rel.related_entity_name,
                    'description': rel.related_entity_description
                }

            # Determine hierarchy depth
            if analysis['second_level_count'] > 0:
                analysis['hierarchy_depth'] = 2
            elif analysis['first_level_count'] > 0:
                analysis['hierarchy_depth'] = 1

            return analysis

        except Exception as e:
            error_msg = f"Failed to analyze boundary hierarchies for space {space_guid}: {e}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)

    def clear_cache(self) -> None:
        """Clear the relationships cache."""
        self._relationships_cache = {}