# Azure SQL Database Setup Guide

## Database Information
- **Server**: thorrasmegadata.database.windows.net
- **Username**: adminUser
- **Password**: Labbetuss99
- **Database Name**: romskjema

## Step 1: Create the Database

### Option A: Azure Portal (Recommended)
1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to SQL servers → thorrasmegadata
3. Click "Create database"
4. Set database name: `romskjema`
5. Choose appropriate pricing tier (Basic for testing)
6. Click "Create"

### Option B: Azure CLI
```bash
# Login first
az login

# Create database (replace YOUR_RESOURCE_GROUP with actual resource group)
az sql db create \
    --resource-group YOUR_RESOURCE_GROUP \
    --server thorrasmegadata \
    --name romskjema \
    --service-objective Basic
```

### Option C: SQL Command
Connect to the `master` database and run:
```sql
CREATE DATABASE romskjema;
```

## Step 2: Install Python Dependencies

```bash
pip install pyodbc sqlalchemy
```

## Step 3: Test Connection

Run the test script:
```bash
python test_romskjema_connection.py
```

## Step 4: Export Room Schedule Data

```python
from ifc_room_schedule.export.azure_sql_exporter import AzureSQLExporter
import json

# Create connection string
connection_string = "mssql+pyodbc://adminUser:Labbetuss99@thorrasmegadata.database.windows.net:1433/romskjema?driver=ODBC+Driver+17+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no&Connection+Timeout=30"

# Initialize exporter
exporter = AzureSQLExporter(connection_string)

# Load your room schedule data
with open('Soner_akkordsvingen_room_schedule.json', 'r', encoding='utf-8') as f:
    room_data = json.load(f)

# Export to database
success = exporter.export_data(room_data, "Soner Akkordsvingen Project")

if success:
    print("✓ Data exported successfully!")
else:
    print("✗ Export failed")
```

## Database Schema

The exporter will create these tables:
- `projects` - Project metadata
- `spaces` - Room/space information
- `space_quantities` - Area, volume measurements
- `surfaces` - Wall, floor, ceiling surfaces
- `space_boundaries` - Boundary relationships
- `relationships` - IFC relationships

## Troubleshooting

### Connection Issues
1. Ensure firewall allows your IP address
2. Check if database exists
3. Verify credentials are correct

### Driver Issues
If you get ODBC driver errors:
- Windows: Install "ODBC Driver 17 for SQL Server"
- Download from Microsoft's website

### Network Issues
- Check if you can ping thorrasmegadata.database.windows.net
- Ensure port 1433 is not blocked

## Security Notes
- Consider using Azure Key Vault for credentials in production
- Enable Azure AD authentication for better security
- Use connection string encryption for sensitive environments