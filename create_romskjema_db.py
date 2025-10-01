#!/usr/bin/env python3
"""
Script to create 'romskjema' database on Azure SQL Server
and test the connection with the Azure SQL exporter.
"""

import sys
import os
import argparse
from ifc_room_schedule.export.azure_sql_exporter import AzureSQLExporter

def get_credentials():
    """Get database credentials from environment variables."""
    server = os.getenv('AZURE_SQL_SERVER', 'thorrasmegadata.database.windows.net')
    username = os.getenv('AZURE_SQL_USERNAME')
    password = os.getenv('AZURE_SQL_PASSWORD')
    
    if not username:
        raise ValueError("AZURE_SQL_USERNAME environment variable is required")
    if not password:
        raise ValueError("AZURE_SQL_PASSWORD environment variable is required")
    
    return server, username, password

def create_database_connection_string():
    """Create connection string for the romskjema database."""
    server, username, password = get_credentials()
    database = 'romskjema'
    
    # Use the exporter's template
    exporter = AzureSQLExporter.__new__(AzureSQLExporter)
    template = exporter.get_connection_string_template()
    
    # Extract server name without .database.windows.net suffix
    server_name = server.replace('.database.windows.net', '')
    
    connection_string = template.format(
        username=username,
        password=password,
        server=server_name,
        database=database
    )
    
    return connection_string

def create_master_connection_string():
    """Create connection string for the master database to create new database."""
    server, username, password = get_credentials()
    database = 'master'  # Connect to master to create new database
    
    # Use the exporter's template
    exporter = AzureSQLExporter.__new__(AzureSQLExporter)
    template = exporter.get_connection_string_template()
    
    # Extract server name without .database.windows.net suffix
    server_name = server.replace('.database.windows.net', '')
    
    connection_string = template.format(
        username=username,
        password=password,
        server=server_name,
        database=database
    )
    
    return connection_string

def main():
    print("Azure SQL Database Creation Script")
    print("=" * 40)
    
    # Check if SQL dependencies are available
    try:
        import pyodbc
        import sqlalchemy
        print("✓ SQL dependencies are available")
    except ImportError as e:
        print("✗ SQL dependencies not available")
        print("Please install: pip install pyodbc sqlalchemy")
        print(f"Error: {e}")
        return False
    
    # Generate connection strings
    master_conn_str = create_master_connection_string()
    romskjema_conn_str = create_database_connection_string()
    
    print(f"\nConnection strings generated:")
    print(f"Master DB: {master_conn_str}")
    print(f"Romskjema DB: {romskjema_conn_str}")
    
    try:
        # Try to connect to master database and create romskjema database
        print(f"\nAttempting to create 'romskjema' database...")
        
        from sqlalchemy import create_engine, text
        
        # Connect to master database
        master_engine = create_engine(master_conn_str)
        
        with master_engine.connect() as conn:
            # Check if database already exists
            result = conn.execute(text(
                "SELECT name FROM sys.databases WHERE name = 'romskjema'"
            ))
            
            if result.fetchone():
                print("✓ Database 'romskjema' already exists")
            else:
                # Create the database
                # Note: CREATE DATABASE cannot be used in a transaction
                conn.execute(text("CREATE DATABASE romskjema"))
                conn.commit()
                print("✓ Database 'romskjema' created successfully")
        
        # Test connection to the new database
        print(f"\nTesting connection to 'romskjema' database...")
        
        try:
            exporter = AzureSQLExporter(romskjema_conn_str)
            test_result = exporter.test_connection()
            
            if test_result['connected']:
                print("✓ Successfully connected to 'romskjema' database")
                print(f"Server info: {test_result['server_info']}")
                
                # Create tables
                print(f"\nCreating tables...")
                if exporter.create_tables():
                    print("✓ Tables created successfully")
                else:
                    print("✗ Failed to create tables")
                    
            else:
                print(f"✗ Failed to connect: {test_result['error']}")
                
        except Exception as e:
            print(f"✗ Error testing connection: {e}")
            
    except Exception as e:
        print(f"✗ Error creating database: {e}")
        print("\nAlternative options:")
        print("1. Use Azure Portal to create the database manually")
        print("2. Use Azure CLI: az sql db create")
        print("3. Use SQL Server Management Studio")
        return False
    
    print(f"\n" + "=" * 40)
    print("Database setup completed!")
    print("You can now use the Azure SQL exporter with your room schedule data.")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)