"""
Enhanced Space Boundary Parser

Enhanced version that better identifies adjacent space relationships.
"""

import math
from typing import List, Dict, Optional, Any, Tuple, Set
from dataclasses import dataclass
from enum import Enum
import ifcopenshell
import ifcopenshell.util.element
import ifcopenshell.util.unit
from ..utils.enhanced_logging import enhanced_logger
import ifcopenshell.geom
from ..data.space_boundary_model import SpaceBoundaryData


class AdjacencyDetectionMethod(Enum):
    """Methods for detecting adjacent spaces."""
    CORRESPONDING_BOUNDARY = "corresponding_boundary"
    SHARED_ELEMENTS = "shared_elements"
    GEOMETRIC_ANALYSIS = "geometric_analysis"
    NAME_HEURISTICS = "name_heuristics"


class BoundaryType(Enum):
    """Types of space boundaries."""
    PHYSICAL = "PHYSICAL"
    VIRTUAL = "VIRTUAL"
    UNDEFINED = "UNDEFINED"


class BoundaryLocation(Enum):
    """Location classification of boundaries."""
    INTERNAL = "INTERNAL"
    EXTERNAL = "EXTERNAL"
    EXTERNAL_EARTH = "EXTERNAL_EARTH"
    EXTERNAL_WATER = "EXTERNAL_WATER"
    EXTERNAL_FIRE = "EXTERNAL_FIRE"
    UNDEFINED = "UNDEFINED"


class SurfaceType(Enum):
    """Surface types for space boundaries."""
    WALL = "Wall"
    FLOOR = "Floor"
    CEILING = "Ceiling"
    ROOF = "Roof"
    WINDOW = "Window"
    DOOR = "Door"
    OPENING = "Opening"
    CURTAIN_WALL = "CurtainWall"
    RAILING = "Railing"
    OTHER = "Other"
    UNKNOWN = "Unknown"


class BoundaryOrientation(Enum):
    """Orientation of space boundaries."""
    NORTH = "North"
    SOUTH = "South"
    EAST = "East"
    WEST = "West"
    NORTHEAST = "Northeast"
    NORTHWEST = "Northwest"
    SOUTHEAST = "Southeast"
    SOUTHWEST = "Southwest"
    HORIZONTAL_UP = "HorizontalUp"
    HORIZONTAL_DOWN = "HorizontalDown"
    UNKNOWN = "Unknown"


@dataclass
class GeometricPoint:
    """3D point for geometric calculations."""
    x: float
    y: float
    z: float
    
    def distance_to(self, other: 'GeometricPoint') -> float:
        """Calculate Euclidean distance to another point."""
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2 + (self.z - other.z)**2)


@dataclass
class BoundaryGeometry:
    """Geometric representation of a space boundary."""
    center_point: GeometricPoint
    normal_vector: Tuple[float, float, float]
    vertices: List[GeometricPoint]
    area: float
    bounding_box: Tuple[GeometricPoint, GeometricPoint]  # min, max points


@dataclass
class ElementInfo:
    """Information about a building element."""
    guid: str = ""
    name: str = ""
    element_type: str = ""
    entity: Optional[Any] = None
    
    @property
    def surface_type(self) -> SurfaceType:
        """Get the surface type based on element type."""
        if not self.element_type:
            return SurfaceType.UNKNOWN
            
        element_type_lower = self.element_type.lower()
        
        if 'wall' in element_type_lower:
            return SurfaceType.WALL
        elif 'slab' in element_type_lower or 'floor' in element_type_lower:
            return SurfaceType.FLOOR
        elif 'roof' in element_type_lower:
            return SurfaceType.ROOF
        elif 'ceiling' in element_type_lower:
            return SurfaceType.CEILING
        elif 'window' in element_type_lower:
            return SurfaceType.WINDOW
        elif 'door' in element_type_lower:
            return SurfaceType.DOOR
        elif 'opening' in element_type_lower:
            return SurfaceType.OPENING
        elif 'curtain' in element_type_lower:
            return SurfaceType.CURTAIN_WALL
        elif 'railing' in element_type_lower:
            return SurfaceType.RAILING
        else:
            return SurfaceType.OTHER


