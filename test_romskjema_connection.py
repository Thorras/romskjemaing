#!/usr/bin/env python3
"""
Test connection to the romskjema database and demonstrate usage.
"""

import json
from ifc_room_schedule.export.azure_sql_exporter import AzureSQLExporter

def test_connection():
    """Test connection to romskjema database."""
    
    # Database connection details
    server = 'thorrasmegadata.database.windows.net'
    username = 'adminUser'
    password = 'Labbetuss99'
    database = 'romskjema'
    
    print("Testing Azure SQL Connection")
    print("=" * 30)
    print(f"Server: {server}")
    print(f"Database: {database}")
    print(f"Username: {username}")
    
    try:
        # Create exporter instance
        exporter = AzureSQLExporter.__new__(AzureSQLExporter)
        template = exporter.get_connection_string_template()
        
        connection_string = template.format(
            username=username,
            password=password,
            server='thorrasmegadata',
            database=database
        )
        
        print(f"\nConnection string: {connection_string}")
        
        # Test without actual SQL dependencies (will show ImportError)
        try:
            exporter = AzureSQLExporter(connection_string)
            print("✓ Exporter created successfully")
        except ImportError as e:
            print(f"ℹ SQL dependencies needed: {e}")
            print("To install: pip install pyodbc sqlalchemy")
            return False
        except Exception as e:
            print(f"✗ Error: {e}")
            return False
            
        # Test connection
        result = exporter.test_connection()
        
        if result['connected']:
            print("✓ Connection successful!")
            print(f"Server info: {result['server_info']}")
            
            # Create tables if they don't exist
            if exporter.create_tables():
                print("✓ Database tables ready")
            else:
                print("⚠ Could not create tables")
                
        else:
            print(f"✗ Connection failed: {result['error']}")
            return False
            
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False
    
    return True

def demonstrate_export():
    """Demonstrate how to export data to the database."""
    
    print(f"\n" + "=" * 30)
    print("Export Demonstration")
    print("=" * 30)
    
    # Load sample data from the JSON file
    try:
        with open('Soner_akkordsvingen_room_schedule.json', 'r', encoding='utf-8') as f:
            room_data = json.load(f)
        
        print(f"✓ Loaded room schedule data")
        print(f"  - Spaces: {len(room_data.get('spaces', []))}")
        print(f"  - Export date: {room_data.get('metadata', {}).get('export_date', 'N/A')}")
        
        # Show how to export (without actually doing it due to dependencies)
        print(f"\nTo export this data to Azure SQL:")
        print(f"1. Ensure SQL dependencies are installed")
        print(f"2. Create exporter with connection string")
        print(f"3. Call exporter.export_data(room_data, 'Soner Akkordsvingen')")
        
    except FileNotFoundError:
        print("ℹ Sample JSON file not found")
        print("You can export any room schedule data using the same pattern")
    except Exception as e:
        print(f"✗ Error loading sample data: {e}")

if __name__ == "__main__":
    if test_connection():
        demonstrate_export()
    else:
        print("\nPlease ensure:")
        print("1. The database 'romskjema' exists on the server")
        print("2. SQL dependencies are installed: pip install pyodbc sqlalchemy")
        print("3. Network connectivity to Azure SQL is available")