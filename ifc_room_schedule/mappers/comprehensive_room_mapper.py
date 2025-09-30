"""
Comprehensive Room Mapper

Maps space data to the comprehensive room schedule structure
that matches the JSON template format.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from ..data.space_model import SpaceData
from ..data.comprehensive_room_schedule_model import ComprehensiveRoomSchedule
from ..parsers.ns8360_name_parser import NS8360NameParser
from ..mappers.ns3940_classifier import NS3940Classifier


class ComprehensiveRoomMapper:
    """Maps space data to comprehensive room schedule format."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.name_parser = NS8360NameParser()
        self.classifier = NS3940Classifier()
    
    def map_space_to_comprehensive_schedule(
        self, 
        space: SpaceData, 
        project_info: Optional[Dict[str, Any]] = None,
        ifc_info: Optional[Dict[str, Any]] = None,
        user_data: Optional[Dict[str, Any]] = None
    ) -> ComprehensiveRoomSchedule:
        """
        Map a space to comprehensive room schedule format.
        
        Args:
            space: Space data from IFC
            project_info: Project-level information
            ifc_info: IFC file and model information
            user_data: User-provided data that cannot be extracted from IFC
            
        Returns:
            ComprehensiveRoomSchedule instance
        """
        schedule = ComprehensiveRoomSchedule()
        
        # Populate meta section
        self._populate_meta_section(schedule, project_info)
        
        # Populate identification section
        self._populate_identification_section(schedule, space, project_info)
        
        # Populate IFC section
        self._populate_ifc_section(schedule, space, ifc_info)
        
        # Populate classification section
        self._populate_classification_section(schedule, space)
        
        # Populate geometry section
        self._populate_geometry_section(schedule, space)
        
        # Populate performance requirements (from user data or defaults)
        self._populate_performance_requirements(schedule, space, user_data)
        
        # Populate user-provided sections
        if user_data:
            schedule.populate_user_data(user_data)
        
        return schedule
    
    def _populate_meta_section(self, schedule: ComprehensiveRoomSchedule, project_info: Optional[Dict[str, Any]]):
        """Populate meta section with project and creation information."""
        schedule.meta.created_at = datetime.now().isoformat()
        schedule.meta.revision = 0
        
        if project_info:
            schedule.meta.created_by = project_info.get('created_by')
            if 'phase' in project_info:
                schedule.meta.status['phase'] = project_info['phase']
            if 'state' in project_info:
                schedule.meta.status['state'] = project_info['state']
    
    def _populate_identification_section(
        self, 
        schedule: ComprehensiveRoomSchedule, 
        space: SpaceData, 
        project_info: Optional[Dict[str, Any]]
    ):
        """Populate identification section from space and project data."""
        # Basic room information
        schedule.identification.room_name = space.name
        schedule.identification.room_number = space.number
        
        # Parse NS 8360 name if available
        if space.name:
            try:
                parsed_name = self.name_parser.parse(space.name)
                if parsed_name and parsed_name.is_valid:
                    schedule.identification.function = parsed_name.function_code
                    if hasattr(parsed_name, 'storey'):
                        schedule.identification.storey_name = parsed_name.storey
            except Exception as e:
                self.logger.warning(f"Failed to parse NS 8360 name '{space.name}': {e}")
        
        # Project information
        if project_info:
            schedule.identification.project_id = project_info.get('project_id')
            schedule.identification.project_name = project_info.get('project_name')
            schedule.identification.building_id = project_info.get('building_id')
            schedule.identification.building_name = project_info.get('building_name')
            schedule.identification.storey_elevation_m = project_info.get('storey_elevation_m')
        
        # Determine occupancy type from classification
        if space.name:
            try:
                classification = self.classifier.classify_space(space.name)
                if classification:
                    schedule.identification.occupancy_type = classification.get('occupancy_type')
            except Exception as e:
                self.logger.warning(f"Failed to classify space '{space.name}': {e}")
    
    def _populate_ifc_section(
        self, 
        schedule: ComprehensiveRoomSchedule, 
        space: SpaceData, 
        ifc_info: Optional[Dict[str, Any]]
    ):
        """Populate IFC section with space and model information."""
        # Space information
        schedule.ifc.space_global_id = space.guid
        schedule.ifc.space_long_name = space.long_name
        schedule.ifc.space_number = space.number
        
        # IFC hierarchy (if available)
        if ifc_info:
            schedule.ifc.site_guid = ifc_info.get('site_guid')
            schedule.ifc.building_guid = ifc_info.get('building_guid')
            schedule.ifc.storey_guid = ifc_info.get('storey_guid')
            
            # Model source information
            schedule.ifc.model_source.file_name = ifc_info.get('file_name')
            schedule.ifc.model_source.file_version = ifc_info.get('ifc_version', 'IFC4')
            schedule.ifc.model_source.discipline = ifc_info.get('discipline', 'ARK')
    
    def _populate_classification_section(self, schedule: ComprehensiveRoomSchedule, space: SpaceData):
        """Populate classification section with NS codes."""
        if space.name:
            try:
                # Try to extract NS 3451 code from name or classification
                classification = self.classifier.classify_space(space.name)
                if classification:
                    schedule.classification.ns3451 = classification.get('ns3940_code')
                    
                    # Add custom codes if available
                    if 'custom_codes' in classification:
                        schedule.classification.custom_codes = classification['custom_codes']
            except Exception as e:
                self.logger.warning(f"Failed to classify space for NS codes '{space.name}': {e}")
    
    def _populate_geometry_section(self, schedule: ComprehensiveRoomSchedule, space: SpaceData):
        """Populate geometry section from space quantities."""
        if space.quantities:
            quantities = space.quantities
            
            # Area information
            if 'NetArea' in quantities:
                schedule.geometry.area_nett_m2 = float(quantities['NetArea'])
            if 'GrossArea' in quantities:
                schedule.geometry.area_brutto_m2 = float(quantities['GrossArea'])
            
            # Dimensional information
            if 'Height' in quantities:
                schedule.geometry.clear_height_m = float(quantities['Height'])
            if 'Perimeter' in quantities:
                schedule.geometry.perimeter_m = float(quantities['Perimeter'])
            
            # Try to calculate length and width from area and perimeter
            if 'NetArea' in quantities and 'Perimeter' in quantities:
                area = float(quantities['NetArea'])
                perimeter = float(quantities['Perimeter'])
                
                # Assume rectangular room for estimation
                # P = 2(L + W), A = L * W
                # Solve for L and W assuming square-ish room
                if perimeter > 0 and area > 0:
                    # Estimate dimensions (this is a rough approximation)
                    estimated_side = (area ** 0.5)  # Square root of area
                    schedule.geometry.length_m = estimated_side
                    schedule.geometry.width_m = estimated_side
        
        # Set local origin (default to 0,0,0)
        schedule.geometry.room_local_origin.description = f"Lokal 0,0,0 for rom {space.name or space.guid}"
    
    def _populate_performance_requirements(
        self, 
        schedule: ComprehensiveRoomSchedule, 
        space: SpaceData, 
        user_data: Optional[Dict[str, Any]]
    ):
        """Populate performance requirements from space classification and user data."""
        # Get room classification for default requirements
        classification = None
        if space.name:
            try:
                classification = self.classifier.classify_space(space.name)
            except Exception as e:
                self.logger.warning(f"Failed to classify space for performance requirements '{space.name}': {e}")
        
        # Set default requirements based on room type
        if classification:
            room_type = classification.get('room_type', '').lower()
            
            # Fire requirements based on room type
            if 'våtrom' in room_type or 'bad' in room_type:
                schedule.performance_requirements.fire.fire_class = "Standard"
                schedule.performance_requirements.fire.door_rating = "EI30"
            elif 'kjøkken' in room_type:
                schedule.performance_requirements.fire.fire_class = "Forhøyet"
                schedule.performance_requirements.fire.door_rating = "EI30"
            
            # Acoustics requirements
            if 'soverom' in room_type:
                schedule.performance_requirements.acoustics.class_ns8175 = "B"
                schedule.performance_requirements.acoustics.background_noise_dB = 30.0
            elif 'oppholdsrom' in room_type or 'stue' in room_type:
                schedule.performance_requirements.acoustics.class_ns8175 = "C"
                schedule.performance_requirements.acoustics.background_noise_dB = 35.0
            
            # Lighting requirements
            if 'kjøkken' in room_type:
                schedule.performance_requirements.lighting.task_lux = 500
            elif 'bad' in room_type or 'våtrom' in room_type:
                schedule.performance_requirements.lighting.task_lux = 300
            elif 'soverom' in room_type:
                schedule.performance_requirements.lighting.task_lux = 100
            else:
                schedule.performance_requirements.lighting.task_lux = 200
            
            # Ventilation requirements
            if 'våtrom' in room_type or 'bad' in room_type:
                schedule.performance_requirements.ventilation.airflow_extract_m3h = 108.0  # 30 l/s
            elif 'kjøkken' in room_type:
                schedule.performance_requirements.ventilation.airflow_extract_m3h = 144.0  # 40 l/s
        
        # Override with user data if provided
        if user_data and 'performance_requirements' in user_data:
            perf_data = user_data['performance_requirements']
            
            # Fire requirements
            if 'fire' in perf_data:
                fire_data = perf_data['fire']
                if 'fire_class' in fire_data:
                    schedule.performance_requirements.fire.fire_class = fire_data['fire_class']
                if 'door_rating' in fire_data:
                    schedule.performance_requirements.fire.door_rating = fire_data['door_rating']
            
            # Acoustics requirements
            if 'acoustics' in perf_data:
                acoustics_data = perf_data['acoustics']
                if 'class_ns8175' in acoustics_data:
                    schedule.performance_requirements.acoustics.class_ns8175 = acoustics_data['class_ns8175']
                if 'rw_dB' in acoustics_data:
                    schedule.performance_requirements.acoustics.rw_dB = acoustics_data['rw_dB']
            
            # Continue for other performance requirements...
    
    def map_multiple_spaces(
        self, 
        spaces: List[SpaceData], 
        project_info: Optional[Dict[str, Any]] = None,
        ifc_info: Optional[Dict[str, Any]] = None,
        user_data_per_space: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> List[ComprehensiveRoomSchedule]:
        """
        Map multiple spaces to comprehensive room schedules.
        
        Args:
            spaces: List of space data
            project_info: Project-level information
            ifc_info: IFC file and model information
            user_data_per_space: User data keyed by space GUID
            
        Returns:
            List of ComprehensiveRoomSchedule instances
        """
        schedules = []
        
        for space in spaces:
            try:
                # Get user data for this specific space
                space_user_data = None
                if user_data_per_space and space.guid in user_data_per_space:
                    space_user_data = user_data_per_space[space.guid]
                
                # Map the space
                schedule = self.map_space_to_comprehensive_schedule(
                    space, project_info, ifc_info, space_user_data
                )
                schedules.append(schedule)
                
            except Exception as e:
                self.logger.error(f"Error mapping space {space.guid}: {str(e)}")
                # Continue with other spaces
                continue
        
        return schedules
    
    def create_template_for_user_input(self, space: SpaceData) -> Dict[str, Any]:
        """
        Create a template structure for user input based on space data.
        This shows what data the user needs to provide.
        """
        template = {
            "space_guid": space.guid,
            "space_name": space.name,
            "performance_requirements": {
                "fire": {
                    "fire_compartment": None,
                    "fire_class": None,
                    "door_rating": None,
                    "penetration_sealing_class": None
                },
                "acoustics": {
                    "class_ns8175": None,
                    "rw_dB": None,
                    "ln_w_dB": None,
                    "background_noise_dB": None
                },
                "thermal": {
                    "setpoint_heating_C": None,
                    "setpoint_cooling_C": None,
                    "u_values": {
                        "walls_W_m2K": None,
                        "floor_W_m2K": None,
                        "ceiling_W_m2K": None,
                        "window_W_m2K": None
                    }
                },
                "ventilation": {
                    "airflow_supply_m3h": None,
                    "airflow_extract_m3h": None,
                    "co2_setpoint_ppm": None,
                    "pressure_room_Pa": None
                },
                "lighting": {
                    "task_lux": None,
                    "emergency_lighting": False,
                    "color_rendering_CRI": None,
                    "UGR_max": None
                },
                "power_data": {
                    "sockets_count": None,
                    "data_outlets_count": None,
                    "cleaning_socket": False,
                    "circuits": []
                },
                "water_sanitary": {
                    "fixtures": [],
                    "hot_cold_water": False,
                    "drainage_required": False
                }
            },
            "finishes": {
                "floor": {
                    "system": None,
                    "layers": [],
                    "tolerances": {}
                },
                "ceiling": {
                    "system": None,
                    "height_m": None,
                    "acoustic_class": None,
                    "notes": None
                },
                "walls": [],
                "skirting": {
                    "type": None,
                    "height_mm": None,
                    "material": None
                }
            },
            "notes": None
        }
        
        return template