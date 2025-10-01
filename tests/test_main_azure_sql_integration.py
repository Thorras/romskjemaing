#!/usr/bin/env python3
"""Test Azure SQL integration in main.py"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from main import RomskjemaGenerator
from ifc_room_schedule.data.space_model import SpaceData


class TestMainAzureSQLIntegration:
    """Test Azure SQL integration in the main application"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.app = RomskjemaGenerator()
        
        # Create mock space data
        self.mock_spaces = [
            SpaceData(
                guid="test-guid-1",
                name="Test Room 1",
                long_name="Test Room 1 Long Name",
                description="Test room description",
                object_type="IfcSpace",
                zone_category="Room",
                number="101",
                elevation=0.0,
                quantities={"NetFloorArea": 25.5, "GrossVolume": 75.0}
            ),
            SpaceData(
                guid="test-guid-2", 
                name="Test Room 2",
                long_name="Test Room 2 Long Name",
                description="Test room description",
                object_type="IfcSpace",
                zone_category="Room",
                number="102",
                elevation=0.0,
                quantities={"NetFloorArea": 30.0, "GrossVolume": 90.0}
            )
        ]
    
    def test_azure_sql_format_in_choices(self):
        """Test that azure-sql is available as a format choice"""
        import argparse
        from main import main
        
        # Create parser like in main()
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "--format", "-f",
            choices=["json", "csv", "excel", "pdf", "azure-sql"],
            default="json"
        )
        
        # Test that azure-sql is accepted
        args = parser.parse_args(["--format", "azure-sql"])
        assert args.format == "azure-sql"
    
    def test_azure_connection_string_validation(self):
        """Test Azure SQL connection string validation"""
        # Test without connection string
        result = self.app._process_standard(
            spaces=self.mock_spaces,
            output_path="test.json",
            export_profile="production", 
            export_format="azure-sql",
            azure_connection_string=None,
            azure_table_name="test_table"
        )
        
        assert "error" in result
        assert "Azure SQL connection string is required" in result["error"]
    
    @patch('main.AzureSQLExporter')
    def test_azure_sql_exporter_initialization(self, mock_exporter_class):
        """Test that Azure SQL exporter is properly initialized"""
        mock_exporter = Mock()
        mock_exporter.export_data.return_value = True
        mock_exporter_class.return_value = mock_exporter
        
        # Mock the json builder
        with patch.object(self.app.json_builder, 'build_enhanced_json_structure') as mock_builder:
            mock_builder.return_value = {"test": "data"}
            
            result = self.app._process_standard(
                spaces=self.mock_spaces,
                output_path="test.json",
                export_profile="production",
                export_format="azure-sql", 
                azure_connection_string="Server=test;Database=test;",
                azure_table_name="test_table"
            )
        
        # Verify exporter was initialized with connection string
        mock_exporter_class.assert_called_once_with("Server=test;Database=test;")
        
        # Verify export_data was called with correct parameters
        mock_exporter.export_data.assert_called_once_with({"test": "data"}, "test_table")
        
        assert result["success"] is True
        assert result["format"] == "azure-sql"
    
    @patch('main.AzureSQLExporter')
    def test_azure_sql_export_error_handling(self, mock_exporter_class):
        """Test error handling in Azure SQL export"""
        mock_exporter = Mock()
        mock_exporter.export_data.side_effect = Exception("Connection failed")
        mock_exporter_class.return_value = mock_exporter
        
        with patch.object(self.app.json_builder, 'build_enhanced_json_structure') as mock_builder:
            mock_builder.return_value = {"test": "data"}
            
            result = self.app._process_standard(
                spaces=self.mock_spaces,
                output_path="test.json", 
                export_profile="production",
                export_format="azure-sql",
                azure_connection_string="Server=test;Database=test;",
                azure_table_name="test_table"
            )
        
        assert "error" in result
        assert "Azure SQL export failed: Connection failed" in result["error"]
    
    def test_batch_processing_with_azure_sql(self):
        """Test that batch processing passes Azure SQL parameters correctly"""
        with patch.object(self.app, '_process_standard') as mock_standard:
            mock_standard.return_value = {"success": True, "format": "azure-sql"}
            
            result = self.app._process_batch(
                spaces=self.mock_spaces,
                output_path="test.json",
                export_profile="production",
                export_format="azure-sql",
                chunk_size=100,
                azure_connection_string="Server=test;Database=test;",
                azure_table_name="test_table"
            )
            
            # Verify _process_standard was called with correct Azure parameters
            mock_standard.assert_called_once_with(
                self.mock_spaces,
                "test.json", 
                "production",
                "azure-sql",
                "Server=test;Database=test;",
                "test_table"
            )
    
    def test_process_ifc_file_with_azure_parameters(self):
        """Test that process_ifc_file passes Azure parameters correctly"""
        with patch.object(self.app.ifc_reader, 'load_file') as mock_load_file:
            mock_load.return_value = self.mock_spaces
            
            with patch.object(self.app.quality_analyzer, 'analyze_spaces_quality') as mock_analyze:
                mock_analyze.return_value = {"total_spaces": 2}
                
                with patch.object(self.app, '_process_standard') as mock_standard:
                    mock_standard.return_value = {"success": True, "format": "azure-sql"}
                    
                    result = self.app.process_ifc_file(
                        ifc_path="test.ifc",
                        output_path="test.json",
                        export_format="azure-sql",
                        azure_connection_string="Server=test;Database=test;",
                        azure_table_name="custom_table"
                    )
                    
                    # Verify Azure parameters were passed through
                    mock_standard.assert_called_once()
                    args = mock_standard.call_args[1] if mock_standard.call_args[1] else mock_standard.call_args[0]
                    
                    # Check if azure parameters are in the call
                    call_args = mock_standard.call_args
                    assert "Server=test;Database=test;" in str(call_args)
                    assert "custom_table" in str(call_args)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])