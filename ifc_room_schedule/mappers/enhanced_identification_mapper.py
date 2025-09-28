"""
Enhanced Identification Mapper

Maps IFC Space data to identification section using NS 8360/NS 3940 Norwegian standards.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from ..data.space_model import SpaceData
from ..parsers.ns8360_name_parser import NS8360NameParser
from .ns3940_classifier import NS3940Classifier


@dataclass
class IdentificationData:
    """Identification section data for room schedule."""
    
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


@dataclass
class MetaData:
    """Meta section data for room schedule."""
    
    schema_version: str = "1.1.0"
    locale: str = "nb-NO"
    created_at: Optional[str] = None
    revised_at: Optional[str] = None
    created_by: Optional[str] = None
    revised_by: Optional[str] = None
    revision: int = 0
    status: Dict[str, str] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.status is None:
            self.status = {
                "phase": "Detaljprosjektering",
                "state": "Utkast"
            }


@dataclass
class IFCMetadata:
    """Enhanced IFC metadata with NS 8360 compliance."""
    
    space_global_id: Optional[str] = None
    space_long_name: Optional[str] = None
    space_number: Optional[str] = None
    site_guid: Optional[str] = None
    building_guid: Optional[str] = None
    storey_guid: Optional[str] = None
    ns8360_compliant: bool = False
    parsed_name_components: Optional[Dict[str, str]] = None
    model_source: Optional[Dict[str, str]] = None


@dataclass
class ClassificationData:
    """Enhanced classification with NS 3940 structured data."""
    
    ns3940: Optional[Dict[str, Any]] = None
    ns8360_compliance: Optional[Dict[str, Any]] = None
    tfm: Optional[str] = None
    custom_codes: list = None
    
    def __post_init__(self):
        if self.custom_codes is None:
            self.custom_codes = []


class EnhancedIdentificationMapper:
    """Enhanced identification mapper using NS 8360 and NS 3940 standards."""
    
    def __init__(self):
        self.name_parser = NS8360NameParser()
        self.classifier = NS3940Classifier()
    
    def map_identification(self, space: SpaceData, ifc_file_name: str = None) -> IdentificationData:
        """
        Map space to identification section using Norwegian standards.
        
        Args:
            space: SpaceData to map
            ifc_file_name: Name of source IFC file
            
        Returns:
            IdentificationData with mapped values
        """
        # Parse NS 8360 compliant name
        parsed_name = self.name_parser.parse(space.name)
        
        # Get NS 3940 classification
        classification = None
        if parsed_name.is_valid and parsed_name.function_code:
            classification = self.classifier.classify_from_code(parsed_name.function_code)
        else:
            # Fallback: infer from name
            classification = self.classifier.classify_from_name(space.name)
        
        # Extract project hierarchy
        project_id = self._extract_project_id(space, ifc_file_name)
        building_name = self._extract_building_name(space)
        
        return IdentificationData(
            project_id=project_id,
            project_name=self._extract_project_name(space, ifc_file_name),
            building_id=self._extract_building_id(space),
            building_name=building_name,
            storey_name=parsed_name.storey if parsed_name.is_valid else self._fallback_storey(space),
            storey_elevation_m=space.elevation,
            room_number=parsed_name.sequence if parsed_name.is_valid else self._fallback_room_number(space),
            room_name=self._generate_readable_name(space, classification, parsed_name),
            function=classification.label if classification else None,
            occupancy_type=classification.occupancy_type if classification else None
        )
    
    def map_meta(self, space: SpaceData, created_by: str = None) -> MetaData:
        """
        Map meta section with Norwegian standards.
        
        Args:
            space: SpaceData to map
            created_by: Creator name
            
        Returns:
            MetaData with mapped values
        """
        return MetaData(
            created_by=created_by or "IFC Room Schedule Generator",
            status={
                "phase": "Detaljprosjektering",
                "state": "Utkast"
            }
        )
    
    def map_ifc_metadata(self, space: SpaceData, ifc_file_name: str = None) -> IFCMetadata:
        """
        Map IFC metadata with NS 8360 compliance tracking.
        
        Args:
            space: SpaceData to map
            ifc_file_name: Name of source IFC file
            
        Returns:
            IFCMetadata with enhanced data
        """
        parsed_name = self.name_parser.parse(space.name)
        
        # Build parsed components dict
        parsed_components = None
        if parsed_name.is_valid:
            parsed_components = {
                "storey": parsed_name.storey,
                "function_code": parsed_name.function_code,
                "sequence": parsed_name.sequence
            }
            if parsed_name.zone:
                parsed_components["zone"] = parsed_name.zone
        
        return IFCMetadata(
            space_global_id=space.guid,
            space_long_name=space.long_name,
            space_number=parsed_name.sequence if parsed_name.is_valid else space.number,
            ns8360_compliant=parsed_name.is_valid,
            parsed_name_components=parsed_components,
            model_source={
                "file_name": ifc_file_name,
                "file_version": "IFC4",
                "discipline": "ARK"  # Default, could be inferred
            }
        )
    
    def map_classification(self, space: SpaceData) -> ClassificationData:
        """
        Map classification with NS 3940 structured data.
        
        Args:
            space: SpaceData to map
            
        Returns:
            ClassificationData with NS 3940 data
        """
        parsed_name = self.name_parser.parse(space.name)
        
        # Get NS 3940 classification
        classification = None
        source = "unknown"
        
        if parsed_name.is_valid and parsed_name.function_code:
            classification = self.classifier.classify_from_code(parsed_name.function_code)
            source = "parsed_from_name"
        else:
            classification = self.classifier.classify_from_name(space.name)
            source = "inferred_from_name"
        
        # Build NS 3940 data
        ns3940_data = None
        if classification:
            ns3940_data = {
                "code": classification.function_code,
                "label": classification.label,
                "category": classification.category,
                "confidence": classification.confidence,
                "source": source
            }
        
        # Build NS 8360 compliance data
        ns8360_compliance = {
            "name_pattern_valid": parsed_name.is_valid,
            "confidence": parsed_name.confidence
        }
        
        if parsed_name.is_valid:
            ns8360_compliance["parsed_components"] = {
                "storey": parsed_name.storey,
                "function_code": parsed_name.function_code,
                "sequence": parsed_name.sequence
            }
            if parsed_name.zone:
                ns8360_compliance["parsed_components"]["zone"] = parsed_name.zone
        
        return ClassificationData(
            ns3940=ns3940_data,
            ns8360_compliance=ns8360_compliance
        )
    
    def _extract_project_id(self, space: SpaceData, ifc_file_name: str = None) -> str:
        """Extract or generate project ID."""
        # Try to extract from file name
        if ifc_file_name:
            # Remove file extension and use as project ID
            return ifc_file_name.replace('.ifc', '').replace('.IFC', '')
        
        # Fallback to generic project ID
        return f"PROJECT_{datetime.now().strftime('%Y%m%d')}"
    
    def _extract_project_name(self, space: SpaceData, ifc_file_name: str = None) -> str:
        """Extract or generate project name."""
        if ifc_file_name:
            # Clean up file name for display
            name = ifc_file_name.replace('.ifc', '').replace('.IFC', '')
            name = name.replace('_', ' ').replace('-', ' ')
            return name.title()
        
        return "IFC Building Project"
    
    def _extract_building_id(self, space: SpaceData) -> str:
        """Extract building ID from space data."""
        # Could be enhanced to parse IFC building hierarchy
        return "BUILDING_01"
    
    def _extract_building_name(self, space: SpaceData) -> str:
        """Extract building name from space data."""
        # Could be enhanced to parse IFC building hierarchy
        return "Main Building"
    
    def _fallback_storey(self, space: SpaceData) -> str:
        """Fallback storey extraction."""
        # Try to infer from elevation
        if space.elevation >= 0:
            storey_num = int(space.elevation / 3.0) + 1  # Assume 3m per floor
            return f"{storey_num:02d}"
        return "01"
    
    def _fallback_room_number(self, space: SpaceData) -> str:
        """Fallback room number extraction."""
        if space.number:
            return space.number
        
        # Generate from GUID last 3 chars
        return space.guid[-3:] if len(space.guid) >= 3 else "001"
    
    def _generate_readable_name(self, space: SpaceData, classification, parsed_name) -> str:
        """Generate human-readable room name."""
        if space.long_name:
            return space.long_name
        
        # Build structured name
        parts = []
        
        if classification:
            parts.append(classification.label)
        
        if parsed_name.is_valid:
            if parsed_name.storey:
                parts.append(f"Etasje {parsed_name.storey}")
            if parsed_name.zone:
                parts.append(parsed_name.zone)
            if classification:
                parts.append(f"NS3940:{parsed_name.function_code}")
        
        if parts:
            return " | ".join(parts)
        
        return space.name or f"Rom {space.guid[:8]}"


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
            elevation=6.0,  # 2nd floor
            quantities={"NetFloorArea": 24.0, "GrossFloorArea": 25.5}
        ),
        SpaceData(
            guid="GUID-BAD-001", 
            name="Bad 2. etasje",  # Non-compliant name
            long_name="",
            description="Bad med dusj",
            object_type="IfcSpace",
            zone_category="Residential",
            number="001",
            elevation=6.0,
            quantities={"NetFloorArea": 4.8, "GrossFloorArea": 5.2}
        )
    ]
    
    mapper = EnhancedIdentificationMapper()
    
    print("Enhanced Identification Mapper Test Results:")
    print("=" * 60)
    
    for i, space in enumerate(test_spaces, 1):
        print(f"\n--- Test Space {i}: {space.name} ---")
        
        # Test identification mapping
        identification = mapper.map_identification(space, "AkkordSvingen_23_ARK.ifc")
        print(f"Room Number: {identification.room_number}")
        print(f"Room Name: {identification.room_name}")
        print(f"Function: {identification.function}")
        print(f"Occupancy Type: {identification.occupancy_type}")
        print(f"Storey: {identification.storey_name}")
        
        # Test classification mapping
        classification = mapper.map_classification(space)
        if classification.ns3940:
            print(f"NS 3940 Code: {classification.ns3940['code']}")
            print(f"NS 3940 Label: {classification.ns3940['label']}")
            print(f"Classification Confidence: {classification.ns3940['confidence']}")
        
        print(f"NS 8360 Compliant: {classification.ns8360_compliance['name_pattern_valid']}")
        
        # Test IFC metadata mapping
        ifc_metadata = mapper.map_ifc_metadata(space, "AkkordSvingen_23_ARK.ifc")
        print(f"NS 8360 Compliant: {ifc_metadata.ns8360_compliant}")
        if ifc_metadata.parsed_name_components:
            print(f"Parsed Components: {ifc_metadata.parsed_name_components}")
