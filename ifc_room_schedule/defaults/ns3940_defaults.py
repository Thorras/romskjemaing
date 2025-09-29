"""
NS 3940 Performance Defaults Database

Comprehensive database of performance requirements based on NS 3940 function codes
and Norwegian building standards (NS 8175, TEK17).
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class LightingRequirements:
    """Lighting performance requirements."""
    
    task_lux: int
    color_rendering_CRI: int
    emergency_lighting: bool = False
    UGR_max: int = 22
    uniformity_ratio: float = 0.7
    daylight_factor_min: float = 2.0
    lighting_control: str = "Manual"


@dataclass
class AcousticsRequirements:
    """Acoustics performance requirements."""
    
    class_ns8175: str  # A, B, C, D
    rw_dB: int  # Sound reduction index
    background_noise_dB: int
    reverberation_time_s: Optional[float] = None
    impact_sound_dB: Optional[int] = None


@dataclass
class VentilationRequirements:
    """Ventilation performance requirements."""
    
    airflow_supply_m3h: Optional[float] = None
    airflow_extract_m3h: Optional[float] = None
    co2_setpoint_ppm: int = 1000
    pressure_room_Pa: Optional[int] = None
    air_change_rate_h: Optional[float] = None
    filter_class: str = "G4"


@dataclass
class ThermalRequirements:
    """Thermal performance requirements."""
    
    setpoint_heating_C: float
    setpoint_cooling_C: Optional[float] = None
    u_values: Optional[Dict[str, float]] = None
    thermal_mass: Optional[str] = None
    heating_system: Optional[str] = None


@dataclass
class WaterSanitaryRequirements:
    """Water and sanitary requirements."""
    
    hot_cold_water: bool
    drainage_required: bool
    fixtures: List[str]
    water_pressure_bar: Optional[float] = None
    drainage_diameter_mm: Optional[int] = None


@dataclass
class AccessibilityRequirements:
    """Accessibility and universal design requirements."""
    
    universal_design: bool
    clear_width_door_mm: int
    turning_radius_m: Optional[float] = None
    slip_resistance_class: Optional[str] = None
    handrail_height_mm: Optional[int] = None
    accessible_wc: bool = False


@dataclass
class EquipmentRequirements:
    """Equipment and fixture requirements."""
    
    electrical_outlets: int
    lighting_points: int
    switches: int
    data_points: int = 0
    tv_points: int = 0
    telephone_points: int = 0
    fire_detection: bool = False
    emergency_equipment: List[str] = None
    
    def __post_init__(self):
        if self.emergency_equipment is None:
            self.emergency_equipment = []


@dataclass
class PerformanceDefaults:
    """Complete performance defaults for a room type."""
    
    lighting: LightingRequirements
    acoustics: AcousticsRequirements
    ventilation: VentilationRequirements
    thermal: ThermalRequirements
    water_sanitary: Optional[WaterSanitaryRequirements] = None
    accessibility: AccessibilityRequirements = None
    equipment: EquipmentRequirements = None
    fire_safety: Optional[Dict[str, Any]] = None
    energy_efficiency: Optional[Dict[str, Any]] = None


class NS3940DefaultsDatabase:
    """Database of NS 3940 performance defaults."""
    
    def __init__(self):
        """Initialize the defaults database."""
        self._defaults = self._build_defaults_database()
    
    def get_defaults(self, function_code: str) -> Optional[PerformanceDefaults]:
        """
        Get performance defaults for a function code.
        
        Args:
            function_code: NS 3940 function code
            
        Returns:
            PerformanceDefaults if code exists, None otherwise
        """
        return self._defaults.get(function_code)
    
    def get_all_function_codes(self) -> List[str]:
        """Get all supported function codes."""
        return list(self._defaults.keys())
    
    def get_wet_room_codes(self) -> List[str]:
        """Get all wet room function codes."""
        wet_room_codes = []
        for code, defaults in self._defaults.items():
            if defaults.water_sanitary and defaults.water_sanitary.drainage_required:
                wet_room_codes.append(code)
        return wet_room_codes
    
    def is_wet_room(self, function_code: str) -> bool:
        """Check if function code represents a wet room."""
        defaults = self.get_defaults(function_code)
        return (defaults and 
                defaults.water_sanitary and 
                defaults.water_sanitary.drainage_required)
    
    def get_lighting_requirements(self, function_code: str) -> Optional[LightingRequirements]:
        """Get lighting requirements for a function code."""
        defaults = self.get_defaults(function_code)
        return defaults.lighting if defaults else None
    
    def get_acoustics_requirements(self, function_code: str) -> Optional[AcousticsRequirements]:
        """Get acoustics requirements for a function code."""
        defaults = self.get_defaults(function_code)
        return defaults.acoustics if defaults else None
    
    def get_ventilation_requirements(self, function_code: str) -> Optional[VentilationRequirements]:
        """Get ventilation requirements for a function code."""
        defaults = self.get_defaults(function_code)
        return defaults.ventilation if defaults else None
    
    def get_thermal_requirements(self, function_code: str) -> Optional[ThermalRequirements]:
        """Get thermal requirements for a function code."""
        defaults = self.get_defaults(function_code)
        return defaults.thermal if defaults else None
    
    def get_water_sanitary_requirements(self, function_code: str) -> Optional[WaterSanitaryRequirements]:
        """Get water/sanitary requirements for a function code."""
        defaults = self.get_defaults(function_code)
        return defaults.water_sanitary if defaults else None
    
    def get_accessibility_requirements(self, function_code: str) -> Optional[AccessibilityRequirements]:
        """Get accessibility requirements for a function code."""
        defaults = self.get_defaults(function_code)
        return defaults.accessibility if defaults else None
    
    def get_equipment_requirements(self, function_code: str) -> Optional[EquipmentRequirements]:
        """Get equipment requirements for a function code."""
        defaults = self.get_defaults(function_code)
        return defaults.equipment if defaults else None
    
    def _build_defaults_database(self) -> Dict[str, PerformanceDefaults]:
        """Build the complete defaults database."""
        return {
            "111": PerformanceDefaults(  # Oppholdsrom
                lighting=LightingRequirements(
                    task_lux=200,
                    color_rendering_CRI=80,
                    emergency_lighting=False,
                    UGR_max=22,
                    uniformity_ratio=0.7,
                    daylight_factor_min=2.0
                ),
                acoustics=AcousticsRequirements(
                    class_ns8175="C",
                    rw_dB=52,
                    background_noise_dB=35,
                    reverberation_time_s=0.6
                ),
                ventilation=VentilationRequirements(
                    airflow_supply_m3h=7.2,  # Per m2
                    co2_setpoint_ppm=1000,
                    air_change_rate_h=0.5
                ),
                thermal=ThermalRequirements(
                    setpoint_heating_C=20,
                    setpoint_cooling_C=26,
                    u_values={
                        "wall_W_m2K": 0.18,
                        "floor_W_m2K": 0.15,
                        "ceiling_W_m2K": 0.15,
                        "window_W_m2K": 1.2
                    }
                ),
                accessibility=AccessibilityRequirements(
                    universal_design=True,
                    clear_width_door_mm=850,
                    turning_radius_m=1.5
                ),
                equipment=EquipmentRequirements(
                    electrical_outlets=6,
                    lighting_points=1,
                    switches=2,
                    data_points=1,
                    tv_points=1
                )
            ),
            
            "121": PerformanceDefaults(  # Soverom
                lighting=LightingRequirements(
                    task_lux=150,
                    color_rendering_CRI=80,
                    emergency_lighting=False,
                    UGR_max=22,
                    uniformity_ratio=0.7
                ),
                acoustics=AcousticsRequirements(
                    class_ns8175="B",  # Higher requirement for bedrooms
                    rw_dB=55,
                    background_noise_dB=30,
                    reverberation_time_s=0.5
                ),
                ventilation=VentilationRequirements(
                    airflow_supply_m3h=5.4,  # Per m2, lower for bedrooms
                    co2_setpoint_ppm=1000,
                    air_change_rate_h=0.3
                ),
                thermal=ThermalRequirements(
                    setpoint_heating_C=18,  # Cooler for sleeping
                    setpoint_cooling_C=24,
                    u_values={
                        "wall_W_m2K": 0.18,
                        "floor_W_m2K": 0.15,
                        "ceiling_W_m2K": 0.15,
                        "window_W_m2K": 1.2
                    }
                ),
                accessibility=AccessibilityRequirements(
                    universal_design=True,
                    clear_width_door_mm=850
                ),
                equipment=EquipmentRequirements(
                    electrical_outlets=4,
                    lighting_points=1,
                    switches=2,
                    data_points=1
                )
            ),
            
            "130": PerformanceDefaults(  # Våtrom
                lighting=LightingRequirements(
                    task_lux=200,
                    color_rendering_CRI=90,  # Higher for grooming tasks
                    emergency_lighting=True,
                    UGR_max=22,
                    uniformity_ratio=0.8
                ),
                acoustics=AcousticsRequirements(
                    class_ns8175="C",
                    rw_dB=52,
                    background_noise_dB=40,  # Higher tolerance due to ventilation
                    reverberation_time_s=0.4
                ),
                ventilation=VentilationRequirements(
                    airflow_extract_m3h=54,  # TEK17 requirement
                    pressure_room_Pa=-5,  # Negative pressure
                    air_change_rate_h=6.0
                ),
                thermal=ThermalRequirements(
                    setpoint_heating_C=22,  # Warmer for comfort
                    u_values={
                        "wall_W_m2K": 0.18,
                        "floor_W_m2K": 0.15,
                        "ceiling_W_m2K": 0.15
                    }
                ),
                water_sanitary=WaterSanitaryRequirements(
                    hot_cold_water=True,
                    drainage_required=True,
                    fixtures=["shower", "wc", "sink"],
                    water_pressure_bar=3.0,
                    drainage_diameter_mm=100
                ),
                accessibility=AccessibilityRequirements(
                    universal_design=True,
                    clear_width_door_mm=850,
                    turning_radius_m=1.5,
                    slip_resistance_class="R10",
                    accessible_wc=True
                ),
                equipment=EquipmentRequirements(
                    electrical_outlets=2,
                    lighting_points=1,
                    switches=1,
                    fire_detection=True,
                    emergency_equipment=["emergency_lighting"]
                )
            ),
            
            "131": PerformanceDefaults(  # WC
                lighting=LightingRequirements(
                    task_lux=150,
                    color_rendering_CRI=80,
                    emergency_lighting=False,
                    UGR_max=22
                ),
                acoustics=AcousticsRequirements(
                    class_ns8175="C",
                    rw_dB=52,
                    background_noise_dB=40
                ),
                ventilation=VentilationRequirements(
                    airflow_extract_m3h=36,  # TEK17 requirement for WC
                    pressure_room_Pa=-5,
                    air_change_rate_h=4.0
                ),
                thermal=ThermalRequirements(
                    setpoint_heating_C=20,
                    u_values={
                        "wall_W_m2K": 0.18,
                        "floor_W_m2K": 0.15,
                        "ceiling_W_m2K": 0.15
                    }
                ),
                water_sanitary=WaterSanitaryRequirements(
                    hot_cold_water=False,  # Often only cold water
                    drainage_required=True,
                    fixtures=["wc", "sink"],
                    water_pressure_bar=3.0,
                    drainage_diameter_mm=100
                ),
                accessibility=AccessibilityRequirements(
                    universal_design=True,
                    clear_width_door_mm=850,
                    turning_radius_m=1.5,
                    accessible_wc=True
                ),
                equipment=EquipmentRequirements(
                    electrical_outlets=1,
                    lighting_points=1,
                    switches=1
                )
            ),
            
            "132": PerformanceDefaults(  # Baderom
                lighting=LightingRequirements(
                    task_lux=200,
                    color_rendering_CRI=90,
                    emergency_lighting=True,
                    UGR_max=22,
                    uniformity_ratio=0.8
                ),
                acoustics=AcousticsRequirements(
                    class_ns8175="C",
                    rw_dB=52,
                    background_noise_dB=40,
                    reverberation_time_s=0.4
                ),
                ventilation=VentilationRequirements(
                    airflow_extract_m3h=54,
                    pressure_room_Pa=-5,
                    air_change_rate_h=6.0
                ),
                thermal=ThermalRequirements(
                    setpoint_heating_C=24,  # Warmer for bathing
                    u_values={
                        "wall_W_m2K": 0.18,
                        "floor_W_m2K": 0.15,
                        "ceiling_W_m2K": 0.15
                    }
                ),
                water_sanitary=WaterSanitaryRequirements(
                    hot_cold_water=True,
                    drainage_required=True,
                    fixtures=["bathtub", "shower", "sink"],
                    water_pressure_bar=3.0,
                    drainage_diameter_mm=100
                ),
                accessibility=AccessibilityRequirements(
                    universal_design=True,
                    clear_width_door_mm=850,
                    turning_radius_m=1.5,
                    slip_resistance_class="R10",
                    accessible_wc=True
                ),
                equipment=EquipmentRequirements(
                    electrical_outlets=3,
                    lighting_points=2,
                    switches=2,
                    fire_detection=True,
                    emergency_equipment=["emergency_lighting"]
                )
            ),
            
            "140": PerformanceDefaults(  # Kjøkken
                lighting=LightingRequirements(
                    task_lux=500,  # High for food preparation
                    color_rendering_CRI=90,
                    emergency_lighting=False,
                    UGR_max=22,
                    uniformity_ratio=0.8
                ),
                acoustics=AcousticsRequirements(
                    class_ns8175="C",
                    rw_dB=52,
                    background_noise_dB=40
                ),
                ventilation=VentilationRequirements(
                    airflow_extract_m3h=108,  # Higher for cooking
                    airflow_supply_m3h=7.2,
                    air_change_rate_h=8.0
                ),
                thermal=ThermalRequirements(
                    setpoint_heating_C=20,
                    setpoint_cooling_C=24,
                    u_values={
                        "wall_W_m2K": 0.18,
                        "floor_W_m2K": 0.15,
                        "ceiling_W_m2K": 0.15,
                        "window_W_m2K": 1.2
                    }
                ),
                water_sanitary=WaterSanitaryRequirements(
                    hot_cold_water=True,
                    drainage_required=True,
                    fixtures=["sink"],
                    water_pressure_bar=3.0,
                    drainage_diameter_mm=50
                ),
                accessibility=AccessibilityRequirements(
                    universal_design=True,
                    clear_width_door_mm=850
                ),
                equipment=EquipmentRequirements(
                    electrical_outlets=8,
                    lighting_points=2,
                    switches=3,
                    data_points=1
                )
            ),
            
            "150": PerformanceDefaults(  # Gang/Trappe
                lighting=LightingRequirements(
                    task_lux=100,
                    color_rendering_CRI=80,
                    emergency_lighting=True,
                    UGR_max=25,
                    uniformity_ratio=0.6
                ),
                acoustics=AcousticsRequirements(
                    class_ns8175="D",
                    rw_dB=45,
                    background_noise_dB=45
                ),
                ventilation=VentilationRequirements(
                    airflow_supply_m3h=3.6,  # Per m2
                    air_change_rate_h=0.2
                ),
                thermal=ThermalRequirements(
                    setpoint_heating_C=18,
                    u_values={
                        "wall_W_m2K": 0.18,
                        "floor_W_m2K": 0.15,
                        "ceiling_W_m2K": 0.15
                    }
                ),
                accessibility=AccessibilityRequirements(
                    universal_design=True,
                    clear_width_door_mm=850,
                    turning_radius_m=1.5
                ),
                equipment=EquipmentRequirements(
                    electrical_outlets=2,
                    lighting_points=1,
                    switches=1,
                    fire_detection=True,
                    emergency_equipment=["emergency_lighting", "exit_signs"]
                )
            )
        }
    
    def get_standards_references(self) -> Dict[str, List[str]]:
        """Get standards references for validation."""
        return {
            "NS 3940": ["NS 3940:2023 - Byggelementer og bygningsdeler"],
            "NS 8175": ["NS 8175:2018 - Akustikk i bygninger"],
            "TEK17": ["TEK17 - Byggekrav", "TEK17 §12 - Universell utforming"],
            "NS 3420": ["NS 3420:2019 - Byggeprosjekter"],
            "NS 3031": ["NS 3031:2014 - Beregning av bygningers energibehov"]
        }


# Example usage and testing
if __name__ == "__main__":
    db = NS3940DefaultsDatabase()
    
    print("NS 3940 Performance Defaults Database Test:")
    print("=" * 60)
    
    # Test function codes
    test_codes = ["111", "130", "131", "132", "140", "150"]
    
    for code in test_codes:
        defaults = db.get_defaults(code)
        if defaults:
            print(f"\n--- Function Code {code} ---")
            print(f"Lighting Task Lux: {defaults.lighting.task_lux}")
            print(f"Acoustics Class: {defaults.acoustics.class_ns8175}")
            print(f"Ventilation Supply: {defaults.ventilation.airflow_supply_m3h} m³/h")
            print(f"Thermal Heating: {defaults.thermal.setpoint_heating_C}°C")
            print(f"Wet Room: {db.is_wet_room(code)}")
            if defaults.water_sanitary:
                print(f"Water Required: {defaults.water_sanitary.hot_cold_water}")
                print(f"Drainage Required: {defaults.water_sanitary.drainage_required}")
            if defaults.equipment:
                print(f"Electrical Outlets: {defaults.equipment.electrical_outlets}")
                print(f"Lighting Points: {defaults.equipment.lighting_points}")
    
    # Test wet room detection
    print(f"\nWet Room Codes: {db.get_wet_room_codes()}")
    
    # Test standards references
    print(f"\nStandards References:")
    for standard, refs in db.get_standards_references().items():
        print(f"{standard}: {', '.join(refs)}")
