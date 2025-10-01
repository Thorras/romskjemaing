#!/usr/bin/env python3
"""
Setup script for database configuration
"""

import os
from pathlib import Path


def setup_database_config():
    """Set up database configuration."""
    print("Romskjema Database Configuration Setup")
    print("=" * 50)
    
    print("\nChoose database configuration:")
    print("1. Azure SQL Database (cloud)")
    print("2. Local SQL Server Express")
    print("3. Custom configuration")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        setup_azure_sql()
    elif choice == "2":
        setup_local_sql()
    elif choice == "3":
        setup_custom_config()
    else:
        print("Invalid choice. Exiting.")


def setup_azure_sql():
    """Set up Azure SQL configuration."""
    print("\nAzure SQL Database Setup")
    print("-" * 30)
    
    server = input("Server name (without .database.windows.net): ").strip()
    database = input("Database name: ").strip()
    username = input("Username: ").strip()
    password = input("Password: ").strip()
    
    if not all([server, database, username, password]):
        print("All fields are required!")
        return
    
    # Update config file
    config_file = Path("config/database_config.py")
    if config_file.exists():
        content = config_file.read_text()
        
        # Replace default values
        content = content.replace('DEFAULT_SERVER = "romskjema-server"', f'DEFAULT_SERVER = "{server}"')
        content = content.replace('DEFAULT_DATABASE = "romskjema_db"', f'DEFAULT_DATABASE = "{database}"')
        content = content.replace('DEFAULT_USERNAME = "romskjema_user"', f'DEFAULT_USERNAME = "{username}"')
        
        config_file.write_text(content)
        
        # Set environment variable for password
        print(f"\nConfiguration updated!")
        print(f"Set environment variable: AZURE_SQL_PASSWORD={password}")
        print("\nOn Windows: set AZURE_SQL_PASSWORD=" + password)
        print("On Linux/Mac: export AZURE_SQL_PASSWORD=" + password)
        
        # Create .env file
        env_file = Path(".env")
        env_content = f"AZURE_SQL_PASSWORD={password}\n"
        if env_file.exists():
            existing = env_file.read_text()
            if "AZURE_SQL_PASSWORD" not in existing:
                env_file.write_text(existing + env_content)
        else:
            env_file.write_text(env_content)
        
        print(f"\nPassword saved to .env file")
        print("Configuration complete!")


def setup_local_sql():
    """Set up local SQL Server Express configuration."""
    print("\nLocal SQL Server Express Setup")
    print("-" * 35)
    
    database = input("Database name (default: RomskjemaDB): ").strip()
    if not database:
        database = "RomskjemaDB"
    
    print(f"\nLocal database configuration:")
    print(f"Server: .\\SQLEXPRESS")
    print(f"Database: {database}")
    print(f"Authentication: Windows Authentication")
    
    print("\nTo use local database, run:")
    print("python main.py --input file.ifc --format azure-sql --local-db")


def setup_custom_config():
    """Set up custom configuration."""
    print("\nCustom Configuration")
    print("-" * 20)
    
    print("Edit config/database_config.py manually to set your custom configuration.")
    print("You can also use environment variables:")
    print("- AZURE_SQL_PASSWORD")
    print("- AZURE_SQL_SERVER")
    print("- AZURE_SQL_DATABASE")
    print("- AZURE_SQL_USERNAME")


def test_configuration():
    """Test the current configuration."""
    print("\nTesting Configuration")
    print("-" * 25)
    
    try:
        from config.database_config import DatabaseConfig
        
        # Try to get default connection string
        try:
            conn_str = DatabaseConfig.get_default_connection_string()
            print("✓ Default configuration is valid")
            print(f"Connection string: {conn_str[:50]}...")
        except ValueError as e:
            print(f"✗ Configuration error: {e}")
            
    except ImportError as e:
        print(f"✗ Import error: {e}")


if __name__ == "__main__":
    setup_database_config()
    
    print("\n" + "=" * 50)
    test_configuration()
    
    print("\nNext steps:")
    print("1. Run the application: python run_app.bat")
    print("2. Load an IFC file")
    print("3. Choose 'Azure SQL' export format")
    print("4. Check 'Use default database configuration'")
    print("5. Export your data!")