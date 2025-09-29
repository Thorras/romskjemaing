"""
NS 3940 Validator

Validates room classifications and performance requirements against NS 3940 standards.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from ..mappers.ns3940_classifier import NS3940Classifier
from ..defaults.ns3940_defaults import NS3940DefaultsDatabase


@dataclass
class ValidationResult:
    """Result of NS 3940 validation."""
    
    is_valid: bool
    confidence: float
    errors: List[str]
    warnings: List[str]
    recommendations: List[str]
    function_code: Optional[str] = None
    room_type: Optional[str] = None


@dataclass
class WetRoomValidation:
    """Wet room specific validation results."""
    
    is_wet_room: bool
    drainage_required: bool
    ventilation_adequate: bool
    accessibility_compliant: bool
    issues: List[str]
    recommendations: List[str]


class NS3940Validator:
    """Validates room classifications and requirements against NS 3940 standards."""
    
    def __init__(self):
        """Initialize NS3940Validator."""
        self.classifier = NS3940Classifier()
        self.defaults_db = NS3940DefaultsDatabase()
    
    def validate_classification(self, space_name: str, function_code: Optional[str] = None) -> ValidationResult:
        """
        Validate room classification against NS 3940 standards.
        
        Args:
            space_name: Space name to validate
            function_code: Optional function code to validate
            
        Returns:
            ValidationResult with validation details
        """
        # Determine function code if not provided
        if not function_code:
            function_code = self.classifier.infer_code_from_name(space_name)
        
        # Initialize result
        result = ValidationResult(
            is_valid=True,
            confidence=1.0,
            errors=[],
            warnings=[],
            recommendations=[],
            function_code=function_code
        )
        
        # Validate function code exists
        if not function_code:
            result.is_valid = False
            result.errors.append("No function code could be determined")
            result.recommendations.append("Use NS 3940 compliant function code")
            return result
        
        # Check if function code is supported
        if function_code not in self.defaults_db.get_all_function_codes():
            result.is_valid = False
            result.errors.append(f"Function code '{function_code}' not supported")
            result.recommendations.append("Use valid NS 3940 function code")
            return result
        
        # Get classification data
        classification = self.classifier.classify_from_code(function_code)
        if classification:
            result.room_type = classification.label
            result.confidence = classification.confidence
        
        # Validate classification consistency
        self._validate_classification_consistency(space_name, function_code, result)
        
        return result
    
    def validate_wet_room_consistency(self, function_code: str, 
                                    performance_data: Dict[str, Any]) -> WetRoomValidation:
        """
        Validate wet room consistency per NS 3940.
        
        Args:
            function_code: NS 3940 function code
            performance_data: Performance requirements data
            
        Returns:
            WetRoomValidation with wet room specific validation
        """
        is_wet_room = self.defaults_db.is_wet_room(function_code)
        
        validation = WetRoomValidation(
            is_wet_room=is_wet_room,
            drainage_required=False,
            ventilation_adequate=False,
            accessibility_compliant=False,
            issues=[],
            recommendations=[]
        )
        
        if not is_wet_room:
            validation.drainage_required = True
            validation.ventilation_adequate = True
            validation.accessibility_compliant = True
            return validation
        
        # Validate drainage requirements
        water_sanitary = performance_data.get("water_sanitary", {})
        validation.drainage_required = water_sanitary.get("drainage_required", False)
        
        if not validation.drainage_required:
            validation.issues.append("Wet room requires drainage system")
            validation.recommendations.append("Add drainage_required=true for wet rooms")
        
        # Validate ventilation requirements
        ventilation = performance_data.get("ventilation", {})
        extract_airflow = ventilation.get("airflow_extract_m3h", 0)
        
        # Get minimum requirements from defaults
        defaults = self.defaults_db.get_defaults(function_code)
        min_extract = 0
        if defaults and defaults.ventilation:
            min_extract = defaults.ventilation.airflow_extract_m3h or 0
        
        validation.ventilation_adequate = extract_airflow >= min_extract
        
        if not validation.ventilation_adequate:
            validation.issues.append(f"Insufficient extract ventilation: {extract_airflow} < {min_extract} m³/h")
            validation.recommendations.append(f"Increase extract ventilation to minimum {min_extract} m³/h")
        
        # Validate accessibility requirements
        accessibility = performance_data.get("accessibility", {})
        validation.accessibility_compliant = (
            accessibility.get("universal_design", False) and
            accessibility.get("clear_width_door_mm", 0) >= 850 and
            accessibility.get("turning_radius_m", 0) >= 1.5
        )
        
        if not validation.accessibility_compliant:
            validation.issues.append("Wet room accessibility requirements not met")
            validation.recommendations.append("Ensure universal design compliance for wet rooms")
        
        return validation
    
    def validate_performance_requirements(self, function_code: str, 
                                        performance_data: Dict[str, Any]) -> ValidationResult:
        """
        Validate performance requirements against NS 3940 standards.
        
        Args:
            function_code: NS 3940 function code
            performance_data: Performance requirements to validate
            
        Returns:
            ValidationResult with validation details
        """
        # Get reference defaults
        defaults = self.defaults_db.get_defaults(function_code)
        if not defaults:
            return ValidationResult(
                is_valid=False,
                confidence=0.0,
                errors=[f"No defaults available for function code '{function_code}'"],
                warnings=[],
                recommendations=["Use valid NS 3940 function code"]
            )
        
        result = ValidationResult(
            is_valid=True,
            confidence=1.0,
            errors=[],
            warnings=[],
            recommendations=[],
            function_code=function_code
        )
        
        # Validate lighting requirements
        self._validate_lighting_requirements(defaults.lighting, performance_data.get("lighting", {}), result)
        
        # Validate acoustics requirements
        self._validate_acoustics_requirements(defaults.acoustics, performance_data.get("acoustics", {}), result)
        
        # Validate ventilation requirements
        self._validate_ventilation_requirements(defaults.ventilation, performance_data.get("ventilation", {}), result)
        
        # Validate thermal requirements
        self._validate_thermal_requirements(defaults.thermal, performance_data.get("thermal", {}), result)
        
        # Validate accessibility requirements
        if defaults.accessibility:
            self._validate_accessibility_requirements(defaults.accessibility, performance_data.get("accessibility", {}), result)
        
        # Validate wet room requirements
        if self.defaults_db.is_wet_room(function_code):
            wet_room_validation = self.validate_wet_room_consistency(function_code, performance_data)
            if wet_room_validation.issues:
                result.warnings.extend(wet_room_validation.issues)
            if wet_room_validation.recommendations:
                result.recommendations.extend(wet_room_validation.recommendations)
        
        return result
    
    def validate_equipment_requirements(self, function_code: str, 
                                      equipment_data: Dict[str, Any]) -> ValidationResult:
        """
        Validate equipment requirements against NS 3940 standards.
        
        Args:
            function_code: NS 3940 function code
            equipment_data: Equipment requirements to validate
            
        Returns:
            ValidationResult with validation details
        """
        defaults = self.defaults_db.get_defaults(function_code)
        if not defaults or not defaults.equipment:
            return ValidationResult(
                is_valid=True,
                confidence=1.0,
                errors=[],
                warnings=[],
                recommendations=[],
                function_code=function_code
            )
        
        result = ValidationResult(
            is_valid=True,
            confidence=1.0,
            errors=[],
            warnings=[],
            recommendations=[],
            function_code=function_code
        )
        
        # Validate electrical outlets
        required_outlets = defaults.equipment.electrical_outlets
        provided_outlets = equipment_data.get("electrical_outlets", 0)
        
        if provided_outlets < required_outlets:
            result.warnings.append(f"Insufficient electrical outlets: {provided_outlets} < {required_outlets}")
            result.recommendations.append(f"Add {required_outlets - provided_outlets} more electrical outlets")
        
        # Validate lighting points
        required_lighting = defaults.equipment.lighting_points
        provided_lighting = equipment_data.get("lighting_points", 0)
        
        if provided_lighting < required_lighting:
            result.warnings.append(f"Insufficient lighting points: {provided_lighting} < {required_lighting}")
            result.recommendations.append(f"Add {required_lighting - provided_lighting} more lighting points")
        
        # Validate switches
        required_switches = defaults.equipment.switches
        provided_switches = equipment_data.get("switches", 0)
        
        if provided_switches < required_switches:
            result.warnings.append(f"Insufficient switches: {provided_switches} < {required_switches}")
            result.recommendations.append(f"Add {required_switches - provided_switches} more switches")
        
        # Validate emergency equipment for wet rooms
        if self.defaults_db.is_wet_room(function_code):
            if defaults.equipment.emergency_equipment:
                provided_emergency = equipment_data.get("emergency_equipment", [])
                for required_item in defaults.equipment.emergency_equipment:
                    if required_item not in provided_emergency:
                        result.warnings.append(f"Missing emergency equipment: {required_item}")
                        result.recommendations.append(f"Add {required_item} for wet room safety")
        
        return result
    
    def get_compliance_report(self, validation_results: List[ValidationResult]) -> Dict[str, Any]:
        """
        Generate compliance report for multiple validation results.
        
        Args:
            validation_results: List of validation results
            
        Returns:
            Compliance report with statistics and recommendations
        """
        total_validations = len(validation_results)
        valid_count = sum(1 for result in validation_results if result.is_valid)
        high_confidence_count = sum(1 for result in validation_results if result.confidence >= 0.8)
        
        # Collect all issues
        all_errors = []
        all_warnings = []
        all_recommendations = []
        
        for result in validation_results:
            all_errors.extend(result.errors)
            all_warnings.extend(result.warnings)
            all_recommendations.extend(result.recommendations)
        
        # Count by function code
        function_code_counts = {}
        for result in validation_results:
            if result.function_code:
                function_code_counts[result.function_code] = function_code_counts.get(result.function_code, 0) + 1
        
        return {
            "total_validations": total_validations,
            "valid_count": valid_count,
            "high_confidence_count": high_confidence_count,
            "compliance_percentage": (valid_count / total_validations * 100) if total_validations > 0 else 0,
            "confidence_percentage": (high_confidence_count / total_validations * 100) if total_validations > 0 else 0,
            "total_errors": len(all_errors),
            "total_warnings": len(all_warnings),
            "function_code_distribution": function_code_counts,
            "common_errors": self._get_common_issues(all_errors),
            "common_warnings": self._get_common_issues(all_warnings),
            "recommendations": list(set(all_recommendations))
        }
    
    def _validate_classification_consistency(self, space_name: str, function_code: str, result: ValidationResult):
        """Validate consistency between space name and function code."""
        # Get classification from name
        name_classification = self.classifier.classify_from_name(space_name)
        
        if name_classification and name_classification.function_code != function_code:
            result.warnings.append(f"Function code '{function_code}' doesn't match name classification '{name_classification.function_code}'")
            result.recommendations.append("Ensure function code matches room type")
    
    def _validate_lighting_requirements(self, reference, provided, result):
        """Validate lighting requirements."""
        if not reference or not provided:
            return
        
        # Check task lux
        if "task_lux" in provided:
            if provided["task_lux"] < reference.task_lux * 0.8:
                result.warnings.append(f"Low lighting level: {provided['task_lux']} < {reference.task_lux} lux")
            elif provided["task_lux"] > reference.task_lux * 1.5:
                result.warnings.append(f"High lighting level: {provided['task_lux']} > {reference.task_lux} lux")
        
        # Check emergency lighting for wet rooms
        if reference.emergency_lighting and not provided.get("emergency_lighting", False):
            result.warnings.append("Emergency lighting required but not specified")
            result.recommendations.append("Add emergency lighting for wet rooms")
    
    def _validate_acoustics_requirements(self, reference, provided, result):
        """Validate acoustics requirements."""
        if not reference or not provided:
            return
        
        # Check NS 8175 class
        if "class_ns8175" in provided:
            reference_class = reference.class_ns8175
            provided_class = provided["class_ns8175"]
            
            # Convert class to numeric for comparison
            class_values = {"A": 4, "B": 3, "C": 2, "D": 1}
            ref_value = class_values.get(reference_class, 2)
            prov_value = class_values.get(provided_class, 2)
            
            if prov_value < ref_value:
                result.warnings.append(f"Acoustics class '{provided_class}' below requirement '{reference_class}'")
                result.recommendations.append(f"Upgrade to NS 8175 class '{reference_class}' or better")
    
    def _validate_ventilation_requirements(self, reference, provided, result):
        """Validate ventilation requirements."""
        if not reference or not provided:
            return
        
        # Check supply airflow
        if reference.airflow_supply_m3h and "airflow_supply_m3h" in provided:
            if provided["airflow_supply_m3h"] < reference.airflow_supply_m3h * 0.8:
                result.warnings.append(f"Low supply airflow: {provided['airflow_supply_m3h']} < {reference.airflow_supply_m3h} m³/h")
        
        # Check extract airflow
        if reference.airflow_extract_m3h and "airflow_extract_m3h" in provided:
            if provided["airflow_extract_m3h"] < reference.airflow_extract_m3h * 0.8:
                result.warnings.append(f"Low extract airflow: {provided['airflow_extract_m3h']} < {reference.airflow_extract_m3h} m³/h")
    
    def _validate_thermal_requirements(self, reference, provided, result):
        """Validate thermal requirements."""
        if not reference or not provided:
            return
        
        # Check heating setpoint
        if "setpoint_heating_C" in provided:
            if provided["setpoint_heating_C"] < reference.setpoint_heating_C - 2:
                result.warnings.append(f"Low heating setpoint: {provided['setpoint_heating_C']} < {reference.setpoint_heating_C}°C")
            elif provided["setpoint_heating_C"] > reference.setpoint_heating_C + 2:
                result.warnings.append(f"High heating setpoint: {provided['setpoint_heating_C']} > {reference.setpoint_heating_C}°C")
    
    def _validate_accessibility_requirements(self, reference, provided, result):
        """Validate accessibility requirements."""
        if not reference or not provided:
            return
        
        # Check universal design
        if reference.universal_design and not provided.get("universal_design", False):
            result.warnings.append("Universal design required but not specified")
            result.recommendations.append("Enable universal design compliance")
        
        # Check door width
        if "clear_width_door_mm" in provided:
            if provided["clear_width_door_mm"] < reference.clear_width_door_mm:
                result.warnings.append(f"Door width {provided['clear_width_door_mm']}mm below requirement {reference.clear_width_door_mm}mm")
                result.recommendations.append(f"Increase door width to minimum {reference.clear_width_door_mm}mm")
    
    def _get_common_issues(self, issues: List[str]) -> Dict[str, int]:
        """Get count of common issues."""
        issue_counts = {}
        for issue in issues:
            issue_counts[issue] = issue_counts.get(issue, 0) + 1
        return issue_counts


# Example usage and testing
if __name__ == "__main__":
    validator = NS3940Validator()
    
    # Test classification validation
    print("NS 3940 Validator Test Results:")
    print("=" * 60)
    
    test_cases = [
        ("SPC-02-A101-111-003", "111"),  # Valid living room
        ("Bad 2. etasje", "130"),        # Wet room
        ("Kjøkken", "140"),              # Kitchen
        ("Unknown Room", "999"),         # Invalid code
        ("Stue", None),                  # Infer from name
    ]
    
    for space_name, function_code in test_cases:
        print(f"\n--- Testing: '{space_name}' (Code: {function_code}) ---")
        
        # Test classification validation
        classification_result = validator.validate_classification(space_name, function_code)
        print(f"Valid: {classification_result.is_valid}")
        print(f"Confidence: {classification_result.confidence:.2f}")
        print(f"Room Type: {classification_result.room_type}")
        
        if classification_result.errors:
            print(f"Errors: {', '.join(classification_result.errors)}")
        if classification_result.warnings:
            print(f"Warnings: {', '.join(classification_result.warnings)}")
        
        # Test wet room validation
        if function_code and validator.defaults_db.is_wet_room(function_code):
            wet_room_data = {
                "water_sanitary": {"drainage_required": True, "hot_cold_water": True},
                "ventilation": {"airflow_extract_m3h": 54},
                "accessibility": {"universal_design": True, "clear_width_door_mm": 850}
            }
            
            wet_room_result = validator.validate_wet_room_consistency(function_code, wet_room_data)
            print(f"Wet Room Valid: {wet_room_result.drainage_required and wet_room_result.ventilation_adequate}")
            if wet_room_result.issues:
                print(f"Wet Room Issues: {', '.join(wet_room_result.issues)}")
    
    # Test performance validation
    print(f"\n{'='*60}")
    print("Performance Validation Test:")
    
    performance_data = {
        "lighting": {"task_lux": 200, "emergency_lighting": False},
        "acoustics": {"class_ns8175": "C", "background_noise_dB": 35},
        "ventilation": {"airflow_supply_m3h": 7.2, "airflow_extract_m3h": 0},
        "thermal": {"setpoint_heating_C": 20},
        "accessibility": {"universal_design": True, "clear_width_door_mm": 850}
    }
    
    perf_result = validator.validate_performance_requirements("111", performance_data)
    print(f"Performance Valid: {perf_result.is_valid}")
    if perf_result.warnings:
        print(f"Performance Warnings: {', '.join(perf_result.warnings)}")
    if perf_result.recommendations:
        print(f"Performance Recommendations: {', '.join(perf_result.recommendations)}")
