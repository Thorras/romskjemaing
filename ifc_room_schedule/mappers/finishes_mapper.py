"""
Finishes Mapper

Maps IFC material and finish data to room schedule finishes section.
Handles surface finishes, materials, and finish specifications.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from ..data.space_model import SpaceData, SurfaceData
from ..parsers.ns8360_name_parser import NS8360NameParser
from ..mappers.ns3940_classifier import NS3940Classifier


@dataclass
class FinishLayer:
    """Individual finish layer data."""
    
    product: Optional[str] = None
    thickness_mm: Optional[float] = None
    color_code: Optional[str] = None
    finish_code: Optional[str] = None
    supplier: Optional[str] = None
    notes: Optional[str] = None
    material_guid: Optional[str] = None


@dataclass
class FloorFinish:
    """Floor finish system data."""
    
    system: Optional[str] = None
    layers: List[FinishLayer] = None
    tolerances: Dict[str, Optional[float]] = None
    
    def __post_init__(self):
        if self.layers is None:
            self.layers = []
        if self.tolerances is None:
            self.tolerances = {
                "flatness_mm_per_2m": None,
                "levelness_mm": None
            }


@dataclass
class CeilingFinish:
    """Ceiling finish system data."""
    
    system: Optional[str] = None
    height_m: Optional[float] = None
    acoustic_class: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class WallFinish:
    """Wall finish data."""
    
    name: str  # north, east, south, west, A, B, C, D
    system: Optional[str] = None
    finish: Optional[str] = None
    color_code: Optional[str] = None
    impact_resistance: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class SkirtingFinish:
    """Skirting finish data."""
    
    type: Optional[str] = None
    height_mm: Optional[float] = None
    material: Optional[str] = None


@dataclass
class FinishesData:
    """Complete finishes data for a space."""
    
    floor: FloorFinish
    ceiling: CeilingFinish
    walls: List[WallFinish]
    skirting: SkirtingFinish
    last_updated: datetime = None
    
    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.now()


class FinishesMapper:
    """Maps IFC data to finishes section."""
    
    def __init__(self):
        """Initialize the finishes mapper."""
        self.name_parser = NS8360NameParser()
        self.classifier = NS3940Classifier()
    
    def extract_surface_finishes(self, space: SpaceData) -> FinishesData:
        """
        Extract surface finishes from space data.
        
        Args:
            space: SpaceData to extract finishes from
            
        Returns:
            FinishesData with extracted finish information
        """
        # Get room type for default finishes
        room_type = self._get_room_type(space)
        
        # Extract floor finishes
        floor_finish = self._extract_floor_finishes(space, room_type)
        
        # Extract ceiling finishes
        ceiling_finish = self._extract_ceiling_finishes(space, room_type)
        
        # Extract wall finishes
        wall_finishes = self._extract_wall_finishes(space, room_type)
        
        # Extract skirting
        skirting = self._extract_skirting_finishes(space, room_type)
        
        return FinishesData(
            floor=floor_finish,
            ceiling=ceiling_finish,
            walls=wall_finishes,
            skirting=skirting
        )
    
    def map_material_properties(self, surfaces: List[SurfaceData]) -> Dict[str, Any]:
        """
        Map material properties from surfaces.
        
        Args:
            surfaces: List of SurfaceData objects
            
        Returns:
            Dictionary of material properties
        """
        materials = {}
        
        for surface in surfaces:
            if surface.material:
                material_info = {
                    "name": surface.material.get("name", "Unknown"),
                    "description": surface.material.get("description", ""),
                    "category": surface.material.get("category", "Unknown"),
                    "color": surface.material.get("color", ""),
                    "finish": surface.material.get("finish", ""),
                    "supplier": surface.material.get("supplier", ""),
                    "product_code": surface.material.get("product_code", ""),
                    "thickness_mm": surface.material.get("thickness_mm"),
                    "u_value": surface.material.get("u_value"),
                    "fire_rating": surface.material.get("fire_rating", ""),
                    "acoustic_rating": surface.material.get("acoustic_rating", ""),
                    "emissions_class": surface.material.get("emissions_class", "")
                }
                materials[surface.surface_id] = material_info
        
        return materials
    
    def apply_finish_defaults(self, room_type: str) -> FinishesData:
        """
        Apply default finishes based on room type.
        
        Args:
            room_type: NS 3940 room type code
            
        Returns:
            FinishesData with default finishes
        """
        defaults = self._get_room_type_defaults(room_type)
        
        # Floor defaults
        floor_layers = []
        for layer_data in defaults.get("floor_layers", []):
            layer = FinishLayer(
                product=layer_data.get("product"),
                thickness_mm=layer_data.get("thickness_mm"),
                color_code=layer_data.get("color_code"),
                finish_code=layer_data.get("finish_code"),
                supplier=layer_data.get("supplier")
            )
            floor_layers.append(layer)
        
        floor = FloorFinish(
            system=defaults.get("floor_system"),
            layers=floor_layers,
            tolerances=defaults.get("floor_tolerances", {})
        )
        
        # Ceiling defaults
        ceiling = CeilingFinish(
            system=defaults.get("ceiling_system"),
            height_m=defaults.get("ceiling_height_m"),
            acoustic_class=defaults.get("ceiling_acoustic_class")
        )
        
        # Wall defaults
        walls = []
        for wall_data in defaults.get("wall_finishes", []):
            wall = WallFinish(
                name=wall_data["name"],
                system=wall_data.get("system"),
                finish=wall_data.get("finish"),
                color_code=wall_data.get("color_code"),
                impact_resistance=wall_data.get("impact_resistance")
            )
            walls.append(wall)
        
        # Skirting defaults
        skirting = SkirtingFinish(
            type=defaults.get("skirting_type"),
            height_mm=defaults.get("skirting_height_mm"),
            material=defaults.get("skirting_material")
        )
        
        return FinishesData(
            floor=floor,
            ceiling=ceiling,
            walls=walls,
            skirting=skirting
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
    
    def _extract_floor_finishes(self, space: SpaceData, room_type: str) -> FloorFinish:
        """Extract floor finish data from space."""
        # Look for floor surfaces
        floor_surfaces = [s for s in space.surfaces if s.surface_type == "floor"]
        
        if not floor_surfaces:
            # Apply defaults if no floor data
            defaults = self._get_room_type_defaults(room_type)
            return FloorFinish(
                system=defaults.get("floor_system"),
                layers=[],
                tolerances=defaults.get("floor_tolerances", {})
            )
        
        # Extract from first floor surface
        floor_surface = floor_surfaces[0]
        layers = []
        
        if floor_surface.material:
            layer = FinishLayer(
                product=floor_surface.material.get("name"),
                thickness_mm=floor_surface.material.get("thickness_mm"),
                color_code=floor_surface.material.get("color"),
                finish_code=floor_surface.material.get("finish"),
                supplier=floor_surface.material.get("supplier"),
                material_guid=floor_surface.material.get("guid")
            )
            layers.append(layer)
        
        return FloorFinish(
            system=floor_surface.material.get("system") if floor_surface.material else None,
            layers=layers,
            tolerances={
                "flatness_mm_per_2m": 2.0,  # Default tolerance
                "levelness_mm": 3.0
            }
        )
    
    def _extract_ceiling_finishes(self, space: SpaceData, room_type: str) -> CeilingFinish:
        """Extract ceiling finish data from space."""
        # Look for ceiling surfaces
        ceiling_surfaces = [s for s in space.surfaces if s.surface_type == "ceiling"]
        
        if not ceiling_surfaces:
            # Apply defaults if no ceiling data
            defaults = self._get_room_type_defaults(room_type)
            return CeilingFinish(
                system=defaults.get("ceiling_system"),
                height_m=defaults.get("ceiling_height_m"),
                acoustic_class=defaults.get("ceiling_acoustic_class")
            )
        
        # Extract from first ceiling surface
        ceiling_surface = ceiling_surfaces[0]
        
        return CeilingFinish(
            system=ceiling_surface.material.get("system") if ceiling_surface.material else None,
            height_m=space.quantities.get("Height") if space.quantities else None,
            acoustic_class=ceiling_surface.material.get("acoustic_class") if ceiling_surface.material else None
        )
    
    def _extract_wall_finishes(self, space: SpaceData, room_type: str) -> List[WallFinish]:
        """Extract wall finish data from space."""
        # Look for wall surfaces
        wall_surfaces = [s for s in space.surfaces if s.surface_type == "wall"]
        
        if not wall_surfaces:
            # Apply defaults if no wall data
            defaults = self._get_room_type_defaults(room_type)
            walls = []
            for wall_data in defaults.get("wall_finishes", []):
                wall = WallFinish(
                    name=wall_data["name"],
                    system=wall_data.get("system"),
                    finish=wall_data.get("finish"),
                    color_code=wall_data.get("color_code"),
                    impact_resistance=wall_data.get("impact_resistance")
                )
                walls.append(wall)
            return walls
        
        # Extract from wall surfaces
        walls = []
        for i, wall_surface in enumerate(wall_surfaces):
            wall_name = f"wall_{i+1}"  # Default naming
            if wall_surface.user_description:
                wall_name = wall_surface.user_description
            
            wall = WallFinish(
                name=wall_name,
                system=wall_surface.material.get("system") if wall_surface.material else None,
                finish=wall_surface.material.get("finish") if wall_surface.material else None,
                color_code=wall_surface.material.get("color") if wall_surface.material else None,
                impact_resistance=wall_surface.material.get("impact_resistance") if wall_surface.material else None
            )
            walls.append(wall)
        
        return walls
    
    def _extract_skirting_finishes(self, space: SpaceData, room_type: str) -> SkirtingFinish:
        """Extract skirting finish data from space."""
        # Skirting is typically not modeled in IFC, so use defaults
        defaults = self._get_room_type_defaults(room_type)
        
        return SkirtingFinish(
            type=defaults.get("skirting_type"),
            height_mm=defaults.get("skirting_height_mm"),
            material=defaults.get("skirting_material")
        )
    
    def _get_room_type_defaults(self, room_type: str) -> Dict[str, Any]:
        """Get default finishes for room type."""
        defaults = {
            "111": {  # Oppholdsrom
                "floor_system": "Laminate flooring",
                "floor_layers": [
                    {
                        "product": "Laminate flooring",
                        "thickness_mm": 8.0,
                        "color_code": "Oak natural",
                        "finish_code": "AC4",
                        "supplier": "Pergo"
                    }
                ],
                "floor_tolerances": {
                    "flatness_mm_per_2m": 2.0,
                    "levelness_mm": 3.0
                },
                "ceiling_system": "Gypsum board",
                "ceiling_height_m": 2.4,
                "ceiling_acoustic_class": "C",
                "wall_finishes": [
                    {"name": "north", "system": "Paint", "finish": "Matt", "color_code": "White"},
                    {"name": "east", "system": "Paint", "finish": "Matt", "color_code": "White"},
                    {"name": "south", "system": "Paint", "finish": "Matt", "color_code": "White"},
                    {"name": "west", "system": "Paint", "finish": "Matt", "color_code": "White"}
                ],
                "skirting_type": "MDF skirting",
                "skirting_height_mm": 100.0,
                "skirting_material": "MDF"
            },
            "130": {  # Våtrom
                "floor_system": "Ceramic tiles",
                "floor_layers": [
                    {
                        "product": "Ceramic tiles",
                        "thickness_mm": 10.0,
                        "color_code": "White",
                        "finish_code": "R10",
                        "supplier": "Porcelanosa"
                    }
                ],
                "floor_tolerances": {
                    "flatness_mm_per_2m": 1.0,
                    "levelness_mm": 2.0
                },
                "ceiling_system": "Moisture resistant gypsum board",
                "ceiling_height_m": 2.4,
                "ceiling_acoustic_class": "C",
                "wall_finishes": [
                    {"name": "north", "system": "Ceramic tiles", "finish": "Gloss", "color_code": "White", "impact_resistance": "High"},
                    {"name": "east", "system": "Ceramic tiles", "finish": "Gloss", "color_code": "White", "impact_resistance": "High"},
                    {"name": "south", "system": "Ceramic tiles", "finish": "Gloss", "color_code": "White", "impact_resistance": "High"},
                    {"name": "west", "system": "Ceramic tiles", "finish": "Gloss", "color_code": "White", "impact_resistance": "High"}
                ],
                "skirting_type": "Ceramic skirting",
                "skirting_height_mm": 100.0,
                "skirting_material": "Ceramic"
            },
            "131": {  # WC
                "floor_system": "Vinyl flooring",
                "floor_layers": [
                    {
                        "product": "Vinyl flooring",
                        "thickness_mm": 2.0,
                        "color_code": "Grey",
                        "finish_code": "R10",
                        "supplier": "Tarkett"
                    }
                ],
                "floor_tolerances": {
                    "flatness_mm_per_2m": 1.0,
                    "levelness_mm": 2.0
                },
                "ceiling_system": "Moisture resistant gypsum board",
                "ceiling_height_m": 2.4,
                "ceiling_acoustic_class": "C",
                "wall_finishes": [
                    {"name": "north", "system": "Paint", "finish": "Semi-gloss", "color_code": "White", "impact_resistance": "Medium"},
                    {"name": "east", "system": "Paint", "finish": "Semi-gloss", "color_code": "White", "impact_resistance": "Medium"},
                    {"name": "south", "system": "Paint", "finish": "Semi-gloss", "color_code": "White", "impact_resistance": "Medium"},
                    {"name": "west", "system": "Paint", "finish": "Semi-gloss", "color_code": "White", "impact_resistance": "Medium"}
                ],
                "skirting_type": "Vinyl skirting",
                "skirting_height_mm": 100.0,
                "skirting_material": "Vinyl"
            },
            "132": {  # Baderom
                "floor_system": "Ceramic tiles",
                "floor_layers": [
                    {
                        "product": "Ceramic tiles",
                        "thickness_mm": 10.0,
                        "color_code": "White",
                        "finish_code": "R10",
                        "supplier": "Porcelanosa"
                    }
                ],
                "floor_tolerances": {
                    "flatness_mm_per_2m": 1.0,
                    "levelness_mm": 2.0
                },
                "ceiling_system": "Moisture resistant gypsum board",
                "ceiling_height_m": 2.4,
                "ceiling_acoustic_class": "C",
                "wall_finishes": [
                    {"name": "north", "system": "Ceramic tiles", "finish": "Gloss", "color_code": "White", "impact_resistance": "High"},
                    {"name": "east", "system": "Ceramic tiles", "finish": "Gloss", "color_code": "White", "impact_resistance": "High"},
                    {"name": "south", "system": "Ceramic tiles", "finish": "Gloss", "color_code": "White", "impact_resistance": "High"},
                    {"name": "west", "system": "Ceramic tiles", "finish": "Gloss", "color_code": "White", "impact_resistance": "High"}
                ],
                "skirting_type": "Ceramic skirting",
                "skirting_height_mm": 100.0,
                "skirting_material": "Ceramic"
            },
            "140": {  # Kjøkken
                "floor_system": "Vinyl flooring",
                "floor_layers": [
                    {
                        "product": "Vinyl flooring",
                        "thickness_mm": 2.0,
                        "color_code": "Grey",
                        "finish_code": "R10",
                        "supplier": "Tarkett"
                    }
                ],
                "floor_tolerances": {
                    "flatness_mm_per_2m": 1.0,
                    "levelness_mm": 2.0
                },
                "ceiling_system": "Gypsum board",
                "ceiling_height_m": 2.4,
                "ceiling_acoustic_class": "C",
                "wall_finishes": [
                    {"name": "north", "system": "Paint", "finish": "Semi-gloss", "color_code": "White", "impact_resistance": "Medium"},
                    {"name": "east", "system": "Paint", "finish": "Semi-gloss", "color_code": "White", "impact_resistance": "Medium"},
                    {"name": "south", "system": "Paint", "finish": "Semi-gloss", "color_code": "White", "impact_resistance": "Medium"},
                    {"name": "west", "system": "Paint", "finish": "Semi-gloss", "color_code": "White", "impact_resistance": "Medium"}
                ],
                "skirting_type": "Vinyl skirting",
                "skirting_height_mm": 100.0,
                "skirting_material": "Vinyl"
            }
        }
        
        return defaults.get(room_type, defaults["111"])  # Default to oppholdsrom


# Example usage and testing
if __name__ == "__main__":
    mapper = FinishesMapper()
    
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
    
    print("Finishes Mapper Test:")
    print("=" * 50)
    
    # Test finish extraction
    finishes = mapper.extract_surface_finishes(sample_space)
    print(f"Floor system: {finishes.floor.system}")
    print(f"Floor layers: {len(finishes.floor.layers)}")
    print(f"Ceiling system: {finishes.ceiling.system}")
    print(f"Wall finishes: {len(finishes.walls)}")
    print(f"Skirting type: {finishes.skirting.type}")
    
    # Test defaults
    defaults = mapper.apply_finish_defaults("130")  # Våtrom
    print(f"\nVåtrom defaults:")
    print(f"Floor system: {defaults.floor.system}")
    print(f"Floor layers: {len(defaults.floor.layers)}")
    print(f"Ceiling system: {defaults.ceiling.system}")
    print(f"Wall finishes: {len(defaults.walls)}")
    print(f"Skirting type: {defaults.skirting.type}")
