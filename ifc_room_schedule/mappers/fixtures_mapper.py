"""
Fixtures Mapper

Maps IFC equipment and fixture data to room schedule fixtures section.
Handles equipment by discipline, connections, and room-specific fixtures.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from ..data.space_model import SpaceData
from ..parsers.ns8360_name_parser import NS8360NameParser
from ..mappers.ns3940_classifier import NS3940Classifier


@dataclass
class ConnectionData:
    """Equipment connection requirements."""
    
    power: Optional[bool] = None
    data: Optional[bool] = None
    water: Optional[bool] = None
    drain: Optional[bool] = None
    vent: Optional[bool] = None
    gas: Optional[bool] = None
    compressed_air: Optional[bool] = None
    fire_suppression: Optional[bool] = None
    security: Optional[bool] = None
    notes: Optional[str] = None


@dataclass
class FixtureData:
    """Individual fixture/equipment data."""
    
    discipline: str  # ARK, RIV, RIE, RIB, RIA, RIBr, Annet
    type: Optional[str] = None
    id: Optional[str] = None
    description: Optional[str] = None
    mounting_height_m: Optional[float] = None
    location_xyz_m: Dict[str, Optional[float]] = None
    connections: ConnectionData = None
    supplier: Optional[str] = None
    product_code: Optional[str] = None
    epd_reference: Optional[str] = None
    remarks: Optional[str] = None
    quantity: int = 1
    power_consumption_W: Optional[float] = None
    water_flow_l_min: Optional[float] = None
    air_flow_m3h: Optional[float] = None
    
    def __post_init__(self):
        if self.location_xyz_m is None:
            self.location_xyz_m = {"x": None, "y": None, "z": None}
        if self.connections is None:
            self.connections = ConnectionData()


@dataclass
class FixturesData:
    """Complete fixtures data for a space."""
    
    fixtures: List[FixtureData]
    total_power_consumption_W: Optional[float] = None
    total_water_flow_l_min: Optional[float] = None
    total_air_flow_m3h: Optional[float] = None
    last_updated: datetime = None
    
    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.now()
        
        # Calculate totals
        self.total_power_consumption_W = sum(
            f.power_consumption_W or 0 for f in self.fixtures
        )
        self.total_water_flow_l_min = sum(
            f.water_flow_l_min or 0 for f in self.fixtures
        )
        self.total_air_flow_m3h = sum(
            f.air_flow_m3h or 0 for f in self.fixtures
        )


class FixturesMapper:
    """Maps IFC data to fixtures section."""
    
    def __init__(self):
        """Initialize the fixtures mapper."""
        self.name_parser = NS8360NameParser()
        self.classifier = NS3940Classifier()
    
    def extract_fixtures(self, space: SpaceData) -> FixturesData:
        """
        Extract fixtures from space data.
        
        Args:
            space: SpaceData to extract fixtures from
            
        Returns:
            FixturesData with extracted fixture information
        """
        # Get room type for default fixtures
        room_type = self._get_room_type(space)
        
        # Extract fixtures from space relationships
        fixtures = self._extract_fixtures_from_relationships(space, room_type)
        
        # Add room-specific fixtures based on type
        room_fixtures = self._get_room_type_fixtures(room_type)
        fixtures.extend(room_fixtures)
        
        return FixturesData(fixtures=fixtures)
    
    def map_equipment_by_discipline(self, space: SpaceData) -> Dict[str, List[FixtureData]]:
        """
        Map equipment by discipline.
        
        Args:
            space: SpaceData to analyze
            
        Returns:
            Dictionary of fixtures grouped by discipline
        """
        fixtures = self.extract_fixtures(space)
        
        # Group by discipline
        by_discipline = {}
        for fixture in fixtures.fixtures:
            discipline = fixture.discipline
            if discipline not in by_discipline:
                by_discipline[discipline] = []
            by_discipline[discipline].append(fixture)
        
        return by_discipline
    
    def infer_equipment_from_room_type(self, room_type: str) -> List[FixtureData]:
        """
        Infer equipment requirements from room type.
        
        Args:
            room_type: NS 3940 room type code
            
        Returns:
            List of inferred FixtureData objects
        """
        return self._get_room_type_fixtures(room_type)
    
    def map_connection_requirements(self, fixture_type: str) -> ConnectionData:
        """
        Map connection requirements for fixture type.
        
        Args:
            fixture_type: Type of fixture/equipment
            
        Returns:
            ConnectionData with connection requirements
        """
        connection_map = {
            "Lighting": ConnectionData(power=True, data=False, water=False, drain=False, vent=False),
            "Power Outlet": ConnectionData(power=True, data=False, water=False, drain=False, vent=False),
            "Data Outlet": ConnectionData(power=True, data=True, water=False, drain=False, vent=False),
            "Washbasin": ConnectionData(power=False, data=False, water=True, drain=True, vent=False),
            "WC": ConnectionData(power=False, data=False, water=True, drain=True, vent=False),
            "Shower": ConnectionData(power=False, data=False, water=True, drain=True, vent=False),
            "Bathtub": ConnectionData(power=False, data=False, water=True, drain=True, vent=False),
            "Kitchen Sink": ConnectionData(power=False, data=False, water=True, drain=True, vent=False),
            "Dishwasher": ConnectionData(power=True, data=False, water=True, drain=True, vent=False),
            "Washing Machine": ConnectionData(power=True, data=False, water=True, drain=True, vent=False),
            "Ventilation Fan": ConnectionData(power=True, data=False, water=False, drain=False, vent=True),
            "Heating Radiator": ConnectionData(power=False, data=False, water=True, drain=False, vent=False),
            "Air Conditioning": ConnectionData(power=True, data=False, water=False, drain=False, vent=True),
            "Fire Alarm": ConnectionData(power=True, data=True, water=False, drain=False, vent=False),
            "Emergency Lighting": ConnectionData(power=True, data=False, water=False, drain=False, vent=False),
            "Cleaning Socket": ConnectionData(power=True, data=False, water=False, drain=False, vent=False)
        }
        
        return connection_map.get(fixture_type, ConnectionData())
    
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
    
    def _extract_fixtures_from_relationships(self, space: SpaceData, room_type: str) -> List[FixtureData]:
        """Extract fixtures from space relationships."""
        fixtures = []
        
        # Look for contained elements in space relationships
        if space.relationships:
            for relationship in space.relationships:
                if relationship.relationship_type == "IfcRelContainedInSpatialStructure":
                    # This would contain equipment/fixtures
                    # For now, we'll add some basic fixtures based on room type
                    pass
        
        return fixtures
    
    def _get_room_type_fixtures(self, room_type: str) -> List[FixtureData]:
        """Get default fixtures for room type."""
        defaults = {
            "111": [  # Oppholdsrom
                FixtureData(
                    discipline="RIE",
                    type="Lighting",
                    description="General lighting",
                    mounting_height_m=2.4,
                    connections=self.map_connection_requirements("Lighting"),
                    power_consumption_W=50.0
                ),
                FixtureData(
                    discipline="RIE",
                    type="Power Outlet",
                    description="General power outlet",
                    mounting_height_m=0.3,
                    connections=self.map_connection_requirements("Power Outlet"),
                    quantity=8
                ),
                FixtureData(
                    discipline="RIE",
                    type="Data Outlet",
                    description="Data/network outlet",
                    mounting_height_m=0.3,
                    connections=self.map_connection_requirements("Data Outlet"),
                    quantity=2
                ),
                FixtureData(
                    discipline="RIE",
                    type="Cleaning Socket",
                    description="Cleaning power socket",
                    mounting_height_m=0.3,
                    connections=self.map_connection_requirements("Cleaning Socket"),
                    quantity=1
                ),
                FixtureData(
                    discipline="RIE",
                    type="Emergency Lighting",
                    description="Emergency lighting",
                    mounting_height_m=2.4,
                    connections=self.map_connection_requirements("Emergency Lighting"),
                    power_consumption_W=10.0
                )
            ],
            "130": [  # Våtrom
                FixtureData(
                    discipline="RIE",
                    type="Lighting",
                    description="Bathroom lighting",
                    mounting_height_m=2.4,
                    connections=self.map_connection_requirements("Lighting"),
                    power_consumption_W=60.0
                ),
                FixtureData(
                    discipline="RIE",
                    type="Power Outlet",
                    description="Bathroom power outlet",
                    mounting_height_m=1.2,
                    connections=self.map_connection_requirements("Power Outlet"),
                    quantity=4
                ),
                FixtureData(
                    discipline="RIE",
                    type="Ventilation Fan",
                    description="Bathroom ventilation",
                    mounting_height_m=2.4,
                    connections=self.map_connection_requirements("Ventilation Fan"),
                    power_consumption_W=30.0,
                    air_flow_m3h=60.0
                ),
                FixtureData(
                    discipline="RIV",
                    type="Washbasin",
                    description="Washbasin with tap",
                    mounting_height_m=0.8,
                    connections=self.map_connection_requirements("Washbasin"),
                    water_flow_l_min=6.0
                ),
                FixtureData(
                    discipline="RIV",
                    type="WC",
                    description="Toilet",
                    mounting_height_m=0.4,
                    connections=self.map_connection_requirements("WC"),
                    water_flow_l_min=6.0
                ),
                FixtureData(
                    discipline="RIV",
                    type="Shower",
                    description="Shower with mixer",
                    mounting_height_m=2.0,
                    connections=self.map_connection_requirements("Shower"),
                    water_flow_l_min=10.0
                ),
                FixtureData(
                    discipline="RIE",
                    type="Emergency Lighting",
                    description="Emergency lighting",
                    mounting_height_m=2.4,
                    connections=self.map_connection_requirements("Emergency Lighting"),
                    power_consumption_W=10.0
                )
            ],
            "131": [  # WC
                FixtureData(
                    discipline="RIE",
                    type="Lighting",
                    description="WC lighting",
                    mounting_height_m=2.4,
                    connections=self.map_connection_requirements("Lighting"),
                    power_consumption_W=40.0
                ),
                FixtureData(
                    discipline="RIE",
                    type="Power Outlet",
                    description="WC power outlet",
                    mounting_height_m=1.2,
                    connections=self.map_connection_requirements("Power Outlet"),
                    quantity=2
                ),
                FixtureData(
                    discipline="RIE",
                    type="Ventilation Fan",
                    description="WC ventilation",
                    mounting_height_m=2.4,
                    connections=self.map_connection_requirements("Ventilation Fan"),
                    power_consumption_W=20.0,
                    air_flow_m3h=30.0
                ),
                FixtureData(
                    discipline="RIV",
                    type="Washbasin",
                    description="Washbasin with tap",
                    mounting_height_m=0.8,
                    connections=self.map_connection_requirements("Washbasin"),
                    water_flow_l_min=6.0
                ),
                FixtureData(
                    discipline="RIV",
                    type="WC",
                    description="Toilet",
                    mounting_height_m=0.4,
                    connections=self.map_connection_requirements("WC"),
                    water_flow_l_min=6.0
                ),
                FixtureData(
                    discipline="RIE",
                    type="Emergency Lighting",
                    description="Emergency lighting",
                    mounting_height_m=2.4,
                    connections=self.map_connection_requirements("Emergency Lighting"),
                    power_consumption_W=10.0
                )
            ],
            "132": [  # Baderom
                FixtureData(
                    discipline="RIE",
                    type="Lighting",
                    description="Bathroom lighting",
                    mounting_height_m=2.4,
                    connections=self.map_connection_requirements("Lighting"),
                    power_consumption_W=80.0
                ),
                FixtureData(
                    discipline="RIE",
                    type="Power Outlet",
                    description="Bathroom power outlet",
                    mounting_height_m=1.2,
                    connections=self.map_connection_requirements("Power Outlet"),
                    quantity=4
                ),
                FixtureData(
                    discipline="RIE",
                    type="Ventilation Fan",
                    description="Bathroom ventilation",
                    mounting_height_m=2.4,
                    connections=self.map_connection_requirements("Ventilation Fan"),
                    power_consumption_W=30.0,
                    air_flow_m3h=60.0
                ),
                FixtureData(
                    discipline="RIV",
                    type="Washbasin",
                    description="Washbasin with tap",
                    mounting_height_m=0.8,
                    connections=self.map_connection_requirements("Washbasin"),
                    water_flow_l_min=6.0
                ),
                FixtureData(
                    discipline="RIV",
                    type="WC",
                    description="Toilet",
                    mounting_height_m=0.4,
                    connections=self.map_connection_requirements("WC"),
                    water_flow_l_min=6.0
                ),
                FixtureData(
                    discipline="RIV",
                    type="Bathtub",
                    description="Bathtub with mixer",
                    mounting_height_m=0.6,
                    connections=self.map_connection_requirements("Bathtub"),
                    water_flow_l_min=15.0
                ),
                FixtureData(
                    discipline="RIV",
                    type="Shower",
                    description="Shower with mixer",
                    mounting_height_m=2.0,
                    connections=self.map_connection_requirements("Shower"),
                    water_flow_l_min=10.0
                ),
                FixtureData(
                    discipline="RIE",
                    type="Emergency Lighting",
                    description="Emergency lighting",
                    mounting_height_m=2.4,
                    connections=self.map_connection_requirements("Emergency Lighting"),
                    power_consumption_W=10.0
                )
            ],
            "140": [  # Kjøkken
                FixtureData(
                    discipline="RIE",
                    type="Lighting",
                    description="Kitchen lighting",
                    mounting_height_m=2.4,
                    connections=self.map_connection_requirements("Lighting"),
                    power_consumption_W=100.0
                ),
                FixtureData(
                    discipline="RIE",
                    type="Power Outlet",
                    description="Kitchen power outlet",
                    mounting_height_m=1.2,
                    connections=self.map_connection_requirements("Power Outlet"),
                    quantity=12
                ),
                FixtureData(
                    discipline="RIE",
                    type="Data Outlet",
                    description="Kitchen data outlet",
                    mounting_height_m=1.2,
                    connections=self.map_connection_requirements("Data Outlet"),
                    quantity=2
                ),
                FixtureData(
                    discipline="RIE",
                    type="Ventilation Fan",
                    description="Kitchen ventilation",
                    mounting_height_m=2.4,
                    connections=self.map_connection_requirements("Ventilation Fan"),
                    power_consumption_W=100.0,
                    air_flow_m3h=120.0
                ),
                FixtureData(
                    discipline="RIV",
                    type="Kitchen Sink",
                    description="Kitchen sink with mixer",
                    mounting_height_m=0.9,
                    connections=self.map_connection_requirements("Kitchen Sink"),
                    water_flow_l_min=8.0
                ),
                FixtureData(
                    discipline="RIV",
                    type="Dishwasher",
                    description="Dishwasher",
                    mounting_height_m=0.8,
                    connections=self.map_connection_requirements("Dishwasher"),
                    power_consumption_W=2000.0,
                    water_flow_l_min=10.0
                ),
                FixtureData(
                    discipline="RIV",
                    type="Washing Machine",
                    description="Washing machine",
                    mounting_height_m=0.8,
                    connections=self.map_connection_requirements("Washing Machine"),
                    power_consumption_W=2500.0,
                    water_flow_l_min=12.0
                ),
                FixtureData(
                    discipline="RIE",
                    type="Emergency Lighting",
                    description="Emergency lighting",
                    mounting_height_m=2.4,
                    connections=self.map_connection_requirements("Emergency Lighting"),
                    power_consumption_W=10.0
                )
            ]
        }
        
        return defaults.get(room_type, defaults["111"])  # Default to oppholdsrom


# Example usage and testing
if __name__ == "__main__":
    mapper = FixturesMapper()
    
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
    
    print("Fixtures Mapper Test:")
    print("=" * 50)
    
    # Test fixture extraction
    fixtures = mapper.extract_fixtures(sample_space)
    print(f"Total fixtures: {len(fixtures.fixtures)}")
    print(f"Total power consumption: {fixtures.total_power_consumption_W}W")
    print(f"Total water flow: {fixtures.total_water_flow_l_min} l/min")
    
    # Test by discipline
    by_discipline = mapper.map_equipment_by_discipline(sample_space)
    for discipline, fixture_list in by_discipline.items():
        print(f"{discipline}: {len(fixture_list)} fixtures")
    
    # Test room type fixtures
    kitchen_fixtures = mapper.infer_equipment_from_room_type("140")
    print(f"\\nKitchen fixtures: {len(kitchen_fixtures)}")
    for fixture in kitchen_fixtures:
        print(f"  - {fixture.type}: {fixture.description}")
    
    # Test connection requirements
    connections = mapper.map_connection_requirements("Dishwasher")
    print(f"\\nDishwasher connections:")
    print(f"  Power: {connections.power}")
    print(f"  Water: {connections.water}")
    print(f"  Drain: {connections.drain}")
