"""
Performance Requirements Mapper

Maps IFC data to performance requirements section including fire, acoustics, 
thermal, ventilation, lighting, power, and water/sanitary requirements.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from ..data.space_model import SpaceData
from ..parsers.ns8360_name_parser import NS8360NameParser
from ..mappers.ns3940_classifier import NS3940Classifier


@dataclass
class FireRequirements:
    """Fire safety requirements."""
    
    fire_compartment: Optional[str] = None
    fire_class: Optional[str] = None
    door_rating: Optional[str] = None  # EI30, EI60, EI90, EI120
    penetration_sealing_class: Optional[str] = None
    fire_resistance_rating: Optional[str] = None
    smoke_control: Optional[bool] = None
    escape_route: Optional[bool] = None


@dataclass
class AcousticRequirements:
    """Acoustic performance requirements."""
    
    class_ns8175: Optional[str] = None  # A, B, C, D, E
    rw_dB: Optional[float] = None  # Sound reduction index
    ln_w_dB: Optional[float] = None  # Weighted normalized impact sound pressure level
    background_noise_dB: Optional[float] = None
    reverberation_time_s: Optional[float] = None
    speech_intelligibility: Optional[str] = None  # Good, Fair, Poor


@dataclass
class ThermalRequirements:
    """Thermal performance requirements."""
    
    setpoint_heating_C: Optional[float] = None
    setpoint_cooling_C: Optional[float] = None
    u_values: Dict[str, Optional[float]] = None  # walls, floor, ceiling, window
    thermal_comfort_class: Optional[str] = None  # A, B, C
    heating_load_W: Optional[float] = None
    cooling_load_W: Optional[float] = None
    
    def __post_init__(self):
        if self.u_values is None:
            self.u_values = {
                "walls_W_m2K": None,
                "floor_W_m2K": None,
                "ceiling_W_m2K": None,
                "window_W_m2K": None
            }


@dataclass
class VentilationRequirements:
    """Ventilation requirements."""
    
    airflow_supply_m3h: Optional[float] = None
    airflow_extract_m3h: Optional[float] = None
    co2_setpoint_ppm: Optional[float] = None
    pressure_room_Pa: Optional[float] = None
    air_changes_per_hour: Optional[float] = None
    ventilation_type: Optional[str] = None  # Natural, Mechanical, Mixed
    filtration_class: Optional[str] = None  # G1-G4, F5-F9, H10-H14


@dataclass
class LightingRequirements:
    """Lighting requirements."""
    
    task_lux: Optional[float] = None
    emergency_lighting: bool = False
    color_rendering_CRI: Optional[float] = None
    UGR_max: Optional[float] = None  # Unified Glare Rating
    daylight_factor: Optional[float] = None
    lighting_control: Optional[str] = None  # Manual, Automatic, Occupancy
    energy_efficiency_class: Optional[str] = None  # A++, A+, A, B, C, D, E, F, G


@dataclass
class PowerRequirements:
    """Power and electrical requirements."""
    
    sockets_count: Optional[int] = None
    data_outlets_count: Optional[int] = None
    cleaning_socket: bool = False
    circuits: List[Dict[str, Any]] = None
    power_density_W_m2: Optional[float] = None
    emergency_power: Optional[bool] = None
    UPS_required: Optional[bool] = None
    
    def __post_init__(self):
        if self.circuits is None:
            self.circuits = []


@dataclass
class WaterSanitaryRequirements:
    """Water and sanitary requirements."""
    
    fixtures: List[Dict[str, Any]] = None
    hot_cold_water: bool = False
    drainage_required: bool = False
    water_pressure_bar: Optional[float] = None
    water_temperature_C: Optional[float] = None
    water_quality_standard: Optional[str] = None
    
    def __post_init__(self):
        if self.fixtures is None:
            self.fixtures = []


@dataclass
class PerformanceRequirements:
    """Complete performance requirements for a space."""
    
    fire: FireRequirements
    acoustics: AcousticRequirements
    thermal: ThermalRequirements
    ventilation: VentilationRequirements
    lighting: LightingRequirements
    power_data: PowerRequirements
    water_sanitary: WaterSanitaryRequirements
    last_updated: datetime = None
    
    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.now()


class PerformanceRequirementsMapper:
    """Maps IFC data to performance requirements section."""
    
    def __init__(self):
        """Initialize the performance requirements mapper."""
        self.name_parser = NS8360NameParser()
        self.classifier = NS3940Classifier()
    
    def extract_performance_requirements(self, space: SpaceData) -> PerformanceRequirements:
        """
        Extract performance requirements from space data.
        
        Args:
            space: SpaceData to extract requirements from
            
        Returns:
            PerformanceRequirements with extracted data
        """
        # Get room type for default requirements
        room_type = self._get_room_type(space)
        
        # Extract fire requirements
        fire_req = self._extract_fire_requirements(space, room_type)
        
        # Extract acoustic requirements
        acoustic_req = self._extract_acoustic_requirements(space, room_type)
        
        # Extract thermal requirements
        thermal_req = self._extract_thermal_requirements(space, room_type)
        
        # Extract ventilation requirements
        ventilation_req = self._extract_ventilation_requirements(space, room_type)
        
        # Extract lighting requirements
        lighting_req = self._extract_lighting_requirements(space, room_type)
        
        # Extract power requirements
        power_req = self._extract_power_requirements(space, room_type)
        
        # Extract water/sanitary requirements
        water_req = self._extract_water_sanitary_requirements(space, room_type)
        
        return PerformanceRequirements(
            fire=fire_req,
            acoustics=acoustic_req,
            thermal=thermal_req,
            ventilation=ventilation_req,
            lighting=lighting_req,
            power_data=power_req,
            water_sanitary=water_req
        )
    
    def apply_performance_defaults(self, room_type: str) -> PerformanceRequirements:
        """
        Apply default performance requirements based on room type.
        
        Args:
            room_type: NS 3940 room type code
            
        Returns:
            PerformanceRequirements with default values
        """
        defaults = self._get_room_type_defaults(room_type)
        
        # Fire requirements
        fire_data = defaults.get("fire", {})
        fire_req = FireRequirements(
            fire_compartment=fire_data.get("fire_compartment"),
            fire_class=fire_data.get("fire_class"),
            door_rating=fire_data.get("door_rating"),
            penetration_sealing_class=fire_data.get("penetration_sealing_class"),
            fire_resistance_rating=fire_data.get("fire_resistance_rating"),
            smoke_control=fire_data.get("smoke_control"),
            escape_route=fire_data.get("escape_route")
        )
        
        # Acoustic requirements
        acoustic_data = defaults.get("acoustics", {})
        acoustic_req = AcousticRequirements(
            class_ns8175=acoustic_data.get("class_ns8175"),
            rw_dB=acoustic_data.get("rw_dB"),
            ln_w_dB=acoustic_data.get("ln_w_dB"),
            background_noise_dB=acoustic_data.get("background_noise_dB"),
            reverberation_time_s=acoustic_data.get("reverberation_time_s"),
            speech_intelligibility=acoustic_data.get("speech_intelligibility")
        )
        
        # Thermal requirements
        thermal_data = defaults.get("thermal", {})
        thermal_req = ThermalRequirements(
            setpoint_heating_C=thermal_data.get("setpoint_heating_C"),
            setpoint_cooling_C=thermal_data.get("setpoint_cooling_C"),
            u_values=thermal_data.get("u_values", {}),
            thermal_comfort_class=thermal_data.get("thermal_comfort_class"),
            heating_load_W=thermal_data.get("heating_load_W"),
            cooling_load_W=thermal_data.get("cooling_load_W")
        )
        
        # Ventilation requirements
        ventilation_data = defaults.get("ventilation", {})
        ventilation_req = VentilationRequirements(
            airflow_supply_m3h=ventilation_data.get("airflow_supply_m3h"),
            airflow_extract_m3h=ventilation_data.get("airflow_extract_m3h"),
            co2_setpoint_ppm=ventilation_data.get("co2_setpoint_ppm"),
            pressure_room_Pa=ventilation_data.get("pressure_room_Pa"),
            air_changes_per_hour=ventilation_data.get("air_changes_per_hour"),
            ventilation_type=ventilation_data.get("ventilation_type"),
            filtration_class=ventilation_data.get("filtration_class")
        )
        
        # Lighting requirements
        lighting_data = defaults.get("lighting", {})
        lighting_req = LightingRequirements(
            task_lux=lighting_data.get("task_lux"),
            emergency_lighting=lighting_data.get("emergency_lighting", False),
            color_rendering_CRI=lighting_data.get("color_rendering_CRI"),
            UGR_max=lighting_data.get("UGR_max"),
            daylight_factor=lighting_data.get("daylight_factor"),
            lighting_control=lighting_data.get("lighting_control"),
            energy_efficiency_class=lighting_data.get("energy_efficiency_class")
        )
        
        # Power requirements
        power_data = defaults.get("power_data", {})
        power_req = PowerRequirements(
            sockets_count=power_data.get("sockets_count"),
            data_outlets_count=power_data.get("data_outlets_count"),
            cleaning_socket=power_data.get("cleaning_socket", False),
            circuits=power_data.get("circuits", []),
            power_density_W_m2=power_data.get("power_density_W_m2"),
            emergency_power=power_data.get("emergency_power"),
            UPS_required=power_data.get("UPS_required")
        )
        
        # Water/sanitary requirements
        water_data = defaults.get("water_sanitary", {})
        water_req = WaterSanitaryRequirements(
            fixtures=water_data.get("fixtures", []),
            hot_cold_water=water_data.get("hot_cold_water", False),
            drainage_required=water_data.get("drainage_required", False),
            water_pressure_bar=water_data.get("water_pressure_bar"),
            water_temperature_C=water_data.get("water_temperature_C"),
            water_quality_standard=water_data.get("water_quality_standard")
        )
        
        return PerformanceRequirements(
            fire=fire_req,
            acoustics=acoustic_req,
            thermal=thermal_req,
            ventilation=ventilation_req,
            lighting=lighting_req,
            power_data=power_req,
            water_sanitary=water_req
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
    
    def _extract_fire_requirements(self, space: SpaceData, room_type: str) -> FireRequirements:
        """Extract fire safety requirements from space."""
        # Look for fire-related properties in space
        fire_compartment = None
        fire_class = None
        door_rating = None
        
        # Check if space has fire-related properties
        if space.quantities:
            # Could extract from property sets
            pass
        
        # Apply defaults if no specific data
        defaults = self._get_room_type_defaults(room_type)
        fire_data = defaults.get("fire", {})
        
        return FireRequirements(
            fire_compartment=fire_compartment or fire_data.get("fire_compartment"),
            fire_class=fire_class or fire_data.get("fire_class"),
            door_rating=door_rating or fire_data.get("door_rating"),
            penetration_sealing_class=fire_data.get("penetration_sealing_class"),
            fire_resistance_rating=fire_data.get("fire_resistance_rating"),
            smoke_control=fire_data.get("smoke_control"),
            escape_route=fire_data.get("escape_route")
        )
    
    def _extract_acoustic_requirements(self, space: SpaceData, room_type: str) -> AcousticRequirements:
        """Extract acoustic requirements from space."""
        # Look for acoustic-related properties
        acoustic_class = None
        rw_dB = None
        
        # Check if space has acoustic properties
        if space.quantities:
            # Could extract from property sets
            pass
        
        # Apply defaults
        defaults = self._get_room_type_defaults(room_type)
        acoustic_data = defaults.get("acoustics", {})
        
        return AcousticRequirements(
            class_ns8175=acoustic_class or acoustic_data.get("class_ns8175"),
            rw_dB=rw_dB or acoustic_data.get("rw_dB"),
            ln_w_dB=acoustic_data.get("ln_w_dB"),
            background_noise_dB=acoustic_data.get("background_noise_dB"),
            reverberation_time_s=acoustic_data.get("reverberation_time_s"),
            speech_intelligibility=acoustic_data.get("speech_intelligibility")
        )
    
    def _extract_thermal_requirements(self, space: SpaceData, room_type: str) -> ThermalRequirements:
        """Extract thermal requirements from space."""
        # Look for thermal-related properties
        heating_setpoint = None
        cooling_setpoint = None
        u_values = {}
        
        # Check if space has thermal properties
        if space.quantities:
            # Could extract from property sets
            pass
        
        # Apply defaults
        defaults = self._get_room_type_defaults(room_type)
        thermal_data = defaults.get("thermal", {})
        
        return ThermalRequirements(
            setpoint_heating_C=heating_setpoint or thermal_data.get("setpoint_heating_C"),
            setpoint_cooling_C=cooling_setpoint or thermal_data.get("setpoint_cooling_C"),
            u_values=u_values or thermal_data.get("u_values", {}),
            thermal_comfort_class=thermal_data.get("thermal_comfort_class"),
            heating_load_W=thermal_data.get("heating_load_W"),
            cooling_load_W=thermal_data.get("cooling_load_W")
        )
    
    def _extract_ventilation_requirements(self, space: SpaceData, room_type: str) -> VentilationRequirements:
        """Extract ventilation requirements from space."""
        # Look for ventilation-related properties
        supply_airflow = None
        extract_airflow = None
        
        # Check if space has ventilation properties
        if space.quantities:
            # Could extract from property sets
            pass
        
        # Apply defaults
        defaults = self._get_room_type_defaults(room_type)
        ventilation_data = defaults.get("ventilation", {})
        
        return VentilationRequirements(
            airflow_supply_m3h=supply_airflow or ventilation_data.get("airflow_supply_m3h"),
            airflow_extract_m3h=extract_airflow or ventilation_data.get("airflow_extract_m3h"),
            co2_setpoint_ppm=ventilation_data.get("co2_setpoint_ppm"),
            pressure_room_Pa=ventilation_data.get("pressure_room_Pa"),
            air_changes_per_hour=ventilation_data.get("air_changes_per_hour"),
            ventilation_type=ventilation_data.get("ventilation_type"),
            filtration_class=ventilation_data.get("filtration_class")
        )
    
    def _extract_lighting_requirements(self, space: SpaceData, room_type: str) -> LightingRequirements:
        """Extract lighting requirements from space."""
        # Look for lighting-related properties
        task_lux = None
        emergency_lighting = False
        
        # Check if space has lighting properties
        if space.quantities:
            # Could extract from property sets
            pass
        
        # Apply defaults
        defaults = self._get_room_type_defaults(room_type)
        lighting_data = defaults.get("lighting", {})
        
        return LightingRequirements(
            task_lux=task_lux or lighting_data.get("task_lux"),
            emergency_lighting=emergency_lighting or lighting_data.get("emergency_lighting", False),
            color_rendering_CRI=lighting_data.get("color_rendering_CRI"),
            UGR_max=lighting_data.get("UGR_max"),
            daylight_factor=lighting_data.get("daylight_factor"),
            lighting_control=lighting_data.get("lighting_control"),
            energy_efficiency_class=lighting_data.get("energy_efficiency_class")
        )
    
    def _extract_power_requirements(self, space: SpaceData, room_type: str) -> PowerRequirements:
        """Extract power requirements from space."""
        # Look for power-related properties
        sockets_count = None
        data_outlets_count = None
        
        # Check if space has power properties
        if space.quantities:
            # Could extract from property sets
            pass
        
        # Apply defaults
        defaults = self._get_room_type_defaults(room_type)
        power_data = defaults.get("power_data", {})
        
        return PowerRequirements(
            sockets_count=sockets_count or power_data.get("sockets_count"),
            data_outlets_count=data_outlets_count or power_data.get("data_outlets_count"),
            cleaning_socket=power_data.get("cleaning_socket", False),
            circuits=power_data.get("circuits", []),
            power_density_W_m2=power_data.get("power_density_W_m2"),
            emergency_power=power_data.get("emergency_power"),
            UPS_required=power_data.get("UPS_required")
        )
    
    def _extract_water_sanitary_requirements(self, space: SpaceData, room_type: str) -> WaterSanitaryRequirements:
        """Extract water/sanitary requirements from space."""
        # Look for water-related properties
        fixtures = []
        hot_cold_water = False
        drainage_required = False
        
        # Check if space has water properties
        if space.quantities:
            # Could extract from property sets
            pass
        
        # Apply defaults
        defaults = self._get_room_type_defaults(room_type)
        water_data = defaults.get("water_sanitary", {})
        
        return WaterSanitaryRequirements(
            fixtures=fixtures or water_data.get("fixtures", []),
            hot_cold_water=hot_cold_water or water_data.get("hot_cold_water", False),
            drainage_required=drainage_required or water_data.get("drainage_required", False),
            water_pressure_bar=water_data.get("water_pressure_bar"),
            water_temperature_C=water_data.get("water_temperature_C"),
            water_quality_standard=water_data.get("water_quality_standard")
        )
    
    def _get_room_type_defaults(self, room_type: str) -> Dict[str, Any]:
        """Get default performance requirements for room type."""
        defaults = {
            "111": {  # Oppholdsrom
                "fire": {
                    "fire_compartment": "Standard",
                    "fire_class": "B-s1, d0",
                    "door_rating": "EI30",
                    "penetration_sealing_class": "EI30",
                    "fire_resistance_rating": "EI30",
                    "smoke_control": False,
                    "escape_route": True
                },
                "acoustics": {
                    "class_ns8175": "C",
                    "rw_dB": 45.0,
                    "ln_w_dB": 60.0,
                    "background_noise_dB": 35.0,
                    "reverberation_time_s": 0.6,
                    "speech_intelligibility": "Good"
                },
                "thermal": {
                    "setpoint_heating_C": 21.0,
                    "setpoint_cooling_C": 24.0,
                    "u_values": {
                        "walls_W_m2K": 0.18,
                        "floor_W_m2K": 0.15,
                        "ceiling_W_m2K": 0.15,
                        "window_W_m2K": 1.2
                    },
                    "thermal_comfort_class": "B",
                    "heating_load_W": 50.0,
                    "cooling_load_W": 30.0
                },
                "ventilation": {
                    "airflow_supply_m3h": 30.0,
                    "airflow_extract_m3h": 30.0,
                    "co2_setpoint_ppm": 1000.0,
                    "pressure_room_Pa": 0.0,
                    "air_changes_per_hour": 0.5,
                    "ventilation_type": "Mechanical",
                    "filtration_class": "G4"
                },
                "lighting": {
                    "task_lux": 300.0,
                    "emergency_lighting": True,
                    "color_rendering_CRI": 80.0,
                    "UGR_max": 19.0,
                    "daylight_factor": 2.0,
                    "lighting_control": "Manual",
                    "energy_efficiency_class": "A"
                },
                "power_data": {
                    "sockets_count": 8,
                    "data_outlets_count": 2,
                    "cleaning_socket": True,
                    "circuits": [
                        {"type": "General", "rating_A": 16, "description": "General power outlets"},
                        {"type": "Lighting", "rating_A": 10, "description": "Lighting circuit"}
                    ],
                    "power_density_W_m2": 10.0,
                    "emergency_power": False,
                    "UPS_required": False
                },
                "water_sanitary": {
                    "fixtures": [],
                    "hot_cold_water": False,
                    "drainage_required": False,
                    "water_pressure_bar": None,
                    "water_temperature_C": None,
                    "water_quality_standard": None
                }
            },
            "130": {  # Våtrom
                "fire": {
                    "fire_compartment": "Standard",
                    "fire_class": "B-s1, d0",
                    "door_rating": "EI30",
                    "penetration_sealing_class": "EI30",
                    "fire_resistance_rating": "EI30",
                    "smoke_control": False,
                    "escape_route": True
                },
                "acoustics": {
                    "class_ns8175": "C",
                    "rw_dB": 50.0,
                    "ln_w_dB": 55.0,
                    "background_noise_dB": 30.0,
                    "reverberation_time_s": 0.4,
                    "speech_intelligibility": "Good"
                },
                "thermal": {
                    "setpoint_heating_C": 24.0,
                    "setpoint_cooling_C": 26.0,
                    "u_values": {
                        "walls_W_m2K": 0.15,
                        "floor_W_m2K": 0.12,
                        "ceiling_W_m2K": 0.12,
                        "window_W_m2K": 1.2
                    },
                    "thermal_comfort_class": "A",
                    "heating_load_W": 60.0,
                    "cooling_load_W": 20.0
                },
                "ventilation": {
                    "airflow_supply_m3h": 50.0,
                    "airflow_extract_m3h": 60.0,
                    "co2_setpoint_ppm": 800.0,
                    "pressure_room_Pa": -5.0,
                    "air_changes_per_hour": 1.0,
                    "ventilation_type": "Mechanical",
                    "filtration_class": "F7"
                },
                "lighting": {
                    "task_lux": 500.0,
                    "emergency_lighting": True,
                    "color_rendering_CRI": 90.0,
                    "UGR_max": 16.0,
                    "daylight_factor": 1.5,
                    "lighting_control": "Automatic",
                    "energy_efficiency_class": "A+"
                },
                "power_data": {
                    "sockets_count": 4,
                    "data_outlets_count": 1,
                    "cleaning_socket": True,
                    "circuits": [
                        {"type": "General", "rating_A": 16, "description": "General power outlets"},
                        {"type": "Lighting", "rating_A": 10, "description": "Lighting circuit"},
                        {"type": "Ventilation", "rating_A": 16, "description": "Ventilation fan"}
                    ],
                    "power_density_W_m2": 15.0,
                    "emergency_power": False,
                    "UPS_required": False
                },
                "water_sanitary": {
                    "fixtures": [
                        {"type": "Shower", "quantity": 1, "water_flow_l_min": 10.0},
                        {"type": "WC", "quantity": 1, "water_flow_l_min": 6.0},
                        {"type": "Washbasin", "quantity": 1, "water_flow_l_min": 6.0}
                    ],
                    "hot_cold_water": True,
                    "drainage_required": True,
                    "water_pressure_bar": 3.0,
                    "water_temperature_C": 60.0,
                    "water_quality_standard": "NS-EN 1717"
                }
            },
            "131": {  # WC
                "fire": {
                    "fire_compartment": "Standard",
                    "fire_class": "B-s1, d0",
                    "door_rating": "EI30",
                    "penetration_sealing_class": "EI30",
                    "fire_resistance_rating": "EI30",
                    "smoke_control": False,
                    "escape_route": True
                },
                "acoustics": {
                    "class_ns8175": "C",
                    "rw_dB": 45.0,
                    "ln_w_dB": 55.0,
                    "background_noise_dB": 30.0,
                    "reverberation_time_s": 0.4,
                    "speech_intelligibility": "Good"
                },
                "thermal": {
                    "setpoint_heating_C": 22.0,
                    "setpoint_cooling_C": 25.0,
                    "u_values": {
                        "walls_W_m2K": 0.15,
                        "floor_W_m2K": 0.12,
                        "ceiling_W_m2K": 0.12,
                        "window_W_m2K": 1.2
                    },
                    "thermal_comfort_class": "B",
                    "heating_load_W": 40.0,
                    "cooling_load_W": 15.0
                },
                "ventilation": {
                    "airflow_supply_m3h": 20.0,
                    "airflow_extract_m3h": 30.0,
                    "co2_setpoint_ppm": 1000.0,
                    "pressure_room_Pa": -5.0,
                    "air_changes_per_hour": 0.8,
                    "ventilation_type": "Mechanical",
                    "filtration_class": "G4"
                },
                "lighting": {
                    "task_lux": 300.0,
                    "emergency_lighting": True,
                    "color_rendering_CRI": 80.0,
                    "UGR_max": 19.0,
                    "daylight_factor": 1.0,
                    "lighting_control": "Automatic",
                    "energy_efficiency_class": "A"
                },
                "power_data": {
                    "sockets_count": 2,
                    "data_outlets_count": 0,
                    "cleaning_socket": True,
                    "circuits": [
                        {"type": "General", "rating_A": 16, "description": "General power outlets"},
                        {"type": "Lighting", "rating_A": 10, "description": "Lighting circuit"}
                    ],
                    "power_density_W_m2": 8.0,
                    "emergency_power": False,
                    "UPS_required": False
                },
                "water_sanitary": {
                    "fixtures": [
                        {"type": "WC", "quantity": 1, "water_flow_l_min": 6.0},
                        {"type": "Washbasin", "quantity": 1, "water_flow_l_min": 6.0}
                    ],
                    "hot_cold_water": True,
                    "drainage_required": True,
                    "water_pressure_bar": 3.0,
                    "water_temperature_C": 60.0,
                    "water_quality_standard": "NS-EN 1717"
                }
            },
            "132": {  # Baderom
                "fire": {
                    "fire_compartment": "Standard",
                    "fire_class": "B-s1, d0",
                    "door_rating": "EI30",
                    "penetration_sealing_class": "EI30",
                    "fire_resistance_rating": "EI30",
                    "smoke_control": False,
                    "escape_route": True
                },
                "acoustics": {
                    "class_ns8175": "C",
                    "rw_dB": 50.0,
                    "ln_w_dB": 55.0,
                    "background_noise_dB": 30.0,
                    "reverberation_time_s": 0.4,
                    "speech_intelligibility": "Good"
                },
                "thermal": {
                    "setpoint_heating_C": 24.0,
                    "setpoint_cooling_C": 26.0,
                    "u_values": {
                        "walls_W_m2K": 0.15,
                        "floor_W_m2K": 0.12,
                        "ceiling_W_m2K": 0.12,
                        "window_W_m2K": 1.2
                    },
                    "thermal_comfort_class": "A",
                    "heating_load_W": 60.0,
                    "cooling_load_W": 20.0
                },
                "ventilation": {
                    "airflow_supply_m3h": 50.0,
                    "airflow_extract_m3h": 60.0,
                    "co2_setpoint_ppm": 800.0,
                    "pressure_room_Pa": -5.0,
                    "air_changes_per_hour": 1.0,
                    "ventilation_type": "Mechanical",
                    "filtration_class": "F7"
                },
                "lighting": {
                    "task_lux": 500.0,
                    "emergency_lighting": True,
                    "color_rendering_CRI": 90.0,
                    "UGR_max": 16.0,
                    "daylight_factor": 1.5,
                    "lighting_control": "Automatic",
                    "energy_efficiency_class": "A+"
                },
                "power_data": {
                    "sockets_count": 4,
                    "data_outlets_count": 1,
                    "cleaning_socket": True,
                    "circuits": [
                        {"type": "General", "rating_A": 16, "description": "General power outlets"},
                        {"type": "Lighting", "rating_A": 10, "description": "Lighting circuit"},
                        {"type": "Ventilation", "rating_A": 16, "description": "Ventilation fan"}
                    ],
                    "power_density_W_m2": 15.0,
                    "emergency_power": False,
                    "UPS_required": False
                },
                "water_sanitary": {
                    "fixtures": [
                        {"type": "Bathtub", "quantity": 1, "water_flow_l_min": 15.0},
                        {"type": "Shower", "quantity": 1, "water_flow_l_min": 10.0},
                        {"type": "WC", "quantity": 1, "water_flow_l_min": 6.0},
                        {"type": "Washbasin", "quantity": 1, "water_flow_l_min": 6.0}
                    ],
                    "hot_cold_water": True,
                    "drainage_required": True,
                    "water_pressure_bar": 3.0,
                    "water_temperature_C": 60.0,
                    "water_quality_standard": "NS-EN 1717"
                }
            },
            "140": {  # Kjøkken
                "fire": {
                    "fire_compartment": "Standard",
                    "fire_class": "B-s1, d0",
                    "door_rating": "EI30",
                    "penetration_sealing_class": "EI30",
                    "fire_resistance_rating": "EI30",
                    "smoke_control": True,
                    "escape_route": True
                },
                "acoustics": {
                    "class_ns8175": "C",
                    "rw_dB": 45.0,
                    "ln_w_dB": 60.0,
                    "background_noise_dB": 40.0,
                    "reverberation_time_s": 0.5,
                    "speech_intelligibility": "Good"
                },
                "thermal": {
                    "setpoint_heating_C": 20.0,
                    "setpoint_cooling_C": 24.0,
                    "u_values": {
                        "walls_W_m2K": 0.18,
                        "floor_W_m2K": 0.15,
                        "ceiling_W_m2K": 0.15,
                        "window_W_m2K": 1.2
                    },
                    "thermal_comfort_class": "B",
                    "heating_load_W": 60.0,
                    "cooling_load_W": 40.0
                },
                "ventilation": {
                    "airflow_supply_m3h": 100.0,
                    "airflow_extract_m3h": 120.0,
                    "co2_setpoint_ppm": 1000.0,
                    "pressure_room_Pa": -10.0,
                    "air_changes_per_hour": 1.5,
                    "ventilation_type": "Mechanical",
                    "filtration_class": "F7"
                },
                "lighting": {
                    "task_lux": 500.0,
                    "emergency_lighting": True,
                    "color_rendering_CRI": 90.0,
                    "UGR_max": 16.0,
                    "daylight_factor": 2.0,
                    "lighting_control": "Manual",
                    "energy_efficiency_class": "A+"
                },
                "power_data": {
                    "sockets_count": 12,
                    "data_outlets_count": 2,
                    "cleaning_socket": True,
                    "circuits": [
                        {"type": "General", "rating_A": 16, "description": "General power outlets"},
                        {"type": "Lighting", "rating_A": 10, "description": "Lighting circuit"},
                        {"type": "Kitchen", "rating_A": 20, "description": "Kitchen appliances"},
                        {"type": "Ventilation", "rating_A": 16, "description": "Kitchen ventilation"}
                    ],
                    "power_density_W_m2": 25.0,
                    "emergency_power": False,
                    "UPS_required": False
                },
                "water_sanitary": {
                    "fixtures": [
                        {"type": "Kitchen sink", "quantity": 1, "water_flow_l_min": 8.0},
                        {"type": "Dishwasher", "quantity": 1, "water_flow_l_min": 10.0},
                        {"type": "Washing machine", "quantity": 1, "water_flow_l_min": 12.0}
                    ],
                    "hot_cold_water": True,
                    "drainage_required": True,
                    "water_pressure_bar": 3.0,
                    "water_temperature_C": 60.0,
                    "water_quality_standard": "NS-EN 1717"
                }
            }
        }
        
        return defaults.get(room_type, defaults["111"])  # Default to oppholdsrom


# Example usage and testing
if __name__ == "__main__":
    mapper = PerformanceRequirementsMapper()
    
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
    
    print("Performance Requirements Mapper Test:")
    print("=" * 50)
    
    # Test performance extraction
    performance = mapper.extract_performance_requirements(sample_space)
    print(f"Fire class: {performance.fire.fire_class}")
    print(f"Acoustic class: {performance.acoustics.class_ns8175}")
    print(f"Heating setpoint: {performance.thermal.setpoint_heating_C}°C")
    print(f"Ventilation: {performance.ventilation.airflow_supply_m3h} m³/h")
    print(f"Lighting: {performance.lighting.task_lux} lux")
    print(f"Power sockets: {performance.power_data.sockets_count}")
    print(f"Water fixtures: {len(performance.water_sanitary.fixtures)}")
    
    # Test defaults
    defaults = mapper.apply_performance_defaults("130")  # Våtrom
    print(f"\nVåtrom defaults:")
    print(f"Fire class: {defaults.fire.fire_class}")
    print(f"Acoustic class: {defaults.acoustics.class_ns8175}")
    print(f"Heating setpoint: {defaults.thermal.setpoint_heating_C}°C")
    print(f"Ventilation: {defaults.ventilation.airflow_supply_m3h} m³/h")
    print(f"Lighting: {defaults.lighting.task_lux} lux")
    print(f"Power sockets: {defaults.power_data.sockets_count}")
    print(f"Water fixtures: {len(defaults.water_sanitary.fixtures)}")
    print(f"Water fixtures: {[f['type'] for f in defaults.water_sanitary.fixtures]}")
