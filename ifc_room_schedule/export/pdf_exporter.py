"""
PDF Exporter

Handles exporting room schedule data to PDF format using reportlab.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.platypus.tableofcontents import TableOfContents
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

from ..data.space_model import SpaceData


class PdfExporter:
    """Exports room schedule data to PDF format."""
    
    def __init__(self):
        """Initialize the PDF exporter."""
        if not REPORTLAB_AVAILABLE:
            raise ImportError("reportlab is required for PDF export. Install with: pip install reportlab")
        
        self.source_file_path: Optional[str] = None
        self.application_version: str = "1.0.0"
        
        # Get styles
        self.styles = getSampleStyleSheet()
        
        # Define custom styles
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Title'],
            fontSize=24,
            spaceAfter=30,
            textColor=colors.HexColor('#2F5597')
        )
        
        self.heading1_style = ParagraphStyle(
            'CustomHeading1',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceAfter=12,
            textColor=colors.HexColor('#2F5597'),
            borderWidth=1,
            borderColor=colors.HexColor('#2F5597'),
            borderPadding=5,
            backColor=colors.HexColor('#F0F4F8')
        )
        
        self.heading2_style = ParagraphStyle(
            'CustomHeading2',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=10,
            textColor=colors.HexColor('#366092')
        )
        
        self.normal_style = self.styles['Normal']
        self.table_header_style = ParagraphStyle(
            'TableHeader',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.white,
            alignment=1  # Center alignment
        )
    
    def set_source_file(self, file_path: str) -> None:
        """Set the source IFC file path."""
        self.source_file_path = file_path
    
    def export_to_pdf(self, spaces: List[SpaceData], filename: str,
                     include_surfaces: bool = True,
                     include_boundaries: bool = True,
                     include_relationships: bool = True,
                     page_size=A4) -> Tuple[bool, str]:
        """
        Export space data to PDF format.
        
        Args:
            spaces: List of SpaceData objects to export
            filename: Output PDF filename
            include_surfaces: Whether to include surface data
            include_boundaries: Whether to include boundary data
            include_relationships: Whether to include relationship data
            page_size: Page size (default A4)
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Validate input
            if not filename:
                return False, "Filename cannot be empty"
            
            if not spaces:
                # Create empty PDF file with headers only
                if not filename.lower().endswith('.pdf'):
                    filename += '.pdf'
                
                file_path = Path(filename)
                file_path.parent.mkdir(parents=True, exist_ok=True)
                
                doc = SimpleDocTemplate(str(file_path), pagesize=letter)
                story = []
                
                # Add title
                title = Paragraph("Room Schedule Report", self.title_style)
                story.append(title)
                story.append(Spacer(1, 20))
                
                # Add summary
                summary_text = f"Total spaces: 0"
                summary = Paragraph(summary_text, self.normal_style)
                story.append(summary)
                story.append(Spacer(1, 20))
                
                # Add note about empty data
                note_text = "No space data available for export."
                note = Paragraph(note_text, self.normal_style)
                story.append(note)
                
                doc.build(story)
                return True, "Successfully exported 0 spaces"
            
            # Ensure .pdf extension
            if not filename.lower().endswith('.pdf'):
                filename += '.pdf'
            
            file_path = Path(filename)
            
            # Check write permissions and disk space
            try:
                # Create directory if needed
                file_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Check write permissions
                if file_path.exists():
                    if not os.access(file_path, os.W_OK):
                        return False, f"No write permission for file: {filename}"
                else:
                    if not os.access(file_path.parent, os.W_OK):
                        return False, f"No write permission for directory: {file_path.parent}"
                
                # Check disk space (require at least 10MB for PDF files)
                import shutil
                free_space = shutil.disk_usage(file_path.parent).free
                if free_space < 10 * 1024 * 1024:  # 10MB minimum
                    return False, f"Insufficient disk space. Available: {free_space / (1024*1024):.1f}MB"
                    
            except OSError as e:
                return False, f"File system error: {str(e)}"
            
            # Create document with temp file for atomic operation
            temp_filename = str(file_path) + '.tmp'
            try:
                doc = SimpleDocTemplate(
                    temp_filename,
                    pagesize=page_size,
                    rightMargin=72,
                    leftMargin=72,
                    topMargin=72,
                    bottomMargin=18
                )
                
                # Build story (content) with error handling
                story = []
                
                try:
                    # Title page
                    self._add_title_page(story, spaces)
                    
                    # Table of contents
                    story.append(PageBreak())
                    self._add_table_of_contents(story)
                    
                    # Overview section
                    story.append(PageBreak())
                    self._add_overview_section(story, spaces)
                    
                    # Spaces section
                    story.append(PageBreak())
                    self._add_spaces_section(story, spaces)
                    
                    if include_surfaces:
                        story.append(PageBreak())
                        self._add_surfaces_section(story, spaces)
                    
                    if include_boundaries:
                        story.append(PageBreak())
                        self._add_boundaries_section(story, spaces)
                    
                    if include_relationships:
                        story.append(PageBreak())
                        self._add_relationships_section(story, spaces)
                    
                    # Summary section
                    story.append(PageBreak())
                    self._add_summary_section(story, spaces)
                    
                except Exception as e:
                    return False, f"Error building PDF content: {str(e)}"
                
                # Build PDF
                doc.build(story)
                
                # Atomic rename
                if os.name == 'nt':  # Windows
                    if file_path.exists():
                        os.remove(file_path)
                os.rename(temp_filename, filename)
                
                return True, f"Successfully exported {len(spaces)} spaces to {Path(filename).name}"
                
            except Exception as e:
                # Clean up temp file
                if os.path.exists(temp_filename):
                    try:
                        os.remove(temp_filename)
                    except:
                        pass
                return False, f"Error creating PDF: {str(e)}"
            
        except PermissionError as e:
            return False, f"Permission denied: {str(e)}"
        except OSError as e:
            return False, f"OS error: {str(e)}"
        except Exception as e:
            return False, f"PDF export failed: {str(e)}"
    
    def _add_title_page(self, story: List, spaces: List[SpaceData]) -> None:
        """Add title page to the PDF."""
        # Main title
        title = Paragraph("IFC Room Schedule Export", self.title_style)
        story.append(title)
        story.append(Spacer(1, 0.5*inch))
        
        # Metadata table
        metadata_data = [
            ['Export Date:', datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
            ['Application Version:', self.application_version],
            ['Total Spaces:', str(len(spaces))],
            ['Processed Spaces:', str(sum(1 for space in spaces if space.processed))]
        ]
        
        if self.source_file_path:
            metadata_data.insert(2, ['Source File:', Path(self.source_file_path).name])
        
        metadata_table = Table(metadata_data, colWidths=[2*inch, 3*inch])
        metadata_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ]))
        
        story.append(metadata_table)
        story.append(Spacer(1, 1*inch))
        
        # Quick statistics
        total_surfaces = sum(len(space.surfaces) for space in spaces)
        total_boundaries = sum(len(space.space_boundaries) for space in spaces)
        total_relationships = sum(len(space.relationships) for space in spaces)
        total_surface_area = sum(space.get_total_surface_area() for space in spaces)
        total_boundary_area = sum(space.get_total_boundary_area() for space in spaces)
        
        stats_data = [
            ['Total Surfaces:', str(total_surfaces)],
            ['Total Boundaries:', str(total_boundaries)],
            ['Total Relationships:', str(total_relationships)],
            ['Total Surface Area (m²):', f"{total_surface_area:.2f}"],
            ['Total Boundary Area (m²):', f"{total_boundary_area:.2f}"]
        ]
        
        stats_table = Table(stats_data, colWidths=[2.5*inch, 2.5*inch])
        stats_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ]))
        
        story.append(stats_table)
    
    def _add_table_of_contents(self, story: List) -> None:
        """Add table of contents."""
        toc_title = Paragraph("Table of Contents", self.heading1_style)
        story.append(toc_title)
        story.append(Spacer(1, 0.2*inch))
        
        # Simple TOC entries
        toc_entries = [
            "1. Overview",
            "2. Spaces Data",
            "3. Surfaces Data",
            "4. Space Boundaries Data", 
            "5. Relationships Data",
            "6. Summary Statistics"
        ]
        
        for entry in toc_entries:
            toc_para = Paragraph(entry, self.normal_style)
            story.append(toc_para)
            story.append(Spacer(1, 0.1*inch))
    
    def _add_overview_section(self, story: List, spaces: List[SpaceData]) -> None:
        """Add overview section."""
        title = Paragraph("1. Overview", self.heading1_style)
        story.append(title)
        
        overview_text = f"""
        This document contains the room schedule data exported from an IFC file. 
        The export includes {len(spaces)} spaces with their associated surfaces, 
        space boundaries, and relationships.
        """
        
        overview_para = Paragraph(overview_text, self.normal_style)
        story.append(overview_para)
        story.append(Spacer(1, 0.2*inch))
    
    def _add_spaces_section(self, story: List, spaces: List[SpaceData]) -> None:
        """Add spaces data section."""
        title = Paragraph("2. Spaces Data", self.heading1_style)
        story.append(title)
        
        # Create table data
        headers = ['GUID', 'Name', 'Long Name', 'Object Type', 'Processed', 'Surface Area (m²)']
        data = [headers]
        
        for space in spaces:
            row = [
                space.guid[:20] + '...' if len(space.guid) > 20 else space.guid,
                space.name or '',
                space.long_name or '',
                space.object_type or '',
                'Yes' if space.processed else 'No',
                f"{space.get_total_surface_area():.2f}"
            ]
            data.append(row)
        
        # Create table
        table = Table(data, repeatRows=1)
        table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#366092')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            
            # Data rows
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            
            # Alternating row colors
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')])
        ]))
        
        story.append(table)
    
    def _add_surfaces_section(self, story: List, spaces: List[SpaceData]) -> None:
        """Add surfaces data section."""
        title = Paragraph("3. Surfaces Data", self.heading1_style)
        story.append(title)
        
        # Create table data
        headers = ['Space Name', 'Surface Type', 'Area (m²)', 'Material', 'IFC Type']
        data = [headers]
        
        for space in spaces:
            for surface in space.surfaces:
                row = [
                    space.name or '',
                    surface.type or '',
                    f"{surface.area:.2f}" if surface.area else '0.00',
                    surface.material or '',
                    surface.ifc_type or ''
                ]
                data.append(row)
        
        if len(data) > 1:  # Only add table if there's data
            table = Table(data, repeatRows=1)
            table.setStyle(self._get_standard_table_style())
            story.append(table)
        else:
            no_data_para = Paragraph("No surface data available.", self.normal_style)
            story.append(no_data_para)
    
    def _add_boundaries_section(self, story: List, spaces: List[SpaceData]) -> None:
        """Add space boundaries data section."""
        title = Paragraph("4. Space Boundaries Data", self.heading1_style)
        story.append(title)
        
        # Create table data
        headers = ['Space Name', 'Boundary Type', 'Surface Type', 'Orientation', 'Area (m²)', 'Display Label']
        data = [headers]
        
        for space in spaces:
            for boundary in space.space_boundaries:
                row = [
                    space.name or '',
                    boundary.physical_or_virtual_boundary or '',
                    boundary.boundary_surface_type or '',
                    boundary.boundary_orientation or '',
                    f"{boundary.calculated_area:.2f}" if boundary.calculated_area else '0.00',
                    boundary.display_label or ''
                ]
                data.append(row)
        
        if len(data) > 1:  # Only add table if there's data
            table = Table(data, repeatRows=1)
            table.setStyle(self._get_standard_table_style())
            story.append(table)
        else:
            no_data_para = Paragraph("No space boundary data available.", self.normal_style)
            story.append(no_data_para)
    
    def _add_relationships_section(self, story: List, spaces: List[SpaceData]) -> None:
        """Add relationships data section."""
        title = Paragraph("5. Relationships Data", self.heading1_style)
        story.append(title)
        
        # Create table data
        headers = ['Space Name', 'Related Entity Name', 'Relationship Type', 'IFC Relationship Type']
        data = [headers]
        
        for space in spaces:
            for relationship in space.relationships:
                row = [
                    space.name or '',
                    relationship.related_entity_name or '',
                    relationship.relationship_type or '',
                    relationship.ifc_relationship_type or ''
                ]
                data.append(row)
        
        if len(data) > 1:  # Only add table if there's data
            table = Table(data, repeatRows=1)
            table.setStyle(self._get_standard_table_style())
            story.append(table)
        else:
            no_data_para = Paragraph("No relationship data available.", self.normal_style)
            story.append(no_data_para)
    
    def _add_summary_section(self, story: List, spaces: List[SpaceData]) -> None:
        """Add summary statistics section."""
        title = Paragraph("6. Summary Statistics", self.heading1_style)
        story.append(title)
        
        # Calculate summary statistics
        total_spaces = len(spaces)
        processed_spaces = sum(1 for space in spaces if space.processed)
        total_surfaces = sum(len(space.surfaces) for space in spaces)
        total_boundaries = sum(len(space.space_boundaries) for space in spaces)
        total_relationships = sum(len(space.relationships) for space in spaces)
        total_surface_area = sum(space.get_total_surface_area() for space in spaces)
        total_boundary_area = sum(space.get_total_boundary_area() for space in spaces)
        
        # Basic statistics table
        basic_stats_data = [
            ['Metric', 'Value'],
            ['Total Spaces', str(total_spaces)],
            ['Processed Spaces', str(processed_spaces)],
            ['Total Surfaces', str(total_surfaces)],
            ['Total Boundaries', str(total_boundaries)],
            ['Total Relationships', str(total_relationships)],
            ['Total Surface Area (m²)', f"{total_surface_area:.2f}"],
            ['Total Boundary Area (m²)', f"{total_boundary_area:.2f}"]
        ]
        
        basic_stats_table = Table(basic_stats_data, colWidths=[3*inch, 2*inch])
        basic_stats_table.setStyle(self._get_standard_table_style())
        story.append(basic_stats_table)
        
        story.append(Spacer(1, 0.3*inch))
        
        # Surface areas by type
        subtitle = Paragraph("Surface Areas by Type", self.heading2_style)
        story.append(subtitle)
        
        surface_area_by_type = {}
        for space in spaces:
            space_areas = space.get_surface_area_by_type()
            for surface_type, area in space_areas.items():
                if surface_type not in surface_area_by_type:
                    surface_area_by_type[surface_type] = 0.0
                surface_area_by_type[surface_type] += area
        
        if surface_area_by_type:
            surface_data = [['Surface Type', 'Area (m²)']]
            for surface_type, area in surface_area_by_type.items():
                surface_data.append([surface_type, f"{area:.2f}"])
            
            surface_table = Table(surface_data, colWidths=[3*inch, 2*inch])
            surface_table.setStyle(self._get_standard_table_style())
            story.append(surface_table)
        else:
            no_surface_para = Paragraph("No surface area data available.", self.normal_style)
            story.append(no_surface_para)
    
    def _get_standard_table_style(self) -> TableStyle:
        """Get standard table style."""
        return TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#366092')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            
            # Data rows
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            
            # Alternating row colors
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')])
        ])