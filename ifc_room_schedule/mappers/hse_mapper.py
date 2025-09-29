"""
HSE Mapper

Maps IFC data to HSE (Health, Safety, Environment) and accessibility requirements.
Handles universal design, safety requirements, and environmental compliance.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from ..data.space_model import SpaceData
from ..parsers.ns8360_name_parser import NS8360NameParser
from ..mappers.ns3940_classifier import NS3940Classifier


@dataclass
class UniversalDesignData:
    """Universal design requirements."""
    
    universal_design: bool = True
    turning_radius_m: Optional[float] = None
    clear_width_door_mm: Optional[float] = None
    slip_resistance_class: Optional[str] = None  # R9, R10, R11, R12, R13
    emissions_class: Optional[str] = None  # M1, A+, null
    accessible_height_mm: Optional[float] = None
    contrast_requirements: Optional[str] = None
    tactile_guidance: Optional[bool] = None
    visual_guidance: Optional[bool] = None


@dataclass
class SafetyData:
    """Safety requirements."""
    
    fire_safety_class: Optional[str] = None
    escape_route_width_mm: Optional[float] = None
    emergency_exit: Optional[bool] = None
    smoke_detection: Optional[bool] = None
    fire_suppression: Optional[bool] = None
    first_aid_equipment: Optional[bool] = None
    safety_signage: Optional[bool] = None
    emergency_lighting: Optional[bool] = None
    handrail_required: Optional[bool] = None
    guardrail_required: Optional[bool] = None


@dataclass
class EnvironmentalData:
    """Environmental requirements."""
    
    breeam_credits: List[str] = None
    reused_materials: List[str] = None
    epd_requirements: List[str] = None
    waste_sorting_fraction: List[str] = None
    energy_efficiency_class: Optional[str] = None
    co2_emissions_kg_m2: Optional[float] = None
    renewable_energy: Optional[bool] = None
    daylight_factor: Optional[float] = None
    natural_ventilation: Optional[bool] = None
    
    def __post_init__(self):
        if self.breeam_credits is None:
            self.breeam_credits = []
        if self.reused_materials is None:
            self.reused_materials = []
        if self.epd_requirements is None:
            self.epd_requirements = []
        if self.waste_sorting_fraction is None:
            self.waste_sorting_fraction = []


@dataclass
class AccessibilityData:
    """Accessibility requirements."""
    
    wheelchair_accessible: Optional[bool] = None
    hearing_loop: Optional[bool] = None
    visual_alerts: Optional[bool] = None
    accessible_controls: Optional[bool] = None
    accessible_furniture: Optional[bool] = None
    assistive_technology: Optional[bool] = None
    quiet_space: Optional[bool] = None
    sensory_friendly: Optional[bool] = None


@dataclass
class HSEData:
    """Complete HSE data for a space."""
    
    universal_design: UniversalDesignData
    safety: SafetyData
    environmental: EnvironmentalData
    accessibility: AccessibilityData
    last_updated: datetime = None
    
    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.now()


class HSEMapper:
    """Maps IFC data to HSE section."""
    
    def __init__(self):
        """Initialize the HSE mapper."""
        self.name_parser = NS8360NameParser()
        self.classifier = NS3940Classifier()
    
    def extract_hse_requirements(self, space: SpaceData) -> HSEData:
        """
        Extract HSE requirements from space data.
        
        Args:
            space: SpaceData to extract HSE requirements from
            
        Returns:
            HSEData with extracted HSE information
        """
        # Get room type for default requirements
        room_type = self._get_room_type(space)
        
        # Extract universal design requirements
        universal_design = self._extract_universal_design(space, room_type)
        
        # Extract safety requirements
        safety = self._extract_safety_requirements(space, room_type)
        
        # Extract environmental requirements
        environmental = self._extract_environmental_requirements(space, room_type)
        
        # Extract accessibility requirements
        accessibility = self._extract_accessibility_requirements(space, room_type)
        
        return HSEData(
            universal_design=universal_design,
            safety=safety,
            environmental=environmental,
            accessibility=accessibility
        )
    
    def apply_universal_design_requirements(self, space: SpaceData) -> UniversalDesignData:
        """
        Apply universal design requirements to space.
        
        Args:
            space: SpaceData to apply requirements to
            
        Returns:
            UniversalDesignData with requirements
        """
        room_type = self._get_room_type(space)
        defaults = self._get_room_type_defaults(room_type)
        universal_data = defaults.get("universal_design", {})
        
        return UniversalDesignData(
            universal_design=universal_data.get("universal_design", True),
            turning_radius_m=universal_data.get("turning_radius_m"),
            clear_width_door_mm=universal_data.get("clear_width_door_mm"),
            slip_resistance_class=universal_data.get("slip_resistance_class"),
            emissions_class=universal_data.get("emissions_class"),
            accessible_height_mm=universal_data.get("accessible_height_mm"),
            contrast_requirements=universal_data.get("contrast_requirements"),
            tactile_guidance=universal_data.get("tactile_guidance"),
            visual_guidance=universal_data.get("visual_guidance")
        )
    
    def validate_accessibility_compliance(self, space: SpaceData) -> bool:
        """
        Validate accessibility compliance for space.
        
        Args:
            space: SpaceData to validate
            
        Returns:
            True if compliant, False otherwise
        """
        hse_data = self.extract_hse_requirements(space)
        
        # Check universal design compliance
        if not hse_data.universal_design.universal_design:
            return False
        
        # Check accessibility requirements
        if not hse_data.accessibility.wheelchair_accessible:
            return False
        
        # Check door width
        if hse_data.universal_design.clear_width_door_mm and hse_data.universal_design.clear_width_door_mm < 800:
            return False
        
        # Check turning radius
        if hse_data.universal_design.turning_radius_m and hse_data.universal_design.turning_radius_m < 1.5:
            return False
        
        return True
    
    def map_safety_requirements(self, room_type: str) -> Dict[str, Any]:
        """
        Map safety requirements for room type.
        
        Args:
            room_type: NS 3940 room type code
            
        Returns:
            Dictionary of safety requirements
        """
        defaults = self._get_room_type_defaults(room_type)
        return defaults.get("safety", {})
    
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
    
    def _extract_universal_design(self, space: SpaceData, room_type: str) -> UniversalDesignData:
        """Extract universal design requirements from space."""
        # Look for universal design properties
        universal_design = True
        turning_radius = None
        door_width = None
        
        # Check if space has universal design properties
        if space.quantities:
            # Could extract from property sets
            pass
        
        # Apply defaults
        defaults = self._get_room_type_defaults(room_type)
        universal_data = defaults.get("universal_design", {})
        
        return UniversalDesignData(
            universal_design=universal_design and universal_data.get("universal_design", True),
            turning_radius_m=turning_radius or universal_data.get("turning_radius_m"),
            clear_width_door_mm=door_width or universal_data.get("clear_width_door_mm"),
            slip_resistance_class=universal_data.get("slip_resistance_class"),
            emissions_class=universal_data.get("emissions_class"),
            accessible_height_mm=universal_data.get("accessible_height_mm"),
            contrast_requirements=universal_data.get("contrast_requirements"),
            tactile_guidance=universal_data.get("tactile_guidance"),
            visual_guidance=universal_data.get("visual_guidance")
        )
    
    def _extract_safety_requirements(self, space: SpaceData, room_type: str) -> SafetyData:
        """Extract safety requirements from space."""
        # Look for safety properties
        fire_safety_class = None
        escape_route_width = None
        
        # Check if space has safety properties
        if space.quantities:
            # Could extract from property sets
            pass
        
        # Apply defaults
        defaults = self._get_room_type_defaults(room_type)
        safety_data = defaults.get("safety", {})
        
        return SafetyData(
            fire_safety_class=fire_safety_class or safety_data.get("fire_safety_class"),
            escape_route_width_mm=escape_route_width or safety_data.get("escape_route_width_mm"),
            emergency_exit=safety_data.get("emergency_exit"),
            smoke_detection=safety_data.get("smoke_detection"),
            fire_suppression=safety_data.get("fire_suppression"),
            first_aid_equipment=safety_data.get("first_aid_equipment"),
            safety_signage=safety_data.get("safety_signage"),
            emergency_lighting=safety_data.get("emergency_lighting"),
            handrail_required=safety_data.get("handrail_required"),
            guardrail_required=safety_data.get("guardrail_required")
        )
    
    def _extract_environmental_requirements(self, space: SpaceData, room_type: str) -> EnvironmentalData:
        """Extract environmental requirements from space."""
        # Look for environmental properties
        breeam_credits = []
        reused_materials = []
        
        # Check if space has environmental properties
        if space.quantities:
            # Could extract from property sets
            pass
        
        # Apply defaults
        defaults = self._get_room_type_defaults(room_type)
        environmental_data = defaults.get("environmental", {})
        
        return EnvironmentalData(
            breeam_credits=breeam_credits or environmental_data.get("breeam_credits", []),
            reused_materials=reused_materials or environmental_data.get("reused_materials", []),
            epd_requirements=environmental_data.get("epd_requirements", []),
            waste_sorting_fraction=environmental_data.get("waste_sorting_fraction", []),
            energy_efficiency_class=environmental_data.get("energy_efficiency_class"),
            co2_emissions_kg_m2=environmental_data.get("co2_emissions_kg_m2"),
            renewable_energy=environmental_data.get("renewable_energy"),
            daylight_factor=environmental_data.get("daylight_factor"),
            natural_ventilation=environmental_data.get("natural_ventilation")
        )
    
    def _extract_accessibility_requirements(self, space: SpaceData, room_type: str) -> AccessibilityData:
        """Extract accessibility requirements from space."""
        # Look for accessibility properties
        wheelchair_accessible = None
        hearing_loop = None
        
        # Check if space has accessibility properties
        if space.quantities:
            # Could extract from property sets
            pass
        
        # Apply defaults
        defaults = self._get_room_type_defaults(room_type)
        accessibility_data = defaults.get("accessibility", {})
        
        return AccessibilityData(
            wheelchair_accessible=wheelchair_accessible or accessibility_data.get("wheelchair_accessible"),
            hearing_loop=hearing_loop or accessibility_data.get("hearing_loop"),
            visual_alerts=accessibility_data.get("visual_alerts"),
            accessible_controls=accessibility_data.get("accessible_controls"),
            accessible_furniture=accessibility_data.get("accessible_furniture"),
            assistive_technology=accessibility_data.get("assistive_technology"),
            quiet_space=accessibility_data.get("quiet_space"),
            sensory_friendly=accessibility_data.get("sensory_friendly")
        )
    
    def _get_room_type_defaults(self, room_type: str) -> Dict[str, Any]:
        """Get default HSE requirements for room type."""
        defaults = {
            "111": {  # Oppholdsrom
                "universal_design": {
                    "universal_design": True,
                    "turning_radius_m": 1.5,
                    "clear_width_door_mm": 800.0,
                    "slip_resistance_class": "R10",
                    "emissions_class": "A+",
                    "accessible_height_mm": 1200.0,
                    "contrast_requirements": "High contrast",
                    "tactile_guidance": False,
                    "visual_guidance": True
                },
                "safety": {
                    "fire_safety_class": "B-s1, d0",
                    "escape_route_width_mm": 800.0,
                    "emergency_exit": False,
                    "smoke_detection": True,
                    "fire_suppression": False,
                    "first_aid_equipment": False,
                    "safety_signage": True,
                    "emergency_lighting": True,
                    "handrail_required": False,
                    "guardrail_required": False
                },
                "environmental": {
                    "breeam_credits": ["Hea 01", "Hea 02", "Ene 01"],
                    "reused_materials": [],
                    "epd_requirements": ["Flooring", "Paint"],
                    "waste_sorting_fraction": ["Rest", "Papir/Kartong"],
                    "energy_efficiency_class": "A",
                    "co2_emissions_kg_m2": 15.0,
                    "renewable_energy": False,
                    "daylight_factor": 2.0,
                    "natural_ventilation": True
                },
                "accessibility": {
                    "wheelchair_accessible": True,
                    "hearing_loop": False,
                    "visual_alerts": False,
                    "accessible_controls": True,
                    "accessible_furniture": True,
                    "assistive_technology": False,
                    "quiet_space": False,
                    "sensory_friendly": False
                }
            },
            "130": {  # Våtrom
                "universal_design": {
                    "universal_design": True,
                    "turning_radius_m": 1.5,
                    "clear_width_door_mm": 800.0,
                    "slip_resistance_class": "R11",
                    "emissions_class": "M1",
                    "accessible_height_mm": 1200.0,
                    "contrast_requirements": "High contrast",
                    "tactile_guidance": True,
                    "visual_guidance": True
                },
                "safety": {
                    "fire_safety_class": "B-s1, d0",
                    "escape_route_width_mm": 800.0,
                    "emergency_exit": False,
                    "smoke_detection": True,
                    "fire_suppression": False,
                    "first_aid_equipment": False,
                    "safety_signage": True,
                    "emergency_lighting": True,
                    "handrail_required": True,
                    "guardrail_required": False
                },
                "environmental": {
                    "breeam_credits": ["Hea 01", "Hea 02", "Wat 01"],
                    "reused_materials": [],
                    "epd_requirements": ["Tiles", "Sanitary ware"],
                    "waste_sorting_fraction": ["Rest", "Papir/Kartong"],
                    "energy_efficiency_class": "A+",
                    "co2_emissions_kg_m2": 12.0,
                    "renewable_energy": False,
                    "daylight_factor": 1.5,
                    "natural_ventilation": False
                },
                "accessibility": {
                    "wheelchair_accessible": True,
                    "hearing_loop": False,
                    "visual_alerts": True,
                    "accessible_controls": True,
                    "accessible_furniture": True,
                    "assistive_technology": True,
                    "quiet_space": False,
                    "sensory_friendly": False
                }
            },
            "131": {  # WC
                "universal_design": {
                    "universal_design": True,
                    "turning_radius_m": 1.5,
                    "clear_width_door_mm": 800.0,
                    "slip_resistance_class": "R10",
                    "emissions_class": "M1",
                    "accessible_height_mm": 1200.0,
                    "contrast_requirements": "High contrast",
                    "tactile_guidance": True,
                    "visual_guidance": True
                },
                "safety": {
                    "fire_safety_class": "B-s1, d0",
                    "escape_route_width_mm": 800.0,
                    "emergency_exit": False,
                    "smoke_detection": True,
                    "fire_suppression": False,
                    "first_aid_equipment": False,
                    "safety_signage": True,
                    "emergency_lighting": True,
                    "handrail_required": True,
                    "guardrail_required": False
                },
                "environmental": {
                    "breeam_credits": ["Hea 01", "Wat 01"],
                    "reused_materials": [],
                    "epd_requirements": ["Sanitary ware"],
                    "waste_sorting_fraction": ["Rest"],
                    "energy_efficiency_class": "A",
                    "co2_emissions_kg_m2": 10.0,
                    "renewable_energy": False,
                    "daylight_factor": 1.0,
                    "natural_ventilation": False
                },
                "accessibility": {
                    "wheelchair_accessible": True,
                    "hearing_loop": False,
                    "visual_alerts": True,
                    "accessible_controls": True,
                    "accessible_furniture": True,
                    "assistive_technology": True,
                    "quiet_space": False,
                    "sensory_friendly": False
                }
            },
            "132": {  # Baderom
                "universal_design": {
                    "universal_design": True,
                    "turning_radius_m": 1.5,
                    "clear_width_door_mm": 800.0,
                    "slip_resistance_class": "R11",
                    "emissions_class": "M1",
                    "accessible_height_mm": 1200.0,
                    "contrast_requirements": "High contrast",
                    "tactile_guidance": True,
                    "visual_guidance": True
                },
                "safety": {
                    "fire_safety_class": "B-s1, d0",
                    "escape_route_width_mm": 800.0,
                    "emergency_exit": False,
                    "smoke_detection": True,
                    "fire_suppression": False,
                    "first_aid_equipment": False,
                    "safety_signage": True,
                    "emergency_lighting": True,
                    "handrail_required": True,
                    "guardrail_required": False
                },
                "environmental": {
                    "breeam_credits": ["Hea 01", "Hea 02", "Wat 01"],
                    "reused_materials": [],
                    "epd_requirements": ["Tiles", "Sanitary ware"],
                    "waste_sorting_fraction": ["Rest", "Papir/Kartong"],
                    "energy_efficiency_class": "A+",
                    "co2_emissions_kg_m2": 12.0,
                    "renewable_energy": False,
                    "daylight_factor": 1.5,
                    "natural_ventilation": False
                },
                "accessibility": {
                    "wheelchair_accessible": True,
                    "hearing_loop": False,
                    "visual_alerts": True,
                    "accessible_controls": True,
                    "accessible_furniture": True,
                    "assistive_technology": True,
                    "quiet_space": False,
                    "sensory_friendly": False
                }
            },
            "140": {  # Kjøkken
                "universal_design": {
                    "universal_design": True,
                    "turning_radius_m": 1.5,
                    "clear_width_door_mm": 800.0,
                    "slip_resistance_class": "R10",
                    "emissions_class": "A+",
                    "accessible_height_mm": 1200.0,
                    "contrast_requirements": "High contrast",
                    "tactile_guidance": False,
                    "visual_guidance": True
                },
                "safety": {
                    "fire_safety_class": "B-s1, d0",
                    "escape_route_width_mm": 800.0,
                    "emergency_exit": False,
                    "smoke_detection": True,
                    "fire_suppression": True,
                    "first_aid_equipment": True,
                    "safety_signage": True,
                    "emergency_lighting": True,
                    "handrail_required": False,
                    "guardrail_required": False
                },
                "environmental": {
                    "breeam_credits": ["Hea 01", "Hea 02", "Ene 01", "Wat 01"],
                    "reused_materials": ["Kitchen cabinets"],
                    "epd_requirements": ["Appliances", "Worktops"],
                    "waste_sorting_fraction": ["Rest", "Papir/Kartong", "Plast", "Metall"],
                    "energy_efficiency_class": "A+",
                    "co2_emissions_kg_m2": 18.0,
                    "renewable_energy": False,
                    "daylight_factor": 2.0,
                    "natural_ventilation": True
                },
                "accessibility": {
                    "wheelchair_accessible": True,
                    "hearing_loop": False,
                    "visual_alerts": False,
                    "accessible_controls": True,
                    "accessible_furniture": True,
                    "assistive_technology": False,
                    "quiet_space": False,
                    "sensory_friendly": False
                }
            }
        }
        
        return defaults.get(room_type, defaults["111"])  # Default to oppholdsrom


# Example usage and testing
if __name__ == "__main__":
    mapper = HSEMapper()
    
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
    
    print("HSE Mapper Test:")
    print("=" * 50)
    
    # Test HSE extraction
    hse_data = mapper.extract_hse_requirements(sample_space)
    print(f"Universal design: {hse_data.universal_design.universal_design}")
    print(f"Turning radius: {hse_data.universal_design.turning_radius_m}m")
    print(f"Door width: {hse_data.universal_design.clear_width_door_mm}mm")
    print(f"Slip resistance: {hse_data.universal_design.slip_resistance_class}")
    print(f"Fire safety: {hse_data.safety.fire_safety_class}")
    print(f"Emergency lighting: {hse_data.safety.emergency_lighting}")
    print(f"Wheelchair accessible: {hse_data.accessibility.wheelchair_accessible}")
    print(f"BREEAM credits: {hse_data.environmental.breeam_credits}")
    
    # Test accessibility compliance
    is_compliant = mapper.validate_accessibility_compliance(sample_space)
    print(f"\\nAccessibility compliant: {is_compliant}")
    
    # Test safety requirements
    safety_req = mapper.map_safety_requirements("130")
    print(f"\\nVåtrom safety requirements:")
    print(f"Fire safety class: {safety_req.get('fire_safety_class')}")
    print(f"Handrail required: {safety_req.get('handrail_required')}")
    print(f"Emergency lighting: {safety_req.get('emergency_lighting')}")
