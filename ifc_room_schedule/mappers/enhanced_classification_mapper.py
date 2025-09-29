"""
Enhanced Classification Mapper

Maps IFC Space data to enhanced classification section using NS 3940 standards.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from ..data.space_model import SpaceData
from ..parsers.ns8360_name_parser import NS8360NameParser
from .ns3940_classifier import NS3940Classifier
from ..validation.ns8360_validator import NS8360Validator
from ..validation.ns3940_validator import NS3940Validator


@dataclass
class EnhancedClassificationData:
    """Enhanced classification data for room schedule."""
    
    # NS 3940 classification
    ns3940: Optional[Dict[str, Any]] = None
    
    # NS 8360 compliance
    ns8360_compliance: Optional[Dict[str, Any]] = None
    
    # TFM classification (if available)
    tfm: Optional[str] = None
    
    # Custom codes
    custom_codes: List[str] = None
    
    # Validation results
    validation_status: Optional[Dict[str, Any]] = None
    
    # Confidence and source
    overall_confidence: float = 0.0
    classification_source: str = "unknown"
    
    def __post_init__(self):
        if self.custom_codes is None:
            self.custom_codes = []


class EnhancedClassificationMapper:
    """Maps IFC Space data to enhanced classification section."""
    
    def __init__(self):
        """Initialize EnhancedClassificationMapper."""
        self.name_parser = NS8360NameParser()
        self.classifier = NS3940Classifier()
        self.ns8360_validator = NS8360Validator()
        self.ns3940_validator = NS3940Validator()
    
    def map_classification(self, space: SpaceData) -> EnhancedClassificationData:
        """
        Map space to enhanced classification with NS 3940 structured data.
        
        Args:
            space: SpaceData to map
            
        Returns:
            EnhancedClassificationData with comprehensive classification
        """
        # Parse NS 8360 compliant name
        parsed_name = self.name_parser.parse(space.name)
        
        # Get NS 3940 classification
        classification = None
        source = "unknown"
        confidence = 0.0
        
        if parsed_name.is_valid and parsed_name.function_code:
            # Direct classification from parsed function code
            classification = self.classifier.classify_from_code(parsed_name.function_code)
            source = "parsed_from_name"
            confidence = parsed_name.confidence
        else:
            # Fallback: infer from name
            classification = self.classifier.classify_from_name(space.name)
            source = "inferred_from_name"
            confidence = classification.confidence if classification else 0.0
        
        # Build NS 3940 data
        ns3940_data = None
        if classification:
            ns3940_data = {
                "code": classification.function_code,
                "label": classification.label,
                "category": classification.category,
                "occupancy_type": classification.occupancy_type,
                "is_wet_room": classification.is_wet_room,
                "typical_equipment": classification.typical_equipment,
                "performance_defaults": classification.performance_defaults,
                "accessibility_requirements": classification.accessibility_requirements,
                "confidence": classification.confidence,
                "source": source
            }
        
        # Build NS 8360 compliance data
        ns8360_compliance = self._build_ns8360_compliance(parsed_name)
        
        # Validate classification consistency
        validation_status = self._validate_classification_consistency(space, parsed_name, classification)
        
        # Determine overall confidence
        overall_confidence = self._calculate_overall_confidence(parsed_name, classification, validation_status)
        
        # Extract custom codes if any
        custom_codes = self._extract_custom_codes(space)
        
        return EnhancedClassificationData(
            ns3940=ns3940_data,
            ns8360_compliance=ns8360_compliance,
            tfm=self._extract_tfm_classification(space),
            custom_codes=custom_codes,
            validation_status=validation_status,
            overall_confidence=overall_confidence,
            classification_source=source
        )
    
    def validate_classification_consistency(self, space: SpaceData, 
                                          classification_data: EnhancedClassificationData) -> Dict[str, Any]:
        """
        Validate classification consistency between name and code.
        
        Args:
            space: SpaceData to validate
            classification_data: Classification data to validate
            
        Returns:
            Validation results
        """
        validation_results = {
            "is_consistent": True,
            "warnings": [],
            "errors": [],
            "recommendations": []
        }
        
        # Validate NS 8360 compliance
        if classification_data.ns8360_compliance:
            ns8360_valid = classification_data.ns8360_compliance.get("name_pattern_valid", False)
            if not ns8360_valid:
                validation_results["warnings"].append("Space name not NS 8360 compliant")
                validation_results["recommendations"].append("Use NS 8360 naming convention")
        
        # Validate NS 3940 classification
        if classification_data.ns3940:
            function_code = classification_data.ns3940.get("code")
            if function_code:
                # Validate against NS 3940 standards
                ns3940_validation = self.ns3940_validator.validate_classification(space.name, function_code)
                
                if not ns3940_validation.is_valid:
                    validation_results["errors"].extend(ns3940_validation.errors)
                    validation_results["is_consistent"] = False
                
                validation_results["warnings"].extend(ns3940_validation.warnings)
                validation_results["recommendations"].extend(ns3940_validation.recommendations)
        
        # Check confidence levels
        if classification_data.overall_confidence < 0.5:
            validation_results["warnings"].append("Low classification confidence")
            validation_results["recommendations"].append("Review and improve space naming")
        
        return validation_results
    
    def get_classification_summary(self, classification_data: EnhancedClassificationData) -> Dict[str, Any]:
        """
        Get summary of classification data.
        
        Args:
            classification_data: Classification data to summarize
            
        Returns:
            Summary information
        """
        summary = {
            "has_ns3940": classification_data.ns3940 is not None,
            "has_ns8360": classification_data.ns8360_compliance is not None,
            "is_ns8360_compliant": False,
            "function_code": None,
            "room_type": None,
            "is_wet_room": False,
            "confidence_level": "low",
            "validation_status": "unknown"
        }
        
        # NS 3940 information
        if classification_data.ns3940:
            summary["function_code"] = classification_data.ns3940.get("code")
            summary["room_type"] = classification_data.ns3940.get("label")
            summary["is_wet_room"] = classification_data.ns3940.get("is_wet_room", False)
        
        # NS 8360 compliance
        if classification_data.ns8360_compliance:
            summary["is_ns8360_compliant"] = classification_data.ns8360_compliance.get("name_pattern_valid", False)
        
        # Confidence level
        confidence = classification_data.overall_confidence
        if confidence >= 0.8:
            summary["confidence_level"] = "high"
        elif confidence >= 0.6:
            summary["confidence_level"] = "medium"
        else:
            summary["confidence_level"] = "low"
        
        # Validation status
        if classification_data.validation_status:
            if classification_data.validation_status.get("is_consistent", True):
                summary["validation_status"] = "consistent"
            else:
                summary["validation_status"] = "inconsistent"
        
        return summary
    
    def _build_ns8360_compliance(self, parsed_name) -> Dict[str, Any]:
        """Build NS 8360 compliance data."""
        return {
            "name_pattern_valid": parsed_name.is_valid,
            "confidence": parsed_name.confidence,
            "parsed_components": {
                "prefix": parsed_name.prefix,
                "storey": parsed_name.storey,
                "function_code": parsed_name.function_code,
                "sequence": parsed_name.sequence
            } if parsed_name.is_valid else None,
            "zone": parsed_name.zone if parsed_name.zone else None,
            "raw_name": parsed_name.raw_name
        }
    
    def _validate_classification_consistency(self, space: SpaceData, parsed_name, classification) -> Dict[str, Any]:
        """Validate consistency between parsed name and classification."""
        validation_results = {
            "is_consistent": True,
            "warnings": [],
            "errors": [],
            "recommendations": []
        }
        
        # Check if parsed function code matches classification
        if parsed_name.is_valid and parsed_name.function_code and classification:
            if parsed_name.function_code != classification.function_code:
                validation_results["warnings"].append(
                    f"Parsed function code '{parsed_name.function_code}' doesn't match classification '{classification.function_code}'"
                )
                validation_results["recommendations"].append("Ensure function code consistency")
        
        # Check confidence levels
        if parsed_name.confidence < 0.5:
            validation_results["warnings"].append("Low NS 8360 parsing confidence")
            validation_results["recommendations"].append("Improve space naming for better parsing")
        
        if classification and classification.confidence < 0.5:
            validation_results["warnings"].append("Low NS 3940 classification confidence")
            validation_results["recommendations"].append("Review room type classification")
        
        return validation_results
    
    def _calculate_overall_confidence(self, parsed_name, classification, validation_status) -> float:
        """Calculate overall confidence score."""
        confidence_scores = []
        
        # NS 8360 parsing confidence
        if parsed_name.is_valid:
            confidence_scores.append(parsed_name.confidence)
        else:
            confidence_scores.append(parsed_name.confidence * 0.5)  # Reduce for invalid parsing
        
        # NS 3940 classification confidence
        if classification:
            confidence_scores.append(classification.confidence)
        else:
            confidence_scores.append(0.0)
        
        # Validation consistency
        if validation_status.get("is_consistent", True):
            confidence_scores.append(1.0)
        else:
            confidence_scores.append(0.5)
        
        # Calculate weighted average
        if confidence_scores:
            return sum(confidence_scores) / len(confidence_scores)
        else:
            return 0.0
    
    def _extract_custom_codes(self, space: SpaceData) -> List[str]:
        """Extract custom classification codes from space data."""
        custom_codes = []
        
        # Check for custom properties in space data
        if hasattr(space, 'properties') and space.properties:
            # Look for common custom code properties
            custom_properties = [
                'CustomCode', 'ClassificationCode', 'RoomCode',
                'CustomClassification', 'AdditionalCode'
            ]
            
            for prop in custom_properties:
                if prop in space.properties:
                    custom_codes.append(space.properties[prop])
        
        # Check for custom codes in description
        if space.description:
            # Look for patterns like "Code: XXX" or "Classification: XXX"
            import re
            code_patterns = [
                r'Code:\s*([A-Z0-9]+)',
                r'Classification:\s*([A-Z0-9]+)',
                r'Custom:\s*([A-Z0-9]+)'
            ]
            
            for pattern in code_patterns:
                matches = re.findall(pattern, space.description, re.IGNORECASE)
                custom_codes.extend(matches)
        
        return custom_codes
    
    def _extract_tfm_classification(self, space: SpaceData) -> Optional[str]:
        """Extract TFM (Teknisk Funksjonell Målsetting) classification."""
        # TFM classification is typically found in IFC properties
        if hasattr(space, 'properties') and space.properties:
            tfm_properties = [
                'TFM', 'TFMCode', 'TFMClassification',
                'TekniskFunksjonellMålsetting'
            ]
            
            for prop in tfm_properties:
                if prop in space.properties:
                    return space.properties[prop]
        
        # Check in description
        if space.description:
            import re
            tfm_pattern = r'TFM[:\s]*([A-Z0-9]+)'
            match = re.search(tfm_pattern, space.description, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None


# Example usage and testing
if __name__ == "__main__":
    from ..data.space_model import SpaceData
    
    # Create test space data
    test_spaces = [
        SpaceData(
            guid="GUID-STUE-001",
            name="SPC-02-A101-111-003",
            long_name="Stue | 02/A101 | NS3940:111",
            description="Oppholdsrom i A101 - TFM: L001",
            object_type="IfcSpace",
            zone_category="Residential",
            number="003",
            elevation=6.0,
            quantities={"NetFloorArea": 24.0, "GrossFloorArea": 25.5},
            properties={"CustomCode": "CUSTOM-001", "TFM": "L001"}
        ),
        SpaceData(
            guid="GUID-BAD-001",
            name="Bad 2. etasje",
            description="Bad med dusj - Code: BATH-001",
            object_type="IfcSpace",
            zone_category="Residential",
            number="001",
            elevation=6.0,
            quantities={"NetFloorArea": 4.8, "GrossFloorArea": 5.2}
        ),
        SpaceData(
            guid="GUID-UNKNOWN-001",
            name="Unknown Room",
            description="Room without clear classification",
            object_type="IfcSpace",
            zone_category="Residential",
            number="001",
            elevation=6.0,
            quantities={}
        )
    ]
    
    mapper = EnhancedClassificationMapper()
    
    print("Enhanced Classification Mapper Test Results:")
    print("=" * 70)
    
    for i, space in enumerate(test_spaces, 1):
        print(f"\n--- Test Space {i}: {space.name} ---")
        
        # Map classification
        classification = mapper.map_classification(space)
        
        print(f"Classification Source: {classification.classification_source}")
        print(f"Overall Confidence: {classification.overall_confidence:.2f}")
        
        # NS 3940 data
        if classification.ns3940:
            print(f"NS 3940 Code: {classification.ns3940['code']}")
            print(f"Room Type: {classification.ns3940['label']}")
            print(f"Category: {classification.ns3940['category']}")
            print(f"Wet Room: {classification.ns3940['is_wet_room']}")
            print(f"Confidence: {classification.ns3940['confidence']:.2f}")
        
        # NS 8360 compliance
        if classification.ns8360_compliance:
            print(f"NS 8360 Compliant: {classification.ns8360_compliance['name_pattern_valid']}")
            print(f"Parsing Confidence: {classification.ns8360_compliance['confidence']:.2f}")
            if classification.ns8360_compliance['parsed_components']:
                print(f"Parsed Components: {classification.ns8360_compliance['parsed_components']}")
        
        # TFM classification
        if classification.tfm:
            print(f"TFM Classification: {classification.tfm}")
        
        # Custom codes
        if classification.custom_codes:
            print(f"Custom Codes: {', '.join(classification.custom_codes)}")
        
        # Validation status
        if classification.validation_status:
            print(f"Consistent: {classification.validation_status['is_consistent']}")
            if classification.validation_status['warnings']:
                print(f"Warnings: {', '.join(classification.validation_status['warnings'])}")
            if classification.validation_status['recommendations']:
                print(f"Recommendations: {', '.join(classification.validation_status['recommendations'])}")
        
        # Test validation
        validation = mapper.validate_classification_consistency(space, classification)
        print(f"Validation Consistent: {validation['is_consistent']}")
        if validation['warnings']:
            print(f"Validation Warnings: {', '.join(validation['warnings'])}")
        
        # Test summary
        summary = mapper.get_classification_summary(classification)
        print(f"Summary - NS3940: {summary['has_ns3940']}, NS8360: {summary['is_ns8360_compliant']}, Confidence: {summary['confidence_level']}")
