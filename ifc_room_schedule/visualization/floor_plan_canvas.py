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
    
    # Colors - Professional ArchiCAD-style
    COLOR_BACKGROUND = QColor(255, 255, 255)  # Pure white background
    COLOR_ROOM_BORDER = QColor(0, 0, 0)       # Black borders like ArchiCAD
    COLOR_ROOM_FILL = QColor(255, 255, 255, 0)  # No fill by default (transparent)
    COLOR_ROOM_SELECTED = QColor(0, 120, 215)
    COLOR_ROOM_HOVER = QColor(0, 120, 215, 50)
    COLOR_ROOM_TEXT = QColor(0, 0, 0)         # Black text like ArchiCAD
    COLOR_NO_GEOMETRY = QColor(200, 200, 200, 150)
    COLOR_GRID = QColor(220, 220, 220)        # Light gray grid
    COLOR_GRID_MAJOR = QColor(180, 180, 180)  # Darker major grid lines
    
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
        
        # Enhanced labeling and visual feedback - ArchiCAD style
        self.show_room_labels = True
        self.show_room_numbers = True
        self.show_room_areas = True  # Show area like ArchiCAD
        self.label_min_zoom = 0.4  # Show labels at reasonable zoom to avoid clutter
        self.detailed_label_min_zoom = 0.8  # Show detailed labels at higher zoom
        self.label_font_size = 10  # Professional font size
        
        # Professional drawing style
        self.use_color_coding = False  # Default to no fill like ArchiCAD
        self.use_professional_style = True  # Clean, architectural drawing style
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
        self.use_professional_style = not enabled  # Professional style when no colors
        
        if enabled:
            self._update_color_scheme_for_current_floor()
        else:
            self.space_color_scheme.clear()
        self.update()
        self.logger.debug(f"NS 3940 color coding {'enabled' if enabled else 'disabled'}")
    
    def set_professional_style(self, enabled: bool = True) -> None:
        """
        Enable or disable professional ArchiCAD-style drawing.
        
        Args:
            enabled: Whether to use professional style (no fill, black borders)
        """
        self.use_professional_style = enabled
        if enabled:
            self.use_color_coding = False  # Disable colors in professional mode
            self.space_color_scheme.clear()
        self.update()
        self.logger.debug(f"Professional style {'enabled' if enabled else 'disabled'}")
    
    def set_show_room_areas(self, show: bool = True) -> None:
        """
        Enable or disable room area display.
        
        Args:
            show: Whether to show room areas in labels
        """
        self.show_room_areas = show
        self.update()
        self.logger.debug(f"Room areas {'shown' if show else 'hidden'}")
    
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
        Get appropriate label text for a space polygon in ArchiCAD style.
        
        Args:
            polygon: Space polygon
            detailed: Whether to show detailed information
            
        Returns:
            Label text string formatted like ArchiCAD (room number + name + area)
        """
        lines = []
        
        # Extract room number from space name if available
        room_number = None
        space_name = polygon.space_name.strip() if polygon.space_name else ""
        
        # Try to extract room number from the beginning of space name
        import re
        if space_name:
            # Look for patterns like "01", "201", "2.01", etc.
            number_match = re.match(r'^(\d+\.?\d*)\s*(.*)$', space_name)
            if number_match:
                room_number = number_match.group(1)
                remaining_name = number_match.group(2).strip()
                if remaining_name:
                    space_name = remaining_name
        
        # Room number on first line (like "01", "201" in ArchiCAD)
        if room_number and self.show_room_numbers:
            lines.append(room_number)
        elif hasattr(polygon, 'room_number') and polygon.room_number:
            lines.append(str(polygon.room_number))
        
        # Space name on second line (like "Stue", "Sov", "Bad" in ArchiCAD)
        if self.show_room_labels and space_name:
            # Clean up common Norwegian room names to match ArchiCAD style
            name_mapping = {
                'stue': 'Stue',
                'soverom': 'Sov', 
                'sov': 'Sov',
                'bad': 'Bad',
                'gang': 'Gang',
                'kjøkken': 'Kjøkken',
                'wc': 'WC',
                'toalett': 'WC',
                'entre': 'Entre',
                'bod': 'Bod',
                'lager': 'Lager'
            }
            
            # Check for mapped names
            name_lower = space_name.lower()
            mapped_name = None
            for key, value in name_mapping.items():
                if key in name_lower:
                    mapped_name = value
                    break
            
            if mapped_name:
                lines.append(mapped_name)
            else:
                # Use original name, truncated if necessary
                if not detailed and len(space_name) > 10:
                    space_name = space_name[:8] + ".."
                lines.append(space_name)
        
        # Area on third line (like "37.6 m²" in ArchiCAD) - only if detailed or room is large
        if self.show_room_areas:
            area = polygon.get_area()
            if area > 0:
                # Show area if detailed view, or if room is large enough, or if zoom is high
                show_area = (detailed or 
                           area > 10.0 or  # Large rooms always show area
                           self.zoom_level > 1.0)  # High zoom shows all areas
                
                if show_area:
                    lines.append(f"{area:.1f} m²")
        
        # Fallback if no meaningful info
        if not lines:
            # Use truncated GUID as last resort
            lines.append(polygon.space_guid[:6])
        
        return "\n".join(lines)
    
    def _get_label_font(self, line_type: str = "normal") -> QFont:
        """Get font for labels based on current zoom level and line type."""
        # Base font size adjusted for zoom level - more conservative scaling
        base_size = self.label_font_size
        
        # Scale font size more gradually with zoom
        if self.zoom_level >= 1.0:
            adjusted_size = base_size
        elif self.zoom_level >= 0.5:
            adjusted_size = max(8, int(base_size * 0.9))
        else:
            adjusted_size = max(7, int(base_size * 0.8))
        
        # Professional font like ArchiCAD
        font = QFont("Arial", adjusted_size)
        
        # Different weights for different line types
        if line_type == "room_number":
            font.setBold(True)  # Room numbers bold
            font.setPointSize(adjusted_size)
        elif line_type == "room_name":
            font.setBold(False)  # Room names normal weight
            font.setPointSize(adjusted_size)
        elif line_type == "area":
            font.setBold(False)  # Area normal weight
            font.setPointSize(max(6, adjusted_size - 1))  # Slightly smaller for area
        else:
            font.setBold(adjusted_size <= 8)  # Bold for small sizes
        
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
        
        # Enhanced rendering quality
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        
        # Clear background with subtle gradient
        self._draw_background(painter)
        
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
        
        # Draw professional overlays
        self._draw_grid_overlay(painter)
        
        # Draw room labels (top layer for visibility)
        if self._should_show_labels():
            self._draw_room_labels(painter)
        
        # Draw professional indicators (not affected by transform)
        painter.resetTransform()
        self._draw_scale_indicator(painter)
        self._draw_north_arrow(painter)
    
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
        """Draw room polygon outlines in professional ArchiCAD style."""
        if not self.visible_rooms:
            self.logger.debug("No visible rooms to draw")
            return
        
        self.logger.debug(f"Drawing {len(self.visible_rooms)} visible rooms at zoom {self.zoom_level:.2f}")
        
        # Draw visible rooms in professional architectural style
        for i, polygon in enumerate(self.visible_rooms):
            try:
                # Always draw room borders - essential for floor plans
                # Use cosmetic pen that doesn't scale with coordinate system (important for mm coordinates)
                border_width = 1.0  # Always 1 pixel wide on screen
                
                # Create cosmetic pen for room borders - always visible regardless of coordinate scale
                pen = QPen(self.COLOR_ROOM_BORDER, border_width)
                pen.setCosmetic(True)  # CRITICAL: Pen width in screen pixels, not world coordinates
                pen.setJoinStyle(Qt.PenJoinStyle.MiterJoin)  # Sharp corners like ArchiCAD
                pen.setCapStyle(Qt.PenCapStyle.SquareCap)    # Square line ends
                painter.setPen(pen)
                
                # Set fill based on style
                if self.use_professional_style:
                    # No fill (transparent) like ArchiCAD
                    painter.setBrush(Qt.BrushStyle.NoBrush)
                else:
                    # Colored style for when color coding is enabled
                    if self.use_color_coding:
                        fill_color = self.get_space_color(polygon.space_guid)
                        fill_color.setAlpha(120)  # Semi-transparent
                    else:
                        # Light fill for better room distinction
                        fill_color = QColor(245, 245, 245, 80)
                    
                    painter.setBrush(QBrush(fill_color))
                
                qt_polygon = self._polygon_to_qt(polygon)
                
                # Debug: Log polygon info
                if i < 3:  # Log first 3 polygons
                    bounds = polygon.get_bounds()
                    self.logger.debug(f"Drawing polygon {i}: {polygon.space_name} at bounds ({bounds[0]:.1f}, {bounds[1]:.1f}, {bounds[2]:.1f}, {bounds[3]:.1f})")
                    self.logger.debug(f"Qt polygon has {qt_polygon.size()} points")
                
                # Draw the polygon
                painter.drawPolygon(qt_polygon)
                
            except Exception as e:
                self.logger.warning(f"Failed to draw polygon {i}: {e}")
                continue
    
    def _draw_room_labels(self, painter: QPainter) -> None:
        """Draw enhanced room labels with zoom-appropriate visibility and collision avoidance."""
        if not self._should_show_labels():
            return
        
        # Check if we should show detailed labels
        detailed = self._should_show_detailed_labels()
        
        # Only show labels at appropriate zoom levels to avoid clutter
        if self.zoom_level < 0.3:
            return
        
        # Collect label information for collision detection
        label_info = []
        
        for polygon in self.visible_rooms:
            # Get room bounds to determine if it's large enough for labels
            bounds = polygon.get_bounds()
            room_width = bounds[2] - bounds[0]
            room_height = bounds[3] - bounds[1]
            
            # Skip very small rooms at low zoom levels
            min_size_for_labels = 3.0 / self.zoom_level  # Minimum 3 screen units
            if room_width < min_size_for_labels or room_height < min_size_for_labels:
                continue
            
            # Get appropriate label text
            label_text = self._get_space_label_text(polygon, detailed)
            if not label_text:
                continue
            
            # Calculate optimal label position
            centroid = polygon.get_centroid()
            
            # Ensure label is within room bounds with some margin
            margin = 0.5
            label_x = max(bounds[0] + margin, min(bounds[2] - margin, centroid.x))
            label_y = max(bounds[1] + margin, min(bounds[3] - margin, centroid.y))
            
            label_info.append({
                'polygon': polygon,
                'text': label_text,
                'position': QPointF(label_x, label_y),
                'bounds': bounds
            })
        
        # Draw labels with collision avoidance
        self._draw_labels_with_collision_avoidance(painter, label_info, detailed)
    
    def _draw_text_with_background(self, painter: QPainter, position: QPointF, text: str) -> None:
        """
        Draw text in professional ArchiCAD style without background.
        
        Args:
            painter: QPainter instance
            position: Position to draw text
            text: Text to draw
        """
        # Handle multi-line text with different formatting per line
        lines = text.split('\n')
        if not lines:
            return
        
        # Calculate total height for centering
        line_heights = []
        total_height = 0
        
        for i, line in enumerate(lines):
            if i == 0:
                font = self._get_label_font("room_number")  # First line (room number)
            elif i == len(lines) - 1 and "m²" in line:
                font = self._get_label_font("area")  # Last line if it's area
            else:
                font = self._get_label_font("room_name")  # Middle lines (room name)
            
            painter.setFont(font)
            font_metrics = painter.fontMetrics()
            line_height = font_metrics.height()
            line_heights.append(line_height)
            total_height += line_height
        
        # Professional black text without background (like ArchiCAD)
        painter.setPen(QPen(self.COLOR_ROOM_TEXT))
        
        # Draw each line with appropriate formatting
        current_y = position.y() - total_height / 2
        
        for i, line in enumerate(lines):
            if not line.strip():
                continue
                
            # Set appropriate font for this line
            if i == 0:
                font = self._get_label_font("room_number")
            elif i == len(lines) - 1 and "m²" in line:
                font = self._get_label_font("area")
            else:
                font = self._get_label_font("room_name")
            
            painter.setFont(font)
            font_metrics = painter.fontMetrics()
            
            # Center the text horizontally
            text_width = font_metrics.horizontalAdvance(line)
            line_x = position.x() - text_width / 2
            line_y = current_y + font_metrics.ascent()
            
            # Draw the text
            painter.drawText(QPointF(line_x, line_y), line)
            
            # Move to next line
            current_y += line_heights[i]
    
    def _draw_labels_with_collision_avoidance(self, painter: QPainter, label_info: List[Dict], detailed: bool) -> None:
        """
        Draw room labels with collision avoidance to prevent overlap.
        
        Args:
            painter: QPainter instance
            label_info: List of label information dictionaries
            detailed: Whether to show detailed labels
        """
        # Sort by room size (largest first) to prioritize important rooms
        label_info.sort(key=lambda x: (x['bounds'][2] - x['bounds'][0]) * (x['bounds'][3] - x['bounds'][1]), reverse=True)
        
        drawn_labels = []  # Track drawn label positions to avoid overlap
        
        for info in label_info:
            text = info['text']
            position = info['position']
            bounds = info['bounds']
            
            # Calculate text dimensions
            lines = text.split('\n')
            if not lines:
                continue
            
            # Get maximum text width and total height
            max_width = 0
            total_height = 0
            
            for i, line in enumerate(lines):
                if i == 0:
                    font = self._get_label_font("room_number")
                elif i == len(lines) - 1 and "m²" in line:
                    font = self._get_label_font("area")
                else:
                    font = self._get_label_font("room_name")
                
                painter.setFont(font)
                font_metrics = painter.fontMetrics()
                line_width = font_metrics.horizontalAdvance(line)
                line_height = font_metrics.height()
                
                max_width = max(max_width, line_width)
                total_height += line_height
            
            # Convert to screen coordinates for collision detection
            screen_pos = self.view_transform.map(position)
            screen_width = max_width * self.zoom_level
            screen_height = total_height * self.zoom_level
            
            # Create label rectangle in screen coordinates
            label_rect = QRectF(
                screen_pos.x() - screen_width / 2,
                screen_pos.y() - screen_height / 2,
                screen_width,
                screen_height
            )
            
            # Check for collision with existing labels
            collision = False
            for existing_rect in drawn_labels:
                if label_rect.intersects(existing_rect):
                    collision = True
                    break
            
            # Skip if there's a collision and room is small
            room_area = (bounds[2] - bounds[0]) * (bounds[3] - bounds[1])
            if collision and room_area < 15.0:  # Skip small rooms if collision
                continue
            
            # Draw the label
            self._draw_single_room_label(painter, position, text, detailed)
            
            # Add to drawn labels list
            drawn_labels.append(label_rect)
    
    def _draw_single_room_label(self, painter: QPainter, position: QPointF, text: str, detailed: bool) -> None:
        """
        Draw a single room label with proper formatting.
        
        Args:
            painter: QPainter instance
            position: Position to draw text
            text: Text to draw
            detailed: Whether this is detailed view
        """
        lines = text.split('\n')
        if not lines:
            return
        
        # Calculate line spacing based on zoom level
        base_spacing = 1.2  # Base line spacing multiplier
        zoom_spacing = max(0.8, min(1.5, 1.0 / self.zoom_level))  # Adjust for zoom
        line_spacing = base_spacing * zoom_spacing
        
        # Calculate total height for centering
        total_height = 0
        line_heights = []
        
        for i, line in enumerate(lines):
            if i == 0:
                font = self._get_label_font("room_number")
            elif i == len(lines) - 1 and "m²" in line:
                font = self._get_label_font("area")
            else:
                font = self._get_label_font("room_name")
            
            painter.setFont(font)
            font_metrics = painter.fontMetrics()
            line_height = font_metrics.height() * line_spacing
            line_heights.append(line_height)
            total_height += line_height
        
        # Start drawing from top
        current_y = position.y() - total_height / 2
        
        for i, line in enumerate(lines):
            if not line.strip():
                continue
            
            # Set appropriate font and color for this line
            if i == 0:
                font = self._get_label_font("room_number")
                painter.setPen(QPen(QColor(0, 0, 0)))  # Black for room number
            elif i == len(lines) - 1 and "m²" in line:
                font = self._get_label_font("area")
                painter.setPen(QPen(QColor(80, 80, 80)))  # Slightly gray for area
            else:
                font = self._get_label_font("room_name")
                painter.setPen(QPen(QColor(40, 40, 40)))  # Dark gray for room name
            
            painter.setFont(font)
            font_metrics = painter.fontMetrics()
            
            # Center the text horizontally
            text_width = font_metrics.horizontalAdvance(line)
            line_x = position.x() - text_width / 2
            line_y = current_y + font_metrics.ascent()
            
            # Draw the text
            painter.drawText(QPointF(line_x, line_y), line)
            
            # Move to next line
            current_y += line_heights[i]
    
    def _draw_selection_highlights(self, painter: QPainter) -> None:
        """Draw enhanced highlights for selected rooms."""
        if not self.selected_rooms:
            return
        
        # Draw selection highlights with glow effect
        for polygon in self.visible_rooms:
            if polygon.space_guid in self.selected_rooms:
                qt_polygon = self._polygon_to_qt(polygon)
                
                # Draw glow effect (outer highlight)
                glow_pen = QPen(self.COLOR_SELECTION_GLOW, self.SELECTION_GLOW_WIDTH)
                glow_pen.setCosmetic(True)  # Screen pixels, not world coordinates
                glow_brush = QBrush(self.COLOR_SELECTION_GLOW)
                painter.setPen(glow_pen)
                painter.setBrush(glow_brush)
                painter.drawPolygon(qt_polygon)
                
                # Draw main selection border
                selection_pen = QPen(self.COLOR_SELECTION_BORDER, self.ROOM_SELECTED_WIDTH)
                selection_pen.setCosmetic(True)  # Screen pixels, not world coordinates
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
                glow_pen = QPen(self.COLOR_HOVER_GLOW, self.HOVER_GLOW_WIDTH)
                glow_pen.setCosmetic(True)  # Screen pixels, not world coordinates
                glow_brush = QBrush(self.COLOR_HOVER_GLOW)
                painter.setPen(glow_pen)
                painter.setBrush(glow_brush)
                painter.drawPolygon(qt_polygon)
                
                # Draw hover border
                hover_pen = QPen(self.COLOR_HOVER_BORDER, self.ROOM_HOVER_WIDTH)
                hover_pen.setCosmetic(True)  # Screen pixels, not world coordinates
                painter.setPen(hover_pen)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawPolygon(qt_polygon)
    
    def _draw_no_data_message(self, painter: QPainter) -> None:
        """Draw message when no floor geometry is available."""
        painter.setPen(QPen(QColor(100, 100, 100)))
        painter.setFont(QFont("Arial", 12))
        
        message = "No floor plan data available"
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, message)
    
    def _draw_background(self, painter: QPainter) -> None:
        """Draw clean white background like ArchiCAD."""
        # Pure white background for professional architectural drawings
        painter.fillRect(self.rect(), self.COLOR_BACKGROUND)
    
    def _draw_grid_overlay(self, painter: QPainter) -> None:
        """Draw professional grid overlay like ArchiCAD."""
        if not self.floor_geometry or self.zoom_level < 0.15:
            return
        
        # Save current painter state
        painter.save()
        
        # Grid configuration based on zoom level - more subtle like ArchiCAD
        if self.zoom_level > 1.5:
            grid_spacing = 1.0  # 1m grid for high zoom
            show_grid = True
        elif self.zoom_level > 0.5:
            grid_spacing = 2.5  # 2.5m grid for medium zoom
            show_grid = True
        elif self.zoom_level > 0.25:
            grid_spacing = 5.0  # 5m grid for lower zoom
            show_grid = True
        else:
            grid_spacing = 10.0  # 10m grid for very low zoom
            show_grid = self.zoom_level > 0.15
        
        if not show_grid:
            painter.restore()
            return
        
        # Very light grid like ArchiCAD
        grid_pen = QPen(self.COLOR_GRID, 0.25)
        grid_pen.setCosmetic(True)  # Screen pixels, not world coordinates
        painter.setPen(grid_pen)
        
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
        
        # Draw major grid lines (every 5m or 10m) with slightly stronger emphasis
        major_spacing = 5.0 if grid_spacing <= 2.5 else 10.0
        if major_spacing > grid_spacing:
            major_pen = QPen(self.COLOR_GRID_MAJOR, 0.5)
            major_pen.setCosmetic(True)  # Screen pixels, not world coordinates
            painter.setPen(major_pen)
            
            # Major vertical lines
            major_x = int(visible_rect.left() / major_spacing) * major_spacing
            while major_x <= visible_rect.right():
                painter.drawLine(QPointF(major_x, visible_rect.top()), QPointF(major_x, visible_rect.bottom()))
                major_x += major_spacing
            
            # Major horizontal lines
            major_y = int(visible_rect.top() / major_spacing) * major_spacing
            while major_y <= visible_rect.bottom():
                painter.drawLine(QPointF(visible_rect.left(), major_y), QPointF(visible_rect.right(), major_y))
                major_y += major_spacing
        
        # Restore painter state
        painter.restore()
    
    def _draw_scale_indicator(self, painter: QPainter) -> None:
        """Draw scale indicator in bottom-right corner."""
        if not self.floor_geometry:
            return
        
        painter.save()
        
        # Calculate scale bar length in meters
        if self.zoom_level > 2.0:
            scale_length_m = 5.0
        elif self.zoom_level > 0.5:
            scale_length_m = 10.0
        elif self.zoom_level > 0.2:
            scale_length_m = 25.0
        else:
            scale_length_m = 50.0
        
        # Convert to screen pixels
        scale_length_px = scale_length_m * self.zoom_level
        
        # Position in bottom-right corner
        margin = 20
        start_x = self.width() - margin - scale_length_px - 60
        start_y = self.height() - margin - 30
        
        # Draw scale bar background
        bg_rect = QRectF(start_x - 10, start_y - 15, scale_length_px + 80, 35)
        painter.fillRect(bg_rect, QColor(255, 255, 255, 200))
        painter.setPen(QPen(QColor(200, 200, 200), 1))
        painter.drawRect(bg_rect)
        
        # Draw scale bar
        painter.setPen(QPen(QColor(0, 0, 0), 2))
        painter.drawLine(QPointF(start_x, start_y), QPointF(start_x + scale_length_px, start_y))
        
        # Draw tick marks
        painter.drawLine(QPointF(start_x, start_y - 5), QPointF(start_x, start_y + 5))
        painter.drawLine(QPointF(start_x + scale_length_px, start_y - 5), QPointF(start_x + scale_length_px, start_y + 5))
        
        # Draw scale text
        painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        scale_text = f"{scale_length_m:.0f}m"
        painter.drawText(QPointF(start_x + scale_length_px + 10, start_y + 5), scale_text)
        
        painter.restore()
    
    def _draw_north_arrow(self, painter: QPainter) -> None:
        """Draw north arrow in top-right corner."""
        painter.save()
        
        # Position in top-right corner
        margin = 20
        center_x = self.width() - margin - 25
        center_y = margin + 25
        
        # Draw background circle
        painter.setBrush(QBrush(QColor(255, 255, 255, 200)))
        painter.setPen(QPen(QColor(200, 200, 200), 1))
        painter.drawEllipse(QPointF(center_x, center_y), 20, 20)
        
        # Draw north arrow
        painter.setBrush(QBrush(QColor(220, 50, 50)))  # Red arrow
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        
        # Arrow points
        arrow_points = [
            QPointF(center_x, center_y - 15),      # Top point
            QPointF(center_x - 6, center_y + 5),   # Bottom left
            QPointF(center_x, center_y),           # Center
            QPointF(center_x + 6, center_y + 5),   # Bottom right
        ]
        
        from PyQt6.QtGui import QPolygonF
        arrow_polygon = QPolygonF(arrow_points)
        painter.drawPolygon(arrow_polygon)
        
        # Draw "N" label
        painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
        painter.setPen(QPen(QColor(0, 0, 0)))
        painter.drawText(QPointF(center_x - 4, center_y + 18), "N")
        
        painter.restore()
    
    def _draw_debug_info(self, painter: QPainter) -> None:
        """Draw debug information like coordinate system and grid."""
        if not self.floor_geometry:
            return
        
        # Only show debug info in debug mode
        if not getattr(self, 'debug_mode', False):
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