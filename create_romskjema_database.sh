#!/bin/bash
# Script to create romskjema database on Azure SQL Server

# Set variables
SERVER_NAME="thorrasmegadata"
DATABASE_NAME="romskjema"
RESOURCE_GROUP="your-resource-group-name"  # Replace with your actual resource group

# Login to Azure (you'll need to do this first)
echo "Please run: az login"
echo ""

# Create the database
echo "Creating database '$DATABASE_NAME' on server '$SERVER_NAME'..."
az sql db create \
    --resource-group $RESOURCE_GROUP \
    --server $SERVER_NAME \
    --name $DATABASE_NAME \
    --service-objective Basic \
    --backup-storage-redundancy Local

echo "Database creation command executed."
echo "Check Azure Portal to verify the database was created successfully."