@dataclass
class SpaceInfo:
    """Information about a space."""
    guid: str = ""
    name: str = ""
    long_name: str = ""
    entity: Optional[Any] = None
    
    @property
    def display_name(self) -> str:
        """Get the best display name for the space."""
        return self.name or self.long_name or f"Space {self.guid[:8]}"


@dataclass
class AdjacencyResult:
    """Result of adjacency detection."""
    adjacent_space_guid: str = ""
    adjacent_space_name: str = ""
    detection_method: Optional[AdjacencyDetectionMethod] = None
    confidence: float = 0.0  # 0.0 to 1.0
    
    @property
    def is_valid(self) -> bool:
        """Check if the adjacency result is valid."""
        return bool(self.adjacent_space_guid)


@dataclass
class ParserConfiguration:
    """Configuration options for the enhanced space boundary parser."""
    enabled_detection_methods: Set[AdjacencyDetectionMethod] = None
    geometric_tolerance: float = 0.01  # meters
    enable_performance_monitoring: bool = True
    max_geometric_search_distance: float = 1.0  # meters
    enable_detailed_logging: bool = False
    cache_geometry: bool = True
    
    def __post_init__(self):
        if self.enabled_detection_methods is None:
            self.enabled_detection_methods = {
                AdjacencyDetectionMethod.CORRESPONDING_BOUNDARY,
                AdjacencyDetectionMethod.SHARED_ELEMENTS,
                AdjacencyDetectionMethod.GEOMETRIC_ANALYSIS,
                AdjacencyDetectionMethod.NAME_HEURISTICS
            }


