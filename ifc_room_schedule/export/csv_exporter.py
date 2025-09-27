"""
CSV Exporter

Handles exporting room schedule data to CSV format.
"""

import csv
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from ..data.space_model import SpaceData


class CsvExporter:
    """Exports room schedule data to CSV format."""
    
    def __init__(self):
        """Initialize the CSV exporter."""
        self.source_file_path: Optional[str] = None
        self.application_version: str = "1.0.0"
    
    def set_source_file(self, file_path: str) -> None:
        """Set the source IFC file path."""
        self.source_file_path = file_path
    
    def export_to_csv(self, spaces: List[SpaceData], filename: str, 
                     include_surfaces: bool = True, 
                     include_boundaries: bool = True,
                     include_relationships: bool = True) -> Tuple[bool, str]:
        """
        Export space data to CSV format.
        
        Args:
            spaces: List of SpaceData objects to export
            filename: Output CSV filename
            include_surfaces: Whether to include surface data
            include_boundaries: Whether to include boundary data
            include_relationships: Whether to include relationship data
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Ensure .csv extension
            if not filename.lower().endswith('.csv'):
                filename += '.csv'
            
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write metadata header
                self._write_metadata_header(writer, spaces)
                
                # Write spaces data
                self._write_spaces_data(writer, spaces)
                
                if include_surfaces:
                    self._write_surfaces_data(writer, spaces)
                
                if include_boundaries:
                    self._write_boundaries_data(writer, spaces)
                
                if include_relationships:
                    self._write_relationships_data(writer, spaces)
                
                # Write summary
                self._write_summary_data(writer, spaces)
            
            return True, f"Successfully exported {len(spaces)} spaces to {Path(filename).name}"
            
        except Exception as e:
            return False, f"CSV export failed: {str(e)}"
    
    def _write_metadata_header(self, writer: csv.writer, spaces: List[SpaceData]) -> None:
        """Write metadata header to CSV."""
        writer.writerow(['# Room Schedule Export - CSV Format'])
        writer.writerow(['# Export Date:', datetime.now().isoformat()])
        writer.writerow(['# Application Version:', self.application_version])
        if self.source_file_path:
            writer.writerow(['# Source File:', Path(self.source_file_path).name])
        writer.writerow(['# Total Spaces:', len(spaces)])
        writer.writerow([])  # Empty row for separation
    
    def _write_spaces_data(self, writer: csv.writer, spaces: List[SpaceData]) -> None:
        """Write spaces data section."""
        writer.writerow(['=== SPACES DATA ==='])
        
        # Header row
        headers = [
            'GUID', 'Name', 'Long Name', 'Description', 'Object Type',
            'Zone Category', 'Number', 'Elevation', 'Processed',
            'Height', 'Finish Floor Height', 'Finish Ceiling Height',
            'Total Surface Area', 'Total Boundary Area', 'User Description'
        ]
        writer.writerow(headers)
        
        # Data rows
        for space in spaces:
            quantities = space.quantities or {}
            user_desc = space.user_descriptions.get('space', '') if space.user_descriptions else ''
            
            row = [
                space.guid,
                space.name or '',
                space.long_name or '',
                space.description or '',
                space.object_type or '',
                space.zone_category or '',
                space.number or '',
                space.elevation or 0.0,
                'Yes' if space.processed else 'No',
                quantities.get('Height', ''),
                quantities.get('FinishFloorHeight', ''),
                quantities.get('FinishCeilingHeight', ''),
                round(space.get_total_surface_area(), 2),
                round(space.get_total_boundary_area(), 2),
                user_desc
            ]
            writer.writerow(row)
        
        writer.writerow([])  # Empty row for separation
    
    def _write_surfaces_data(self, writer: csv.writer, spaces: List[SpaceData]) -> None:
        """Write surfaces data section."""
        writer.writerow(['=== SURFACES DATA ==='])
        
        # Header row
        headers = [
            'Space GUID', 'Space Name', 'Surface ID', 'Surface Type',
            'Area (m²)', 'Material', 'IFC Type', 'User Description'
        ]
        writer.writerow(headers)
        
        # Data rows
        for space in spaces:
            for surface in space.surfaces:
                row = [
                    space.guid,
                    space.name or '',
                    surface.id,
                    surface.type or '',
                    round(surface.area, 2) if surface.area else 0.0,
                    surface.material or '',
                    surface.ifc_type or '',
                    surface.user_description or ''
                ]
                writer.writerow(row)
        
        writer.writerow([])  # Empty row for separation
    
    def _write_boundaries_data(self, writer: csv.writer, spaces: List[SpaceData]) -> None:
        """Write space boundaries data section."""
        writer.writerow(['=== SPACE BOUNDARIES DATA ==='])
        
        # Header row
        headers = [
            'Space GUID', 'Space Name', 'Boundary GUID', 'Boundary Name',
            'Physical/Virtual', 'Internal/External', 'Surface Type', 'Orientation',
            'Area (m²)', 'Related Element GUID', 'Related Element Name', 'Related Element Type',
            'Adjacent Space GUID', 'Adjacent Space Name', 'Boundary Level', 'Display Label',
            'User Description'
        ]
        writer.writerow(headers)
        
        # Data rows
        for space in spaces:
            for boundary in space.space_boundaries:
                row = [
                    space.guid,
                    space.name or '',
                    boundary.guid,
                    boundary.name or '',
                    boundary.physical_or_virtual_boundary or '',
                    boundary.internal_or_external_boundary or '',
                    boundary.boundary_surface_type or '',
                    boundary.boundary_orientation or '',
                    round(boundary.calculated_area, 2) if boundary.calculated_area else 0.0,
                    boundary.related_building_element_guid or '',
                    boundary.related_building_element_name or '',
                    boundary.related_building_element_type or '',
                    boundary.adjacent_space_guid or '',
                    boundary.adjacent_space_name or '',
                    boundary.boundary_level or 1,
                    boundary.display_label or '',
                    boundary.user_description or ''
                ]
                writer.writerow(row)
        
        writer.writerow([])  # Empty row for separation
    
    def _write_relationships_data(self, writer: csv.writer, spaces: List[SpaceData]) -> None:
        """Write relationships data section."""
        writer.writerow(['=== RELATIONSHIPS DATA ==='])
        
        # Header row
        headers = [
            'Space GUID', 'Space Name', 'Related Entity GUID', 'Related Entity Name',
            'Related Entity Description', 'Relationship Type', 'IFC Relationship Type'
        ]
        writer.writerow(headers)
        
        # Data rows
        for space in spaces:
            for relationship in space.relationships:
                row = [
                    space.guid,
                    space.name or '',
                    relationship.related_entity_guid,
                    relationship.related_entity_name or '',
                    relationship.related_entity_description or '',
                    relationship.relationship_type or '',
                    relationship.ifc_relationship_type or ''
                ]
                writer.writerow(row)
        
        writer.writerow([])  # Empty row for separation
    
    def _write_summary_data(self, writer: csv.writer, spaces: List[SpaceData]) -> None:
        """Write summary statistics section."""
        writer.writerow(['=== SUMMARY STATISTICS ==='])
        
        # Calculate summary statistics
        total_spaces = len(spaces)
        processed_spaces = sum(1 for space in spaces if space.processed)
        total_surfaces = sum(len(space.surfaces) for space in spaces)
        total_boundaries = sum(len(space.space_boundaries) for space in spaces)
        total_relationships = sum(len(space.relationships) for space in spaces)
        total_surface_area = sum(space.get_total_surface_area() for space in spaces)
        total_boundary_area = sum(space.get_total_boundary_area() for space in spaces)
        
        # Surface areas by type
        surface_area_by_type = {}
        for space in spaces:
            space_areas = space.get_surface_area_by_type()
            for surface_type, area in space_areas.items():
                if surface_type not in surface_area_by_type:
                    surface_area_by_type[surface_type] = 0.0
                surface_area_by_type[surface_type] += area
        
        # Boundary areas by type
        boundary_area_by_type = {}
        for space in spaces:
            space_boundary_areas = space.get_boundary_area_by_type()
            for boundary_type, area in space_boundary_areas.items():
                if boundary_type not in boundary_area_by_type:
                    boundary_area_by_type[boundary_type] = 0.0
                boundary_area_by_type[boundary_type] += area
        
        # Write summary data
        writer.writerow(['Metric', 'Value'])
        writer.writerow(['Total Spaces', total_spaces])
        writer.writerow(['Processed Spaces', processed_spaces])
        writer.writerow(['Total Surfaces', total_surfaces])
        writer.writerow(['Total Boundaries', total_boundaries])
        writer.writerow(['Total Relationships', total_relationships])
        writer.writerow(['Total Surface Area (m²)', round(total_surface_area, 2)])
        writer.writerow(['Total Boundary Area (m²)', round(total_boundary_area, 2)])
        
        writer.writerow([])
        writer.writerow(['Surface Areas by Type (m²)'])
        for surface_type, area in surface_area_by_type.items():
            writer.writerow([surface_type, round(area, 2)])
        
        writer.writerow([])
        writer.writerow(['Boundary Areas by Type (m²)'])
        for boundary_type, area in boundary_area_by_type.items():
            writer.writerow([boundary_type, round(area, 2)])