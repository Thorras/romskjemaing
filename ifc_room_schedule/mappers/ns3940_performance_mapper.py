"""
NS 3940 Performance Mapper

Maps NS 3940 function codes to performance requirements using the defaults database.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from ..data.space_model import SpaceData
from ..parsers.ns8360_name_parser import NS8360NameParser
from .ns3940_classifier import NS3940Classifier
from ..defaults.ns3940_defaults import NS3940DefaultsDatabase, PerformanceDefaults


@dataclass
class PerformanceRequirementsData:
    """Performance requirements data for room schedule."""
    
    lighting: Optional[Dict[str, Any]] = None
    acoustics: Optional[Dict[str, Any]] = None
    ventilation: Optional[Dict[str, Any]] = None
    thermal: Optional[Dict[str, Any]] = None
    water_sanitary: Optional[Dict[str, Any]] = None
    accessibility: Optional[Dict[str, Any]] = None
    equipment: Optional[Dict[str, Any]] = None
    fire_safety: Optional[Dict[str, Any]] = None
    energy_efficiency: Optional[Dict[str, Any]] = None
    
    # Metadata
    source: str = "ns3940_defaults"
    confidence: float = 1.0
    function_code: Optional[str] = None
    room_type: Optional[str] = None


class NS3940PerformanceMapper:
    """Maps NS 3940 function codes to performance requirements."""
    
    def __init__(self):
        """Initialize NS3940PerformanceMapper."""
        self.name_parser = NS8360NameParser()
        self.classifier = NS3940Classifier()
        self.defaults_db = NS3940DefaultsDatabase()
    
    def map_performance_requirements(self, space: SpaceData, 
                                   function_code: Optional[str] = None) -> PerformanceRequirementsData:
        """
        Map performance requirements for a space.
        
        Args:
            space: SpaceData to map
            function_code: Optional function code (will be inferred if not provided)
            
        Returns:
            PerformanceRequirementsData with mapped requirements
        """
        # Determine function code
        if not function_code:
            function_code = self._determine_function_code(space)
        
        # Get defaults from database
        defaults = self.defaults_db.get_defaults(function_code)
        
        if not defaults:
            # Fallback to generic requirements
            return self._create_fallback_requirements(space, function_code)
        
        # Map all performance sections
        performance_data = PerformanceRequirementsData(
            lighting=self._map_lighting_requirements(defaults.lighting),
            acoustics=self._map_acoustics_requirements(defaults.acoustics),
            ventilation=self._map_ventilation_requirements(defaults.ventilation),
            thermal=self._map_thermal_requirements(defaults.thermal),
            water_sanitary=self._map_water_sanitary_requirements(defaults.water_sanitary),
            accessibility=self._map_accessibility_requirements(defaults.accessibility),
            equipment=self._map_equipment_requirements(defaults.equipment),
            fire_safety=self._map_fire_safety_requirements(defaults.fire_safety),
            energy_efficiency=self._map_energy_efficiency_requirements(defaults.energy_efficiency),
            source="ns3940_defaults",
            confidence=1.0,
            function_code=function_code,
            room_type=defaults.lighting.task_lux if defaults.lighting else None
        )
        
        return performance_data
    
    def get_room_type_defaults(self, function_code: str) -> Optional[PerformanceDefaults]:
        """
        Get complete defaults for a room type.
        
        Args:
            function_code: NS 3940 function code
            
        Returns:
            PerformanceDefaults if code exists, None otherwise
        """
        return self.defaults_db.get_defaults(function_code)
    
    def map_technical_requirements(self, space: SpaceData, 
                                 custom_requirements: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Map technical requirements with intelligent defaults.
        
        Args:
            space: SpaceData to map
            custom_requirements: Optional custom requirements to override defaults
            
        Returns:
            Dictionary with technical requirements
        """
        # Get base requirements
        function_code = self._determine_function_code(space)
        performance_data = self.map_performance_requirements(space, function_code)
        
        # Convert to dictionary format
        technical_reqs = {
            "function_code": function_code,
            "room_type": performance_data.room_type,
            "source": performance_data.source,
            "confidence": performance_data.confidence
        }
        
        # Add performance sections
        if performance_data.lighting:
            technical_reqs["lighting"] = performance_data.lighting
        if performance_data.acoustics:
            technical_reqs["acoustics"] = performance_data.acoustics
        if performance_data.ventilation:
            technical_reqs["ventilation"] = performance_data.ventilation
        if performance_data.thermal:
            technical_reqs["thermal"] = performance_data.thermal
        if performance_data.water_sanitary:
            technical_reqs["water_sanitary"] = performance_data.water_sanitary
        if performance_data.accessibility:
            technical_reqs["accessibility"] = performance_data.accessibility
        if performance_data.equipment:
            technical_reqs["equipment"] = performance_data.equipment
        if performance_data.fire_safety:
            technical_reqs["fire_safety"] = performance_data.fire_safety
        if performance_data.energy_efficiency:
            technical_reqs["energy_efficiency"] = performance_data.energy_efficiency
        
        # Apply custom requirements if provided
        if custom_requirements:
            technical_reqs.update(custom_requirements)
        
        return technical_reqs
    
    def detect_wet_room_requirements(self, space: SpaceData) -> Dict[str, Any]:
        """
        Detect and map wet room specific requirements.
        
        Args:
            space: SpaceData to analyze
            
        Returns:
            Dictionary with wet room requirements
        """
        function_code = self._determine_function_code(space)
        
        if not self.defaults_db.is_wet_room(function_code):
            return {
                "is_wet_room": False,
                "requirements": None
            }
        
        # Get wet room specific requirements
        defaults = self.defaults_db.get_defaults(function_code)
        if not defaults or not defaults.water_sanitary:
            return {
                "is_wet_room": True,
                "requirements": None
            }
        
        return {
            "is_wet_room": True,
            "requirements": {
                "drainage_required": defaults.water_sanitary.drainage_required,
                "hot_cold_water": defaults.water_sanitary.hot_cold_water,
                "fixtures": defaults.water_sanitary.fixtures,
                "water_pressure_bar": defaults.water_sanitary.water_pressure_bar,
                "drainage_diameter_mm": defaults.water_sanitary.drainage_diameter_mm,
                "ventilation_extract_m3h": defaults.ventilation.airflow_extract_m3h,
                "pressure_room_Pa": defaults.ventilation.pressure_room_Pa,
                "slip_resistance_class": defaults.accessibility.slip_resistance_class if defaults.accessibility else None,
                "emergency_lighting": defaults.lighting.emergency_lighting
            }
        }
    
    def validate_performance_consistency(self, space: SpaceData, 
                                       performance_data: PerformanceRequirementsData) -> Dict[str, Any]:
        """
        Validate performance requirements consistency.
        
        Args:
            space: SpaceData to validate
            performance_data: Performance requirements to validate
            
        Returns:
            Validation results
        """
        validation_results = {
            "is_consistent": True,
            "warnings": [],
            "errors": [],
            "recommendations": []
        }
        
        # Check wet room consistency
        if performance_data.water_sanitary and performance_data.water_sanitary.get("drainage_required"):
            if not performance_data.ventilation or not performance_data.ventilation.get("airflow_extract_m3h"):
                validation_results["warnings"].append("Wet room requires extract ventilation")
                validation_results["recommendations"].append("Add extract ventilation requirements")
        
        # Check accessibility consistency
        if performance_data.accessibility and performance_data.accessibility.get("universal_design"):
            if not performance_data.accessibility.get("clear_width_door_mm") or performance_data.accessibility.get("clear_width_door_mm") < 850:
                validation_results["warnings"].append("Universal design requires minimum 850mm door width")
                validation_results["recommendations"].append("Ensure door width meets accessibility requirements")
        
        # Check lighting consistency
        if performance_data.lighting:
            task_lux = performance_data.lighting.get("task_lux", 0)
            if task_lux < 100:
                validation_results["warnings"].append("Very low lighting levels may not meet standards")
            elif task_lux > 1000:
                validation_results["warnings"].append("Very high lighting levels may cause glare")
        
        # Check ventilation consistency
        if performance_data.ventilation:
            supply = performance_data.ventilation.get("airflow_supply_m3h", 0)
            extract = performance_data.ventilation.get("airflow_extract_m3h", 0)
            if extract > 0 and supply > 0 and extract > supply * 2:
                validation_results["warnings"].append("Extract airflow significantly higher than supply")
                validation_results["recommendations"].append("Consider balanced ventilation system")
        
        return validation_results
    
    def _determine_function_code(self, space: SpaceData) -> str:
        """Determine function code from space data."""
        # Try parsing NS 8360 compliant name first
        parsed_name = self.name_parser.parse(space.name)
        if parsed_name.is_valid and parsed_name.function_code:
            return parsed_name.function_code
        
        # Fallback to name inference
        inferred_code = self.classifier.infer_code_from_name(space.name)
        if inferred_code:
            return inferred_code
        
        # Default fallback
        return "111"  # Oppholdsrom
    
    def _create_fallback_requirements(self, space: SpaceData, function_code: str) -> PerformanceRequirementsData:
        """Create fallback requirements when defaults are not available."""
        return PerformanceRequirementsData(
            lighting={
                "task_lux": 200,
                "color_rendering_CRI": 80,
                "emergency_lighting": False
            },
            acoustics={
                "class_ns8175": "C",
                "rw_dB": 52,
                "background_noise_dB": 35
            },
            ventilation={
                "airflow_supply_m3h": 7.2,
                "co2_setpoint_ppm": 1000
            },
            thermal={
                "setpoint_heating_C": 20,
                "setpoint_cooling_C": 26
            },
            accessibility={
                "universal_design": True,
                "clear_width_door_mm": 850
            },
            source="fallback_defaults",
            confidence=0.5,
            function_code=function_code,
            room_type="Unknown"
        )
    
    def _map_lighting_requirements(self, lighting) -> Dict[str, Any]:
        """Map lighting requirements to dictionary."""
        if not lighting:
            return None
        
        return {
            "task_lux": lighting.task_lux,
            "color_rendering_CRI": lighting.color_rendering_CRI,
            "emergency_lighting": lighting.emergency_lighting,
            "UGR_max": lighting.UGR_max,
            "uniformity_ratio": lighting.uniformity_ratio,
            "daylight_factor_min": lighting.daylight_factor_min,
            "lighting_control": lighting.lighting_control
        }
    
    def _map_acoustics_requirements(self, acoustics) -> Dict[str, Any]:
        """Map acoustics requirements to dictionary."""
        if not acoustics:
            return None
        
        return {
            "class_ns8175": acoustics.class_ns8175,
            "rw_dB": acoustics.rw_dB,
            "background_noise_dB": acoustics.background_noise_dB,
            "reverberation_time_s": acoustics.reverberation_time_s,
            "impact_sound_dB": acoustics.impact_sound_dB
        }
    
    def _map_ventilation_requirements(self, ventilation) -> Dict[str, Any]:
        """Map ventilation requirements to dictionary."""
        if not ventilation:
            return None
        
        return {
            "airflow_supply_m3h": ventilation.airflow_supply_m3h,
            "airflow_extract_m3h": ventilation.airflow_extract_m3h,
            "co2_setpoint_ppm": ventilation.co2_setpoint_ppm,
            "pressure_room_Pa": ventilation.pressure_room_Pa,
            "air_change_rate_h": ventilation.air_change_rate_h,
            "filter_class": ventilation.filter_class
        }
    
    def _map_thermal_requirements(self, thermal) -> Dict[str, Any]:
        """Map thermal requirements to dictionary."""
        if not thermal:
            return None
        
        return {
            "setpoint_heating_C": thermal.setpoint_heating_C,
            "setpoint_cooling_C": thermal.setpoint_cooling_C,
            "u_values": thermal.u_values,
            "thermal_mass": thermal.thermal_mass,
            "heating_system": thermal.heating_system
        }
    
    def _map_water_sanitary_requirements(self, water_sanitary) -> Dict[str, Any]:
        """Map water/sanitary requirements to dictionary."""
        if not water_sanitary:
            return None
        
        return {
            "hot_cold_water": water_sanitary.hot_cold_water,
            "drainage_required": water_sanitary.drainage_required,
            "fixtures": water_sanitary.fixtures,
            "water_pressure_bar": water_sanitary.water_pressure_bar,
            "drainage_diameter_mm": water_sanitary.drainage_diameter_mm
        }
    
    def _map_accessibility_requirements(self, accessibility) -> Dict[str, Any]:
        """Map accessibility requirements to dictionary."""
        if not accessibility:
            return None
        
        return {
            "universal_design": accessibility.universal_design,
            "clear_width_door_mm": accessibility.clear_width_door_mm,
            "turning_radius_m": accessibility.turning_radius_m,
            "slip_resistance_class": accessibility.slip_resistance_class,
            "handrail_height_mm": accessibility.handrail_height_mm,
            "accessible_wc": accessibility.accessible_wc
        }
    
    def _map_equipment_requirements(self, equipment) -> Dict[str, Any]:
        """Map equipment requirements to dictionary."""
        if not equipment:
            return None
        
        return {
            "electrical_outlets": equipment.electrical_outlets,
            "lighting_points": equipment.lighting_points,
            "switches": equipment.switches,
            "data_points": equipment.data_points,
            "tv_points": equipment.tv_points,
            "telephone_points": equipment.telephone_points,
            "fire_detection": equipment.fire_detection,
            "emergency_equipment": equipment.emergency_equipment
        }
    
    def _map_fire_safety_requirements(self, fire_safety) -> Dict[str, Any]:
        """Map fire safety requirements to dictionary."""
        if not fire_safety:
            return None
        
        return fire_safety
    
    def _map_energy_efficiency_requirements(self, energy_efficiency) -> Dict[str, Any]:
        """Map energy efficiency requirements to dictionary."""
        if not energy_efficiency:
            return None
        
        return energy_efficiency


