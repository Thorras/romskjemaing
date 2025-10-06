"""
Data Quality Analyzer

Analyzes IFC data quality and coverage against comprehensive room schedule template.
Provides insights into data completeness and identifies missing sections.
"""

import os
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

from ..data.space_model import SpaceData
from ..parser.ifc_file_reader import IfcFileReader
from ..parser.ifc_space_extractor import IfcSpaceExtractor
from ..parsers.ns8360_name_parser import NS8360NameParser
from ..mappers.ns3940_classifier import NS3940Classifier


@dataclass
class MissingDataReport:
    """Report on missing data sections."""
    
    space_guid: str
    space_name: str
    ns8360_compliant: bool
    ns3940_classified: bool
    quantities_complete: bool
    surfaces_present: bool
    boundaries_present: bool
    relationships_present: bool
    missing_sections: List[str]
    recommendations: List[str]


@dataclass
class CoverageReport:
    """Report on data coverage and quality."""
    
    total_spaces: int
    compliance_stats: Dict[str, int]
    recommendations: List[str]
    quality_reports: List[MissingDataReport]


class DataQualityAnalyzer:
    """Analyzes IFC data quality and coverage."""
    
    def __init__(self):
        """Initialize the data quality analyzer."""
        self.name_parser = NS8360NameParser()
        self.classifier = NS3940Classifier()
    
    def analyze_spaces_quality(self, spaces: List[SpaceData]) -> Optional[CoverageReport]:
        """
        Analyze quality of provided spaces.
        
        Args:
            spaces: List of spaces to analyze
            
        Returns:
            CoverageReport with analysis results
        """
        if not spaces:
            return None
        
        # Analyze each space
        quality_reports = []
        for space in spaces:
            quality_report = self._analyze_single_space(space)
            quality_reports.append(quality_report)
        
        # Calculate overall statistics
        total_spaces = len(spaces)
        compliance_stats = {
            "ns8360_compliant": sum(1 for q in quality_reports if q.ns8360_compliant),
            "ns3940_classified": sum(1 for q in quality_reports if q.ns3940_classified),
            "quantities_complete": sum(1 for q in quality_reports if q.quantities_complete),
            "surfaces_present": sum(1 for q in quality_reports if q.surfaces_present),
            "boundaries_present": sum(1 for q in quality_reports if q.boundaries_present),
            "relationships_present": sum(1 for q in quality_reports if q.relationships_present)
        }
        
        # Generate recommendations
        recommendations = self._generate_simple_recommendations(compliance_stats, total_spaces)
        
        return CoverageReport(
            total_spaces=total_spaces,
            compliance_stats=compliance_stats,
            recommendations=recommendations,
            quality_reports=quality_reports
        )
    
    def _analyze_single_space(self, space: SpaceData) -> MissingDataReport:
        """Analyze a single space for data quality."""
        # Check NS 8360 compliance
        ns8360_compliant = self._is_ns8360_compliant(space.name)
        
        # Check NS 3940 classification
        ns3940_classified = self._has_ns3940_classification(space.name)
        
        # Check quantities
        quantities_complete = bool(space.quantities and len(space.quantities) > 0)
        
        # Check surfaces
        surfaces_present = bool(space.surfaces and len(space.surfaces) > 0)
        
        # Check boundaries
        boundaries_present = bool(space.space_boundaries and len(space.space_boundaries) > 0)
        
        # Check relationships
        relationships_present = bool(space.relationships and len(space.relationships) > 0)
        
        return MissingDataReport(
            space_guid=space.guid,
            space_name=space.name,
            ns8360_compliant=ns8360_compliant,
            ns3940_classified=ns3940_classified,
            quantities_complete=quantities_complete,
            surfaces_present=surfaces_present,
            boundaries_present=boundaries_present,
            relationships_present=relationships_present,
            missing_sections=[],
            recommendations=[]
        )
    
    def _is_ns8360_compliant(self, name: str) -> bool:
        """Check if name is NS 8360 compliant."""
        if not name:
            return False
        
        import re
        pattern = r"^SPC-[A-Z0-9]{1,3}-[A-Z0-9]{1,6}-\d{3}-\d{3}$|^SPC-[A-Z0-9]{1,3}-\d{3}-\d{3}$"
        return bool(re.match(pattern, name))
    
    def _has_ns3940_classification(self, name: str) -> bool:
        """Check if name has NS 3940 classification."""
        if not name:
            return False
        
        import re
        pattern = r"-\d{3}-"
        return bool(re.search(pattern, name))
    
    def _generate_simple_recommendations(self, compliance_stats: Dict[str, int], total_spaces: int) -> List[str]:
        """Generate simple recommendations based on compliance stats."""
        recommendations = []
        
        if compliance_stats["ns8360_compliant"] < total_spaces * 0.8:
            recommendations.append("Improve NS 8360 naming compliance")
        
        if compliance_stats["ns3940_classified"] < total_spaces * 0.8:
            recommendations.append("Add NS 3940 classification codes")
        
        if compliance_stats["quantities_complete"] < total_spaces * 0.9:
            recommendations.append("Complete quantity data for spaces")
        
        if compliance_stats["surfaces_present"] < total_spaces * 0.7:
            recommendations.append("Add surface data for better material mapping")
        
        if compliance_stats["boundaries_present"] < total_spaces * 0.7:
            recommendations.append("Add space boundary data")
        
        if compliance_stats["relationships_present"] < total_spaces * 0.5:
            recommendations.append("Add relationship data for better context")
        
        if not recommendations:
            recommendations.append("Data quality looks good!")
        
        return recommendations
    
    def analyze_ifc_coverage(self, ifc_file_or_spaces) -> Dict[str, Any]:
        """
        Analyze IFC file coverage against room schedule template.
        
        Args:
            ifc_file_or_spaces: Path to IFC file or list of SpaceData objects
            
        Returns:
            CoverageReport with detailed analysis
        """
        # Handle both file paths and space lists
        if isinstance(ifc_file_or_spaces, str):
            # It's a file path
            ifc_file = ifc_file_or_spaces
            if not os.path.exists(ifc_file):
                raise FileNotFoundError(f"IFC file not found: {ifc_file}")
            
            # Load IFC file and extract spaces
            reader = IfcFileReader()
            success, message = reader.load_file(ifc_file)
            
            if not success:
                raise ValueError(f"Failed to load IFC file: {ifc_file} - {message}")
            
            # Get the loaded IFC file
            ifc_data = reader.ifc_file
            if not ifc_data:
                raise ValueError(f"No IFC data loaded from file: {ifc_file}")
            
            extractor = IfcSpaceExtractor()
            extractor.set_ifc_file(ifc_data)
            spaces = extractor.extract_spaces()
        elif isinstance(ifc_file_or_spaces, list):
            # It's a list of spaces
            spaces = ifc_file_or_spaces
            ifc_file = "<direct_spaces_input>"  # Placeholder for when spaces are passed directly
        else:
            raise ValueError("Input must be either a file path string or a list of SpaceData objects")
        
        return self._analyze_spaces(spaces, ifc_file)
    
    def analyze_space_quality(self, space: SpaceData) -> Dict[str, Any]:
        """
        Analyze quality of a single space.
        
        Args:
            space: SpaceData object to analyze
            
        Returns:
            Dictionary with quality analysis results
        """
        report = self._analyze_single_space(space)
        return {
            "space_guid": report.space_guid,
            "space_name": report.space_name,
            "ns8360_compliant": report.ns8360_compliant,
            "ns3940_classified": report.ns3940_classified,
            "quantities_complete": report.quantities_complete,
            "surfaces_present": report.surfaces_present,
            "boundaries_present": report.boundaries_present,
            "relationships_present": report.relationships_present,
            "missing_sections": report.missing_sections,
            "recommendations": report.recommendations
        }
    
    def identify_missing_sections(self, spaces: List[SpaceData]) -> MissingDataReport:
        """
        Identify missing data sections for each space.
        
        Args:
            spaces: List of SpaceData objects
            
        Returns:
            MissingDataReport with missing data analysis
        """
        spaces_missing_names = []
        spaces_missing_quantities = []
        spaces_missing_surfaces = []
        spaces_missing_boundaries = []
        spaces_missing_relationships = []
        spaces_non_ns8360_compliant = []
        spaces_missing_ns3940_classification = []
        
        for space in spaces:
            # Check name completeness
            if not space.name or space.name.strip() == "":
                spaces_missing_names.append(space.guid)
            else:
                # Check NS 8360 compliance
                parsed_name = self.name_parser.parse(space.name)
                if not parsed_name.is_valid:
                    spaces_non_ns8360_compliant.append(space.guid)
            
            # Check quantities
            if not space.quantities or len(space.quantities) == 0:
                spaces_missing_quantities.append(space.guid)
            
            # Check surfaces
            if not space.surfaces or len(space.surfaces) == 0:
                spaces_missing_surfaces.append(space.guid)
            
            # Check boundaries
            if not space.space_boundaries or len(space.space_boundaries) == 0:
                spaces_missing_boundaries.append(space.guid)
            
            # Check relationships
            if not space.relationships or len(space.relationships) == 0:
                spaces_missing_relationships.append(space.guid)
            
            # Check NS 3940 classification
            if space.name:
                classification = self.classifier.classify_from_name(space.name)
                if not classification:
                    spaces_missing_ns3940_classification.append(space.guid)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            spaces_missing_names,
            spaces_missing_quantities,
            spaces_missing_surfaces,
            spaces_missing_boundaries,
            spaces_missing_relationships,
            spaces_non_ns8360_compliant,
            spaces_missing_ns3940_classification
        )
        
        return MissingDataReport(
            spaces_missing_names=spaces_missing_names,
            spaces_missing_quantities=spaces_missing_quantities,
            spaces_missing_surfaces=spaces_missing_surfaces,
            spaces_missing_boundaries=spaces_missing_boundaries,
            spaces_missing_relationships=spaces_missing_relationships,
            spaces_non_ns8360_compliant=spaces_non_ns8360_compliant,
            spaces_missing_ns3940_classification=spaces_missing_ns3940_classification,
            recommendations=recommendations
        )
    
    def estimate_completion_percentage(self, space: SpaceData) -> float:
        """
        Estimate completion percentage for a single space.
        
        Args:
            space: SpaceData object to analyze
            
        Returns:
            Completion percentage (0.0 to 1.0)
        """
        total_components = 8  # Name, quantities, surfaces, boundaries, relationships, NS8360, NS3940, user_desc
        completed_components = 0
        
        # Check name
        if space.name and space.name.strip():
            completed_components += 1
        
        # Check quantities
        if space.quantities and len(space.quantities) > 0:
            completed_components += 1
        
        # Check surfaces
        if space.surfaces and len(space.surfaces) > 0:
            completed_components += 1
        
        # Check boundaries
        if space.space_boundaries and len(space.space_boundaries) > 0:
            completed_components += 1
        
        # Check relationships
        if space.relationships and len(space.relationships) > 0:
            completed_components += 1
        
        # Check NS 8360 compliance
        if space.name:
            parsed_name = self.name_parser.parse(space.name)
            if parsed_name.is_valid:
                completed_components += 1
        
        # Check NS 3940 classification
        if space.name:
            classification = self.classifier.classify_from_name(space.name)
            if classification:
                completed_components += 1
        
        # Check user descriptions
        if space.user_descriptions and len(space.user_descriptions) > 0:
            completed_components += 1
        
        return completed_components / total_components
    
    def generate_recommendations(self, analysis: CoverageReport) -> List[str]:
        """
        Generate recommendations based on analysis results.
        
        Args:
            analysis: CoverageReport to analyze
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        # Name quality recommendations
        if analysis.name_completeness < 0.9:
            recommendations.append(
                f"Improve name completeness: {analysis.name_completeness:.1%} of spaces have names. "
                "Consider implementing NS 8360 naming standards."
            )
        
        # NS 8360 compliance recommendations
        if analysis.ns8360_compliance_rate < 0.7:
            recommendations.append(
                f"Improve NS 8360 compliance: {analysis.ns8360_compliance_rate:.1%} of spaces follow standard. "
                "Implement NS 8360 naming conventions (SPC-{storey}-{zone}-{func}-{seq})."
            )
        
        # NS 3940 classification recommendations
        if analysis.ns3940_classification_rate < 0.8:
            recommendations.append(
                f"Improve NS 3940 classification: {analysis.ns3940_classification_rate:.1%} of spaces classified. "
                "Add function codes (111, 130, 131, 132, 140) to space names."
            )
        
        # Quantities recommendations
        if analysis.quantity_completeness < 0.8:
            recommendations.append(
                f"Improve quantity data: {analysis.quantity_completeness:.1%} of spaces have quantities. "
                "Ensure Qto_SpaceBaseQuantities property sets are populated."
            )
        
        # Surface data recommendations
        if analysis.surface_completeness < 0.6:
            recommendations.append(
                f"Improve surface data: {analysis.surface_completeness:.1%} of spaces have surfaces. "
                "Check IFC space boundary relationships and surface extraction."
            )
        
        # Overall quality recommendations
        if analysis.overall_quality_score < 0.7:
            recommendations.append(
                f"Overall data quality is {analysis.overall_quality_score:.1%}. "
                "Consider implementing comprehensive data validation and quality control processes."
            )
        
        return recommendations
    
    def _analyze_spaces(self, spaces: List[SpaceData], ifc_file: str) -> Dict[str, Any]:
        """Analyze spaces and generate coverage report."""
        total_spaces = len(spaces)
        
        if total_spaces == 0:
            return {
                "total_spaces": 0,
                "spaces_with_names": 0,
                "spaces_with_ns8360_compliant_names": 0,
                "spaces_with_classification": 0,
                "spaces_with_quantities": 0,
                "spaces_with_surfaces": 0,
                "spaces_with_boundaries": 0,
                "spaces_with_relationships": 0,
                "ns8360_compliance_rate": 0.0,
                "ns3940_classification_rate": 0.0,
                "name_completeness": 0.0,
                "quantity_completeness": 0.0,
                "surface_completeness": 0.0,
                "boundary_completeness": 0.0,
                "relationship_completeness": 0.0,
                "overall_quality_score": 0.0,
                "missing_name_count": 0,
                "missing_quantities_count": 0,
                "missing_surfaces_count": 0,
                "missing_boundaries_count": 0,
                "missing_relationships_count": 0,
                "compliance_stats": {
                    "ns8360_compliant": 0,
                    "ns3940_classified": 0,
                    "total_spaces": 0
                }
            }
        
        # Count spaces with data
        spaces_with_names = sum(1 for s in spaces if s.name and s.name.strip())
        spaces_with_quantities = sum(1 for s in spaces if s.quantities and len(s.quantities) > 0)
        spaces_with_surfaces = sum(1 for s in spaces if s.surfaces and len(s.surfaces) > 0)
        spaces_with_boundaries = sum(1 for s in spaces if s.space_boundaries and len(s.space_boundaries) > 0)
        spaces_with_relationships = sum(1 for s in spaces if s.relationships and len(s.relationships) > 0)
        
        # NS 8360 compliance
        ns8360_compliant = 0
        for space in spaces:
            if space.name:
                parsed_name = self.name_parser.parse(space.name)
                if parsed_name.is_valid:
                    ns8360_compliant += 1
        
        # NS 3940 classification
        ns3940_classified = 0
        for space in spaces:
            if space.name:
                classification = self.classifier.classify_from_name(space.name)
                if classification:
                    ns3940_classified += 1
        
        # Calculate completeness rates
        name_completeness = spaces_with_names / total_spaces
        quantity_completeness = spaces_with_quantities / total_spaces
        surface_completeness = spaces_with_surfaces / total_spaces
        boundary_completeness = spaces_with_boundaries / total_spaces
        relationship_completeness = spaces_with_relationships / total_spaces
        
        ns8360_compliance_rate = ns8360_compliant / total_spaces
        ns3940_classification_rate = ns3940_classified / total_spaces
        
        # Calculate overall quality score
        component_scores = [
            name_completeness,
            quantity_completeness,
            surface_completeness,
            boundary_completeness,
            relationship_completeness,
            ns8360_compliance_rate,
            ns3940_classification_rate
        ]
        overall_quality_score = sum(component_scores) / len(component_scores)
        
        return {
            "total_spaces": total_spaces,
            "spaces_with_names": spaces_with_names,
            "spaces_with_ns8360_compliant_names": ns8360_compliant,
            "spaces_with_classification": ns3940_classified,
            "spaces_with_quantities": spaces_with_quantities,
            "spaces_with_surfaces": spaces_with_surfaces,
            "spaces_with_boundaries": spaces_with_boundaries,
            "spaces_with_relationships": spaces_with_relationships,
            "ns8360_compliance_rate": ns8360_compliance_rate,
            "ns3940_classification_rate": ns3940_classification_rate,
            "name_completeness": name_completeness,
            "quantity_completeness": quantity_completeness,
            "surface_completeness": surface_completeness,
            "boundary_completeness": boundary_completeness,
            "relationship_completeness": relationship_completeness,
            "overall_quality_score": overall_quality_score,
            "missing_name_count": total_spaces - spaces_with_names,
            "missing_quantities_count": total_spaces - spaces_with_quantities,
            "missing_surfaces_count": total_spaces - spaces_with_surfaces,
            "missing_boundaries_count": total_spaces - spaces_with_boundaries,
            "missing_relationships_count": total_spaces - spaces_with_relationships,
            "compliance_stats": {
                "ns8360_compliant": ns8360_compliant,
                "ns3940_classified": ns3940_classified,
                "total_spaces": total_spaces
            }
        }
    
    def _generate_recommendations(self, missing_names: List[str], missing_quantities: List[str],
                                missing_surfaces: List[str], missing_boundaries: List[str],
                                missing_relationships: List[str], non_ns8360: List[str],
                                missing_ns3940: List[str]) -> List[str]:
        """Generate specific recommendations based on missing data."""
        recommendations = []
        
        if missing_names:
            recommendations.append(f"Add names to {len(missing_names)} spaces without names")
        
        if non_ns8360:
            recommendations.append(f"Implement NS 8360 naming for {len(non_ns8360)} spaces")
        
        if missing_ns3940:
            recommendations.append(f"Add NS 3940 classification to {len(missing_ns3940)} spaces")
        
        if missing_quantities:
            recommendations.append(f"Populate quantities for {len(missing_quantities)} spaces")
        
        if missing_surfaces:
            recommendations.append(f"Add surface data for {len(missing_surfaces)} spaces")
        
        if missing_boundaries:
            recommendations.append(f"Add boundary data for {len(missing_boundaries)} spaces")
        
        if missing_relationships:
            recommendations.append(f"Add relationship data for {len(missing_relationships)} spaces")
        
        return recommendations


# Example usage and testing
if __name__ == "__main__":
    analyzer = DataQualityAnalyzer()
    
    # Test with sample data
    from ..data.space_model import SpaceData
    
    sample_spaces = [
        SpaceData(
            guid="test1",
            name="SPC-02-A101-111-003",
            long_name="Stue | 02/A101 | NS3940:111",
            description="Test space",
            object_type="IfcSpace",
            zone_category="A101",
            number="003",
            elevation=0.0,
            quantities={"GrossArea": 25.5},
            surfaces=[],
            boundaries=[],
            relationships=[]
        ),
        SpaceData(
            guid="test2",
            name="Bad 2. etasje",
            long_name="Bad",
            description="Test bathroom",
            object_type="IfcSpace",
            zone_category="A101",
            number="001",
            elevation=0.0,
            quantities={},
            surfaces=[],
            boundaries=[],
            relationships=[]
        )
    ]
    
    print("Data Quality Analyzer Test:")
    print("=" * 50)
    
    # Test missing data analysis
    missing_report = analyzer.identify_missing_sections(sample_spaces)
    print(f"Missing names: {len(missing_report.spaces_missing_names)}")
    print(f"Non-NS8360 compliant: {len(missing_report.spaces_non_ns8360_compliant)}")
    print(f"Missing NS3940 classification: {len(missing_report.spaces_missing_ns3940_classification)}")
    
    # Test completion percentage
    for space in sample_spaces:
        completion = analyzer.estimate_completion_percentage(space)
        print(f"Space {space.guid}: {completion:.1%} complete")
