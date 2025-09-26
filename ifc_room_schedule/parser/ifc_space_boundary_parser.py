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
            # Get all IfcSpaceBoundary entities
            ifc_boundaries = self.ifc_file.by_type("IfcSpaceBoundary")
            
            if not ifc_boundaries:
                self.logger.warning("No IfcSpaceBoundary entities found in the file")
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

            self.logger.info(f"Successfully extracted {len(boundaries)} space boundaries from {len(ifc_boundaries)} IfcSpaceBoundary entities")
            
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
        Extract properties from a single IfcSpaceBoundary entity.
        
        Args:
            ifc_boundary: IfcSpaceBoundary entity from IfcOpenShell
            
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
            # This is a simplified approach - in reality, this would require more complex logic
            pass
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
            connection_geometry = getattr(ifc_boundary, 'ConnectionGeometry', None)
            if not connection_geometry:
                return geometry_info

            # Get the surface geometry
            surface_geometry = getattr(connection_geometry, 'SurfaceOnRelatingElement', None)
            if not surface_geometry:
                return geometry_info

            # Calculate area using IfcOpenShell geometry processing
            area = self._calculate_boundary_area(surface_geometry)
            geometry_info['area'] = area

            # Extract geometric details for orientation calculation
            geometric_details = self._extract_geometric_details(surface_geometry)
            geometry_info.update(geometric_details)

        except Exception as e:
            self.logger.warning(f"Error extracting connection geometry: {e}")
            
        return geometry_info

    def _calculate_boundary_area(self, surface_geometry) -> float:
        """Calculate the area of a boundary surface."""
        try:
            if not self._geometry_settings:
                self._geometry_settings = ifcopenshell.geom.settings()
                
            # Try to create shape and calculate area
            shape = ifcopenshell.geom.create_shape(self._geometry_settings, surface_geometry)
            if shape and hasattr(shape, 'geometry'):
                # This is a simplified calculation - in practice, you'd need more sophisticated geometry processing
                return float(getattr(shape.geometry, 'area', 0.0))
                
        except Exception as e:
            self.logger.warning(f"Error calculating boundary area: {e}")
            
        return 0.0

    def _extract_geometric_details(self, surface_geometry) -> Dict[str, Any]:
        """Extract geometric details for orientation calculation."""
        details = {
            'vertices': [],
            'normal_vector': None,
            'center_point': None
        }
        
        try:
            # This would require more sophisticated geometry processing
            # For now, return empty details
            pass
        except Exception as e:
            self.logger.warning(f"Error extracting geometric details: {e}")
            
        return details

    def _determine_boundary_orientation(self, geometry_info: Dict[str, Any]) -> str:
        """Determine boundary orientation from geometry."""
        try:
            normal_vector = geometry_info.get('normal_vector')
            if not normal_vector:
                return "Unknown"

            # Simplified orientation detection based on normal vector
            # In practice, this would require more sophisticated analysis
            x, y, z = normal_vector
            
            # Determine primary direction
            abs_x, abs_y, abs_z = abs(x), abs(y), abs(z)
            
            if abs_z > max(abs_x, abs_y):
                return "Horizontal"
            elif abs_x > abs_y:
                return "East" if x > 0 else "West"
            else:
                return "North" if y > 0 else "South"
                
        except Exception as e:
            self.logger.warning(f"Error determining boundary orientation: {e}")
            
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
                return 2  # 2nd level: space-to-space
        except Exception:
            return 1  # Default to 1st level

    def _extract_material_properties(self, building_element) -> Dict[str, Any]:
        """Extract material properties from building element."""
        properties = {}
        
        try:
            if not building_element:
                return properties
                
            # Extract material information
            # This would require more sophisticated material property extraction
            pass
            
        except Exception as e:
            self.logger.warning(f"Error extracting material properties: {e}")
            
        return properties

    def _extract_thermal_properties(self, building_element) -> Dict[str, Any]:
        """Extract thermal properties from building element."""
        properties = {}
        
        try:
            if not building_element:
                return properties
                
            # Extract thermal information
            # This would require more sophisticated thermal property extraction
            pass
            
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
                errors.append(f"Boundary {i+1}: Missing GUID")
            if not boundary.related_space_guid:
                errors.append(f"Boundary {boundary.guid}: Missing related space GUID")
            if boundary.calculated_area < 0:
                errors.append(f"Boundary {boundary.guid}: Negative calculated area")

        return len(errors) == 0, errors