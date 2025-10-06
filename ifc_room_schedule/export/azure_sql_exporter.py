"""
Azure SQL Database Exporter

Exports room schedule data to Azure SQL Database with proper schema creation
and data normalization.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

try:
    import pyodbc
    import sqlalchemy
    from sqlalchemy import create_engine, text, MetaData, Table, Column, String, Float, Integer, DateTime, Text, Boolean
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.exc import SQLAlchemyError
    SQL_AVAILABLE = True
except ImportError:
    SQL_AVAILABLE = False

from ..data.space_model import SpaceData

# Import database config with proper path handling
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
from config.database_config import DatabaseConfig


class AzureSQLExporter:
    """Exports room schedule data to Azure SQL Database."""
    
    def __init__(self, connection_string: str = None, use_default_config: bool = False):
        """
        Initialize Azure SQL exporter.
        
        Args:
            connection_string: Azure SQL connection string (optional if using default config)
            use_default_config: Use default database configuration
        """
        if not SQL_AVAILABLE:
            raise ImportError(
                "SQL dependencies not available. Install with: "
                "pip install pyodbc sqlalchemy"
            )
        
        # Initialize logger first
        self.logger = logging.getLogger(__name__)
        
        # Determine connection string to use
        if use_default_config:
            try:
                self.connection_string = DatabaseConfig.get_default_connection_string()
                self.logger.info("Using default database configuration")
            except ValueError as e:
                self.logger.error(f"Failed to get default connection string: {e}")
                raise
        elif connection_string:
            self.connection_string = connection_string
        else:
            raise ValueError(
                "Either provide connection_string or set use_default_config=True"
            )
        
        self.engine = None
        self.metadata = MetaData()
        
        # Define table schemas
        self._define_schemas()
    
    def _define_schemas(self):
        """Define database table schemas."""
        
        # Projects table
        self.projects_table = Table(
            'projects', self.metadata,
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('name', String(255), nullable=False),
            Column('source_file', String(500)),
            Column('source_file_path', String(1000)),
            Column('export_date', DateTime, default=datetime.utcnow),
            Column('application_version', String(50)),
            Column('created_at', DateTime, default=datetime.utcnow)
        )
        
        # Spaces table
        self.spaces_table = Table(
            'spaces', self.metadata,
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('project_id', Integer, nullable=False),
            Column('guid', String(50), nullable=False, unique=True),
            Column('name', String(255)),
            Column('long_name', String(500)),
            Column('description', Text),
            Column('object_type', String(100)),
            Column('zone_category', String(100)),
            Column('number', String(50)),
            Column('elevation', Float),
            Column('processed', Boolean, default=False),
            Column('user_descriptions', Text),  # JSON string
            Column('created_at', DateTime, default=datetime.utcnow)
        )
        
        # Space quantities table
        self.space_quantities_table = Table(
            'space_quantities', self.metadata,
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('space_id', Integer, nullable=False),
            Column('height', Float),
            Column('finish_ceiling_height', Float),
            Column('finish_floor_height', Float),
            Column('gross_floor_area', Float),
            Column('net_floor_area', Float),
            Column('gross_ceiling_area', Float),
            Column('net_ceiling_area', Float),
            Column('gross_wall_area', Float),
            Column('net_wall_area', Float),
            Column('gross_perimeter', Float),
            Column('net_perimeter', Float),
            Column('gross_volume', Float),
            Column('net_volume', Float)
        )
        
        # Surfaces table
        self.surfaces_table = Table(
            'surfaces', self.metadata,
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('space_id', Integer, nullable=False),
            Column('surface_id', String(50), nullable=False),
            Column('type', String(100)),
            Column('area', Float),
            Column('material', String(255)),
            Column('ifc_type', String(100)),
            Column('user_description', Text),
            Column('name', String(255)),
            Column('description', Text),
            Column('created_at', DateTime, default=datetime.utcnow)
        )
        
        # Space boundaries table
        self.space_boundaries_table = Table(
            'space_boundaries', self.metadata,
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('space_id', Integer, nullable=False),
            Column('boundary_id', String(50), nullable=False),
            Column('guid', String(50)),
            Column('name', String(255)),
            Column('description', Text),
            Column('physical_or_virtual_boundary', String(50)),
            Column('internal_or_external_boundary', String(50)),
            Column('related_building_element_guid', String(50)),
            Column('related_building_element_name', String(255)),
            Column('related_building_element_type', String(100)),
            Column('adjacent_space_guid', String(50)),
            Column('adjacent_space_name', String(255)),
            Column('boundary_surface_type', String(100)),
            Column('boundary_orientation', String(50)),
            Column('calculated_area', Float),
            Column('user_description', Text),
            Column('boundary_level', Integer),
            Column('display_label', String(255)),
            Column('connection_geometry', Text),  # JSON string
            Column('thermal_properties', Text),   # JSON string
            Column('material_properties', Text),  # JSON string
            Column('created_at', DateTime, default=datetime.utcnow)
        )
        
        # Relationships table
        self.relationships_table = Table(
            'relationships', self.metadata,
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('space_id', Integer, nullable=False),
            Column('related_entity_guid', String(50)),
            Column('related_entity_name', String(255)),
            Column('related_entity_description', Text),
            Column('relationship_type', String(100)),
            Column('ifc_relationship_type', String(100)),
            Column('created_at', DateTime, default=datetime.utcnow)
        )
    
    def connect(self) -> bool:
        """
        Establish connection to Azure SQL Database.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.engine = create_engine(self.connection_string)
            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            self.logger.info("Successfully connected to Azure SQL Database")
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect to Azure SQL Database: {e}")
            return False
    
    def create_tables(self) -> bool:
        """
        Create database tables if they don't exist.
        
        Returns:
            True if tables created successfully, False otherwise
        """
        try:
            self.metadata.create_all(self.engine)
            self.logger.info("Database tables created successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to create database tables: {e}")
            return False
    
    def export_data(self, data: Dict[str, Any], project_name: str = None) -> bool:
        """
        Export room schedule data to Azure SQL Database.
        
        Args:
            data: Room schedule data dictionary
            project_name: Optional project name override
            
        Returns:
            True if export successful, False otherwise
        """
        if not self.engine:
            if not self.connect():
                return False
        
        if not self.create_tables():
            return False
        
        try:
            with self.engine.begin() as conn:
                # Insert project
                project_id = self._insert_project(conn, data, project_name)
                
                # Insert spaces and related data
                for space_data in data.get('spaces', []):
                    space_id = self._insert_space(conn, project_id, space_data)
                    self._insert_space_quantities(conn, space_id, space_data)
                    self._insert_surfaces(conn, space_id, space_data)
                    self._insert_space_boundaries(conn, space_id, space_data)
                    self._insert_relationships(conn, space_id, space_data)
            
            self.logger.info(f"Successfully exported data to Azure SQL Database")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export data: {e}")
            return False
    
    def _insert_project(self, conn, data: Dict[str, Any], project_name: str = None) -> int:
        """Insert project record and return project ID."""
        metadata = data.get('metadata', {})
        
        project_data = {
            'name': project_name or metadata.get('source_file', 'Unknown Project'),
            'source_file': metadata.get('source_file'),
            'source_file_path': metadata.get('source_file_path'),
            'export_date': datetime.fromisoformat(metadata.get('export_date', datetime.utcnow().isoformat())),
            'application_version': metadata.get('application_version')
        }
        
        result = conn.execute(self.projects_table.insert().values(**project_data))
        return result.inserted_primary_key[0]
    
    def _insert_space(self, conn, project_id: int, space_data: Dict[str, Any]) -> int:
        """Insert space record and return space ID."""
        properties = space_data.get('properties', {})
        
        space_record = {
            'project_id': project_id,
            'guid': space_data.get('guid'),
            'name': properties.get('name'),
            'long_name': properties.get('long_name'),
            'description': properties.get('description'),
            'object_type': properties.get('object_type'),
            'zone_category': properties.get('zone_category'),
            'number': properties.get('number'),
            'elevation': properties.get('elevation'),
            'processed': properties.get('processed', False),
            'user_descriptions': json.dumps(properties.get('user_descriptions', {}))
        }
        
        result = conn.execute(self.spaces_table.insert().values(**space_record))
        return result.inserted_primary_key[0]
    
    def _insert_space_quantities(self, conn, space_id: int, space_data: Dict[str, Any]):
        """Insert space quantities record."""
        quantities = space_data.get('properties', {}).get('quantities', {})
        
        if quantities:
            quantities_record = {
                'space_id': space_id,
                'height': quantities.get('Height'),
                'finish_ceiling_height': quantities.get('FinishCeilingHeight'),
                'finish_floor_height': quantities.get('FinishFloorHeight'),
                'gross_floor_area': quantities.get('GrossFloorArea'),
                'net_floor_area': quantities.get('NetFloorArea'),
                'gross_ceiling_area': quantities.get('GrossCeilingArea'),
                'net_ceiling_area': quantities.get('NetCeilingArea'),
                'gross_wall_area': quantities.get('GrossWallArea'),
                'net_wall_area': quantities.get('NetWallArea'),
                'gross_perimeter': quantities.get('GrossPerimeter'),
                'net_perimeter': quantities.get('NetPerimeter'),
                'gross_volume': quantities.get('GrossVolume'),
                'net_volume': quantities.get('NetVolume')
            }
            
            conn.execute(self.space_quantities_table.insert().values(**quantities_record))
    
    def _insert_surfaces(self, conn, space_id: int, space_data: Dict[str, Any]):
        """Insert surface records."""
        for surface in space_data.get('surfaces', []):
            properties = surface.get('properties', {})
            
            surface_record = {
                'space_id': space_id,
                'surface_id': surface.get('id'),
                'type': surface.get('type'),
                'area': surface.get('area'),
                'material': surface.get('material'),
                'ifc_type': surface.get('ifc_type'),
                'user_description': surface.get('user_description'),
                'name': properties.get('name'),
                'description': properties.get('description')
            }
            
            conn.execute(self.surfaces_table.insert().values(**surface_record))
    
    def _insert_space_boundaries(self, conn, space_id: int, space_data: Dict[str, Any]):
        """Insert space boundary records."""
        for boundary in space_data.get('space_boundaries', []):
            boundary_record = {
                'space_id': space_id,
                'boundary_id': boundary.get('id'),
                'guid': boundary.get('guid'),
                'name': boundary.get('name'),
                'description': boundary.get('description'),
                'physical_or_virtual_boundary': boundary.get('physical_or_virtual_boundary'),
                'internal_or_external_boundary': boundary.get('internal_or_external_boundary'),
                'related_building_element_guid': boundary.get('related_building_element_guid'),
                'related_building_element_name': boundary.get('related_building_element_name'),
                'related_building_element_type': boundary.get('related_building_element_type'),
                'adjacent_space_guid': boundary.get('adjacent_space_guid'),
                'adjacent_space_name': boundary.get('adjacent_space_name'),
                'boundary_surface_type': boundary.get('boundary_surface_type'),
                'boundary_orientation': boundary.get('boundary_orientation'),
                'calculated_area': boundary.get('calculated_area'),
                'user_description': boundary.get('user_description'),
                'boundary_level': boundary.get('boundary_level'),
                'display_label': boundary.get('display_label'),
                'connection_geometry': json.dumps(boundary.get('connection_geometry', {})),
                'thermal_properties': json.dumps(boundary.get('thermal_properties', {})),
                'material_properties': json.dumps(boundary.get('material_properties', {}))
            }
            
            conn.execute(self.space_boundaries_table.insert().values(**boundary_record))
    
    def _insert_relationships(self, conn, space_id: int, space_data: Dict[str, Any]):
        """Insert relationship records."""
        for relationship in space_data.get('relationships', []):
            relationship_record = {
                'space_id': space_id,
                'related_entity_guid': relationship.get('related_entity_guid'),
                'related_entity_name': relationship.get('related_entity_name'),
                'related_entity_description': relationship.get('related_entity_description'),
                'relationship_type': relationship.get('relationship_type'),
                'ifc_relationship_type': relationship.get('ifc_relationship_type')
            }
            
            conn.execute(self.relationships_table.insert().values(**relationship_record))
    
    def get_connection_string_template(self) -> str:
        """
        Get Azure SQL connection string template.
        
        Returns:
            Connection string template with placeholders
        """
        return DatabaseConfig.CONNECTION_STRING_TEMPLATE
    
    @classmethod
    def create_with_default_config(cls):
        """
        Create exporter instance with default database configuration.
        
        Returns:
            AzureSQLExporter instance configured with default settings
        """
        return cls(use_default_config=True)
    
    @classmethod
    def create_with_local_db(cls, database_name: str = "RomskjemaDB"):
        """
        Create exporter instance for local SQL Server Express.
        
        Args:
            database_name: Name of local database
            
        Returns:
            AzureSQLExporter instance configured for local database
        """
        connection_string = DatabaseConfig.get_local_connection_string(database_name)
        return cls(connection_string)
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Test database connection and return status.
        
        Returns:
            Dictionary with connection status and details
        """
        result = {
            'connected': False,
            'error': None,
            'server_info': None
        }
        
        try:
            if not self.engine:
                if not self.connect():
                    result['error'] = "Failed to establish connection"
                    return result
            
            with self.engine.connect() as conn:
                # Test query
                test_result = conn.execute(text("SELECT @@VERSION as version"))
                version = test_result.fetchone()
                
                result['connected'] = True
                result['server_info'] = version[0] if version else "Unknown"
                
        except Exception as e:
            result['error'] = str(e)
        
        return result