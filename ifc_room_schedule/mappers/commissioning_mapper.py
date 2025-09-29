"""
Commissioning Mapper

Maps IFC data to commissioning section including testing, 
balancing, and handover procedures.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from ..data.space_model import SpaceData
from ..parsers.ns8360_name_parser import NS8360NameParser
from ..mappers.ns3940_classifier import NS3940Classifier


class TestType(Enum):
    """Types of commissioning tests."""
    FUNCTIONAL = "functional"
    PERFORMANCE = "performance"
    SAFETY = "safety"
    ENVIRONMENTAL = "environmental"
    INTEGRATION = "integration"


class TestMethod(Enum):
    """Methods for conducting tests."""
    VISUAL_INSPECTION = "visual_inspection"
    MEASUREMENT = "measurement"
    FUNCTIONAL_TEST = "functional_test"
    LOAD_TEST = "load_test"
    PRESSURE_TEST = "pressure_test"
    LEAK_TEST = "leak_test"
    ELECTRICAL_TEST = "electrical_test"
    ACOUSTIC_TEST = "acoustic_test"
    THERMAL_TEST = "thermal_test"


class BalancingType(Enum):
    """Types of balancing required."""
    VENTILATION = "ventilation"
    HEATING = "heating"
    COOLING = "cooling"
    WATER = "water"
    ELECTRICAL = "electrical"


@dataclass
class Test:
    """Commissioning test record."""
    
    name: str
    test_type: TestType
    method: TestMethod
    criteria: str
    witnessed_by: Optional[str] = None
    scheduled_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None
    status: str = "pending"  # pending, in_progress, completed, failed
    results: Dict[str, Any] = None
    notes: Optional[str] = None
    photos: List[str] = None
    certificates: List[str] = None
    
    def __post_init__(self):
        if self.results is None:
            self.results = {}
        if self.photos is None:
            self.photos = []
        if self.certificates is None:
            self.certificates = []


@dataclass
class Balancing:
    """System balancing record."""
    
    system_type: BalancingType
    required: bool
    description: str
    criteria: str
    responsible: Optional[str] = None
    scheduled_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None
    status: str = "pending"  # pending, in_progress, completed, failed
    results: Dict[str, Any] = None
    notes: Optional[str] = None
    certificates: List[str] = None
    
    def __post_init__(self):
        if self.results is None:
            self.results = {}
        if self.certificates is None:
            self.certificates = []


@dataclass
class CommissioningData:
    """Complete commissioning data for a space."""
    
    tests: List[Test]
    balancing: List[Balancing]
    handover_requirements: List[str]
    commissioning_plan: Optional[str] = None
    last_updated: datetime = None
    
    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.now()


class CommissioningMapper:
    """Maps IFC data to commissioning section."""
    
    def __init__(self):
        """Initialize the commissioning mapper."""
        self.name_parser = NS8360NameParser()
        self.classifier = NS3940Classifier()
    
    def extract_commissioning(self, space: SpaceData) -> CommissioningData:
        """
        Extract commissioning from space data.
        
        Args:
            space: SpaceData to extract commissioning from
            
        Returns:
            CommissioningData with extracted commissioning information
        """
        # Get room type for default requirements
        room_type = self._get_room_type(space)
        
        # Extract tests
        tests = self._extract_tests(space, room_type)
        
        # Extract balancing
        balancing = self._extract_balancing(space, room_type)
        
        # Extract handover requirements
        handover_requirements = self._extract_handover_requirements(space, room_type)
        
        return CommissioningData(
            tests=tests,
            balancing=balancing,
            handover_requirements=handover_requirements
        )
    
    def generate_commissioning_plan(self, space: SpaceData) -> str:
        """
        Generate a commissioning plan for the space.
        
        Args:
            space: SpaceData to generate plan for
            
        Returns:
            Commissioning plan as string
        """
        room_type = self._get_room_type(space)
        commissioning_data = self.extract_commissioning(space)
        
        plan = f"Commissioning Plan for {space.name}\n"
        plan += f"Room Type: {room_type}\n"
        plan += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
        
        plan += "TESTS:\n"
        for i, test in enumerate(commissioning_data.tests, 1):
            plan += f"{i}. {test.name} ({test.test_type.value})\n"
            plan += f"   Method: {test.method.value}\n"
            plan += f"   Criteria: {test.criteria}\n"
            if test.witnessed_by:
                plan += f"   Witnessed by: {test.witnessed_by}\n"
            plan += f"   Status: {test.status}\n"
            plan += "\n"
        
        plan += "BALANCING:\n"
        for i, balance in enumerate(commissioning_data.balancing, 1):
            plan += f"{i}. {balance.system_type.value} - {balance.description}\n"
            plan += f"   Required: {balance.required}\n"
            plan += f"   Criteria: {balance.criteria}\n"
            if balance.responsible:
                plan += f"   Responsible: {balance.responsible}\n"
            plan += f"   Status: {balance.status}\n"
            plan += "\n"
        
        plan += "HANDOVER REQUIREMENTS:\n"
        for req in commissioning_data.handover_requirements:
            plan += f"- {req}\n"
        
        return plan
    
    def validate_commissioning_compliance(self, space: SpaceData) -> Dict[str, Any]:
        """
        Validate commissioning compliance for space.
        
        Args:
            space: SpaceData to validate
            
        Returns:
            Dictionary with compliance status and issues
        """
        commissioning_data = self.extract_commissioning(space)
        
        compliance = {
            "compliant": True,
            "issues": [],
            "warnings": [],
            "tests_required": len(commissioning_data.tests),
            "balancing_required": len([b for b in commissioning_data.balancing if b.required]),
            "handover_requirements": len(commissioning_data.handover_requirements)
        }
        
        # Check for missing test criteria
        missing_criteria = [t for t in commissioning_data.tests if not t.criteria]
        if missing_criteria:
            compliance["issues"].append(f"{len(missing_criteria)} tests missing criteria")
            compliance["compliant"] = False
        
        # Check for missing responsible parties
        missing_responsible = [t for t in commissioning_data.tests if not t.witnessed_by]
        if missing_responsible:
            compliance["warnings"].append(f"{len(missing_responsible)} tests missing responsible party")
        
        # Check for required balancing not completed
        required_balancing = [b for b in commissioning_data.balancing if b.required and b.status != "completed"]
        if required_balancing:
            compliance["warnings"].append(f"{len(required_balancing)} required balancing not completed")
        
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
    
    def _extract_tests(self, space: SpaceData, room_type: str) -> List[Test]:
        """Extract tests for space."""
        # Look for test properties in space
        tests = []
        
        # Check if space has test properties
        if space.quantities:
            # Could extract from property sets
            pass
        
        # Apply defaults based on room type
        defaults = self._get_room_type_defaults(room_type)
        tests_data = defaults.get("tests", [])
        
        for test_data in tests_data:
            tests.append(Test(
                name=test_data["name"],
                test_type=TestType(test_data["test_type"]),
                method=TestMethod(test_data["method"]),
                criteria=test_data["criteria"],
                witnessed_by=test_data.get("witnessed_by"),
                scheduled_date=test_data.get("scheduled_date"),
                completed_date=test_data.get("completed_date"),
                status=test_data.get("status", "pending"),
                results=test_data.get("results", {}),
                notes=test_data.get("notes"),
                photos=test_data.get("photos", []),
                certificates=test_data.get("certificates", [])
            ))
        
        return tests
    
    def _extract_balancing(self, space: SpaceData, room_type: str) -> List[Balancing]:
        """Extract balancing for space."""
        # Look for balancing properties in space
        balancing = []
        
        # Check if space has balancing properties
        if space.quantities:
            # Could extract from property sets
            pass
        
        # Apply defaults based on room type
        defaults = self._get_room_type_defaults(room_type)
        balancing_data = defaults.get("balancing", [])
        
        for balance_data in balancing_data:
            balancing.append(Balancing(
                system_type=BalancingType(balance_data["system_type"]),
                required=balance_data["required"],
                description=balance_data["description"],
                criteria=balance_data["criteria"],
                responsible=balance_data.get("responsible"),
                scheduled_date=balance_data.get("scheduled_date"),
                completed_date=balance_data.get("completed_date"),
                status=balance_data.get("status", "pending"),
                results=balance_data.get("results", {}),
                notes=balance_data.get("notes"),
                certificates=balance_data.get("certificates", [])
            ))
        
        return balancing
    
    def _extract_handover_requirements(self, space: SpaceData, room_type: str) -> List[str]:
        """Extract handover requirements for space."""
        # Look for handover requirement properties in space
        handover_requirements = []
        
        # Check if space has handover requirement properties
        if space.quantities:
            # Could extract from property sets
            pass
        
        # Apply defaults based on room type
        defaults = self._get_room_type_defaults(room_type)
        handover_requirements = defaults.get("handover_requirements", [])
        
        return handover_requirements
    
    def _get_room_type_defaults(self, room_type: str) -> Dict[str, Any]:
        """Get default commissioning requirements for room type."""
        defaults = {
            "111": {  # Oppholdsrom
                "tests": [
                    {
                        "name": "Lighting functional test",
                        "test_type": "functional",
                        "method": "functional_test",
                        "criteria": "All lighting fixtures operational",
                        "witnessed_by": "Electrical engineer",
                        "status": "pending"
                    },
                    {
                        "name": "Power outlet test",
                        "test_type": "functional",
                        "method": "electrical_test",
                        "criteria": "All outlets tested and functional",
                        "witnessed_by": "Electrical engineer",
                        "status": "pending"
                    },
                    {
                        "name": "Fire safety test",
                        "test_type": "safety",
                        "method": "functional_test",
                        "criteria": "Fire detection and alarm systems operational",
                        "witnessed_by": "Fire safety engineer",
                        "status": "pending"
                    }
                ],
                "balancing": [
                    {
                        "system_type": "ventilation",
                        "required": False,
                        "description": "Natural ventilation",
                        "criteria": "Adequate air circulation",
                        "responsible": "HVAC engineer",
                        "status": "pending"
                    },
                    {
                        "system_type": "heating",
                        "required": True,
                        "description": "Heating system",
                        "criteria": "Temperature control within ±1°C",
                        "responsible": "HVAC engineer",
                        "status": "pending"
                    }
                ],
                "handover_requirements": [
                    "As-built drawings",
                    "Test certificates",
                    "Warranty documentation",
                    "Operation and maintenance manual"
                ]
            },
            "130": {  # Våtrom
                "tests": [
                    {
                        "name": "Waterproofing test",
                        "test_type": "performance",
                        "method": "leak_test",
                        "criteria": "No water penetration for 24 hours",
                        "witnessed_by": "Waterproofing specialist",
                        "status": "pending"
                    },
                    {
                        "name": "Drainage test",
                        "test_type": "functional",
                        "method": "functional_test",
                        "criteria": "All drains functional and clear",
                        "witnessed_by": "Plumbing engineer",
                        "status": "pending"
                    },
                    {
                        "name": "Ventilation test",
                        "test_type": "performance",
                        "method": "measurement",
                        "criteria": "Air changes per hour as specified",
                        "witnessed_by": "HVAC engineer",
                        "status": "pending"
                    },
                    {
                        "name": "Electrical safety test",
                        "test_type": "safety",
                        "method": "electrical_test",
                        "criteria": "GFCI protection functional",
                        "witnessed_by": "Electrical engineer",
                        "status": "pending"
                    }
                ],
                "balancing": [
                    {
                        "system_type": "ventilation",
                        "required": True,
                        "description": "Mechanical ventilation",
                        "criteria": "Air changes per hour as specified",
                        "responsible": "HVAC engineer",
                        "status": "pending"
                    },
                    {
                        "system_type": "heating",
                        "required": True,
                        "description": "Heating system",
                        "criteria": "Temperature control within ±1°C",
                        "responsible": "HVAC engineer",
                        "status": "pending"
                    }
                ],
                "handover_requirements": [
                    "As-built drawings",
                    "Test certificates",
                    "Waterproofing certificate",
                    "Warranty documentation",
                    "Operation and maintenance manual"
                ]
            },
            "131": {  # WC
                "tests": [
                    {
                        "name": "Waterproofing test",
                        "test_type": "performance",
                        "method": "leak_test",
                        "criteria": "No water penetration for 24 hours",
                        "witnessed_by": "Waterproofing specialist",
                        "status": "pending"
                    },
                    {
                        "name": "Drainage test",
                        "test_type": "functional",
                        "method": "functional_test",
                        "criteria": "All drains functional and clear",
                        "witnessed_by": "Plumbing engineer",
                        "status": "pending"
                    },
                    {
                        "name": "Ventilation test",
                        "test_type": "performance",
                        "method": "measurement",
                        "criteria": "Air changes per hour as specified",
                        "witnessed_by": "HVAC engineer",
                        "status": "pending"
                    }
                ],
                "balancing": [
                    {
                        "system_type": "ventilation",
                        "required": True,
                        "description": "Mechanical ventilation",
                        "criteria": "Air changes per hour as specified",
                        "responsible": "HVAC engineer",
                        "status": "pending"
                    },
                    {
                        "system_type": "heating",
                        "required": True,
                        "description": "Heating system",
                        "criteria": "Temperature control within ±1°C",
                        "responsible": "HVAC engineer",
                        "status": "pending"
                    }
                ],
                "handover_requirements": [
                    "As-built drawings",
                    "Test certificates",
                    "Waterproofing certificate",
                    "Warranty documentation",
                    "Operation and maintenance manual"
                ]
            },
            "132": {  # Baderom
                "tests": [
                    {
                        "name": "Waterproofing test",
                        "test_type": "performance",
                        "method": "leak_test",
                        "criteria": "No water penetration for 24 hours",
                        "witnessed_by": "Waterproofing specialist",
                        "status": "pending"
                    },
                    {
                        "name": "Drainage test",
                        "test_type": "functional",
                        "method": "functional_test",
                        "criteria": "All drains functional and clear",
                        "witnessed_by": "Plumbing engineer",
                        "status": "pending"
                    },
                    {
                        "name": "Ventilation test",
                        "test_type": "performance",
                        "method": "measurement",
                        "criteria": "Air changes per hour as specified",
                        "witnessed_by": "HVAC engineer",
                        "status": "pending"
                    },
                    {
                        "name": "Electrical safety test",
                        "test_type": "safety",
                        "method": "electrical_test",
                        "criteria": "GFCI protection functional",
                        "witnessed_by": "Electrical engineer",
                        "status": "pending"
                    }
                ],
                "balancing": [
                    {
                        "system_type": "ventilation",
                        "required": True,
                        "description": "Mechanical ventilation",
                        "criteria": "Air changes per hour as specified",
                        "responsible": "HVAC engineer",
                        "status": "pending"
                    },
                    {
                        "system_type": "heating",
                        "required": True,
                        "description": "Heating system",
                        "criteria": "Temperature control within ±1°C",
                        "responsible": "HVAC engineer",
                        "status": "pending"
                    }
                ],
                "handover_requirements": [
                    "As-built drawings",
                    "Test certificates",
                    "Waterproofing certificate",
                    "Warranty documentation",
                    "Operation and maintenance manual"
                ]
            },
            "140": {  # Kjøkken
                "tests": [
                    {
                        "name": "Plumbing test",
                        "test_type": "functional",
                        "method": "pressure_test",
                        "criteria": "Water pressure and flow as specified",
                        "witnessed_by": "Plumbing engineer",
                        "status": "pending"
                    },
                    {
                        "name": "Drainage test",
                        "test_type": "functional",
                        "method": "functional_test",
                        "criteria": "All drains functional and clear",
                        "witnessed_by": "Plumbing engineer",
                        "status": "pending"
                    },
                    {
                        "name": "Ventilation test",
                        "test_type": "performance",
                        "method": "measurement",
                        "criteria": "Air changes per hour as specified",
                        "witnessed_by": "HVAC engineer",
                        "status": "pending"
                    },
                    {
                        "name": "Electrical test",
                        "test_type": "functional",
                        "method": "electrical_test",
                        "criteria": "All circuits and outlets functional",
                        "witnessed_by": "Electrical engineer",
                        "status": "pending"
                    },
                    {
                        "name": "Appliance test",
                        "test_type": "functional",
                        "method": "functional_test",
                        "criteria": "All appliances operational",
                        "witnessed_by": "Appliance specialist",
                        "status": "pending"
                    }
                ],
                "balancing": [
                    {
                        "system_type": "ventilation",
                        "required": True,
                        "description": "Kitchen ventilation",
                        "criteria": "Air changes per hour as specified",
                        "responsible": "HVAC engineer",
                        "status": "pending"
                    },
                    {
                        "system_type": "heating",
                        "required": True,
                        "description": "Heating system",
                        "criteria": "Temperature control within ±1°C",
                        "responsible": "HVAC engineer",
                        "status": "pending"
                    }
                ],
                "handover_requirements": [
                    "As-built drawings",
                    "Test certificates",
                    "Appliance warranties",
                    "Warranty documentation",
                    "Operation and maintenance manual"
                ]
            }
        }
        
        return defaults.get(room_type, defaults["111"])  # Default to oppholdsrom


# Example usage and testing
if __name__ == "__main__":
    mapper = CommissioningMapper()
    
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
    
    print("Commissioning Mapper Test:")
    print("=" * 50)
    
    # Test commissioning extraction
    commissioning = mapper.extract_commissioning(sample_space)
    print(f"Tests required: {len(commissioning.tests)}")
    print(f"Balancing required: {len([b for b in commissioning.balancing if b.required])}")
    print(f"Handover requirements: {len(commissioning.handover_requirements)}")
    
    # Test commissioning plan
    plan = mapper.generate_commissioning_plan(sample_space)
    print(f"\\nCommissioning Plan:")
    print(plan[:500] + "..." if len(plan) > 500 else plan)
    
    # Test compliance validation
    compliance = mapper.validate_commissioning_compliance(sample_space)
    print(f"\\nCompliance Status:")
    print(f"Compliant: {compliance['compliant']}")
    print(f"Issues: {compliance['issues']}")
    print(f"Warnings: {compliance['warnings']}")
