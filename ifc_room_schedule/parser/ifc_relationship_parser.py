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
                        if any(keyword in property_set_name.lower() for keyword in ['thermal', 'heat', 'insulation', 'conductivity', 'transmittance', 'resistance']):
                            thermal_props = self._extract_properties_from_set(property_definition)
                            thermal_properties.update(thermal_props)
                        
                        # Check if this is a material property set
                        elif any(keyword in property_set_name.lower() for keyword in ['material', 'surface', 'finish', 'common']):
                            material_props = self._extract_properties_from_set(property_definition)
                            material_properties.update(material_props)

            # Extract material information from material associations
            for rel in getattr(element, 'HasAssociations', []):
                if rel.is_a('IfcRelAssociatesMaterial'):
                    material = rel.RelatingMaterial
                    if material:
                        material_info = self._extract_material_info(material)
                        material_properties.update(material_info)

            # Extract thermal properties from material constituents
            thermal_from_materials = self._extract_thermal_properties_from_materials(element)
            thermal_properties.update(thermal_from_materials)

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

    def _extract_thermal_properties_from_materials(self, building_element) -> Dict[str, Any]:
        """Extract thermal properties from material constituents."""
        thermal_properties = {}
        
        try:
            # Look for material layer sets which often contain thermal properties
            for rel in getattr(building_element, 'HasAssociations', []):
                if rel.is_a('IfcRelAssociatesMaterial'):
                    material = rel.RelatingMaterial
                    
                    if material and material.is_a('IfcMaterialLayerSet'):
                        # Extract thermal properties from each layer
                        total_thermal_resistance = 0.0
                        layer_count = 0
                        
                        for layer in getattr(material, 'MaterialLayers', []):
                            layer_material = getattr(layer, 'Material', None)
                            if layer_material:
                                # Look for thermal properties in the layer material
                                for prop_rel in getattr(layer_material, 'HasProperties', []):
                                    if prop_rel.is_a('IfcMaterialProperties'):
                                        for prop in getattr(prop_rel, 'Properties', []):
                                            prop_name = getattr(prop, 'Name', '').lower()
                                            if 'thermal' in prop_name or 'conductivity' in prop_name:
                                                if prop.is_a('IfcPropertySingleValue'):
                                                    value = getattr(prop, 'NominalValue', None)
                                                    if value:
                                                        thermal_properties[f"layer_{layer_count}_{prop.Name}"] = value.wrappedValue
                                
                                # Calculate thermal resistance if thickness and conductivity are available
                                thickness = getattr(layer, 'LayerThickness', 0)
                                if thickness > 0:
                                    # This is a simplified calculation - in reality would need conductivity
                                    layer_count += 1
                        
                        if layer_count > 0:
                            thermal_properties['layer_count'] = layer_count
                            thermal_properties['total_thickness'] = sum(
                                getattr(layer, 'LayerThickness', 0) 
                                for layer in getattr(material, 'MaterialLayers', [])
                            )

        except Exception as e:
            self.logger.debug(f"Error extracting thermal properties from materials: {e}")

        return thermal_properties

    def classify_boundary_level_relationships(self, space_guid: str) -> Dict[str, Any]:
        """
        Classify boundary relationships by level with detailed analysis.
        
        Args:
            space_guid: The GlobalId of the space
            
        Returns:
            Dictionary containing detailed boundary level classification
        """
        if not self.ifc_file:
            raise ValueError("No IFC file loaded. Use set_ifc_file() first.")

        try:
            boundary_relationships = self.get_boundary_level_relationships(space_guid)
            
            classification = {
                'first_level': {
                    'relationships': boundary_relationships['first_level'],
                    'count': len(boundary_relationships['first_level']),
                    'building_elements': {},
                    'thermal_properties': {},
                    'material_properties': {}
                },
                'second_level': {
                    'relationships': boundary_relationships['second_level'],
                    'count': len(boundary_relationships['second_level']),
                    'adjacent_spaces': {},
                    'connection_types': {}
                },
                'hierarchy_analysis': {
                    'max_depth': 2 if boundary_relationships['second_level'] else 1,
                    'has_space_to_space_connections': len(boundary_relationships['second_level']) > 0,
                    'total_boundary_count': len(boundary_relationships['first_level']) + len(boundary_relationships['second_level'])
                }
            }

            # Analyze 1st level boundaries in detail
            for rel in boundary_relationships['first_level']:
                element_guid = rel.related_entity_guid
                element_name = rel.related_entity_name
                
                # Extract thermal and material properties for this element
                properties = self.extract_thermal_and_material_properties(element_guid)
                
                classification['first_level']['building_elements'][element_guid] = {
                    'name': element_name,
                    'description': rel.related_entity_description,
                    'thermal_properties': properties['thermal_properties'],
                    'material_properties': properties['material_properties']
                }
                
                # Aggregate thermal properties
                for prop_name, prop_value in properties['thermal_properties'].items():
                    if prop_name not in classification['first_level']['thermal_properties']:
                        classification['first_level']['thermal_properties'][prop_name] = []
                    classification['first_level']['thermal_properties'][prop_name].append(prop_value)

            # Analyze 2nd level boundaries
            for rel in boundary_relationships['second_level']:
                space_guid = rel.related_entity_guid
                space_name = rel.related_entity_name
                
                classification['second_level']['adjacent_spaces'][space_guid] = {
                    'name': space_name,
                    'description': rel.related_entity_description,
                    'connection_type': 'space_to_space'
                }

            return classification

        except Exception as e:
            error_msg = f"Failed to classify boundary level relationships for space {space_guid}: {e}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)

    def get_boundary_hierarchy_tree(self, space_guid: str) -> Dict[str, Any]:
        """
        Get a hierarchical tree representation of boundary relationships.
        
        Args:
            space_guid: The GlobalId of the space
            
        Returns:
            Dictionary representing the boundary hierarchy tree
        """
        if not self.ifc_file:
            raise ValueError("No IFC file loaded. Use set_ifc_file() first.")

        try:
            classification = self.classify_boundary_level_relationships(space_guid)
            
            # Build hierarchy tree
            hierarchy_tree = {
                'space_guid': space_guid,
                'space_name': self._get_space_name(space_guid),
                'boundary_levels': {
                    'level_1': {
                        'description': 'Space to Building Element Boundaries',
                        'count': classification['first_level']['count'],
                        'elements': []
                    },
                    'level_2': {
                        'description': 'Space to Space Boundaries',
                        'count': classification['second_level']['count'],
                        'spaces': []
                    }
                },
                'summary': {
                    'total_boundaries': classification['hierarchy_analysis']['total_boundary_count'],
                    'max_hierarchy_depth': classification['hierarchy_analysis']['max_depth'],
                    'has_thermal_properties': len(classification['first_level']['thermal_properties']) > 0
                }
            }

            # Populate level 1 elements
            for element_guid, element_data in classification['first_level']['building_elements'].items():
                hierarchy_tree['boundary_levels']['level_1']['elements'].append({
                    'guid': element_guid,
                    'name': element_data['name'],
                    'description': element_data['description'],
                    'has_thermal_properties': len(element_data['thermal_properties']) > 0,
                    'has_material_properties': len(element_data['material_properties']) > 0
                })

            # Populate level 2 spaces
            for space_guid, space_data in classification['second_level']['adjacent_spaces'].items():
                hierarchy_tree['boundary_levels']['level_2']['spaces'].append({
                    'guid': space_guid,
                    'name': space_data['name'],
                    'description': space_data['description'],
                    'connection_type': space_data['connection_type']
                })

            return hierarchy_tree

        except Exception as e:
            error_msg = f"Failed to get boundary hierarchy tree for space {space_guid}: {e}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)

    def _get_space_name(self, space_guid: str) -> str:
        """Get the name of a space by its GUID."""
        try:
            space_entity = self._find_entity_by_guid(space_guid)
            if space_entity:
                return getattr(space_entity, 'Name', '') or getattr(space_entity, 'LongName', '') or space_guid
            return space_guid
        except Exception:
            return space_guid

    def validate_boundary_hierarchy(self, space_guid: str) -> Dict[str, Any]:
        """
        Validate the boundary hierarchy for a space.
        
        Args:
            space_guid: The GlobalId of the space
            
        Returns:
            Dictionary containing validation results
        """
        if not self.ifc_file:
            raise ValueError("No IFC file loaded. Use set_ifc_file() first.")

        validation_result = {
            'is_valid': True,
            'warnings': [],
            'errors': [],
            'statistics': {
                'first_level_boundaries': 0,
                'second_level_boundaries': 0,
                'elements_with_thermal_properties': 0,
                'elements_with_material_properties': 0
            }
        }

        try:
            classification = self.classify_boundary_level_relationships(space_guid)
            
            # Update statistics
            validation_result['statistics']['first_level_boundaries'] = classification['first_level']['count']
            validation_result['statistics']['second_level_boundaries'] = classification['second_level']['count']
            
            # Count elements with properties
            for element_data in classification['first_level']['building_elements'].values():
                if element_data['thermal_properties']:
                    validation_result['statistics']['elements_with_thermal_properties'] += 1
                if element_data['material_properties']:
                    validation_result['statistics']['elements_with_material_properties'] += 1

            # Validation checks
            if classification['first_level']['count'] == 0:
                validation_result['warnings'].append("No 1st level boundaries found - space may not be properly bounded")
            
            if classification['first_level']['count'] < 4:
                validation_result['warnings'].append(f"Only {classification['first_level']['count']} 1st level boundaries found - typical rooms have at least 4 (walls, floor, ceiling)")
            
            if validation_result['statistics']['elements_with_thermal_properties'] == 0:
                validation_result['warnings'].append("No thermal properties found for any building elements")
            
            if validation_result['statistics']['elements_with_material_properties'] == 0:
                validation_result['warnings'].append("No material properties found for any building elements")

            # Check for orphaned boundaries
            for rel in classification['first_level']['relationships']:
                if not rel.related_entity_guid:
                    validation_result['errors'].append(f"1st level boundary missing related building element GUID")
                    validation_result['is_valid'] = False

            for rel in classification['second_level']['relationships']:
                if not rel.related_entity_guid:
                    validation_result['errors'].append(f"2nd level boundary missing related space GUID")
                    validation_result['is_valid'] = False

        except Exception as e:
            validation_result['is_valid'] = False
            validation_result['errors'].append(f"Validation failed: {e}")

        return validation_result

    def clear_cache(self) -> None:
        """Clear the relationships cache."""
        self._relationships_cache = {}