class EnhancedSpaceBoundaryParser:
    """Enhanced parser that better identifies adjacent space relationships."""

    def __init__(self, ifc_file=None, config: ParserConfiguration = None):
        """Initialize the enhanced space boundary parser."""
        self.ifc_file = ifc_file
        self.logger = enhanced_logger.logger
        self.config = config or ParserConfiguration()
        self._boundaries_cache = None
        self._geometry_settings = None
        self._space_cache = None
        self._element_to_spaces_map = None
        self._geometry_cache = {}
        self._performance_stats = {
            'total_boundaries_processed': 0,
            'adjacency_method_usage': {method.value: 0 for method in AdjacencyDetectionMethod},
            'geometric_calculations': 0,
            'cache_hits': 0
        }

    def set_ifc_file(self, ifc_file) -> None:
        """Set the IFC file to extract space boundaries from."""
        self.ifc_file = ifc_file
        self._boundaries_cache = None
        self._geometry_settings = None
        self._space_cache = None
        self._element_to_spaces_map = None
        self._geometry_cache = {}
        # Reset performance stats
        self._performance_stats = {
            'total_boundaries_processed': 0,
            'adjacency_method_usage': {method.value: 0 for method in AdjacencyDetectionMethod},
            'geometric_calculations': 0,
            'cache_hits': 0
        }

    def extract_space_boundaries_with_relationships(self, space_guid: Optional[str] = None) -> List[SpaceBoundaryData]:
        """
        Extract space boundaries with enhanced adjacent space detection.
        
        Args:
            space_guid: Optional GUID to filter boundaries for a specific space
            
        Returns:
            List of SpaceBoundaryData objects with enhanced relationship data
        """
        if not self.ifc_file:
            raise ValueError("No IFC file loaded. Use set_ifc_file() first.")

        try:
            # Start performance monitoring
            operation_id = None
            if self.config.enable_performance_monitoring:
                operation_id = enhanced_logger.start_operation_timing(
                    "extract_space_boundaries_with_relationships"
                )
            
            # Build caches for efficient lookup
            self._build_space_cache()
            self._build_element_to_spaces_map()
            
            # Build geometry cache if enabled
            if self.config.cache_geometry:
                self._build_geometry_cache()
            
            # Get all IfcRelSpaceBoundary entities
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

                    boundary_data = self._extract_enhanced_boundary_properties(ifc_boundary)
                    if boundary_data:
                        boundaries.append(boundary_data)
                except Exception as e:
                    self.logger.error(
                        f"Error extracting boundary {getattr(ifc_boundary, 'GlobalId', 'Unknown')}: {e}"
                    )
                    continue

            # Post-process to enhance adjacent space relationships
            self._enhance_adjacent_space_relationships(boundaries)

            self.logger.info(
                f"Successfully extracted {len(boundaries)} space boundaries with enhanced relationships"
            )

            return boundaries

        except Exception as e:
            error_msg = f"Failed to extract enhanced space boundaries: {e}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)

    def _build_space_cache(self) -> None:
        """Build a cache of all spaces for efficient lookup."""
        if self._space_cache is not None:
            return
            
        self._space_cache = {}
        spaces = self.ifc_file.by_type("IfcSpace")
        
        for space in spaces:
            guid = getattr(space, 'GlobalId', '')
            if guid:
                self._space_cache[guid] = {
                    'entity': space,
                    'name': getattr(space, 'Name', '') or '',
                    'long_name': getattr(space, 'LongName', '') or '',
                    'guid': guid
                }

    def _build_element_to_spaces_map(self) -> None:
        """Build a map of building elements to the spaces they bound."""
        if self._element_to_spaces_map is not None:
            return
            
        self._element_to_spaces_map = {}
        
        # Get all space boundaries
        boundaries = self.ifc_file.by_type("IfcRelSpaceBoundary")
        
        for boundary in boundaries:
            try:
                # Get the related building element
                element = getattr(boundary, 'RelatedBuildingElement', None)
                if not element:
                    continue
                    
                element_guid = getattr(element, 'GlobalId', '')
                if not element_guid:
                    continue
                
                # Get the relating space
                space = getattr(boundary, 'RelatingSpace', None)
                if not space:
                    continue
                    
                space_guid = getattr(space, 'GlobalId', '')
                if not space_guid:
                    continue
                
                # Add to map
                if element_guid not in self._element_to_spaces_map:
                    self._element_to_spaces_map[element_guid] = set()
                    
                self._element_to_spaces_map[element_guid].add(space_guid)
                
            except Exception as e:
                self.logger.debug(f"Error building element-to-spaces map: {e}")
                continue

    def _extract_enhanced_boundary_properties(self, ifc_boundary) -> Optional[SpaceBoundaryData]:
        """Extract properties with enhanced adjacent space detection."""
        try:
            # Extract basic properties (reuse existing logic)
            guid = getattr(ifc_boundary, 'GlobalId', '')
            name = getattr(ifc_boundary, 'Name', '') or ''
            description = getattr(ifc_boundary, 'Description', '') or ''

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

            # Determine boundary level
            boundary_level = self._determine_boundary_level(ifc_boundary)

            # Enhanced adjacent space detection
            adjacent_space_info = self._find_adjacent_space_enhanced(
                ifc_boundary, element_info, space_info, boundary_level
            )

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

            return boundary_data

        except Exception as e:
            self.logger.error(f"Error extracting enhanced boundary properties: {e}")
            return None

    def _find_adjacent_space_enhanced(self, ifc_boundary, element_info: Dict, space_info: Dict, boundary_level: int) -> Dict[str, str]:
        """Enhanced method to find adjacent spaces."""
        adjacent_info = {'guid': '', 'name': ''}
        
        try:
            # Method 1: Try the standard CorrespondingBoundary approach first
            corresponding_boundary = getattr(ifc_boundary, 'CorrespondingBoundary', None)
            if corresponding_boundary:
                adjacent_space = getattr(corresponding_boundary, 'RelatingSpace', None)
                if adjacent_space:
                    adjacent_info['guid'] = getattr(adjacent_space, 'GlobalId', '')
                    adjacent_info['name'] = getattr(adjacent_space, 'Name', '') or getattr(adjacent_space, 'LongName', '')
                    if adjacent_info['guid']:
                        return adjacent_info

            # Method 2: Use element-to-spaces mapping for shared elements
            element_guid = element_info.get('guid', '')
            current_space_guid = space_info.get('guid', '')
            
            if element_guid and current_space_guid and element_guid in self._element_to_spaces_map:
                spaces_sharing_element = self._element_to_spaces_map[element_guid]
                
                # Find other spaces that share this element
                for space_guid in spaces_sharing_element:
                    if space_guid != current_space_guid and space_guid in self._space_cache:
                        space_data = self._space_cache[space_guid]
                        adjacent_info['guid'] = space_guid
                        adjacent_info['name'] = space_data['name'] or space_data['long_name']
                        
                        # Log the relationship found
                        self.logger.debug(
                            f"Found adjacent space via shared element: {current_space_guid} -> {space_guid} "
                            f"via element {element_guid}"
                        )
                        return adjacent_info

            # Method 3: For internal boundaries without elements, try to find adjacent spaces geometrically
            if (internal_or_external := self._extract_internal_or_external_boundary(ifc_boundary)) == "INTERNAL":
                if not element_guid:  # Virtual boundary
                    adjacent_space_guid = self._find_adjacent_space_geometrically(ifc_boundary, current_space_guid)
                    if adjacent_space_guid and adjacent_space_guid in self._space_cache:
                        space_data = self._space_cache[adjacent_space_guid]
                        adjacent_info['guid'] = adjacent_space_guid
                        adjacent_info['name'] = space_data['name'] or space_data['long_name']
                        
                        self.logger.debug(
                            f"Found adjacent space geometrically: {current_space_guid} -> {adjacent_space_guid}"
                        )

        except Exception as e:
            self.logger.warning(f"Error in enhanced adjacent space detection: {e}")

        return adjacent_info

    def _find_adjacent_space_geometrically(self, ifc_boundary, current_space_guid: str) -> Optional[str]:
        """Try to find adjacent space using geometric analysis."""
        try:
            # This is a simplified approach - in a full implementation, you would:
            # 1. Get the boundary geometry
            # 2. Find other spaces whose boundaries are very close or overlapping
            # 3. Use spatial analysis to determine adjacency
            
            # For now, we'll use a simpler heuristic based on boundary names/descriptions
            boundary_name = getattr(ifc_boundary, 'Name', '') or ''
            boundary_desc = getattr(ifc_boundary, 'Description', '') or ''
            
            # Look for space references in the boundary name/description
            for space_guid, space_data in self._space_cache.items():
                if space_guid == current_space_guid:
                    continue
                    
                space_name = space_data['name']
                space_long_name = space_data['long_name']
                
                # Check if space name appears in boundary description
                if space_name and (space_name in boundary_name or space_name in boundary_desc):
                    return space_guid
                    
                if space_long_name and (space_long_name in boundary_name or space_long_name in boundary_desc):
                    return space_guid
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Error in geometric adjacent space detection: {e}")
            return None

    def _enhance_adjacent_space_relationships(self, boundaries: List[SpaceBoundaryData]) -> None:
        """Post-process boundaries to enhance adjacent space relationships."""
        try:
            # Group boundaries by related building element
            element_boundaries = {}
            
            for boundary in boundaries:
                element_guid = boundary.related_building_element_guid
                if element_guid:
                    if element_guid not in element_boundaries:
                        element_boundaries[element_guid] = []
                    element_boundaries[element_guid].append(boundary)
            
            # For each element shared by multiple spaces, establish adjacency
            for element_guid, element_boundary_list in element_boundaries.items():
                if len(element_boundary_list) >= 2:
                    # Create adjacency relationships between spaces sharing this element
                    for i, boundary1 in enumerate(element_boundary_list):
                        for boundary2 in element_boundary_list[i+1:]:
                            # If boundary1 doesn't have adjacent space info, use boundary2's space
                            if not boundary1.adjacent_space_guid and boundary2.related_space_guid:
                                boundary1.adjacent_space_guid = boundary2.related_space_guid
                                if boundary2.related_space_guid in self._space_cache:
                                    space_data = self._space_cache[boundary2.related_space_guid]
                                    boundary1.adjacent_space_name = space_data['name'] or space_data['long_name']
                                    boundary1.update_display_label()
                            
                            # If boundary2 doesn't have adjacent space info, use boundary1's space
                            if not boundary2.adjacent_space_guid and boundary1.related_space_guid:
                                boundary2.adjacent_space_guid = boundary1.related_space_guid
                                if boundary1.related_space_guid in self._space_cache:
                                    space_data = self._space_cache[boundary1.related_space_guid]
                                    boundary2.adjacent_space_name = space_data['name'] or space_data['long_name']
                                    boundary2.update_display_label()
            
            # Count enhanced relationships
            enhanced_count = sum(1 for b in boundaries if b.adjacent_space_guid)
            self.logger.info(f"Enhanced {enhanced_count} boundaries with adjacent space relationships")
            
        except Exception as e:
            self.logger.error(f"Error enhancing adjacent space relationships: {e}")

    # Reuse existing methods from the original parser
    def _extract_physical_or_virtual_boundary(self, ifc_boundary) -> BoundaryType:
        """Extract PhysicalOrVirtualBoundary property."""
        try:
            boundary_type = getattr(ifc_boundary, 'PhysicalOrVirtualBoundary', None)
            if boundary_type:
                boundary_str = str(boundary_type).upper()
                if boundary_str == "PHYSICAL":
                    return BoundaryType.PHYSICAL
                elif boundary_str == "VIRTUAL":
                    return BoundaryType.VIRTUAL
            return BoundaryType.UNDEFINED
        except Exception:
            return BoundaryType.UNDEFINED

    def _extract_internal_or_external_boundary(self, ifc_boundary) -> BoundaryLocation:
        """Extract InternalOrExternalBoundary property."""
        try:
            boundary_type = getattr(ifc_boundary, 'InternalOrExternalBoundary', None)
            if boundary_type:
                boundary_str = str(boundary_type).upper()
                try:
                    return BoundaryLocation(boundary_str)
                except ValueError:
                    # Handle any boundary types not in our enum
                    if "INTERNAL" in boundary_str:
                        return BoundaryLocation.INTERNAL
                    elif "EXTERNAL" in boundary_str:
                        return BoundaryLocation.EXTERNAL
            return BoundaryLocation.UNDEFINED
        except Exception:
            return BoundaryLocation.UNDEFINED

    def _extract_related_building_element(self, ifc_boundary) -> ElementInfo:
        """Extract information about the related building element."""
        try:
            related_element = getattr(ifc_boundary, 'RelatedBuildingElement', None)
            if related_element:
                return ElementInfo(
                    guid=getattr(related_element, 'GlobalId', ''),
                    name=getattr(related_element, 'Name', '') or '',
                    element_type=related_element.is_a() if hasattr(related_element, 'is_a') else '',
                    entity=related_element
                )
        except Exception as e:
            self.logger.warning(f"Error extracting related building element: {e}")

        return ElementInfo()

    def _extract_related_space(self, ifc_boundary) -> SpaceInfo:
        """Extract information about the related space."""
        try:
            related_space = getattr(ifc_boundary, 'RelatingSpace', None)
            if related_space:
                return SpaceInfo(
                    guid=getattr(related_space, 'GlobalId', ''),
                    name=getattr(related_space, 'Name', '') or '',
                    long_name=getattr(related_space, 'LongName', '') or '',
                    entity=related_space
                )
        except Exception as e:
            self.logger.warning(f"Error extracting related space: {e}")

        return SpaceInfo()

    def _extract_connection_geometry(self, ifc_boundary) -> Dict[str, Any]:
        """Extract and process connection geometry."""
        return {
            'area': 0.0,
            'vertices': [],
            'normal_vector': None,
            'center_point': None
        }

    def _determine_boundary_orientation(self, geometry_info: Dict[str, Any]) -> str:
        """Determine boundary orientation from geometry."""
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
        """Determine if this is a 1st level or 2nd level boundary."""
        try:
            related_element = getattr(ifc_boundary, 'RelatedBuildingElement', None)
            if related_element:
                return 1  # 1st level: space-to-element
            else:
                corresponding_boundary = getattr(ifc_boundary, 'CorrespondingBoundary', None)
                if corresponding_boundary:
                    return 2  # 2nd level: space-to-space
                else:
                    return 1  # Default to 1st level
        except Exception:
            return 1

    def _extract_material_properties(self, building_element) -> Dict[str, Any]:
        """Extract material properties from building element."""
        return {}

    def _extract_thermal_properties(self, building_element) -> Dict[str, Any]:
        """Extract thermal properties from building element."""
        return {}