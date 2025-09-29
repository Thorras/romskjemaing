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
class CoverageReport:
    """Report on data coverage and quality."""
    
    total_spaces: int
    spaces_with_names: int
    spaces_with_ns8360_compliant_names: int
    spaces_with_classification: int
    spaces_with_quantities: int
    spaces_with_surfaces: int
    spaces_with_boundaries: int
    spaces_with_relationships: int
    
    # NS Standards compliance
    ns8360_compliance_rate: float
    ns3940_classification_rate: float
    
    # Data completeness scores
    name_completeness: float
    quantity_completeness: float
    surface_completeness: float
    boundary_completeness: float
    relationship_completeness: float
    
    # Overall quality score
    overall_quality_score: float
    
    # Missing data analysis
    missing_name_count: int
    missing_quantities_count: int
    missing_surfaces_count: int
    missing_boundaries_count: int
    missing_relationships_count: int


@dataclass
class MissingDataReport:
    """Report on missing data sections."""
    
    spaces_missing_names: List[str]  # GUIDs
    spaces_missing_quantities: List[str]
    spaces_missing_surfaces: List[str]
    spaces_missing_boundaries: List[str]
    spaces_missing_relationships: List[str]
    
    # NS Standards issues
    spaces_non_ns8360_compliant: List[str]
    spaces_missing_ns3940_classification: List[str]
    
    # Recommendations
    recommendations: List[str]


class DataQualityAnalyzer:
    """Analyzes IFC data quality and coverage."""
    
    def __init__(self):
        """Initialize the data quality analyzer."""
        self.name_parser = NS8360NameParser()
        self.classifier = NS3940Classifier()
    
    def analyze_ifc_coverage(self, ifc_file: str) -> CoverageReport:
        """
        Analyze IFC file coverage against room schedule template.
        
        Args:
            ifc_file: Path to IFC file
            
        Returns:
            CoverageReport with detailed analysis
        """
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
        
        return self._analyze_spaces(spaces, ifc_file)
    
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
    
    def _analyze_spaces(self, spaces: List[SpaceData], ifc_file: str) -> CoverageReport:
        """Analyze spaces and generate coverage report."""
        total_spaces = len(spaces)
        
        if total_spaces == 0:
            return CoverageReport(
                total_spaces=0,
                spaces_with_names=0,
                spaces_with_ns8360_compliant_names=0,
                spaces_with_classification=0,
                spaces_with_quantities=0,
                spaces_with_surfaces=0,
                spaces_with_boundaries=0,
                spaces_with_relationships=0,
                ns8360_compliance_rate=0.0,
                ns3940_classification_rate=0.0,
                name_completeness=0.0,
                quantity_completeness=0.0,
                surface_completeness=0.0,
                boundary_completeness=0.0,
                relationship_completeness=0.0,
                overall_quality_score=0.0,
                missing_name_count=0,
                missing_quantities_count=0,
                missing_surfaces_count=0,
                missing_boundaries_count=0,
                missing_relationships_count=0
            )
        
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
        
        return CoverageReport(
            total_spaces=total_spaces,
            spaces_with_names=spaces_with_names,
            spaces_with_ns8360_compliant_names=ns8360_compliant,
            spaces_with_classification=ns3940_classified,
            spaces_with_quantities=spaces_with_quantities,
            spaces_with_surfaces=spaces_with_surfaces,
            spaces_with_boundaries=spaces_with_boundaries,
            spaces_with_relationships=spaces_with_relationships,
            ns8360_compliance_rate=ns8360_compliance_rate,
            ns3940_classification_rate=ns3940_classification_rate,
            name_completeness=name_completeness,
            quantity_completeness=quantity_completeness,
            surface_completeness=surface_completeness,
            boundary_completeness=boundary_completeness,
            relationship_completeness=relationship_completeness,
            overall_quality_score=overall_quality_score,
            missing_name_count=total_spaces - spaces_with_names,
            missing_quantities_count=total_spaces - spaces_with_quantities,
            missing_surfaces_count=total_spaces - spaces_with_surfaces,
            missing_boundaries_count=total_spaces - spaces_with_boundaries,
            missing_relationships_count=total_spaces - spaces_with_relationships
        )
    
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
