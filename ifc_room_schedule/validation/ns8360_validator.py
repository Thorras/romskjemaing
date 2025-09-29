"""
NS 8360 Validator

Validates IFC Space names against NS 8360 naming conventions.
"""

import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

from ..parsers.ns8360_name_parser import NS8360NameParser, NS8360ParsedName


@dataclass
class ValidationResult:
    """Result of NS 8360 validation."""
    
    is_valid: bool
    confidence: float
    errors: List[str]
    warnings: List[str]
    recommendations: List[str]
    parsed_components: Optional[Dict[str, str]] = None


@dataclass
class ValidationRule:
    """Validation rule for NS 8360 compliance."""
    
    name: str
    description: str
    pattern: re.Pattern
    error_message: str
    warning_message: Optional[str] = None
    recommendation: Optional[str] = None


class NS8360Validator:
    """Validates IFC Space names against NS 8360 standards."""
    
    def __init__(self):
        """Initialize NS8360Validator."""
        self.name_parser = NS8360NameParser()
        self.validation_rules = self._build_validation_rules()
    
    def validate_name_pattern(self, space_name: str) -> ValidationResult:
        """
        Validate space name against NS 8360 pattern.
        
        Args:
            space_name: Space name to validate
            
        Returns:
            ValidationResult with validation details
        """
        if not space_name:
            return ValidationResult(
                is_valid=False,
                confidence=0.0,
                errors=["Empty space name"],
                warnings=[],
                recommendations=["Provide a valid space name"]
            )
        
        # Parse the name
        parsed = self.name_parser.parse(space_name)
        
        # Initialize result
        result = ValidationResult(
            is_valid=parsed.is_valid,
            confidence=parsed.confidence,
            errors=[],
            warnings=[],
            recommendations=[],
            parsed_components=self._extract_parsed_components(parsed)
        )
        
        # Apply validation rules
        for rule in self.validation_rules:
            if not rule.pattern.match(space_name):
                if parsed.is_valid:
                    result.errors.append(rule.error_message)
                else:
                    result.warnings.append(rule.warning_message or rule.error_message)
                
                if rule.recommendation:
                    result.recommendations.append(rule.recommendation)
        
        # Additional validations
        self._validate_components(parsed, result)
        self._validate_naming_conventions(space_name, result)
        
        return result
    
    def validate_batch(self, space_names: List[str]) -> Dict[str, ValidationResult]:
        """
        Validate multiple space names.
        
        Args:
            space_names: List of space names to validate
            
        Returns:
            Dictionary mapping names to validation results
        """
        results = {}
        
        for name in space_names:
            results[name] = self.validate_name_pattern(name)
        
        return results
    
    def get_compliance_summary(self, validation_results: Dict[str, ValidationResult]) -> Dict[str, Any]:
        """
        Get compliance summary for multiple validation results.
        
        Args:
            validation_results: Dictionary of validation results
            
        Returns:
            Summary statistics and recommendations
        """
        total_spaces = len(validation_results)
        valid_spaces = sum(1 for result in validation_results.values() if result.is_valid)
        compliant_spaces = sum(1 for result in validation_results.values() 
                             if result.is_valid and result.confidence >= 0.8)
        
        # Collect all errors and warnings
        all_errors = []
        all_warnings = []
        all_recommendations = []
        
        for result in validation_results.values():
            all_errors.extend(result.errors)
            all_warnings.extend(result.warnings)
            all_recommendations.extend(result.recommendations)
        
        # Calculate compliance percentage
        compliance_percentage = (compliant_spaces / total_spaces * 100) if total_spaces > 0 else 0
        
        return {
            "total_spaces": total_spaces,
            "valid_spaces": valid_spaces,
            "compliant_spaces": compliant_spaces,
            "compliance_percentage": compliance_percentage,
            "total_errors": len(all_errors),
            "total_warnings": len(all_warnings),
            "common_errors": self._get_common_issues(all_errors),
            "common_warnings": self._get_common_issues(all_warnings),
            "recommendations": list(set(all_recommendations))
        }
    
    def suggest_corrections(self, space_name: str) -> List[str]:
        """
        Suggest corrections for non-compliant space names.
        
        Args:
            space_name: Space name to suggest corrections for
            
        Returns:
            List of suggested corrections
        """
        suggestions = []
        
        # Parse the name to understand what we have
        parsed = self.name_parser.parse(space_name)
        
        # If it's already valid, no suggestions needed
        if parsed.is_valid:
            return ["Name is already NS 8360 compliant"]
        
        # Suggest based on what's missing or incorrect
        if not space_name.startswith("SPC-"):
            suggestions.append(f"Add SPC prefix: SPC-{space_name}")
        
        # Check for common patterns and suggest corrections
        if " " in space_name and not space_name.startswith("SPC-"):
            # Try to convert common Norwegian names
            norwegian_suggestions = self._suggest_norwegian_conversion(space_name)
            suggestions.extend(norwegian_suggestions)
        
        # Suggest generic NS 8360 format
        suggestions.append("Use NS 8360 format: SPC-{storey}-{zone}-{function}-{sequence}")
        suggestions.append("Example: SPC-02-A101-111-003")
        
        return suggestions
    
    def _build_validation_rules(self) -> List[ValidationRule]:
        """Build validation rules for NS 8360 compliance."""
        return [
            ValidationRule(
                name="spc_prefix",
                description="Must start with SPC-",
                pattern=re.compile(r'^SPC-'),
                error_message="Space name must start with 'SPC-'",
                recommendation="Add SPC- prefix to space name"
            ),
            ValidationRule(
                name="storey_format",
                description="Storey must be 1-3 alphanumeric characters",
                pattern=re.compile(r'^SPC-[A-Z0-9]{1,3}-'),
                error_message="Storey must be 1-3 alphanumeric characters",
                recommendation="Use format like '01', '02', 'U1' for storey"
            ),
            ValidationRule(
                name="function_code_format",
                description="Function code must be 3 digits",
                pattern=re.compile(r'^SPC-[A-Z0-9]{1,3}-[A-Z0-9]{1,6}-\d{3}-'),
                error_message="Function code must be 3 digits",
                recommendation="Use 3-digit NS 3940 function code (e.g., 111, 130)"
            ),
            ValidationRule(
                name="sequence_format",
                description="Sequence must be 3 digits",
                pattern=re.compile(r'^SPC-[A-Z0-9]{1,3}-[A-Z0-9]{1,6}-\d{3}-\d{3}$'),
                error_message="Sequence must be 3 digits",
                recommendation="Use 3-digit sequence number (e.g., 001, 002)"
            )
        ]
    
    def _extract_parsed_components(self, parsed: NS8360ParsedName) -> Optional[Dict[str, str]]:
        """Extract parsed components for validation result."""
        if not parsed.is_valid:
            return None
        
        components = {
            "prefix": parsed.prefix,
            "storey": parsed.storey,
            "function_code": parsed.function_code,
            "sequence": parsed.sequence
        }
        
        if parsed.zone:
            components["zone"] = parsed.zone
        
        return components
    
    def _validate_components(self, parsed: NS8360ParsedName, result: ValidationResult):
        """Validate individual components of parsed name."""
        # Validate storey format
        if parsed.storey and not re.match(r'^[A-Z0-9]{1,3}$', parsed.storey):
            result.warnings.append(f"Storey '{parsed.storey}' should be 1-3 alphanumeric characters")
        
        # Validate function code
        if parsed.function_code and not re.match(r'^\d{3}$', parsed.function_code):
            result.warnings.append(f"Function code '{parsed.function_code}' should be 3 digits")
        
        # Validate sequence
        if parsed.sequence and not re.match(r'^\d{3}$', parsed.sequence):
            result.warnings.append(f"Sequence '{parsed.sequence}' should be 3 digits")
        
        # Validate zone (if present)
        if parsed.zone and not re.match(r'^[A-Z0-9]{1,6}$', parsed.zone):
            result.warnings.append(f"Zone '{parsed.zone}' should be 1-6 alphanumeric characters")
    
    def _validate_naming_conventions(self, space_name: str, result: ValidationResult):
        """Validate naming conventions and best practices."""
        # Check for common mistakes
        if " " in space_name and space_name.startswith("SPC-"):
            result.warnings.append("NS 8360 names should not contain spaces")
            result.recommendations.append("Use hyphens instead of spaces")
        
        # Check for case sensitivity
        if space_name != space_name.upper():
            result.warnings.append("NS 8360 names should be uppercase")
            result.recommendations.append("Convert to uppercase")
        
        # Check for special characters
        if re.search(r'[^A-Z0-9\-]', space_name):
            result.warnings.append("NS 8360 names should only contain letters, numbers, and hyphens")
            result.recommendations.append("Remove special characters")
    
    def _get_common_issues(self, issues: List[str]) -> Dict[str, int]:
        """Get count of common issues."""
        issue_counts = {}
        for issue in issues:
            issue_counts[issue] = issue_counts.get(issue, 0) + 1
        return issue_counts
    
    def _suggest_norwegian_conversion(self, space_name: str) -> List[str]:
        """Suggest NS 8360 conversion for Norwegian room names."""
        suggestions = []
        
        # Common Norwegian room name mappings
        norwegian_mappings = {
            "stue": "111",
            "opphold": "111",
            "soverom": "121",
            "bad": "130",
            "våtrom": "130",
            "wc": "131",
            "toalett": "131",
            "baderom": "132",
            "kjøkken": "140"
        }
        
        name_lower = space_name.lower()
        for norwegian, code in norwegian_mappings.items():
            if norwegian in name_lower:
                # Try to extract storey and sequence
                storey = "01"  # Default
                sequence = "001"  # Default
                
                # Look for storey information
                storey_match = re.search(r'(\d+)', space_name)
                if storey_match:
                    storey = f"{int(storey_match.group(1)):02d}"
                
                # Look for sequence information
                sequence_match = re.search(r'(\d+)$', space_name)
                if sequence_match:
                    sequence = f"{int(sequence_match.group(1)):03d}"
                
                suggestion = f"SPC-{storey}-{code}-{sequence}"
                suggestions.append(f"Convert to NS 8360: {suggestion}")
                break
        
        return suggestions


