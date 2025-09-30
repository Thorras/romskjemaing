"""
Comprehensive JSON Builder

Builds JSON exports using the comprehensive room schedule structure
that matches the template format.
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import logging

from ..data.space_model import SpaceData
from ..data.comprehensive_room_schedule_model import ComprehensiveRoomSchedule
from ..mappers.comprehensive_room_mapper import ComprehensiveRoomMapper


class ComprehensiveJsonBuilder:
    """Builds comprehensive JSON exports matching the template structure."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.mapper = ComprehensiveRoomMapper()
        self.source_file = None
        self.ifc_version = "IFC4"
    
    def set_source_file(self, file_path: str):
        """Set the source IFC file path."""
        self.source_file = file_path
    
    def set_ifc_version(self, version: str):
        """Set the IFC version."""
        self.ifc_version = version
    
    def build_comprehensive_json_structure(
        self, 
        spaces: List[SpaceData], 
        project_info: Optional[Dict[str, Any]] = None,
        user_data_per_space: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Build comprehensive JSON structure for multiple spaces.
        
        Args:
            spaces: List of space data
            project_info: Project-level information
            user_data_per_space: User data keyed by space GUID
            
        Returns:
            List of room schedule dictionaries
        """
        # Prepare IFC information
        ifc_info = {
            "file_name": Path(self.source_file).name if self.source_file else None,
            "ifc_version": self.ifc_version,
            "discipline": "ARK"  # Default, could be configurable
        }
        
        # Map spaces to comprehensive schedules
        schedules = self.mapper.map_multiple_spaces(
            spaces, project_info, ifc_info, user_data_per_space
        )
        
        # Convert to dictionaries
        json_data = []
        for schedule in schedules:
            try:
                schedule_dict = schedule.to_dict()
                json_data.append(schedule_dict)
            except Exception as e:
                self.logger.error(f"Error converting schedule to dict: {str(e)}")
                continue
        
        return json_data
    
    def build_single_room_json(
        self, 
        space: SpaceData, 
        project_info: Optional[Dict[str, Any]] = None,
        user_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Build comprehensive JSON structure for a single space.
        
        Args:
            space: Space data
            project_info: Project-level information
            user_data: User-provided data for this space
            
        Returns:
            Room schedule dictionary
        """
        # Prepare IFC information
        ifc_info = {
            "file_name": Path(self.source_file).name if self.source_file else None,
            "ifc_version": self.ifc_version,
            "discipline": "ARK"
        }
        
        # Map space to comprehensive schedule
        schedule = self.mapper.map_space_to_comprehensive_schedule(
            space, project_info, ifc_info, user_data
        )
        
        return schedule.to_dict()
    
    def write_comprehensive_json_file(
        self, 
        file_path: str, 
        spaces: List[SpaceData],
        project_info: Optional[Dict[str, Any]] = None,
        user_data_per_space: Optional[Dict[str, Dict[str, Any]]] = None,
        indent: int = 2
    ) -> bool:
        """
        Write comprehensive JSON file.
        
        Args:
            file_path: Output file path
            spaces: List of space data
            project_info: Project-level information
            user_data_per_space: User data keyed by space GUID
            indent: JSON indentation
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Build JSON structure
            json_data = self.build_comprehensive_json_structure(
                spaces, project_info, user_data_per_space
            )
            
            # Create output directory if it doesn't exist
            output_dir = Path(file_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Write JSON file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=indent, ensure_ascii=False)
            
            self.logger.info(f"Successfully wrote comprehensive JSON file: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error writing comprehensive JSON file: {str(e)}")
            return False
    
    def write_single_room_json_file(
        self, 
        file_path: str, 
        space: SpaceData,
        project_info: Optional[Dict[str, Any]] = None,
        user_data: Optional[Dict[str, Any]] = None,
        indent: int = 2
    ) -> bool:
        """
        Write comprehensive JSON file for a single room.
        
        Args:
            file_path: Output file path
            space: Space data
            project_info: Project-level information
            user_data: User-provided data for this space
            indent: JSON indentation
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Build JSON structure
            json_data = self.build_single_room_json(space, project_info, user_data)
            
            # Create output directory if it doesn't exist
            output_dir = Path(file_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Write JSON file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=indent, ensure_ascii=False)
            
            self.logger.info(f"Successfully wrote single room JSON file: {file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error writing single room JSON file: {str(e)}")
            return False
    
    def create_user_input_templates(
        self, 
        spaces: List[SpaceData], 
        output_dir: str
    ) -> List[str]:
        """
        Create user input template files for each space.
        
        Args:
            spaces: List of space data
            output_dir: Output directory for template files
            
        Returns:
            List of created template file paths
        """
        created_files = []
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        for space in spaces:
            try:
                # Create template
                template = self.mapper.create_template_for_user_input(space)
                
                # Create filename
                safe_name = self._make_safe_filename(space.name or space.guid)
                template_file = output_path / f"{safe_name}_user_input_template.json"
                
                # Write template file
                with open(template_file, 'w', encoding='utf-8') as f:
                    json.dump(template, f, indent=2, ensure_ascii=False)
                
                created_files.append(str(template_file))
                self.logger.info(f"Created user input template: {template_file}")
                
            except Exception as e:
                self.logger.error(f"Error creating template for space {space.guid}: {str(e)}")
                continue
        
        return created_files
    
    def load_user_data_from_files(self, template_files: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Load user data from template files that have been filled out.
        
        Args:
            template_files: List of template file paths
            
        Returns:
            Dictionary of user data keyed by space GUID
        """
        user_data = {}
        
        for file_path in template_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                space_guid = data.get('space_guid')
                if space_guid:
                    # Remove metadata fields and keep only user input
                    user_input = {k: v for k, v in data.items() 
                                if k not in ['space_guid', 'space_name']}
                    user_data[space_guid] = user_input
                    
            except Exception as e:
                self.logger.error(f"Error loading user data from {file_path}: {str(e)}")
                continue
        
        return user_data
    
    def validate_comprehensive_data(self, json_data: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
        """
        Validate comprehensive JSON data structure.
        
        Args:
            json_data: List of room schedule dictionaries
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        if not json_data:
            errors.append("No room data provided")
            return False, errors
        
        required_sections = ['meta', 'identification', 'ifc', 'geometry']
        
        for i, room_data in enumerate(json_data):
            room_id = room_data.get('identification', {}).get('room_name', f'Room {i+1}')
            
            # Check required sections
            for section in required_sections:
                if section not in room_data:
                    errors.append(f"{room_id}: Missing required section '{section}'")
            
            # Validate meta section
            if 'meta' in room_data:
                meta = room_data['meta']
                if not meta.get('schema_version'):
                    errors.append(f"{room_id}: Missing schema_version in meta section")
            
            # Validate identification section
            if 'identification' in room_data:
                identification = room_data['identification']
                if not identification.get('room_name'):
                    errors.append(f"{room_id}: Missing room_name in identification section")
            
            # Validate IFC section
            if 'ifc' in room_data:
                ifc = room_data['ifc']
                if not ifc.get('space_global_id'):
                    errors.append(f"{room_id}: Missing space_global_id in IFC section")
            
            # Validate geometry section
            if 'geometry' in room_data:
                geometry = room_data['geometry']
                if not geometry.get('area_nett_m2'):
                    errors.append(f"{room_id}: Missing area_nett_m2 in geometry section")
        
        is_valid = len(errors) == 0
        return is_valid, errors
    
    def _make_safe_filename(self, name: str) -> str:
        """Make a safe filename from a room name."""
        # Replace unsafe characters
        safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
        safe_name = ''.join(c if c in safe_chars else '_' for c in name)
        
        # Limit length
        if len(safe_name) > 50:
            safe_name = safe_name[:50]
        
        return safe_name or "unnamed_room"