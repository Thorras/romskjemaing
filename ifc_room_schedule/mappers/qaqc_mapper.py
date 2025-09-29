"""
QA/QC Mapper

Maps IFC data to QA/QC (Quality Assurance/Quality Control) section including
hold points, inspections, handover documentation, and quality control workflows.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from ..data.space_model import SpaceData
from ..parsers.ns8360_name_parser import NS8360NameParser
from ..mappers.ns3940_classifier import NS3940Classifier


class InspectionType(Enum):
    """Types of inspections."""
    RECEIPT = "mottak"
    SUBSTRATE = "underlag"
    CLOSING = "lukking"
    FINISHED = "ferdig"


class EvidenceType(Enum):
    """Types of evidence for inspections."""
    PHOTO = "foto"
    MEASUREMENT_REPORT = "målerapport"
    CHECKLIST = "sjekkliste"


class HandoverDocType(Enum):
    """Types of handover documentation."""
    FDV = "FDV"
    PRODUCT_DATASHEET = "produktdatablad"
    EPD = "EPD"
    COMPLIANCE_DECLARATION = "samsvarserklæring"
    AS_BUILT = "as-built"


@dataclass
class HoldPoint:
    """Hold point for quality control."""
    
    code: str
    description: str
    by_trade: str  # ARK, RIV, RIE, RIB, RIA, RIBr
    required: bool = True
    critical: bool = False
    phase: str = "Utførelse"  # Forprosjekt, Detaljprosjektering, Utførelse, Ferdigstillelse
    prerequisites: List[str] = None
    acceptance_criteria: str = None
    responsible_party: str = None
    
    def __post_init__(self):
        if self.prerequisites is None:
            self.prerequisites = []


@dataclass
class Inspection:
    """Quality inspection record."""
    
    type: InspectionType
    checklist_id: Optional[str] = None
    acceptance_criteria: Optional[str] = None
    evidence: EvidenceType = EvidenceType.CHECKLIST
    responsible: Optional[str] = None
    scheduled_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None
    status: str = "pending"  # pending, in_progress, completed, failed
    notes: Optional[str] = None
    photos: List[str] = None
    measurements: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.photos is None:
            self.photos = []
        if self.measurements is None:
            self.measurements = {}


@dataclass
class QAQCData:
    """Complete QA/QC data for a space."""
    
    hold_points: List[HoldPoint]
    inspections: List[Inspection]
    handover_docs_required: List[HandoverDocType]
    quality_control_plan: Optional[str] = None
    last_updated: datetime = None
    
    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.now()


class QAQCMapper:
    """Maps IFC data to QA/QC section."""
    
    def __init__(self):
        """Initialize the QA/QC mapper."""
        self.name_parser = NS8360NameParser()
        self.classifier = NS3940Classifier()
    
    def extract_qa_qc_requirements(self, space: SpaceData) -> QAQCData:
        """
        Extract QA/QC requirements from space data.
        
        Args:
            space: SpaceData to extract QA/QC requirements from
            
        Returns:
            QAQCData with extracted QA/QC information
        """
        # Get room type for default requirements
        room_type = self._get_room_type(space)
        
        # Extract hold points
        hold_points = self._extract_hold_points(space, room_type)
        
        # Extract inspections
        inspections = self._extract_inspections(space, room_type)
        
        # Extract handover documentation requirements
        handover_docs = self._extract_handover_docs(space, room_type)
        
        return QAQCData(
            hold_points=hold_points,
            inspections=inspections,
            handover_docs_required=handover_docs
        )
    
    def generate_quality_control_plan(self, space: SpaceData) -> str:
        """
        Generate a quality control plan for the space.
        
        Args:
            space: SpaceData to generate plan for
            
        Returns:
            Quality control plan as string
        """
        room_type = self._get_room_type(space)
        qa_qc_data = self.extract_qa_qc_requirements(space)
        
        plan = f"Quality Control Plan for {space.name}\n"
        plan += f"Room Type: {room_type}\n"
        plan += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        
        plan += "HOLD POINTS:\n"
        for i, hold_point in enumerate(qa_qc_data.hold_points, 1):
            plan += f"{i}. {hold_point.code}: {hold_point.description}\n"
            plan += f"   Trade: {hold_point.by_trade}\n"
            if hold_point.critical:
                plan += f"   CRITICAL\n"
            plan += "\n"
        
        plan += "INSPECTIONS:\n"
        for i, inspection in enumerate(qa_qc_data.inspections, 1):
            plan += f"{i}. {inspection.type.value}: {inspection.acceptance_criteria or 'Standard criteria'}\n"
            plan += f"   Evidence: {inspection.evidence.value}\n"
            if inspection.responsible:
                plan += f"   Responsible: {inspection.responsible}\n"
            plan += "\n"
        
        plan += "HANDOVER DOCUMENTATION:\n"
        for doc_type in qa_qc_data.handover_docs_required:
            plan += f"- {doc_type.value}\n"
        
        return plan
    
    def validate_quality_compliance(self, space: SpaceData) -> Dict[str, Any]:
        """
        Validate quality compliance for space.
        
        Args:
            space: SpaceData to validate
            
        Returns:
            Dictionary with compliance status and issues
        """
        qa_qc_data = self.extract_qa_qc_requirements(space)
        
        compliance = {
            "compliant": True,
            "issues": [],
            "warnings": [],
            "hold_points_required": len(qa_qc_data.hold_points),
            "inspections_required": len(qa_qc_data.inspections),
            "handover_docs_required": len(qa_qc_data.handover_docs_required)
        }
        
        # Check for critical hold points
        critical_hold_points = [hp for hp in qa_qc_data.hold_points if hp.critical]
        if critical_hold_points:
            compliance["warnings"].append(f"{len(critical_hold_points)} critical hold points identified")
        
        # Check for missing acceptance criteria
        missing_criteria = [i for i in qa_qc_data.inspections if not i.acceptance_criteria]
        if missing_criteria:
            compliance["issues"].append(f"{len(missing_criteria)} inspections missing acceptance criteria")
            compliance["compliant"] = False
        
        # Check for missing responsible parties
        missing_responsible = [i for i in qa_qc_data.inspections if not i.responsible]
        if missing_responsible:
            compliance["warnings"].append(f"{len(missing_responsible)} inspections missing responsible party")
        
        return compliance
    
    def _get_room_type(self, space: SpaceData) -> str:
        """Get room type from space data."""
        if space.name:
            parsed_name = self.name_parser.parse(space.name)
            if parsed_name.is_valid and parsed_name.function_code:
                return parsed_name.function_code
            
            classification = self.classifier.classify_from_name(space.name)
            if classification:
                return classification.function_code
        
        return "111"  # Default to oppholdsrom
    
    def _extract_hold_points(self, space: SpaceData, room_type: str) -> List[HoldPoint]:
        """Extract hold points for space."""
        # Look for hold point properties in space
        hold_points = []
        
        # Check if space has hold point properties
        if space.quantities:
            # Could extract from property sets
            pass
        
        # Apply defaults based on room type
        defaults = self._get_room_type_defaults(room_type)
        hold_points_data = defaults.get("hold_points", [])
        
        for hp_data in hold_points_data:
            hold_points.append(HoldPoint(
                code=hp_data["code"],
                description=hp_data["description"],
                by_trade=hp_data["by_trade"],
                required=hp_data.get("required", True),
                critical=hp_data.get("critical", False),
                phase=hp_data.get("phase", "Utførelse"),
                prerequisites=hp_data.get("prerequisites", []),
                acceptance_criteria=hp_data.get("acceptance_criteria"),
                responsible_party=hp_data.get("responsible_party")
            ))
        
        return hold_points
    
    def _extract_inspections(self, space: SpaceData, room_type: str) -> List[Inspection]:
        """Extract inspections for space."""
        # Look for inspection properties in space
        inspections = []
        
        # Check if space has inspection properties
        if space.quantities:
            # Could extract from property sets
            pass
        
        # Apply defaults based on room type
        defaults = self._get_room_type_defaults(room_type)
        inspections_data = defaults.get("inspections", [])
        
        for insp_data in inspections_data:
            inspections.append(Inspection(
                type=InspectionType(insp_data["type"]),
                checklist_id=insp_data.get("checklist_id"),
                acceptance_criteria=insp_data.get("acceptance_criteria"),
                evidence=EvidenceType(insp_data.get("evidence", "sjekkliste")),
                responsible=insp_data.get("responsible"),
                scheduled_date=insp_data.get("scheduled_date"),
                completed_date=insp_data.get("completed_date"),
                status=insp_data.get("status", "pending"),
                notes=insp_data.get("notes"),
                photos=insp_data.get("photos", []),
                measurements=insp_data.get("measurements", {})
            ))
        
        return inspections
    
    def _extract_handover_docs(self, space: SpaceData, room_type: str) -> List[HandoverDocType]:
        """Extract handover documentation requirements for space."""
        # Look for handover doc properties in space
        handover_docs = []
        
        # Check if space has handover doc properties
        if space.quantities:
            # Could extract from property sets
            pass
        
        # Apply defaults based on room type
        defaults = self._get_room_type_defaults(room_type)
        handover_docs_data = defaults.get("handover_docs_required", [])
        
        for doc_type in handover_docs_data:
            handover_docs.append(HandoverDocType(doc_type))
        
        return handover_docs
    
    def _get_room_type_defaults(self, room_type: str) -> Dict[str, Any]:
        """Get default QA/QC requirements for room type."""
        defaults = {
            "111": {  # Oppholdsrom
                "hold_points": [
                    {
                        "code": "HP-001",
                        "description": "Underlag for gulvbelegg",
                        "by_trade": "RIV",
                        "required": True,
                        "critical": True,
                        "phase": "Utførelse",
                        "prerequisites": ["Struktur ferdig", "VVS-installasjoner ferdig"],
                        "acceptance_criteria": "Underlag plan, tørt og rent",
                        "responsible_party": "RIV-ansvarlig"
                    },
                    {
                        "code": "HP-002",
                        "description": "Gulvbelegg installasjon",
                        "by_trade": "RIV",
                        "required": True,
                        "critical": False,
                        "phase": "Utførelse",
                        "prerequisites": ["HP-001 godkjent"],
                        "acceptance_criteria": "Gulvbelegg installert i henhold til spesifikasjon",
                        "responsible_party": "RIV-ansvarlig"
                    },
                    {
                        "code": "HP-003",
                        "description": "Maling av vegger",
                        "by_trade": "RIV",
                        "required": True,
                        "critical": False,
                        "phase": "Utførelse",
                        "prerequisites": ["Gipsplater montert", "Spikling ferdig"],
                        "acceptance_criteria": "Maling utført i henhold til spesifikasjon",
                        "responsible_party": "RIV-ansvarlig"
                    }
                ],
                "inspections": [
                    {
                        "type": "mottak",
                        "checklist_id": "CHK-001",
                        "acceptance_criteria": "Materialer mottatt i henhold til bestilling",
                        "evidence": "sjekkliste",
                        "responsible": "Materialansvarlig"
                    },
                    {
                        "type": "underlag",
                        "checklist_id": "CHK-002",
                        "acceptance_criteria": "Underlag plan, tørt og rent",
                        "evidence": "målerapport",
                        "responsible": "RIV-ansvarlig"
                    },
                    {
                        "type": "lukking",
                        "checklist_id": "CHK-003",
                        "acceptance_criteria": "Alle arbeider utført i henhold til spesifikasjon",
                        "evidence": "sjekkliste",
                        "responsible": "RIV-ansvarlig"
                    },
                    {
                        "type": "ferdig",
                        "checklist_id": "CHK-004",
                        "acceptance_criteria": "Rom ferdig for overlevering",
                        "evidence": "foto",
                        "responsible": "Prosjektleder"
                    }
                ],
                "handover_docs_required": ["FDV", "produktdatablad", "samsvarserklæring"]
            },
            "130": {  # Våtrom
                "hold_points": [
                    {
                        "code": "HP-101",
                        "description": "Vannsperre installasjon",
                        "by_trade": "RIV",
                        "required": True,
                        "critical": True,
                        "phase": "Utførelse",
                        "prerequisites": ["VVS-installasjoner ferdig", "Underlag plan"],
                        "acceptance_criteria": "Vannsperre installert i henhold til NS 3420",
                        "responsible_party": "RIV-ansvarlig"
                    },
                    {
                        "code": "HP-102",
                        "description": "Flisarbeid",
                        "by_trade": "RIV",
                        "required": True,
                        "critical": True,
                        "phase": "Utførelse",
                        "prerequisites": ["HP-101 godkjent", "Vannsperre testet"],
                        "acceptance_criteria": "Fliser installert i henhold til NS 3420-U",
                        "responsible_party": "RIV-ansvarlig"
                    },
                    {
                        "code": "HP-103",
                        "description": "Sanitærmontasje",
                        "by_trade": "RIV",
                        "required": True,
                        "critical": False,
                        "phase": "Utførelse",
                        "prerequisites": ["Flisarbeid ferdig"],
                        "acceptance_criteria": "Sanitær installert og funksjonell",
                        "responsible_party": "RIV-ansvarlig"
                    }
                ],
                "inspections": [
                    {
                        "type": "mottak",
                        "checklist_id": "CHK-101",
                        "acceptance_criteria": "Materialer mottatt i henhold til bestilling",
                        "evidence": "sjekkliste",
                        "responsible": "Materialansvarlig"
                    },
                    {
                        "type": "underlag",
                        "checklist_id": "CHK-102",
                        "acceptance_criteria": "Underlag plan, tørt og rent, vannsperre installert",
                        "evidence": "målerapport",
                        "responsible": "RIV-ansvarlig"
                    },
                    {
                        "type": "lukking",
                        "checklist_id": "CHK-103",
                        "acceptance_criteria": "Alle arbeider utført i henhold til spesifikasjon",
                        "evidence": "sjekkliste",
                        "responsible": "RIV-ansvarlig"
                    },
                    {
                        "type": "ferdig",
                        "checklist_id": "CHK-104",
                        "acceptance_criteria": "Våtrom ferdig for overlevering, vannsperre testet",
                        "evidence": "foto",
                        "responsible": "Prosjektleder"
                    }
                ],
                "handover_docs_required": ["FDV", "produktdatablad", "EPD", "samsvarserklæring", "as-built"]
            },
            "131": {  # WC
                "hold_points": [
                    {
                        "code": "HP-201",
                        "description": "Vannsperre installasjon",
                        "by_trade": "RIV",
                        "required": True,
                        "critical": True,
                        "phase": "Utførelse",
                        "prerequisites": ["VVS-installasjoner ferdig", "Underlag plan"],
                        "acceptance_criteria": "Vannsperre installert i henhold til NS 3420",
                        "responsible_party": "RIV-ansvarlig"
                    },
                    {
                        "code": "HP-202",
                        "description": "Flisarbeid",
                        "by_trade": "RIV",
                        "required": True,
                        "critical": True,
                        "phase": "Utførelse",
                        "prerequisites": ["HP-201 godkjent", "Vannsperre testet"],
                        "acceptance_criteria": "Fliser installert i henhold til NS 3420-U",
                        "responsible_party": "RIV-ansvarlig"
                    },
                    {
                        "code": "HP-203",
                        "description": "Sanitærmontasje",
                        "by_trade": "RIV",
                        "required": True,
                        "critical": False,
                        "phase": "Utførelse",
                        "prerequisites": ["Flisarbeid ferdig"],
                        "acceptance_criteria": "Sanitær installert og funksjonell",
                        "responsible_party": "RIV-ansvarlig"
                    }
                ],
                "inspections": [
                    {
                        "type": "mottak",
                        "checklist_id": "CHK-201",
                        "acceptance_criteria": "Materialer mottatt i henhold til bestilling",
                        "evidence": "sjekkliste",
                        "responsible": "Materialansvarlig"
                    },
                    {
                        "type": "underlag",
                        "checklist_id": "CHK-202",
                        "acceptance_criteria": "Underlag plan, tørt og rent, vannsperre installert",
                        "evidence": "målerapport",
                        "responsible": "RIV-ansvarlig"
                    },
                    {
                        "type": "lukking",
                        "checklist_id": "CHK-203",
                        "acceptance_criteria": "Alle arbeider utført i henhold til spesifikasjon",
                        "evidence": "sjekkliste",
                        "responsible": "RIV-ansvarlig"
                    },
                    {
                        "type": "ferdig",
                        "checklist_id": "CHK-204",
                        "acceptance_criteria": "WC ferdig for overlevering, vannsperre testet",
                        "evidence": "foto",
                        "responsible": "Prosjektleder"
                    }
                ],
                "handover_docs_required": ["FDV", "produktdatablad", "EPD", "samsvarserklæring"]
            },
            "132": {  # Baderom
                "hold_points": [
                    {
                        "code": "HP-301",
                        "description": "Vannsperre installasjon",
                        "by_trade": "RIV",
                        "required": True,
                        "critical": True,
                        "phase": "Utførelse",
                        "prerequisites": ["VVS-installasjoner ferdig", "Underlag plan"],
                        "acceptance_criteria": "Vannsperre installert i henhold til NS 3420",
                        "responsible_party": "RIV-ansvarlig"
                    },
                    {
                        "code": "HP-302",
                        "description": "Flisarbeid",
                        "by_trade": "RIV",
                        "required": True,
                        "critical": True,
                        "phase": "Utførelse",
                        "prerequisites": ["HP-301 godkjent", "Vannsperre testet"],
                        "acceptance_criteria": "Fliser installert i henhold til NS 3420-U",
                        "responsible_party": "RIV-ansvarlig"
                    },
                    {
                        "code": "HP-303",
                        "description": "Sanitærmontasje",
                        "by_trade": "RIV",
                        "required": True,
                        "critical": False,
                        "phase": "Utførelse",
                        "prerequisites": ["Flisarbeid ferdig"],
                        "acceptance_criteria": "Sanitær installert og funksjonell",
                        "responsible_party": "RIV-ansvarlig"
                    }
                ],
                "inspections": [
                    {
                        "type": "mottak",
                        "checklist_id": "CHK-301",
                        "acceptance_criteria": "Materialer mottatt i henhold til bestilling",
                        "evidence": "sjekkliste",
                        "responsible": "Materialansvarlig"
                    },
                    {
                        "type": "underlag",
                        "checklist_id": "CHK-302",
                        "acceptance_criteria": "Underlag plan, tørt og rent, vannsperre installert",
                        "evidence": "målerapport",
                        "responsible": "RIV-ansvarlig"
                    },
                    {
                        "type": "lukking",
                        "checklist_id": "CHK-303",
                        "acceptance_criteria": "Alle arbeider utført i henhold til spesifikasjon",
                        "evidence": "sjekkliste",
                        "responsible": "RIV-ansvarlig"
                    },
                    {
                        "type": "ferdig",
                        "checklist_id": "CHK-304",
                        "acceptance_criteria": "Baderom ferdig for overlevering, vannsperre testet",
                        "evidence": "foto",
                        "responsible": "Prosjektleder"
                    }
                ],
                "handover_docs_required": ["FDV", "produktdatablad", "EPD", "samsvarserklæring", "as-built"]
            },
            "140": {  # Kjøkken
                "hold_points": [
                    {
                        "code": "HP-401",
                        "description": "Underlag for gulvbelegg",
                        "by_trade": "RIV",
                        "required": True,
                        "critical": True,
                        "phase": "Utførelse",
                        "prerequisites": ["Struktur ferdig", "VVS-installasjoner ferdig"],
                        "acceptance_criteria": "Underlag plan, tørt og rent",
                        "responsible_party": "RIV-ansvarlig"
                    },
                    {
                        "code": "HP-402",
                        "description": "Kjøkkenmøbler montering",
                        "by_trade": "RIV",
                        "required": True,
                        "critical": False,
                        "phase": "Utførelse",
                        "prerequisites": ["HP-401 godkjent"],
                        "acceptance_criteria": "Kjøkkenmøbler montert i henhold til spesifikasjon",
                        "responsible_party": "RIV-ansvarlig"
                    },
                    {
                        "code": "HP-403",
                        "description": "VVS-tilkoblinger",
                        "by_trade": "RIV",
                        "required": True,
                        "critical": True,
                        "phase": "Utførelse",
                        "prerequisites": ["Kjøkkenmøbler montert"],
                        "acceptance_criteria": "VVS-tilkoblinger testet og funksjonelle",
                        "responsible_party": "RIV-ansvarlig"
                    }
                ],
                "inspections": [
                    {
                        "type": "mottak",
                        "checklist_id": "CHK-401",
                        "acceptance_criteria": "Materialer mottatt i henhold til bestilling",
                        "evidence": "sjekkliste",
                        "responsible": "Materialansvarlig"
                    },
                    {
                        "type": "underlag",
                        "checklist_id": "CHK-402",
                        "acceptance_criteria": "Underlag plan, tørt og rent",
                        "evidence": "målerapport",
                        "responsible": "RIV-ansvarlig"
                    },
                    {
                        "type": "lukking",
                        "checklist_id": "CHK-403",
                        "acceptance_criteria": "Alle arbeider utført i henhold til spesifikasjon",
                        "evidence": "sjekkliste",
                        "responsible": "RIV-ansvarlig"
                    },
                    {
                        "type": "ferdig",
                        "checklist_id": "CHK-404",
                        "acceptance_criteria": "Kjøkken ferdig for overlevering, VVS testet",
                        "evidence": "foto",
                        "responsible": "Prosjektleder"
                    }
                ],
                "handover_docs_required": ["FDV", "produktdatablad", "EPD", "samsvarserklæring"]
            }
        }
        
        return defaults.get(room_type, defaults["111"])  # Default to oppholdsrom


# Example usage and testing
if __name__ == "__main__":
    mapper = QAQCMapper()
    
    # Test with sample space
    from ..data.space_model import SpaceData
    
    sample_space = SpaceData(
        guid="test_space",
        name="SPC-02-A101-111-003",
        long_name="Stue | 02/A101 | NS3940:111",
        description="Test space",
        object_type="IfcSpace",
        zone_category="A101",
        number="003",
        elevation=0.0,
        quantities={"Height": 2.4},
        surfaces=[],
        space_boundaries=[],
        relationships=[]
    )
    
    print("QA/QC Mapper Test:")
    print("=" * 50)
    
    # Test QA/QC extraction
    qa_qc = mapper.extract_qa_qc_requirements(sample_space)
    print(f"Hold points: {len(qa_qc.hold_points)}")
    print(f"Inspections: {len(qa_qc.inspections)}")
    print(f"Handover docs: {len(qa_qc.handover_docs_required)}")
    
    # Test quality control plan
    plan = mapper.generate_quality_control_plan(sample_space)
    print(f"\\nQuality Control Plan:")
    print(plan[:500] + "..." if len(plan) > 500 else plan)
    
    # Test compliance validation
    compliance = mapper.validate_quality_compliance(sample_space)
    print(f"\\nCompliance Status:")
    print(f"Compliant: {compliance['compliant']}")
    print(f"Issues: {compliance['issues']}")
    print(f"Warnings: {compliance['warnings']}")
