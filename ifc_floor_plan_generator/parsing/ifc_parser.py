"""
IFC parser for IFC Floor Plan Generator.

Wrapper around IfcOpenShell for robust IFC file handling with comprehensive error handling.
"""

import os
import logging
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path

try:
    import ifcopenshell
    import ifcopenshell.util.element
    import ifcopenshell.util.unit
except ImportError:
    ifcopenshell = None

from ..errors.handler import ErrorHandler
from ..errors.exceptions import IFCOpenError, NoStoreysFoundError
from ..models import ClassFilters


class IFCParser:
    """Wrapper around IfcOpenShell for robust IFC file handling."""
    
    def __init__(self, error_handler: Optional[ErrorHandler] = None):
        """Initialize IFC parser.
        
        Args:
            error_handler: Error handler instance for structured error handling
        """
        self._error_handler = error_handler or ErrorHandler()
        self._logger = logging.getLogger(__name__)
        
        # Check if IfcOpenShell is available
        if ifcopenshell is None:
            raise ImportError(
                "IfcOpenShell is required but not installed. "
                "Install it with: pip install ifcopenshell"
            )
    
    def open_file(self, file_path: str) -> ifcopenshell.file:
        """Open IFC file and return IfcFile object.
        
        Args:
            file_path: Path to the IFC file
            
        Returns:
            ifcopenshell.file: The opened IFC file object
            
        Raises:
            IFCOpenError: If the file cannot be opened
        """
        try:
            # Validate file path
            if not file_path:
                raise ValueError("File path cannot be empty")
            
            file_path = str(Path(file_path).resolve())
            
            # Check if file exists
            if not os.path.exists(file_path):
                context = {
                    'file_path': file_path,
                    'original_error': f"File not found: {file_path}"
                }
                self._error_handler.log_error("IFC_OPEN_FAILED", context)
                raise self._error_handler.handle_error("IFC_OPEN_FAILED", context)
            
            # Check if file is readable
            if not os.access(file_path, os.R_OK):
                context = {
                    'file_path': file_path,
                    'original_error': f"File not readable: {file_path}"
                }
                self._error_handler.log_error("IFC_OPEN_FAILED", context)
                raise self._error_handler.handle_error("IFC_OPEN_FAILED", context)
            
            # Attempt to open the IFC file
            self._logger.info(f"Opening IFC file: {file_path}")
            ifc_file = ifcopenshell.open(file_path)
            
            # Validate that we got a valid IFC file
            if ifc_file is None:
                context = {
                    'file_path': file_path,
                    'original_error': "IfcOpenShell returned None"
                }
                self._error_handler.log_error("IFC_OPEN_FAILED", context)
                raise self._error_handler.handle_error("IFC_OPEN_FAILED", context)
            
            # Log basic file information
            schema = getattr(ifc_file, 'schema', 'Unknown')
            self._logger.info(f"Successfully opened IFC file with schema: {schema}")
            
            return ifc_file
            
        except IFCOpenError:
            # Re-raise our custom errors
            raise
        except Exception as e:
            # Handle any other exceptions
            context = {
                'file_path': file_path,
                'original_error': str(e)
            }
            self._error_handler.log_error("IFC_OPEN_FAILED", context)
            raise self._error_handler.handle_error("IFC_OPEN_FAILED", context)
    
    def extract_storeys(self, ifc_file: ifcopenshell.file) -> List[Any]:
        """Extract IfcBuildingStorey elements from IFC file.
        
        Args:
            ifc_file: The opened IFC file object
            
        Returns:
            List of IfcBuildingStorey elements
            
        Raises:
            NoStoreysFoundError: If no building storeys are found
        """
        try:
            if ifc_file is None:
                raise ValueError("IFC file cannot be None")
            
            # Extract all IfcBuildingStorey elements
            storeys = ifc_file.by_type("IfcBuildingStorey")
            
            if not storeys:
                # Log detailed information about what we found instead
                buildings = ifc_file.by_type("IfcBuilding")
                sites = ifc_file.by_type("IfcSite")
                projects = ifc_file.by_type("IfcProject")
                
                context = {
                    'file_path': getattr(ifc_file, 'name', 'unknown'),
                    'buildings_found': len(buildings),
                    'sites_found': len(sites),
                    'projects_found': len(projects)
                }
                
                self._error_handler.log_error("NO_STOREYS_FOUND", context)
                raise self._error_handler.handle_error("NO_STOREYS_FOUND", context)
            
            # Log information about found storeys
            storey_names = []
            for storey in storeys:
                name = getattr(storey, 'Name', None) or getattr(storey, 'LongName', None) or f"Storey_{storey.id()}"
                storey_names.append(name)
            
            self._logger.info(f"Found {len(storeys)} building storeys: {', '.join(storey_names)}")
            
            return storeys
            
        except NoStoreysFoundError:
            # Re-raise our custom errors
            raise
        except Exception as e:
            # Handle any other exceptions
            context = {
                'file_path': getattr(ifc_file, 'name', 'unknown'),
                'original_error': str(e)
            }
            self._error_handler.log_error("NO_STOREYS_FOUND", context)
            raise self._error_handler.handle_error("NO_STOREYS_FOUND", context)
    
    def get_elements_by_storey(self, storey: Any, class_filters: Optional[ClassFilters] = None) -> List[Any]:
        """Get all elements associated with a building storey with optional filtering.
        
        Args:
            storey: IfcBuildingStorey element
            class_filters: Optional filters for IFC classes
            
        Returns:
            List of IFC elements associated with the storey, filtered by class if specified
        """
        try:
            if storey is None:
                raise ValueError("Storey cannot be None")
            
            # Get all elements contained in or related to this storey
            elements = []
            
            # Method 1: Get elements directly contained in the storey
            if hasattr(storey, 'ContainsElements'):
                for rel in storey.ContainsElements:
                    if hasattr(rel, 'RelatedElements'):
                        elements.extend(rel.RelatedElements)
            
            # Method 2: Get elements through spatial containment relationships
            try:
                contained_elements = ifcopenshell.util.element.get_decomposition(storey)
                if contained_elements:
                    elements.extend(contained_elements)
            except:
                # If util method fails, continue with what we have
                pass
            
            # Method 3: Alternative approach - get all elements and filter by storey
            if not elements:
                # This is a fallback method - get all building elements and check their containment
                ifc_file = storey.file
                all_elements = []
                
                # Get common building element types
                element_types = [
                    "IfcWall", "IfcWallStandardCase", "IfcCurtainWall",
                    "IfcDoor", "IfcWindow", 
                    "IfcSlab", "IfcRoof", "IfcStair", "IfcRailing",
                    "IfcColumn", "IfcBeam",
                    "IfcBuildingElementProxy", "IfcFlowTerminal",
                    "IfcFurnishingElement", "IfcDistributionElement"
                ]
                
                for element_type in element_types:
                    try:
                        type_elements = ifc_file.by_type(element_type)
                        all_elements.extend(type_elements)
                    except:
                        continue
                
                # Filter elements that belong to this storey
                for element in all_elements:
                    try:
                        element_storey = ifcopenshell.util.element.get_container(element)
                        if element_storey and element_storey.id() == storey.id():
                            elements.append(element)
                    except:
                        continue
            
            # Remove duplicates while preserving order
            seen_ids = set()
            unique_elements = []
            for element in elements:
                if element.id() not in seen_ids:
                    seen_ids.add(element.id())
                    unique_elements.append(element)
            
            elements = unique_elements
            
            # Apply class filters if provided
            if class_filters:
                filtered_elements = []
                for element in elements:
                    ifc_class = element.is_a()
                    if class_filters.should_include_class(ifc_class):
                        filtered_elements.append(element)
                elements = filtered_elements
            
            # Log information about found elements
            if elements:
                element_counts = {}
                for element in elements:
                    ifc_class = element.is_a()
                    element_counts[ifc_class] = element_counts.get(ifc_class, 0) + 1
                
                storey_name = getattr(storey, 'Name', None) or f"Storey_{storey.id()}"
                self._logger.info(f"Found {len(elements)} elements in storey '{storey_name}': {element_counts}")
            else:
                storey_name = getattr(storey, 'Name', None) or f"Storey_{storey.id()}"
                self._logger.warning(f"No elements found in storey '{storey_name}'")
            
            return elements
            
        except Exception as e:
            storey_name = getattr(storey, 'Name', None) or f"Storey_{getattr(storey, 'id', lambda: 'unknown')()}"
            self._error_handler.log_warning(
                f"Error getting elements for storey '{storey_name}': {str(e)}",
                {'storey_name': storey_name, 'error': str(e)}
            )
            return []
    
    def detect_units(self, ifc_file: ifcopenshell.file) -> float:
        """Detect unit scale from IFC file metadata.
        
        Args:
            ifc_file: The opened IFC file object
            
        Returns:
            float: Scale factor to convert IFC units to meters
        """
        try:
            if ifc_file is None:
                raise ValueError("IFC file cannot be None")
            
            # Try to use IfcOpenShell's utility function
            try:
                # Get the length unit from the IFC file
                length_unit = ifcopenshell.util.unit.get_unit(ifc_file, "LENGTHUNIT")
                
                if length_unit:
                    # Get the unit name and prefix
                    unit_name = getattr(length_unit, 'Name', '').upper()
                    
                    # Handle different unit types
                    if hasattr(length_unit, 'Prefix') and length_unit.Prefix:
                        prefix = length_unit.Prefix.upper()
                    else:
                        prefix = None
                    
                    # Calculate scale factor based on unit
                    scale_factor = self._calculate_unit_scale(unit_name, prefix)
                    
                    if scale_factor is not None:
                        self._logger.info(f"Detected units: {prefix or ''}{unit_name}, scale factor: {scale_factor}")
                        return scale_factor
                
            except Exception as e:
                self._logger.warning(f"Failed to detect units using utility function: {e}")
            
            # Fallback method: look for unit assignments manually
            try:
                # Get project and look for unit assignments
                projects = ifc_file.by_type("IfcProject")
                if projects:
                    project = projects[0]
                    if hasattr(project, 'UnitsInContext') and project.UnitsInContext:
                        units_context = project.UnitsInContext
                        if hasattr(units_context, 'Units'):
                            for unit in units_context.Units:
                                if hasattr(unit, 'UnitType') and unit.UnitType == 'LENGTHUNIT':
                                    if hasattr(unit, 'Name'):
                                        unit_name = unit.Name.upper()
                                        prefix = getattr(unit, 'Prefix', None)
                                        if prefix:
                                            prefix = prefix.upper()
                                        
                                        scale_factor = self._calculate_unit_scale(unit_name, prefix)
                                        if scale_factor is not None:
                                            self._logger.info(f"Detected units (fallback): {prefix or ''}{unit_name}, scale factor: {scale_factor}")
                                            return scale_factor
            
            except Exception as e:
                self._logger.warning(f"Failed to detect units using fallback method: {e}")
            
            # If all methods fail, log warning and return default scale
            self._error_handler.log_warning(
                "Could not detect units from IFC file, using default scale of 1.0",
                {'fallback_scale': 1.0}
            )
            return 1.0
            
        except Exception as e:
            # Handle any unexpected errors
            self._error_handler.log_warning(
                f"Error during units detection: {str(e)}, using default scale of 1.0",
                {'error': str(e), 'fallback_scale': 1.0}
            )
            return 1.0
    
    def _calculate_unit_scale(self, unit_name: str, prefix: Optional[str] = None) -> Optional[float]:
        """Calculate scale factor for converting units to meters.
        
        Args:
            unit_name: Name of the unit (e.g., 'METRE', 'FOOT', 'INCH')
            prefix: Optional prefix (e.g., 'MILLI', 'CENTI', 'KILO')
            
        Returns:
            Scale factor to convert to meters, or None if unknown unit
        """
        # Base unit scales (to meters)
        base_scales = {
            'METRE': 1.0,
            'METER': 1.0,
            'FOOT': 0.3048,
            'INCH': 0.0254,
            'MILLIMETRE': 0.001,
            'MILLIMETER': 0.001,
            'CENTIMETRE': 0.01,
            'CENTIMETER': 0.01,
            'KILOMETRE': 1000.0,
            'KILOMETER': 1000.0,
            'YARD': 0.9144
        }
        
        # Prefix multipliers
        prefix_multipliers = {
            'MILLI': 0.001,
            'CENTI': 0.01,
            'DECI': 0.1,
            'DECA': 10.0,
            'HECTO': 100.0,
            'KILO': 1000.0
        }
        
        # Get base scale
        base_scale = base_scales.get(unit_name)
        if base_scale is None:
            return None
        
        # Apply prefix multiplier if present
        if prefix:
            prefix_multiplier = prefix_multipliers.get(prefix, 1.0)
            return base_scale * prefix_multiplier
        
        return base_scale
    
    def get_file_info(self, ifc_file: ifcopenshell.file) -> Dict[str, Any]:
        """Get basic information about the IFC file.
        
        Args:
            ifc_file: The opened IFC file object
            
        Returns:
            Dictionary containing file information
        """
        try:
            info = {
                'schema': getattr(ifc_file, 'schema', 'Unknown'),
                'file_name': getattr(ifc_file, 'name', 'Unknown'),
                'total_elements': len(ifc_file),
                'storeys_count': len(ifc_file.by_type("IfcBuildingStorey")),
                'buildings_count': len(ifc_file.by_type("IfcBuilding")),
                'sites_count': len(ifc_file.by_type("IfcSite")),
                'projects_count': len(ifc_file.by_type("IfcProject"))
            }
            
            # Try to get application info
            try:
                applications = ifc_file.by_type("IfcApplication")
                if applications:
                    app = applications[0]
                    info['application'] = {
                        'name': getattr(app, 'ApplicationFullName', 'Unknown'),
                        'version': getattr(app, 'Version', 'Unknown'),
                        'identifier': getattr(app, 'ApplicationIdentifier', 'Unknown')
                    }
            except:
                pass
            
            return info
            
        except Exception as e:
            self._logger.warning(f"Error getting file info: {e}")
            return {'error': str(e)}
    
    def filter_elements_by_class(self, elements: List[Any], class_filters: ClassFilters) -> List[Any]:
        """Filter a list of IFC elements by class filters.
        
        Args:
            elements: List of IFC elements to filter
            class_filters: Class filters to apply
            
        Returns:
            List of filtered IFC elements
        """
        if not class_filters:
            return elements
        
        filtered_elements = []
        skipped_count = 0
        
        for element in elements:
            try:
                ifc_class = element.is_a()
                if class_filters.should_include_class(ifc_class):
                    filtered_elements.append(element)
                else:
                    skipped_count += 1
            except Exception as e:
                # If we can't determine the class, skip the element
                self._error_handler.log_warning(
                    f"Could not determine IFC class for element {getattr(element, 'id', lambda: 'unknown')()}: {e}",
                    {'element_id': getattr(element, 'id', lambda: 'unknown')(), 'error': str(e)}
                )
                skipped_count += 1
        
        if skipped_count > 0:
            self._logger.info(f"Filtered out {skipped_count} elements based on class filters")
        
        return filtered_elements
    
    def get_element_classes_in_storey(self, storey: Any) -> Dict[str, int]:
        """Get a count of all IFC classes present in a storey.
        
        Args:
            storey: IfcBuildingStorey element
            
        Returns:
            Dictionary mapping IFC class names to their counts
        """
        elements = self.get_elements_by_storey(storey, class_filters=None)
        class_counts = {}
        
        for element in elements:
            try:
                ifc_class = element.is_a()
                class_counts[ifc_class] = class_counts.get(ifc_class, 0) + 1
            except Exception as e:
                self._error_handler.log_warning(
                    f"Could not determine IFC class for element: {e}",
                    {'element_id': getattr(element, 'id', lambda: 'unknown')(), 'error': str(e)}
                )
        
        return class_counts
    
    def get_all_element_classes_in_file(self, ifc_file: ifcopenshell.file) -> Dict[str, int]:
        """Get a count of all IFC classes present in the entire file.
        
        Args:
            ifc_file: The opened IFC file object
            
        Returns:
            Dictionary mapping IFC class names to their counts
        """
        class_counts = {}
        
        try:
            # Get all entity instances in the file
            for element in ifc_file:
                try:
                    ifc_class = element.is_a()
                    class_counts[ifc_class] = class_counts.get(ifc_class, 0) + 1
                except:
                    continue
        except Exception as e:
            self._error_handler.log_warning(
                f"Error counting element classes: {e}",
                {'error': str(e)}
            )
        
        return class_counts
    
    def validate_class_filters(self, class_filters: ClassFilters, ifc_file: ifcopenshell.file) -> Dict[str, Any]:
        """Validate class filters against available classes in the IFC file.
        
        Args:
            class_filters: Class filters to validate
            ifc_file: The opened IFC file object
            
        Returns:
            Dictionary containing validation results and suggestions
        """
        available_classes = set(self.get_all_element_classes_in_file(ifc_file).keys())
        
        # Check include filters
        invalid_includes = []
        for ifc_class in class_filters.include_ifc_classes:
            if ifc_class not in available_classes:
                invalid_includes.append(ifc_class)
        
        # Check exclude filters
        invalid_excludes = []
        for ifc_class in class_filters.exclude_ifc_classes:
            if ifc_class not in available_classes:
                invalid_excludes.append(ifc_class)
        
        # Find common building element classes that might be relevant
        common_building_classes = [
            "IfcWall", "IfcWallStandardCase", "IfcCurtainWall",
            "IfcDoor", "IfcWindow", 
            "IfcSlab", "IfcRoof", "IfcStair", "IfcRailing",
            "IfcColumn", "IfcBeam",
            "IfcBuildingElementProxy"
        ]
        
        available_building_classes = [cls for cls in common_building_classes if cls in available_classes]
        
        validation_result = {
            'valid': len(invalid_includes) == 0 and len(invalid_excludes) == 0,
            'invalid_includes': invalid_includes,
            'invalid_excludes': invalid_excludes,
            'available_classes': sorted(list(available_classes)),
            'available_building_classes': available_building_classes,
            'total_classes': len(available_classes)
        }
        
        # Log warnings for invalid filters
        if invalid_includes:
            self._error_handler.log_warning(
                f"Include filters contain classes not found in IFC file: {invalid_includes}",
                {'invalid_classes': invalid_includes, 'available_classes': available_building_classes}
            )
        
        if invalid_excludes:
            self._error_handler.log_warning(
                f"Exclude filters contain classes not found in IFC file: {invalid_excludes}",
                {'invalid_classes': invalid_excludes, 'available_classes': available_building_classes}
            )
        
        return validation_result
    
    def get_unit_scale_with_override(self, ifc_file: ifcopenshell.file, manual_scale: Optional[float] = None) -> float:
        """Get unit scale factor with optional manual override.
        
        Args:
            ifc_file: The opened IFC file object
            manual_scale: Optional manual scale override
            
        Returns:
            Scale factor to convert IFC units to meters
        """
        if manual_scale is not None:
            if manual_scale <= 0:
                self._error_handler.log_warning(
                    f"Invalid manual unit scale {manual_scale}, using auto-detection",
                    {'invalid_scale': manual_scale}
                )
                return self.detect_units(ifc_file)
            
            self._logger.info(f"Using manual unit scale override: {manual_scale}")
            return manual_scale
        
        return self.detect_units(ifc_file)
    
    def scale_coordinates(self, coordinates: List[Tuple[float, float]], scale_factor: float) -> List[Tuple[float, float]]:
        """Scale 2D coordinates by the given factor.
        
        Args:
            coordinates: List of (x, y) coordinate tuples
            scale_factor: Scale factor to apply
            
        Returns:
            List of scaled coordinate tuples
        """
        if scale_factor == 1.0:
            return coordinates
        
        return [(x * scale_factor, y * scale_factor) for x, y in coordinates]
    
    def scale_3d_coordinates(self, coordinates: List[Tuple[float, float, float]], scale_factor: float) -> List[Tuple[float, float, float]]:
        """Scale 3D coordinates by the given factor.
        
        Args:
            coordinates: List of (x, y, z) coordinate tuples
            scale_factor: Scale factor to apply
            
        Returns:
            List of scaled coordinate tuples
        """
        if scale_factor == 1.0:
            return coordinates
        
        return [(x * scale_factor, y * scale_factor, z * scale_factor) for x, y, z in coordinates]
    
    def scale_distance(self, distance: float, scale_factor: float) -> float:
        """Scale a distance value by the given factor.
        
        Args:
            distance: Distance value to scale
            scale_factor: Scale factor to apply
            
        Returns:
            Scaled distance value
        """
        return distance * scale_factor
    
    def convert_ifc_coordinates_to_meters(self, ifc_file: ifcopenshell.file, coordinates: List[Tuple[float, float]], manual_scale: Optional[float] = None) -> List[Tuple[float, float]]:
        """Convert IFC coordinates to meters using detected or manual scale.
        
        Args:
            ifc_file: The opened IFC file object
            coordinates: List of (x, y) coordinate tuples in IFC units
            manual_scale: Optional manual scale override
            
        Returns:
            List of coordinate tuples converted to meters
        """
        scale_factor = self.get_unit_scale_with_override(ifc_file, manual_scale)
        return self.scale_coordinates(coordinates, scale_factor)
    
    def get_units_info(self, ifc_file: ifcopenshell.file) -> Dict[str, Any]:
        """Get comprehensive information about units in the IFC file.
        
        Args:
            ifc_file: The opened IFC file object
            
        Returns:
            Dictionary containing units information
        """
        units_info = {
            'detected_scale': None,
            'detected_unit': None,
            'detected_prefix': None,
            'length_units': [],
            'area_units': [],
            'volume_units': [],
            'angle_units': []
        }
        
        try:
            # Get detected scale
            units_info['detected_scale'] = self.detect_units(ifc_file)
            
            # Try to get detailed unit information
            try:
                projects = ifc_file.by_type("IfcProject")
                if projects:
                    project = projects[0]
                    if hasattr(project, 'UnitsInContext') and project.UnitsInContext:
                        units_context = project.UnitsInContext
                        if hasattr(units_context, 'Units'):
                            for unit in units_context.Units:
                                unit_info = {
                                    'type': getattr(unit, 'UnitType', 'Unknown'),
                                    'name': getattr(unit, 'Name', 'Unknown'),
                                    'prefix': getattr(unit, 'Prefix', None)
                                }
                                
                                unit_type = unit_info['type']
                                if unit_type == 'LENGTHUNIT':
                                    units_info['length_units'].append(unit_info)
                                    if not units_info['detected_unit']:
                                        units_info['detected_unit'] = unit_info['name']
                                        units_info['detected_prefix'] = unit_info['prefix']
                                elif unit_type == 'AREAUNIT':
                                    units_info['area_units'].append(unit_info)
                                elif unit_type == 'VOLUMEUNIT':
                                    units_info['volume_units'].append(unit_info)
                                elif unit_type == 'PLANEANGLEUNIT':
                                    units_info['angle_units'].append(unit_info)
            except Exception as e:
                self._logger.warning(f"Error getting detailed units info: {e}")
            
            # Try alternative method using IfcOpenShell utilities
            try:
                length_unit = ifcopenshell.util.unit.get_unit(ifc_file, "LENGTHUNIT")
                if length_unit and not units_info['detected_unit']:
                    units_info['detected_unit'] = getattr(length_unit, 'Name', 'Unknown')
                    units_info['detected_prefix'] = getattr(length_unit, 'Prefix', None)
            except:
                pass
            
        except Exception as e:
            self._error_handler.log_warning(
                f"Error getting units information: {e}",
                {'error': str(e)}
            )
        
        return units_info
    
    def validate_unit_scale(self, scale_factor: float) -> bool:
        """Validate that a unit scale factor is reasonable.
        
        Args:
            scale_factor: Scale factor to validate
            
        Returns:
            True if the scale factor seems reasonable, False otherwise
        """
        # Scale factors should be positive and within reasonable bounds
        # Common scales: mm (0.001), cm (0.01), m (1.0), ft (0.3048), in (0.0254)
        if scale_factor <= 0:
            return False
        
        # Very small scales (smaller than micrometers) are probably wrong
        if scale_factor < 1e-6:
            return False
        
        # Very large scales (larger than kilometers) are probably wrong
        if scale_factor > 1000:
            return False
        
        return True