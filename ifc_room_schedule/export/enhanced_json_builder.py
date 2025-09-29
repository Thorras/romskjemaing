"""
Enhanced JSON Builder

Handles building enhanced JSON export structure with NS 8360/NS 3940 standards integration.
"""

import json
import os
import shutil
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional
from pathlib import Path

from ..data.space_model import SpaceData
from ..data.enhanced_room_schedule_model import EnhancedRoomScheduleData
from ..mappers.meta_mapper import MetaMapper
from ..mappers.enhanced_identification_mapper import EnhancedIdentificationMapper
from ..mappers.ifc_metadata_mapper import IFCMetadataMapper
from ..mappers.geometry_enhanced_mapper import GeometryEnhancedMapper
from ..mappers.enhanced_classification_mapper import EnhancedClassificationMapper
from ..mappers.ns3940_performance_mapper import NS3940PerformanceMapper
from ..validation.ns8360_validator import NS8360Validator
from ..validation.ns3940_validator import NS3940Validator


class EnhancedJsonBuilder:
    """Builds enhanced JSON export structure with NS standards integration."""
    
    def __init__(self):
        """Initialize the enhanced JSON builder."""
        self.source_file_path: Optional[str] = None
        self.ifc_version: Optional[str] = None
        self.application_version: str = "2.0.0"
        
        # Initialize mappers
        self.meta_mapper = MetaMapper()
        self.identification_mapper = EnhancedIdentificationMapper()
        self.ifc_metadata_mapper = IFCMetadataMapper()
        self.geometry_mapper = GeometryEnhancedMapper()
        self.classification_mapper = EnhancedClassificationMapper()
        self.performance_mapper = NS3940PerformanceMapper()
        
        # Initialize validators
        self.ns8360_validator = NS8360Validator()
        self.ns3940_validator = NS3940Validator()
    
    def set_source_file(self, file_path: str) -> None:
        """Set the source IFC file path."""
        self.source_file_path = file_path
    
    def set_ifc_version(self, version: str) -> None:
        """Set the IFC version."""
        self.ifc_version = version
    
    def build_enhanced_json_structure(self, spaces: List[SpaceData], 
                                    ifc_file_metadata: Optional[Dict[str, Any]] = None,
                                    export_profile: str = "production") -> Dict[str, Any]:
        """
        Build enhanced JSON structure with NS standards integration.
        
        Args:
            spaces: List of SpaceData objects to export
            ifc_file_metadata: Optional IFC file metadata
            export_profile: Export profile (core, advanced, production)
            
        Returns:
            Enhanced JSON structure ready for export
        """
        # Generate enhanced metadata
        enhanced_metadata = self._generate_enhanced_metadata(ifc_file_metadata)
        
        # Build enhanced spaces data
        enhanced_spaces = []
        compliance_stats = {
            "total_spaces": len(spaces),
            "ns8360_compliant": 0,
            "ns3940_classified": 0,
            "performance_requirements": 0
        }
        
        for space in spaces:
            space_data = self._build_enhanced_space_dict(space, export_profile)
            enhanced_spaces.append(space_data)
            
            # Update compliance statistics
            if space_data.get("ns8360_compliance", {}).get("name_pattern_valid", False):
                compliance_stats["ns8360_compliant"] += 1
            
            if space_data.get("classification", {}).get("ns3940"):
                compliance_stats["ns3940_classified"] += 1
            
            if space_data.get("performance_requirements"):
                compliance_stats["performance_requirements"] += 1
        
        # Generate enhanced summary
        enhanced_summary = self._generate_enhanced_summary(spaces, compliance_stats)
        
        # Build complete enhanced structure
        enhanced_json = {
            "metadata": enhanced_metadata,
            "spaces": enhanced_spaces,
            "summary": enhanced_summary,
            "ns_standards_compliance": self._generate_compliance_report(compliance_stats)
        }
        
        return enhanced_json
    
    def _generate_enhanced_metadata(self, ifc_file_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate enhanced metadata with NS standards information."""
        # Use MetaMapper to generate metadata
        meta_data = self.meta_mapper.extract_meta_data(
            self.source_file_path or "unknown.ifc",
            ifc_file_metadata
        )
        
        # Convert to dictionary format
        enhanced_metadata = {
            "export_date": meta_data.timestamps["export_date"],
            "application_version": self.application_version,
            "schema_version": "2.0.0",
            "ns_standards": {
                "ns8360_version": meta_data.ns_compliance["ns8360_version"],
                "ns3940_version": meta_data.ns_compliance["ns3940_version"],
                "tek17_version": meta_data.ns_compliance["tek17_version"],
                "compliance_status": meta_data.ns_compliance["compliance_status"]
            },
            "file_info": meta_data.file_info,
            "project_info": meta_data.project_info,
            "timestamps": meta_data.timestamps
        }
        
        return enhanced_metadata
    
    def _build_enhanced_space_dict(self, space: SpaceData, export_profile: str) -> Dict[str, Any]:
        """Build enhanced dictionary representation of a space."""
        # Basic space properties
        space_dict = {
            "guid": space.guid,
            "properties": {
                "name": space.name,
                "long_name": space.long_name,
                "description": space.description,
                "object_type": space.object_type,
                "zone_category": space.zone_category,
                "number": space.number,
                "elevation": space.elevation,
                "quantities": space.quantities,
                "processed": space.processed,
                "user_descriptions": space.user_descriptions
            }
        }
        
        # Add NS standards sections based on export profile
        if export_profile in ["advanced", "production"]:
            # Identification section
            identification = self.identification_mapper.map_identification(space, self.source_file_path)
            space_dict["identification"] = {
                "project_id": identification.project_id,
                "project_name": identification.project_name,
                "building_id": identification.building_id,
                "building_name": identification.building_name,
                "storey_name": identification.storey_name,
                "storey_elevation_m": identification.storey_elevation_m,
                "room_number": identification.room_number,
                "room_name": identification.room_name,
                "function": identification.function,
                "occupancy_type": identification.occupancy_type
            }
            
            # IFC metadata section
            ifc_metadata = self.identification_mapper.map_ifc_metadata(space, self.source_file_path)
            space_dict["ifc_metadata"] = {
                "space_global_id": ifc_metadata.space_global_id,
                "space_long_name": ifc_metadata.space_long_name,
                "space_number": ifc_metadata.space_number,
                "ns8360_compliant": ifc_metadata.ns8360_compliant,
                "parsed_name_components": ifc_metadata.parsed_name_components,
                "model_source": ifc_metadata.model_source
            }
            
            # Enhanced geometry section
            geometry = self.geometry_mapper.calculate_enhanced_geometry(space)
            space_dict["geometry"] = {
                "length_m": geometry.length_m,
                "width_m": geometry.width_m,
                "height_m": geometry.height_m,
                "net_floor_area_m2": geometry.net_floor_area_m2,
                "gross_floor_area_m2": geometry.gross_floor_area_m2,
                "wall_area_m2": geometry.wall_area_m2,
                "ceiling_area_m2": geometry.ceiling_area_m2,
                "net_volume_m3": geometry.net_volume_m3,
                "gross_volume_m3": geometry.gross_volume_m3,
                "room_origin": geometry.room_origin,
                "room_orientation_deg": geometry.room_orientation_deg,
                "room_shape_type": geometry.room_shape_type,
                "room_aspect_ratio": geometry.room_aspect_ratio,
                "clear_width_m": geometry.clear_width_m,
                "clear_height_m": geometry.clear_height_m,
                "turning_radius_m": geometry.turning_radius_m,
                "estimated_dimensions": geometry.estimated_dimensions,
                "estimation_confidence": geometry.estimation_confidence,
                "estimation_method": geometry.estimation_method
            }
            
            # Enhanced classification section
            classification = self.classification_mapper.map_classification(space)
            space_dict["classification"] = {
                "ns3940": classification.ns3940,
                "ns8360_compliance": classification.ns8360_compliance,
                "tfm": classification.tfm,
                "custom_codes": classification.custom_codes,
                "validation_status": classification.validation_status,
                "overall_confidence": classification.overall_confidence,
                "classification_source": classification.classification_source
            }
            
            # Performance requirements section
            if export_profile == "production":
                performance = self.performance_mapper.map_performance_requirements(space)
                space_dict["performance_requirements"] = {
                    "lighting": performance.lighting,
                    "acoustics": performance.acoustics,
                    "ventilation": performance.ventilation,
                    "thermal": performance.thermal,
                    "water_sanitary": performance.water_sanitary,
                    "accessibility": performance.accessibility,
                    "equipment": performance.equipment,
                    "fire_safety": performance.fire_safety,
                    "energy_efficiency": performance.energy_efficiency,
                    "source": performance.source,
                    "confidence": performance.confidence,
                    "function_code": performance.function_code,
                    "room_type": performance.room_type
                }
        
        # Add traditional sections (always included)
        space_dict["surfaces"] = [self._build_surface_dict(surface) for surface in space.surfaces]
        space_dict["space_boundaries"] = [self._build_space_boundary_dict(boundary) for boundary in space.space_boundaries]
        space_dict["relationships"] = [self._build_relationship_dict(relationship) for relationship in space.relationships]
        
        return space_dict
    
    def _build_surface_dict(self, surface) -> Dict[str, Any]:
        """Build dictionary representation of a surface."""
        return {
            "id": surface.id,
            "type": surface.type,
            "area": surface.area,
            "material": surface.material,
            "ifc_type": surface.ifc_type,
            "related_space_guid": surface.related_space_guid,
            "user_description": surface.user_description,
            "properties": surface.properties
        }
    
    def _build_space_boundary_dict(self, boundary) -> Dict[str, Any]:
        """Build dictionary representation of a space boundary."""
        return boundary.to_dict()
    
    def _build_relationship_dict(self, relationship) -> Dict[str, Any]:
        """Build dictionary representation of a relationship."""
        return {
            "related_entity_guid": relationship.related_entity_guid,
            "related_entity_name": relationship.related_entity_name,
            "related_entity_description": relationship.related_entity_description,
            "relationship_type": relationship.relationship_type,
            "ifc_relationship_type": relationship.ifc_relationship_type
        }
    
    def _generate_enhanced_summary(self, spaces: List[SpaceData], compliance_stats: Dict[str, int]) -> Dict[str, Any]:
        """Generate enhanced summary with NS standards statistics."""
        # Basic summary
        total_spaces = len(spaces)
        processed_spaces = sum(1 for space in spaces if space.processed)
        
        # Calculate areas
        total_surface_area = sum(space.get_total_surface_area() for space in spaces)
        total_boundary_area = sum(space.get_total_boundary_area() for space in spaces)
        
        # NS standards compliance
        ns8360_compliance_percentage = (compliance_stats["ns8360_compliant"] / total_spaces * 100) if total_spaces > 0 else 0
        ns3940_classification_percentage = (compliance_stats["ns3940_classified"] / total_spaces * 100) if total_spaces > 0 else 0
        performance_requirements_percentage = (compliance_stats["performance_requirements"] / total_spaces * 100) if total_spaces > 0 else 0
        
        # Room type distribution
        room_type_distribution = {}
        for space in spaces:
            # Try to get room type from classification
            classification = self.classification_mapper.map_classification(space)
            if classification.ns3940 and classification.ns3940.get("label"):
                room_type = classification.ns3940["label"]
                room_type_distribution[room_type] = room_type_distribution.get(room_type, 0) + 1
        
        enhanced_summary = {
            "total_spaces": total_spaces,
            "processed_spaces": processed_spaces,
            "total_surface_area": round(total_surface_area, 2),
            "total_boundary_area": round(total_boundary_area, 2),
            "ns_standards_compliance": {
                "ns8360_compliant_spaces": compliance_stats["ns8360_compliant"],
                "ns8360_compliance_percentage": round(ns8360_compliance_percentage, 1),
                "ns3940_classified_spaces": compliance_stats["ns3940_classified"],
                "ns3940_classification_percentage": round(ns3940_classification_percentage, 1),
                "performance_requirements_spaces": compliance_stats["performance_requirements"],
                "performance_requirements_percentage": round(performance_requirements_percentage, 1)
            },
            "room_type_distribution": room_type_distribution,
            "export_profile": "enhanced_with_ns_standards",
            "standards_versions": {
                "ns8360": "NS 8360:2023",
                "ns3940": "NS 3940:2023",
                "tek17": "TEK17"
            }
        }
        
        return enhanced_summary
    
    def _generate_compliance_report(self, compliance_stats: Dict[str, int]) -> Dict[str, Any]:
        """Generate NS standards compliance report."""
        total_spaces = compliance_stats["total_spaces"]
        
        return {
            "overall_compliance": {
                "total_spaces": total_spaces,
                "ns8360_compliant": compliance_stats["ns8360_compliant"],
                "ns3940_classified": compliance_stats["ns3940_classified"],
                "performance_requirements": compliance_stats["performance_requirements"]
            },
            "compliance_percentages": {
                "ns8360": round((compliance_stats["ns8360_compliant"] / total_spaces * 100) if total_spaces > 0 else 0, 1),
                "ns3940": round((compliance_stats["ns3940_classified"] / total_spaces * 100) if total_spaces > 0 else 0, 1),
                "performance": round((compliance_stats["performance_requirements"] / total_spaces * 100) if total_spaces > 0 else 0, 1)
            },
            "recommendations": self._generate_compliance_recommendations(compliance_stats),
            "validation_timestamp": datetime.now().isoformat()
        }
    
    def _generate_compliance_recommendations(self, compliance_stats: Dict[str, int]) -> List[str]:
        """Generate compliance improvement recommendations."""
        recommendations = []
        total_spaces = compliance_stats["total_spaces"]
        
        if total_spaces == 0:
            return recommendations
        
        ns8360_percentage = (compliance_stats["ns8360_compliant"] / total_spaces * 100)
        ns3940_percentage = (compliance_stats["ns3940_classified"] / total_spaces * 100)
        
        if ns8360_percentage < 50:
            recommendations.append("Improve NS 8360 naming compliance - use SPC-{storey}-{zone}-{function}-{sequence} format")
        
        if ns3940_percentage < 70:
            recommendations.append("Improve NS 3940 classification - ensure room names contain recognizable function keywords")
        
        if compliance_stats["performance_requirements"] < total_spaces * 0.8:
            recommendations.append("Add performance requirements for more spaces using NS 3940 defaults")
        
        return recommendations
    
    def validate_enhanced_export_data(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate enhanced export data for completeness and correctness."""
        errors = []
        
        # Check required top-level keys
        required_keys = ["metadata", "spaces", "summary", "ns_standards_compliance"]
        for key in required_keys:
            if key not in data:
                errors.append(f"Missing required key: {key}")
        
        # Validate metadata
        if "metadata" in data:
            metadata = data["metadata"]
            if "ns_standards" not in metadata:
                errors.append("Missing ns_standards in metadata")
            if "export_date" not in metadata:
                errors.append("Missing export_date in metadata")
        
        # Validate spaces
        if "spaces" in data:
            spaces = data["spaces"]
            if not isinstance(spaces, list):
                errors.append("Spaces must be a list")
            else:
                for i, space in enumerate(spaces):
                    space_errors = self._validate_enhanced_space_data(space, i)
                    errors.extend(space_errors)
        
        return len(errors) == 0, errors
    
    def _validate_enhanced_space_data(self, space_data: Dict[str, Any], space_index: int) -> List[str]:
        """Validate enhanced space data."""
        errors = []
        prefix = f"Space {space_index}"
        
        # Check required keys
        required_keys = ["guid", "properties", "identification", "classification"]
        for key in required_keys:
            if key not in space_data:
                errors.append(f"{prefix}: Missing required key {key}")
        
        # Validate NS standards sections
        if "classification" in space_data:
            classification = space_data["classification"]
            if "ns3940" not in classification and "ns8360_compliance" not in classification:
                errors.append(f"{prefix}: Missing NS standards classification data")
        
        return errors
    
    def export_enhanced_json(self, spaces: List[SpaceData], filename: str,
                           ifc_file_metadata: Optional[Dict[str, Any]] = None,
                           export_profile: str = "production",
                           validate: bool = True) -> Tuple[bool, List[str]]:
        """
        Complete enhanced export workflow with NS standards integration.
        
        Args:
            spaces: List of SpaceData objects to export
            filename: Output filename
            ifc_file_metadata: Optional IFC file metadata
            export_profile: Export profile (core, advanced, production)
            validate: Whether to validate data before export
            
        Returns:
            Tuple of (success, list_of_errors_or_messages)
        """
        try:
            # Build enhanced JSON structure
            json_data = self.build_enhanced_json_structure(spaces, ifc_file_metadata, export_profile)
            
            # Validate if requested
            if validate:
                is_valid, validation_errors = self.validate_enhanced_export_data(json_data)
                if not is_valid:
                    return False, validation_errors
            
            # Write to file
            success, write_message = self._write_enhanced_json_file(filename, json_data)
            if success:
                return True, [f"Successfully exported {len(spaces)} spaces with NS standards to {filename}"]
            else:
                return False, [f"Failed to write enhanced JSON file: {write_message}"]
                
        except Exception as e:
            return False, [f"Enhanced export failed: {str(e)}"]
    
    def _write_enhanced_json_file(self, filename: str, data: Dict[str, Any], indent: int = 2) -> Tuple[bool, str]:
        """Write enhanced JSON data to file with error handling."""
        try:
            if not filename:
                return False, "Filename cannot be empty"
            
            file_path = Path(filename)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Check write permissions
            if file_path.exists():
                if not os.access(file_path, os.W_OK):
                    return False, f"No write permission for file: {filename}"
            else:
                if not os.access(file_path.parent, os.W_OK):
                    return False, f"No write permission for directory: {file_path.parent}"
            
            # Check disk space
            free_space = shutil.disk_usage(file_path.parent).free
            if free_space < 1024 * 1024:  # 1MB minimum
                return False, f"Insufficient disk space. Available: {free_space / (1024*1024):.1f}MB"
            
            # Validate JSON serialization
            try:
                json.dumps(data, indent=indent, ensure_ascii=False)
            except (TypeError, ValueError) as e:
                return False, f"Data cannot be serialized to JSON: {str(e)}"
            
            # Write to temporary file first, then rename for atomic operation
            temp_filename = str(file_path) + '.tmp'
            try:
                with open(temp_filename, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=indent, ensure_ascii=False)
                
                # Atomic rename
                if os.name == 'nt':  # Windows
                    if file_path.exists():
                        os.remove(file_path)
                os.rename(temp_filename, filename)
                
                return True, "Enhanced JSON file written successfully"
                
            except Exception as e:
                # Clean up temp file
                if os.path.exists(temp_filename):
                    try:
                        os.remove(temp_filename)
                    except:
                        pass
                raise e
            
        except PermissionError as e:
            return False, f"Permission denied: {str(e)}"
        except OSError as e:
            return False, f"OS error: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error writing enhanced JSON file: {str(e)}"


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
            elevation=6.0,
            quantities={"NetFloorArea": 24.0, "GrossFloorArea": 25.5}
        ),
        SpaceData(
            guid="GUID-BAD-001",
            name="Bad 2. etasje",
            description="Bad med dusj",
            object_type="IfcSpace",
            zone_category="Residential",
            number="001",
            elevation=6.0,
            quantities={"NetFloorArea": 4.8, "GrossFloorArea": 5.2}
        )
    ]
    
    builder = EnhancedJsonBuilder()
    builder.set_source_file("AkkordSvingen_23_ARK.ifc")
    builder.set_ifc_version("IFC4")
    
    print("Enhanced JSON Builder Test Results:")
    print("=" * 60)
    
    # Test enhanced export
    success, messages = builder.export_enhanced_json(
        test_spaces, 
        "test_enhanced_export.json",
        export_profile="production"
    )
    
    print(f"Export Success: {success}")
    for message in messages:
        print(f"Message: {message}")
    
    # Test JSON structure building
    json_data = builder.build_enhanced_json_structure(test_spaces, export_profile="production")
    
    print(f"\nJSON Structure Keys: {list(json_data.keys())}")
    print(f"Number of Spaces: {len(json_data['spaces'])}")
    print(f"NS Standards Compliance: {json_data['ns_standards_compliance']['compliance_percentages']}")
    
    # Test validation
    is_valid, errors = builder.validate_enhanced_export_data(json_data)
    print(f"Validation Valid: {is_valid}")
    if errors:
        print(f"Validation Errors: {errors}")
