"""
Logistics Mapper

Maps IFC data to logistics section including site planning, 
access routes, work hours constraints, and SHA (Safety, Health, Environment) planning.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from ..data.space_model import SpaceData
from ..parsers.ns8360_name_parser import NS8360NameParser
from ..mappers.ns3940_classifier import NS3940Classifier


class WasteFraction(Enum):
    """Types of waste fractions."""
    WOOD = "Treverk"
    METAL = "Metall"
    PLASTIC = "Plast"
    REST = "Rest"
    PAPER_CARDBOARD = "Papir/Kartong"
    HAZARDOUS = "Farlig avfall"


class PPE(Enum):
    """Types of Personal Protective Equipment."""
    HELMET = "Hjelm"
    SAFETY_SHOES = "Vernesko"
    SAFETY_GLASSES = "Vernebriller"
    GLOVES = "Hansker"


class Permit(Enum):
    """Types of permits required."""
    HOT_WORK = "Varmt arbeid"
    SCAFFOLDING = "Stillaser"
    HEIGHT_WORK = "Arbeid i høyden"


@dataclass
class AccessRoute:
    """Access route information."""
    
    route_id: str
    description: str
    width_m: Optional[float] = None
    height_m: Optional[float] = None
    load_capacity_kg: Optional[float] = None
    restrictions: List[str] = None
    notes: Optional[str] = None
    
    def __post_init__(self):
        if self.restrictions is None:
            self.restrictions = []


@dataclass
class WorkConstraints:
    """Work hour and noise constraints."""
    
    work_hours: Optional[str] = None
    noise_constraints: Optional[str] = None
    cleanliness_requirements: Optional[str] = None
    temperature_requirements: Optional[str] = None
    ventilation_requirements: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class RiggingDrift:
    """Rigging and site facilities."""
    
    site_facilities: List[str] = None
    temporary_utilities: List[str] = None
    material_handling: Dict[str, Any] = None
    storage: Dict[str, Any] = None
    waste_management: Dict[str, Any] = None
    winter_measures: Optional[str] = None
    snow_ice_plan: Optional[str] = None
    
    def __post_init__(self):
        if self.site_facilities is None:
            self.site_facilities = []
        if self.temporary_utilities is None:
            self.temporary_utilities = []
        if self.material_handling is None:
            self.material_handling = {}
        if self.storage is None:
            self.storage = {}
        if self.waste_management is None:
            self.waste_management = {}


@dataclass
class SHAPlan:
    """Safety, Health, Environment plan."""
    
    risk_activities: List[str] = None
    permits_required: List[Permit] = None
    ppe: List[PPE] = None
    sja_required: bool = True
    responsible_roles: List[str] = None
    emergency_procedures: List[str] = None
    environmental_considerations: List[str] = None
    
    def __post_init__(self):
        if self.risk_activities is None:
            self.risk_activities = []
        if self.permits_required is None:
            self.permits_required = []
        if self.ppe is None:
            self.ppe = []
        if self.responsible_roles is None:
            self.responsible_roles = []
        if self.emergency_procedures is None:
            self.emergency_procedures = []
        if self.environmental_considerations is None:
            self.environmental_considerations = []


@dataclass
class LeanTakt:
    """Lean construction and takt planning."""
    
    takt_area_id: Optional[str] = None
    takt_time_days: Optional[int] = None
    sequence: List[str] = None
    constraints: List[str] = None
    handoff_criteria: List[str] = None
    quality_gates: List[str] = None
    notes: Optional[str] = None
    
    def __post_init__(self):
        if self.sequence is None:
            self.sequence = []
        if self.constraints is None:
            self.constraints = []
        if self.handoff_criteria is None:
            self.handoff_criteria = []
        if self.quality_gates is None:
            self.quality_gates = []


@dataclass
class LogisticsData:
    """Complete logistics data for a space."""
    
    access_route: Optional[AccessRoute]
    work_constraints: WorkConstraints
    rigging_drift: RiggingDrift
    sha_plan: SHAPlan
    lean_takt: LeanTakt
    last_updated: datetime = None
    
    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.now()


class LogisticsMapper:
    """Maps IFC data to logistics section."""
    
    def __init__(self):
        """Initialize the logistics mapper."""
        self.name_parser = NS8360NameParser()
        self.classifier = NS3940Classifier()
    
    def extract_logistics(self, space: SpaceData) -> LogisticsData:
        """
        Extract logistics from space data.
        
        Args:
            space: SpaceData to extract logistics from
            
        Returns:
            LogisticsData with extracted logistics information
        """
        # Get room type for default requirements
        room_type = self._get_room_type(space)
        
        # Extract access route
        access_route = self._extract_access_route(space, room_type)
        
        # Extract work constraints
        work_constraints = self._extract_work_constraints(space, room_type)
        
        # Extract rigging drift
        rigging_drift = self._extract_rigging_drift(space, room_type)
        
        # Extract SHA plan
        sha_plan = self._extract_sha_plan(space, room_type)
        
        # Extract lean takt
        lean_takt = self._extract_lean_takt(space, room_type)
        
        return LogisticsData(
            access_route=access_route,
            work_constraints=work_constraints,
            rigging_drift=rigging_drift,
            sha_plan=sha_plan,
            lean_takt=lean_takt
        )
    
    def generate_site_plan(self, space: SpaceData) -> str:
        """
        Generate a site plan for the space.
        
        Args:
            space: SpaceData to generate plan for
            
        Returns:
            Site plan as string
        """
        room_type = self._get_room_type(space)
        logistics_data = self.extract_logistics(space)
        
        plan = f"Site Plan for {space.name}\n"
        plan += f"Room Type: {room_type}\n"
        plan += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        
        if logistics_data.access_route:
            plan += "ACCESS ROUTE:\n"
            plan += f"Route: {logistics_data.access_route.description}\n"
            if logistics_data.access_route.width_m:
                plan += f"Width: {logistics_data.access_route.width_m}m\n"
            if logistics_data.access_route.height_m:
                plan += f"Height: {logistics_data.access_route.height_m}m\n"
            if logistics_data.access_route.load_capacity_kg:
                plan += f"Load Capacity: {logistics_data.access_route.load_capacity_kg}kg\n"
            plan += "\n"
        
        plan += "WORK CONSTRAINTS:\n"
        if logistics_data.work_constraints.work_hours:
            plan += f"Work Hours: {logistics_data.work_constraints.work_hours}\n"
        if logistics_data.work_constraints.noise_constraints:
            plan += f"Noise Constraints: {logistics_data.work_constraints.noise_constraints}\n"
        if logistics_data.work_constraints.cleanliness_requirements:
            plan += f"Cleanliness: {logistics_data.work_constraints.cleanliness_requirements}\n"
        plan += "\n"
        
        plan += "SITE FACILITIES:\n"
        for facility in logistics_data.rigging_drift.site_facilities:
            plan += f"- {facility}\n"
        plan += "\n"
        
        plan += "SAFETY REQUIREMENTS:\n"
        for ppe in logistics_data.sha_plan.ppe:
            plan += f"- {ppe.value}\n"
        for permit in logistics_data.sha_plan.permits_required:
            plan += f"- {permit.value}\n"
        plan += "\n"
        
        return plan
    
    def validate_logistics_compliance(self, space: SpaceData) -> Dict[str, Any]:
        """
        Validate logistics compliance for space.
        
        Args:
            space: SpaceData to validate
            
        Returns:
            Dictionary with compliance status and issues
        """
        logistics_data = self.extract_logistics(space)
        
        compliance = {
            "compliant": True,
            "issues": [],
            "warnings": [],
            "access_route_defined": logistics_data.access_route is not None,
            "sha_plan_defined": len(logistics_data.sha_plan.risk_activities) > 0,
            "lean_takt_defined": logistics_data.lean_takt.takt_area_id is not None
        }
        
        # Check for missing access route
        if not compliance["access_route_defined"]:
            compliance["issues"].append("No access route defined")
            compliance["compliant"] = False
        
        # Check for missing SHA plan
        if not compliance["sha_plan_defined"]:
            compliance["warnings"].append("No SHA plan defined")
        
        # Check for missing lean takt
        if not compliance["lean_takt_defined"]:
            compliance["warnings"].append("No lean takt plan defined")
        
        # Check for missing PPE
        if not logistics_data.sha_plan.ppe:
            compliance["warnings"].append("No PPE requirements defined")
        
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
    
    def _extract_access_route(self, space: SpaceData, room_type: str) -> Optional[AccessRoute]:
        """Extract access route for space."""
        # Look for access route properties in space
        access_route = None
        
        # Check if space has access route properties
        if space.quantities:
            # Could extract from property sets
            pass
        
        # Apply defaults based on room type
        defaults = self._get_room_type_defaults(room_type)
        access_route_data = defaults.get("access_route")
        
        if access_route_data:
            access_route = AccessRoute(
                route_id=access_route_data["route_id"],
                description=access_route_data["description"],
                width_m=access_route_data.get("width_m"),
                height_m=access_route_data.get("height_m"),
                load_capacity_kg=access_route_data.get("load_capacity_kg"),
                restrictions=access_route_data.get("restrictions", []),
                notes=access_route_data.get("notes")
            )
        
        return access_route
    
    def _extract_work_constraints(self, space: SpaceData, room_type: str) -> WorkConstraints:
        """Extract work constraints for space."""
        # Look for work constraint properties in space
        work_constraints = WorkConstraints()
        
        # Check if space has work constraint properties
        if space.quantities:
            # Could extract from property sets
            pass
        
        # Apply defaults based on room type
        defaults = self._get_room_type_defaults(room_type)
        work_constraints_data = defaults.get("work_constraints", {})
        
        return WorkConstraints(
            work_hours=work_constraints_data.get("work_hours"),
            noise_constraints=work_constraints_data.get("noise_constraints"),
            cleanliness_requirements=work_constraints_data.get("cleanliness_requirements"),
            temperature_requirements=work_constraints_data.get("temperature_requirements"),
            ventilation_requirements=work_constraints_data.get("ventilation_requirements"),
            notes=work_constraints_data.get("notes")
        )
    
    def _extract_rigging_drift(self, space: SpaceData, room_type: str) -> RiggingDrift:
        """Extract rigging drift for space."""
        # Look for rigging drift properties in space
        rigging_drift = RiggingDrift()
        
        # Check if space has rigging drift properties
        if space.quantities:
            # Could extract from property sets
            pass
        
        # Apply defaults based on room type
        defaults = self._get_room_type_defaults(room_type)
        rigging_drift_data = defaults.get("rigging_drift", {})
        
        return RiggingDrift(
            site_facilities=rigging_drift_data.get("site_facilities", []),
            temporary_utilities=rigging_drift_data.get("temporary_utilities", []),
            material_handling=rigging_drift_data.get("material_handling", {}),
            storage=rigging_drift_data.get("storage", {}),
            waste_management=rigging_drift_data.get("waste_management", {}),
            winter_measures=rigging_drift_data.get("winter_measures"),
            snow_ice_plan=rigging_drift_data.get("snow_ice_plan")
        )
    
    def _extract_sha_plan(self, space: SpaceData, room_type: str) -> SHAPlan:
        """Extract SHA plan for space."""
        # Look for SHA plan properties in space
        sha_plan = SHAPlan()
        
        # Check if space has SHA plan properties
        if space.quantities:
            # Could extract from property sets
            pass
        
        # Apply defaults based on room type
        defaults = self._get_room_type_defaults(room_type)
        sha_plan_data = defaults.get("sha_plan", {})
        
        return SHAPlan(
            risk_activities=sha_plan_data.get("risk_activities", []),
            permits_required=[Permit(p) for p in sha_plan_data.get("permits_required", [])],
            ppe=[PPE(p) for p in sha_plan_data.get("ppe", [])],
            sja_required=sha_plan_data.get("sja_required", True),
            responsible_roles=sha_plan_data.get("responsible_roles", []),
            emergency_procedures=sha_plan_data.get("emergency_procedures", []),
            environmental_considerations=sha_plan_data.get("environmental_considerations", [])
        )
    
    def _extract_lean_takt(self, space: SpaceData, room_type: str) -> LeanTakt:
        """Extract lean takt for space."""
        # Look for lean takt properties in space
        lean_takt = LeanTakt()
        
        # Check if space has lean takt properties
        if space.quantities:
            # Could extract from property sets
            pass
        
        # Apply defaults based on room type
        defaults = self._get_room_type_defaults(room_type)
        lean_takt_data = defaults.get("lean_takt", {})
        
        return LeanTakt(
            takt_area_id=lean_takt_data.get("takt_area_id"),
            takt_time_days=lean_takt_data.get("takt_time_days"),
            sequence=lean_takt_data.get("sequence", []),
            constraints=lean_takt_data.get("constraints", []),
            handoff_criteria=lean_takt_data.get("handoff_criteria", []),
            quality_gates=lean_takt_data.get("quality_gates", []),
            notes=lean_takt_data.get("notes")
        )
    
    def _get_room_type_defaults(self, room_type: str) -> Dict[str, Any]:
        """Get default logistics requirements for room type."""
        defaults = {
            "111": {  # Oppholdsrom
                "access_route": {
                    "route_id": "AR-001",
                    "description": "Main corridor access",
                    "width_m": 1.2,
                    "height_m": 2.4,
                    "load_capacity_kg": 500.0,
                    "restrictions": ["No heavy machinery", "Standard access only"],
                    "notes": "Standard access route"
                },
                "work_constraints": {
                    "work_hours": "07:00-17:00",
                    "noise_constraints": "Max 85 dB during work hours",
                    "cleanliness_requirements": "Standard cleanliness",
                    "temperature_requirements": "Min 15°C",
                    "ventilation_requirements": "Natural ventilation sufficient"
                },
                "rigging_drift": {
                    "site_facilities": ["riggområde", "garderobe"],
                    "temporary_utilities": ["byggstrøm", "byggvarme"],
                    "material_handling": {
                        "routes": "Main corridor",
                        "lifts_or_hoists": "None required",
                        "cranes": "None required"
                    },
                    "storage": {
                        "indoor": "Adjacent storage room",
                        "outdoor": "Not required",
                        "temperature_controlled": False
                    },
                    "waste_management": {
                        "fractions": ["Treverk", "Metall", "Plast", "Rest", "Papir/Kartong"],
                        "container_locations": ["Building entrance"]
                    }
                },
                "sha_plan": {
                    "risk_activities": ["Manual handling", "Tool use"],
                    "permits_required": [],
                    "ppe": ["Hjelm", "Vernesko", "Hansker"],
                    "sja_required": True,
                    "responsible_roles": ["SHA-koordinator (KP/KU)", "Bas"],
                    "emergency_procedures": ["Fire evacuation", "First aid"],
                    "environmental_considerations": ["Dust control", "Waste sorting"]
                },
                "lean_takt": {
                    "takt_area_id": "TA-001",
                    "takt_time_days": 3,
                    "sequence": ["Structure", "MEP", "Finishes"],
                    "constraints": ["Weather dependent", "Access routes"],
                    "handoff_criteria": ["Quality check", "Safety inspection"],
                    "quality_gates": ["Material delivery", "Work completion"]
                }
            },
            "130": {  # Våtrom
                "access_route": {
                    "route_id": "AR-101",
                    "description": "Main corridor access",
                    "width_m": 1.2,
                    "height_m": 2.4,
                    "load_capacity_kg": 500.0,
                    "restrictions": ["No heavy machinery", "Waterproofing required"],
                    "notes": "Access route for wet room"
                },
                "work_constraints": {
                    "work_hours": "07:00-17:00",
                    "noise_constraints": "Max 85 dB during work hours",
                    "cleanliness_requirements": "High cleanliness required",
                    "temperature_requirements": "Min 15°C",
                    "ventilation_requirements": "Mechanical ventilation required"
                },
                "rigging_drift": {
                    "site_facilities": ["riggområde", "garderobe", "spiserom"],
                    "temporary_utilities": ["byggstrøm", "byggvarme", "midlertidig vann"],
                    "material_handling": {
                        "routes": "Main corridor",
                        "lifts_or_hoists": "None required",
                        "cranes": "None required"
                    },
                    "storage": {
                        "indoor": "Adjacent storage room",
                        "outdoor": "Not required",
                        "temperature_controlled": False
                    },
                    "waste_management": {
                        "fractions": ["Treverk", "Metall", "Plast", "Rest", "Papir/Kartong", "Farlig avfall"],
                        "container_locations": ["Building entrance"]
                    }
                },
                "sha_plan": {
                    "risk_activities": ["Manual handling", "Tool use", "Waterproofing work"],
                    "permits_required": [],
                    "ppe": ["Hjelm", "Vernesko", "Vernebriller", "Hansker"],
                    "sja_required": True,
                    "responsible_roles": ["SHA-koordinator (KP/KU)", "Bas", "Anleggsleder"],
                    "emergency_procedures": ["Fire evacuation", "First aid", "Water damage response"],
                    "environmental_considerations": ["Dust control", "Waste sorting", "Water management"]
                },
                "lean_takt": {
                    "takt_area_id": "TA-101",
                    "takt_time_days": 5,
                    "sequence": ["Structure", "Waterproofing", "MEP", "Finishes"],
                    "constraints": ["Weather dependent", "Access routes", "Waterproofing cure time"],
                    "handoff_criteria": ["Quality check", "Safety inspection", "Waterproofing test"],
                    "quality_gates": ["Material delivery", "Waterproofing completion", "Work completion"]
                }
            },
            "131": {  # WC
                "access_route": {
                    "route_id": "AR-201",
                    "description": "Main corridor access",
                    "width_m": 1.2,
                    "height_m": 2.4,
                    "load_capacity_kg": 500.0,
                    "restrictions": ["No heavy machinery", "Waterproofing required"],
                    "notes": "Access route for WC"
                },
                "work_constraints": {
                    "work_hours": "07:00-17:00",
                    "noise_constraints": "Max 85 dB during work hours",
                    "cleanliness_requirements": "High cleanliness required",
                    "temperature_requirements": "Min 15°C",
                    "ventilation_requirements": "Mechanical ventilation required"
                },
                "rigging_drift": {
                    "site_facilities": ["riggområde", "garderobe"],
                    "temporary_utilities": ["byggstrøm", "byggvarme", "midlertidig vann"],
                    "material_handling": {
                        "routes": "Main corridor",
                        "lifts_or_hoists": "None required",
                        "cranes": "None required"
                    },
                    "storage": {
                        "indoor": "Adjacent storage room",
                        "outdoor": "Not required",
                        "temperature_controlled": False
                    },
                    "waste_management": {
                        "fractions": ["Treverk", "Metall", "Plast", "Rest", "Papir/Kartong"],
                        "container_locations": ["Building entrance"]
                    }
                },
                "sha_plan": {
                    "risk_activities": ["Manual handling", "Tool use", "Waterproofing work"],
                    "permits_required": [],
                    "ppe": ["Hjelm", "Vernesko", "Vernebriller", "Hansker"],
                    "sja_required": True,
                    "responsible_roles": ["SHA-koordinator (KP/KU)", "Bas"],
                    "emergency_procedures": ["Fire evacuation", "First aid", "Water damage response"],
                    "environmental_considerations": ["Dust control", "Waste sorting", "Water management"]
                },
                "lean_takt": {
                    "takt_area_id": "TA-201",
                    "takt_time_days": 4,
                    "sequence": ["Structure", "Waterproofing", "MEP", "Finishes"],
                    "constraints": ["Weather dependent", "Access routes", "Waterproofing cure time"],
                    "handoff_criteria": ["Quality check", "Safety inspection", "Waterproofing test"],
                    "quality_gates": ["Material delivery", "Waterproofing completion", "Work completion"]
                }
            },
            "132": {  # Baderom
                "access_route": {
                    "route_id": "AR-301",
                    "description": "Main corridor access",
                    "width_m": 1.2,
                    "height_m": 2.4,
                    "load_capacity_kg": 500.0,
                    "restrictions": ["No heavy machinery", "Waterproofing required"],
                    "notes": "Access route for bathroom"
                },
                "work_constraints": {
                    "work_hours": "07:00-17:00",
                    "noise_constraints": "Max 85 dB during work hours",
                    "cleanliness_requirements": "High cleanliness required",
                    "temperature_requirements": "Min 15°C",
                    "ventilation_requirements": "Mechanical ventilation required"
                },
                "rigging_drift": {
                    "site_facilities": ["riggområde", "garderobe", "spiserom"],
                    "temporary_utilities": ["byggstrøm", "byggvarme", "midlertidig vann"],
                    "material_handling": {
                        "routes": "Main corridor",
                        "lifts_or_hoists": "None required",
                        "cranes": "None required"
                    },
                    "storage": {
                        "indoor": "Adjacent storage room",
                        "outdoor": "Not required",
                        "temperature_controlled": False
                    },
                    "waste_management": {
                        "fractions": ["Treverk", "Metall", "Plast", "Rest", "Papir/Kartong", "Farlig avfall"],
                        "container_locations": ["Building entrance"]
                    }
                },
                "sha_plan": {
                    "risk_activities": ["Manual handling", "Tool use", "Waterproofing work"],
                    "permits_required": [],
                    "ppe": ["Hjelm", "Vernesko", "Vernebriller", "Hansker"],
                    "sja_required": True,
                    "responsible_roles": ["SHA-koordinator (KP/KU)", "Bas", "Anleggsleder"],
                    "emergency_procedures": ["Fire evacuation", "First aid", "Water damage response"],
                    "environmental_considerations": ["Dust control", "Waste sorting", "Water management"]
                },
                "lean_takt": {
                    "takt_area_id": "TA-301",
                    "takt_time_days": 5,
                    "sequence": ["Structure", "Waterproofing", "MEP", "Finishes"],
                    "constraints": ["Weather dependent", "Access routes", "Waterproofing cure time"],
                    "handoff_criteria": ["Quality check", "Safety inspection", "Waterproofing test"],
                    "quality_gates": ["Material delivery", "Waterproofing completion", "Work completion"]
                }
            },
            "140": {  # Kjøkken
                "access_route": {
                    "route_id": "AR-401",
                    "description": "Main corridor access",
                    "width_m": 1.2,
                    "height_m": 2.4,
                    "load_capacity_kg": 500.0,
                    "restrictions": ["No heavy machinery", "Appliance delivery required"],
                    "notes": "Access route for kitchen"
                },
                "work_constraints": {
                    "work_hours": "07:00-17:00",
                    "noise_constraints": "Max 85 dB during work hours",
                    "cleanliness_requirements": "High cleanliness required",
                    "temperature_requirements": "Min 15°C",
                    "ventilation_requirements": "Mechanical ventilation required"
                },
                "rigging_drift": {
                    "site_facilities": ["riggområde", "garderobe", "spiserom"],
                    "temporary_utilities": ["byggstrøm", "byggvarme", "midlertidig vann"],
                    "material_handling": {
                        "routes": "Main corridor",
                        "lifts_or_hoists": "Appliance hoist required",
                        "cranes": "None required"
                    },
                    "storage": {
                        "indoor": "Adjacent storage room",
                        "outdoor": "Not required",
                        "temperature_controlled": False
                    },
                    "waste_management": {
                        "fractions": ["Treverk", "Metall", "Plast", "Rest", "Papir/Kartong"],
                        "container_locations": ["Building entrance"]
                    }
                },
                "sha_plan": {
                    "risk_activities": ["Manual handling", "Tool use", "Appliance installation"],
                    "permits_required": [],
                    "ppe": ["Hjelm", "Vernesko", "Vernebriller", "Hansker"],
                    "sja_required": True,
                    "responsible_roles": ["SHA-koordinator (KP/KU)", "Bas", "Anleggsleder"],
                    "emergency_procedures": ["Fire evacuation", "First aid", "Gas leak response"],
                    "environmental_considerations": ["Dust control", "Waste sorting", "Gas safety"]
                },
                "lean_takt": {
                    "takt_area_id": "TA-401",
                    "takt_time_days": 6,
                    "sequence": ["Structure", "MEP", "Appliances", "Finishes"],
                    "constraints": ["Weather dependent", "Access routes", "Appliance delivery"],
                    "handoff_criteria": ["Quality check", "Safety inspection", "Appliance testing"],
                    "quality_gates": ["Material delivery", "Appliance delivery", "Work completion"]
                }
            }
        }
        
        return defaults.get(room_type, defaults["111"])  # Default to oppholdsrom


# Example usage and testing
if __name__ == "__main__":
    mapper = LogisticsMapper()
    
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
    
    print("Logistics Mapper Test:")
    print("=" * 50)
    
    # Test logistics extraction
    logistics = mapper.extract_logistics(sample_space)
    print(f"Access route defined: {logistics.access_route is not None}")
    print(f"Site facilities: {len(logistics.rigging_drift.site_facilities)}")
    print(f"PPE required: {len(logistics.sha_plan.ppe)}")
    print(f"Takt area: {logistics.lean_takt.takt_area_id}")
    
    # Test site plan
    plan = mapper.generate_site_plan(sample_space)
    print(f"\\nSite Plan:")
    print(plan[:500] + "..." if len(plan) > 500 else plan)
    
    # Test compliance validation
    compliance = mapper.validate_logistics_compliance(sample_space)
    print(f"\\nCompliance Status:")
    print(f"Compliant: {compliance['compliant']}")
    print(f"Issues: {compliance['issues']}")
    print(f"Warnings: {compliance['warnings']}")
