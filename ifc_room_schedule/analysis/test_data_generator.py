"""
Test Data Generator for IFC Room Schedule

Generates mock IFC data with different quality levels for testing
the data quality analyzer and room schedule functionality.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import random
from datetime import datetime

from ..data.space_model import SpaceData
from ..data.surface_model import SurfaceData
from ..data.relationship_model import RelationshipData
from ..data.space_boundary_model import SpaceBoundaryData


@dataclass
class TestDataQualityLevel:
    """Configuration for different data quality levels."""
    
    name: str
    description: str
    completion_percentage_range: tuple[float, float]
    has_surfaces: bool
    has_relationships: bool
    has_quantities: bool
    has_materials: bool
    has_classification: bool
    has_performance_data: bool


class TestDataGenerator:
    """
    Generates mock IFC data with different quality levels for testing.
    
    This generator creates realistic test data that simulates various
    IFC file quality scenarios to test the data quality analyzer.
    """
    
    # Define quality levels
    QUALITY_LEVELS = {
        "high": TestDataQualityLevel(
            name="High Quality",
            description="Complete data with all sections populated",
            completion_percentage_range=(85.0, 95.0),
            has_surfaces=True,
            has_relationships=True,
            has_quantities=True,
            has_materials=True,
            has_classification=True,
            has_performance_data=True
        ),
        "medium": TestDataQualityLevel(
            name="Medium Quality", 
            description="Partial data with most basic sections",
            completion_percentage_range=(60.0, 80.0),
            has_surfaces=True,
            has_relationships=True,
            has_quantities=True,
            has_materials=False,
            has_classification=True,
            has_performance_data=False
        ),
        "low": TestDataQualityLevel(
            name="Low Quality",
            description="Minimal data with basic identification only",
            completion_percentage_range=(20.0, 40.0),
            has_surfaces=False,
            has_relationships=False,
            has_quantities=False,
            has_materials=False,
            has_classification=False,
            has_performance_data=False
        ),
        "mixed": TestDataQualityLevel(
            name="Mixed Quality",
            description="Inconsistent data quality across spaces",
            completion_percentage_range=(30.0, 70.0),
            has_surfaces=True,
            has_relationships=True,
            has_quantities=True,
            has_materials=True,
            has_classification=True,
            has_performance_data=False
        )
    }
    
    # Norwegian room types and NS 3940 codes
    ROOM_TYPES = {
        "111": {"name": "Oppholdsrom", "description": "Stue, oppholdsrom"},
        "130": {"name": "Våtrom", "description": "Bad, våtrom"},
        "131": {"name": "WC", "description": "Toalett"},
        "132": {"name": "Baderom", "description": "Baderom med badekar"},
        "140": {"name": "Kjøkken", "description": "Kjøkken"},
        "150": {"name": "Soverom", "description": "Soverom"},
        "160": {"name": "Kontor", "description": "Kontor, arbeidsrom"},
        "170": {"name": "Møterom", "description": "Møterom, konferanse"},
        "180": {"name": "Teknisk", "description": "Teknisk rom, VVS"}
    }
    
    # Surface types
    SURFACE_TYPES = ["Floor", "Wall", "Ceiling", "Opening"]
    
    # Materials
    MATERIALS = {
        "Floor": ["Concrete", "Wood", "Tile", "Carpet", "Vinyl"],
        "Wall": ["Brick", "Concrete", "Wood", "Plaster", "Paint"],
        "Ceiling": ["Concrete", "Plaster", "Suspended", "Wood"],
        "Opening": ["Glass", "Wood", "Metal", "Aluminum"]
    }
    
    # Equipment types
    EQUIPMENT_TYPES = {
        "door": ["Entrance Door", "Interior Door", "Fire Door", "Sliding Door"],
        "window": ["Fixed Window", "Opening Window", "Skylight", "Bay Window"],
        "fixture": ["Toilet", "Sink", "Shower", "Bathtub", "Kitchen Cabinet"],
        "equipment": ["HVAC Unit", "Electrical Panel", "Water Heater", "Pump"]
    }
    
    def __init__(self, seed: Optional[int] = None):
        """Initialize the test data generator."""
        if seed is not None:
            random.seed(seed)
    
    def generate_test_spaces(self, 
                           quality_level: str, 
                           count: int = 5,
                           building_id: str = "B001",
                           storey: str = "02") -> List[SpaceData]:
        """
        Generate test spaces with specified quality level.
        
        Args:
            quality_level: Quality level ("high", "medium", "low", "mixed")
            count: Number of spaces to generate
            building_id: Building identifier
            storey: Storey identifier
            
        Returns:
            List of SpaceData objects
        """
        if quality_level not in self.QUALITY_LEVELS:
            raise ValueError(f"Invalid quality level: {quality_level}")
        
        level_config = self.QUALITY_LEVELS[quality_level]
        spaces = []
        
        for i in range(count):
            # Generate space with random room type
            room_code = random.choice(list(self.ROOM_TYPES.keys()))
            room_info = self.ROOM_TYPES[room_code]
            
            # Generate space name following NS 8360 pattern
            space_name = f"SPC-{storey}-A{i+1:02d}-{room_code}-{i+1:03d}"
            long_name = f"{room_info['name']} {i+1:03d}"
            
            # Create base space data
            space = SpaceData(
                guid=f"SPACE_{i+1:03d}",
                name=space_name,
                long_name=long_name,
                description=room_info['description'],
                object_type="IfcSpace",
                zone_category=f"A{i+1:02d}",
                number=f"{i+1:03d}",
                elevation=0.0,
                quantities={},
                surfaces=[],
                relationships=[],
                user_descriptions={},
                processed=True
            )
            
            # Add data based on quality level
            if quality_level == "mixed":
                # Randomly apply different quality levels to different spaces
                space_quality = random.choice(["high", "medium", "low"])
                self._apply_quality_level(space, space_quality, room_code)
            else:
                self._apply_quality_level(space, quality_level, room_code)
            
            spaces.append(space)
        
        return spaces
    
    def _apply_quality_level(self, space: SpaceData, quality_level: str, room_code: str) -> None:
        """Apply specific quality level to a space."""
        level_config = self.QUALITY_LEVELS[quality_level]
        
        # Add quantities if specified
        if level_config.has_quantities:
            space.quantities = self._generate_quantities(room_code)
        
        # Add surfaces if specified
        if level_config.has_surfaces:
            space.surfaces = self._generate_surfaces(space.guid, room_code, level_config.has_materials)
        
        # Add relationships if specified
        if level_config.has_relationships:
            space.relationships = self._generate_relationships(room_code)
        
        # Add classification data if specified
        if level_config.has_classification:
            space.user_descriptions.update({
                "ns3940_code": room_code,
                "ns3940_label": self.ROOM_TYPES[room_code]["name"],
                "occupancy_type": self._get_occupancy_type(room_code),
                "category": self._get_room_category(room_code)
            })
        
        # Add performance data if specified
        if level_config.has_performance_data:
            space.user_descriptions.update(self._generate_performance_data(room_code))
    
    def _generate_quantities(self, room_code: str) -> Dict[str, float]:
        """Generate realistic quantities based on room type."""
        # Base area ranges by room type
        area_ranges = {
            "111": (15.0, 40.0),  # Oppholdsrom
            "130": (6.0, 12.0),   # Våtrom
            "131": (2.0, 4.0),    # WC
            "132": (8.0, 15.0),   # Baderom
            "140": (8.0, 20.0),   # Kjøkken
            "150": (10.0, 25.0),  # Soverom
            "160": (12.0, 30.0),  # Kontor
            "170": (15.0, 40.0),  # Møterom
            "180": (4.0, 12.0)    # Teknisk
        }
        
        min_area, max_area = area_ranges.get(room_code, (10.0, 25.0))
        gross_area = round(random.uniform(min_area, max_area), 2)
        net_area = round(gross_area * random.uniform(0.85, 0.95), 2)
        
        # Estimate other dimensions
        perimeter = round(2 * (gross_area ** 0.5 + gross_area ** 0.5), 2)
        height = round(random.uniform(2.4, 3.0), 2)
        volume = round(gross_area * height, 2)
        
        return {
            "GrossArea": gross_area,
            "NetArea": net_area,
            "Perimeter": perimeter,
            "Height": height,
            "Volume": volume
        }
    
    def _generate_surfaces(self, space_guid: str, room_code: str, include_materials: bool) -> List[SurfaceData]:
        """Generate surfaces for a space."""
        surfaces = []
        
        # Generate floor
        floor_area = random.uniform(8.0, 25.0)
        material = random.choice(self.MATERIALS["Floor"]) if include_materials else "Unknown"
        surfaces.append(SurfaceData(
            id=f"SURF_{space_guid}_FLOOR",
            type="Floor",
            area=round(floor_area, 2),
            material=material,
            ifc_type="IfcSlab",
            related_space_guid=space_guid,
            user_description=f"Floor surface",
            properties={}
        ))
        
        # Generate walls (2-4 walls)
        wall_count = random.randint(2, 4)
        for i in range(wall_count):
            wall_area = random.uniform(8.0, 20.0)
            material = random.choice(self.MATERIALS["Wall"]) if include_materials else "Unknown"
            surfaces.append(SurfaceData(
                id=f"SURF_{space_guid}_WALL_{i+1}",
                type="Wall",
                area=round(wall_area, 2),
                material=material,
                ifc_type="IfcWall",
                related_space_guid=space_guid,
                user_description=f"Wall {i+1}",
                properties={}
            ))
        
        # Generate ceiling
        ceiling_area = floor_area * random.uniform(0.9, 1.1)
        material = random.choice(self.MATERIALS["Ceiling"]) if include_materials else "Unknown"
        surfaces.append(SurfaceData(
            id=f"SURF_{space_guid}_CEILING",
            type="Ceiling",
            area=round(ceiling_area, 2),
            material=material,
            ifc_type="IfcSlab",
            related_space_guid=space_guid,
            user_description="Ceiling surface",
            properties={}
        ))
        
        return surfaces
    
    def _generate_relationships(self, room_code: str) -> List[RelationshipData]:
        """Generate relationships for a space."""
        relationships = []
        
        # Generate doors (1-3 doors)
        door_count = random.randint(1, 3)
        for i in range(door_count):
            door_type = random.choice(self.EQUIPMENT_TYPES["door"])
            relationships.append(RelationshipData(
                related_entity_guid=f"DOOR_{i+1:03d}",
                related_entity_name=f"Door {i+1}",
                related_entity_description=door_type,
                relationship_type="door",
                ifc_relationship_type="IfcRelSpaceBoundary"
            ))
        
        # Generate windows (0-2 windows)
        if random.random() < 0.7:  # 70% chance of having windows
            window_count = random.randint(1, 2)
            for i in range(window_count):
                window_type = random.choice(self.EQUIPMENT_TYPES["window"])
                relationships.append(RelationshipData(
                    related_entity_guid=f"WINDOW_{i+1:03d}",
                    related_entity_name=f"Window {i+1}",
                    related_entity_description=window_type,
                    relationship_type="window",
                    ifc_relationship_type="IfcRelSpaceBoundary"
                ))
        
        # Generate fixtures for wet rooms
        if room_code in ["130", "131", "132"]:  # Wet rooms
            fixture_count = random.randint(1, 3)
            for i in range(fixture_count):
                fixture_type = random.choice(self.EQUIPMENT_TYPES["fixture"])
                relationships.append(RelationshipData(
                    related_entity_guid=f"FIXTURE_{i+1:03d}",
                    related_entity_name=f"Fixture {i+1}",
                    related_entity_description=fixture_type,
                    relationship_type="fixture",
                    ifc_relationship_type="IfcRelContainedInSpatialStructure"
                ))
        
        return relationships
    
    def _get_occupancy_type(self, room_code: str) -> str:
        """Get occupancy type based on NS 3940 code."""
        occupancy_mapping = {
            "111": "Opphold",
            "130": "Våtrom",
            "131": "Våtrom",
            "132": "Våtrom",
            "140": "Kjøkken",
            "150": "Soverom",
            "160": "Kontor",
            "170": "Møterom",
            "180": "Teknisk"
        }
        return occupancy_mapping.get(room_code, "Opphold")
    
    def _get_room_category(self, room_code: str) -> str:
        """Get room category based on NS 3940 code."""
        category_mapping = {
            "111": "Bolig",
            "130": "Bolig",
            "131": "Bolig",
            "132": "Bolig",
            "140": "Bolig",
            "150": "Bolig",
            "160": "Kontor",
            "170": "Kontor",
            "180": "Teknisk"
        }
        return category_mapping.get(room_code, "Bolig")
    
    def _generate_performance_data(self, room_code: str) -> Dict[str, Any]:
        """Generate performance requirements based on room type."""
        performance_data = {}
        
        # Lighting requirements
        if room_code in ["111", "160", "170"]:  # Living/office spaces
            performance_data["lighting"] = {
                "task_lux": random.randint(200, 500),
                "color_rendering_CRI": random.randint(80, 95)
            }
        elif room_code in ["130", "131", "132"]:  # Wet rooms
            performance_data["lighting"] = {
                "task_lux": random.randint(200, 300),
                "emergency_lighting": True
            }
        
        # Acoustics requirements
        if room_code in ["160", "170"]:  # Office spaces
            performance_data["acoustics"] = {
                "class_ns8175": random.choice(["B", "C"]),
                "background_noise_dB": random.randint(30, 40)
            }
        
        # Ventilation requirements
        if room_code in ["130", "131", "132"]:  # Wet rooms
            performance_data["ventilation"] = {
                "airflow_extract_m3h": random.randint(50, 100)
            }
        else:
            performance_data["ventilation"] = {
                "airflow_supply_m3h": random.randint(5, 15)
            }
        
        return performance_data
    
    def generate_mixed_quality_dataset(self, total_spaces: int = 20) -> List[SpaceData]:
        """Generate a mixed quality dataset with varying data completeness."""
        spaces = []
        
        # Generate different quality levels
        high_count = total_spaces // 4
        medium_count = total_spaces // 2
        low_count = total_spaces - high_count - medium_count
        
        # High quality spaces
        spaces.extend(self.generate_test_spaces("high", high_count))
        
        # Medium quality spaces
        spaces.extend(self.generate_test_spaces("medium", medium_count))
        
        # Low quality spaces
        spaces.extend(self.generate_test_spaces("low", low_count))
        
        # Shuffle the spaces
        random.shuffle(spaces)
        
        return spaces
    
    def create_test_scenarios(self) -> Dict[str, List[SpaceData]]:
        """Create various test scenarios for comprehensive testing."""
        scenarios = {}
        
        # High quality scenario
        scenarios["high_quality"] = self.generate_test_spaces("high", 10)
        
        # Medium quality scenario
        scenarios["medium_quality"] = self.generate_test_spaces("medium", 10)
        
        # Low quality scenario
        scenarios["low_quality"] = self.generate_test_spaces("low", 10)
        
        # Mixed quality scenario
        scenarios["mixed_quality"] = self.generate_mixed_quality_dataset(15)
        
        # Realistic project scenario (mix of all types)
        realistic_spaces = []
        realistic_spaces.extend(self.generate_test_spaces("high", 5))  # Key spaces
        realistic_spaces.extend(self.generate_test_spaces("medium", 8))  # Most spaces
        realistic_spaces.extend(self.generate_test_spaces("low", 3))  # Some incomplete
        random.shuffle(realistic_spaces)
        scenarios["realistic_project"] = realistic_spaces
        
        return scenarios


