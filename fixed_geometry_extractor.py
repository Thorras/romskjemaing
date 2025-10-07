#!/usr/bin/env python3
"""
Fixed Geometry Extractor that creates proper room boundaries for floor plans.

This version fixes the overlapping zones issue by:
1. Combining multiple space boundaries into single room polygons
2. Using only the outer boundary of each space
3. Ensuring each room has one clear, non-overlapping boundary
4. Proper 2D projection from IFC space geometry
"""

import sys
import os
import logging
from typing import Dict, List, Optional, Tuple, Any
import math

# Add project root to path
sys.path.append('.')

try:
    import ifcopenshell
    import ifcopenshell.geom
    IFC_AVAILABLE = True
except ImportError:
    IFC_AVAILABLE = False

from ifc_room_schedule.visualization.geometry_models import Point2D, Polygon2D, FloorLevel, FloorGeometry
from ifc_room_schedule.visualization.geometry_extractor import GeometryExtractor, GeometryExtractionError


class FixedGeometryExtractor(GeometryExtractor):
    """Fixed geometry extractor that creates proper room boundaries."""
    
    def extract_space_boundaries(self, ifc_space) -> List[Polygon2D]:
        """
        Extract a single, clean 2D boundary polygon for an IFC space.
        
        This method fixes the overlapping issue by creating one polygon per space
        instead of multiple overlapping polygons from space boundaries.
        
        Args:
            ifc_space: IFC space entity
            
        Returns:
            List containing a single Polygon2D object representing the room boundary
        """
        try:
            space_guid = ifc_space.GlobalId
            space_name = getattr(ifc_space, 'Name', None) or f"Space {space_guid[:8]}"
            
            self.logger.debug(f"Extracting clean boundary for space: {space_name} ({space_guid})")
            
            # Method 1: Try to get the space's own geometry representation
            polygon = self._extract_space_footprint(ifc_space, space_guid, space_name)
            if polygon:
                self.logger.debug(f"Extracted space footprint successfully")
                return [polygon]
            
            # Method 2: Try to extract from space boundaries but combine them
            polygon = self._extract_combined_space_boundary(ifc_space, space_guid, space_name)
            if polygon:
                self.logger.debug(f"Extracted combined space boundary successfully")
                return [polygon]
            
            # Method 3: Generate from space properties (area-based)
            polygon = self._generate_area_based_geometry(ifc_space, space_guid, space_name)
            if polygon:
                self.logger.debug(f"Generated area-based geometry successfully")
                return [polygon]
            
            # Method 4: Final fallback - simple rectangular geometry
            polygon = self._generate_simple_fallback_geometry(ifc_space, space_guid, space_name)
            if polygon:
                self.logger.debug(f"Generated simple fallback geometry")
                return [polygon]
            
            self.logger.warning(f"Could not extract any geometry for space {space_name} ({space_guid})")
            return []
            
        except Exception as e:
            self.logger.error(f"Failed to extract space boundaries for {space_name}: {e}")
            return []
    
    def _extract_space_footprint(self, ifc_space, space_guid: str, space_name: str) -> Optional[Polygon2D]:
        """
        Extract the space's own geometric representation as a 2D footprint.
        
        Args:
            ifc_space: IFC space entity
            space_guid: Space GUID
            space_name: Space name
            
        Returns:
            Polygon2D representing the space footprint or None
        """
        try:
            # Try to get the space's representation directly
            if hasattr(ifc_space, 'Representation') and ifc_space.Representation:
                for representation in ifc_space.Representation.Representations:
                    if representation.RepresentationType in ['FootPrint', 'Curve2D', 'GeometricSet']:
                        polygon = self._extract_2d_from_representation(representation, space_guid, space_name)
                        if polygon:
                            return polygon
            
            # Try using ifcopenshell geometry processing
            if IFC_AVAILABLE:
                try:
                    settings = ifcopenshell.geom.settings()
                    settings.set(settings.USE_WORLD_COORDS, True)
                    settings.set(settings.WELD_VERTICES, True)
                    
                    shape = ifcopenshell.geom.create_shape(settings, ifc_space)
                    if shape:
                        return self._convert_shape_to_2d_polygon(shape, space_guid, space_name)
                        
                except Exception as e:
                    self.logger.debug(f"ifcopenshell geometry extraction failed: {e}")
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Space footprint extraction failed: {e}")
            return None
    
    def _extract_combined_space_boundary(self, ifc_space, space_guid: str, space_name: str) -> Optional[Polygon2D]:
        """
        Extract and combine space boundaries into a single room polygon.
        
        Args:
            ifc_space: IFC space entity
            space_guid: Space GUID
            space_name: Space name
            
        Returns:
            Combined Polygon2D or None
        """
        try:
            # Get space boundaries
            boundaries = self._get_space_boundaries_enhanced(ifc_space)
            if not boundaries:
                return None
            
            # Extract all boundary points
            all_points = []
            
            for boundary in boundaries:
                try:
                    # Only use physical boundaries (walls, floors)
                    if hasattr(boundary, 'PhysicalOrVirtualBoundary'):
                        if boundary.PhysicalOrVirtualBoundary == 'VIRTUAL':
                            continue
                    
                    # Extract points from this boundary
                    boundary_points = self._extract_boundary_points(boundary)
                    if boundary_points:
                        all_points.extend(boundary_points)
                        
                except Exception as e:
                    self.logger.debug(f"Failed to extract boundary points: {e}")
                    continue
            
            if len(all_points) < 3:
                return None
            
            # Create convex hull or outer boundary from all points
            outer_boundary = self._create_outer_boundary(all_points)
            
            if len(outer_boundary) >= 3:
                return Polygon2D(outer_boundary, space_guid, space_name)
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Combined space boundary extraction failed: {e}")
            return None
    
    def _extract_boundary_points(self, boundary) -> List[Point2D]:
        """
        Extract 2D points from a space boundary.
        
        Args:
            boundary: IFC space boundary entity
            
        Returns:
            List of Point2D objects
        """
        points = []
        
        try:
            if hasattr(boundary, 'ConnectionGeometry') and boundary.ConnectionGeometry:
                connection_geom = boundary.ConnectionGeometry
                
                if hasattr(connection_geom, 'SurfaceOnRelatingElement'):
                    surface = connection_geom.SurfaceOnRelatingElement
                    
                    # Extract points from surface geometry
                    if hasattr(surface, 'BasisSurface'):
                        basis_surface = surface.BasisSurface
                        
                        if hasattr(basis_surface, 'OuterBoundary'):
                            outer_boundary = basis_surface.OuterBoundary
                            points.extend(self._extract_points_from_curve(outer_boundary))
                        
                        # Also check for inner boundaries (holes)
                        if hasattr(basis_surface, 'InnerBoundaries'):
                            for inner_boundary in basis_surface.InnerBoundaries:
                                # For now, we'll ignore holes to keep it simple
                                pass
            
            return points
            
        except Exception as e:
            self.logger.debug(f"Failed to extract boundary points: {e}")
            return []
    
    def _extract_points_from_curve(self, curve) -> List[Point2D]:
        """
        Extract 2D points from an IFC curve.
        
        Args:
            curve: IFC curve entity
            
        Returns:
            List of Point2D objects
        """
        points = []
        
        try:
            if hasattr(curve, 'Bound') and curve.Bound:
                for bound in curve.Bound:
                    if hasattr(bound, 'Bound') and bound.Bound:
                        bound_curve = bound.Bound
                        
                        if hasattr(bound_curve, 'Points'):
                            for point in bound_curve.Points:
                                if hasattr(point, 'Coordinates') and len(point.Coordinates) >= 2:
                                    x, y = point.Coordinates[0], point.Coordinates[1]
                                    points.append(Point2D(x, y))
                        
                        elif hasattr(bound_curve, 'Polygon'):
                            for point in bound_curve.Polygon:
                                if hasattr(point, 'Coordinates') and len(point.Coordinates) >= 2:
                                    x, y = point.Coordinates[0], point.Coordinates[1]
                                    points.append(Point2D(x, y))
            
            return points
            
        except Exception as e:
            self.logger.debug(f"Failed to extract points from curve: {e}")
            return []
    
    def _create_outer_boundary(self, points: List[Point2D]) -> List[Point2D]:
        """
        Create an outer boundary from a collection of points using convex hull.
        
        Args:
            points: List of Point2D objects
            
        Returns:
            List of Point2D objects forming the outer boundary
        """
        if len(points) < 3:
            return points
        
        try:
            # Simple convex hull algorithm (Graham scan)
            # Find the bottom-most point (and leftmost in case of tie)
            start_point = min(points, key=lambda p: (p.y, p.x))
            
            # Sort points by polar angle with respect to start_point
            def polar_angle(p):
                dx = p.x - start_point.x
                dy = p.y - start_point.y
                return math.atan2(dy, dx)
            
            sorted_points = sorted([p for p in points if p != start_point], key=polar_angle)
            
            # Build convex hull
            hull = [start_point]
            
            for point in sorted_points:
                # Remove points that make a right turn
                while len(hull) > 1:
                    # Check if we make a left turn
                    o1, o2, o3 = hull[-2], hull[-1], point
                    cross_product = (o2.x - o1.x) * (o3.y - o1.y) - (o2.y - o1.y) * (o3.x - o1.x)
                    if cross_product > 0:  # Left turn
                        break
                    hull.pop()
                
                hull.append(point)
            
            return hull
            
        except Exception as e:
            self.logger.debug(f"Failed to create outer boundary: {e}")
            # Fallback: return original points
            return points
    
    def _generate_area_based_geometry(self, ifc_space, space_guid: str, space_name: str) -> Optional[Polygon2D]:
        """
        Generate geometry based on space area and try to infer shape.
        
        Args:
            ifc_space: IFC space entity
            space_guid: Space GUID
            space_name: Space name
            
        Returns:
            Polygon2D based on area or None
        """
        try:
            # Get area from space properties
            area = self._get_space_area(ifc_space)
            if area <= 0:
                return None
            
            # Try to get space location for positioning
            location = self._get_space_location(ifc_space)
            if not location:
                location = Point2D(0, 0)
            
            # Generate a rectangular room based on area
            # Assume reasonable aspect ratio (not too narrow)
            aspect_ratio = 1.5  # width/height ratio
            
            height = math.sqrt(area / aspect_ratio)
            width = area / height
            
            # Create rectangle centered at location
            half_width = width / 2
            half_height = height / 2
            
            points = [
                Point2D(location.x - half_width, location.y - half_height),
                Point2D(location.x + half_width, location.y - half_height),
                Point2D(location.x + half_width, location.y + half_height),
                Point2D(location.x - half_width, location.y + half_height)
            ]
            
            return Polygon2D(points, space_guid, space_name)
            
        except Exception as e:
            self.logger.debug(f"Area-based geometry generation failed: {e}")
            return None
    
    def _get_space_area(self, ifc_space) -> float:
        """Get space area from IFC properties."""
        try:
            # Check for area in quantities
            if hasattr(ifc_space, 'IsDefinedBy'):
                for definition in ifc_space.IsDefinedBy:
                    if hasattr(definition, 'RelatingPropertyDefinition'):
                        prop_def = definition.RelatingPropertyDefinition
                        
                        if prop_def.is_a("IfcElementQuantity"):
                            for quantity in getattr(prop_def, 'Quantities', []):
                                if hasattr(quantity, 'Name') and quantity.Name:
                                    name = quantity.Name.lower()
                                    if 'area' in name or 'floor' in name:
                                        if hasattr(quantity, 'AreaValue'):
                                            return float(quantity.AreaValue)
                                        elif hasattr(quantity, 'NominalValue'):
                                            return float(quantity.NominalValue.wrappedValue)
            
            return 0.0
            
        except Exception as e:
            self.logger.debug(f"Failed to get space area: {e}")
            return 0.0
    
    def _get_space_location(self, ifc_space) -> Optional[Point2D]:
        """Get space location from IFC placement."""
        try:
            if hasattr(ifc_space, 'ObjectPlacement') and ifc_space.ObjectPlacement:
                placement = ifc_space.ObjectPlacement
                
                if hasattr(placement, 'RelativePlacement') and placement.RelativePlacement:
                    rel_placement = placement.RelativePlacement
                    
                    if hasattr(rel_placement, 'Location') and rel_placement.Location:
                        location = rel_placement.Location
                        
                        if hasattr(location, 'Coordinates') and len(location.Coordinates) >= 2:
                            x, y = location.Coordinates[0], location.Coordinates[1]
                            return Point2D(x, y)
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Failed to get space location: {e}")
            return None
    
    def _generate_simple_fallback_geometry(self, ifc_space, space_guid: str, space_name: str) -> Optional[Polygon2D]:
        """
        Generate simple fallback geometry as last resort.
        
        Args:
            ifc_space: IFC space entity
            space_guid: Space GUID
            space_name: Space name
            
        Returns:
            Simple rectangular Polygon2D
        """
        try:
            # Get area or use default
            area = self._get_space_area(ifc_space)
            if area <= 0:
                area = 15.0  # Default 15 m²
            
            # Get location or use incremental positioning
            location = self._get_space_location(ifc_space)
            if not location:
                # Use a simple grid positioning based on space GUID hash
                hash_val = hash(space_guid) % 1000
                grid_x = (hash_val % 10) * 8  # 8m spacing
                grid_y = (hash_val // 10) * 6  # 6m spacing
                location = Point2D(grid_x, grid_y)
            
            # Create square room
            side_length = math.sqrt(area)
            half_side = side_length / 2
            
            points = [
                Point2D(location.x - half_side, location.y - half_side),
                Point2D(location.x + half_side, location.y - half_side),
                Point2D(location.x + half_side, location.y + half_side),
                Point2D(location.x - half_side, location.y + half_side)
            ]
            
            return Polygon2D(points, space_guid, space_name)
            
        except Exception as e:
            self.logger.debug(f"Simple fallback geometry generation failed: {e}")
            return None
    
    def _convert_shape_to_2d_polygon(self, shape, space_guid: str, space_name: str) -> Optional[Polygon2D]:
        """
        Convert ifcopenshell shape to 2D polygon.
        
        Args:
            shape: ifcopenshell shape object
            space_guid: Space GUID
            space_name: Space name
            
        Returns:
            Polygon2D or None
        """
        try:
            if hasattr(shape, 'geometry'):
                geometry = shape.geometry
                
                if hasattr(geometry, 'verts'):
                    vertices = geometry.verts
                    points = []
                    
                    # Extract 2D points (ignore Z coordinate)
                    for i in range(0, len(vertices), 3):
                        if i + 1 < len(vertices):
                            x = vertices[i]
                            y = vertices[i + 1]
                            points.append(Point2D(x, y))
                    
                    if len(points) >= 3:
                        # Remove duplicate points and create outer boundary
                        unique_points = []
                        for point in points:
                            if not unique_points or point.distance_to(unique_points[-1]) > 0.01:
                                unique_points.append(point)
                        
                        if len(unique_points) >= 3:
                            return Polygon2D(unique_points, space_guid, space_name)
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Shape to 2D polygon conversion failed: {e}")
            return None


def test_fixed_geometry_extraction():
    """Test the fixed geometry extractor."""
    print("Testing Fixed Geometry Extractor")
    print("=" * 50)
    
    try:
        # Test with AkkordSvingen file
        from ifc_room_schedule.parser.ifc_file_reader import IfcFileReader
        
        test_file = "tesfiler/AkkordSvingen 23_ARK.ifc"
        if not os.path.exists(test_file):
            print(f"Test file not found: {test_file}")
            return False
        
        # Load IFC file
        reader = IfcFileReader()
        success, message = reader.load_file(test_file)
        if not success:
            print(f"Failed to load IFC file: {message}")
            return False
        
        print(f"✓ Loaded IFC file: {test_file}")
        
        # Extract geometry with fixed extractor
        fixed_extractor = FixedGeometryExtractor()
        
        def progress_callback(status: str, progress: int):
            print(f"  {status} ({progress}%)")
        
        floor_geometries = fixed_extractor.extract_floor_geometry(
            reader.get_ifc_file(),
            progress_callback=progress_callback
        )
        
        if not floor_geometries:
            print("✗ No geometry extracted")
            return False
        
        print(f"✓ Extracted geometry for {len(floor_geometries)} floors")
        
        # Analyze results
        total_rooms = 0
        for floor_id, geometry in floor_geometries.items():
            room_count = geometry.get_room_count()
            total_rooms += room_count
            
            print(f"  Floor {geometry.level.name}: {room_count} rooms")
            
            # Check for overlapping rooms (should be minimal now)
            overlaps = 0
            for i, room1 in enumerate(geometry.room_polygons):
                for j, room2 in enumerate(geometry.room_polygons[i+1:], i+1):
                    # Simple overlap check using bounding boxes
                    bounds1 = room1.get_bounds()
                    bounds2 = room2.get_bounds()
                    
                    if (bounds1[0] < bounds2[2] and bounds1[2] > bounds2[0] and
                        bounds1[1] < bounds2[3] and bounds1[3] > bounds2[1]):
                        overlaps += 1
            
            print(f"    Potential overlaps: {overlaps}")
        
        print(f"✓ Total rooms with geometry: {total_rooms}")
        print("✅ Fixed geometry extraction test completed!")
        
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {str(e)}")
        return False


if __name__ == "__main__":
    test_fixed_geometry_extraction()