# Example usage and testing
if __name__ == "__main__":
    from ..data.space_model import SpaceData
    
    # Create test space data
    test_spaces = [
        SpaceData(
            guid="GUID-STUE-001",
            name="SPC-02-A101-111-003",
            long_name="Stue | 02/A101 | NS3940:111",
            description="Oppholdsrom i A101",
            object_type="IfcSpace",
            zone_category="Residential",
            number="003",
            elevation=6.0,
            quantities={"NetFloorArea": 24.0, "GrossFloorArea": 25.5}
        ),
        SpaceData(
            guid="GUID-BAD-001",
            name="Bad 2. etasje",
            description="Bad med dusj",
            object_type="IfcSpace",
            zone_category="Residential",
            number="001",
            elevation=6.0,
            quantities={"NetFloorArea": 4.8, "GrossFloorArea": 5.2}
        )
    ]
    
    mapper = NS3940PerformanceMapper()
    
    print("NS 3940 Performance Mapper Test Results:")
    print("=" * 60)
    
    for i, space in enumerate(test_spaces, 1):
        print(f"\n--- Test Space {i}: {space.name} ---")
        
        # Map performance requirements
        performance = mapper.map_performance_requirements(space)
        
        print(f"Function Code: {performance.function_code}")
        print(f"Room Type: {performance.room_type}")
        print(f"Source: {performance.source}")
        print(f"Confidence: {performance.confidence}")
        
        if performance.lighting:
            print(f"Lighting Task Lux: {performance.lighting['task_lux']}")
            print(f"Emergency Lighting: {performance.lighting['emergency_lighting']}")
        
        if performance.acoustics:
            print(f"Acoustics Class: {performance.acoustics['class_ns8175']}")
            print(f"Background Noise: {performance.acoustics['background_noise_dB']} dB")
        
        if performance.ventilation:
            print(f"Supply Airflow: {performance.ventilation['airflow_supply_m3h']} m³/h")
            print(f"Extract Airflow: {performance.ventilation['airflow_extract_m3h']} m³/h")
        
        if performance.thermal:
            print(f"Heating Setpoint: {performance.thermal['setpoint_heating_C']}°C")
            print(f"Cooling Setpoint: {performance.thermal['setpoint_cooling_C']}°C")
        
        if performance.water_sanitary:
            print(f"Drainage Required: {performance.water_sanitary['drainage_required']}")
            print(f"Fixtures: {', '.join(performance.water_sanitary['fixtures'])}")
        
        if performance.equipment:
            print(f"Electrical Outlets: {performance.equipment['electrical_outlets']}")
            print(f"Lighting Points: {performance.equipment['lighting_points']}")
        
        # Test wet room detection
        wet_room_info = mapper.detect_wet_room_requirements(space)
        print(f"Wet Room: {wet_room_info['is_wet_room']}")
        
        # Test validation
        validation = mapper.validate_performance_consistency(space, performance)
        print(f"Consistent: {validation['is_consistent']}")
        if validation['warnings']:
            print(f"Warnings: {', '.join(validation['warnings'])}")
        if validation['recommendations']:
            print(f"Recommendations: {', '.join(validation['recommendations'])}")
