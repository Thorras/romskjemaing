"""
Meta Mapper

Maps IFC file metadata to room schedule meta section with NS 8360/NS 3940 compliance tracking.
"""

import os
from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass

from ifc_room_schedule.data.enhanced_room_schedule_model import MetaData


@dataclass
class IFCFileMetadata:
    """Metadata extracted from IFC file."""
    
    file_name: str
    file_size_bytes: int
    ifc_version: str
    model_source: str
    project_name: str
    project_number: str
    building_name: str
    building_number: str
    site_name: str
    site_number: str
    organization_name: str
    author: str
    creation_date: Optional[datetime]
    last_modified: Optional[datetime]
    software_version: str
    schema_version: str


class MetaMapper:
    """Maps IFC file metadata to room schedule meta section."""
    
    def __init__(self):
        """Initialize MetaMapper."""
        self.ns_standards_version = "NS 8360:2023, NS 3940:2023"
        self.tek17_version = "TEK17"
    
    def extract_meta_data(self, ifc_file_path: str, ifc_file_metadata: Optional[IFCFileMetadata] = None) -> MetaData:
        """
        Extract metadata from IFC file and create MetaData object.
        
        Args:
            ifc_file_path: Path to IFC file
            ifc_file_metadata: Optional pre-extracted IFC metadata
            
        Returns:
            MetaData object with all metadata
        """
        # Extract basic file information
        file_name = os.path.basename(ifc_file_path)
        file_size = os.path.getsize(ifc_file_path) if os.path.exists(ifc_file_path) else 0
        
        # Use provided metadata or create default
        if ifc_file_metadata:
            ifc_version = ifc_file_metadata.ifc_version
            model_source = ifc_file_metadata.model_source
            project_name = ifc_file_metadata.project_name
            project_number = ifc_file_metadata.project_number
            building_name = ifc_file_metadata.building_name
            building_number = ifc_file_metadata.building_number
            site_name = ifc_file_metadata.site_name
            site_number = ifc_file_metadata.site_number
            organization_name = ifc_file_metadata.organization_name
            author = ifc_file_metadata.author
            creation_date = ifc_file_metadata.creation_date
            last_modified = ifc_file_metadata.last_modified
            software_version = ifc_file_metadata.software_version
            schema_version = ifc_file_metadata.schema_version
        else:
            # Default values when IFC metadata is not available
            ifc_version = "IFC4"
            model_source = "Unknown"
            project_name = self._extract_project_name_from_filename(file_name)
            project_number = ""
            building_name = ""
            building_number = ""
            site_name = ""
            site_number = ""
            organization_name = ""
            author = ""
            creation_date = None
            last_modified = None
            software_version = "Unknown"
            schema_version = "IFC4"
        
        # Generate timestamps
        export_timestamp = datetime.now()
        generation_timestamp = creation_date or export_timestamp
        
        # Build NS standards compliance info
        ns_compliance = {
            "ns8360_version": "NS 8360:2023",
            "ns3940_version": "NS 3940:2023",
            "tek17_version": "TEK17",
            "compliance_status": "Partial",  # Will be updated based on actual data
            "validation_level": "Moderate"
        }
        
        # Build application info
        application_info = {
            "name": "IFC Room Schedule Generator",
            "version": "2.0.0",
            "build_date": "2025-01-29",
            "ns_standards_integration": True,
            "enhanced_export": True
        }
        
        # Build file info
        file_info = {
            "source_file": file_name,
            "file_size_mb": round(file_size / (1024 * 1024), 2),
            "ifc_version": ifc_version,
            "schema_version": schema_version,
            "model_source": model_source,
            "software_version": software_version
        }
        
        # Build project info
        project_info = {
            "project_name": project_name,
            "project_number": project_number,
            "building_name": building_name,
            "building_number": building_number,
            "site_name": site_name,
            "site_number": site_number,
            "organization": organization_name,
            "author": author
        }
        
        # Build timestamps
        timestamps = {
            "export_date": export_timestamp.isoformat(),
            "generation_date": generation_timestamp.isoformat() if generation_timestamp else None,
            "last_modified": last_modified.isoformat() if last_modified else None,
            "timezone": "Europe/Oslo"
        }
        
        return MetaData(
            ns_compliance=ns_compliance,
            application_info=application_info,
            file_info=file_info,
            project_info=project_info,
            timestamps=timestamps
        )
    
    def generate_timestamps(self) -> Dict[str, str]:
        """
        Generate standardized timestamps for export.
        
        Returns:
            Dictionary with timestamp information
        """
        now = datetime.now()
        
        return {
            "export_date": now.isoformat(),
            "generation_date": now.isoformat(),
            "timezone": "Europe/Oslo",
            "format": "ISO 8601"
        }
    
    def update_ns_compliance_status(self, meta_data: MetaData, compliance_data: Dict[str, Any]) -> MetaData:
        """
        Update NS compliance status based on actual data analysis.
        
        Args:
            meta_data: Existing MetaData object
            compliance_data: Compliance analysis results
            
        Returns:
            Updated MetaData object
        """
        # Update compliance status based on analysis
        compliance_status = "Full"
        if compliance_data.get("ns8360_compliant_spaces", 0) < compliance_data.get("total_spaces", 1) * 0.8:
            compliance_status = "Partial"
        if compliance_data.get("ns8360_compliant_spaces", 0) < compliance_data.get("total_spaces", 1) * 0.5:
            compliance_status = "Limited"
        
        # Update NS compliance info
        updated_ns_compliance = meta_data.ns_compliance.copy()
        updated_ns_compliance.update({
            "compliance_status": compliance_status,
            "ns8360_compliant_spaces": compliance_data.get("ns8360_compliant_spaces", 0),
            "total_spaces": compliance_data.get("total_spaces", 0),
            "compliance_percentage": compliance_data.get("compliance_percentage", 0.0),
            "validation_level": compliance_data.get("validation_level", "Moderate")
        })
        
        # Create updated MetaData
        return MetaData(
            ns_compliance=updated_ns_compliance,
            application_info=meta_data.application_info,
            file_info=meta_data.file_info,
            project_info=meta_data.project_info,
            timestamps=meta_data.timestamps
        )
    
    def _extract_project_name_from_filename(self, filename: str) -> str:
        """Extract project name from IFC filename."""
        # Remove .ifc extension
        name = filename.replace('.ifc', '').replace('.IFC', '')
        
        # Common patterns for Norwegian project names
        # Remove common suffixes
        suffixes_to_remove = [
            '_ARK', '_RIV', '_RIE', '_RIA', '_RIB', '_RIBr',
            '_23', '_24', '_25', '_26', '_27', '_28', '_29', '_30',
            '_FINAL', '_LATEST', '_REV01', '_REV02', '_REV03'
        ]
        
        for suffix in suffixes_to_remove:
            if name.endswith(suffix):
                name = name[:-len(suffix)]
                break
        
        return name or "Unknown Project"
    
    def validate_metadata_completeness(self, meta_data: MetaData) -> Dict[str, Any]:
        """
        Validate completeness of metadata.
        
        Args:
            meta_data: MetaData object to validate
            
        Returns:
            Validation results with completeness scores
        """
        validation_results = {
            "overall_completeness": 0.0,
            "missing_fields": [],
            "recommendations": []
        }
        
        completeness_scores = []
        
        # Check project info completeness
        project_fields = [
            ("project_name", meta_data.project_info.get("project_name")),
            ("project_number", meta_data.project_info.get("project_number")),
            ("building_name", meta_data.project_info.get("building_name")),
            ("organization", meta_data.project_info.get("organization")),
            ("author", meta_data.project_info.get("author"))
        ]
        
        project_completeness = sum(1 for _, value in project_fields if value and value.strip()) / len(project_fields)
        completeness_scores.append(project_completeness)
        
        if project_completeness < 0.8:
            validation_results["missing_fields"].extend([
                field for field, value in project_fields if not value or not value.strip()
            ])
            validation_results["recommendations"].append("Complete project information in IFC file properties")
        
        # Check file info completeness
        file_fields = [
            ("ifc_version", meta_data.file_info.get("ifc_version")),
            ("model_source", meta_data.file_info.get("model_source")),
            ("software_version", meta_data.file_info.get("software_version"))
        ]
        
        file_completeness = sum(1 for _, value in file_fields if value and value.strip()) / len(file_fields)
        completeness_scores.append(file_completeness)
        
        if file_completeness < 0.8:
            validation_results["missing_fields"].extend([
                field for field, value in file_fields if not value or not value.strip()
            ])
            validation_results["recommendations"].append("Ensure IFC file contains proper metadata")
        
        # Calculate overall completeness
        validation_results["overall_completeness"] = sum(completeness_scores) / len(completeness_scores)
        
        return validation_results


