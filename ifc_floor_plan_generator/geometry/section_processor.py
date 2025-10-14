"""
Section processor for IFC Floor Plan Generator.

Implements horizontal section cutting and 2D polyline generation using OpenCASCADE.
"""

import logging
from typing import List, Tuple, Optional, Any

from ..dependencies.occ_wrapper import (
    HAS_OCC, require_occ, OCCDependencyError,
    gp_Pln, gp_Pnt, gp_Dir, gp_Ax3,
    TopoDS_Shape, TopoDS_Edge, TopoDS_Compound,
    BRepAlgoAPI_Section,
    BRep_Tool, BRep_Builder,
    TopExp_Explorer, TopAbs_EDGE, TopAbs_VERTEX,
    BRepAdaptor_Curve,
    GCPnts_UniformAbscissa,
    GeomAbs_Line, GeomAbs_Circle, GeomAbs_BSplineCurve,
    TopoDS
)
from ..models import Polyline2D
from ..errors.handler import ErrorHandler
from ..errors.exceptions import ProcessingError, EmptyCutResultError


class SectionProcessor:
    """Processes horizontal sections and converts to 2D polylines."""
    
    def __init__(self, slice_tolerance: float = 1e-6, chain_tolerance: float = 1e-3):
        """Initialize section processor with tolerances.
        
        Args:
            slice_tolerance: Tolerance for section plane operations
            chain_tolerance: Tolerance for polyline chaining (used in task 6.2)
        """
        self.slice_tolerance = slice_tolerance
        self.chain_tolerance = chain_tolerance
        self._logger = logging.getLogger(__name__)
        self._error_handler = ErrorHandler()
        
        # Check OCC availability and warn if not available
        if not HAS_OCC:
            self._logger.warning(
                "OpenCASCADE not available - section processing will be limited. "
                "Install with: conda install -c conda-forge opencascade"
            )
    
    def create_section_plane(self, z_height: float) -> gp_Pln:
        """Create horizontal section plane at specified height.
        
        Args:
            z_height: Height (Z-coordinate) for the horizontal section plane
            
        Returns:
            gp_Pln: OpenCASCADE plane object for the horizontal section
        """
        try:
            # Create a horizontal plane at the specified Z height
            # The plane is defined by a point on the plane and a normal vector
            plane_point = gp_Pnt(0.0, 0.0, z_height)
            plane_normal = gp_Dir(0.0, 0.0, 1.0)  # Z-axis (upward)
            
            # Create coordinate system for the plane
            plane_axis = gp_Ax3(plane_point, plane_normal)
            
            # Create the plane
            section_plane = gp_Pln(plane_axis)
            
            self._logger.debug(f"Created section plane at Z={z_height}")
            return section_plane
            
        except Exception as e:
            self._logger.error(f"Failed to create section plane at Z={z_height}: {e}")
            raise ProcessingError(
                error_code="SECTION_PLANE_FAILED",
                message=f"Kunne ikke lage snittplan på høyde {z_height}m",
                context={"z_height": z_height, "error": str(e)}
            )
    
    def intersect_shape_with_plane(self, shape: TopoDS_Shape, plane: gp_Pln) -> List[TopoDS_Edge]:
        """Intersect 3D shape with section plane to get intersection edges.
        
        Args:
            shape: 3D shape to intersect
            plane: Section plane
            
        Returns:
            List[TopoDS_Edge]: List of intersection edges
            
        Raises:
            ProcessingError: If intersection operation fails
        """
        try:
            # Create section algorithm
            section_algo = BRepAlgoAPI_Section()
            
            # Set the shape and plane for intersection
            section_algo.SetArguments([shape])
            section_algo.SetTools([BRep_Tool.MakeFace(plane)])
            
            # Set tolerance
            section_algo.SetFuzzyValue(self.slice_tolerance)
            
            # Perform the intersection
            section_algo.Build()
            
            if not section_algo.IsDone():
                self._logger.warning("Section algorithm did not complete successfully")
                return []
            
            # Get the result
            result_shape = section_algo.Shape()
            
            if result_shape.IsNull():
                self._logger.debug("Section result is null - no intersection found")
                return []
            
            # Extract edges from the result
            edges = []
            edge_explorer = TopExp_Explorer(result_shape, TopAbs_EDGE)
            
            while edge_explorer.More():
                edge = TopoDS.Edge_s(edge_explorer.Current())
                if not edge.IsNull():
                    edges.append(edge)
                edge_explorer.Next()
            
            self._logger.debug(f"Found {len(edges)} intersection edges")
            return edges
            
        except Exception as e:
            self._logger.error(f"Shape intersection failed: {e}")
            raise ProcessingError(
                error_code="SHAPE_INTERSECTION_FAILED",
                message=f"Snitt-operasjon feilet: {str(e)}",
                context={"error": str(e)}
            )
    
    def edges_to_polylines(self, edges: List[TopoDS_Edge]) -> List[Polyline2D]:
        """Convert intersection edges to 2D polylines.
        
        Args:
            edges: List of intersection edges from section operation
            
        Returns:
            List[Polyline2D]: List of 2D polylines with points projected to XY plane
        """
        if not edges:
            self._logger.debug("No edges to convert to polylines")
            return []
        
        polylines = []
        
        for i, edge in enumerate(edges):
            try:
                points = self._edge_to_points(edge)
                if len(points) >= 2:
                    # Create polyline with placeholder metadata
                    # Real metadata will be added by the calling code
                    polyline = Polyline2D(
                        points=points,
                        ifc_class="Unknown",  # Will be set by caller
                        element_guid=f"edge_{i}",  # Will be set by caller
                        is_closed=self._is_edge_closed(edge)
                    )
                    polylines.append(polyline)
                else:
                    self._logger.debug(f"Edge {i} produced insufficient points ({len(points)})")
                    
            except Exception as e:
                self._logger.warning(f"Failed to convert edge {i} to polyline: {e}")
                continue
        
        self._logger.debug(f"Converted {len(edges)} edges to {len(polylines)} polylines")
        return polylines
    
    def _edge_to_points(self, edge: TopoDS_Edge) -> List[Tuple[float, float]]:
        """Convert a TopoDS_Edge to a list of 2D points.
        
        Args:
            edge: OpenCASCADE edge to convert
            
        Returns:
            List[Tuple[float, float]]: List of (x, y) points
        """
        points = []
        
        try:
            # Create curve adaptor for the edge
            curve_adaptor = BRepAdaptor_Curve(edge)
            curve_type = curve_adaptor.GetType()
            
            # Get parameter range
            first_param = curve_adaptor.FirstParameter()
            last_param = curve_adaptor.LastParameter()
            
            # Determine number of points based on curve type
            if curve_type == GeomAbs_Line:
                # For lines, just use start and end points
                num_points = 2
            elif curve_type == GeomAbs_Circle:
                # For circles, use more points for smooth representation
                num_points = max(8, int(abs(last_param - first_param) * 8 / (2 * 3.14159)))
            else:
                # For other curves (B-splines, etc.), use adaptive sampling
                num_points = max(4, int((last_param - first_param) * 10))
            
            # Generate points along the curve
            if num_points == 2:
                # Just start and end points
                params = [first_param, last_param]
            else:
                # Uniform distribution
                param_step = (last_param - first_param) / (num_points - 1)
                params = [first_param + i * param_step for i in range(num_points)]
            
            # Convert parameters to 3D points, then project to 2D
            for param in params:
                try:
                    point_3d = curve_adaptor.Value(param)
                    # Project to XY plane (ignore Z coordinate)
                    point_2d = (point_3d.X(), point_3d.Y())
                    points.append(point_2d)
                except Exception as e:
                    self._logger.debug(f"Failed to evaluate curve at parameter {param}: {e}")
                    continue
            
            # Remove duplicate consecutive points
            points = self._remove_duplicate_points(points)
            
        except Exception as e:
            self._logger.warning(f"Failed to extract points from edge: {e}")
            # Fallback: try to get just the vertices
            try:
                vertex_explorer = TopExp_Explorer(edge, TopAbs_VERTEX)
                while vertex_explorer.More():
                    vertex = TopoDS.Vertex_s(vertex_explorer.Current())
                    point_3d = BRep_Tool.Pnt(vertex)
                    points.append((point_3d.X(), point_3d.Y()))
                    vertex_explorer.Next()
            except Exception as fallback_error:
                self._logger.error(f"Fallback vertex extraction also failed: {fallback_error}")
        
        return points
    
    def _is_edge_closed(self, edge: TopoDS_Edge) -> bool:
        """Check if an edge represents a closed curve.
        
        Args:
            edge: OpenCASCADE edge to check
            
        Returns:
            bool: True if the edge is closed
        """
        try:
            curve_adaptor = BRepAdaptor_Curve(edge)
            return curve_adaptor.IsClosed()
        except Exception:
            return False
    
    def _remove_duplicate_points(self, points: List[Tuple[float, float]], tolerance: float = 1e-6) -> List[Tuple[float, float]]:
        """Remove consecutive duplicate points from a list.
        
        Args:
            points: List of 2D points
            tolerance: Distance tolerance for considering points as duplicates
            
        Returns:
            List[Tuple[float, float]]: List with duplicates removed
        """
        if len(points) <= 1:
            return points
        
        filtered_points = [points[0]]
        
        for i in range(1, len(points)):
            current_point = points[i]
            last_point = filtered_points[-1]
            
            # Calculate distance between consecutive points
            dx = current_point[0] - last_point[0]
            dy = current_point[1] - last_point[1]
            distance = (dx * dx + dy * dy) ** 0.5
            
            if distance > tolerance:
                filtered_points.append(current_point)
        
        return filtered_points
    
    def process_shape_section(self, shape: TopoDS_Shape, z_height: float, 
                            ifc_class: str = "Unknown", element_guid: str = "unknown") -> List[Polyline2D]:
        """Process a complete shape section operation.
        
        This is a convenience method that combines plane creation, intersection, and polyline conversion.
        
        Args:
            shape: 3D shape to section
            z_height: Height for the horizontal section
            ifc_class: IFC class of the element (for metadata)
            element_guid: GUID of the element (for metadata)
            
        Returns:
            List[Polyline2D]: List of resulting polylines
            
        Raises:
            EmptyCutResultError: If no geometry is produced by the section
        """
        try:
            # Create section plane
            plane = self.create_section_plane(z_height)
            
            # Perform intersection
            edges = self.intersect_shape_with_plane(shape, plane)
            
            if not edges:
                raise EmptyCutResultError(
                    storey_name="unknown",  # Will be set by caller
                    cut_height=z_height
                )
            
            # Convert to polylines
            polylines = self.edges_to_polylines(edges)
            
            # Update metadata for all polylines
            for polyline in polylines:
                polyline.ifc_class = ifc_class
                polyline.element_guid = element_guid
            
            self._logger.debug(f"Processed shape section: {len(polylines)} polylines generated")
            return polylines
            
        except EmptyCutResultError:
            # Re-raise empty cut errors as-is
            raise
        except Exception as e:
            self._logger.error(f"Shape section processing failed: {e}")
            raise ProcessingError(
                error_code="SECTION_PROCESSING_FAILED",
                message=f"Snitt-prosessering feilet: {str(e)}",
                context={
                    "z_height": z_height,
                    "ifc_class": ifc_class,
                    "element_guid": element_guid,
                    "error": str(e)
                }
            )
    
    def chain_polylines(self, polylines: List[Polyline2D], tolerance: float) -> List[Polyline2D]:
        """Chain polylines with specified tolerance.
        
        Connects polylines that have endpoints within the specified tolerance distance.
        Detects and creates closed loops where possible.
        
        Args:
            polylines: List of polylines to chain
            tolerance: Distance tolerance for connecting polylines
            
        Returns:
            List[Polyline2D]: Chained polylines with optimized connections
        """
        if not polylines:
            return []
        
        if len(polylines) == 1:
            return polylines
        
        self._logger.debug(f"Chaining {len(polylines)} polylines with tolerance {tolerance}")
        
        # Create working copies of polylines
        working_polylines = [self._copy_polyline(p) for p in polylines]
        chained_polylines = []
        
        # Process polylines until all are consumed
        while working_polylines:
            # Start a new chain with the first available polyline
            current_chain = working_polylines.pop(0)
            chain_modified = True
            
            # Keep trying to extend the chain until no more connections are found
            while chain_modified and working_polylines:
                chain_modified = False
                
                # Try to connect to the end of the current chain
                for i, candidate in enumerate(working_polylines):
                    connection_result = self._try_connect_polylines(current_chain, candidate, tolerance)
                    
                    if connection_result is not None:
                        current_chain = connection_result
                        working_polylines.pop(i)
                        chain_modified = True
                        break
                
                # If no connection at the end, try connecting to the beginning
                if not chain_modified:
                    for i, candidate in enumerate(working_polylines):
                        connection_result = self._try_connect_polylines(candidate, current_chain, tolerance)
                        
                        if connection_result is not None:
                            current_chain = connection_result
                            working_polylines.pop(i)
                            chain_modified = True
                            break
            
            # Check if the chain can be closed (forms a loop)
            current_chain = self._try_close_polyline(current_chain, tolerance)
            
            chained_polylines.append(current_chain)
        
        self._logger.debug(f"Chaining complete: {len(chained_polylines)} chains created")
        return chained_polylines
    
    def _copy_polyline(self, polyline: Polyline2D) -> Polyline2D:
        """Create a deep copy of a polyline.
        
        Args:
            polyline: Polyline to copy
            
        Returns:
            Polyline2D: Deep copy of the polyline
        """
        return Polyline2D(
            points=polyline.points.copy(),
            ifc_class=polyline.ifc_class,
            element_guid=polyline.element_guid,
            is_closed=polyline.is_closed
        )
    
    def _try_connect_polylines(self, first: Polyline2D, second: Polyline2D, tolerance: float) -> Optional[Polyline2D]:
        """Try to connect two polylines if their endpoints are within tolerance.
        
        Args:
            first: First polyline (will be extended)
            second: Second polyline (will be appended)
            tolerance: Distance tolerance for connection
            
        Returns:
            Optional[Polyline2D]: Connected polyline if connection is possible, None otherwise
        """
        if not first.points or not second.points:
            return None
        
        # Skip if either polyline is already closed
        if first.is_closed or second.is_closed:
            return None
        
        first_end = first.points[-1]
        second_start = second.points[0]
        second_end = second.points[-1]
        first_start = first.points[0]
        
        # Try different connection combinations
        connections = [
            # Connect first.end to second.start
            (first_end, second_start, lambda: first.points + second.points[1:]),
            # Connect first.end to second.end (reverse second)
            (first_end, second_end, lambda: first.points + list(reversed(second.points))[1:]),
        ]
        
        for point1, point2, connect_func in connections:
            distance = self._calculate_distance(point1, point2)
            
            if distance <= tolerance:
                # Create connected polyline
                connected_points = connect_func()
                
                # Remove duplicate points at connection
                connected_points = self._remove_duplicate_points(connected_points, tolerance)
                
                if len(connected_points) >= 2:
                    return Polyline2D(
                        points=connected_points,
                        ifc_class=first.ifc_class,  # Use first polyline's metadata
                        element_guid=first.element_guid,
                        is_closed=False  # Will be determined later
                    )
        
        return None
    
    def _try_close_polyline(self, polyline: Polyline2D, tolerance: float) -> Polyline2D:
        """Try to close a polyline if start and end points are within tolerance.
        
        Args:
            polyline: Polyline to potentially close
            tolerance: Distance tolerance for closing
            
        Returns:
            Polyline2D: Polyline with updated is_closed status
        """
        if polyline.is_closed or len(polyline.points) < 3:
            return polyline
        
        start_point = polyline.points[0]
        end_point = polyline.points[-1]
        
        distance = self._calculate_distance(start_point, end_point)
        
        if distance <= tolerance:
            # Close the polyline by removing the duplicate end point
            closed_points = polyline.points[:-1] if distance < tolerance * 0.1 else polyline.points
            
            return Polyline2D(
                points=closed_points,
                ifc_class=polyline.ifc_class,
                element_guid=polyline.element_guid,
                is_closed=True
            )
        
        return polyline
    
    def _calculate_distance(self, point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
        """Calculate Euclidean distance between two 2D points.
        
        Args:
            point1: First point (x, y)
            point2: Second point (x, y)
            
        Returns:
            float: Distance between the points
        """
        dx = point2[0] - point1[0]
        dy = point2[1] - point1[1]
        return (dx * dx + dy * dy) ** 0.5
    
    def transform_coordinates(self, polylines: List[Polyline2D], invert_y: bool = True, 
                            scale_factor: float = 1.0, offset_x: float = 0.0, 
                            offset_y: float = 0.0) -> List[Polyline2D]:
        """Transform coordinate system for polylines.
        
        Applies coordinate transformations including Y-axis inversion for classic 2D drawing orientation.
        
        Args:
            polylines: List of polylines to transform
            invert_y: Whether to invert Y-axis (for classic 2D drawing orientation)
            scale_factor: Scaling factor to apply to coordinates
            offset_x: X-axis offset to apply
            offset_y: Y-axis offset to apply
            
        Returns:
            List[Polyline2D]: Transformed polylines
        """
        if not polylines:
            return []
        
        transformed_polylines = []
        
        # Calculate bounding box for Y-inversion reference if needed
        y_reference = 0.0
        if invert_y:
            all_y_coords = []
            for polyline in polylines:
                for point in polyline.points:
                    all_y_coords.append(point[1])
            
            if all_y_coords:
                y_reference = (max(all_y_coords) + min(all_y_coords)) / 2
        
        for polyline in polylines:
            transformed_points = []
            
            for x, y in polyline.points:
                # Apply scaling
                new_x = x * scale_factor
                new_y = y * scale_factor
                
                # Apply Y-inversion if requested
                if invert_y:
                    new_y = 2 * y_reference - new_y
                
                # Apply offsets
                new_x += offset_x
                new_y += offset_y
                
                transformed_points.append((new_x, new_y))
            
            transformed_polyline = Polyline2D(
                points=transformed_points,
                ifc_class=polyline.ifc_class,
                element_guid=polyline.element_guid,
                is_closed=polyline.is_closed
            )
            
            transformed_polylines.append(transformed_polyline)
        
        self._logger.debug(f"Transformed {len(polylines)} polylines (invert_y={invert_y}, scale={scale_factor})")
        return transformed_polylines
    
    def optimize_polylines(self, polylines: List[Polyline2D], 
                          simplification_tolerance: float = 1e-3) -> List[Polyline2D]:
        """Optimize polylines by removing redundant points and simplifying geometry.
        
        Args:
            polylines: List of polylines to optimize
            simplification_tolerance: Tolerance for point simplification
            
        Returns:
            List[Polyline2D]: Optimized polylines
        """
        if not polylines:
            return []
        
        optimized_polylines = []
        
        for polyline in polylines:
            # Simplify by removing collinear points
            simplified_points = self._simplify_collinear_points(polyline.points, simplification_tolerance)
            
            # Remove duplicate consecutive points
            simplified_points = self._remove_duplicate_points(simplified_points, simplification_tolerance)
            
            # Only keep polylines with sufficient points
            if len(simplified_points) >= 2:
                optimized_polyline = Polyline2D(
                    points=simplified_points,
                    ifc_class=polyline.ifc_class,
                    element_guid=polyline.element_guid,
                    is_closed=polyline.is_closed
                )
                optimized_polylines.append(optimized_polyline)
        
        self._logger.debug(f"Optimized {len(polylines)} polylines to {len(optimized_polylines)}")
        return optimized_polylines
    
    def _simplify_collinear_points(self, points: List[Tuple[float, float]], 
                                  tolerance: float) -> List[Tuple[float, float]]:
        """Remove collinear points that don't contribute to the shape.
        
        Uses the Douglas-Peucker-like algorithm to remove points that are within
        tolerance distance from the line between their neighbors.
        
        Args:
            points: List of points to simplify
            tolerance: Distance tolerance for considering points collinear
            
        Returns:
            List[Tuple[float, float]]: Simplified points
        """
        if len(points) <= 2:
            return points
        
        simplified = [points[0]]  # Always keep first point
        
        for i in range(1, len(points) - 1):
            prev_point = simplified[-1]
            current_point = points[i]
            next_point = points[i + 1]
            
            # Calculate distance from current point to line between prev and next
            distance = self._point_to_line_distance(current_point, prev_point, next_point)
            
            # Keep point if it's not collinear within tolerance
            if distance > tolerance:
                simplified.append(current_point)
        
        simplified.append(points[-1])  # Always keep last point
        return simplified
    
    def _point_to_line_distance(self, point: Tuple[float, float], 
                               line_start: Tuple[float, float], 
                               line_end: Tuple[float, float]) -> float:
        """Calculate perpendicular distance from point to line segment.
        
        Args:
            point: Point to measure distance from
            line_start: Start point of line segment
            line_end: End point of line segment
            
        Returns:
            float: Perpendicular distance from point to line
        """
        x0, y0 = point
        x1, y1 = line_start
        x2, y2 = line_end
        
        # Calculate line length
        line_length_sq = (x2 - x1) ** 2 + (y2 - y1) ** 2
        
        if line_length_sq == 0:
            # Line is actually a point
            return self._calculate_distance(point, line_start)
        
        # Calculate perpendicular distance using cross product formula
        numerator = abs((y2 - y1) * x0 - (x2 - x1) * y0 + x2 * y1 - y2 * x1)
        distance = numerator / (line_length_sq ** 0.5)
        
        return distance