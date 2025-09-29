"""
IFC Metadata Mapper

Maps IFC file metadata and hierarchy to room schedule IFC section with comprehensive GUID tracking.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime

from ..data.space_model import SpaceData


@dataclass
class IFCFileInfo:
    """IFC file information."""
    
    file_name: str
    file_size_bytes: int
    ifc_version: str
    schema_version: str
    model_source: str
    software_version: str
    creation_date: Optional[datetime] = None
    last_modified: Optional[datetime] = None


@dataclass
class IFCProjectInfo:
    """IFC project information."""
    
    project_guid: Optional[str] = None
    project_name: Optional[str] = None
    project_number: Optional[str] = None
    project_description: Optional[str] = None
    organization_name: Optional[str] = None
    organization_description: Optional[str] = None
    author: Optional[str] = None
    author_email: Optional[str] = None
    creation_date: Optional[datetime] = None
    last_modified: Optional[datetime] = None


@dataclass
class IFCSiteInfo:
    """IFC site information."""
    
    site_guid: Optional[str] = None
    site_name: Optional[str] = None
    site_description: Optional[str] = None
    site_address: Optional[str] = None
    site_elevation: Optional[float] = None
    site_latitude: Optional[float] = None
    site_longitude: Optional[float] = None


@dataclass
class IFCBuildingInfo:
    """IFC building information."""
    
    building_guid: Optional[str] = None
    building_name: Optional[str] = None
    building_description: Optional[str] = None
    building_number: Optional[str] = None
    building_elevation: Optional[float] = None
    building_height: Optional[float] = None
    building_volume: Optional[float] = None


@dataclass
class IFCStoreyInfo:
    """IFC storey information."""
    
    storey_guid: Optional[str] = None
    storey_name: Optional[str] = None
    storey_description: Optional[str] = None
    storey_number: Optional[str] = None
    storey_elevation: Optional[float] = None
    storey_height: Optional[float] = None


@dataclass
class IFCSpaceInfo:
    """IFC space information."""
    
    space_guid: str
    space_name: str
    space_description: Optional[str] = None
    space_number: Optional[str] = None
    space_elevation: Optional[float] = None
    space_height: Optional[float] = None
    space_area: Optional[float] = None
    space_volume: Optional[float] = None
    space_type: Optional[str] = None
    space_usage: Optional[str] = None


@dataclass
class IFCReferenceData:
    """Complete IFC reference data for room schedule."""
    
    file_info: IFCFileInfo
    project_info: IFCProjectInfo
    site_info: IFCSiteInfo
    building_info: IFCBuildingInfo
    storey_info: IFCStoreyInfo
    space_info: IFCSpaceInfo
    hierarchy_guids: Dict[str, str]
    model_source: Dict[str, str]
    validation_status: Dict[str, Any]


class IFCMetadataMapper:
    """Maps IFC metadata and hierarchy to room schedule IFC section."""
    
    def __init__(self):
        """Initialize IFCMetadataMapper."""
        self.default_ifc_version = "IFC4"
        self.default_schema_version = "IFC4"
    
    def extract_complete_hierarchy(self, space: SpaceData, ifc_file_info: Optional[IFCFileInfo] = None) -> IFCReferenceData:
        """
        Extract complete IFC hierarchy for a space.
        
        Args:
            space: SpaceData to extract hierarchy for
            ifc_file_info: Optional IFC file information
            
        Returns:
            IFCReferenceData with complete hierarchy
        """
        # Use provided file info or create default
        file_info = ifc_file_info or self._create_default_file_info()
        
        # Extract project information
        project_info = self._extract_project_info(space)
        
        # Extract site information
        site_info = self._extract_site_info(space)
        
        # Extract building information
        building_info = self._extract_building_info(space)
        
        # Extract storey information
        storey_info = self._extract_storey_info(space)
        
        # Extract space information
        space_info = self._extract_space_info(space)
        
        # Build hierarchy GUIDs
        hierarchy_guids = self._build_hierarchy_guids(space, project_info, site_info, building_info, storey_info)
        
        # Build model source information
        model_source = self._build_model_source_info(file_info, project_info)
        
        # Validate GUID consistency
        validation_status = self._validate_guid_consistency(hierarchy_guids, space)
        
        return IFCReferenceData(
            file_info=file_info,
            project_info=project_info,
            site_info=site_info,
            building_info=building_info,
            storey_info=storey_info,
            space_info=space_info,
            hierarchy_guids=hierarchy_guids,
            model_source=model_source,
            validation_status=validation_status
        )
    
    def map_model_source_info(self, ifc_file_info: IFCFileInfo, project_info: IFCProjectInfo) -> Dict[str, str]:
        """
        Map model source information.
        
        Args:
            ifc_file_info: IFC file information
            project_info: IFC project information
            
        Returns:
            Dictionary with model source information
        """
        return {
            "file_name": ifc_file_info.file_name,
            "file_size_mb": f"{ifc_file_info.file_size_bytes / (1024 * 1024):.2f}",
            "ifc_version": ifc_file_info.ifc_version,
            "schema_version": ifc_file_info.schema_version,
            "model_source": ifc_file_info.model_source,
            "software_version": ifc_file_info.software_version,
            "project_name": project_info.project_name or "Unknown Project",
            "project_number": project_info.project_number or "",
            "organization": project_info.organization_name or "Unknown Organization",
            "author": project_info.author or "Unknown Author",
            "creation_date": project_info.creation_date.isoformat() if project_info.creation_date else "",
            "last_modified": project_info.last_modified.isoformat() if project_info.last_modified else ""
        }
    
    def validate_guid_consistency(self, hierarchy_guids: Dict[str, str], space: SpaceData) -> Dict[str, Any]:
        """
        Validate GUID consistency across IFC hierarchy.
        
        Args:
            hierarchy_guids: Dictionary of hierarchy GUIDs
            space: SpaceData to validate
            
        Returns:
            Validation results
        """
        validation_results = {
            "is_consistent": True,
            "missing_guids": [],
            "invalid_guids": [],
            "warnings": [],
            "recommendations": []
        }
        
        # Check for missing GUIDs
        required_guids = ["space_guid", "storey_guid", "building_guid", "site_guid", "project_guid"]
        for guid_type in required_guids:
            if not hierarchy_guids.get(guid_type):
                validation_results["missing_guids"].append(guid_type)
                validation_results["is_consistent"] = False
        
        # Validate GUID format (basic check)
        for guid_type, guid_value in hierarchy_guids.items():
            if guid_value and not self._is_valid_guid_format(guid_value):
                validation_results["invalid_guids"].append(guid_type)
                validation_results["is_consistent"] = False
        
        # Check space GUID matches
        if space.guid != hierarchy_guids.get("space_guid"):
            validation_results["warnings"].append("Space GUID mismatch")
        
        # Generate recommendations
        if validation_results["missing_guids"]:
            validation_results["recommendations"].append(
                f"Complete IFC hierarchy: missing {', '.join(validation_results['missing_guids'])}"
            )
        
        if validation_results["invalid_guids"]:
            validation_results["recommendations"].append(
                f"Fix invalid GUIDs: {', '.join(validation_results['invalid_guids'])}"
            )
        
        return validation_results
    
    def _create_default_file_info(self) -> IFCFileInfo:
        """Create default IFC file information."""
        return IFCFileInfo(
            file_name="Unknown.ifc",
            file_size_bytes=0,
            ifc_version=self.default_ifc_version,
            schema_version=self.default_schema_version,
            model_source="Unknown",
            software_version="Unknown"
        )
    
    def _extract_project_info(self, space: SpaceData) -> IFCProjectInfo:
        """Extract project information from space data."""
        # In a real implementation, this would parse IFC project hierarchy
        # For now, return default values
        return IFCProjectInfo(
            project_guid="PROJECT-GUID-001",
            project_name="IFC Building Project",
            project_number="2025-001",
            project_description="Building project from IFC file",
            organization_name="Unknown Organization",
            author="Unknown Author",
            creation_date=datetime.now()
        )
    
    def _extract_site_info(self, space: SpaceData) -> IFCSiteInfo:
        """Extract site information from space data."""
        return IFCSiteInfo(
            site_guid="SITE-GUID-001",
            site_name="Building Site",
            site_description="Main building site",
            site_elevation=0.0
        )
    
    def _extract_building_info(self, space: SpaceData) -> IFCBuildingInfo:
        """Extract building information from space data."""
        return IFCBuildingInfo(
            building_guid="BUILDING-GUID-001",
            building_name="Main Building",
            building_description="Primary building structure",
            building_number="001",
            building_elevation=0.0,
            building_height=space.elevation + 3.0 if space.elevation else 10.0
        )
    
    def _extract_storey_info(self, space: SpaceData) -> IFCStoreyInfo:
        """Extract storey information from space data."""
        storey_num = int(space.elevation / 3.0) + 1 if space.elevation else 1
        
        return IFCStoreyInfo(
            storey_guid=f"STOREY-GUID-{storey_num:03d}",
            storey_name=f"Etasje {storey_num}",
            storey_description=f"Floor level {storey_num}",
            storey_number=f"{storey_num:02d}",
            storey_elevation=space.elevation or 0.0,
            storey_height=3.0
        )
    
    def _extract_space_info(self, space: SpaceData) -> IFCSpaceInfo:
        """Extract space information from space data."""
        return IFCSpaceInfo(
            space_guid=space.guid,
            space_name=space.name,
            space_description=space.description,
            space_number=space.number,
            space_elevation=space.elevation,
            space_height=3.0,  # Default ceiling height
            space_area=space.quantities.get("NetFloorArea") if space.quantities else None,
            space_volume=space.quantities.get("GrossFloorArea", 0) * 3.0 if space.quantities else None,
            space_type=space.object_type,
            space_usage=space.zone_category
        )
    
    def _build_hierarchy_guids(self, space: SpaceData, project_info: IFCProjectInfo, 
                              site_info: IFCSiteInfo, building_info: IFCBuildingInfo, 
                              storey_info: IFCStoreyInfo) -> Dict[str, str]:
        """Build complete hierarchy GUIDs dictionary."""
        return {
            "project_guid": project_info.project_guid,
            "site_guid": site_info.site_guid,
            "building_guid": building_info.building_guid,
            "storey_guid": storey_info.storey_guid,
            "space_guid": space.guid,
            "space_parent_guid": storey_info.storey_guid,
            "building_parent_guid": site_info.site_guid,
            "site_parent_guid": project_info.project_guid
        }
    
    def _build_model_source_info(self, file_info: IFCFileInfo, project_info: IFCProjectInfo) -> Dict[str, str]:
        """Build model source information dictionary."""
        return {
            "file_name": file_info.file_name,
            "file_size_mb": f"{file_info.file_size_bytes / (1024 * 1024):.2f}",
            "ifc_version": file_info.ifc_version,
            "schema_version": file_info.schema_version,
            "model_source": file_info.model_source,
            "software_version": file_info.software_version,
            "project_name": project_info.project_name or "Unknown Project",
            "project_number": project_info.project_number or "",
            "organization": project_info.organization_name or "Unknown Organization",
            "author": project_info.author or "Unknown Author",
            "creation_date": project_info.creation_date.isoformat() if project_info.creation_date else "",
            "last_modified": project_info.last_modified.isoformat() if project_info.last_modified else ""
        }
    
    def _is_valid_guid_format(self, guid: str) -> bool:
        """Check if GUID has valid format."""
        if not guid:
            return False
        
        # Basic GUID format check (simplified)
        # Real IFC GUIDs are more complex, but this is a basic validation
        return len(guid) > 10 and "-" in guid
    
    def _validate_guid_consistency(self, hierarchy_guids: Dict[str, str], space: SpaceData) -> Dict[str, Any]:
        """Validate GUID consistency (internal method)."""
        return self.validate_guid_consistency(hierarchy_guids, space)


# Example usage and testing
if __name__ == "__main__":
    from ..data.space_model import SpaceData
    
    # Create test space data
    test_space = SpaceData(
        guid="GUID-STUE-001",
        name="SPC-02-A101-111-003",
        long_name="Stue | 02/A101 | NS3940:111",
        description="Oppholdsrom i A101",
        object_type="IfcSpace",
        zone_category="Residential",
        number="003",
        elevation=6.0,
        quantities={"NetFloorArea": 24.0, "GrossFloorArea": 25.5}
    )
    
    # Create test IFC file info
    test_file_info = IFCFileInfo(
        file_name="AkkordSvingen_23_ARK.ifc",
        file_size_bytes=2400000,
        ifc_version="IFC4",
        schema_version="IFC4",
        model_source="Revit 2023",
        software_version="Revit 2023.2",
        creation_date=datetime(2023, 1, 15),
        last_modified=datetime(2023, 6, 20)
    )
    
    mapper = IFCMetadataMapper()
    
    # Extract complete hierarchy
    ifc_data = mapper.extract_complete_hierarchy(test_space, test_file_info)
    
    print("IFC Metadata Mapper Test Results:")
    print("=" * 50)
    print(f"Project: {ifc_data.project_info.project_name}")
    print(f"Building: {ifc_data.building_info.building_name}")
    print(f"Storey: {ifc_data.storey_info.storey_name}")
    print(f"Space: {ifc_data.space_info.space_name}")
    print(f"Space GUID: {ifc_data.space_info.space_guid}")
    print(f"IFC Version: {ifc_data.file_info.ifc_version}")
    print(f"Model Source: {ifc_data.file_info.model_source}")
    
    # Test validation
    validation = ifc_data.validation_status
    print(f"\nValidation Status:")
    print(f"Consistent: {validation['is_consistent']}")
    if validation['missing_guids']:
        print(f"Missing GUIDs: {', '.join(validation['missing_guids'])}")
    if validation['warnings']:
        print(f"Warnings: {', '.join(validation['warnings'])}")
    if validation['recommendations']:
        print(f"Recommendations: {', '.join(validation['recommendations'])}")
