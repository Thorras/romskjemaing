"""
IFC Surface Extractor

Extracts surface information from IFC files using IfcOpenShell.
"""

from typing import List, Dict, Optional, Any, Tuple
import ifcopenshell
import ifcopenshell.util.element
import ifcopenshell.util.unit
from ..utils.enhanced_logging import enhanced_logger
from ..data.surface_model import SurfaceData


class IfcSurfaceExtractor:
    """Extracts surface data associated with IFC spaces."""

    def __init__(self, ifc_file=None):
        """
        Initialize the surface extractor.
        
        Args:
            ifc_file: IfcOpenShell file object (optional)
        """
        self.ifc_file = ifc_file
        self.logger = enhanced_logger.logger

    def set_ifc_file(self, ifc_file) -> None:
        """
        Set the IFC file to extract surfaces from.
        
        Args:
            ifc_file: IfcOpenShell file object
        """
        self.ifc_file = ifc_file

    def extract_surfaces_for_space(self, space_guid: str) -> List[SurfaceData]:
        """
        Extract all surfaces associated with a specific IFC space.
        
        Args:
            space_guid: The GlobalId of the space
            
        Returns:
            List of SurfaceData objects
            
        Raises:
            ValueError: If no IFC file is loaded or space not found
            RuntimeError: If extraction fails
        """
        if not self.ifc_file:
            raise ValueError("No IFC file loaded. Use set_ifc_file() first.")

        try:
            # Find the space by GUID
            ifc_space = self._find_space_by_guid(space_guid)
            if not ifc_space:
                self.logger.warning(f"Space with GUID {space_guid} not found")
                return []

            surfaces = []
            
            # Extract surfaces from space boundaries
            surfaces.extend(self._extract_surfaces_from_boundaries(ifc_space))
            
            # Extract surfaces from related building elements
            surfaces.extend(self._extract_surfaces_from_related_elements(ifc_space))
            
            # Extract surfaces from containment relationships
            surfaces.extend(self._extract_surfaces_from_containment(ifc_space))

            self.logger.info(f"Extracted {len(surfaces)} surfaces for space {space_guid}")
            return surfaces

        except Exception as e:
            error_msg = f"Failed to extract surfaces for space {space_guid}: {e}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)

    def _find_space_by_guid(self, space_guid: str):
        """Find an IFC space by its GUID."""
        try:
            return self.ifc_file.by_guid(space_guid)
        except:
            return None

    def _extract_surfaces_from_boundaries(self, ifc_space) -> List[SurfaceData]:
        """Extract surfaces from space boundaries."""
        surfaces = []
        
        try:
            # Get space boundaries
            for rel in getattr(ifc_space, 'BoundedBy', []):
                if rel.is_a('IfcRelSpaceBoundary'):
                    boundary = rel.RelatedBuildingElement
                    if boundary:
                        surface_data = self._create_surface_from_element(boundary, ifc_space.GlobalId)
                        if surface_data:
                            surfaces.append(surface_data)
                            
        except Exception as e:
            self.logger.warning(f"Error extracting surfaces from boundaries: {e}")
            
        return surfaces

    def _extract_surfaces_from_related_elements(self, ifc_space) -> List[SurfaceData]:
        """Extract surfaces from elements related to the space."""
        surfaces = []
        
        try:
            # Check for relationships where space is the relating object
            for rel in getattr(ifc_space, 'IsDecomposedBy', []):
                if rel.is_a('IfcRelAggregates'):
                    for element in rel.RelatedObjects:
                        if self._is_surface_element(element):
                            surface_data = self._create_surface_from_element(element, ifc_space.GlobalId)
                            if surface_data:
                                surfaces.append(surface_data)
                                
        except Exception as e:
            self.logger.warning(f"Error extracting surfaces from related elements: {e}")
            
        return surfaces

    def _extract_surfaces_from_containment(self, ifc_space) -> List[SurfaceData]:
        """Extract surfaces from containment relationships."""
        surfaces = []
        
        try:
            # Check containment relationships
            for rel in getattr(ifc_space, 'ContainsElements', []):
                if rel.is_a('IfcRelContainedInSpatialStructure'):
                    for element in rel.RelatedElements:
                        if self._is_surface_element(element):
                            surface_data = self._create_surface_from_element(element, ifc_space.GlobalId)
                            if surface_data:
                                surfaces.append(surface_data)
                                
        except Exception as e:
            self.logger.warning(f"Error extracting surfaces from containment: {e}")
            
        return surfaces

    def _is_surface_element(self, element) -> bool:
        """Check if an element represents a surface."""
        surface_types = [
            'IfcWall', 'IfcWallStandardCase',
            'IfcSlab', 'IfcRoof',
            'IfcCovering', 'IfcCurtainWall',
            'IfcWindow', 'IfcDoor',
            'IfcPlate', 'IfcMember'
        ]
        
        return any(element.is_a(surface_type) for surface_type in surface_types)

    def _create_surface_from_element(self, element, space_guid: str) -> Optional[SurfaceData]:
        """Create a SurfaceData object from an IFC element."""
        try:
            # Basic properties
            element_id = getattr(element, 'GlobalId', '')
            element_name = getattr(element, 'Name', '') or ''
            element_type = element.is_a()
            
            if not element_id:
                return None

            # Determine surface type
            surface_type = self._determine_surface_type(element)
            
            # Calculate area
            area = self._calculate_element_area(element)
            
            # Extract material
            material = self._extract_material(element)
            
            # Create surface data
            surface_data = SurfaceData(
                id=element_id,
                type=surface_type,
                area=area,
                material=material,
                ifc_type=element_type,
                related_space_guid=space_guid
            )
            
            # Add additional properties
            surface_data.add_property('name', element_name)
            surface_data.add_property('description', getattr(element, 'Description', '') or '')
            
            return surface_data
            
        except Exception as e:
            self.logger.warning(f"Error creating surface from element {getattr(element, 'GlobalId', 'Unknown')}: {e}")
            return None

    def _determine_surface_type(self, element) -> str:
        """Determine the surface type from IFC element type."""
        element_type = element.is_a()
        
        # Wall types
        if element_type in ['IfcWall', 'IfcWallStandardCase', 'IfcCurtainWall']:
            return 'Wall'
        
        # Floor types
        elif element_type == 'IfcSlab':
            # Check if it's a floor or ceiling based on predefined type
            predefined_type = getattr(element, 'PredefinedType', None)
            if predefined_type == 'FLOOR':
                return 'Floor'
            elif predefined_type == 'ROOF':
                return 'Ceiling'
            else:
                # Try to determine from position or name
                name = getattr(element, 'Name', '').lower()
                if 'floor' in name or 'gulv' in name:
                    return 'Floor'
                elif 'ceiling' in name or 'tak' in name:
                    return 'Ceiling'
                else:
                    return 'Floor'  # Default assumption
        
        # Roof types
        elif element_type == 'IfcRoof':
            return 'Ceiling'
        
        # Covering types
        elif element_type == 'IfcCovering':
            predefined_type = getattr(element, 'PredefinedType', None)
            if predefined_type == 'FLOORING':
                return 'Floor'
            elif predefined_type == 'CEILING':
                return 'Ceiling'
            else:
                return 'Covering'
        
        # Opening types
        elif element_type in ['IfcWindow', 'IfcDoor']:
            return 'Opening'
        
        # Other types
        elif element_type in ['IfcPlate', 'IfcMember']:
            return 'Other'
        
        else:
            return 'Unknown'

    def _calculate_element_area(self, element) -> float:
        """Calculate the area of an IFC element."""
        try:
            # Try to get area from quantities first
            area = self._get_area_from_quantities(element)
            if area > 0:
                return area
            
            # Try to calculate from geometry
            area = self._calculate_area_from_geometry(element)
            if area > 0:
                return area
            
            # Fallback to estimated area
            return self._estimate_area_from_properties(element)
            
        except Exception as e:
            self.logger.warning(f"Error calculating area for element {getattr(element, 'GlobalId', 'Unknown')}: {e}")
            return 0.0

    def _get_area_from_quantities(self, element) -> float:
        """Get area from IFC quantity sets."""
        try:
            for rel in getattr(element, 'IsDefinedBy', []):
                if rel.is_a('IfcRelDefinesByProperties'):
                    prop_def = rel.RelatingPropertyDefinition
                    
                    if prop_def.is_a('IfcElementQuantity'):
                        for quantity in prop_def.Quantities:
                            if quantity.is_a('IfcQuantityArea'):
                                quantity_name = getattr(quantity, 'Name', '').lower()
                                # Look for area-related quantities
                                if any(keyword in quantity_name for keyword in ['area', 'areal', 'surface']):
                                    return float(quantity.AreaValue or 0)
                                    
        except Exception as e:
            self.logger.debug(f"Error getting area from quantities: {e}")
            
        return 0.0

    def _calculate_area_from_geometry(self, element) -> float:
        """Calculate area from IFC geometric representation."""
        try:
            # This is a simplified approach - in practice, you might need
            # more sophisticated geometry processing
            representation = getattr(element, 'Representation', None)
            if not representation:
                return 0.0
                
            # Look for surface area in geometric representations
            for rep in representation.Representations:
                for item in rep.Items:
                    if hasattr(item, 'SurfaceArea'):
                        return float(item.SurfaceArea)
                        
        except Exception as e:
            self.logger.debug(f"Error calculating area from geometry: {e}")
            
        return 0.0

    def _estimate_area_from_properties(self, element) -> float:
        """Estimate area from basic properties like height and width."""
        try:
            # Get basic dimensions
            height = 0.0
            width = 0.0
            length = 0.0
            
            # Try to get dimensions from properties
            for rel in getattr(element, 'IsDefinedBy', []):
                if rel.is_a('IfcRelDefinesByProperties'):
                    prop_def = rel.RelatingPropertyDefinition
                    
                    if prop_def.is_a('IfcElementQuantity'):
                        for quantity in prop_def.Quantities:
                            if quantity.is_a('IfcQuantityLength'):
                                name = getattr(quantity, 'Name', '').lower()
                                value = float(quantity.LengthValue or 0)
                                
                                if 'height' in name or 'høyde' in name:
                                    height = value
                                elif 'width' in name or 'bredde' in name:
                                    width = value
                                elif 'length' in name or 'lengde' in name:
                                    length = value
            
            # Calculate area based on element type
            element_type = element.is_a()
            if element_type in ['IfcWall', 'IfcWallStandardCase']:
                # For walls: height * length
                if height > 0 and length > 0:
                    return height * length
                elif height > 0 and width > 0:
                    return height * width
            elif element_type == 'IfcSlab':
                # For slabs: length * width
                if length > 0 and width > 0:
                    return length * width
                    
        except Exception as e:
            self.logger.debug(f"Error estimating area from properties: {e}")
            
        return 0.0

    def _extract_material(self, element) -> str:
        """Extract material information from an IFC element."""
        try:
            # Check material associations
            for rel in getattr(element, 'HasAssociations', []):
                if rel.is_a('IfcRelAssociatesMaterial'):
                    material = rel.RelatingMaterial
                    
                    if material.is_a('IfcMaterial'):
                        return getattr(material, 'Name', '') or 'Unknown'
                    elif material.is_a('IfcMaterialLayerSetUsage'):
                        layer_set = material.ForLayerSet
                        if layer_set and layer_set.MaterialLayers:
                            # Return the first layer material
                            first_layer = layer_set.MaterialLayers[0]
                            if first_layer.Material:
                                return getattr(first_layer.Material, 'Name', '') or 'Unknown'
                    elif material.is_a('IfcMaterialList'):
                        if material.Materials:
                            return getattr(material.Materials[0], 'Name', '') or 'Unknown'
                            
        except Exception as e:
            self.logger.debug(f"Error extracting material: {e}")
            
        return 'Unknown'

    def calculate_surface_areas_by_type(self, surfaces: List[SurfaceData]) -> Dict[str, float]:
        """
        Calculate total surface areas grouped by type.
        
        Args:
            surfaces: List of SurfaceData objects
            
        Returns:
            Dictionary mapping surface type to total area
        """
        areas_by_type = {}
        
        for surface in surfaces:
            surface_type = surface.type
            if surface_type not in areas_by_type:
                areas_by_type[surface_type] = 0.0
            areas_by_type[surface_type] += surface.area
            
        return areas_by_type

    def validate_surfaces(self, surfaces: List[SurfaceData]) -> Tuple[bool, List[str]]:
        """
        Validate extracted surface data.
        
        Args:
            surfaces: List of SurfaceData objects to validate
            
        Returns:
            Tuple of (is_valid: bool, error_messages: List[str])
        """
        errors = []
        warnings = []
        
        if not surfaces:
            warnings.append("No surfaces found")
            
        # Check for duplicate IDs
        surface_ids = [surface.id for surface in surfaces]
        duplicate_ids = set([sid for sid in surface_ids if surface_ids.count(sid) > 1])
        if duplicate_ids:
            errors.append(f"Duplicate surface IDs found: {', '.join(duplicate_ids)}")

        # Check for missing or invalid areas
        zero_area_count = 0
        for surface in surfaces:
            if not surface.is_valid_area():
                zero_area_count += 1
                
        if zero_area_count > 0:
            warnings.append(f"{zero_area_count} surfaces have zero or invalid area")

        # Check for missing materials
        no_material_count = sum(1 for surface in surfaces if not surface.has_material())
        if no_material_count > 0:
            warnings.append(f"{no_material_count} surfaces have no material information")

        # Log warnings
        for warning in warnings:
            self.logger.warning(warning)

        return len(errors) == 0, errors + warnings