"""
Database Configuration

Statisk konfigurasjon for Azure SQL Database tilkobling.
"""

import os
from typing import Optional


class DatabaseConfig:
    """Statisk database konfigurasjon."""
    
    # Standard Azure SQL Database konfigurasjon
    DEFAULT_SERVER = "thorrasmegadata"  # Endre til din server
    DEFAULT_DATABASE = "romskjema"
    DEFAULT_USERNAME = "adminUser"
    DEFAULT_TABLE_NAME = "room_schedule"
    
    # Connection string template
    CONNECTION_STRING_TEMPLATE = (
        "mssql+pyodbc://{username}:{password}@{server}.database.windows.net:1433/"
        "{database}?driver=ODBC+Driver+17+for+SQL+Server&Encrypt=yes&"
        "TrustServerCertificate=no&Connection+Timeout=30"
    )
    
    @classmethod
    def get_default_connection_string(cls, password: Optional[str] = None) -> str:
        """
        Få standard connection string.
        
        Args:
            password: Database passord (kan også hentes fra miljøvariabel)
            
        Returns:
            Ferdig connection string
        """
        # Prøv å hente passord fra miljøvariabel først
        if not password:
            password = os.getenv('AZURE_SQL_PASSWORD')
        
        if not password:
            raise ValueError(
                "Database passord må oppgis enten som parameter eller "
                "som miljøvariabel AZURE_SQL_PASSWORD"
            )
        
        return cls.CONNECTION_STRING_TEMPLATE.format(
            username=cls.DEFAULT_USERNAME,
            password=password,
            server=cls.DEFAULT_SERVER,
            database=cls.DEFAULT_DATABASE
        )
    
    @classmethod
    def get_custom_connection_string(cls, server: str, database: str, 
                                   username: str, password: str) -> str:
        """
        Lag tilpasset connection string.
        
        Args:
            server: Server navn (uten .database.windows.net)
            database: Database navn
            username: Brukernavn
            password: Passord
            
        Returns:
            Connection string
        """
        return cls.CONNECTION_STRING_TEMPLATE.format(
            username=username,
            password=password,
            server=server,
            database=database
        )
    
    @classmethod
    def get_local_connection_string(cls, database: str = "RomskjemaDB") -> str:
        """
        Få connection string for lokal SQL Server Express.
        
        Args:
            database: Database navn
            
        Returns:
            Connection string for lokal database
        """
        return (
            f"mssql+pyodbc://./SQLEXPRESS?driver=ODBC+Driver+17+for+SQL+Server&"
            f"database={database}&trusted_connection=yes"
        )


# Standard konfigurasjon som kan importeres direkte
DEFAULT_CONNECTION_CONFIG = {
    'server': DatabaseConfig.DEFAULT_SERVER,
    'database': DatabaseConfig.DEFAULT_DATABASE,
    'username': DatabaseConfig.DEFAULT_USERNAME,
    'table_name': DatabaseConfig.DEFAULT_TABLE_NAME
}