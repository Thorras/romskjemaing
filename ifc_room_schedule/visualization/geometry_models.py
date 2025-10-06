"""
Geometric Data Models for 2D Floor Plan Visualization

This module defines the core data structures for representing 2D geometric
data extracted from IFC files for floor plan visualization.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Dict, Any
import math


@dataclass
class Point2D:
    """Represents a 2D point with x, y coordinates."""
    
    x: float
    y: float
    
    def __post_init__(self):
        """Validate point coordinates."""
        if not isinstance(self.x, (int, float)) or not isinstance(self.y, (int, float)):
            raise ValueError("Point coordinates must be numeric")
        if math.isnan(self.x) or math.isnan(self.y):
            raise ValueError("Point coordinates cannot be NaN")
        if math.isinf(self.x) or math.isinf(self.y):
            raise ValueError("Point coordinates cannot be infinite")
    
    def distance_to(self, other: 'Point2D') -> float:
        """Calculate Euclidean distance to another point."""
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)
    
    def translate(self, dx: float, dy: float) -> 'Point2D':
        """Return a new point translated by dx, dy."""
        return Point2D(self.x + dx, self.y + dy)
    
    def scale(self, factor: float, origin: Optional['Point2D'] = None) -> 'Point2D':
        """Return a new point scaled by factor around origin."""
        if origin is None:
            origin = Point2D(0, 0)
        
        dx = self.x - origin.x
        dy = self.y - origin.y
        
        return Point2D(
            origin.x + dx * factor,
            origin.y + dy * factor
        )
    
    def to_tuple(self) -> Tuple[float, float]:
        """Convert to tuple representation."""
        return (self.x, self.y)
    
    def __str__(self) -> str:
        return f"Point2D({self.x:.2f}, {self.y:.2f})"


@dataclass
class Polygon2D:
    """Represents a 2D polygon with associated space information."""
    
    points: List[Point2D]
    space_guid: str
    space_name: str
    
    def __post_init__(self):
        """Validate polygon data."""
        if not self.points:
            raise ValueError("Polygon must have at least one point")
        
        if len(self.points) < 3:
            raise ValueError("Polygon must have at least 3 points")
        
        if not self.space_guid:
            raise ValueError("Polygon must have a valid space GUID")
        
        if not self.space_name:
            self.space_name = f"Space {self.space_guid[:8]}"
        
        # Ensure polygon is closed
        if len(self.points) > 2 and self.points[0].to_tuple() != self.points[-1].to_tuple():
            self.points.append(self.points[0])
    
    def get_bounds(self) -> Tuple[float, float, float, float]:
        """Get bounding box as (min_x, min_y, max_x, max_y)."""
        if not self.points:
            return (0, 0, 0, 0)
        
        x_coords = [p.x for p in self.points]
        y_coords = [p.y for p in self.points]
        
        return (
            min(x_coords),
            min(y_coords),
            max(x_coords),
            max(y_coords)
        )
    
    def get_centroid(self) -> Point2D:
        """Calculate polygon centroid using the shoelace formula."""
        if len(self.points) < 3:
            # For degenerate cases, return average of points
            avg_x = sum(p.x for p in self.points) / len(self.points)
            avg_y = sum(p.y for p in self.points) / len(self.points)
            return Point2D(avg_x, avg_y)
        
        # Use shoelace formula for polygon centroid
        area = 0.0
        cx = 0.0
        cy = 0.0
        
        for i in range(len(self.points) - 1):
            p1 = self.points[i]
            p2 = self.points[i + 1]
            
            cross = p1.x * p2.y - p2.x * p1.y
            area += cross
            cx += (p1.x + p2.x) * cross
            cy += (p1.y + p2.y) * cross
        
        area *= 0.5
        
        if abs(area) < 1e-10:  # Very small area, use simple average
            avg_x = sum(p.x for p in self.points) / len(self.points)
            avg_y = sum(p.y for p in self.points) / len(self.points)
            return Point2D(avg_x, avg_y)
        
        cx /= (6.0 * area)
        cy /= (6.0 * area)
        
        return Point2D(cx, cy)
    
    def get_area(self) -> float:
        """Calculate polygon area using the shoelace formula."""
        if len(self.points) < 3:
            return 0.0
        
        area = 0.0
        for i in range(len(self.points) - 1):
            p1 = self.points[i]
            p2 = self.points[i + 1]
            area += p1.x * p2.y - p2.x * p1.y
        
        return abs(area) * 0.5
    
    def contains_point(self, point: Point2D) -> bool:
        """Check if point is inside polygon using ray casting algorithm."""
        if len(self.points) < 3:
            return False
        
        x, y = point.x, point.y
        inside = False
        
        j = len(self.points) - 2  # Skip the duplicate closing point
        for i in range(len(self.points) - 1):
            xi, yi = self.points[i].x, self.points[i].y
            xj, yj = self.points[j].x, self.points[j].y
            
            if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
                inside = not inside
            
            j = i
        
        return inside
    
    def translate(self, dx: float, dy: float) -> 'Polygon2D':
        """Return a new polygon translated by dx, dy."""
        translated_points = [p.translate(dx, dy) for p in self.points]
        return Polygon2D(translated_points, self.space_guid, self.space_name)
    
    def scale(self, factor: float, origin: Optional[Point2D] = None) -> 'Polygon2D':
        """Return a new polygon scaled by factor around origin."""
        if origin is None:
            origin = self.get_centroid()
        
        scaled_points = [p.scale(factor, origin) for p in self.points]
        return Polygon2D(scaled_points, self.space_guid, self.space_name)
    
    def to_tuples(self) -> List[Tuple[float, float]]:
        """Convert points to list of tuples."""
        return [p.to_tuple() for p in self.points]
    
    def __str__(self) -> str:
        return f"Polygon2D({self.space_name}, {len(self.points)} points)"


@dataclass
class FloorLevel:
    """Represents a building floor/level with associated spaces."""
    
    id: str
    name: str
    elevation: float
    spaces: List[str] = field(default_factory=list)  # space GUIDs
    
    def __post_init__(self):
        """Validate floor level data."""
        if not self.id:
            raise ValueError("Floor level must have a valid ID")
        
        if not self.name:
            self.name = f"Level {self.id}"
        
        if not isinstance(self.elevation, (int, float)):
            raise ValueError("Floor elevation must be numeric")
        
        if math.isnan(self.elevation) or math.isinf(self.elevation):
            raise ValueError("Floor elevation must be a finite number")
        
        # Remove duplicates from spaces list
        self.spaces = list(dict.fromkeys(self.spaces))
    
    def add_space(self, space_guid: str) -> None:
        """Add a space GUID to this floor level."""
        if space_guid and space_guid not in self.spaces:
            self.spaces.append(space_guid)
    
    def remove_space(self, space_guid: str) -> None:
        """Remove a space GUID from this floor level."""
        if space_guid in self.spaces:
            self.spaces.remove(space_guid)
    
    def get_space_count(self) -> int:
        """Get the number of spaces on this floor."""
        return len(self.spaces)
    
    def __str__(self) -> str:
        return f"FloorLevel({self.name}, {self.get_space_count()} spaces)"


@dataclass
class FloorGeometry:
    """Complete geometric data for a building floor."""
    
    level: FloorLevel
    room_polygons: List[Polygon2D] = field(default_factory=list)
    building_outline: Optional[Polygon2D] = None
    bounds: Optional[Tuple[float, float, float, float]] = None
    
    def __post_init__(self):
        """Calculate bounds and validate data."""
        if not self.level:
            raise ValueError("FloorGeometry must have a valid FloorLevel")
        
        # Calculate bounds from room polygons if not provided
        if self.bounds is None:
            self.bounds = self._calculate_bounds()
        
        # Validate that room polygons match floor spaces
        polygon_guids = {p.space_guid for p in self.room_polygons}
        floor_spaces = set(self.level.spaces)
        
        # Add any missing spaces to the floor level
        for guid in polygon_guids:
            if guid not in floor_spaces:
                self.level.add_space(guid)
    
    def _calculate_bounds(self) -> Tuple[float, float, float, float]:
        """Calculate bounding box from all room polygons."""
        if not self.room_polygons:
            return (0, 0, 0, 0)
        
        all_bounds = [polygon.get_bounds() for polygon in self.room_polygons]
        
        min_x = min(bounds[0] for bounds in all_bounds)
        min_y = min(bounds[1] for bounds in all_bounds)
        max_x = max(bounds[2] for bounds in all_bounds)
        max_y = max(bounds[3] for bounds in all_bounds)
        
        return (min_x, min_y, max_x, max_y)
    
    def get_room_by_guid(self, space_guid: str) -> Optional[Polygon2D]:
        """Get room polygon by space GUID."""
        for polygon in self.room_polygons:
            if polygon.space_guid == space_guid:
                return polygon
        return None
    
    def get_rooms_by_guids(self, space_guids: List[str]) -> List[Polygon2D]:
        """Get multiple room polygons by space GUIDs."""
        return [
            polygon for polygon in self.room_polygons
            if polygon.space_guid in space_guids
        ]
    
    def find_room_at_point(self, point: Point2D) -> Optional[Polygon2D]:
        """Find room polygon containing the given point."""
        for polygon in self.room_polygons:
            if polygon.contains_point(point):
                return polygon
        return None
    
    def get_total_area(self) -> float:
        """Calculate total area of all rooms on this floor."""
        return sum(polygon.get_area() for polygon in self.room_polygons)
    
    def get_room_count(self) -> int:
        """Get the number of rooms with geometry on this floor."""
        return len(self.room_polygons)
    
    def get_bounds_width(self) -> float:
        """Get the width of the floor bounds."""
        if not self.bounds:
            return 0.0
        return self.bounds[2] - self.bounds[0]
    
    def get_bounds_height(self) -> float:
        """Get the height of the floor bounds."""
        if not self.bounds:
            return 0.0
        return self.bounds[3] - self.bounds[1]
    
    def get_bounds_center(self) -> Point2D:
        """Get the center point of the floor bounds."""
        if not self.bounds:
            return Point2D(0, 0)
        
        center_x = (self.bounds[0] + self.bounds[2]) / 2
        center_y = (self.bounds[1] + self.bounds[3]) / 2
        
        return Point2D(center_x, center_y)
    
    def __str__(self) -> str:
        return f"FloorGeometry({self.level.name}, {self.get_room_count()} rooms)"


@dataclass
class FloorPlanState:
    """Represents the current state of the floor plan interface."""
    
    current_floor_id: Optional[str] = None
    selected_rooms: List[str] = field(default_factory=list)
    view_bounds: Optional[Tuple[float, float, float, float]] = None
    zoom_level: float = 1.0
    available_floors: List[FloorLevel] = field(default_factory=list)
    geometry_data: Dict[str, FloorGeometry] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate state data."""
        if self.zoom_level <= 0:
            self.zoom_level = 1.0
        
        # Remove duplicates from selected rooms
        self.selected_rooms = list(dict.fromkeys(self.selected_rooms))
    
    def add_floor(self, floor_geometry: FloorGeometry) -> None:
        """Add floor geometry data to the state."""
        floor_id = floor_geometry.level.id
        self.geometry_data[floor_id] = floor_geometry
        
        # Add to available floors if not already present
        if not any(floor.id == floor_id for floor in self.available_floors):
            self.available_floors.append(floor_geometry.level)
    
    def get_current_floor_geometry(self) -> Optional[FloorGeometry]:
        """Get geometry data for the current floor."""
        if self.current_floor_id and self.current_floor_id in self.geometry_data:
            return self.geometry_data[self.current_floor_id]
        return None
    
    def set_current_floor(self, floor_id: str) -> bool:
        """Set the current floor if it exists in available floors."""
        if floor_id in self.geometry_data:
            self.current_floor_id = floor_id
            return True
        return False
    
    def add_room_to_selection(self, room_guid: str) -> None:
        """Add a room to the current selection."""
        if room_guid and room_guid not in self.selected_rooms:
            self.selected_rooms.append(room_guid)
    
    def remove_room_from_selection(self, room_guid: str) -> None:
        """Remove a room from the current selection."""
        if room_guid in self.selected_rooms:
            self.selected_rooms.remove(room_guid)
    
    def clear_selection(self) -> None:
        """Clear all selected rooms."""
        self.selected_rooms.clear()
    
    def is_room_selected(self, room_guid: str) -> bool:
        """Check if a room is currently selected."""
        return room_guid in self.selected_rooms
    
    def get_selected_room_count(self) -> int:
        """Get the number of currently selected rooms."""
        return len(self.selected_rooms)
    
    def __str__(self) -> str:
        floor_count = len(self.available_floors)
        selected_count = len(self.selected_rooms)
        return f"FloorPlanState({floor_count} floors, {selected_count} selected)"