"""
IFC Space Boundary Parser

Extracts and processes IfcSpaceBoundary entities from IFC files using IfcOpenShell.
"""

import logging
import math
from typing import List, Dict, Optional, Any, Tuple
import ifcopenshell
import ifcopenshell.util.element
import ifcopenshell.util.unit
import ifcopenshell.geom
from ..data.space_boundary_model import SpaceBoundaryData


class IfcSpaceBoundaryParser:
    """Extracts and processes IfcSpaceBoundary entities from IFC files."""

    def __init__(self, ifc_file=None):
        """
        Initialize the space boundary parser.

        Args:
            ifc_file: IfcOpenShell file object (optional)
        """
        self.ifc_file = ifc_file
        self.logger = logging.getLogger(__name__)
        self._boundaries_cache = None
        self._geometry_settings = None

    def set_ifc_file(self, ifc_file) -> None:
        """
        Set the IFC file to extract space boundaries from.

        Args:
            ifc_file: IfcOpenShell file object
        """
        self.ifc_file = ifc_file
        self._boundaries_cache = None  # Clear cache when file changes
        self._geometry_settings = None

    def extract_space_boundaries(self, space_guid: Optional[str] = None) -> List[SpaceBoundaryData]:
        """
        Extract IfcSpaceBoundary entities from the IFC file.

        Args:
            space_guid: Optional GUID to filter boundaries for a specific space

        Returns:
            List of SpaceBoundaryData objects

        Raises:
            ValueError: If no IFC file is loaded
            RuntimeError: If extraction fails
        """
        if not self.ifc_file:
            raise ValueError("No IFC file loaded. Use set_ifc_file() first.")

        try:
            # Get all IfcRelSpaceBoundary entities (IFC4 schema)
            ifc_boundaries = self.ifc_file.by_type("IfcRelSpaceBoundary")

            if not ifc_boundaries:
                self.logger.warning("No IfcRelSpaceBoundary entities found in the file")
                return []

            boundaries = []
            for ifc_boundary in ifc_boundaries:
                try:
                    # Filter by space GUID if specified
                    if space_guid:
                        related_space = getattr(ifc_boundary, 'RelatingSpace', None)
                        if not related_space or getattr(related_space, 'GlobalId', '') != space_guid:
                            continue

                    boundary_data = self._extract_boundary_properties(ifc_boundary)
                    if boundary_data:
                        boundaries.append(boundary_data)
                except Exception as e:
                    self.logger.error(
                        f"Error extracting boundary {getattr(ifc_boundary, 'GlobalId', 'Unknown')}: {e}"
                    )
                    # Continue processing other boundaries
                    continue

            self.logger.info(
                f"Successfully extracted {len(boundaries)} space boundaries "
                f"from {len(ifc_boundaries)} IfcRelSpaceBoundary entities"
            )

            if not space_guid:  # Only cache if extracting all boundaries
                self._boundaries_cache = boundaries

            return boundaries

        except Exception as e:
            error_msg = f"Failed to extract space boundaries from IFC file: {e}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)

    def get_boundaries_for_space(self, space_guid: str) -> List[SpaceBoundaryData]:
        """
        Get all boundaries for a specific space.

        Args:
            space_guid: The GlobalId of the space

        Returns:
            List of SpaceBoundaryData objects for the space
        """
        return self.extract_space_boundaries(space_guid)

    def _extract_boundary_properties(self, ifc_boundary) -> Optional[SpaceBoundaryData]:
        """
        Extract properties from a single IfcRelSpaceBoundary entity.

        Args:
            ifc_boundary: IfcRelSpaceBoundary entity from IfcOpenShell

        Returns:
            SpaceBoundaryData object or None if extraction fails
        """
        try:
            # Extract basic properties
            guid = getattr(ifc_boundary, 'GlobalId', '')
            name = getattr(ifc_boundary, 'Name', '') or ''
            description = getattr(ifc_boundary, 'Description', '') or ''

            # Validate required fields
            if not guid:
                self.logger.warning("Space boundary missing GlobalId, skipping")
                return None

            # Extract boundary type properties
            physical_or_virtual = self._extract_physical_or_virtual_boundary(ifc_boundary)
            internal_or_external = self._extract_internal_or_external_boundary(ifc_boundary)

            # Extract related building element information
            element_info = self._extract_related_building_element(ifc_boundary)

            # Extract related space information
            space_info = self._extract_related_space(ifc_boundary)

            # Extract connection geometry and calculate area
            geometry_info = self._extract_connection_geometry(ifc_boundary)
            calculated_area = geometry_info.get('area', 0.0)

            # Determine boundary orientation from geometry
            boundary_orientation = self._determine_boundary_orientation(geometry_info)

            # Classify boundary surface type
            boundary_surface_type = self._classify_boundary_surface_type(element_info.get('type', ''))

            # Determine boundary level (1st or 2nd level)
            boundary_level = self._determine_boundary_level(ifc_boundary)

            # Extract adjacent space for 2nd level boundaries
            adjacent_space_info = self._extract_adjacent_space(ifc_boundary) if boundary_level == 2 else {}

            # Extract material and thermal properties
            material_properties = self._extract_material_properties(element_info.get('element'))
            thermal_properties = self._extract_thermal_properties(element_info.get('element'))

            # Create SpaceBoundaryData object
            boundary_data = SpaceBoundaryData(
                id=f"boundary_{guid}",
                guid=guid,
                name=name,
                description=description,
                physical_or_virtual_boundary=physical_or_virtual,
                internal_or_external_boundary=internal_or_external,
                related_building_element_guid=element_info.get('guid', ''),
                related_building_element_name=element_info.get('name', ''),
                related_building_element_type=element_info.get('type', ''),
                related_space_guid=space_info.get('guid', ''),
                adjacent_space_guid=adjacent_space_info.get('guid', ''),
                adjacent_space_name=adjacent_space_info.get('name', ''),
                boundary_surface_type=boundary_surface_type,
                boundary_orientation=boundary_orientation,
                connection_geometry=geometry_info,
                calculated_area=calculated_area,
                thermal_properties=thermal_properties,
                material_properties=material_properties,
                boundary_level=boundary_level
            )

            # Generate display label
            boundary_data.update_display_label()

            self.logger.debug(f"Extracted space boundary: {guid} - {name}")
            return boundary_data

        except Exception as e:
            self.logger.error(f"Error extracting properties from space boundary: {e}")
            return None

    def _extract_physical_or_virtual_boundary(self, ifc_boundary) -> str:
        """Extract PhysicalOrVirtualBoundary property."""
        try:
            boundary_type = getattr(ifc_boundary, 'PhysicalOrVirtualBoundary', None)
            if boundary_type:
                return str(boundary_type)
            return "Undefined"
        except Exception:
            return "Undefined"

    def _extract_internal_or_external_boundary(self, ifc_boundary) -> str:
        """Extract InternalOrExternalBoundary property."""
        try:
            boundary_type = getattr(ifc_boundary, 'InternalOrExternalBoundary', None)
            if boundary_type:
                return str(boundary_type)
            return "Undefined"
        except Exception:
            return "Undefined"

    def _extract_related_building_element(self, ifc_boundary) -> Dict[str, str]:
        """Extract information about the related building element."""
        element_info = {'guid': '', 'name': '', 'type': '', 'element': None}

        try:
            related_element = getattr(ifc_boundary, 'RelatedBuildingElement', None)
            if related_element:
                element_info['guid'] = getattr(related_element, 'GlobalId', '')
                element_info['name'] = getattr(related_element, 'Name', '') or ''
                element_info['type'] = related_element.is_a() if hasattr(related_element, 'is_a') else ''
                element_info['element'] = related_element
        except Exception as e:
            self.logger.warning(f"Error extracting related building element: {e}")

        return element_info

    def _extract_related_space(self, ifc_boundary) -> Dict[str, str]:
        """Extract information about the related space."""
        space_info = {'guid': '', 'name': ''}

        try:
            related_space = getattr(ifc_boundary, 'RelatingSpace', None)
            if related_space:
                space_info['guid'] = getattr(related_space, 'GlobalId', '')
                space_info['name'] = getattr(related_space, 'Name', '') or ''
        except Exception as e:
            self.logger.warning(f"Error extracting related space: {e}")

        return space_info

    def _extract_adjacent_space(self, ifc_boundary) -> Dict[str, str]:
        """Extract information about adjacent space for 2nd level boundaries."""
        adjacent_info = {'guid': '', 'name': ''}

        try:
            # For 2nd level boundaries, check if there's a corresponding boundary
            corresponding_boundary = getattr(ifc_boundary, 'CorrespondingBoundary', None)
            if corresponding_boundary:
                # Get the space from the corresponding boundary
                adjacent_space = getattr(corresponding_boundary, 'RelatingSpace', None)
                if adjacent_space:
                    adjacent_info['guid'] = getattr(adjacent_space, 'GlobalId', '')
                    adjacent_info['name'] = getattr(adjacent_space, 'Name', '') or getattr(adjacent_space, 'LongName', '')
        except Exception as e:
            self.logger.warning(f"Error extracting adjacent space: {e}")

        return adjacent_info

    def _extract_connection_geometry(self, ifc_boundary) -> Dict[str, Any]:
        """Extract and process connection geometry."""
        geometry_info = {
            'area': 0.0,
            'vertices': [],
            'normal_vector': None,
            'center_point': None
        }

        try:
            # First try to get area from related building element quantities
            area = self._get_area_from_related_element(ifc_boundary)
            if area > 0:
                geometry_info['area'] = area

            # Then try connection geometry for orientation
            connection_geometry = getattr(ifc_boundary, 'ConnectionGeometry', None)
            if connection_geometry:
                surface_geometry = getattr(connection_geometry, 'SurfaceOnRelatingElement', None)
                if surface_geometry:
                    # If we didn't get area from element, try from geometry
                    if geometry_info['area'] == 0:
                        geom_area = self._calculate_boundary_area(surface_geometry)
                        geometry_info['area'] = geom_area

                    # Extract geometric details for orientation calculation
                    geometric_details = self._extract_geometric_details(surface_geometry)
                    geometry_info.update(geometric_details)

        except Exception as e:
            self.logger.warning(f"Error extracting connection geometry: {e}")

        return geometry_info

    def _get_area_from_related_element(self, ifc_boundary) -> float:
        """Get area from the related building element's quantities."""
        try:
            related_element = getattr(ifc_boundary, 'RelatedBuildingElement', None)
            if not related_element:
                return 0.0

            # Check element quantities
            for rel in getattr(related_element, 'IsDefinedBy', []):
                if rel.is_a('IfcRelDefinesByProperties'):
                    prop_def = rel.RelatingPropertyDefinition
                    if prop_def.is_a('IfcElementQuantity'):
                        for quantity in prop_def.Quantities:
                            if quantity.is_a('IfcQuantityArea'):
                                quantity_name = getattr(quantity, 'Name', '').lower()
                                # Look for area-related quantities
                                if any(keyword in quantity_name for keyword in ['area', 'areal', 'surface']):
                                    area_value = getattr(quantity, 'AreaValue', 0)
                                    if area_value and area_value > 0:
                                        return float(area_value)

            return 0.0

        except Exception as e:
            self.logger.debug(f"Error getting area from related element: {e}")
            return 0.0

    def _calculate_boundary_area(self, surface_geometry) -> float:
        """Calculate the area of a boundary surface."""
        try:
            if not self._geometry_settings:
                self._geometry_settings = ifcopenshell.geom.settings()
                self._geometry_settings.set(self._geometry_settings.USE_WORLD_COORDS, True)

            # Try to create shape and calculate area
            shape = ifcopenshell.geom.create_shape(self._geometry_settings, surface_geometry)
            if shape and hasattr(shape, 'geometry'):
                # Get the geometry and calculate area
                geometry = shape.geometry
                if hasattr(geometry, 'area'):
                    return float(geometry.area)

                # Alternative: calculate from vertices if area not available
                vertices = geometry.verts
                if len(vertices) >= 9:  # At least 3 vertices (3 coords each)
                    return self._calculate_area_from_vertices(vertices)

        except Exception as e:
            self.logger.debug(f"Error calculating boundary area from geometry: {e}")

        # Fallback: try to get area from quantity sets
        return self._get_area_from_boundary_quantities(surface_geometry)

    def _calculate_area_from_vertices(self, vertices) -> float:
        """Calculate area from vertex coordinates using triangulation."""
        try:
            # Convert flat vertex list to 3D points
            points = []
            for i in range(0, len(vertices), 3):
                if i + 2 < len(vertices):
                    points.append((vertices[i], vertices[i + 1], vertices[i + 2]))

            if len(points) < 3:
                return 0.0

            # Simple triangulation for planar surfaces
            total_area = 0.0
            for i in range(1, len(points) - 1):
                # Calculate area of triangle formed by points[0], points[i], points[i+1]
                v1 = (points[i][0] - points[0][0], points[i][1] - points[0][1], points[i][2] - points[0][2])
                v2 = (points[i + 1][0] - points[0][0], points[i + 1][1] - points[0][1], points[i + 1][2] - points[0][2])

                # Cross product
                cross = (
                    v1[1] * v2[2] - v1[2] * v2[1],
                    v1[2] * v2[0] - v1[0] * v2[2],
                    v1[0] * v2[1] - v1[1] * v2[0]
                )

                # Magnitude of cross product / 2 = triangle area
                magnitude = math.sqrt(cross[0] ** 2 + cross[1] ** 2 + cross[2] ** 2)
                total_area += magnitude / 2.0

            return total_area

        except Exception as e:
            self.logger.debug(f"Error calculating area from vertices: {e}")
            return 0.0

    def _get_area_from_boundary_quantities(self, surface_geometry) -> float:
        """Try to get area from IFC quantity sets."""
        try:
            # This would require traversing the IFC relationships to find quantity sets
            # For now, return 0 as fallback
            return 0.0
        except Exception:
            return 0.0

    def _extract_geometric_details(self, surface_geometry) -> Dict[str, Any]:
        """Extract geometric details for orientation calculation."""
        details = {
            'vertices': [],
            'normal_vector': None,
            'center_point': None
        }

        try:
            if not self._geometry_settings:
                self._geometry_settings = ifcopenshell.geom.settings()
                self._geometry_settings.set(self._geometry_settings.USE_WORLD_COORDS, True)

            # Create shape and extract geometry
            shape = ifcopenshell.geom.create_shape(self._geometry_settings, surface_geometry)
            if shape and hasattr(shape, 'geometry'):
                geometry = shape.geometry

                # Extract vertices
                vertices = geometry.verts
                if vertices:
                    # Convert to 3D points
                    points = []
                    for i in range(0, len(vertices), 3):
                        if i + 2 < len(vertices):
                            points.append((vertices[i], vertices[i + 1], vertices[i + 2]))
                    details['vertices'] = points

                    # Calculate normal vector from first three points
                    if len(points) >= 3:
                        normal = self._calculate_normal_vector(points[0], points[1], points[2])
                        details['normal_vector'] = normal

                    # Calculate center point
                    if points:
                        center_x = sum(p[0] for p in points) / len(points)
                        center_y = sum(p[1] for p in points) / len(points)
                        center_z = sum(p[2] for p in points) / len(points)
                        details['center_point'] = (center_x, center_y, center_z)

        except Exception as e:
            self.logger.debug(f"Error extracting geometric details: {e}")

        return details

    def _calculate_normal_vector(self, p1, p2, p3) -> tuple:
        """Calculate normal vector from three points."""
        try:
            # Vector from p1 to p2
            v1 = (p2[0] - p1[0], p2[1] - p1[1], p2[2] - p1[2])
            # Vector from p1 to p3
            v2 = (p3[0] - p1[0], p3[1] - p1[1], p3[2] - p1[2])

            # Cross product
            normal = (
                v1[1] * v2[2] - v1[2] * v2[1],
                v1[2] * v2[0] - v1[0] * v2[2],
                v1[0] * v2[1] - v1[1] * v2[0]
            )

            # Normalize
            magnitude = math.sqrt(normal[0]**2 + normal[1]**2 + normal[2]**2)
            if magnitude > 0:
                return (normal[0] / magnitude, normal[1] / magnitude, normal[2] / magnitude)
            else:
                return (0, 0, 1)  # Default to Z-up

        except Exception as e:
            self.logger.debug(f"Error calculating normal vector: {e}")
            return (0, 0, 1)

    def _determine_boundary_orientation(self, geometry_info: Dict[str, Any]) -> str:
        """Determine boundary orientation from geometry."""
        try:
            normal_vector = geometry_info.get('normal_vector')
            if not normal_vector:
                # Try to determine orientation from vertices if available
                vertices = geometry_info.get('vertices', [])
                if len(vertices) >= 3:
                    # Calculate normal from vertices
                    normal_vector = self._calculate_normal_vector(vertices[0], vertices[1], vertices[2])
                else:
                    return "Unknown"

            x, y, z = normal_vector

            # Determine primary direction based on normal vector
            abs_x, abs_y, abs_z = abs(x), abs(y), abs(z)

            # Threshold for considering a surface horizontal
            horizontal_threshold = 0.6  # Lowered threshold for better detection

            if abs_z > horizontal_threshold:
                # Surface is mostly horizontal
                if z > 0:
                    return "Horizontal Up"  # Floor viewed from above
                else:
                    return "Horizontal Down"  # Ceiling viewed from below
            else:
                # Surface is mostly vertical - determine cardinal direction
                # Use the dominant horizontal component
                
                if abs_x > abs_y:
                    # X component is dominant
                    if x > 0:
                        return "East"  # Normal points east
                    else:
                        return "West"  # Normal points west
                else:
                    # Y component is dominant
                    if y > 0:
                        return "North"  # Normal points north
                    else:
                        return "South"  # Normal points south

        except Exception as e:
            self.logger.debug(f"Error determining boundary orientation: {e}")

        return "Unknown"

    def _classify_boundary_surface_type(self, element_type: str) -> str:
        """Classify boundary surface type based on building element type."""
        if not element_type:
            return "Unknown"

        element_type_lower = element_type.lower()

        if 'wall' in element_type_lower:
            return "Wall"
        elif 'slab' in element_type_lower or 'floor' in element_type_lower:
            return "Floor"
        elif 'roof' in element_type_lower or 'ceiling' in element_type_lower:
            return "Ceiling"
        elif 'window' in element_type_lower:
            return "Window"
        elif 'door' in element_type_lower:
            return "Door"
        elif 'opening' in element_type_lower:
            return "Opening"
        else:
            return "Other"

    def _determine_boundary_level(self, ifc_boundary) -> int:
        """Determine if this is a 1st level (space-to-element) or 2nd level (space-to-space) boundary."""
        try:
            # Check if there's a related building element
            related_element = getattr(ifc_boundary, 'RelatedBuildingElement', None)
            if related_element:
                return 1  # 1st level: space-to-element
            else:
                # Check if this is a 2nd level boundary by looking for corresponding boundary
                corresponding_boundary = getattr(ifc_boundary, 'CorrespondingBoundary', None)
                if corresponding_boundary:
                    return 2  # 2nd level: space-to-space
                else:
                    return 1  # Default to 1st level if unclear
        except Exception:
            return 1  # Default to 1st level

    def _extract_material_properties(self, building_element) -> Dict[str, Any]:
        """Extract material properties from building element."""
        properties = {}

        try:
            if not building_element:
                return properties

            # Extract material information from associations
            for rel in getattr(building_element, 'HasAssociations', []):
                if rel.is_a('IfcRelAssociatesMaterial'):
                    material = rel.RelatingMaterial
                    if material:
                        # Basic material properties
                        properties['material_name'] = getattr(material, 'Name', '')
                        properties['material_description'] = getattr(material, 'Description', '')
                        properties['material_category'] = getattr(material, 'Category', '')
                        
                        # Handle different material types
                        if material.is_a('IfcMaterialLayerSet'):
                            layers = []
                            total_thickness = 0.0
                            for layer in getattr(material, 'MaterialLayers', []):
                                layer_thickness = getattr(layer, 'LayerThickness', 0)
                                layer_material = getattr(layer, 'Material', None)
                                layer_info = {
                                    'thickness': layer_thickness,
                                    'material_name': getattr(layer_material, 'Name', '') if layer_material else '',
                                    'priority': getattr(layer, 'Priority', 0)
                                }
                                layers.append(layer_info)
                                total_thickness += layer_thickness
                            
                            properties['layers'] = layers
                            properties['total_thickness'] = total_thickness
                            properties['layer_count'] = len(layers)

        except Exception as e:
            self.logger.warning(f"Error extracting material properties: {e}")

        return properties

    def _extract_thermal_properties(self, building_element) -> Dict[str, Any]:
        """Extract thermal properties from building element."""
        properties = {}

        try:
            if not building_element:
                return properties

            # Extract thermal properties from property sets
            for rel in getattr(building_element, 'IsDefinedBy', []):
                if rel.is_a('IfcRelDefinesByProperties'):
                    property_definition = rel.RelatingPropertyDefinition
                    
                    if property_definition.is_a('IfcPropertySet'):
                        property_set_name = getattr(property_definition, 'Name', '').lower()
                        
                        # Look for thermal-related property sets
                        if any(keyword in property_set_name for keyword in ['thermal', 'heat', 'insulation', 'conductivity', 'transmittance']):
                            for prop in getattr(property_definition, 'HasProperties', []):
                                prop_name = getattr(prop, 'Name', '')
                                
                                if prop.is_a('IfcPropertySingleValue'):
                                    nominal_value = getattr(prop, 'NominalValue', None)
                                    if nominal_value:
                                        properties[prop_name] = nominal_value.wrappedValue
                                        
                                        # Also store unit if available
                                        unit = getattr(prop, 'Unit', None)
                                        if unit:
                                            properties[f"{prop_name}_unit"] = str(unit)

            # Extract thermal properties from material constituents
            for rel in getattr(building_element, 'HasAssociations', []):
                if rel.is_a('IfcRelAssociatesMaterial'):
                    material = rel.RelatingMaterial
                    if material and material.is_a('IfcMaterialLayerSet'):
                        # Calculate overall thermal properties from layers
                        total_thermal_resistance = 0.0
                        total_thickness = 0.0
                        
                        for layer in getattr(material, 'MaterialLayers', []):
                            layer_thickness = getattr(layer, 'LayerThickness', 0)
                            total_thickness += layer_thickness
                            
                            # Look for thermal conductivity in layer material
                            layer_material = getattr(layer, 'Material', None)
                            if layer_material:
                                for prop_rel in getattr(layer_material, 'HasProperties', []):
                                    if prop_rel.is_a('IfcMaterialProperties'):
                                        for prop in getattr(prop_rel, 'Properties', []):
                                            prop_name = getattr(prop, 'Name', '').lower()
                                            if 'conductivity' in prop_name and prop.is_a('IfcPropertySingleValue'):
                                                conductivity_value = getattr(prop, 'NominalValue', None)
                                                if conductivity_value and layer_thickness > 0:
                                                    # R = thickness / conductivity
                                                    layer_resistance = layer_thickness / conductivity_value.wrappedValue
                                                    total_thermal_resistance += layer_resistance
                        
                        if total_thermal_resistance > 0:
                            properties['total_thermal_resistance'] = total_thermal_resistance
                            properties['overall_u_value'] = 1.0 / total_thermal_resistance  # U = 1/R
                        
                        if total_thickness > 0:
                            properties['total_thickness'] = total_thickness

        except Exception as e:
            self.logger.warning(f"Error extracting thermal properties: {e}")

        return properties

    def get_boundary_count(self) -> int:
        """
        Get the total number of space boundaries in the IFC file.

        Returns:
            Number of IfcSpaceBoundary entities
        """
        if not self.ifc_file:
            return 0

        try:
            return len(self.ifc_file.by_type("IfcSpaceBoundary"))
        except Exception:
            return 0

    def validate_boundaries(self, boundaries: List[SpaceBoundaryData]) -> Tuple[bool, List[str]]:
        """
        Validate extracted space boundary data.

        Args:
            boundaries: List of SpaceBoundaryData objects to validate

        Returns:
            Tuple of (is_valid: bool, error_messages: List[str])
        """
        errors = []

        if not boundaries:
            errors.append("No space boundaries found to validate")
            return False, errors

        # Check for duplicate GUIDs
        guids = [boundary.guid for boundary in boundaries]
        duplicate_guids = set([guid for guid in guids if guids.count(guid) > 1])
        if duplicate_guids:
            errors.append(f"Duplicate boundary GUIDs found: {', '.join(duplicate_guids)}")

        # Check for missing required properties
        for i, boundary in enumerate(boundaries):
            if not boundary.guid:
                errors.append(f"Boundary {i + 1}: Missing GUID")
            if not boundary.related_space_guid:
                errors.append(f"Boundary {boundary.guid}: Missing related space GUID")
            if boundary.calculated_area < 0:
                errors.append(f"Boundary {boundary.guid}: Negative calculated area")

        return len(errors) == 0, errors

    def classify_boundaries_by_level(self, boundaries: List[SpaceBoundaryData]) -> Dict[str, List[SpaceBoundaryData]]:
        """
        Classify boundaries by their level (1st or 2nd level).
        
        Args:
            boundaries: List of SpaceBoundaryData objects
            
        Returns:
            Dictionary with 'first_level' and 'second_level' keys containing boundary lists
        """
        classification = {
            'first_level': [],
            'second_level': []
        }
        
        for boundary in boundaries:
            if boundary.boundary_level == 1:
                classification['first_level'].append(boundary)
            elif boundary.boundary_level == 2:
                classification['second_level'].append(boundary)
        
        return classification

    def get_boundary_hierarchy_summary(self, space_guid: str) -> Dict[str, Any]:
        """
        Get a summary of boundary hierarchy for a specific space.
        
        Args:
            space_guid: The GlobalId of the space
            
        Returns:
            Dictionary containing hierarchy summary
        """
        try:
            boundaries = self.get_boundaries_for_space(space_guid)
            classification = self.classify_boundaries_by_level(boundaries)
            
            summary = {
                'space_guid': space_guid,
                'total_boundaries': len(boundaries),
                'first_level_count': len(classification['first_level']),
                'second_level_count': len(classification['second_level']),
                'building_elements': {},
                'adjacent_spaces': {},
                'thermal_data_available': False,
                'material_data_available': False
            }
            
            # Analyze 1st level boundaries
            for boundary in classification['first_level']:
                if boundary.related_building_element_guid:
                    element_guid = boundary.related_building_element_guid
                    summary['building_elements'][element_guid] = {
                        'name': boundary.related_building_element_name,
                        'type': boundary.related_building_element_type,
                        'surface_type': boundary.boundary_surface_type,
                        'orientation': boundary.boundary_orientation,
                        'area': boundary.calculated_area,
                        'has_thermal_properties': len(boundary.thermal_properties) > 0,
                        'has_material_properties': len(boundary.material_properties) > 0
                    }
                    
                    if boundary.thermal_properties:
                        summary['thermal_data_available'] = True
                    if boundary.material_properties:
                        summary['material_data_available'] = True
            
            # Analyze 2nd level boundaries
            for boundary in classification['second_level']:
                if boundary.adjacent_space_guid:
                    space_guid = boundary.adjacent_space_guid
                    summary['adjacent_spaces'][space_guid] = {
                        'name': boundary.adjacent_space_name,
                        'area': boundary.calculated_area,
                        'orientation': boundary.boundary_orientation
                    }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error getting boundary hierarchy summary for space {space_guid}: {e}")
            return {
                'space_guid': space_guid,
                'error': str(e),
                'total_boundaries': 0,
                'first_level_count': 0,
                'second_level_count': 0
            }

    def analyze_thermal_performance(self, boundaries: List[SpaceBoundaryData]) -> Dict[str, Any]:
        """
        Analyze thermal performance based on boundary data.
        
        Args:
            boundaries: List of SpaceBoundaryData objects
            
        Returns:
            Dictionary containing thermal performance analysis
        """
        analysis = {
            'total_boundary_area': 0.0,
            'thermal_boundaries_count': 0,
            'average_u_value': 0.0,
            'total_thermal_resistance': 0.0,
            'boundary_types': {},
            'orientations': {}
        }
        
        try:
            total_u_value_weighted = 0.0
            total_area_with_u_value = 0.0
            
            for boundary in boundaries:
                area = boundary.calculated_area
                analysis['total_boundary_area'] += area
                
                # Count by boundary type
                surface_type = boundary.boundary_surface_type
                if surface_type not in analysis['boundary_types']:
                    analysis['boundary_types'][surface_type] = {'count': 0, 'total_area': 0.0}
                analysis['boundary_types'][surface_type]['count'] += 1
                analysis['boundary_types'][surface_type]['total_area'] += area
                
                # Count by orientation
                orientation = boundary.boundary_orientation
                if orientation not in analysis['orientations']:
                    analysis['orientations'][orientation] = {'count': 0, 'total_area': 0.0}
                analysis['orientations'][orientation]['count'] += 1
                analysis['orientations'][orientation]['total_area'] += area
                
                # Analyze thermal properties
                if boundary.thermal_properties:
                    analysis['thermal_boundaries_count'] += 1
                    
                    # Look for U-value
                    u_value = boundary.thermal_properties.get('overall_u_value', 0)
                    if u_value > 0 and area > 0:
                        total_u_value_weighted += u_value * area
                        total_area_with_u_value += area
                    
                    # Sum thermal resistance
                    thermal_resistance = boundary.thermal_properties.get('total_thermal_resistance', 0)
                    if thermal_resistance > 0:
                        analysis['total_thermal_resistance'] += thermal_resistance
            
            # Calculate average U-value weighted by area
            if total_area_with_u_value > 0:
                analysis['average_u_value'] = total_u_value_weighted / total_area_with_u_value
            
        except Exception as e:
            self.logger.error(f"Error analyzing thermal performance: {e}")
            analysis['error'] = str(e)
        
        return analysis