# Example usage and testing
if __name__ == "__main__":
    mapper = MetaMapper()
    
    # Test with sample data
    test_file_path = "test_project.ifc"
    
    # Create sample IFC metadata
    sample_metadata = IFCFileMetadata(
        file_name="AkkordSvingen_23_ARK.ifc",
        file_size_bytes=2400000,
        ifc_version="IFC4",
        model_source="Revit 2023",
        project_name="AkkordSvingen",
        project_number="2023-001",
        building_name="AkkordSvingen",
        building_number="001",
        site_name="Oslo",
        site_number="001",
        organization_name="Akkord AS",
        author="Architect Name",
        creation_date=datetime(2023, 1, 15),
        last_modified=datetime(2023, 6, 20),
        software_version="Revit 2023.2",
        schema_version="IFC4"
    )
    
    # Extract metadata
    meta_data = mapper.extract_meta_data(test_file_path, sample_metadata)
    
    print("Meta Mapper Test Results:")
    print("=" * 50)
    print(f"Project: {meta_data.project_info['project_name']}")
    print(f"IFC Version: {meta_data.file_info['ifc_version']}")
    print(f"NS Compliance: {meta_data.ns_compliance['compliance_status']}")
    print(f"Export Date: {meta_data.timestamps['export_date']}")
    
    # Test validation
    validation = mapper.validate_metadata_completeness(meta_data)
    print(f"\nCompleteness: {validation['overall_completeness']:.1%}")
    if validation['missing_fields']:
        print(f"Missing: {', '.join(validation['missing_fields'])}")
