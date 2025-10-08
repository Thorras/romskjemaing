"""
Floor Plan Canvas for 2D Visualization

Custom Qt widget for rendering 2D floor plans and handling user interactions
including room selection, zoom, and pan functionality.
"""

import logging
import math
from typing import Optional, List, Set, Tuple, Dict, Any
from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore import Qt, QRectF, QPointF, pyqtSignal, QTimer
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QPolygonF, QTransform, QWheelEvent, QMouseEvent, QPaintEvent, QResizeEvent

from .geometry_models import Point2D, Polygon2D, FloorGeometry, FloorLevel


class SpaceColorScheme:
    """NS 3940 compliant color coding for space types."""
    
    # Standard NS 3940 categories with colors
    OFFICE_SPACES = QColor(173, 216, 230)      # Light blue
    MEETING_ROOMS = QColor(144, 238, 144)      # Light green  
    CIRCULATION = QColor(255, 218, 185)        # Peach
    TECHNICAL_SPACES = QColor(221, 160, 221)   # Plum
    STORAGE = QColor(255, 255, 224)            # Light yellow
    SANITARY = QColor(255, 182, 193)           # Light pink
    KITCHEN_DINING = QColor(255, 228, 196)     # Bisque
    EDUCATION = QColor(176, 224, 230)          # Powder blue
    HEALTHCARE = QColor(240, 248, 255)         # Alice blue
    RETAIL = QColor(255, 239, 213)             # Papaya whip
    RESIDENTIAL = QColor(255, 228, 225)        # Misty rose
    INDUSTRIAL = QColor(192, 192, 192)         # Silver
    DEFAULT = QColor(240, 240, 240)            # Light gray
    
    # NS 3940 space type mappings (Norwegian terms)
    SPACE_TYPE_MAPPINGS = {
        # Office spaces
        'kontor': OFFICE_SPACES,
        'office': OFFICE_SPACES,
        'arbeidsrom': OFFICE_SPACES,
        'workspace': OFFICE_SPACES,
        'arbeidsplass': OFFICE_SPACES,
        
        # Meeting rooms
        'møterom': MEETING_ROOMS,
        'meeting': MEETING_ROOMS,
        'konferanse': MEETING_ROOMS,
        'conference': MEETING_ROOMS,
        'seminar': MEETING_ROOMS,
        
        # Circulation
        'gang': CIRCULATION,
        'korridor': CIRCULATION,
        'corridor': CIRCULATION,
        'hall': CIRCULATION,
        'lobby': CIRCULATION,
        'foaje': CIRCULATION,
        'trapp': CIRCULATION,
        'stair': CIRCULATION,
        'heis': CIRCULATION,
        'elevator': CIRCULATION,
        
        # Technical spaces
        'teknisk': TECHNICAL_SPACES,
        'technical': TECHNICAL_SPACES,
        'maskin': TECHNICAL_SPACES,
        'machinery': TECHNICAL_SPACES,
        'ventilasjon': TECHNICAL_SPACES,
        'ventilation': TECHNICAL_SPACES,
        'el': TECHNICAL_SPACES,
        'electrical': TECHNICAL_SPACES,
        
        # Storage
        'lager': STORAGE,
        'storage': STORAGE,
        'arkiv': STORAGE,
        'archive': STORAGE,
        'bod': STORAGE,
        'closet': STORAGE,
        
        # Sanitary
        'toalett': SANITARY,
        'toilet': SANITARY,
        'wc': SANITARY,
        'bad': SANITARY,
        'bathroom': SANITARY,
        'dusj': SANITARY,
        'shower': SANITARY,
        
        # Kitchen/Dining
        'kjøkken': KITCHEN_DINING,
        'kitchen': KITCHEN_DINING,
        'kantina': KITCHEN_DINING,
        'canteen': KITCHEN_DINING,
        'spise': KITCHEN_DINING,
        'dining': KITCHEN_DINING,
        
        # Education
        'klasserom': EDUCATION,
        'classroom': EDUCATION,
        'undervisning': EDUCATION,
        'teaching': EDUCATION,
        'auditorium': EDUCATION,
        'bibliotek': EDUCATION,
        'library': EDUCATION,
        
        # Healthcare
        'behandling': HEALTHCARE,
        'treatment': HEALTHCARE,
        'konsultasjon': HEALTHCARE,
        'consultation': HEALTHCARE,
        'medisin': HEALTHCARE,
        'medical': HEALTHCARE,
        
        # Retail
        'butikk': RETAIL,
        'shop': RETAIL,
        'retail': RETAIL,
        'salg': RETAIL,
        'sales': RETAIL,
        
        # Residential
        'bolig': RESIDENTIAL,
        'residential': RESIDENTIAL,
        'leilighet': RESIDENTIAL,
        'apartment': RESIDENTIAL,
        'soverom': RESIDENTIAL,
        'bedroom': RESIDENTIAL,
        'stue': RESIDENTIAL,
        'living': RESIDENTIAL,
        
        # Industrial
        'produksjon': INDUSTRIAL,
        'production': INDUSTRIAL,
        'industri': INDUSTRIAL,
        'industrial': INDUSTRIAL,
        'verksted': INDUSTRIAL,
        'workshop': INDUSTRIAL,
    }
    
    @classmethod
    def get_color_for_space_type(cls, space_type: str) -> QColor:
        """
        Get color for a space type based on NS 3940 standards.
        
        Args:
            space_type: Space type string (Norwegian or English)
            
        Returns:
            QColor for the space type
        """
        if not space_type:
            return cls.DEFAULT
        
        # Normalize space type for lookup
        normalized_type = space_type.lower().strip()
        
        # Direct lookup
        if normalized_type in cls.SPACE_TYPE_MAPPINGS:
            return cls.SPACE_TYPE_MAPPINGS[normalized_type]
        
        # Partial matching for compound space names
        for key, color in cls.SPACE_TYPE_MAPPINGS.items():
            if key in normalized_type or normalized_type in key:
                return color
        
        return cls.DEFAULT
    
    @classmethod
    def get_color_for_space_name(cls, space_name: str) -> QColor:
        """
        Get color for a space based on its name.
        
        Args:
            space_name: Space name string
            
        Returns:
            QColor for the space
        """
        return cls.get_color_for_space_type(space_name)
    
    @classmethod
    def get_all_colors(cls) -> Dict[str, QColor]:
        """Get all available colors with their category names."""
        return {
            'Office Spaces': cls.OFFICE_SPACES,
            'Meeting Rooms': cls.MEETING_ROOMS,
            'Circulation': cls.CIRCULATION,
            'Technical Spaces': cls.TECHNICAL_SPACES,
            'Storage': cls.STORAGE,
            'Sanitary': cls.SANITARY,
            'Kitchen/Dining': cls.KITCHEN_DINING,
            'Education': cls.EDUCATION,
            'Healthcare': cls.HEALTHCARE,
            'Retail': cls.RETAIL,
            'Residential': cls.RESIDENTIAL,
            'Industrial': cls.INDUSTRIAL,
            'Default': cls.DEFAULT,
        }


