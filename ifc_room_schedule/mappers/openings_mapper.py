"""
Openings Mapper

Maps IFC door and window data to room schedule openings section.
Handles doors, windows, and penetrations.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from ..data.space_model import SpaceData, SurfaceData
from ..parsers.ns8360_name_parser import NS8360NameParser
from ..mappers.ns3940_classifier import NS3940Classifier


@dataclass
class DoorData:
    """Door opening data."""
    
    id: Optional[str] = None
    width_mm: Optional[float] = None
    height_mm: Optional[float] = None
    fire_rating: Optional[str] = None
    sound_rating_rw_db: Optional[float] = None
    threshold: Optional[str] = None  # yes, no, null
    hardware_set: Optional[str] = None
    access_control: bool = False
    notes: Optional[str] = None
    material: Optional[str] = None
    frame_material: Optional[str] = None
    glazing: Optional[str] = None
    door_type: Optional[str] = None  # Single, Double, Sliding, etc.
    swing_direction: Optional[str] = None  # Left, Right, Double
    surface_guid: Optional[str] = None


@dataclass
class WindowData:
    """Window opening data."""
    
    id: Optional[str] = None
    width_mm: Optional[float] = None
    height_mm: Optional[float] = None
    u_value_w_m2k: Optional[float] = None
    g_value: Optional[float] = None
    safety_glass: bool = False
    solar_shading: Optional[str] = None
    frame_material: Optional[str] = None
    glazing_type: Optional[str] = None
    window_type: Optional[str] = None  # Fixed, Casement, Tilt-turn, etc.
    opening_direction: Optional[str] = None
    surface_guid: Optional[str] = None


@dataclass
class PenetrationData:
    """Penetration opening data."""
    
    id: Optional[str] = None
    type: Optional[str] = None  # Electrical, Plumbing, HVAC, etc.
    diameter_mm: Optional[float] = None
    width_mm: Optional[float] = None
    height_mm: Optional[float] = None
    fire_sealing: Optional[str] = None
    acoustic_sealing: Optional[str] = None
    notes: Optional[str] = None
    surface_guid: Optional[str] = None


@dataclass
class OpeningsData:
    """Complete openings data for a space."""
    
    doors: List[DoorData]
    windows: List[WindowData]
    penetrations: List[PenetrationData]
    last_updated: datetime = None
    
    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.now()


class OpeningsMapper:
    """Maps IFC data to openings section."""
    
    def __init__(self):
        """Initialize the openings mapper."""
        self.name_parser = NS8360NameParser()
        self.classifier = NS3940Classifier()
    
    def extract_openings(self, space: SpaceData) -> OpeningsData:
        """
        Extract openings from space data.
        
        Args:
            space: SpaceData to extract openings from
            
        Returns:
            OpeningsData with extracted opening information
        """
        # Get room type for default openings
        room_type = self._get_room_type(space)
        
        # Extract doors
        doors = self._extract_doors(space, room_type)
        
        # Extract windows
        windows = self._extract_windows(space, room_type)
        
        # Extract penetrations
        penetrations = self._extract_penetrations(space, room_type)
        
        return OpeningsData(
            doors=doors,
            windows=windows,
            penetrations=penetrations
        )
    
    def map_door_properties(self, surfaces: List[SurfaceData]) -> List[DoorData]:
        """
        Map door properties from surfaces.
        
        Args:
            surfaces: List of SurfaceData objects
            
        Returns:
            List of DoorData objects
        """
        doors = []
        
        for surface in surfaces:
            if surface.surface_type == "door" or "door" in surface.user_description.lower():
                door = DoorData(
                    id=surface.surface_id,
                    width_mm=surface.dimensions.get("width_mm") if surface.dimensions else None,
                    height_mm=surface.dimensions.get("height_mm") if surface.dimensions else None,
                    fire_rating=surface.material.get("fire_rating") if surface.material else None,
                    sound_rating_rw_db=surface.material.get("sound_rating_rw_db") if surface.material else None,
                    material=surface.material.get("name") if surface.material else None,
                    frame_material=surface.material.get("frame_material") if surface.material else None,
                    door_type=surface.material.get("door_type") if surface.material else None,
                    swing_direction=surface.material.get("swing_direction") if surface.material else None,
                    surface_guid=surface.surface_id
                )
                doors.append(door)
        
        return doors
    
    def map_window_properties(self, surfaces: List[SurfaceData]) -> List[WindowData]:
        """
        Map window properties from surfaces.
        
        Args:
            surfaces: List of SurfaceData objects
            
        Returns:
            List of WindowData objects
        """
        windows = []
        
        for surface in surfaces:
            if surface.surface_type == "window" or "window" in surface.user_description.lower():
                window = WindowData(
                    id=surface.surface_id,
                    width_mm=surface.dimensions.get("width_mm") if surface.dimensions else None,
                    height_mm=surface.dimensions.get("height_mm") if surface.dimensions else None,
                    u_value_w_m2k=surface.material.get("u_value") if surface.material else None,
                    g_value=surface.material.get("g_value") if surface.material else None,
                    safety_glass=surface.material.get("safety_glass", False) if surface.material else False,
                    solar_shading=surface.material.get("solar_shading") if surface.material else None,
                    frame_material=surface.material.get("frame_material") if surface.material else None,
                    glazing_type=surface.material.get("glazing_type") if surface.material else None,
                    window_type=surface.material.get("window_type") if surface.material else None,
                    opening_direction=surface.material.get("opening_direction") if surface.material else None,
                    surface_guid=surface.surface_id
                )
                windows.append(window)
        
        return windows
    
    def apply_opening_defaults(self, room_type: str) -> OpeningsData:
        """
        Apply default openings based on room type.
        
        Args:
            room_type: NS 3940 room type code
            
        Returns:
            OpeningsData with default openings
        """
        defaults = self._get_room_type_defaults(room_type)
        
        # Door defaults
        doors = []
        for door_data in defaults.get("doors", []):
            door = DoorData(
                id=door_data.get("id"),
                width_mm=door_data.get("width_mm"),
                height_mm=door_data.get("height_mm"),
                fire_rating=door_data.get("fire_rating"),
                sound_rating_rw_db=door_data.get("sound_rating_rw_db"),
                threshold=door_data.get("threshold"),
                hardware_set=door_data.get("hardware_set"),
                access_control=door_data.get("access_control", False),
                material=door_data.get("material"),
                frame_material=door_data.get("frame_material"),
                door_type=door_data.get("door_type"),
                swing_direction=door_data.get("swing_direction")
            )
            doors.append(door)
        
        # Window defaults
        windows = []
        for window_data in defaults.get("windows", []):
            window = WindowData(
                id=window_data.get("id"),
                width_mm=window_data.get("width_mm"),
                height_mm=window_data.get("height_mm"),
                u_value_w_m2k=window_data.get("u_value_w_m2k"),
                g_value=window_data.get("g_value"),
                safety_glass=window_data.get("safety_glass", False),
                solar_shading=window_data.get("solar_shading"),
                frame_material=window_data.get("frame_material"),
                glazing_type=window_data.get("glazing_type"),
                window_type=window_data.get("window_type"),
                opening_direction=window_data.get("opening_direction")
            )
            windows.append(window)
        
        # Penetration defaults
        penetrations = []
        for penetration_data in defaults.get("penetrations", []):
            penetration = PenetrationData(
                id=penetration_data.get("id"),
                type=penetration_data.get("type"),
                diameter_mm=penetration_data.get("diameter_mm"),
                width_mm=penetration_data.get("width_mm"),
                height_mm=penetration_data.get("height_mm"),
                fire_sealing=penetration_data.get("fire_sealing"),
                acoustic_sealing=penetration_data.get("acoustic_sealing"),
                notes=penetration_data.get("notes")
            )
            penetrations.append(penetration)
        
        return OpeningsData(
            doors=doors,
            windows=windows,
            penetrations=penetrations
        )
    
    def _get_room_type(self, space: SpaceData) -> str:
        """Get room type from space data."""
        if space.name:
            parsed_name = self.name_parser.parse(space.name)
            if parsed_name.is_valid and parsed_name.function_code:
                return parsed_name.function_code
            
            classification = self.classifier.classify_from_name(space.name)
            if classification:
                return classification.function_code
        
        return "111"  # Default to oppholdsrom
    
    def _extract_doors(self, space: SpaceData, room_type: str) -> List[DoorData]:
        """Extract door data from space."""
        # Look for door surfaces
        door_surfaces = [s for s in space.surfaces if s.surface_type == "door"]
        
        if not door_surfaces:
            # Apply defaults if no door data
            defaults = self._get_room_type_defaults(room_type)
            doors = []
            for door_data in defaults.get("doors", []):
                door = DoorData(
                    id=door_data.get("id"),
                    width_mm=door_data.get("width_mm"),
                    height_mm=door_data.get("height_mm"),
                    fire_rating=door_data.get("fire_rating"),
                    sound_rating_rw_db=door_data.get("sound_rating_rw_db"),
                    threshold=door_data.get("threshold"),
                    hardware_set=door_data.get("hardware_set"),
                    access_control=door_data.get("access_control", False),
                    material=door_data.get("material"),
                    frame_material=door_data.get("frame_material"),
                    door_type=door_data.get("door_type"),
                    swing_direction=door_data.get("swing_direction")
                )
                doors.append(door)
            return doors
        
        # Extract from door surfaces
        doors = []
        for surface in door_surfaces:
            door = DoorData(
                id=surface.surface_id,
                width_mm=surface.dimensions.get("width_mm") if surface.dimensions else None,
                height_mm=surface.dimensions.get("height_mm") if surface.dimensions else None,
                fire_rating=surface.material.get("fire_rating") if surface.material else None,
                sound_rating_rw_db=surface.material.get("sound_rating_rw_db") if surface.material else None,
                material=surface.material.get("name") if surface.material else None,
                frame_material=surface.material.get("frame_material") if surface.material else None,
                door_type=surface.material.get("door_type") if surface.material else None,
                swing_direction=surface.material.get("swing_direction") if surface.material else None,
                surface_guid=surface.surface_id
            )
            doors.append(door)
        
        return doors
    
    def _extract_windows(self, space: SpaceData, room_type: str) -> List[WindowData]:
        """Extract window data from space."""
        # Look for window surfaces
        window_surfaces = [s for s in space.surfaces if s.surface_type == "window"]
        
        if not window_surfaces:
            # Apply defaults if no window data
            defaults = self._get_room_type_defaults(room_type)
            windows = []
            for window_data in defaults.get("windows", []):
                window = WindowData(
                    id=window_data.get("id"),
                    width_mm=window_data.get("width_mm"),
                    height_mm=window_data.get("height_mm"),
                    u_value_w_m2k=window_data.get("u_value_w_m2k"),
                    g_value=window_data.get("g_value"),
                    safety_glass=window_data.get("safety_glass", False),
                    solar_shading=window_data.get("solar_shading"),
                    frame_material=window_data.get("frame_material"),
                    glazing_type=window_data.get("glazing_type"),
                    window_type=window_data.get("window_type"),
                    opening_direction=window_data.get("opening_direction")
                )
                windows.append(window)
            return windows
        
        # Extract from window surfaces
        windows = []
        for surface in window_surfaces:
            window = WindowData(
                id=surface.surface_id,
                width_mm=surface.dimensions.get("width_mm") if surface.dimensions else None,
                height_mm=surface.dimensions.get("height_mm") if surface.dimensions else None,
                u_value_w_m2k=surface.material.get("u_value") if surface.material else None,
                g_value=surface.material.get("g_value") if surface.material else None,
                safety_glass=surface.material.get("safety_glass", False) if surface.material else False,
                solar_shading=surface.material.get("solar_shading") if surface.material else None,
                frame_material=surface.material.get("frame_material") if surface.material else None,
                glazing_type=surface.material.get("glazing_type") if surface.material else None,
                window_type=surface.material.get("window_type") if surface.material else None,
                opening_direction=surface.material.get("opening_direction") if surface.material else None,
                surface_guid=surface.surface_id
            )
            windows.append(window)
        
        return windows
    
    def _extract_penetrations(self, space: SpaceData, room_type: str) -> List[PenetrationData]:
        """Extract penetration data from space."""
        # Look for penetration surfaces
        penetration_surfaces = [s for s in space.surfaces if s.surface_type == "penetration"]
        
        if not penetration_surfaces:
            # Apply defaults if no penetration data
            defaults = self._get_room_type_defaults(room_type)
            penetrations = []
            for penetration_data in defaults.get("penetrations", []):
                penetration = PenetrationData(
                    id=penetration_data.get("id"),
                    type=penetration_data.get("type"),
                    diameter_mm=penetration_data.get("diameter_mm"),
                    width_mm=penetration_data.get("width_mm"),
                    height_mm=penetration_data.get("height_mm"),
                    fire_sealing=penetration_data.get("fire_sealing"),
                    acoustic_sealing=penetration_data.get("acoustic_sealing"),
                    notes=penetration_data.get("notes")
                )
                penetrations.append(penetration)
            return penetrations
        
        # Extract from penetration surfaces
        penetrations = []
        for surface in penetration_surfaces:
            penetration = PenetrationData(
                id=surface.surface_id,
                type=surface.material.get("type") if surface.material else None,
                diameter_mm=surface.dimensions.get("diameter_mm") if surface.dimensions else None,
                width_mm=surface.dimensions.get("width_mm") if surface.dimensions else None,
                height_mm=surface.dimensions.get("height_mm") if surface.dimensions else None,
                fire_sealing=surface.material.get("fire_sealing") if surface.material else None,
                acoustic_sealing=surface.material.get("acoustic_sealing") if surface.material else None,
                notes=surface.user_description,
                surface_guid=surface.surface_id
            )
            penetrations.append(penetration)
        
        return penetrations
    
    def _get_room_type_defaults(self, room_type: str) -> Dict[str, Any]:
        """Get default openings for room type."""
        defaults = {
            "111": {  # Oppholdsrom
                "doors": [
                    {
                        "id": "door_001",
                        "width_mm": 900.0,
                        "height_mm": 2100.0,
                        "fire_rating": "EI30",
                        "sound_rating_rw_db": 30.0,
                        "threshold": "no",
                        "hardware_set": "Standard",
                        "access_control": False,
                        "material": "Wood",
                        "frame_material": "Wood",
                        "door_type": "Single",
                        "swing_direction": "Left"
                    }
                ],
                "windows": [
                    {
                        "id": "window_001",
                        "width_mm": 1200.0,
                        "height_mm": 1200.0,
                        "u_value_w_m2k": 1.2,
                        "g_value": 0.6,
                        "safety_glass": False,
                        "solar_shading": "None",
                        "frame_material": "Aluminum",
                        "glazing_type": "Double glazing",
                        "window_type": "Casement",
                        "opening_direction": "Outward"
                    }
                ],
                "penetrations": []
            },
            "130": {  # Våtrom
                "doors": [
                    {
                        "id": "door_001",
                        "width_mm": 800.0,
                        "height_mm": 2100.0,
                        "fire_rating": "EI30",
                        "sound_rating_rw_db": 35.0,
                        "threshold": "yes",
                        "hardware_set": "Bathroom",
                        "access_control": False,
                        "material": "Moisture resistant",
                        "frame_material": "Aluminum",
                        "door_type": "Single",
                        "swing_direction": "Outward"
                    }
                ],
                "windows": [
                    {
                        "id": "window_001",
                        "width_mm": 600.0,
                        "height_mm": 600.0,
                        "u_value_w_m2k": 1.2,
                        "g_value": 0.6,
                        "safety_glass": True,
                        "solar_shading": "None",
                        "frame_material": "Aluminum",
                        "glazing_type": "Double glazing",
                        "window_type": "Fixed",
                        "opening_direction": "None"
                    }
                ],
                "penetrations": [
                    {
                        "id": "pen_001",
                        "type": "Plumbing",
                        "diameter_mm": 100.0,
                        "fire_sealing": "Firestop",
                        "acoustic_sealing": "Acoustic seal"
                    }
                ]
            },
            "131": {  # WC
                "doors": [
                    {
                        "id": "door_001",
                        "width_mm": 800.0,
                        "height_mm": 2100.0,
                        "fire_rating": "EI30",
                        "sound_rating_rw_db": 35.0,
                        "threshold": "no",
                        "hardware_set": "Bathroom",
                        "access_control": False,
                        "material": "Moisture resistant",
                        "frame_material": "Aluminum",
                        "door_type": "Single",
                        "swing_direction": "Outward"
                    }
                ],
                "windows": [],
                "penetrations": [
                    {
                        "id": "pen_001",
                        "type": "Plumbing",
                        "diameter_mm": 100.0,
                        "fire_sealing": "Firestop",
                        "acoustic_sealing": "Acoustic seal"
                    }
                ]
            },
            "132": {  # Baderom
                "doors": [
                    {
                        "id": "door_001",
                        "width_mm": 800.0,
                        "height_mm": 2100.0,
                        "fire_rating": "EI30",
                        "sound_rating_rw_db": 35.0,
                        "threshold": "yes",
                        "hardware_set": "Bathroom",
                        "access_control": False,
                        "material": "Moisture resistant",
                        "frame_material": "Aluminum",
                        "door_type": "Single",
                        "swing_direction": "Outward"
                    }
                ],
                "windows": [
                    {
                        "id": "window_001",
                        "width_mm": 600.0,
                        "height_mm": 600.0,
                        "u_value_w_m2k": 1.2,
                        "g_value": 0.6,
                        "safety_glass": True,
                        "solar_shading": "None",
                        "frame_material": "Aluminum",
                        "glazing_type": "Double glazing",
                        "window_type": "Fixed",
                        "opening_direction": "None"
                    }
                ],
                "penetrations": [
                    {
                        "id": "pen_001",
                        "type": "Plumbing",
                        "diameter_mm": 100.0,
                        "fire_sealing": "Firestop",
                        "acoustic_sealing": "Acoustic seal"
                    }
                ]
            },
            "140": {  # Kjøkken
                "doors": [
                    {
                        "id": "door_001",
                        "width_mm": 900.0,
                        "height_mm": 2100.0,
                        "fire_rating": "EI30",
                        "sound_rating_rw_db": 30.0,
                        "threshold": "no",
                        "hardware_set": "Standard",
                        "access_control": False,
                        "material": "Wood",
                        "frame_material": "Wood",
                        "door_type": "Single",
                        "swing_direction": "Left"
                    }
                ],
                "windows": [
                    {
                        "id": "window_001",
                        "width_mm": 1200.0,
                        "height_mm": 1200.0,
                        "u_value_w_m2k": 1.2,
                        "g_value": 0.6,
                        "safety_glass": False,
                        "solar_shading": "None",
                        "frame_material": "Aluminum",
                        "glazing_type": "Double glazing",
                        "window_type": "Casement",
                        "opening_direction": "Outward"
                    }
                ],
                "penetrations": [
                    {
                        "id": "pen_001",
                        "type": "Electrical",
                        "width_mm": 100.0,
                        "height_mm": 50.0,
                        "fire_sealing": "Firestop",
                        "acoustic_sealing": "Acoustic seal"
                    },
                    {
                        "id": "pen_002",
                        "type": "Plumbing",
                        "diameter_mm": 50.0,
                        "fire_sealing": "Firestop",
                        "acoustic_sealing": "Acoustic seal"
                    }
                ]
            }
        }
        
        return defaults.get(room_type, defaults["111"])  # Default to oppholdsrom


# Example usage and testing
if __name__ == "__main__":
    mapper = OpeningsMapper()
    
    # Test with sample space
    from ..data.space_model import SpaceData
    
    sample_space = SpaceData(
        guid="test_space",
        name="SPC-02-A101-111-003",
        long_name="Stue | 02/A101 | NS3940:111",
        description="Test space",
        object_type="IfcSpace",
        zone_category="A101",
        number="003",
        elevation=0.0,
        quantities={"Height": 2.4},
        surfaces=[],
        space_boundaries=[],
        relationships=[]
    )
    
    print("Openings Mapper Test:")
    print("=" * 50)
    
    # Test opening extraction
    openings = mapper.extract_openings(sample_space)
    print(f"Doors: {len(openings.doors)}")
    print(f"Windows: {len(openings.windows)}")
    print(f"Penetrations: {len(openings.penetrations)}")
    
    if openings.doors:
        door = openings.doors[0]
        print(f"Door: {door.width_mm}x{door.height_mm}mm, {door.material}")
    
    if openings.windows:
        window = openings.windows[0]
        print(f"Window: {window.width_mm}x{window.height_mm}mm, U={window.u_value_w_m2k}")
    
    # Test defaults
    defaults = mapper.apply_opening_defaults("130")  # Våtrom
    print(f"\nVåtrom defaults:")
    print(f"Doors: {len(defaults.doors)}")
    print(f"Windows: {len(defaults.windows)}")
    print(f"Penetrations: {len(defaults.penetrations)}")
    
    if defaults.doors:
        door = defaults.doors[0]
        print(f"Door: {door.width_mm}x{door.height_mm}mm, {door.material}")
    
    if defaults.windows:
        window = defaults.windows[0]
        print(f"Window: {window.width_mm}x{window.height_mm}mm, U={window.u_value_w_m2k}")
    
    if defaults.penetrations:
        penetration = defaults.penetrations[0]
        print(f"Penetration: {penetration.type}, Ø{penetration.diameter_mm}mm")
