"""
Interfaces Mapper

Maps IFC data to interfaces section including trade boundaries, 
adjacent rooms, trade interfaces, and sequence coordination.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from ..data.space_model import SpaceData
from ..parsers.ns8360_name_parser import NS8360NameParser
from ..mappers.ns3940_classifier import NS3940Classifier


class TradeType(Enum):
    """Types of trades."""
    ARK = "ARK"  # Architecture
    RIV = "RIV"  # Civil/Structural
    RIE = "RIE"  # Electrical
    RIB = "RIB"  # HVAC
    RIA = "RIA"  # Plumbing
    RIBr = "RIBr"  # Fire Safety
    OTHER = "Annet"


class InterfaceType(Enum):
    """Types of interfaces."""
    SPATIAL = "spatial"
    STRUCTURAL = "structural"
    MEP = "mep"
    FIRE_SAFETY = "fire_safety"
    ACCESSIBILITY = "accessibility"
    ACOUSTIC = "acoustic"
    THERMAL = "thermal"


@dataclass
class AdjacentRoom:
    """Adjacent room information."""
    
    room_id: str
    room_name: str
    room_type: str
    shared_boundary_length_m: Optional[float] = None
    interface_type: InterfaceType = InterfaceType.SPATIAL
    fire_compartment: Optional[str] = None
    acoustic_rating: Optional[str] = None
    thermal_interface: Optional[bool] = None
    notes: Optional[str] = None


@dataclass
class TradeInterface:
    """Trade interface information."""
    
    from_trade: TradeType
    to_trade: TradeType
    scope_boundary: str
    interface_description: str
    critical: bool = False
    sequence_dependency: Optional[str] = None
    coordination_required: bool = True
    handover_requirements: List[str] = None
    quality_requirements: List[str] = None
    notes: Optional[str] = None
    
    def __post_init__(self):
        if self.handover_requirements is None:
            self.handover_requirements = []
        if self.quality_requirements is None:
            self.quality_requirements = []


@dataclass
class SequenceNote:
    """Sequence coordination note."""
    
    phase: str
    description: str
    dependencies: List[str] = None
    constraints: List[str] = None
    responsible_trade: TradeType = None
    critical_path: bool = False
    notes: Optional[str] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.constraints is None:
            self.constraints = []


@dataclass
class InterfacesData:
    """Complete interfaces data for a space."""
    
    adjacent_rooms: List[AdjacentRoom]
    trade_interfaces: List[TradeInterface]
    sequence_notes: List[SequenceNote]
    last_updated: datetime = None
    
    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.now()


class InterfacesMapper:
    """Maps IFC data to interfaces section."""
    
    def __init__(self):
        """Initialize the interfaces mapper."""
        self.name_parser = NS8360NameParser()
        self.classifier = NS3940Classifier()
    
    def extract_interfaces(self, space: SpaceData) -> InterfacesData:
        """
        Extract interfaces from space data.
        
        Args:
            space: SpaceData to extract interfaces from
            
        Returns:
            InterfacesData with extracted interface information
        """
        # Get room type for default requirements
        room_type = self._get_room_type(space)
        
        # Extract adjacent rooms
        adjacent_rooms = self._extract_adjacent_rooms(space, room_type)
        
        # Extract trade interfaces
        trade_interfaces = self._extract_trade_interfaces(space, room_type)
        
        # Extract sequence notes
        sequence_notes = self._extract_sequence_notes(space, room_type)
        
        return InterfacesData(
            adjacent_rooms=adjacent_rooms,
            trade_interfaces=trade_interfaces,
            sequence_notes=sequence_notes
        )
    
    def identify_critical_interfaces(self, space: SpaceData) -> List[TradeInterface]:
        """
        Identify critical interfaces for space.
        
        Args:
            space: SpaceData to analyze
            
        Returns:
            List of critical trade interfaces
        """
        interfaces_data = self.extract_interfaces(space)
        return [ti for ti in interfaces_data.trade_interfaces if ti.critical]
    
    def generate_coordination_plan(self, space: SpaceData) -> str:
        """
        Generate a coordination plan for the space.
        
        Args:
            space: SpaceData to generate plan for
            
        Returns:
            Coordination plan as string
        """
        room_type = self._get_room_type(space)
        interfaces_data = self.extract_interfaces(space)
        
        plan = f"Coordination Plan for {space.name}\n"
        plan += f"Room Type: {room_type}\n"
        plan += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        
        plan += "ADJACENT ROOMS:\n"
        for i, room in enumerate(interfaces_data.adjacent_rooms, 1):
            plan += f"{i}. {room.room_name} ({room.room_type})\n"
            plan += f"   Interface: {room.interface_type.value}\n"
            if room.shared_boundary_length_m:
                plan += f"   Boundary: {room.shared_boundary_length_m}m\n"
            if room.notes:
                plan += f"   Notes: {room.notes}\n"
            plan += "\n"
        
        plan += "TRADE INTERFACES:\n"
        for i, interface in enumerate(interfaces_data.trade_interfaces, 1):
            plan += f"{i}. {interface.from_trade.value} -> {interface.to_trade.value}\n"
            plan += f"   Scope: {interface.scope_boundary}\n"
            plan += f"   Description: {interface.interface_description}\n"
            if interface.critical:
                plan += f"   CRITICAL\n"
            if interface.coordination_required:
                plan += f"   Coordination Required\n"
            plan += "\n"
        
        plan += "SEQUENCE NOTES:\n"
        for i, note in enumerate(interfaces_data.sequence_notes, 1):
            plan += f"{i}. {note.phase}: {note.description}\n"
            if note.dependencies:
                plan += f"   Dependencies: {', '.join(note.dependencies)}\n"
            if note.constraints:
                plan += f"   Constraints: {', '.join(note.constraints)}\n"
            if note.critical_path:
                plan += f"   CRITICAL PATH\n"
            plan += "\n"
        
        return plan
    
    def validate_interface_compliance(self, space: SpaceData) -> Dict[str, Any]:
        """
        Validate interface compliance for space.
        
        Args:
            space: SpaceData to validate
            
        Returns:
            Dictionary with compliance status and issues
        """
        interfaces_data = self.extract_interfaces(space)
        
        compliance = {
            "compliant": True,
            "issues": [],
            "warnings": [],
            "adjacent_rooms": len(interfaces_data.adjacent_rooms),
            "trade_interfaces": len(interfaces_data.trade_interfaces),
            "critical_interfaces": len([ti for ti in interfaces_data.trade_interfaces if ti.critical])
        }
        
        # Check for missing coordination
        missing_coordination = [ti for ti in interfaces_data.trade_interfaces 
                               if ti.coordination_required and not ti.interface_description]
        if missing_coordination:
            compliance["issues"].append(f"{len(missing_coordination)} interfaces missing coordination details")
            compliance["compliant"] = False
        
        # Check for critical interfaces without handover requirements
        critical_no_handover = [ti for ti in interfaces_data.trade_interfaces 
                               if ti.critical and not ti.handover_requirements]
        if critical_no_handover:
            compliance["warnings"].append(f"{len(critical_no_handover)} critical interfaces missing handover requirements")
        
        # Check for missing sequence dependencies
        missing_dependencies = [sn for sn in interfaces_data.sequence_notes 
                               if not sn.dependencies and sn.critical_path]
        if missing_dependencies:
            compliance["warnings"].append(f"{len(missing_dependencies)} critical path items missing dependencies")
        
        return compliance
    
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
    
    def _extract_adjacent_rooms(self, space: SpaceData, room_type: str) -> List[AdjacentRoom]:
        """Extract adjacent rooms for space."""
        # Look for adjacent room properties in space
        adjacent_rooms = []
        
        # Check if space has adjacent room properties
        if space.quantities:
            # Could extract from property sets or relationships
            pass
        
        # Apply defaults based on room type
        defaults = self._get_room_type_defaults(room_type)
        adjacent_rooms_data = defaults.get("adjacent_rooms", [])
        
        for room_data in adjacent_rooms_data:
            adjacent_rooms.append(AdjacentRoom(
                room_id=room_data["room_id"],
                room_name=room_data["room_name"],
                room_type=room_data["room_type"],
                shared_boundary_length_m=room_data.get("shared_boundary_length_m"),
                interface_type=InterfaceType(room_data.get("interface_type", "spatial")),
                fire_compartment=room_data.get("fire_compartment"),
                acoustic_rating=room_data.get("acoustic_rating"),
                thermal_interface=room_data.get("thermal_interface"),
                notes=room_data.get("notes")
            ))
        
        return adjacent_rooms
    
    def _extract_trade_interfaces(self, space: SpaceData, room_type: str) -> List[TradeInterface]:
        """Extract trade interfaces for space."""
        # Look for trade interface properties in space
        trade_interfaces = []
        
        # Check if space has trade interface properties
        if space.quantities:
            # Could extract from property sets
            pass
        
        # Apply defaults based on room type
        defaults = self._get_room_type_defaults(room_type)
        trade_interfaces_data = defaults.get("trade_interfaces", [])
        
        for interface_data in trade_interfaces_data:
            trade_interfaces.append(TradeInterface(
                from_trade=TradeType(interface_data["from_trade"]),
                to_trade=TradeType(interface_data["to_trade"]),
                scope_boundary=interface_data["scope_boundary"],
                interface_description=interface_data["interface_description"],
                critical=interface_data.get("critical", False),
                sequence_dependency=interface_data.get("sequence_dependency"),
                coordination_required=interface_data.get("coordination_required", True),
                handover_requirements=interface_data.get("handover_requirements", []),
                quality_requirements=interface_data.get("quality_requirements", []),
                notes=interface_data.get("notes")
            ))
        
        return trade_interfaces
    
    def _extract_sequence_notes(self, space: SpaceData, room_type: str) -> List[SequenceNote]:
        """Extract sequence notes for space."""
        # Look for sequence note properties in space
        sequence_notes = []
        
        # Check if space has sequence note properties
        if space.quantities:
            # Could extract from property sets
            pass
        
        # Apply defaults based on room type
        defaults = self._get_room_type_defaults(room_type)
        sequence_notes_data = defaults.get("sequence_notes", [])
        
        for note_data in sequence_notes_data:
            sequence_notes.append(SequenceNote(
                phase=note_data["phase"],
                description=note_data["description"],
                dependencies=note_data.get("dependencies", []),
                constraints=note_data.get("constraints", []),
                responsible_trade=TradeType(note_data["responsible_trade"]) if note_data.get("responsible_trade") else None,
                critical_path=note_data.get("critical_path", False),
                notes=note_data.get("notes")
            ))
        
        return sequence_notes
    
    def _get_room_type_defaults(self, room_type: str) -> Dict[str, Any]:
        """Get default interface requirements for room type."""
        defaults = {
            "111": {  # Oppholdsrom
                "adjacent_rooms": [
                    {
                        "room_id": "adj_001",
                        "room_name": "Korridor",
                        "room_type": "111",
                        "shared_boundary_length_m": 2.0,
                        "interface_type": "spatial",
                        "fire_compartment": "Same",
                        "acoustic_rating": "C",
                        "thermal_interface": True,
                        "notes": "Main circulation route"
                    }
                ],
                "trade_interfaces": [
                    {
                        "from_trade": "ARK",
                        "to_trade": "RIV",
                        "scope_boundary": "Wall/floor interface",
                        "interface_description": "Coordinate wall openings and floor penetrations",
                        "critical": True,
                        "sequence_dependency": "Structure before finishes",
                        "coordination_required": True,
                        "handover_requirements": ["As-built drawings", "Penetration schedule"],
                        "quality_requirements": ["Opening dimensions", "Fire rating compliance"]
                    },
                    {
                        "from_trade": "RIV",
                        "to_trade": "RIE",
                        "scope_boundary": "Electrical installations",
                        "interface_description": "Coordinate electrical outlets and lighting",
                        "critical": False,
                        "sequence_dependency": "Finishes before electrical",
                        "coordination_required": True,
                        "handover_requirements": ["Electrical drawings", "Load calculations"],
                        "quality_requirements": ["Outlet locations", "Cable routing"]
                    }
                ],
                "sequence_notes": [
                    {
                        "phase": "Utførelse",
                        "description": "Complete structural work before finishes",
                        "dependencies": ["Foundation", "Structure"],
                        "constraints": ["Weather protection", "Access routes"],
                        "responsible_trade": "RIV",
                        "critical_path": True
                    }
                ]
            },
            "130": {  # Våtrom
                "adjacent_rooms": [
                    {
                        "room_id": "adj_001",
                        "room_name": "Korridor",
                        "room_type": "111",
                        "shared_boundary_length_m": 1.5,
                        "interface_type": "spatial",
                        "fire_compartment": "Same",
                        "acoustic_rating": "C",
                        "thermal_interface": True,
                        "notes": "Main circulation route"
                    }
                ],
                "trade_interfaces": [
                    {
                        "from_trade": "RIV",
                        "to_trade": "RIA",
                        "scope_boundary": "Waterproofing and plumbing",
                        "interface_description": "Coordinate waterproofing with plumbing penetrations",
                        "critical": True,
                        "sequence_dependency": "Waterproofing before plumbing",
                        "coordination_required": True,
                        "handover_requirements": ["Waterproofing certificate", "Plumbing test results"],
                        "quality_requirements": ["Waterproofing continuity", "Penetration sealing"]
                    },
                    {
                        "from_trade": "RIA",
                        "to_trade": "RIE",
                        "scope_boundary": "Electrical in wet areas",
                        "interface_description": "Coordinate electrical installations in wet areas",
                        "critical": True,
                        "sequence_dependency": "Electrical after waterproofing",
                        "coordination_required": True,
                        "handover_requirements": ["Electrical certificates", "IP rating compliance"],
                        "quality_requirements": ["IP65 rating", "GFCI protection"]
                    }
                ],
                "sequence_notes": [
                    {
                        "phase": "Utførelse",
                        "description": "Complete waterproofing before any other work",
                        "dependencies": ["Structure", "Plumbing rough-in"],
                        "constraints": ["Weather protection", "Access routes"],
                        "responsible_trade": "RIV",
                        "critical_path": True
                    }
                ]
            },
            "131": {  # WC
                "adjacent_rooms": [
                    {
                        "room_id": "adj_001",
                        "room_name": "Korridor",
                        "room_type": "111",
                        "shared_boundary_length_m": 1.0,
                        "interface_type": "spatial",
                        "fire_compartment": "Same",
                        "acoustic_rating": "C",
                        "thermal_interface": True,
                        "notes": "Main circulation route"
                    }
                ],
                "trade_interfaces": [
                    {
                        "from_trade": "RIV",
                        "to_trade": "RIA",
                        "scope_boundary": "Waterproofing and plumbing",
                        "interface_description": "Coordinate waterproofing with plumbing penetrations",
                        "critical": True,
                        "sequence_dependency": "Waterproofing before plumbing",
                        "coordination_required": True,
                        "handover_requirements": ["Waterproofing certificate", "Plumbing test results"],
                        "quality_requirements": ["Waterproofing continuity", "Penetration sealing"]
                    }
                ],
                "sequence_notes": [
                    {
                        "phase": "Utførelse",
                        "description": "Complete waterproofing before any other work",
                        "dependencies": ["Structure", "Plumbing rough-in"],
                        "constraints": ["Weather protection", "Access routes"],
                        "responsible_trade": "RIV",
                        "critical_path": True
                    }
                ]
            },
            "132": {  # Baderom
                "adjacent_rooms": [
                    {
                        "room_id": "adj_001",
                        "room_name": "Korridor",
                        "room_type": "111",
                        "shared_boundary_length_m": 1.5,
                        "interface_type": "spatial",
                        "fire_compartment": "Same",
                        "acoustic_rating": "C",
                        "thermal_interface": True,
                        "notes": "Main circulation route"
                    }
                ],
                "trade_interfaces": [
                    {
                        "from_trade": "RIV",
                        "to_trade": "RIA",
                        "scope_boundary": "Waterproofing and plumbing",
                        "interface_description": "Coordinate waterproofing with plumbing penetrations",
                        "critical": True,
                        "sequence_dependency": "Waterproofing before plumbing",
                        "coordination_required": True,
                        "handover_requirements": ["Waterproofing certificate", "Plumbing test results"],
                        "quality_requirements": ["Waterproofing continuity", "Penetration sealing"]
                    },
                    {
                        "from_trade": "RIA",
                        "to_trade": "RIE",
                        "scope_boundary": "Electrical in wet areas",
                        "interface_description": "Coordinate electrical installations in wet areas",
                        "critical": True,
                        "sequence_dependency": "Electrical after waterproofing",
                        "coordination_required": True,
                        "handover_requirements": ["Electrical certificates", "IP rating compliance"],
                        "quality_requirements": ["IP65 rating", "GFCI protection"]
                    }
                ],
                "sequence_notes": [
                    {
                        "phase": "Utførelse",
                        "description": "Complete waterproofing before any other work",
                        "dependencies": ["Structure", "Plumbing rough-in"],
                        "constraints": ["Weather protection", "Access routes"],
                        "responsible_trade": "RIV",
                        "critical_path": True
                    }
                ]
            },
            "140": {  # Kjøkken
                "adjacent_rooms": [
                    {
                        "room_id": "adj_001",
                        "room_name": "Korridor",
                        "room_type": "111",
                        "shared_boundary_length_m": 2.5,
                        "interface_type": "spatial",
                        "fire_compartment": "Same",
                        "acoustic_rating": "C",
                        "thermal_interface": True,
                        "notes": "Main circulation route"
                    }
                ],
                "trade_interfaces": [
                    {
                        "from_trade": "RIV",
                        "to_trade": "RIA",
                        "scope_boundary": "Kitchen plumbing and drainage",
                        "interface_description": "Coordinate kitchen plumbing with finishes",
                        "critical": True,
                        "sequence_dependency": "Plumbing before finishes",
                        "coordination_required": True,
                        "handover_requirements": ["Plumbing test results", "Drainage test results"],
                        "quality_requirements": ["Water pressure", "Drainage flow"]
                    },
                    {
                        "from_trade": "RIA",
                        "to_trade": "RIE",
                        "scope_boundary": "Kitchen electrical and appliances",
                        "interface_description": "Coordinate electrical for kitchen appliances",
                        "critical": True,
                        "sequence_dependency": "Electrical after plumbing",
                        "coordination_required": True,
                        "handover_requirements": ["Electrical certificates", "Appliance specifications"],
                        "quality_requirements": ["Load calculations", "Circuit protection"]
                    }
                ],
                "sequence_notes": [
                    {
                        "phase": "Utførelse",
                        "description": "Complete plumbing and electrical before finishes",
                        "dependencies": ["Structure", "Plumbing rough-in", "Electrical rough-in"],
                        "constraints": ["Appliance delivery", "Access routes"],
                        "responsible_trade": "RIV",
                        "critical_path": True
                    }
                ]
            }
        }
        
        return defaults.get(room_type, defaults["111"])  # Default to oppholdsrom


# Example usage and testing
if __name__ == "__main__":
    mapper = InterfacesMapper()
    
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
    
    print("Interfaces Mapper Test:")
    print("=" * 50)
    
    # Test interfaces extraction
    interfaces = mapper.extract_interfaces(sample_space)
    print(f"Adjacent rooms: {len(interfaces.adjacent_rooms)}")
    print(f"Trade interfaces: {len(interfaces.trade_interfaces)}")
    print(f"Sequence notes: {len(interfaces.sequence_notes)}")
    
    # Test critical interfaces
    critical = mapper.identify_critical_interfaces(sample_space)
    print(f"\\nCritical interfaces: {len(critical)}")
    
    # Test coordination plan
    plan = mapper.generate_coordination_plan(sample_space)
    print(f"\\nCoordination Plan:")
    print(plan[:500] + "..." if len(plan) > 500 else plan)
    
    # Test compliance validation
    compliance = mapper.validate_interface_compliance(sample_space)
    print(f"\\nCompliance Status:")
    print(f"Compliant: {compliance['compliant']}")
    print(f"Issues: {compliance['issues']}")
    print(f"Warnings: {compliance['warnings']}")
