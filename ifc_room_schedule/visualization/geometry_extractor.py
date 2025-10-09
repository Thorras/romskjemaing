"""
Geometry Extractor for IFC 2D Floor Plan Data

This module extracts 2D geometric data from IFC files for floor plan visualization,
including space boundaries, floor levels, and coordinate transformations.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
import math

try:
    import ifcopenshell
    import ifcopenshell.geom
    IFC_AVAILABLE = True
except ImportError:
    IFC_AVAILABLE = False

from .geometry_models import Point2D, Polygon2D, FloorLevel, FloorGeometry
from ..data.space_model import SpaceData


class GeometryExtractionError(Exception):
    """Exception raised when geometry extraction fails."""
    
    def __init__(self, message: str, error_type: str, affected_spaces: List[str] = None):
        super().__init__(message)
        self.error_type = error_type
        self.affected_spaces = affected_spaces or []


class GeometryExtractor:
    """Extracts 2D geometric data from IFC files for floor plan visualization."""
    
    def __init__(self):
        """Initialize the geometry extractor."""
        self.logger = logging.getLogger(__name__)
        
        if not IFC_AVAILABLE:
            raise ImportError(
                "IfcOpenShell is required for geometry extraction. "
                "Install with: pip install ifcopenshell"
            )
    
    def extract_floor_geometry(self, ifc_file, progress_callback=None) -> Dict[str, FloorGeometry]:
        """
        Extract 2D floor plan geometry from IFC file with progressive loading support.
        
        Args:
            ifc_file: Loaded IFC file object
            progress_callback: Optional callback function for progress updates
            
        Returns:
            Dictionary mapping floor IDs to FloorGeometry objects
            
        Raises:
            GeometryExtractionError: If extraction fails
        """
        try:
            self.logger.info("Starting enhanced floor geometry extraction")
            
            # Check file size and complexity for progressive loading
            total_spaces = len(ifc_file.by_type("IfcSpace"))
            total_storeys = len(ifc_file.by_type("IfcBuildingStorey"))
            
            self.logger.info(f"IFC file contains {total_spaces} spaces across {total_storeys} storeys")
            
            # Determine if progressive loading is needed
            use_progressive_loading = total_spaces > 100 or total_storeys > 10
            
            if use_progressive_loading:
                self.logger.info("Using progressive loading for large IFC file")
                return self._extract_geometry_progressive(ifc_file, progress_callback)
            else:
                return self._extract_geometry_standard(ifc_file, progress_callback)
            
        except GeometryExtractionError:
            raise
        except MemoryError as e:
            raise GeometryExtractionError(
                "Insufficient memory for geometry extraction",
                "memory_error"
            )
        except Exception as e:
            raise GeometryExtractionError(
                f"Failed to extract floor geometry: {str(e)}",
                "extraction_error"
            )
    
    def _extract_geometry_standard(self, ifc_file, progress_callback=None) -> Dict[str, FloorGeometry]:
        """Standard geometry extraction for smaller files."""
        try:
            # Get all building storeys (floors)
            floor_levels = self.get_floor_levels(ifc_file)
            if not floor_levels:
                raise GeometryExtractionError(
                    "No building storeys found in IFC file",
                    "no_floors"
                )
            
            # Extract geometry for each floor
            floor_geometries = {}
            total_floors = len(floor_levels)
            
            for i, floor_level in enumerate(floor_levels):
                try:
                    if progress_callback:
                        progress = (i / total_floors) * 100
                        progress_callback(f"Processing floor {floor_level.name}", progress)
                    
                    geometry = self._extract_floor_level_geometry_enhanced(ifc_file, floor_level)
                    if geometry:
                        floor_geometries[floor_level.id] = geometry
                        self.logger.info(
                            f"Extracted geometry for floor {floor_level.name}: "
                            f"{geometry.get_room_count()} rooms"
                        )
                    else:
                        self.logger.warning(f"No geometry found for floor {floor_level.name}")
                        
                except Exception as e:
                    self.logger.error(f"Failed to extract geometry for floor {floor_level.name}: {e}")
                    # Continue with other floors
                    continue
            
            if not floor_geometries:
                raise GeometryExtractionError(
                    "No geometric data could be extracted from any floor",
                    "no_geometry"
                )
            
            if progress_callback:
                progress_callback("Geometry extraction complete", 100)
            
            self.logger.info(f"Successfully extracted geometry for {len(floor_geometries)} floors")
            return floor_geometries
            
        except Exception as e:
            if isinstance(e, GeometryExtractionError):
                raise
            raise GeometryExtractionError(f"Standard extraction failed: {str(e)}", "extraction_error")
    
    def _extract_geometry_progressive(self, ifc_file, progress_callback=None) -> Dict[str, FloorGeometry]:
        """Progressive geometry extraction for large files."""
        try:
            self.logger.info("Starting progressive geometry extraction")
            
            # Get floor levels
            floor_levels = self.get_floor_levels(ifc_file)
            if not floor_levels:
                raise GeometryExtractionError(
                    "No building storeys found in IFC file",
                    "no_floors"
                )
            
            floor_geometries = {}
            total_floors = len(floor_levels)
            
            # Process floors in batches to manage memory
            batch_size = max(1, min(5, total_floors // 2))  # Process 1-5 floors at a time
            
            for batch_start in range(0, total_floors, batch_size):
                batch_end = min(batch_start + batch_size, total_floors)
                batch_floors = floor_levels[batch_start:batch_end]
                
                self.logger.info(f"Processing floor batch {batch_start + 1}-{batch_end} of {total_floors}")
                
                for i, floor_level in enumerate(batch_floors):
                    try:
                        if progress_callback:
                            overall_progress = ((batch_start + i) / total_floors) * 100
                            progress_callback(f"Processing floor {floor_level.name}", overall_progress)
                        
                        # Use memory-efficient extraction for each floor
                        geometry = self._extract_floor_level_geometry_memory_efficient(ifc_file, floor_level)
                        if geometry:
                            floor_geometries[floor_level.id] = geometry
                            self.logger.info(
                                f"Extracted geometry for floor {floor_level.name}: "
                                f"{geometry.get_room_count()} rooms"
                            )
                        
                    except Exception as e:
                        self.logger.error(f"Failed to extract geometry for floor {floor_level.name}: {e}")
                        continue
                
                # Force garbage collection between batches
                import gc
                gc.collect()
            
            if not floor_geometries:
                raise GeometryExtractionError(
                    "No geometric data could be extracted from any floor",
                    "no_geometry"
                )
            
            if progress_callback:
                progress_callback("Progressive extraction complete", 100)
            
            self.logger.info(f"Successfully extracted geometry for {len(floor_geometries)} floors using progressive loading")
            return floor_geometries
            
        except Exception as e:
            if isinstance(e, GeometryExtractionError):
                raise
            raise GeometryExtractionError(f"Progressive extraction failed: {str(e)}", "extraction_error")
    
    def get_floor_levels(self, ifc_file) -> List[FloorLevel]:
        """
        Extract floor levels from IFC file with enhanced detection and grouping.
        
        Args:
            ifc_file: Loaded IFC file object
            
        Returns:
            List of FloorLevel objects sorted by elevation
        """
        try:
            floor_levels = []
            processed_storeys = set()
            
            # Get all IfcBuildingStorey entities
            storeys = ifc_file.by_type("IfcBuildingStorey")
            self.logger.info(f"Found {len(storeys)} building storeys in IFC file")
            
            for storey in storeys:
                try:
                    # Skip if already processed (handle duplicates)
                    storey_id = storey.GlobalId
                    if storey_id in processed_storeys:
                        continue
                    processed_storeys.add(storey_id)
                    
                    # Extract enhanced storey information
                    storey_name = self._extract_storey_name(storey)
                    elevation = self._extract_storey_elevation_enhanced(storey)
                    
                    # Get spaces on this storey with validation
                    space_guids = self._get_spaces_on_storey_enhanced(ifc_file, storey)
                    
                    # Validate storey has meaningful content
                    if not space_guids and not self._storey_has_building_elements(ifc_file, storey):
                        self.logger.debug(f"Skipping empty storey: {storey_name}")
                        continue
                    
                    floor_level = FloorLevel(
                        id=storey_id,
                        name=storey_name,
                        elevation=elevation,
                        spaces=space_guids
                    )
                    
                    floor_levels.append(floor_level)
                    self.logger.debug(f"Processed storey: {storey_name} at elevation {elevation:.2f}m with {len(space_guids)} spaces")
                    
                except Exception as e:
                    self.logger.warning(f"Failed to process storey {getattr(storey, 'Name', 'Unknown')}: {e}")
                    continue
            
            # Group spaces by elevation if no explicit storeys found
            if not floor_levels:
                self.logger.info("No valid building storeys found, attempting elevation-based grouping")
                floor_levels = self._group_spaces_by_elevation(ifc_file)
            
            # Sort floors by elevation and validate sequence
            floor_levels = self._sort_and_validate_floors(floor_levels)
            
            # Handle orphaned spaces (spaces not assigned to any floor)
            orphaned_spaces = self._find_orphaned_spaces(ifc_file, floor_levels)
            if orphaned_spaces:
                floor_levels = self._handle_orphaned_spaces(orphaned_spaces, floor_levels)
            
            self.logger.info(f"Successfully extracted {len(floor_levels)} floor levels")
            return floor_levels
            
        except Exception as e:
            self.logger.error(f"Failed to extract floor levels: {e}")
            return []
    
    def extract_space_boundaries(self, ifc_space) -> List[Polygon2D]:
        """
        Extract 2D boundary polygons for an IFC space with enhanced error handling.
        
        Args:
            ifc_space: IFC space entity
            
        Returns:
            List of Polygon2D objects representing space boundaries
        """
        try:
            polygons = []
            space_guid = ifc_space.GlobalId
            space_name = getattr(ifc_space, 'Name', None) or f"Space {space_guid[:8]}"
            
            self.logger.debug(f"Extracting boundaries for space: {space_name} ({space_guid})")
            
            # Method 1: Try IfcOpenShell direct geometry extraction (most accurate)
            try:
                polygon = self._extract_polygon_with_ifcopenshell(ifc_space, space_guid, space_name)
                if polygon and self._validate_polygon(polygon):
                    polygons.append(polygon)
                    self.logger.debug(f"Extracted polygon using IfcOpenShell for space {space_name}")
                    return polygons
            except Exception as e:
                self.logger.debug(f"IfcOpenShell extraction failed: {e}")
            
            # Method 2: Try to extract from space boundaries (fallback)
            try:
                boundaries = self._get_space_boundaries_enhanced(ifc_space)
                if boundaries:
                    for boundary in boundaries:
                        try:
                            polygon = self._extract_boundary_polygon_enhanced(boundary, space_guid, space_name)
                            if polygon and self._validate_polygon(polygon):
                                polygons.append(polygon)
                        except Exception as e:
                            self.logger.debug(f"Failed to extract boundary polygon: {e}")
                            continue
                    
                    if polygons:
                        self.logger.debug(f"Extracted {len(polygons)} polygons from space boundaries")
                        return polygons
            except Exception as e:
                self.logger.debug(f"Space boundary extraction failed: {e}")
            
            # Method 3: Try to get geometry directly from space representation
            try:
                polygon = self._extract_space_geometry_enhanced(ifc_space, space_guid, space_name)
                if polygon and self._validate_polygon(polygon):
                    polygons.append(polygon)
                    self.logger.debug(f"Extracted geometry from space representation")
                    return polygons
            except Exception as e:
                self.logger.debug(f"Direct geometry extraction failed: {e}")
            
            # Method 4: Try to extract from related building elements
            try:
                polygon = self._extract_geometry_from_related_elements(ifc_space, space_guid, space_name)
                if polygon and self._validate_polygon(polygon):
                    polygons.append(polygon)
                    self.logger.debug(f"Extracted geometry from related elements")
                    return polygons
            except Exception as e:
                self.logger.debug(f"Related elements extraction failed: {e}")
            
            # Method 5: Generate fallback geometry only if space has meaningful properties
            try:
                # Only generate fallback if we have a real space name and GUID
                if space_name and space_name != "Unknown Space" and space_guid and space_guid != "unknown":
                    polygon = self._generate_fallback_geometry(ifc_space, space_guid, space_name)
                    if polygon and self._validate_polygon(polygon):
                        polygons.append(polygon)
                        self.logger.debug(f"Generated fallback geometry for space {space_name}")
                        return polygons
            except Exception as e:
                self.logger.debug(f"Fallback geometry generation failed: {e}")
            
            # If all methods fail, log warning but don't crash
            self.logger.debug(f"Could not extract any geometry for space {space_name} ({space_guid})")
            return []
            
        except Exception as e:
            self.logger.error(f"Failed to extract space boundaries for {space_name}: {e}")
            return []
    
    def convert_to_2d_coordinates(self, geometry_3d, space_guid: str = "unknown", space_name: str = "Unknown Space") -> Optional[Polygon2D]:
        """
        Convert 3D IFC geometry to 2D floor plan coordinates with enhanced processing.
        IFC coordinates are in millimeters, so we convert to meters for display.
        
        Args:
            geometry_3d: 3D geometry data from IFC
            space_guid: GUID of the space
            space_name: Name of the space
            
        Returns:
            Polygon2D object or None if conversion fails
        """
        try:
            if not geometry_3d:
                return None
            
            # Handle different geometry types
            if hasattr(geometry_3d, 'verts') and hasattr(geometry_3d, 'faces'):
                # Extract vertices and project to 2D (ignore Z coordinate)
                vertices = geometry_3d.verts
                faces = geometry_3d.faces
                
                if not vertices or len(vertices) < 9:  # Need at least 3 points (x,y,z each)
                    return None
                
                # Convert vertices to 2D points (convert from mm to meters)
                points_3d = []
                for i in range(0, len(vertices), 3):
                    if i + 2 < len(vertices):
                        # Convert from millimeters to meters
                        x = vertices[i] / 1000.0
                        y = vertices[i + 1] / 1000.0
                        z = vertices[i + 2] / 1000.0
                        points_3d.append((x, y, z))
                
                if len(points_3d) < 3:
                    return None
                
                # Find the dominant plane (usually XY plane for floor plans)
                # Calculate the average Z coordinate to determine floor level
                avg_z = sum(p[2] for p in points_3d) / len(points_3d)
                
                # Filter points that are close to the floor level (within 0.5 meters)
                floor_points = []
                for x, y, z in points_3d:
                    if abs(z - avg_z) < 0.5:  # Points close to floor level
                        floor_points.append(Point2D(x, y))
                
                if len(floor_points) < 3:
                    # Fallback: use all points projected to XY plane
                    floor_points = [Point2D(x, y) for x, y, z in points_3d]
                
                if len(floor_points) >= 3:
                    # Remove duplicate points (now in meters, so use smaller threshold)
                    unique_points = []
                    for point in floor_points:
                        is_duplicate = False
                        for existing in unique_points:
                            if abs(point.x - existing.x) < 0.001 and abs(point.y - existing.y) < 0.001:  # 1mm tolerance
                                is_duplicate = True
                                break
                        if not is_duplicate:
                            unique_points.append(point)
                    
                    if len(unique_points) >= 3:
                        # Create polygon and validate
                        polygon = Polygon2D(unique_points, space_guid, space_name)
                        
                        # Validate polygon area (now in square meters)
                        area = polygon.get_area()
                        if area > 0.1:  # Minimum area threshold (0.1 m²)
                            return polygon
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Failed to convert 3D geometry to 2D for {space_name}: {e}")
            return None
    
    def _extract_floor_level_geometry_enhanced(self, ifc_file, floor_level: FloorLevel) -> Optional[FloorGeometry]:
        """Extract geometry for a specific floor level with enhanced processing."""
        try:
            room_polygons = []
            extraction_stats = {
                'total_spaces': len(floor_level.spaces),
                'successful_extractions': 0,
                'failed_extractions': 0,
                'fallback_geometries': 0
            }
            
            # Pre-cache space entities for efficiency
            space_entities = {}
            for space in ifc_file.by_type("IfcSpace"):
                if hasattr(space, 'GlobalId') and space.GlobalId in floor_level.spaces:
                    space_entities[space.GlobalId] = space
            
            # Track processed spaces to avoid duplicates
            processed_spaces = set()
            
            # Extract geometry for each space
            for space_guid in floor_level.spaces:
                try:
                    if space_guid in processed_spaces:
                        continue
                    
                    space_entity = space_entities.get(space_guid)
                    if not space_entity:
                        self.logger.debug(f"Space entity not found for GUID: {space_guid}")
                        extraction_stats['failed_extractions'] += 1
                        continue
                    
                    # Extract boundaries for this space
                    space_polygons = self.extract_space_boundaries(space_entity)
                    
                    if space_polygons:
                        # Merge multiple polygons for the same space into one if possible
                        merged_polygon = self._merge_space_polygons(space_polygons, space_guid)
                        if merged_polygon:
                            room_polygons.append(merged_polygon)
                            extraction_stats['successful_extractions'] += 1
                            processed_spaces.add(space_guid)
                            
                            # Check if polygon was generated using fallback methods
                            if self._is_fallback_geometry(merged_polygon):
                                extraction_stats['fallback_geometries'] += 1
                        else:
                            # If merging fails, use the largest polygon
                            largest_polygon = max(space_polygons, key=lambda p: p.get_area())
                            room_polygons.append(largest_polygon)
                            extraction_stats['successful_extractions'] += 1
                            processed_spaces.add(space_guid)
                    else:
                        extraction_stats['failed_extractions'] += 1
                    
                except Exception as e:
                    self.logger.debug(f"Failed to extract geometry for space {space_guid}: {e}")
                    extraction_stats['failed_extractions'] += 1
                    continue
            
            # Log extraction statistics
            self.logger.info(
                f"Floor {floor_level.name} extraction stats: "
                f"{extraction_stats['successful_extractions']}/{extraction_stats['total_spaces']} successful, "
                f"{extraction_stats['fallback_geometries']} fallback geometries"
            )
            
            if room_polygons:
                # Create floor geometry with enhanced metadata
                floor_geometry = FloorGeometry(
                    level=floor_level,
                    room_polygons=room_polygons
                )
                
                # Add extraction metadata
                floor_geometry.metadata = {
                    'extraction_stats': extraction_stats,
                    'extraction_method': 'enhanced',
                    'total_area': floor_geometry.get_total_area(),
                    'room_count': floor_geometry.get_room_count()
                }
                
                return floor_geometry
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to extract enhanced floor level geometry: {e}")
            return None
    
    def _extract_floor_level_geometry_memory_efficient(self, ifc_file, floor_level: FloorLevel) -> Optional[FloorGeometry]:
        """Extract geometry for a floor level with memory-efficient processing."""
        try:
            room_polygons = []
            
            # Process spaces in smaller batches to reduce memory usage
            batch_size = 20  # Process 20 spaces at a time
            total_spaces = len(floor_level.spaces)
            
            for batch_start in range(0, total_spaces, batch_size):
                batch_end = min(batch_start + batch_size, total_spaces)
                batch_spaces = floor_level.spaces[batch_start:batch_end]
                
                # Process batch
                batch_polygons = []
                for space_guid in batch_spaces:
                    try:
                        # Find space entity efficiently
                        space_entity = self._get_space_by_guid(ifc_file, space_guid)
                        if space_entity:
                            space_polygons = self.extract_space_boundaries(space_entity)
                            batch_polygons.extend(space_polygons)
                        
                    except Exception as e:
                        self.logger.debug(f"Failed to extract geometry for space {space_guid}: {e}")
                        continue
                
                # Add batch results to main collection
                room_polygons.extend(batch_polygons)
                
                # Clear batch data to free memory
                batch_polygons.clear()
            
            if room_polygons:
                return FloorGeometry(
                    level=floor_level,
                    room_polygons=room_polygons
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to extract memory-efficient floor level geometry: {e}")
            return None
    
    def _is_fallback_geometry(self, polygon: Polygon2D) -> bool:
        """Check if a polygon was generated using fallback methods."""
        try:
            # Simple heuristic: check if polygon is a perfect square/rectangle
            # which is typical of fallback geometries
            bounds = polygon.get_bounds()
            width = bounds[2] - bounds[0]
            height = bounds[3] - bounds[1]
            
            # Check if it's close to a square with common fallback dimensions
            common_sizes = [3.0, 4.0, 5.0, math.sqrt(15), math.sqrt(20), math.sqrt(25)]
            
            for size in common_sizes:
                if (abs(width - size) < 0.1 and abs(height - size) < 0.1):
                    return True
            
            return False
            
        except Exception as e:
            self.logger.debug(f"Failed to check if geometry is fallback: {e}")
            return False
    
    def _extract_storey_name(self, storey) -> str:
        """Extract enhanced storey name with fallback options."""
        try:
            # Primary: Use Name attribute
            if hasattr(storey, 'Name') and storey.Name:
                name = str(storey.Name).strip()
                if name:
                    return name
            
            # Secondary: Use LongName attribute
            if hasattr(storey, 'LongName') and storey.LongName:
                long_name = str(storey.LongName).strip()
                if long_name:
                    return long_name
            
            # Tertiary: Extract from ObjectType
            if hasattr(storey, 'ObjectType') and storey.ObjectType:
                obj_type = str(storey.ObjectType).strip()
                if obj_type and obj_type.lower() != 'ifcbuildingstorey':
                    return obj_type
            
            # Fallback: Use GlobalId prefix
            storey_id = getattr(storey, 'GlobalId', 'Unknown')
            return f"Level {storey_id[:8]}"
            
        except Exception as e:
            self.logger.warning(f"Failed to extract storey name: {e}")
            return f"Level {getattr(storey, 'GlobalId', 'Unknown')[:8]}"
    
    def _extract_storey_elevation_enhanced(self, storey) -> float:
        """Extract elevation from building storey with enhanced detection."""
        try:
            elevation = None
            
            # Method 1: Try ObjectPlacement hierarchy
            if hasattr(storey, 'ObjectPlacement') and storey.ObjectPlacement:
                elevation = self._extract_elevation_from_placement(storey.ObjectPlacement)
                if elevation is not None:
                    return elevation
            
            # Method 2: Try direct Elevation property
            if hasattr(storey, 'Elevation') and storey.Elevation is not None:
                try:
                    elevation = float(storey.Elevation)
                    if not (math.isnan(elevation) or math.isinf(elevation)):
                        return elevation
                except (ValueError, TypeError):
                    pass
            
            # Method 3: Try to extract from property sets
            elevation = self._extract_elevation_from_properties(storey)
            if elevation is not None:
                return elevation
            
            # Method 4: Try to infer from contained spaces
            elevation = self._infer_elevation_from_spaces(storey)
            if elevation is not None:
                return elevation
            
            # Default to 0.0
            self.logger.debug(f"Using default elevation 0.0 for storey {getattr(storey, 'Name', 'Unknown')}")
            return 0.0
            
        except Exception as e:
            self.logger.warning(f"Failed to extract storey elevation: {e}")
            return 0.0
    
    def _extract_elevation_from_placement(self, placement, accumulated_z: float = 0.0) -> Optional[float]:
        """Recursively extract elevation from placement hierarchy."""
        try:
            current_z = accumulated_z
            
            # Get local placement coordinates
            if hasattr(placement, 'RelativePlacement') and placement.RelativePlacement:
                rel_placement = placement.RelativePlacement
                if hasattr(rel_placement, 'Location') and rel_placement.Location:
                    location = rel_placement.Location
                    if hasattr(location, 'Coordinates') and location.Coordinates:
                        coords = location.Coordinates
                        if len(coords) >= 3:
                            current_z += float(coords[2])
            
            # Recurse up the placement hierarchy
            if hasattr(placement, 'PlacementRelTo') and placement.PlacementRelTo:
                parent_z = self._extract_elevation_from_placement(placement.PlacementRelTo, current_z)
                if parent_z is not None:
                    return parent_z
            
            return current_z if current_z != 0.0 else None
            
        except Exception as e:
            self.logger.debug(f"Failed to extract elevation from placement: {e}")
            return None
    
    def _extract_elevation_from_properties(self, storey) -> Optional[float]:
        """Extract elevation from property sets."""
        try:
            if not hasattr(storey, 'IsDefinedBy'):
                return None
            
            for definition in storey.IsDefinedBy:
                if hasattr(definition, 'RelatingPropertyDefinition'):
                    prop_def = definition.RelatingPropertyDefinition
                    
                    # Check property sets
                    if prop_def.is_a("IfcPropertySet"):
                        for prop in getattr(prop_def, 'HasProperties', []):
                            if hasattr(prop, 'Name') and prop.Name:
                                prop_name = prop.Name.lower()
                                if any(keyword in prop_name for keyword in ['elevation', 'level', 'height', 'z']):
                                    if hasattr(prop, 'NominalValue') and prop.NominalValue:
                                        try:
                                            value = float(prop.NominalValue.wrappedValue)
                                            if not (math.isnan(value) or math.isinf(value)):
                                                return value
                                        except (ValueError, TypeError, AttributeError):
                                            continue
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Failed to extract elevation from properties: {e}")
            return None
    
    def _infer_elevation_from_spaces(self, storey) -> Optional[float]:
        """Infer storey elevation from contained spaces."""
        try:
            # This would require analyzing space geometries
            # For now, return None to use default
            return None
            
        except Exception as e:
            self.logger.debug(f"Failed to infer elevation from spaces: {e}")
            return None
    
    def _group_spaces_by_elevation(self, ifc_file) -> List[FloorLevel]:
        """Group spaces by elevation when no explicit storeys are found."""
        try:
            self.logger.info("Grouping spaces by elevation analysis")
            
            # Get all spaces and their elevations
            spaces_with_elevations = []
            all_spaces = ifc_file.by_type("IfcSpace")
            
            for space in all_spaces:
                if hasattr(space, 'GlobalId') and self._validate_space_for_floor_plan(space):
                    elevation = self._extract_space_elevation(space)
                    spaces_with_elevations.append((space.GlobalId, elevation, space))
            
            if not spaces_with_elevations:
                return []
            
            # Group spaces by similar elevations (within tolerance)
            elevation_tolerance = 0.5  # 0.5 meters tolerance
            elevation_groups = {}
            
            for space_guid, elevation, space_entity in spaces_with_elevations:
                # Find existing group with similar elevation
                matched_group = None
                for group_elevation in elevation_groups.keys():
                    if abs(elevation - group_elevation) <= elevation_tolerance:
                        matched_group = group_elevation
                        break
                
                if matched_group is not None:
                    elevation_groups[matched_group].append(space_guid)
                else:
                    elevation_groups[elevation] = [space_guid]
            
            # Create floor levels from elevation groups
            floor_levels = []
            for i, (elevation, space_guids) in enumerate(sorted(elevation_groups.items())):
                floor_level = FloorLevel(
                    id=f"elevation_floor_{i}",
                    name=f"Level {elevation:.1f}m",
                    elevation=elevation,
                    spaces=space_guids
                )
                floor_levels.append(floor_level)
            
            self.logger.info(f"Created {len(floor_levels)} floors from elevation grouping")
            return floor_levels
            
        except Exception as e:
            self.logger.error(f"Failed to group spaces by elevation: {e}")
            return []
    
    def _extract_space_elevation(self, space) -> float:
        """Extract elevation from space placement."""
        try:
            if hasattr(space, 'ObjectPlacement') and space.ObjectPlacement:
                elevation = self._extract_elevation_from_placement(space.ObjectPlacement)
                if elevation is not None:
                    return elevation
            
            # Default elevation
            return 0.0
            
        except Exception as e:
            self.logger.debug(f"Failed to extract space elevation: {e}")
            return 0.0
    
    def _sort_and_validate_floors(self, floor_levels: List[FloorLevel]) -> List[FloorLevel]:
        """Sort floors by elevation and validate the sequence."""
        try:
            if not floor_levels:
                return []
            
            # Sort by elevation
            sorted_floors = sorted(floor_levels, key=lambda f: f.elevation)
            
            # Validate elevation sequence and detect potential issues
            for i in range(1, len(sorted_floors)):
                current_floor = sorted_floors[i]
                previous_floor = sorted_floors[i-1]
                
                elevation_diff = current_floor.elevation - previous_floor.elevation
                
                # Check for suspicious elevation differences
                if elevation_diff < 0.1:  # Very small difference
                    self.logger.warning(
                        f"Small elevation difference between floors: "
                        f"{previous_floor.name} ({previous_floor.elevation:.2f}m) and "
                        f"{current_floor.name} ({current_floor.elevation:.2f}m)"
                    )
                elif elevation_diff > 10.0:  # Very large difference
                    self.logger.warning(
                        f"Large elevation difference between floors: "
                        f"{previous_floor.name} ({previous_floor.elevation:.2f}m) and "
                        f"{current_floor.name} ({current_floor.elevation:.2f}m)"
                    )
            
            return sorted_floors
            
        except Exception as e:
            self.logger.error(f"Failed to sort and validate floors: {e}")
            return floor_levels
    
    def _find_orphaned_spaces(self, ifc_file, floor_levels: List[FloorLevel]) -> List[str]:
        """Find spaces that are not assigned to any floor."""
        try:
            # Get all space GUIDs assigned to floors
            assigned_spaces = set()
            for floor in floor_levels:
                assigned_spaces.update(floor.spaces)
            
            # Get all valid spaces in the file
            all_spaces = set()
            for space in ifc_file.by_type("IfcSpace"):
                if hasattr(space, 'GlobalId') and self._validate_space_for_floor_plan(space):
                    all_spaces.add(space.GlobalId)
            
            # Find orphaned spaces
            orphaned_spaces = all_spaces - assigned_spaces
            
            if orphaned_spaces:
                self.logger.info(f"Found {len(orphaned_spaces)} orphaned spaces")
            
            return list(orphaned_spaces)
            
        except Exception as e:
            self.logger.error(f"Failed to find orphaned spaces: {e}")
            return []
    
    def _handle_orphaned_spaces(self, orphaned_spaces: List[str], floor_levels: List[FloorLevel]) -> List[FloorLevel]:
        """Handle orphaned spaces by assigning them to appropriate floors or creating new ones."""
        try:
            if not orphaned_spaces:
                return floor_levels
            
            self.logger.info(f"Handling {len(orphaned_spaces)} orphaned spaces")
            
            # If no floors exist, create a default floor for orphaned spaces
            if not floor_levels:
                default_floor = FloorLevel(
                    id="default_floor",
                    name="Default Floor",
                    elevation=0.0,
                    spaces=orphaned_spaces
                )
                return [default_floor]
            
            # Try to assign orphaned spaces to existing floors based on elevation
            updated_floors = floor_levels.copy()
            remaining_orphaned = []
            
            for space_guid in orphaned_spaces:
                # Get space entity and its elevation
                space_entity = self._get_space_by_guid(ifc_file, space_guid)
                if space_entity:
                    space_elevation = self._extract_space_elevation(space_entity)
                    
                    # Find closest floor by elevation
                    closest_floor = min(updated_floors, key=lambda f: abs(f.elevation - space_elevation))
                    elevation_diff = abs(closest_floor.elevation - space_elevation)
                    
                    # If elevation is close enough (within 2 meters), assign to that floor
                    if elevation_diff <= 2.0:
                        closest_floor.add_space(space_guid)
                        self.logger.debug(f"Assigned orphaned space {space_guid} to floor {closest_floor.name}")
                    else:
                        remaining_orphaned.append(space_guid)
            
            # Create a new floor for remaining orphaned spaces
            if remaining_orphaned:
                orphaned_floor = FloorLevel(
                    id="orphaned_spaces_floor",
                    name="Unassigned Spaces",
                    elevation=max(f.elevation for f in updated_floors) + 3.0,  # Place above highest floor
                    spaces=remaining_orphaned
                )
                updated_floors.append(orphaned_floor)
                self.logger.info(f"Created new floor for {len(remaining_orphaned)} remaining orphaned spaces")
            
            return updated_floors
            
        except Exception as e:
            self.logger.error(f"Failed to handle orphaned spaces: {e}")
            return floor_levels
    
    def _get_spaces_on_storey_enhanced(self, ifc_file, storey) -> List[str]:
        """Get all space GUIDs on a building storey with enhanced detection."""
        try:
            space_guids = set()  # Use set to automatically handle duplicates
            
            # Method 1: IfcRelAggregates relationships (decomposition)
            for rel in ifc_file.by_type("IfcRelAggregates"):
                if hasattr(rel, 'RelatingObject') and rel.RelatingObject == storey:
                    if hasattr(rel, 'RelatedObjects'):
                        for obj in rel.RelatedObjects:
                            if obj.is_a("IfcSpace") and hasattr(obj, 'GlobalId'):
                                space_guids.add(obj.GlobalId)
            
            # Method 2: IfcRelContainedInSpatialStructure (spatial containment)
            for rel in ifc_file.by_type("IfcRelContainedInSpatialStructure"):
                if hasattr(rel, 'RelatingStructure') and rel.RelatingStructure == storey:
                    if hasattr(rel, 'RelatedElements'):
                        for element in rel.RelatedElements:
                            if element.is_a("IfcSpace") and hasattr(element, 'GlobalId'):
                                space_guids.add(element.GlobalId)
            
            # Method 3: Check spaces that reference this storey in their placement
            all_spaces = ifc_file.by_type("IfcSpace")
            for space in all_spaces:
                if hasattr(space, 'GlobalId') and self._is_space_on_storey(space, storey):
                    space_guids.add(space.GlobalId)
            
            # Method 4: Validate spaces have valid geometry or properties
            validated_spaces = []
            for space_guid in space_guids:
                space_entity = self._get_space_by_guid(ifc_file, space_guid)
                if space_entity and self._validate_space_for_floor_plan(space_entity):
                    validated_spaces.append(space_guid)
            
            self.logger.debug(f"Found {len(validated_spaces)} valid spaces on storey {getattr(storey, 'Name', 'Unknown')}")
            return validated_spaces
            
        except Exception as e:
            self.logger.warning(f"Failed to get spaces on storey: {e}")
            return []
    
    def _is_space_on_storey(self, space, storey) -> bool:
        """Check if a space belongs to a specific storey based on placement hierarchy."""
        try:
            # Check if space's placement hierarchy references the storey
            if hasattr(space, 'ObjectPlacement') and space.ObjectPlacement:
                return self._placement_references_storey(space.ObjectPlacement, storey)
            return False
            
        except Exception as e:
            self.logger.debug(f"Failed to check space-storey relationship: {e}")
            return False
    
    def _placement_references_storey(self, placement, target_storey) -> bool:
        """Recursively check if placement hierarchy references target storey."""
        try:
            # Check current placement
            if hasattr(placement, 'PlacementRelTo') and placement.PlacementRelTo:
                parent_placement = placement.PlacementRelTo
                
                # Check if parent placement belongs to target storey
                if hasattr(parent_placement, 'PlacesObject') and parent_placement.PlacesObject:
                    for obj in parent_placement.PlacesObject:
                        if obj == target_storey:
                            return True
                
                # Recurse up the hierarchy
                return self._placement_references_storey(parent_placement, target_storey)
            
            return False
            
        except Exception as e:
            self.logger.debug(f"Failed to check placement hierarchy: {e}")
            return False
    
    def _get_space_by_guid(self, ifc_file, space_guid: str):
        """Get space entity by GUID."""
        try:
            for space in ifc_file.by_type("IfcSpace"):
                if hasattr(space, 'GlobalId') and space.GlobalId == space_guid:
                    return space
            return None
            
        except Exception as e:
            self.logger.debug(f"Failed to get space by GUID {space_guid}: {e}")
            return None
    
    def _validate_space_for_floor_plan(self, space) -> bool:
        """Validate that a space is suitable for floor plan visualization."""
        try:
            # Check if space has a name or identifier
            if not (hasattr(space, 'Name') or hasattr(space, 'GlobalId')):
                return False
            
            # Check if space has some geometric representation or properties
            has_geometry = (
                hasattr(space, 'Representation') and space.Representation or
                hasattr(space, 'ObjectPlacement') and space.ObjectPlacement
            )
            
            has_properties = (
                hasattr(space, 'IsDefinedBy') and space.IsDefinedBy
            )
            
            # Space should have either geometry or meaningful properties
            return has_geometry or has_properties
            
        except Exception as e:
            self.logger.debug(f"Failed to validate space: {e}")
            return False
    
    def _storey_has_building_elements(self, ifc_file, storey) -> bool:
        """Check if storey contains building elements (walls, slabs, etc.)."""
        try:
            # Check for building elements contained in this storey
            for rel in ifc_file.by_type("IfcRelContainedInSpatialStructure"):
                if hasattr(rel, 'RelatingStructure') and rel.RelatingStructure == storey:
                    if hasattr(rel, 'RelatedElements'):
                        for element in rel.RelatedElements:
                            if element.is_a() in ["IfcWall", "IfcSlab", "IfcColumn", "IfcBeam", "IfcDoor", "IfcWindow"]:
                                return True
            
            return False
            
        except Exception as e:
            self.logger.debug(f"Failed to check building elements on storey: {e}")
            return False
    
    def _get_space_boundaries_enhanced(self, ifc_space) -> List[Any]:
        """Get space boundaries for an IFC space with enhanced detection."""
        try:
            boundaries = []
            ifc_file = ifc_space.file
            
            # Look for different types of space boundary relationships
            boundary_types = [
                "IfcRelSpaceBoundary",
                "IfcRelSpaceBoundary1stLevel", 
                "IfcRelSpaceBoundary2ndLevel"
            ]
            
            for boundary_type in boundary_types:
                try:
                    for rel in ifc_file.by_type(boundary_type):
                        if hasattr(rel, 'RelatingSpace') and rel.RelatingSpace == ifc_space:
                            # Validate boundary has useful geometry
                            if self._validate_space_boundary(rel):
                                boundaries.append(rel)
                except Exception as e:
                    self.logger.debug(f"Failed to get {boundary_type} boundaries: {e}")
                    continue
            
            # Remove duplicate boundaries
            unique_boundaries = []
            seen_elements = set()
            
            for boundary in boundaries:
                # Use related building element as uniqueness key
                element_key = None
                if hasattr(boundary, 'RelatedBuildingElement') and boundary.RelatedBuildingElement:
                    element_key = boundary.RelatedBuildingElement.GlobalId
                elif hasattr(boundary, 'GlobalId'):
                    element_key = boundary.GlobalId
                
                if element_key and element_key not in seen_elements:
                    seen_elements.add(element_key)
                    unique_boundaries.append(boundary)
            
            self.logger.debug(f"Found {len(unique_boundaries)} unique space boundaries")
            return unique_boundaries
            
        except Exception as e:
            self.logger.warning(f"Failed to get space boundaries: {e}")
            return []
    
    def _validate_space_boundary(self, boundary) -> bool:
        """Validate that a space boundary has useful geometry information."""
        try:
            # Check if boundary has connection geometry
            if hasattr(boundary, 'ConnectionGeometry') and boundary.ConnectionGeometry:
                return True
            
            # Check if boundary has a related building element with geometry
            if hasattr(boundary, 'RelatedBuildingElement') and boundary.RelatedBuildingElement:
                element = boundary.RelatedBuildingElement
                if hasattr(element, 'Representation') and element.Representation:
                    return True
            
            return False
            
        except Exception as e:
            self.logger.debug(f"Failed to validate space boundary: {e}")
            return False
    
    def _extract_boundary_polygon_enhanced(self, boundary, space_guid: str, space_name: str) -> Optional[Polygon2D]:
        """Extract polygon from space boundary with enhanced geometry processing."""
        try:
            # Method 1: Try to extract from ConnectionGeometry
            if hasattr(boundary, 'ConnectionGeometry') and boundary.ConnectionGeometry:
                polygon = self._extract_from_connection_geometry(boundary.ConnectionGeometry, space_guid, space_name)
                if polygon:
                    return polygon
            
            # Method 2: Try to extract from related building element
            if hasattr(boundary, 'RelatedBuildingElement') and boundary.RelatedBuildingElement:
                element = boundary.RelatedBuildingElement
                polygon = self._extract_from_building_element(element, space_guid, space_name)
                if polygon:
                    return polygon
            
            # Don't create fallback geometry from boundaries - this creates too many duplicates
            return None
            
        except Exception as e:
            self.logger.debug(f"Failed to extract boundary polygon: {e}")
            return None
    
    def _extract_from_connection_geometry(self, connection_geom, space_guid: str, space_name: str) -> Optional[Polygon2D]:
        """Extract polygon from IFC connection geometry."""
        try:
            # Handle different types of connection geometry
            if hasattr(connection_geom, 'SurfaceOnRelatingElement'):
                surface = connection_geom.SurfaceOnRelatingElement
                return self._extract_from_surface_geometry(surface, space_guid, space_name)
            
            if hasattr(connection_geom, 'SurfaceOnRelatedElement'):
                surface = connection_geom.SurfaceOnRelatedElement
                return self._extract_from_surface_geometry(surface, space_guid, space_name)
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Failed to extract from connection geometry: {e}")
            return None
    
    def _extract_from_surface_geometry(self, surface, space_guid: str, space_name: str) -> Optional[Polygon2D]:
        """Extract polygon from surface geometry."""
        try:
            # This would require detailed IFC geometry processing
            # For now, return None to use fallback methods
            return None
            
        except Exception as e:
            self.logger.debug(f"Failed to extract from surface geometry: {e}")
            return None
    
    def _extract_from_building_element(self, element, space_guid: str, space_name: str) -> Optional[Polygon2D]:
        """Extract polygon from building element geometry."""
        try:
            if hasattr(element, 'Representation') and element.Representation:
                # Try to use ifcopenshell.geom to extract element geometry
                settings = ifcopenshell.geom.settings()
                settings.set(settings.USE_WORLD_COORDS, True)
                
                try:
                    shape = ifcopenshell.geom.create_shape(settings, element)
                    if shape:
                        return self.convert_to_2d_coordinates(shape.geometry, space_guid, space_name)
                except Exception as e:
                    self.logger.debug(f"Failed to create shape for element: {e}")
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Failed to extract from building element: {e}")
            return None
    
    def _create_simple_boundary_polygon(self, space_guid: str, space_name: str) -> Optional[Polygon2D]:
        """Create a simple boundary polygon as fallback - DISABLED to avoid duplicates."""
        # This method is disabled to prevent creating too many duplicate fallback geometries
        return None
    
    def _extract_space_geometry_enhanced(self, ifc_space, space_guid: str, space_name: str) -> Optional[Polygon2D]:
        """Extract geometry directly from IFC space entity with enhanced processing."""
        try:
            # Method 1: Try ifcopenshell.geom with different settings
            polygon = self._extract_with_ifcopenshell_geom(ifc_space, space_guid, space_name)
            if polygon:
                return polygon
            
            # Method 2: Try to extract from space representation items
            polygon = self._extract_from_representation_items(ifc_space, space_guid, space_name)
            if polygon:
                return polygon
            
            # Method 3: Extract from space quantities and create geometric approximation
            polygon = self._extract_from_space_quantities(ifc_space, space_guid, space_name)
            if polygon:
                return polygon
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Failed to extract enhanced space geometry: {e}")
            return None
    
    def _extract_with_ifcopenshell_geom(self, ifc_space, space_guid: str, space_name: str) -> Optional[Polygon2D]:
        """Extract geometry using ifcopenshell.geom with multiple settings."""
        try:
            # Try different geometry settings with more comprehensive options
            settings_configs = [
                {"USE_WORLD_COORDS": True, "WELD_VERTICES": True, "USE_BREP_DATA": True},
                {"USE_WORLD_COORDS": True, "WELD_VERTICES": False, "USE_BREP_DATA": True},
                {"USE_WORLD_COORDS": False, "WELD_VERTICES": True, "USE_BREP_DATA": False},
                {"USE_WORLD_COORDS": True, "WELD_VERTICES": True, "USE_BREP_DATA": False},
            ]
            
            for config in settings_configs:
                try:
                    settings = ifcopenshell.geom.settings()
                    for key, value in config.items():
                        if hasattr(settings, key):
                            settings.set(getattr(settings, key), value)
                    
                    shape = ifcopenshell.geom.create_shape(settings, ifc_space)
                    if shape and shape.geometry:
                        polygon = self.convert_to_2d_coordinates(shape.geometry, space_guid, space_name)
                        if polygon and self._validate_polygon(polygon):
                            # Check if this is a meaningful geometry (not just a fallback-like rectangle)
                            area = polygon.get_area()
                            bounds = polygon.get_bounds()
                            width = bounds[2] - bounds[0]
                            height = bounds[3] - bounds[1]
                            
                            # Skip if it looks like a generic template (dimensions now in meters)
                            if not (abs(width - 13.7) < 0.1 and abs(height - 5.6) < 0.1 and abs(area - 77.7) < 0.1):
                                self.logger.debug(f"Successfully extracted geometry with config: {config} (area: {area:.1f} m², dims: {width:.1f}x{height:.1f}m)")
                                return polygon
                        
                except Exception as e:
                    self.logger.debug(f"Failed with config {config}: {e}")
                    continue
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Failed ifcopenshell geometry extraction: {e}")
            return None
    
    def _extract_from_representation_items(self, ifc_space, space_guid: str, space_name: str) -> Optional[Polygon2D]:
        """Extract geometry from space representation items."""
        try:
            if not (hasattr(ifc_space, 'Representation') and ifc_space.Representation):
                return None
            
            representation = ifc_space.Representation
            if not hasattr(representation, 'Representations'):
                return None
            
            for rep in representation.Representations:
                if hasattr(rep, 'Items'):
                    for item in rep.Items:
                        try:
                            polygon = self._process_representation_item(item, space_guid, space_name)
                            if polygon and self._validate_polygon(polygon):
                                return polygon
                        except Exception as e:
                            self.logger.debug(f"Failed to process representation item: {e}")
                            continue
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Failed to extract from representation items: {e}")
            return None
    
    def _process_representation_item(self, item, space_guid: str, space_name: str) -> Optional[Polygon2D]:
        """Process individual representation item to extract geometry."""
        try:
            # Handle different types of representation items
            if item.is_a("IfcExtrudedAreaSolid"):
                return self._extract_from_extruded_area_solid(item, space_guid, space_name)
            elif item.is_a("IfcFacetedBrep"):
                return self._extract_from_faceted_brep(item, space_guid, space_name)
            elif item.is_a("IfcPolygonalBoundedHalfSpace"):
                return self._extract_from_polygonal_bounded_halfspace(item, space_guid, space_name)
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Failed to process representation item: {e}")
            return None
    
    def _extract_from_extruded_area_solid(self, item, space_guid: str, space_name: str) -> Optional[Polygon2D]:
        """Extract 2D polygon from extruded area solid."""
        try:
            if hasattr(item, 'SweptArea') and item.SweptArea:
                swept_area = item.SweptArea
                if swept_area.is_a("IfcRectangleProfileDef"):
                    return self._extract_from_rectangle_profile(swept_area, space_guid, space_name)
                elif swept_area.is_a("IfcArbitraryClosedProfileDef"):
                    return self._extract_from_arbitrary_profile(swept_area, space_guid, space_name)
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Failed to extract from extruded area solid: {e}")
            return None
    
    def _extract_from_rectangle_profile(self, profile, space_guid: str, space_name: str) -> Optional[Polygon2D]:
        """Extract polygon from rectangle profile definition."""
        try:
            if hasattr(profile, 'XDim') and hasattr(profile, 'YDim'):
                x_dim = float(profile.XDim)
                y_dim = float(profile.YDim)
                
                # Create rectangle centered at origin
                half_x = x_dim / 2
                half_y = y_dim / 2
                
                points = [
                    Point2D(-half_x, -half_y),
                    Point2D(half_x, -half_y),
                    Point2D(half_x, half_y),
                    Point2D(-half_x, half_y),
                    Point2D(-half_x, -half_y)
                ]
                
                return Polygon2D(points, space_guid, space_name)
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Failed to extract from rectangle profile: {e}")
            return None
    
    def _extract_from_arbitrary_profile(self, profile, space_guid: str, space_name: str) -> Optional[Polygon2D]:
        """Extract polygon from arbitrary closed profile definition."""
        try:
            # This would require detailed curve processing
            # For now, return None to use fallback methods
            return None
            
        except Exception as e:
            self.logger.debug(f"Failed to extract from arbitrary profile: {e}")
            return None
    
    def _extract_from_faceted_brep(self, item, space_guid: str, space_name: str) -> Optional[Polygon2D]:
        """Extract polygon from faceted boundary representation."""
        try:
            # This would require complex B-rep processing
            # For now, return None to use fallback methods
            return None
            
        except Exception as e:
            self.logger.debug(f"Failed to extract from faceted brep: {e}")
            return None
    
    def _extract_from_polygonal_bounded_halfspace(self, item, space_guid: str, space_name: str) -> Optional[Polygon2D]:
        """Extract polygon from polygonal bounded half space."""
        try:
            # This would require half-space intersection processing
            # For now, return None to use fallback methods
            return None
            
        except Exception as e:
            self.logger.debug(f"Failed to extract from polygonal bounded halfspace: {e}")
            return None
    
    def _extract_from_space_quantities(self, ifc_space, space_guid: str, space_name: str) -> Optional[Polygon2D]:
        """Extract geometry approximation from space quantities."""
        try:
            area = None
            perimeter = None
            height = None
            
            # Extract quantities from property definitions
            if hasattr(ifc_space, 'IsDefinedBy'):
                for definition in ifc_space.IsDefinedBy:
                    if hasattr(definition, 'RelatingPropertyDefinition'):
                        prop_def = definition.RelatingPropertyDefinition
                        if prop_def.is_a("IfcElementQuantity"):
                            for quantity in prop_def.Quantities:
                                if quantity.is_a("IfcQuantityArea"):
                                    if quantity.Name in ["NetFloorArea", "GrossFloorArea", "Area"]:
                                        area = float(quantity.AreaValue)
                                elif quantity.is_a("IfcQuantityLength"):
                                    if quantity.Name in ["Perimeter", "NetPerimeter"]:
                                        perimeter = float(quantity.LengthValue)
                                    elif quantity.Name in ["Height", "NetHeight"]:
                                        height = float(quantity.LengthValue)
            
            # Create geometry based on available quantities
            if area is not None:
                if perimeter is not None:
                    # Try to create a more accurate shape based on area and perimeter
                    return self._create_polygon_from_area_perimeter(area, perimeter, space_guid, space_name)
                else:
                    # Create square based on area
                    side_length = math.sqrt(area)
                    return self._create_square_polygon(side_length, space_guid, space_name)
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Failed to extract from space quantities: {e}")
            return None

    def _create_polygon_from_area_perimeter(self, area: float, perimeter: float, space_guid: str, space_name: str) -> Optional[Polygon2D]:
        """Create polygon approximation from area and perimeter."""
        try:
            # Assume rectangular shape and solve for dimensions
            # For rectangle: area = w * h, perimeter = 2 * (w + h)
            # Solving: h = (perimeter/2) - w, area = w * ((perimeter/2) - w)
            # This gives: w^2 - (perimeter/2)*w + area = 0
            
            p_half = perimeter / 2
            discriminant = (p_half ** 2) - (4 * area)
            
            if discriminant >= 0:
                sqrt_discriminant = math.sqrt(discriminant)
                w1 = (p_half + sqrt_discriminant) / 2
                w2 = (p_half - sqrt_discriminant) / 2
                
                # Use the larger dimension as width
                width = max(w1, w2)
                height = area / width
                
                if width > 0 and height > 0:
                    points = [
                        Point2D(0, 0),
                        Point2D(width, 0),
                        Point2D(width, height),
                        Point2D(0, height),
                        Point2D(0, 0)
                    ]
                    
                    return Polygon2D(points, space_guid, space_name)
            
            # Fallback to square if calculation fails
            return self._create_square_polygon(math.sqrt(area), space_guid, space_name)
            
        except Exception as e:
            self.logger.debug(f"Failed to create polygon from area/perimeter: {e}")
            return None
    
    def _create_square_polygon(self, side_length: float, space_guid: str, space_name: str) -> Optional[Polygon2D]:
        """Create a square polygon with given side length."""
        try:
            if side_length <= 0:
                side_length = 5.0  # Default 5m x 5m
            
            points = [
                Point2D(0, 0),
                Point2D(side_length, 0),
                Point2D(side_length, side_length),
                Point2D(0, side_length),
                Point2D(0, 0)
            ]
            
            return Polygon2D(points, space_guid, space_name)
            
        except Exception as e:
            self.logger.debug(f"Failed to create square polygon: {e}")
            return None
    
    def _extract_geometry_from_related_elements(self, ifc_space, space_guid: str, space_name: str) -> Optional[Polygon2D]:
        """Extract geometry from elements related to the space."""
        try:
            # Look for elements that bound or define the space
            related_elements = []
            
            # Check for elements contained in the same spatial structure
            if hasattr(ifc_space, 'Decomposes'):
                for rel in ifc_space.Decomposes:
                    if hasattr(rel, 'RelatingObject'):
                        spatial_element = rel.RelatingObject
                        # Find other elements in the same spatial structure
                        related_elements.extend(self._get_elements_in_spatial_structure(spatial_element))
            
            # Try to create boundary from surrounding walls
            if related_elements:
                return self._create_boundary_from_walls(related_elements, space_guid, space_name)
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Failed to extract geometry from related elements: {e}")
            return None
    
    def _get_elements_in_spatial_structure(self, spatial_element) -> List[Any]:
        """Get building elements in a spatial structure."""
        try:
            elements = []
            ifc_file = spatial_element.file
            
            for rel in ifc_file.by_type("IfcRelContainedInSpatialStructure"):
                if hasattr(rel, 'RelatingStructure') and rel.RelatingStructure == spatial_element:
                    if hasattr(rel, 'RelatedElements'):
                        elements.extend(rel.RelatedElements)
            
            return elements
            
        except Exception as e:
            self.logger.debug(f"Failed to get elements in spatial structure: {e}")
            return []
    
    def _extract_polygon_with_ifcopenshell(self, ifc_space, space_guid: str, space_name: str) -> Optional[Polygon2D]:
        """Extract 2D polygon using IfcOpenShell geometry processing."""
        try:
            # Create geometry settings for 2D extraction
            settings = ifcopenshell.geom.settings()
            settings.set(settings.USE_WORLD_COORDS, True)
            settings.set(settings.INCLUDE_CURVES, True)
            
            # Extract 3D geometry
            shape = ifcopenshell.geom.create_shape(settings, ifc_space)
            if not shape:
                return None
            
            geometry = shape.geometry
            if not hasattr(geometry, 'verts') or not geometry.verts:
                return None
            
            # Get vertices (they come as flat array: x1,y1,z1,x2,y2,z2,...)
            verts = geometry.verts
            vertices_3d = []
            
            for i in range(0, len(verts), 3):
                x, y, z = verts[i], verts[i+1], verts[i+2]
                vertices_3d.append((x, y, z))
            
            if len(vertices_3d) < 3:
                return None
            
            # Convert to 2D by projecting to XY plane and finding boundary
            points_2d = [(x, y) for x, y, z in vertices_3d]
            
            # Remove duplicate points
            unique_points = []
            tolerance = 0.001  # 1mm tolerance
            
            for point in points_2d:
                is_duplicate = False
                for existing in unique_points:
                    if abs(point[0] - existing[0]) < tolerance and abs(point[1] - existing[1]) < tolerance:
                        is_duplicate = True
                        break
                if not is_duplicate:
                    unique_points.append(point)
            
            if len(unique_points) < 3:
                return None
            
            # Find convex hull or boundary of the points
            boundary_points = self._find_2d_boundary(unique_points)
            
            if len(boundary_points) < 3:
                return None
            
            # Convert to Point2D objects (coordinates might be in meters already)
            polygon_points = []
            for x, y in boundary_points:
                # Check if coordinates seem to be in mm (very large values) or meters (reasonable values)
                if abs(x) > 1000 or abs(y) > 1000:
                    # Likely in mm, convert to meters
                    polygon_points.append(Point2D(x / 1000.0, y / 1000.0))
                else:
                    # Likely already in meters
                    polygon_points.append(Point2D(x, y))
            
            # Close the polygon if not already closed
            if len(polygon_points) > 0:
                first_point = polygon_points[0]
                last_point = polygon_points[-1]
                if abs(first_point.x - last_point.x) > 0.001 or abs(first_point.y - last_point.y) > 0.001:
                    polygon_points.append(Point2D(first_point.x, first_point.y))
            
            return Polygon2D(polygon_points, space_guid, space_name)
            
        except Exception as e:
            self.logger.debug(f"IfcOpenShell polygon extraction failed: {e}")
            return None
    
    def _find_2d_boundary(self, points: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """Find the boundary/convex hull of 2D points."""
        try:
            if len(points) < 3:
                return points
            
            # Simple convex hull algorithm (Graham scan)
            def cross_product(o, a, b):
                return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
            
            # Sort points lexicographically
            points = sorted(set(points))
            if len(points) <= 1:
                return points
            
            # Build lower hull
            lower = []
            for p in points:
                while len(lower) >= 2 and cross_product(lower[-2], lower[-1], p) <= 0:
                    lower.pop()
                lower.append(p)
            
            # Build upper hull
            upper = []
            for p in reversed(points):
                while len(upper) >= 2 and cross_product(upper[-2], upper[-1], p) <= 0:
                    upper.pop()
                upper.append(p)
            
            # Remove last point of each half because it's repeated
            return lower[:-1] + upper[:-1]
            
        except Exception as e:
            self.logger.debug(f"Boundary finding failed: {e}")
            return points

    def _create_boundary_from_walls(self, elements, space_guid: str, space_name: str) -> Optional[Polygon2D]:
        """Create space boundary from surrounding wall elements."""
        try:
            # This would require complex geometric analysis of wall positions
            # For now, return None to use fallback methods
            return None
            
        except Exception as e:
            self.logger.debug(f"Failed to create boundary from walls: {e}")
            return None
    
    def _generate_fallback_geometry(self, ifc_space, space_guid: str, space_name: str) -> Optional[Polygon2D]:
        """Generate fallback geometry when all other methods fail. Coordinates in meters."""
        try:
            self.logger.debug(f"Generating fallback geometry for space {space_name}")
            
            # Use default dimensions based on space type or name (in square meters)
            default_area = self._estimate_area_from_space_info(ifc_space)
            
            # Create more varied shapes based on space type
            import hashlib
            hash_value = int(hashlib.md5(space_guid.encode()).hexdigest()[:8], 16)
            
            # Create a grid layout with appropriate spacing for meters
            grid_size = 8.0  # 8 meters between grid points
            grid_x = (hash_value % 20) * grid_size  # 20x20 grid
            grid_y = ((hash_value // 20) % 20) * grid_size
            
            # Add consistent offset based on GUID to spread out rooms
            import random
            random.seed(hash_value)
            offset_x = grid_x + random.uniform(0, 2)
            offset_y = grid_y + random.uniform(0, 2)
            
            # Create varied room shapes based on area and hash
            if default_area < 10:  # Small rooms - more square
                width = math.sqrt(default_area) + random.uniform(-0.5, 0.5)
                height = default_area / width if width > 0 else default_area
            elif default_area < 25:  # Medium rooms - rectangular
                aspect_ratio = 1.2 + random.uniform(-0.3, 0.3)
                width = math.sqrt(default_area * aspect_ratio)
                height = default_area / width if width > 0 else default_area
            else:  # Large rooms - more varied shapes
                aspect_ratio = 1.5 + random.uniform(-0.5, 0.8)
                width = math.sqrt(default_area * aspect_ratio)
                height = default_area / width if width > 0 else default_area
            
            # Ensure minimum dimensions (in meters)
            width = max(1.5, width)
            height = max(1.5, height)
            
            points = [
                Point2D(offset_x, offset_y),
                Point2D(offset_x + width, offset_y),
                Point2D(offset_x + width, offset_y + height),
                Point2D(offset_x, offset_y + height),
                Point2D(offset_x, offset_y)
            ]
            
            return Polygon2D(points, space_guid, space_name)
            
        except Exception as e:
            self.logger.debug(f"Failed to generate fallback geometry: {e}")
            return None
    
    def _estimate_area_from_space_info(self, ifc_space) -> float:
        """Estimate space area from space information."""
        try:
            # Try to get space type or function
            space_type = None
            
            if hasattr(ifc_space, 'ObjectType') and ifc_space.ObjectType:
                space_type = ifc_space.ObjectType.lower()
            elif hasattr(ifc_space, 'Name') and ifc_space.Name:
                space_name = ifc_space.Name.lower()
                # Guess space type from name
                if any(keyword in space_name for keyword in ['office', 'kontor']):
                    space_type = 'office'
                elif any(keyword in space_name for keyword in ['meeting', 'møte']):
                    space_type = 'meeting'
                elif any(keyword in space_name for keyword in ['corridor', 'gang']):
                    space_type = 'corridor'
                elif any(keyword in space_name for keyword in ['toilet', 'wc']):
                    space_type = 'toilet'
            
            # Return estimated area based on space type
            area_estimates = {
                'office': 15.0,      # 15 m²
                'meeting': 25.0,     # 25 m²
                'corridor': 10.0,    # 10 m²
                'toilet': 4.0,       # 4 m²
                'storage': 8.0,      # 8 m²
                'technical': 12.0,   # 12 m²
            }
            
            return area_estimates.get(space_type, 20.0)  # Default 20 m²
            
        except Exception as e:
            self.logger.debug(f"Failed to estimate area from space info: {e}")
            return 20.0  # Default area
    
    def _merge_space_polygons(self, polygons: List[Polygon2D], space_guid: str) -> Optional[Polygon2D]:
        """Merge multiple polygons for the same space into one representative polygon."""
        try:
            if not polygons:
                return None
            
            if len(polygons) == 1:
                return polygons[0]
            
            # For now, use the largest polygon as the representative
            # In the future, this could be enhanced to actually merge geometries
            largest_polygon = max(polygons, key=lambda p: p.get_area())
            
            self.logger.debug(f"Merged {len(polygons)} polygons for space {space_guid}, using largest ({largest_polygon.get_area():.1f} m²)")
            return largest_polygon
            
        except Exception as e:
            self.logger.debug(f"Failed to merge polygons for space {space_guid}: {e}")
            return polygons[0] if polygons else None
    
    def _merge_space_polygons(self, polygons: List[Polygon2D], space_guid: str) -> Optional[Polygon2D]:
        """
        Merge multiple polygons for the same space into a single representative polygon.
        
        Args:
            polygons: List of polygons for the same space
            space_guid: GUID of the space
            
        Returns:
            Merged polygon or None if merging fails
        """
        try:
            if not polygons:
                return None
            
            if len(polygons) == 1:
                return polygons[0]
            
            # For now, use the largest polygon as the representative
            # In the future, this could be enhanced to actually merge geometries
            largest_polygon = max(polygons, key=lambda p: p.get_area())
            
            self.logger.debug(f"Merged {len(polygons)} polygons for space {space_guid}, using largest ({largest_polygon.get_area():.1f} m²)")
            return largest_polygon
            
        except Exception as e:
            self.logger.debug(f"Failed to merge polygons for space {space_guid}: {e}")
            return polygons[0] if polygons else None

    def _validate_polygon(self, polygon: Polygon2D) -> bool:
        """Validate that a polygon is suitable for floor plan display."""
        try:
            if not polygon or not polygon.points:
                return False
            
            # Check minimum number of points
            if len(polygon.points) < 4:  # At least 3 points + closing point
                return False
            
            # Check for reasonable area (in square meters)
            area = polygon.get_area()
            if area < 0.5 or area > 10000:  # Between 0.5 m² and 10,000 m²
                self.logger.debug(f"Polygon area {area:.2f} m² is outside reasonable range")
                return False
            
            # Check for reasonable bounds (in meters)
            bounds = polygon.get_bounds()
            width = bounds[2] - bounds[0]
            height = bounds[3] - bounds[1]
            
            if width < 0.5 or height < 0.5 or width > 500 or height > 500:
                self.logger.debug(f"Polygon dimensions {width:.2f}x{height:.2f} m are outside reasonable range")
                return False
            
            # Check for valid coordinates (no NaN or infinite values)
            for point in polygon.points:
                if (math.isnan(point.x) or math.isnan(point.y) or 
                    math.isinf(point.x) or math.isinf(point.y)):
                    self.logger.debug("Polygon contains invalid coordinates")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.debug(f"Failed to validate polygon: {e}")
            return False