"""
Enhanced Room Schedule Model

Extended data models for comprehensive room schedule functionality
with support for all sections defined in the room schedule template.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum

from .room_schedule_model import RoomSchedule, RoomScheduleMetadata
from .space_model import SpaceData


class ValidationLevel(Enum):
    """Validation levels for data quality."""
    STRICT = "strict"
    MODERATE = "moderate"
    LENIENT = "lenient"


class FallbackStrategy(Enum):
    """Fallback strategies for missing data."""
    SKIP = "skip"
    DEFAULT = "default"
    INFER = "infer"
    PROMPT = "prompt"


class Phase(Enum):
    """Development phases for feature rollout."""
    CORE = "core"
    ADVANCED = "advanced"
    PRODUCTION = "production"


@dataclass
class MetaData:
    """Enhanced metadata for room schedule with NS 8360 compliance."""
    
    schema_version: str = "1.1.0"
    locale: str = "nb-NO"
    created_at: Optional[datetime] = None
    revised_at: Optional[datetime] = None
    created_by: Optional[str] = None
    revised_by: Optional[str] = None
    revision: int = 0
    status: Dict[str, str] = field(default_factory=lambda: {
        "phase": "Forprosjekt",
        "state": "Utkast"
    })
    project_id: Optional[str] = None
    project_name: Optional[str] = None
    building_id: Optional[str] = None
    building_name: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary for export."""
        return {
            "schema_version": self.schema_version,
            "locale": self.locale,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "revised_at": self.revised_at.isoformat() if self.revised_at else None,
            "created_by": self.created_by,
            "revised_by": self.revised_by,
            "revision": self.revision,
            "status": self.status,
            "project_id": self.project_id,
            "project_name": self.project_name,
            "building_id": self.building_id,
            "building_name": self.building_name
        }


@dataclass
class IdentificationData:
    """Enhanced identification data with NS 8360 structured parsing."""
    
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
    
    # NS 8360 parsed components
    ns8360_parsed: Optional[Dict[str, str]] = None
    ns8360_compliant: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert identification data to dictionary for export."""
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
            "occupancy_type": self.occupancy_type,
            "ns8360_parsed": self.ns8360_parsed,
            "ns8360_compliant": self.ns8360_compliant
        }


@dataclass
class ClassificationData:
    """Enhanced classification data with NS 3940 support."""
    
    ns3940_code: Optional[str] = None
    ns3940_label: Optional[str] = None
    occupancy_type: Optional[str] = None
    category: Optional[str] = None
    is_wet_room: bool = False
    function_code: Optional[str] = None
    confidence_score: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert classification data to dictionary for export."""
        return {
            "ns3940_code": self.ns3940_code,
            "ns3940_label": self.ns3940_label,
            "occupancy_type": self.occupancy_type,
            "category": self.category,
            "is_wet_room": self.is_wet_room,
            "function_code": self.function_code,
            "confidence_score": self.confidence_score
        }


@dataclass
class StructureData:
    """Building structure and hierarchy data."""
    
    site: Optional[str] = None
    building: Optional[str] = None
    building_storey: Optional[str] = None
    zone: Optional[str] = None
    zone_category: Optional[str] = None
    zone_type: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert structure data to dictionary for export."""
        return {
            "site": self.site,
            "building": self.building,
            "building_storey": self.building_storey,
            "zone": self.zone,
            "zone_category": self.zone_category,
            "zone_type": self.zone_type
        }


@dataclass
class GeometryEnhanced:
    """Enhanced geometry data with additional calculations."""
    
    gross_area: Optional[float] = None
    net_area: Optional[float] = None
    perimeter: Optional[float] = None
    height: Optional[float] = None
    volume: Optional[float] = None
    
    # Enhanced geometry
    floor_area: Optional[float] = None
    wall_area: Optional[float] = None
    ceiling_area: Optional[float] = None
    opening_area: Optional[float] = None
    
    # Local origin and placement
    local_origin: Optional[Dict[str, float]] = None
    bounding_box: Optional[Dict[str, float]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert geometry data to dictionary for export."""
        return {
            "gross_area": self.gross_area,
            "net_area": self.net_area,
            "perimeter": self.perimeter,
            "height": self.height,
            "volume": self.volume,
            "floor_area": self.floor_area,
            "wall_area": self.wall_area,
            "ceiling_area": self.ceiling_area,
            "opening_area": self.opening_area,
            "local_origin": self.local_origin,
            "bounding_box": self.bounding_box
        }


