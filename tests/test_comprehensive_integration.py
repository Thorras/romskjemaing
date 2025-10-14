#!/usr/bin/env python3
"""
Comprehensive Integration Test for IFC Floor Plan Generator

This test validates the complete system integration.
"""

import pytest
import json
import os
import tempfile
import time
from pathlib import Path
from typing import List, Dict, Any

from ifc_room_schedule.parser.ifc_file_reader import IfcFileReader
from ifc_room_schedule.export.enhanced_json_builder import EnhancedJsonBuilder
from ifc_room_schedule.analysis.data_quality_analyzer import DataQualityAnalyzer
from ifc_room_schedule.parser.batch_processor import BatchProcessor
from ifc_room_schedule.utils.caching_manager import CachingManager, CacheConfig
from ifc_room_schedule.data.space_model import SpaceData


from ifc_room_schedule.mappers.ns3940_classifier import NS3940Classifier
from ifc_room_schedule.parsers.ns8360_name_parser import NS8360NameParser


@pytest.fixture
def temp_output_dir():
    """Create temporary output directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


class TestComprehensiveIntegration:
    """Comprehensive integration tests."""
    
    @pytest.fixture
    def sample_spaces(self) -> List[SpaceData]:
        """Create sample spaces for testing."""
        return [
            SpaceData(
                guid="test_space_1",
                name="SPC-02-A101-111-003",
                long_name="Stue | 02/A101 | NS3940:111",
                description="Test living room",
                object_type="IfcSpace",
                zone_category="A101",
                number="003",
                elevation=0.0,
                quantities={"Height": 2.4, "NetArea": 25.0, "GrossArea": 30.0},
                surfaces=[],
                space_boundaries=[],
                relationships=[]
            ),
            SpaceData(
                guid="test_space_2",
                name="SPC-02-A101-130-001",
                long_name="Bad | 02/A101 | NS3940:130",
                description="Test bathroom",
                object_type="IfcSpace",
                zone_category="A101",
                number="001",
                elevation=0.0,
                quantities={"Height": 2.4, "NetArea": 8.0, "GrossArea": 10.0},
                surfaces=[],
                space_boundaries=[],
                relationships=[]
            ),
            SpaceData(
                guid="test_space_3",
                name="SPC-02-A101-150-002",
                long_name="Kjøkken | 02/A101 | NS3940:150",
                description="Test kitchen",
                object_type="IfcSpace",
                zone_category="A101",
                number="002",
                elevation=0.0,
                quantities={"Height": 2.4, "NetArea": 15.0, "GrossArea": 18.0},
                surfaces=[],
                space_boundaries=[],
                relationships=[]
            )
        ]
    
    def test_end_to_end_export_pipeline(self, sample_spaces, temp_output_dir):
        """Test complete export pipeline from spaces to JSON."""
        # Initialize components
        builder = EnhancedJsonBuilder()
        builder.set_source_file("test.ifc")
        builder.set_ifc_version("IFC4")
        
        # Test different export profiles
        profiles = ["core", "advanced", "production"]
        
        for profile in profiles:
            output_file = os.path.join(temp_output_dir, f"test_export_{profile}.json")
            
            # Build enhanced JSON structure
            enhanced_data = builder.build_enhanced_json_structure(
                spaces=sample_spaces,
                export_profile=profile
            )
            
            # Write to file
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(enhanced_data, f, indent=2, ensure_ascii=False)
            
            # Verify file was created
            assert os.path.exists(output_file)
            
            # Verify JSON structure
            with open(output_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            assert "metadata" in data
            assert "spaces" in data
            assert len(data["spaces"]) == len(sample_spaces)
            
            # Verify space structure
            for space_data in data["spaces"]:
                assert "identification" in space_data
                assert "ifc_metadata" in space_data
                assert "geometry" in space_data
                assert "classification" in space_data
                
                if profile == "production":
                    # Verify Phase 2B and 2C sections
                    assert "performance_requirements" in space_data
                    assert "finishes" in space_data
                    assert "openings" in space_data
                    assert "fixtures_and_equipment" in space_data
                    assert "hse_and_accessibility" in space_data
                    assert "qa_qc" in space_data
                    assert "interfaces" in space_data
                    assert "logistics_and_site" in space_data
                    assert "commissioning" in space_data
    
    def test_data_quality_analysis_integration(self, sample_spaces):
        """Test data quality analysis integration."""
        analyzer = DataQualityAnalyzer()
        
        # Analyze coverage
        coverage_report = analyzer.analyze_ifc_coverage(sample_spaces)
        
        assert coverage_report is not None
        assert "total_spaces" in coverage_report
        assert "compliance_stats" in coverage_report
        assert coverage_report["total_spaces"] == len(sample_spaces)
        
        # Analyze individual spaces
        for space in sample_spaces:
            quality_report = analyzer.analyze_space_quality(space)
            
            assert quality_report is not None
            assert "ns8360_compliant" in quality_report
            assert "ns3940_classified" in quality_report
            assert "quantities_complete" in quality_report
    
    def test_batch_processing_integration(self, sample_spaces, temp_output_dir):
        """Test batch processing integration."""
        # Create larger dataset
        large_spaces = []
        for i in range(100):
            space = SpaceData(
                guid=f"test_space_{i}",
                name=f"SPC-02-A101-111-{i:03d}",
                long_name=f"Test Space {i} | 02/A101 | NS3940:111",
                description=f"Test space {i}",
                object_type="IfcSpace",
                zone_category="A101",
                number=f"{i:03d}",
                elevation=0.0,
                quantities={"Height": 2.4, "NetArea": 25.0},
                surfaces=[],
                space_boundaries=[],
                relationships=[]
            )
            large_spaces.append(space)
        
        # Test batch processing
        processor = BatchProcessor(max_memory_mb=128, chunk_size=20)
        output_file = os.path.join(temp_output_dir, "batch_test.json")
        
        progress_updates = []
        
        def progress_callback(progress: int, status: str):
            progress_updates.append((progress, status))
        
        # Process spaces
        stats = processor.process_spaces_batch(
            large_spaces,
            output_file,
            "production",
            progress_callback
        )
        
        # Verify results
        assert stats["total_spaces"] == 100
        assert stats["processed_spaces"] == 100
        assert stats["processing_time"] > 0
        assert os.path.exists(output_file)
        
        # Verify progress updates
        assert len(progress_updates) > 0
        assert progress_updates[-1][0] == 100  # Final progress should be 100%
        
        # Verify output file
        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert len(data["spaces"]) == 100
    
    def test_caching_integration(self, sample_spaces):
        """Test caching system integration."""
        # Initialize cache
        cache_config = CacheConfig(max_memory_mb=64, max_disk_mb=128)
        cache = CachingManager(cache_config)
        
        # Test caching with expensive operation
        def expensive_operation():
            time.sleep(0.1)  # Simulate expensive operation
            return {"result": "expensive_data", "timestamp": time.time()}
        
        # First call - should be slow
        start_time = time.time()
        result1 = cache.get_or_set("expensive_key", expensive_operation)
        first_call_time = time.time() - start_time
        
        # Second call - should be fast (cached)
        start_time = time.time()
        result2 = cache.get_or_set("expensive_key", expensive_operation)
        second_call_time = time.time() - start_time
        
        # Verify caching worked
        assert result1 == result2
        assert second_call_time < first_call_time
        
        # Verify cache statistics
        stats = cache.get_stats()
        assert stats["hits"] > 0
        assert stats["hit_rate"] > 0
    
    def test_ns_standards_integration(self, sample_spaces):
        """Test NS 8360 and NS 3940 standards integration."""
        classifier = NS3940Classifier()
        name_parser = NS8360NameParser()
        
        for space in sample_spaces:
            # Test NS 8360 parsing
            parsed_name = name_parser.parse_space_name(space.name)
            assert parsed_name is not None
            
            # Test NS 3940 classification
            classification = classifier.classify_space(space.name, space.long_name)
            assert classification is not None
            assert hasattr(classification, 'function_code')
            assert hasattr(classification, 'label')
            assert classification.function_code is not None
    
    def test_export_formats_integration(self, sample_spaces, temp_output_dir):
        """Test integration with all export formats."""
        from ifc_room_schedule.export.csv_exporter import CsvExporter
        from ifc_room_schedule.export.excel_exporter import ExcelExporter
        from ifc_room_schedule.export.pdf_exporter import PdfExporter
        
        # Test CSV export
        csv_file = os.path.join(temp_output_dir, "test_export.csv")
        csv_exporter = CsvExporter()
        success = csv_exporter.export_to_csv(sample_spaces, csv_file)
        assert success
        assert os.path.exists(csv_file)
        
        # Test Excel export
        excel_file = os.path.join(temp_output_dir, "test_export.xlsx")
        excel_exporter = ExcelExporter()
        success = excel_exporter.export_to_excel(sample_spaces, excel_file)
        assert success
        assert os.path.exists(excel_file)
        
        # Test PDF export
        pdf_file = os.path.join(temp_output_dir, "test_export.pdf")
        pdf_exporter = PdfExporter()
        success = pdf_exporter.export_to_pdf(sample_spaces, pdf_file)
        assert success
        assert os.path.exists(pdf_file)
    
    def test_error_handling_integration(self, temp_output_dir):
        """Test error handling across the pipeline."""
        # Test with invalid spaces
        invalid_spaces = [
            SpaceData(
                guid="invalid_space",
                name="",  # Invalid name
                long_name="",
                description="",
                object_type="IfcSpace",
                zone_category="",
                number="",
                elevation=0.0,
                quantities={},
                surfaces=[],
                space_boundaries=[],
                relationships=[]
            )
        ]
        
        # Test export with invalid data
        builder = EnhancedJsonBuilder()
        try:
            enhanced_data = builder.build_enhanced_json_structure(
                spaces=invalid_spaces,
                export_profile="production"
            )
            # Should not raise exception, but handle gracefully
            assert enhanced_data is not None
        except Exception as e:
            # If exception is raised, it should be handled gracefully
            assert "error" in str(e).lower() or "invalid" in str(e).lower()
    
    def test_performance_integration(self, temp_output_dir):
        """Test performance with larger datasets."""
        # Create performance test dataset
        large_spaces = []
        for i in range(500):
            space = SpaceData(
                guid=f"perf_space_{i}",
                name=f"SPC-02-A101-111-{i:03d}",
                long_name=f"Performance Test Space {i} | 02/A101 | NS3940:111",
                description=f"Performance test space {i}",
                object_type="IfcSpace",
                zone_category="A101",
                number=f"{i:03d}",
                elevation=0.0,
                quantities={"Height": 2.4, "NetArea": 25.0},
                surfaces=[],
                space_boundaries=[],
                relationships=[]
            )
            large_spaces.append(space)
        
        # Test performance
        start_time = time.time()
        
        processor = BatchProcessor(max_memory_mb=256, chunk_size=50)
        output_file = os.path.join(temp_output_dir, "performance_test.json")
        
        stats = processor.process_spaces_batch(
            large_spaces,
            output_file,
            "production"
        )
        
        processing_time = time.time() - start_time
        
        # Verify performance
        assert stats["total_spaces"] == 500
        assert stats["processed_spaces"] == 500
        assert processing_time < 30.0  # Should complete within 30 seconds
        assert os.path.exists(output_file)
        
        # Verify output
        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert len(data["spaces"]) == 500
    
    def test_memory_management_integration(self):
        """Test memory management with large datasets."""
        import gc
        import psutil
        
        # Get initial memory
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create large dataset
        large_spaces = []
        for i in range(1000):
            space = SpaceData(
                guid=f"mem_space_{i}",
                name=f"SPC-02-A101-111-{i:03d}",
                long_name=f"Memory Test Space {i} | 02/A101 | NS3940:111",
                description=f"Memory test space {i}",
                object_type="IfcSpace",
                zone_category="A101",
                number=f"{i:03d}",
                elevation=0.0,
                quantities={"Height": 2.4, "NetArea": 25.0},
                surfaces=[],
                space_boundaries=[],
                relationships=[]
            )
            large_spaces.append(space)
        
        # Process with memory management
        processor = BatchProcessor(max_memory_mb=128, chunk_size=25)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = os.path.join(temp_dir, "memory_test.json")
            
            stats = processor.process_spaces_batch(
                large_spaces,
                output_file,
                "production"
            )
        
        # Force garbage collection
        gc.collect()
        
        # Check memory usage
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 200MB)
        assert memory_increase < 200.0
        
        # Verify processing completed
        assert stats["total_spaces"] == 1000
        assert stats["processed_spaces"] == 1000


class TestRealWorldScenarios:
    """Tests for real-world usage scenarios."""
    
    def test_office_building_scenario(self, temp_output_dir):
        """Test typical office building room schedule."""
        # Create office building spaces
        office_spaces = [
            SpaceData(
                guid="office_1",
                name="SPC-01-A101-111-001",
                long_name="Kontor | 01/A101 | NS3940:111",
                description="Open office space",
                object_type="IfcSpace",
                zone_category="A101",
                number="001",
                elevation=0.0,
                quantities={"Height": 2.7, "NetArea": 50.0, "GrossArea": 60.0},
                surfaces=[],
                space_boundaries=[],
                relationships=[]
            ),
            SpaceData(
                guid="meeting_1",
                name="SPC-01-A101-112-002",
                long_name="Møterom | 01/A101 | NS3940:112",
                description="Meeting room",
                object_type="IfcSpace",
                zone_category="A101",
                number="002",
                elevation=0.0,
                quantities={"Height": 2.7, "NetArea": 20.0, "GrossArea": 25.0},
                surfaces=[],
                space_boundaries=[],
                relationships=[]
            ),
            SpaceData(
                guid="reception_1",
                name="SPC-01-A101-113-003",
                long_name="Resepsjon | 01/A101 | NS3940:113",
                description="Reception area",
                object_type="IfcSpace",
                zone_category="A101",
                number="003",
                elevation=0.0,
                quantities={"Height": 2.7, "NetArea": 30.0, "GrossArea": 35.0},
                surfaces=[],
                space_boundaries=[],
                relationships=[]
            )
        ]
        
        # Test production export
        builder = EnhancedJsonBuilder()
        builder.set_source_file("office_building.ifc")
        builder.set_ifc_version("IFC4")
        
        output_file = os.path.join(temp_output_dir, "office_building.json")
        
        enhanced_data = builder.build_enhanced_json_structure(
            spaces=office_spaces,
            export_profile="production"
        )
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(enhanced_data, f, indent=2, ensure_ascii=False)
        
        # Verify office-specific data
        assert os.path.exists(output_file)
        
        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Check that all spaces have required sections
        for space_data in data["spaces"]:
            assert "performance_requirements" in space_data
            assert "finishes" in space_data
            assert "fixtures_and_equipment" in space_data
            assert "hse_and_accessibility" in space_data
    
    def test_residential_building_scenario(self, temp_output_dir):
        """Test typical residential building room schedule."""
        # Create residential spaces
        residential_spaces = [
            SpaceData(
                guid="apartment_1",
                name="SPC-02-A101-111-001",
                long_name="Stue | 02/A101 | NS3940:111",
                description="Living room",
                object_type="IfcSpace",
                zone_category="A101",
                number="001",
                elevation=0.0,
                quantities={"Height": 2.4, "NetArea": 25.0, "GrossArea": 30.0},
                surfaces=[],
                space_boundaries=[],
                relationships=[]
            ),
            SpaceData(
                guid="bedroom_1",
                name="SPC-02-A101-111-002",
                long_name="Soverom | 02/A101 | NS3940:111",
                description="Bedroom",
                object_type="IfcSpace",
                zone_category="A101",
                number="002",
                elevation=0.0,
                quantities={"Height": 2.4, "NetArea": 15.0, "GrossArea": 18.0},
                surfaces=[],
                space_boundaries=[],
                relationships=[]
            ),
            SpaceData(
                guid="bathroom_1",
                name="SPC-02-A101-130-003",
                long_name="Bad | 02/A101 | NS3940:130",
                description="Bathroom",
                object_type="IfcSpace",
                zone_category="A101",
                number="003",
                elevation=0.0,
                quantities={"Height": 2.4, "NetArea": 8.0, "GrossArea": 10.0},
                surfaces=[],
                space_boundaries=[],
                relationships=[]
            )
        ]
        
        # Test advanced export
        builder = EnhancedJsonBuilder()
        builder.set_source_file("residential_building.ifc")
        builder.set_ifc_version("IFC4")
        
        output_file = os.path.join(temp_output_dir, "residential_building.json")
        
        enhanced_data = builder.build_enhanced_json_structure(
            spaces=residential_spaces,
            export_profile="advanced"
        )
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(enhanced_data, f, indent=2, ensure_ascii=False)
        
        # Verify residential-specific data
        assert os.path.exists(output_file)
        
        with open(output_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Check that spaces have appropriate sections for advanced export
        for space_data in data["spaces"]:
            assert "identification" in space_data
            assert "classification" in space_data
            assert "surfaces" in space_data
            assert "space_boundaries" in space_data


if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v"])
