"""
IFC File Reader

Handles reading and basic validation of IFC files using IfcOpenShell.
"""

import os
from typing import Tuple, Optional
import ifcopenshell
import ifcopenshell.util.element


class IfcFileReader:
    """Handles IFC file loading and validation using IfcOpenShell."""

    def __init__(self):
        self.ifc_file = None
        self.file_path = None

    def load_file(self, file_path: str) -> Tuple[bool, str]:
        """
        Load and validate an IFC file.

        Args:
            file_path: Path to the IFC file

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                return False, f"File not found: {file_path}"

            # Check file extension
            if not file_path.lower().endswith(('.ifc', '.ifcxml')):
                return False, ("Invalid file format. Please select an IFC "
                               "or IFCXML file.")

            # Check file size (warn if very large)
            file_size = os.path.getsize(file_path)
            if file_size > 100 * 1024 * 1024:  # 100MB
                size_mb = file_size / (1024*1024)
                return False, (f"File is very large ({size_mb:.1f}MB). "
                               f"This may cause performance issues.")

            # Try to open with IfcOpenShell
            self.ifc_file = ifcopenshell.open(file_path)
            self.file_path = file_path

            # Basic validation - check if file has any entities
            if len(self.ifc_file.by_type("IfcProduct")) == 0:
                self.ifc_file = None
                self.file_path = None
                return False, ("IFC file appears to be empty or contains no "
                               "building elements.")

            # Check for IfcSpace entities specifically
            spaces = self.ifc_file.by_type("IfcSpace")
            if len(spaces) == 0:
                self.ifc_file = None
                self.file_path = None
                return False, ("No IfcSpace entities found in the file. "
                               "This file may not contain room/space data.")

            return True, (f"Successfully loaded IFC file with "
                          f"{len(spaces)} spaces found.")

        except Exception as e:
            self.ifc_file = None
            self.file_path = None
            return False, f"Error loading IFC file: {str(e)}"

    def validate_file(self, file_path: str) -> Tuple[bool, str]:
        """
        Validate an IFC file without loading it into memory.

        Args:
            file_path: Path to the IFC file

        Returns:
            Tuple of (is_valid: bool, message: str)
        """
        try:
            # Basic file checks
            if not os.path.exists(file_path):
                return False, "File does not exist"

            if not file_path.lower().endswith(('.ifc', '.ifcxml')):
                return False, "Not an IFC file format"

            # Try to open and do basic validation
            test_file = ifcopenshell.open(file_path)

            # Check IFC schema version
            schema = test_file.schema
            if schema not in ['IFC2X3', 'IFC4', 'IFC4X1', 'IFC4X3']:
                return False, f"Unsupported IFC schema: {schema}"

            # Check for required entities
            if len(test_file.by_type("IfcSpace")) == 0:
                return False, "No IfcSpace entities found"

            return True, f"Valid IFC file (Schema: {schema})"

        except Exception as e:
            return False, f"Invalid IFC file: {str(e)}"

    def get_file_info(self) -> Optional[dict]:
        """
        Get information about the loaded IFC file.

        Returns:
            Dictionary with file information or None if no file loaded
        """
        if not self.ifc_file:
            return None

        try:
            # Get basic file information
            info = {
                'file_path': self.file_path,
                'schema': self.ifc_file.schema,
                'total_entities': len(self.ifc_file),
                'spaces_count': len(self.ifc_file.by_type("IfcSpace")),
                'building_elements': len(
                    self.ifc_file.by_type("IfcBuildingElement")
                ),
            }

            # Try to get project information
            projects = self.ifc_file.by_type("IfcProject")
            if projects:
                project = projects[0]
                info['project_name'] = getattr(project, 'Name', 'Unknown')
                info['project_description'] = getattr(
                    project, 'Description', ''
                )

            # Get application info if available
            applications = self.ifc_file.by_type("IfcApplication")
            if applications:
                app = applications[0]
                info['created_by'] = getattr(
                    app, 'ApplicationFullName', 'Unknown'
                )
                info['version'] = getattr(app, 'Version', 'Unknown')

            return info

        except Exception as e:
            return {'error': f"Error getting file info: {str(e)}"}

    def is_loaded(self) -> bool:
        """Check if an IFC file is currently loaded."""
        return self.ifc_file is not None

    def get_ifc_file(self):
        """Get the loaded IfcOpenShell file object."""
        return self.ifc_file

    def close_file(self):
        """Close the currently loaded IFC file."""
        self.ifc_file = None
        self.file_path = None