@dataclass
class IFCMetadata:
    """Enhanced IFC metadata and references."""
    
    space_global_id: Optional[str] = None
    space_long_name: Optional[str] = None
    space_number: Optional[str] = None
    space_description: Optional[str] = None
    ifc_class: str = "IfcSpace"
    
    # IFC hierarchy
    site_global_id: Optional[str] = None
    building_global_id: Optional[str] = None
    building_storey_global_id: Optional[str] = None
    
    # Model source information
    model_source: Optional[str] = None
    model_author: Optional[str] = None
    model_creation_date: Optional[datetime] = None
    ifc_schema_version: Optional[str] = None
    
    # GUID consistency
    guid_consistency: bool = True
    validation_errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert IFC metadata to dictionary for export."""
        return {
            "space_global_id": self.space_global_id,
            "space_long_name": self.space_long_name,
            "space_number": self.space_number,
            "space_description": self.space_description,
            "ifc_class": self.ifc_class,
            "site_global_id": self.site_global_id,
            "building_global_id": self.building_global_id,
            "building_storey_global_id": self.building_storey_global_id,
            "model_source": self.model_source,
            "model_author": self.model_author,
            "model_creation_date": self.model_creation_date.isoformat() if self.model_creation_date else None,
            "ifc_schema_version": self.ifc_schema_version,
            "guid_consistency": self.guid_consistency,
            "validation_errors": self.validation_errors
        }


@dataclass
class PerformanceRequirements:
    """Technical performance requirements based on NS 3940."""
    
    lighting: Optional[Dict[str, Any]] = None
    acoustics: Optional[Dict[str, Any]] = None
    ventilation: Optional[Dict[str, Any]] = None
    thermal: Optional[Dict[str, Any]] = None
    fire_safety: Optional[Dict[str, Any]] = None
    accessibility: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert performance requirements to dictionary for export."""
        return {
            "lighting": self.lighting,
            "acoustics": self.acoustics,
            "ventilation": self.ventilation,
            "thermal": self.thermal,
            "fire_safety": self.fire_safety,
            "accessibility": self.accessibility
        }


@dataclass
class FinishesData:
    """Surface finishes and materials data."""
    
    floor_finish: Optional[str] = None
    wall_finish: Optional[str] = None
    ceiling_finish: Optional[str] = None
    materials: List[Dict[str, Any]] = field(default_factory=list)
    finish_specifications: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert finishes data to dictionary for export."""
        return {
            "floor_finish": self.floor_finish,
            "wall_finish": self.wall_finish,
            "ceiling_finish": self.ceiling_finish,
            "materials": self.materials,
            "finish_specifications": self.finish_specifications
        }


@dataclass
class OpeningsData:
    """Doors, windows and other openings data."""
    
    doors: List[Dict[str, Any]] = field(default_factory=list)
    windows: List[Dict[str, Any]] = field(default_factory=list)
    openings_list: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert openings data to dictionary for export."""
        return {
            "doors": self.doors,
            "windows": self.windows,
            "openings_list": self.openings_list
        }


@dataclass
class FixturesData:
    """Equipment and fixtures data."""
    
    equipment: List[Dict[str, Any]] = field(default_factory=list)
    fixtures: List[Dict[str, Any]] = field(default_factory=list)
    connections: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert fixtures data to dictionary for export."""
        return {
            "equipment": self.equipment,
            "fixtures": self.fixtures,
            "connections": self.connections
        }


@dataclass
class HSEData:
    """Health, Safety and Environmental requirements."""
    
    accessibility: Optional[Dict[str, Any]] = None
    safety: Optional[Dict[str, Any]] = None
    fire_safety: Optional[Dict[str, Any]] = None
    universal_design: Optional[Dict[str, Any]] = None
    environmental: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert HSE data to dictionary for export."""
        return {
            "accessibility": self.accessibility,
            "safety": self.safety,
            "fire_safety": self.fire_safety,
            "universal_design": self.universal_design,
            "environmental": self.environmental
        }


