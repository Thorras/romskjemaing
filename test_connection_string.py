#!/usr/bin/env python3
"""
Test script for Azure SQL connection strings
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from ifc_room_schedule.export.azure_sql_exporter import AzureSQLExporter


def test_connection_string(connection_string: str):
    """Test a connection string format and connectivity."""
    print("Testing Azure SQL Connection String")
    print("=" * 50)
    print(f"Connection String: {connection_string}")
    print()
    
    try:
        # Create exporter instance
        exporter = AzureSQLExporter(connection_string)
        print("✓ Connection string format is valid")
        
        # Test actual connection
        print("Testing database connection...")
        result = exporter.test_connection()
        
        if result['connected']:
            print("✓ Successfully connected to database!")
            if result['server_info']:
                print(f"Server Info: {result['server_info']}")
        else:
            print("✗ Failed to connect to database")
            if result['error']:
                print(f"Error: {result['error']}")
                
    except ImportError as e:
        print("✗ Missing dependencies:")
        print(f"  {e}")
        print("\nInstall with: pip install pyodbc sqlalchemy")
        
    except Exception as e:
        print(f"✗ Error: {e}")


def show_connection_string_examples():
    """Show example connection strings."""
    print("Azure SQL Connection String Examples")
    print("=" * 50)
    
    exporter = AzureSQLExporter("dummy")  # Just to get template
    template = exporter.get_connection_string_template()
    
    print("1. SQLAlchemy Format (recommended):")
    print(template)
    print()
    
    print("2. Example with real values:")
    example = template.format(
        username="myuser",
        password="mypassword",
        server="myserver",
        database="mydatabase"
    )
    print(example)
    print()
    
    print("3. ODBC Format:")
    print("Server=myserver.database.windows.net;Database=mydatabase;Uid=myuser;Pwd=mypassword;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;")
    print()
    
    print("4. Local SQL Server Express:")
    print("mssql+pyodbc://./SQLEXPRESS?driver=ODBC+Driver+17+for+SQL+Server&database=TestDB&trusted_connection=yes")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        connection_string = sys.argv[1]
        test_connection_string(connection_string)
    else:
        show_connection_string_examples()
        print("\nUsage:")
        print("  python test_connection_string.py \"your_connection_string_here\"")