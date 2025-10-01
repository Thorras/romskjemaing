"""
Test cases for Azure SQL exporter functionality.
"""

import pytest
from unittest.mock import Mock, patch
import json
from datetime import datetime

from ifc_room_schedule.export.azure_sql_exporter import AzureSQLExporter


class TestAzureSQLExporter:
    """Test cases for AzureSQLExporter."""
    
    def test_import_without_dependencies(self):
        """Test that exporter raises ImportError when SQL dependencies are not available."""
        with patch('ifc_room_schedule.export.azure_sql_exporter.SQL_AVAILABLE', False):
            with pytest.raises(ImportError) as exc_info:
                AzureSQLExporter("test_connection_string")
            assert "SQL dependencies not available" in str(exc_info.value)
    
    def test_connection_string_template(self):
        """Test connection string template generation."""
        # Create exporter without calling __init__ to avoid dependency check
        exporter = AzureSQLExporter.__new__(AzureSQLExporter)
        template = exporter.get_connection_string_template()
        
        expected = (
            "mssql+pyodbc://{username}:{password}@{server}.database.windows.net:1433/"
            "{database}?driver=ODBC+Driver+17+for+SQL+Server&Encrypt=yes&"
            "TrustServerCertificate=no&Connection+Timeout=30"
        )
        assert template == expected
    
    def test_class_attributes_exist(self):
        """Test that the class has the expected methods and attributes."""
        # Test without instantiating to avoid dependency issues
        assert hasattr(AzureSQLExporter, 'connect')
        assert hasattr(AzureSQLExporter, 'create_tables')
        assert hasattr(AzureSQLExporter, 'export_data')
        assert hasattr(AzureSQLExporter, 'test_connection')
        assert hasattr(AzureSQLExporter, 'get_connection_string_template')
        assert callable(getattr(AzureSQLExporter, 'connect'))
        assert callable(getattr(AzureSQLExporter, 'create_tables'))
        assert callable(getattr(AzureSQLExporter, 'export_data'))
        assert callable(getattr(AzureSQLExporter, 'test_connection'))
        assert callable(getattr(AzureSQLExporter, 'get_connection_string_template'))
    
    def test_connection_string_format(self):
        """Test that connection string template has correct format."""
        exporter = AzureSQLExporter.__new__(AzureSQLExporter)
        template = exporter.get_connection_string_template()
        
        # Check that template contains expected placeholders
        assert '{username}' in template
        assert '{password}' in template
        assert '{server}' in template
        assert '{database}' in template
        assert 'database.windows.net' in template
        assert 'ODBC+Driver+17+for+SQL+Server' in template
        assert 'Encrypt=yes' in template