@dataclass
class EnhancedRoomScheduleData:
    """Enhanced room schedule data model with all sections."""
    
    # Core data (always present)
    metadata: RoomScheduleMetadata
    spaces: List[SpaceData]
    
    # Enhanced sections (optional, based on configuration)
    meta: Optional[MetaData] = None
    identification: Optional[IdentificationData] = None
    classification: Optional[ClassificationData] = None
    structure: Optional[StructureData] = None
    geometry_enhanced: Optional[GeometryEnhanced] = None
    ifc_metadata: Optional[IFCMetadata] = None
    performance_requirements: Optional[PerformanceRequirements] = None
    finishes: Optional[FinishesData] = None
    openings: Optional[OpeningsData] = None
    fixtures: Optional[FixturesData] = None
    hse: Optional[HSEData] = None
    
    # Configuration
    validation_level: ValidationLevel = ValidationLevel.MODERATE
    fallback_strategy: FallbackStrategy = FallbackStrategy.INFER
    phase: Phase = Phase.CORE
    
    def __post_init__(self):
        """Initialize enhanced data after creation."""
        if not self.meta:
            self.meta = MetaData()
        if not self.identification:
            self.identification = IdentificationData()
        if not self.classification:
            self.classification = ClassificationData()
    
    def get_active_sections(self) -> List[str]:
        """Get list of active (non-None) sections."""
        active_sections = []
        
        if self.meta:
            active_sections.append("meta")
        if self.identification:
            active_sections.append("identification")
        if self.classification:
            active_sections.append("classification")
        if self.structure:
            active_sections.append("structure")
        if self.geometry_enhanced:
            active_sections.append("geometry_enhanced")
        if self.ifc_metadata:
            active_sections.append("ifc_metadata")
        if self.performance_requirements:
            active_sections.append("performance_requirements")
        if self.finishes:
            active_sections.append("finishes")
        if self.openings:
            active_sections.append("openings")
        if self.fixtures:
            active_sections.append("fixtures")
        if self.hse:
            active_sections.append("hse")
        
        return active_sections
    
    def get_completion_percentage(self) -> float:
        """Calculate completion percentage based on active sections."""
        total_sections = 11  # Total number of possible sections
        active_sections = len(self.get_active_sections())
        return (active_sections / total_sections) * 100.0
    
    def validate_data_quality(self) -> List[str]:
        """Validate data quality and return list of issues."""
        issues = []
        
        # Validate core data
        if not self.spaces:
            issues.append("No spaces in room schedule")
        
        # Validate enhanced sections
        if self.identification and not self.identification.room_name:
            issues.append("Missing room name in identification")
        
        if self.classification and not self.classification.ns3940_code:
            issues.append("Missing NS 3940 classification code")
        
        if self.geometry_enhanced and not self.geometry_enhanced.gross_area:
            issues.append("Missing gross area in geometry")
        
        return issues
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert enhanced room schedule to dictionary for export."""
        result = {
            "metadata": self.metadata.to_dict(),
            "spaces": [self._space_to_dict(space) for space in self.spaces],
            "active_sections": self.get_active_sections(),
            "completion_percentage": self.get_completion_percentage(),
            "validation_level": self.validation_level.value,
            "fallback_strategy": self.fallback_strategy.value,
            "phase": self.phase.value
        }
        
        # Add enhanced sections if present
        if self.meta:
            result["meta"] = self.meta.to_dict()
        if self.identification:
            result["identification"] = self.identification.to_dict()
        if self.classification:
            result["classification"] = self.classification.to_dict()
        if self.structure:
            result["structure"] = self.structure.to_dict()
        if self.geometry_enhanced:
            result["geometry_enhanced"] = self.geometry_enhanced.to_dict()
        if self.ifc_metadata:
            result["ifc_metadata"] = self.ifc_metadata.to_dict()
        if self.performance_requirements:
            result["performance_requirements"] = self.performance_requirements.to_dict()
        if self.finishes:
            result["finishes"] = self.finishes.to_dict()
        if self.openings:
            result["openings"] = self.openings.to_dict()
        if self.fixtures:
            result["fixtures"] = self.fixtures.to_dict()
        if self.hse:
            result["hse"] = self.hse.to_dict()
        
        return result
    
    def _space_to_dict(self, space: SpaceData) -> Dict[str, Any]:
        """Convert a space to dictionary format."""
        return {
            "guid": space.guid,
            "name": space.name,
            "long_name": space.long_name,
            "description": space.description,
            "object_type": space.object_type,
            "zone_category": space.zone_category,
            "number": space.number,
            "elevation": space.elevation,
            "quantities": space.quantities,
            "processed": space.processed,
            "user_descriptions": space.user_descriptions,
            "surfaces": [self._surface_to_dict(surface) for surface in space.surfaces],
            "relationships": [self._relationship_to_dict(rel) for rel in space.relationships],
            "total_surface_area": space.get_total_surface_area(),
            "surface_area_by_type": space.get_surface_area_by_type()
        }
    
    def _surface_to_dict(self, surface) -> Dict[str, Any]:
        """Convert a surface to dictionary format."""
        return {
            "id": surface.id,
            "type": surface.type,
            "area": surface.area,
            "material": surface.material,
            "ifc_type": surface.ifc_type,
            "user_description": surface.user_description,
            "properties": surface.properties
        }
    
    def _relationship_to_dict(self, relationship) -> Dict[str, Any]:
        """Convert a relationship to dictionary format."""
        return {
            "related_entity_guid": relationship.related_entity_guid,
            "related_entity_name": relationship.related_entity_name,
            "related_entity_description": relationship.related_entity_description,
            "relationship_type": relationship.relationship_type,
            "ifc_relationship_type": relationship.ifc_relationship_type,
            "display_name": relationship.get_display_name(),
            "is_spatial": relationship.is_spatial_relationship()
        }


