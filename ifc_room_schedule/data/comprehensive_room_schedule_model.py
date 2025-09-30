"""
Comprehensive Room Schedule Model

Data model that matches the comprehensive JSON template structure
for room schedule data with all required sections.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum


@dataclass
class MetaSection:
    """Meta information section."""
    
    schema_version: str = "1.1.0"
    locale: str = "nb-NO"
    created_at: Optional[str] = None
    revised_at: Optional[str] = None
    created_by: Optional[str] = None
    revised_by: Optional[str] = None
    revision: int = 0
    status: Dict[str, str] = field(default_factory=lambda: {
        "phase": "Forprosjekt",
        "state": "Utkast"
    })
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "locale": self.locale,
            "created_at": self.created_at,
            "revised_at": self.revised_at,
            "created_by": self.created_by,
            "revised_by": self.revised_by,
            "revision": self.revision,
            "status": self.status
        }


@dataclass
class IdentificationSection:
    """Identification section."""
    
    project_id: Optional[str] = None
    project_name: Optional[str] = None
    building_id: Optional[str] = None
    building_name: Optional[str] = None
    storey_name: Optional[str] = None
    storey_elevation_m: Optional[float] = None
    room_number: Optional[str] = None
    room_name: Optional[str] = None
    function: Optional[str] = None
    occupancy_type: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_id": self.project_id,
            "project_name": self.project_name,
            "building_id": self.building_id,
            "building_name": self.building_name,
            "storey_name": self.storey_name,
            "storey_elevation_m": self.storey_elevation_m,
            "room_number": self.room_number,
            "room_name": self.room_name,
            "function": self.function,
            "occupancy_type": self.occupancy_type
        }


@dataclass
class ModelSource:
    """IFC model source information."""
    
    file_name: Optional[str] = None
    file_version: str = "IFC4"
    discipline: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_name": self.file_name,
            "file_version": self.file_version,
            "discipline": self.discipline
        }


@dataclass
class IFCSection:
    """IFC section with space and model information."""
    
    space_global_id: Optional[str] = None
    space_long_name: Optional[str] = None
    space_number: Optional[str] = None
    site_guid: Optional[str] = None
    building_guid: Optional[str] = None
    storey_guid: Optional[str] = None
    model_source: ModelSource = field(default_factory=ModelSource)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "space_global_id": self.space_global_id,
            "space_long_name": self.space_long_name,
            "space_number": self.space_number,
            "site_guid": self.site_guid,
            "building_guid": self.building_guid,
            "storey_guid": self.storey_guid,
            "model_source": self.model_source.to_dict()
        }


@dataclass
class ClassificationSection:
    """Classification section with NS codes."""
    
    ns3451: Optional[str] = None
    tfm: Optional[str] = None
    custom_codes: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "ns3451": self.ns3451,
            "tfm": self.tfm,
            "custom_codes": self.custom_codes
        }


@dataclass
class RoomLocalOrigin:
    """Room local origin coordinates."""
    
    x_m: float = 0.0
    y_m: float = 0.0
    z_m: float = 0.0
    description: str = "Lokal 0,0,0 (m)"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "x_m": self.x_m,
            "y_m": self.y_m,
            "z_m": self.z_m,
            "description": self.description
        }


@dataclass
class GeometrySection:
    """Geometry section with room dimensions."""
    
    area_nett_m2: Optional[float] = None
    area_brutto_m2: Optional[float] = None
    perimeter_m: Optional[float] = None
    length_m: Optional[float] = None
    width_m: Optional[float] = None
    clear_height_m: Optional[float] = None
    floor_load_kN_m2: Optional[float] = None
    room_local_origin: RoomLocalOrigin = field(default_factory=RoomLocalOrigin)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "area_nett_m2": self.area_nett_m2,
            "area_brutto_m2": self.area_brutto_m2,
            "perimeter_m": self.perimeter_m,
            "length_m": self.length_m,
            "width_m": self.width_m,
            "clear_height_m": self.clear_height_m,
            "floor_load_kN_m2": self.floor_load_kN_m2,
            "room_local_origin": self.room_local_origin.to_dict()
        }


@dataclass
class FireRequirements:
    """Fire safety requirements."""
    
    fire_compartment: Optional[str] = None
    fire_class: Optional[str] = None
    door_rating: Optional[str] = None
    penetration_sealing_class: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "fire_compartment": self.fire_compartment,
            "fire_class": self.fire_class,
            "door_rating": self.door_rating,
            "penetration_sealing_class": self.penetration_sealing_class
        }


@dataclass
class AcousticsRequirements:
    """Acoustics requirements."""
    
    class_ns8175: Optional[str] = None
    rw_dB: Optional[float] = None
    ln_w_dB: Optional[float] = None
    background_noise_dB: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "class_ns8175": self.class_ns8175,
            "rw_dB": self.rw_dB,
            "ln_w_dB": self.ln_w_dB,
            "background_noise_dB": self.background_noise_dB
        }


@dataclass
class UValues:
    """U-values for thermal performance."""
    
    walls_W_m2K: Optional[float] = None
    floor_W_m2K: Optional[float] = None
    ceiling_W_m2K: Optional[float] = None
    window_W_m2K: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "walls_W_m2K": self.walls_W_m2K,
            "floor_W_m2K": self.floor_W_m2K,
            "ceiling_W_m2K": self.ceiling_W_m2K,
            "window_W_m2K": self.window_W_m2K
        }


@dataclass
class ThermalRequirements:
    """Thermal requirements."""
    
    setpoint_heating_C: Optional[float] = None
    setpoint_cooling_C: Optional[float] = None
    u_values: UValues = field(default_factory=UValues)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "setpoint_heating_C": self.setpoint_heating_C,
            "setpoint_cooling_C": self.setpoint_cooling_C,
            "u_values": self.u_values.to_dict()
        }


@dataclass
class VentilationRequirements:
    """Ventilation requirements."""
    
    airflow_supply_m3h: Optional[float] = None
    airflow_extract_m3h: Optional[float] = None
    co2_setpoint_ppm: Optional[int] = None
    pressure_room_Pa: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "airflow_supply_m3h": self.airflow_supply_m3h,
            "airflow_extract_m3h": self.airflow_extract_m3h,
            "co2_setpoint_ppm": self.co2_setpoint_ppm,
            "pressure_room_Pa": self.pressure_room_Pa
        }


@dataclass
class LightingRequirements:
    """Lighting requirements."""
    
    task_lux: Optional[int] = None
    emergency_lighting: bool = False
    color_rendering_CRI: Optional[int] = None
    UGR_max: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_lux": self.task_lux,
            "emergency_lighting": self.emergency_lighting,
            "color_rendering_CRI": self.color_rendering_CRI,
            "UGR_max": self.UGR_max
        }


@dataclass
class PowerDataRequirements:
    """Power and data requirements."""
    
    sockets_count: Optional[int] = None
    data_outlets_count: Optional[int] = None
    cleaning_socket: bool = False
    circuits: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "sockets_count": self.sockets_count,
            "data_outlets_count": self.data_outlets_count,
            "cleaning_socket": self.cleaning_socket,
            "circuits": self.circuits
        }


@dataclass
class WaterSanitaryRequirements:
    """Water and sanitary requirements."""
    
    fixtures: List[Dict[str, Any]] = field(default_factory=list)
    hot_cold_water: bool = False
    drainage_required: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "fixtures": self.fixtures,
            "hot_cold_water": self.hot_cold_water,
            "drainage_required": self.drainage_required
        }


@dataclass
class PerformanceRequirementsSection:
    """Performance requirements section."""
    
    fire: FireRequirements = field(default_factory=FireRequirements)
    acoustics: AcousticsRequirements = field(default_factory=AcousticsRequirements)
    thermal: ThermalRequirements = field(default_factory=ThermalRequirements)
    ventilation: VentilationRequirements = field(default_factory=VentilationRequirements)
    lighting: LightingRequirements = field(default_factory=LightingRequirements)
    power_data: PowerDataRequirements = field(default_factory=PowerDataRequirements)
    water_sanitary: WaterSanitaryRequirements = field(default_factory=WaterSanitaryRequirements)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "fire": self.fire.to_dict(),
            "acoustics": self.acoustics.to_dict(),
            "thermal": self.thermal.to_dict(),
            "ventilation": self.ventilation.to_dict(),
            "lighting": self.lighting.to_dict(),
            "power_data": self.power_data.to_dict(),
            "water_sanitary": self.water_sanitary.to_dict()
        }


@dataclass
class ComprehensiveRoomSchedule:
    """Comprehensive room schedule matching the JSON template structure."""
    
    meta: MetaSection = field(default_factory=MetaSection)
    identification: IdentificationSection = field(default_factory=IdentificationSection)
    ifc: IFCSection = field(default_factory=IFCSection)
    classification: ClassificationSection = field(default_factory=ClassificationSection)
    geometry: GeometrySection = field(default_factory=GeometrySection)
    performance_requirements: PerformanceRequirementsSection = field(default_factory=PerformanceRequirementsSection)
    
    # Additional sections can be added here as needed
    finishes: Optional[Dict[str, Any]] = None
    openings: Optional[Dict[str, Any]] = None
    fixtures_and_equipment: List[Dict[str, Any]] = field(default_factory=list)
    hse_and_accessibility: Optional[Dict[str, Any]] = None
    environment: Optional[Dict[str, Any]] = None
    tolerances_and_quality: Optional[Dict[str, Any]] = None
    qa_qc: Optional[Dict[str, Any]] = None
    interfaces: Optional[Dict[str, Any]] = None
    logistics_and_site: Optional[Dict[str, Any]] = None
    commissioning: Optional[Dict[str, Any]] = None
    attachments: List[Dict[str, Any]] = field(default_factory=list)
    notes: Optional[str] = None
    deviations: List[Dict[str, Any]] = field(default_factory=list)
    links: Optional[Dict[str, Any]] = None
    catalogs: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary matching the JSON template structure."""
        result = {
            "meta": self.meta.to_dict(),
            "identification": self.identification.to_dict(),
            "ifc": self.ifc.to_dict(),
            "classification": self.classification.to_dict(),
            "geometry": self.geometry.to_dict(),
            "performance_requirements": self.performance_requirements.to_dict(),
            "fixtures_and_equipment": self.fixtures_and_equipment,
            "attachments": self.attachments,
            "notes": self.notes,
            "deviations": self.deviations
        }
        
        # Add optional sections if they exist
        if self.finishes:
            result["finishes"] = self.finishes
        if self.openings:
            result["openings"] = self.openings
        if self.hse_and_accessibility:
            result["hse_and_accessibility"] = self.hse_and_accessibility
        if self.environment:
            result["environment"] = self.environment
        if self.tolerances_and_quality:
            result["tolerances_and_quality"] = self.tolerances_and_quality
        if self.qa_qc:
            result["qa_qc"] = self.qa_qc
        if self.interfaces:
            result["interfaces"] = self.interfaces
        if self.logistics_and_site:
            result["logistics_and_site"] = self.logistics_and_site
        if self.commissioning:
            result["commissioning"] = self.commissioning
        if self.links:
            result["links"] = self.links
        if self.catalogs:
            result["catalogs"] = self.catalogs
        
        return result
    
    @classmethod
    def from_space_data(cls, space_data, project_info: Optional[Dict[str, Any]] = None) -> 'ComprehensiveRoomSchedule':
        """Create comprehensive room schedule from space data."""
        schedule = cls()
        
        # Populate from space data
        if hasattr(space_data, 'guid'):
            schedule.ifc.space_global_id = space_data.guid
        if hasattr(space_data, 'name'):
            schedule.identification.room_name = space_data.name
        if hasattr(space_data, 'long_name'):
            schedule.ifc.space_long_name = space_data.long_name
        if hasattr(space_data, 'number'):
            schedule.identification.room_number = space_data.number
        
        # Populate geometry from quantities
        if hasattr(space_data, 'quantities') and space_data.quantities:
            quantities = space_data.quantities
            if 'NetArea' in quantities:
                schedule.geometry.area_nett_m2 = quantities['NetArea']
            if 'GrossArea' in quantities:
                schedule.geometry.area_brutto_m2 = quantities['GrossArea']
            if 'Height' in quantities:
                schedule.geometry.clear_height_m = quantities['Height']
            if 'Perimeter' in quantities:
                schedule.geometry.perimeter_m = quantities['Perimeter']
        
        # Add project information if provided
        if project_info:
            if 'project_name' in project_info:
                schedule.identification.project_name = project_info['project_name']
            if 'building_name' in project_info:
                schedule.identification.building_name = project_info['building_name']
        
        # Set creation timestamp
        schedule.meta.created_at = datetime.now().isoformat()
        
        return schedule
    
    def populate_from_ifc_data(self, ifc_data: Dict[str, Any]):
        """Populate fields from IFC data."""
        # IFC hierarchy
        if 'site_guid' in ifc_data:
            self.ifc.site_guid = ifc_data['site_guid']
        if 'building_guid' in ifc_data:
            self.ifc.building_guid = ifc_data['building_guid']
        if 'storey_guid' in ifc_data:
            self.ifc.storey_guid = ifc_data['storey_guid']
        
        # Model source
        if 'file_name' in ifc_data:
            self.ifc.model_source.file_name = ifc_data['file_name']
        if 'ifc_version' in ifc_data:
            self.ifc.model_source.file_version = ifc_data['ifc_version']
    
    def populate_user_data(self, user_data: Dict[str, Any]):
        """Populate fields that require user input."""
        # This method would be called to populate data that cannot be extracted from IFC
        # Examples: performance requirements, finishes, etc.
        
        if 'performance_requirements' in user_data:
            perf_data = user_data['performance_requirements']
            
            # Fire requirements
            if 'fire' in perf_data:
                fire_data = perf_data['fire']
                self.performance_requirements.fire.fire_class = fire_data.get('fire_class')
                self.performance_requirements.fire.door_rating = fire_data.get('door_rating')
            
            # Acoustics requirements
            if 'acoustics' in perf_data:
                acoustics_data = perf_data['acoustics']
                self.performance_requirements.acoustics.class_ns8175 = acoustics_data.get('class_ns8175')
                self.performance_requirements.acoustics.rw_dB = acoustics_data.get('rw_dB')
        
        # Add other user data sections as needed
        if 'finishes' in user_data:
            self.finishes = user_data['finishes']
        
        if 'notes' in user_data:
            self.notes = user_data['notes']