class FloorPlanCanvas(QWidget):
    """Custom widget for rendering and interacting with 2D floor plans."""
    
    # Signals
    room_clicked = pyqtSignal(str, bool)  # room_guid, ctrl_pressed
    rooms_selection_changed = pyqtSignal(list)  # selected room GUIDs
    view_changed = pyqtSignal(QRectF)  # visible area
    floor_bounds_changed = pyqtSignal(QRectF)  # floor bounds changed
    
    # Visual constants
    ROOM_BORDER_WIDTH = 1
    ROOM_SELECTED_WIDTH = 3
    ROOM_HOVER_WIDTH = 2
    
    # Enhanced visual feedback constants
    SELECTION_GLOW_WIDTH = 5
    HOVER_GLOW_WIDTH = 3
    
    # Colors
    COLOR_BACKGROUND = QColor(250, 250, 250)
    COLOR_ROOM_BORDER = QColor(100, 100, 100)
    COLOR_ROOM_FILL = QColor(240, 240, 240, 100)
    COLOR_ROOM_SELECTED = QColor(0, 120, 215)
    COLOR_ROOM_HOVER = QColor(0, 120, 215, 100)
    COLOR_ROOM_TEXT = QColor(50, 50, 50)
    COLOR_NO_GEOMETRY = QColor(200, 200, 200, 150)
    
    # Enhanced selection colors
    COLOR_SELECTION_GLOW = QColor(0, 120, 215, 80)
    COLOR_HOVER_GLOW = QColor(0, 120, 215, 40)
    COLOR_SELECTION_BORDER = QColor(0, 120, 215, 255)
    COLOR_HOVER_BORDER = QColor(0, 120, 215, 150)
    
    def __init__(self, parent=None):
        """Initialize the floor plan canvas."""
        super().__init__(parent)
        
        self.logger = logging.getLogger(__name__)
        
        # Multi-floor data
        self.floor_geometries: Dict[str, FloorGeometry] = {}  # floor_id -> FloorGeometry
        self.current_floor_id: Optional[str] = None
        self.floor_metadata: Dict[str, Dict[str, Any]] = {}  # floor_id -> metadata
        
        # Current floor data (for backward compatibility)
        self.floor_geometry: Optional[FloorGeometry] = None
        
        # View state
        self.view_transform = QTransform()
        self.zoom_level = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 10.0
        self.pan_offset = QPointF(0, 0)
        
        # Floor-aware bounds management
        self.floor_bounds_cache: Dict[str, Tuple[float, float, float, float]] = {}
        
        # Selection state
        self.selected_rooms: Set[str] = set()
        self.hovered_room: Optional[str] = None
        
        # Interaction state
        self.is_panning = False
        self.last_pan_point = QPointF()
        
        # Enhanced labeling and visual feedback
        self.show_room_labels = True
        self.show_room_numbers = True
        self.label_min_zoom = 0.3  # Minimum zoom level to show labels
        self.detailed_label_min_zoom = 0.8  # Minimum zoom for detailed labels
        self.label_font_size = 10
        
        # Color scheme support
        self.use_color_coding = True
        self.space_color_scheme: Dict[str, QColor] = {}  # space_guid -> color
        
        # Performance optimization
        self.visible_rooms: List[Polygon2D] = []
        self.room_lookup = {}  # GUID -> Polygon2D mapping
        
        # Setup widget
        self.setMinimumSize(400, 300)
        self.setMouseTracking(True)  # Enable hover events
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
        # Update timer for smooth interactions
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self.update)
        
        self.logger.info("FloorPlanCanvas initialized")
    
    def set_floor_geometries(self, floor_geometries: Dict[str, FloorGeometry]) -> None:
        """
        Set multiple floor geometry data for multi-floor support.
        
        Args:
            floor_geometries: Dictionary mapping floor_id to FloorGeometry objects
        """
        self.floor_geometries = floor_geometries.copy()
        
        # Update floor bounds cache
        self.floor_bounds_cache.clear()
        for floor_id, geometry in self.floor_geometries.items():
            if geometry.bounds:
                self.floor_bounds_cache[floor_id] = geometry.bounds
        
        # Set current floor to first available if none set
        if self.floor_geometries and not self.current_floor_id:
            self.current_floor_id = next(iter(self.floor_geometries.keys()))
            self._update_current_floor_display()
        
        self.logger.info(f"Set geometries for {len(floor_geometries)} floors")
    
    def set_current_floor(self, floor_id: str) -> bool:
        """
        Set the current floor to display.
        
        Args:
            floor_id: ID of the floor to display
            
        Returns:
            True if floor was set successfully, False if floor not found
        """
        if floor_id not in self.floor_geometries:
            self.logger.warning(f"Floor {floor_id} not found in available geometries")
            return False
        
        if self.current_floor_id != floor_id:
            self.current_floor_id = floor_id
            self._update_current_floor_display()
            
            # Emit floor bounds changed signal
            if floor_id in self.floor_bounds_cache:
                bounds = self.floor_bounds_cache[floor_id]
                bounds_rect = QRectF(bounds[0], bounds[1], bounds[2] - bounds[0], bounds[3] - bounds[1])
                self.floor_bounds_changed.emit(bounds_rect)
            
            self.logger.info(f"Current floor set to: {floor_id}")
        
        return True
    
    def get_current_floor_id(self) -> Optional[str]:
        """Get the ID of the currently displayed floor."""
        return self.current_floor_id
    
    def get_available_floors(self) -> List[str]:
        """Get list of available floor IDs."""
        return list(self.floor_geometries.keys())
    
    def get_floor_metadata(self, floor_id: str) -> Dict[str, Any]:
        """
        Get metadata for a specific floor.
        
        Args:
            floor_id: ID of the floor
            
        Returns:
            Dictionary containing floor metadata
        """
        if floor_id not in self.floor_metadata:
            # Generate default metadata from geometry
            if floor_id in self.floor_geometries:
                geometry = self.floor_geometries[floor_id]
                self.floor_metadata[floor_id] = {
                    'name': geometry.level.name,
                    'elevation': geometry.level.elevation,
                    'space_count': len(geometry.level.spaces),
                    'room_count': geometry.get_room_count(),
                    'total_area': geometry.get_total_area(),
                    'has_geometry': geometry.get_room_count() > 0
                }
        
        return self.floor_metadata.get(floor_id, {})
    
    def set_floor_metadata(self, floor_id: str, metadata: Dict[str, Any]) -> None:
        """
        Set metadata for a specific floor.
        
        Args:
            floor_id: ID of the floor
            metadata: Dictionary containing floor metadata
        """
        self.floor_metadata[floor_id] = metadata.copy()
    
    def set_space_color_scheme(self, color_scheme: Dict[str, QColor]) -> None:
        """
        Set custom color scheme for spaces.
        
        Args:
            color_scheme: Dictionary mapping space_guid to QColor
        """
        self.space_color_scheme = color_scheme.copy()
        self.update()
        self.logger.debug(f"Custom color scheme set for {len(color_scheme)} spaces")
    
    def enable_ns3940_color_coding(self, enabled: bool = True) -> None:
        """
        Enable or disable NS 3940 color coding.
        
        Args:
            enabled: Whether to enable color coding
        """
        self.use_color_coding = enabled
        if enabled:
            self._update_color_scheme_for_current_floor()
        else:
            self.space_color_scheme.clear()
        self.update()
        self.logger.debug(f"NS 3940 color coding {'enabled' if enabled else 'disabled'}")
    
    def _update_color_scheme_for_current_floor(self) -> None:
        """Update color scheme for spaces on the current floor."""
        if not self.floor_geometry or not self.use_color_coding:
            return
        
        # Generate colors for all spaces on current floor
        for polygon in self.floor_geometry.room_polygons:
            if polygon.space_guid not in self.space_color_scheme:
                # Use space name to determine color
                color = SpaceColorScheme.get_color_for_space_name(polygon.space_name)
                self.space_color_scheme[polygon.space_guid] = color
        
        self.logger.debug(f"Updated color scheme for {len(self.floor_geometry.room_polygons)} spaces")
    
    def get_space_color(self, space_guid: str) -> QColor:
        """
        Get color for a specific space.
        
        Args:
            space_guid: GUID of the space
            
        Returns:
            QColor for the space
        """
        if space_guid in self.space_color_scheme:
            return self.space_color_scheme[space_guid]
        
        # Fallback to default color
        return SpaceColorScheme.DEFAULT
    
    def set_label_visibility(self, show_labels: bool, show_numbers: bool = True) -> None:
        """
        Control visibility of space labels and numbers.
        
        Args:
            show_labels: Whether to show space name labels
            show_numbers: Whether to show room numbers
        """
        self.show_room_labels = show_labels
        self.show_room_numbers = show_numbers
        self.update()
        self.logger.debug(f"Label visibility: labels={show_labels}, numbers={show_numbers}")
    
    def set_label_zoom_thresholds(self, min_zoom: float = 0.3, detailed_zoom: float = 0.8) -> None:
        """
        Set zoom level thresholds for label visibility.
        
        Args:
            min_zoom: Minimum zoom level to show any labels
            detailed_zoom: Minimum zoom level to show detailed labels
        """
        self.label_min_zoom = max(0.1, min_zoom)
        self.detailed_label_min_zoom = max(min_zoom, detailed_zoom)
        self.update()
        self.logger.debug(f"Label zoom thresholds: min={self.label_min_zoom}, detailed={self.detailed_label_min_zoom}")
    
    def set_label_font_size(self, font_size: int) -> None:
        """
        Set the font size for space labels.
        
        Args:
            font_size: Font size in points
        """
        self.label_font_size = max(6, min(font_size, 24))
        self.update()
        self.logger.debug(f"Label font size set to: {self.label_font_size}")
    
    def _should_show_labels(self) -> bool:
        """Check if labels should be shown at current zoom level."""
        return (self.show_room_labels or self.show_room_numbers) and self.zoom_level >= self.label_min_zoom
    
    def _should_show_detailed_labels(self) -> bool:
        """Check if detailed labels should be shown at current zoom level."""
        return self.zoom_level >= self.detailed_label_min_zoom
    
    def _get_space_label_text(self, polygon: Polygon2D, detailed: bool = False) -> str:
        """
        Get appropriate label text for a space polygon.
        
        Args:
            polygon: Space polygon
            detailed: Whether to show detailed information
            
        Returns:
            Label text string
        """
        parts = []
        
        # Add room number if available and enabled
        if self.show_room_numbers and hasattr(polygon, 'room_number') and polygon.room_number:
            parts.append(str(polygon.room_number))
        
        # Add space name if available and enabled
        if self.show_room_labels and polygon.space_name and polygon.space_name.strip():
            name = polygon.space_name.strip()
            if name and name != "Unknown Space":
                if detailed:
                    parts.append(name)
                else:
                    # Truncate long names for non-detailed view
                    if len(name) > 15:
                        name = name[:12] + "..."
                    parts.append(name)
        
        # Fallback to truncated GUID if no other info
        if not parts:
            parts.append(polygon.space_guid[:8])
        
        return "\n".join(parts)
    
    def _get_label_font(self) -> QFont:
        """Get font for labels based on current zoom level."""
        # Adjust font size based on zoom level
        adjusted_size = max(6, int(self.label_font_size / max(0.5, self.zoom_level)))
        font = QFont("Arial", adjusted_size)
        
        # Make font bold for better visibility at small sizes
        if adjusted_size <= 8:
            font.setBold(True)
        
        return font
    
    def _update_current_floor_display(self) -> None:
        """Update the display to show the current floor."""
        if self.current_floor_id and self.current_floor_id in self.floor_geometries:
            # Set the current floor geometry for backward compatibility
            self.floor_geometry = self.floor_geometries[self.current_floor_id]
            
            # Update room lookup for current floor
            self.room_lookup = {
                polygon.space_guid: polygon 
                for polygon in self.floor_geometry.room_polygons
            }
            
            # Clear selection if selected rooms are not on current floor
            current_room_guids = set(self.room_lookup.keys())
            self.selected_rooms = self.selected_rooms.intersection(current_room_guids)
            
            # Update color scheme for new floor
            if self.use_color_coding:
                self._update_color_scheme_for_current_floor()
            
            # Reset view to fit new floor
            self.zoom_to_fit()
            
            self.logger.debug(f"Updated display for floor: {self.current_floor_id}")
        else:
            # No current floor or geometry
            self.floor_geometry = None
            self.room_lookup.clear()
            self.selected_rooms.clear()
            
        self.update()
    
    def get_floor_bounds(self, floor_id: Optional[str] = None) -> Optional[Tuple[float, float, float, float]]:
        """
        Get bounds for a specific floor or current floor.
        
        Args:
            floor_id: ID of the floor, or None for current floor
            
        Returns:
            Bounds tuple (min_x, min_y, max_x, max_y) or None if not available
        """
        target_floor = floor_id or self.current_floor_id
        
        if target_floor and target_floor in self.floor_bounds_cache:
            return self.floor_bounds_cache[target_floor]
        
        return None
    
    def set_floor_geometry(self, geometry: FloorGeometry) -> None:
        """
        Set the floor geometry data to display (backward compatibility method).
        
        Args:
            geometry: FloorGeometry object containing room polygons
        """
        if geometry:
            # Add to multi-floor system
            floor_id = geometry.level.id
            self.floor_geometries[floor_id] = geometry
            self.current_floor_id = floor_id
            
            # Update bounds cache
            if geometry.bounds:
                self.floor_bounds_cache[floor_id] = geometry.bounds
            
            # Set for backward compatibility
            self.floor_geometry = geometry
            
            # Build room lookup for fast access
            self.room_lookup = {
                polygon.space_guid: polygon 
                for polygon in geometry.room_polygons
            }
            
            # Update color scheme
            if self.use_color_coding:
                self._update_color_scheme_for_current_floor()
            
            # Reset view to fit new geometry
            self.zoom_to_fit()
            
            self.logger.info(f"Floor geometry set: {geometry.get_room_count()} rooms")
        else:
            # Clear all data
            self.floor_geometry = None
            self.floor_geometries.clear()
            self.current_floor_id = None
            self.floor_bounds_cache.clear()
            self.room_lookup.clear()
            self.visible_rooms.clear()
            
        self.update()
    
    def highlight_rooms(self, room_guids: List[str]) -> None:
        """
        Highlight specific rooms by their GUIDs.
        
        Args:
            room_guids: List of room GUIDs to highlight
        """
        old_selection = self.selected_rooms.copy()
        self.selected_rooms = set(room_guids)
        
        if old_selection != self.selected_rooms:
            self.rooms_selection_changed.emit(list(self.selected_rooms))
            self.update()
            
            self.logger.debug(f"Room selection changed: {len(self.selected_rooms)} rooms selected")
    
    def clear_selection(self) -> None:
        """Clear all room selections."""
        if self.selected_rooms:
            self.selected_rooms.clear()
            self.rooms_selection_changed.emit([])
            self.update()
            
            self.logger.debug("Room selection cleared")
    
    def zoom_to_fit(self) -> None:
        """Zoom and pan to fit all room geometry in the view with improved handling."""
        self.logger.debug("Starting zoom_to_fit")
        
        # Get bounds for current floor
        bounds = self.get_floor_bounds()
        if not bounds:
            # If no bounds available, try to calculate from visible rooms
            if self.floor_geometry and self.floor_geometry.room_polygons:
                all_bounds = [polygon.get_bounds() for polygon in self.floor_geometry.room_polygons]
                if all_bounds:
                    min_x = min(b[0] for b in all_bounds)
                    min_y = min(b[1] for b in all_bounds)
                    max_x = max(b[2] for b in all_bounds)
                    max_y = max(b[3] for b in all_bounds)
                    bounds = (min_x, min_y, max_x, max_y)
                    self.logger.debug(f"Calculated bounds from polygons: {bounds}")
        
        if not bounds:
            self.logger.warning("No bounds available for zoom_to_fit")
            return
        
        # Get geometry bounds
        min_x, min_y, max_x, max_y = bounds
        self.logger.debug(f"Original bounds: ({min_x:.1f}, {min_y:.1f}, {max_x:.1f}, {max_y:.1f})")
        
        # Add padding around the geometry
        padding = max(2.0, (max_x - min_x) * 0.15, (max_y - min_y) * 0.15)
        min_x -= padding
        min_y -= padding
        max_x += padding
        max_y += padding
        
        geometry_width = max_x - min_x
        geometry_height = max_y - min_y
        
        if geometry_width <= 0 or geometry_height <= 0:
            self.logger.warning(f"Invalid geometry dimensions: {geometry_width} x {geometry_height}")
            return
        
        # Calculate required zoom to fit geometry
        widget_width = self.width() - 60  # More margin
        widget_height = self.height() - 60
        
        zoom_x = widget_width / geometry_width if geometry_width > 0 else 1.0
        zoom_y = widget_height / geometry_height if geometry_height > 0 else 1.0
        
        # Use smaller zoom to fit both dimensions, but ensure minimum visibility
        self.zoom_level = min(zoom_x, zoom_y, self.max_zoom)
        self.zoom_level = max(self.zoom_level, self.min_zoom)
        
        # Ensure reasonable zoom level
        if self.zoom_level < 0.01:
            self.zoom_level = 0.1
        elif self.zoom_level > 100:
            self.zoom_level = 10.0
        
        # Center the geometry
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        
        widget_center_x = self.width() / 2
        widget_center_y = self.height() / 2
        
        self.pan_offset = QPointF(
            widget_center_x - center_x * self.zoom_level,
            widget_center_y - center_y * self.zoom_level
        )
        
        self._update_view_transform()
        self.update()
        
        self.logger.info(f"Zoomed to fit: zoom={self.zoom_level:.2f}, bounds=({min_x:.1f},{min_y:.1f},{max_x:.1f},{max_y:.1f}), center=({center_x:.1f},{center_y:.1f})")
    
    def zoom_to_rooms(self, room_guids: List[str]) -> None:
        """
        Zoom and pan to focus on specific rooms.
        
        Args:
            room_guids: List of room GUIDs to focus on
        """
        if not room_guids or not self.floor_geometry:
            return
        
        # Find bounds of selected rooms
        room_polygons = [
            self.room_lookup[guid] for guid in room_guids 
            if guid in self.room_lookup
        ]
        
        if not room_polygons:
            return
        
        # Calculate combined bounds
        all_bounds = [polygon.get_bounds() for polygon in room_polygons]
        
        min_x = min(bounds[0] for bounds in all_bounds)
        min_y = min(bounds[1] for bounds in all_bounds)
        max_x = max(bounds[2] for bounds in all_bounds)
        max_y = max(bounds[3] for bounds in all_bounds)
        
        # Add some padding
        padding = 2.0
        min_x -= padding
        min_y -= padding
        max_x += padding
        max_y += padding
        
        # Calculate zoom and pan similar to zoom_to_fit
        widget_width = self.width() - 40
        widget_height = self.height() - 40
        
        geometry_width = max_x - min_x
        geometry_height = max_y - min_y
        
        if geometry_width > 0 and geometry_height > 0:
            zoom_x = widget_width / geometry_width
            zoom_y = widget_height / geometry_height
            
            self.zoom_level = min(zoom_x, zoom_y, self.max_zoom)
            self.zoom_level = max(self.zoom_level, self.min_zoom)
            
            # Center on selected rooms
            center_x = (min_x + max_x) / 2
            center_y = (min_y + max_y) / 2
            
            widget_center_x = self.width() / 2
            widget_center_y = self.height() / 2
            
            self.pan_offset = QPointF(
                widget_center_x - center_x * self.zoom_level,
                widget_center_y - center_y * self.zoom_level
            )
            
            self._update_view_transform()
            self.update()
            
            self.logger.debug(f"Zoomed to {len(room_guids)} rooms")
    
    def get_room_at_point(self, widget_point: QPointF) -> Optional[str]:
        """
        Find room GUID at the given widget coordinate.
        
        Args:
            widget_point: Point in widget coordinates
            
        Returns:
            Room GUID if found, None otherwise
        """
        if not self.floor_geometry:
            return None
        
        # Transform widget point to floor plan coordinates
        floor_point = self._widget_to_floor_coordinates(widget_point)
        
        # Check each room polygon
        for polygon in self.floor_geometry.room_polygons:
            if polygon.contains_point(floor_point):
                return polygon.space_guid
        
        return None
    
    def paintEvent(self, event: QPaintEvent) -> None:
        """Handle paint events to render the floor plan."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Clear background
        painter.fillRect(self.rect(), self.COLOR_BACKGROUND)
        
        self.logger.debug(f"Paint event - widget size: {self.width()}x{self.height()}")
        
        if not self.floor_geometry:
            self._draw_no_data_message(painter)
            return
        
        self.logger.debug(f"Drawing floor with {len(self.floor_geometry.room_polygons)} rooms")
        
        # Set up coordinate transformation
        painter.setTransform(self.view_transform)
        
        # Update visible rooms for performance
        self._update_visible_rooms()
        
        # Draw room polygons (base layer)
        self._draw_room_polygons(painter)
        
        # Draw hover highlight (before selection to avoid overlap)
        if self.hovered_room:
            self._draw_hover_highlight(painter)
        
        # Draw selection highlights (on top of hover)
        self._draw_selection_highlights(painter)
        
        # Draw debug grid and coordinate system
        self._draw_debug_info(painter)
        
        # Draw room labels (top layer for visibility)
        if self._should_show_labels():
            self._draw_room_labels(painter)
    
    def wheelEvent(self, event: QWheelEvent) -> None:
        """Handle mouse wheel events for zooming."""
        if not self.floor_geometry:
            return
        
        # Calculate zoom factor
        zoom_factor = 1.15 if event.angleDelta().y() > 0 else 1.0 / 1.15
        new_zoom = self.zoom_level * zoom_factor
        
        # Clamp zoom level
        new_zoom = max(self.min_zoom, min(new_zoom, self.max_zoom))
        
        if new_zoom != self.zoom_level:
            # Zoom around mouse cursor
            mouse_pos = event.position()
            
            # Get floor coordinates before zoom
            floor_point_before = self._widget_to_floor_coordinates(mouse_pos)
            
            # Update zoom
            self.zoom_level = new_zoom
            
            # Get floor coordinates after zoom (with old pan offset)
            self._update_view_transform()
            floor_point_after = self._widget_to_floor_coordinates(mouse_pos)
            
            # Adjust pan offset to keep mouse position stable
            delta_x = (floor_point_after.x - floor_point_before.x) * self.zoom_level
            delta_y = (floor_point_after.y - floor_point_before.y) * self.zoom_level
            
            self.pan_offset.setX(self.pan_offset.x() + delta_x)
            self.pan_offset.setY(self.pan_offset.y() + delta_y)
            
            self._update_view_transform()
            self.update()
            
            self.logger.debug(f"Zoomed to {self.zoom_level:.2f}")
    
    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse press events."""
        if event.button() == Qt.MouseButton.LeftButton:
            # Check for room selection
            room_guid = self.get_room_at_point(event.position())
            
            if room_guid:
                # Room clicked
                ctrl_pressed = bool(event.modifiers() & Qt.KeyboardModifier.ControlModifier)
                self.room_clicked.emit(room_guid, ctrl_pressed)
                
                # Update selection
                if ctrl_pressed:
                    # Toggle selection
                    if room_guid in self.selected_rooms:
                        self.selected_rooms.remove(room_guid)
                    else:
                        self.selected_rooms.add(room_guid)
                else:
                    # Single selection
                    self.selected_rooms = {room_guid}
                
                self.rooms_selection_changed.emit(list(self.selected_rooms))
                self.update()
                
            else:
                # Empty area clicked - start panning or clear selection
                if not bool(event.modifiers() & Qt.KeyboardModifier.ControlModifier):
                    self.clear_selection()
                
                self.is_panning = True
                self.last_pan_point = event.position()
                self.setCursor(Qt.CursorShape.ClosedHandCursor)
        
        elif event.button() == Qt.MouseButton.MiddleButton:
            # Middle button - start panning
            self.is_panning = True
            self.last_pan_point = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
    
    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Handle mouse move events."""
        if self.is_panning:
            # Pan the view
            delta = event.position() - self.last_pan_point
            self.pan_offset += delta
            self.last_pan_point = event.position()
            
            self._update_view_transform()
            self.update()
            
        else:
            # Update hover state
            room_guid = self.get_room_at_point(event.position())
            
            if room_guid != self.hovered_room:
                self.hovered_room = room_guid
                
                # Update cursor
                if room_guid:
                    self.setCursor(Qt.CursorShape.PointingHandCursor)
                else:
                    self.setCursor(Qt.CursorShape.ArrowCursor)
                
                # Throttled update for performance
                if not self.update_timer.isActive():
                    self.update_timer.start(16)  # ~60 FPS
    
    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Handle mouse release events."""
        if event.button() in (Qt.MouseButton.LeftButton, Qt.MouseButton.MiddleButton):
            self.is_panning = False
            
            # Restore cursor
            room_guid = self.get_room_at_point(event.position())
            if room_guid:
                self.setCursor(Qt.CursorShape.PointingHandCursor)
            else:
                self.setCursor(Qt.CursorShape.ArrowCursor)
    
    def resizeEvent(self, event: QResizeEvent) -> None:
        """Handle widget resize events."""
        super().resizeEvent(event)
        self._update_view_transform()
    
    def keyPressEvent(self, event) -> None:
        """Handle keyboard events."""
        if event.key() == Qt.Key.Key_Escape:
            self.clear_selection()
        elif event.key() == Qt.Key.Key_A and bool(event.modifiers() & Qt.KeyboardModifier.ControlModifier):
            # Select all rooms
            if self.floor_geometry:
                all_guids = [p.space_guid for p in self.floor_geometry.room_polygons]
                self.highlight_rooms(all_guids)
        elif event.key() == Qt.Key.Key_0 and bool(event.modifiers() & Qt.KeyboardModifier.ControlModifier):
            # Zoom to fit
            self.zoom_to_fit()
        else:
            super().keyPressEvent(event)
    
    def _update_view_transform(self) -> None:
        """Update the view transformation matrix."""
        self.view_transform = QTransform()
        self.view_transform.translate(self.pan_offset.x(), self.pan_offset.y())
        self.view_transform.scale(self.zoom_level, self.zoom_level)
        
        # Emit view changed signal
        visible_rect = self._get_visible_floor_rect()
        self.view_changed.emit(visible_rect)
    
    def _get_visible_floor_rect(self) -> QRectF:
        """Get the currently visible area in floor coordinates."""
        widget_rect = QRectF(0, 0, self.width(), self.height())
        
        # Transform to floor coordinates
        inverse_transform, invertible = self.view_transform.inverted()
        if invertible:
            return inverse_transform.mapRect(widget_rect)
        else:
            return QRectF()
    
    def _widget_to_floor_coordinates(self, widget_point: QPointF) -> Point2D:
        """Convert widget coordinates to floor plan coordinates."""
        inverse_transform, invertible = self.view_transform.inverted()
        if invertible:
            floor_point = inverse_transform.map(widget_point)
            return Point2D(floor_point.x(), floor_point.y())
        else:
            return Point2D(0, 0)
    
    def _update_visible_rooms(self) -> None:
        """Update the list of visible rooms for performance optimization."""
        if not self.floor_geometry:
            self.visible_rooms = []
            self.logger.debug("No floor geometry available")
            return
        
        visible_rect = self._get_visible_floor_rect()
        self.logger.debug(f"Visible rect: {visible_rect.x():.1f}, {visible_rect.y():.1f}, {visible_rect.width():.1f}, {visible_rect.height():.1f}")
        
        # Simple bounds checking - could be optimized with spatial indexing
        self.visible_rooms = []
        total_rooms = len(self.floor_geometry.room_polygons)
        
        for i, polygon in enumerate(self.floor_geometry.room_polygons):
            bounds = polygon.get_bounds()
            room_rect = QRectF(bounds[0], bounds[1], bounds[2] - bounds[0], bounds[3] - bounds[1])
            
            # Log first few rooms for debugging
            if i < 3:
                self.logger.debug(f"Room {i} ({polygon.space_name}): bounds=({bounds[0]:.1f}, {bounds[1]:.1f}, {bounds[2]:.1f}, {bounds[3]:.1f})")
                self.logger.debug(f"Room rect: {room_rect.x():.1f}, {room_rect.y():.1f}, {room_rect.width():.1f}, {room_rect.height():.1f}")
                self.logger.debug(f"Intersects visible: {visible_rect.intersects(room_rect)}")
            
            # Include all rooms for now to ensure visibility
            self.visible_rooms.append(polygon)
        
        self.logger.debug(f"Updated visible rooms: {len(self.visible_rooms)}/{total_rooms} rooms visible")
    
    def _draw_room_polygons(self, painter: QPainter) -> None:
        """Draw room polygon outlines and fills with enhanced visibility."""
        if not self.visible_rooms:
            self.logger.debug("No visible rooms to draw")
            return
        
        self.logger.debug(f"Drawing {len(self.visible_rooms)} visible rooms at zoom {self.zoom_level:.2f}")
        
        # Draw visible rooms with appropriate colors
        for i, polygon in enumerate(self.visible_rooms):
            try:
                # Get color for this space - use more contrasting colors
                if self.use_color_coding:
                    fill_color = self.get_space_color(polygon.space_guid)
                    # Make fill color more opaque for better visibility
                    fill_color.setAlpha(180)
                else:
                    # Use alternating colors for better distinction
                    colors = [
                        QColor(173, 216, 230, 180),  # Light blue
                        QColor(144, 238, 144, 180),  # Light green
                        QColor(255, 218, 185, 180),  # Peach
                        QColor(221, 160, 221, 180),  # Plum
                        QColor(255, 255, 224, 180),  # Light yellow
                    ]
                    fill_color = colors[i % len(colors)]
                
                # Set up brush for fill
                brush = QBrush(fill_color)
                painter.setBrush(brush)
                
                # Set up pen for border - make it very visible
                border_width = max(2.0, 3.0 / self.zoom_level)  # Minimum 2px border
                pen = QPen(QColor(0, 0, 0), border_width)  # Black border
                painter.setPen(pen)
                
                qt_polygon = self._polygon_to_qt(polygon)
                
                # Debug: Log polygon info
                if i < 3:  # Log first 3 polygons
                    bounds = polygon.get_bounds()
                    self.logger.debug(f"Drawing polygon {i}: {polygon.space_name} at bounds ({bounds[0]:.1f}, {bounds[1]:.1f}, {bounds[2]:.1f}, {bounds[3]:.1f})")
                    self.logger.debug(f"Qt polygon has {qt_polygon.size()} points")
                
                # Draw the filled polygon
                painter.drawPolygon(qt_polygon)
                
                # Draw an additional outline for extra visibility
                outline_pen = QPen(QColor(50, 50, 50), border_width * 0.5)
                painter.setPen(outline_pen)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawPolygon(qt_polygon)
                
            except Exception as e:
                self.logger.warning(f"Failed to draw polygon {i}: {e}")
                continue
    
    def _draw_room_labels(self, painter: QPainter) -> None:
        """Draw enhanced room labels with zoom-appropriate visibility."""
        if not self._should_show_labels():
            return
        
        # Set up font and pen
        font = self._get_label_font()
        painter.setFont(font)
        
        # Use contrasting text color
        painter.setPen(QPen(self.COLOR_ROOM_TEXT))
        
        # Check if we should show detailed labels
        detailed = self._should_show_detailed_labels()
        
        # Draw labels for visible rooms
        for polygon in self.visible_rooms:
            centroid = polygon.get_centroid()
            label_point = QPointF(centroid.x, centroid.y)
            
            # Get appropriate label text
            label_text = self._get_space_label_text(polygon, detailed)
            
            if label_text:
                # Draw text with background for better visibility
                self._draw_text_with_background(painter, label_point, label_text)
    
    def _draw_text_with_background(self, painter: QPainter, position: QPointF, text: str) -> None:
        """
        Draw text with a semi-transparent background for better visibility.
        
        Args:
            painter: QPainter instance
            position: Position to draw text
            text: Text to draw
        """
        # Calculate text bounds
        font_metrics = painter.fontMetrics()
        
        # Handle multi-line text
        lines = text.split('\n')
        line_height = font_metrics.height()
        max_width = max(font_metrics.horizontalAdvance(line) for line in lines)
        total_height = line_height * len(lines)
        
        # Create background rectangle
        padding = 2
        bg_rect = QRectF(
            position.x() - max_width / 2 - padding,
            position.y() - total_height / 2 - padding,
            max_width + 2 * padding,
            total_height + 2 * padding
        )
        
        # Draw semi-transparent background
        bg_color = QColor(255, 255, 255, 180)  # Semi-transparent white
        painter.fillRect(bg_rect, bg_color)
        
        # Draw border around background
        border_pen = QPen(QColor(200, 200, 200), 1)
        painter.setPen(border_pen)
        painter.drawRect(bg_rect)
        
        # Restore text pen and draw text
        painter.setPen(QPen(self.COLOR_ROOM_TEXT))
        
        # Draw each line of text
        for i, line in enumerate(lines):
            line_y = position.y() - total_height / 2 + (i + 0.8) * line_height
            line_pos = QPointF(position.x() - font_metrics.horizontalAdvance(line) / 2, line_y)
            painter.drawText(line_pos, line)
    
    def _draw_selection_highlights(self, painter: QPainter) -> None:
        """Draw enhanced highlights for selected rooms."""
        if not self.selected_rooms:
            return
        
        # Draw selection highlights with glow effect
        for polygon in self.visible_rooms:
            if polygon.space_guid in self.selected_rooms:
                qt_polygon = self._polygon_to_qt(polygon)
                
                # Draw glow effect (outer highlight)
                glow_pen = QPen(self.COLOR_SELECTION_GLOW, self.SELECTION_GLOW_WIDTH / self.zoom_level)
                glow_brush = QBrush(self.COLOR_SELECTION_GLOW)
                painter.setPen(glow_pen)
                painter.setBrush(glow_brush)
                painter.drawPolygon(qt_polygon)
                
                # Draw main selection border
                selection_pen = QPen(self.COLOR_SELECTION_BORDER, self.ROOM_SELECTED_WIDTH / self.zoom_level)
                painter.setPen(selection_pen)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawPolygon(qt_polygon)
    
    def _draw_hover_highlight(self, painter: QPainter) -> None:
        """Draw enhanced highlight for hovered room."""
        if not self.hovered_room:
            return
        
        # Find hovered room polygon
        hovered_polygon = None
        for polygon in self.visible_rooms:
            if polygon.space_guid == self.hovered_room:
                hovered_polygon = polygon
                break
        
        if hovered_polygon:
            qt_polygon = self._polygon_to_qt(hovered_polygon)
            
            # Don't draw hover if room is already selected
            if hovered_polygon.space_guid not in self.selected_rooms:
                # Draw subtle glow effect
                glow_pen = QPen(self.COLOR_HOVER_GLOW, self.HOVER_GLOW_WIDTH / self.zoom_level)
                glow_brush = QBrush(self.COLOR_HOVER_GLOW)
                painter.setPen(glow_pen)
                painter.setBrush(glow_brush)
                painter.drawPolygon(qt_polygon)
                
                # Draw hover border
                hover_pen = QPen(self.COLOR_HOVER_BORDER, self.ROOM_HOVER_WIDTH / self.zoom_level)
                painter.setPen(hover_pen)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawPolygon(qt_polygon)
    
    def _draw_no_data_message(self, painter: QPainter) -> None:
        """Draw message when no floor geometry is available."""
        painter.setPen(QPen(QColor(100, 100, 100)))
        painter.setFont(QFont("Arial", 12))
        
        message = "No floor plan data available"
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, message)
    
    def _draw_debug_info(self, painter: QPainter) -> None:
        """Draw debug information like coordinate system and grid."""
        if not self.floor_geometry:
            return
        
        # Save current painter state
        painter.save()
        
        # Draw coordinate system axes
        pen = QPen(QColor(255, 0, 0, 100), 1.0)  # Semi-transparent red
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        
        # Draw X axis
        painter.drawLine(QPointF(-1000, 0), QPointF(1000, 0))
        # Draw Y axis  
        painter.drawLine(QPointF(0, -1000), QPointF(0, 1000))
        
        # Draw grid
        if self.zoom_level > 0.1:
            grid_pen = QPen(QColor(200, 200, 200, 50), 0.5)
            painter.setPen(grid_pen)
            
            # Grid spacing based on zoom level
            grid_spacing = 5.0 if self.zoom_level > 0.5 else 10.0
            
            # Get visible area
            visible_rect = self._get_visible_floor_rect()
            
            # Draw vertical grid lines
            start_x = int(visible_rect.left() / grid_spacing) * grid_spacing
            end_x = visible_rect.right()
            x = start_x
            while x <= end_x:
                painter.drawLine(QPointF(x, visible_rect.top()), QPointF(x, visible_rect.bottom()))
                x += grid_spacing
            
            # Draw horizontal grid lines
            start_y = int(visible_rect.top() / grid_spacing) * grid_spacing
            end_y = visible_rect.bottom()
            y = start_y
            while y <= end_y:
                painter.drawLine(QPointF(visible_rect.left(), y), QPointF(visible_rect.right(), y))
                y += grid_spacing
        
        # Draw floor bounds rectangle
        if self.floor_geometry.bounds:
            bounds = self.floor_geometry.bounds
            bounds_rect = QRectF(bounds[0], bounds[1], bounds[2] - bounds[0], bounds[3] - bounds[1])
            
            bounds_pen = QPen(QColor(0, 255, 0, 150), 2.0)  # Green bounds
            painter.setPen(bounds_pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(bounds_rect)
        
        # Restore painter state
        painter.restore()
    
    def _polygon_to_qt(self, polygon: Polygon2D) -> QPolygonF:
        """Convert Polygon2D to Qt QPolygonF."""
        qt_polygon = QPolygonF()
        for point in polygon.points:
            qt_polygon.append(QPointF(point.x, point.y))
        return qt_polygon