# Example usage and testing
if __name__ == "__main__":
    validator = NS8360Validator()
    
    # Test cases
    test_names = [
        "SPC-02-A101-111-003",  # Valid
        "SPC-01-A101-130-001",  # Valid
        "SPC-02-111-003",       # Valid without zone
        "Bad 2. etasje",        # Norwegian name
        "Stue leilighet A101",  # Norwegian name
        "SPC-02-A101-111",      # Missing sequence
        "SPC-02-A101-11-003",   # Invalid function code
        "SPC-02-A101-111-3",    # Invalid sequence
        "spc-02-a101-111-003",  # Wrong case
        "SPC 02 A101 111 003",  # Spaces instead of hyphens
        "InvalidName123",       # Completely invalid
        ""                      # Empty
    ]
    
    print("NS 8360 Validator Test Results:")
    print("=" * 60)
    
    for name in test_names:
        print(f"\n--- Testing: '{name}' ---")
        result = validator.validate_name_pattern(name)
        
        print(f"Valid: {result.is_valid}")
        print(f"Confidence: {result.confidence:.2f}")
        
        if result.errors:
            print(f"Errors: {', '.join(result.errors)}")
        if result.warnings:
            print(f"Warnings: {', '.join(result.warnings)}")
        if result.recommendations:
            print(f"Recommendations: {', '.join(result.recommendations)}")
        
        if result.parsed_components:
            print(f"Parsed Components: {result.parsed_components}")
        
        # Test suggestions
        suggestions = validator.suggest_corrections(name)
        if suggestions:
            print(f"Suggestions: {', '.join(suggestions[:2])}")  # Show first 2 suggestions
    
    # Test batch validation
    print(f"\n{'='*60}")
    print("Batch Validation Summary:")
    
    batch_results = validator.validate_batch(test_names)
    summary = validator.get_compliance_summary(batch_results)
    
    print(f"Total Spaces: {summary['total_spaces']}")
    print(f"Valid Spaces: {summary['valid_spaces']}")
    print(f"Compliant Spaces: {summary['compliant_spaces']}")
    print(f"Compliance Percentage: {summary['compliance_percentage']:.1f}%")
    print(f"Total Errors: {summary['total_errors']}")
    print(f"Total Warnings: {summary['total_warnings']}")
    
    if summary['common_errors']:
        print(f"Common Errors: {summary['common_errors']}")
    if summary['recommendations']:
        print(f"Recommendations: {summary['recommendations'][:3]}")  # Show first 3
