"""
Output manager for IFC Floor Plan Generator.

Handles file naming, path sanitization, directory creation, and file writing operations.
"""

import os
import re
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from ..models import Config
from ..errors.handler import ErrorHandler
from ..errors.exceptions import WriteFailedError, ProcessingError


class OutputManager:
    """Manages file output operations including naming, path creation, and writing."""
    
    def __init__(self, config: Config):
        """Initialize output manager with configuration.
        
        Args:
            config: Main configuration containing output settings
        """
        self.config = config
        self._logger = logging.getLogger(__name__)
        self._error_handler = ErrorHandler()
        
        # Ensure output directory exists
        self._ensure_output_directory()
    
    def generate_svg_filename(self, storey_name: str, index: int) -> str:
        """Generate SVG filename using the configured pattern.
        
        Args:
            storey_name: Name of the building storey
            index: Index number for the storey
            
        Returns:
            str: Generated filename following the pattern
        """
        # Sanitize storey name
        sanitized_name = self.sanitize_filename(storey_name)
        
        # Apply filename pattern
        filename = self.config.output.svg_filename_pattern.format(
            index=index,
            storey_name=sanitized_name
        )
        
        self._logger.debug(f"Generated SVG filename: {filename}")
        return filename
    
    def generate_geojson_filename(self, storey_name: str, index: int) -> str:
        """Generate GeoJSON filename using the configured pattern.
        
        Args:
            storey_name: Name of the building storey
            index: Index number for the storey
            
        Returns:
            str: Generated filename following the pattern
        """
        # Sanitize storey name
        sanitized_name = self.sanitize_filename(storey_name)
        
        # Apply filename pattern
        filename = self.config.output.geojson_filename_pattern.format(
            index=index,
            storey_name=sanitized_name
        )
        
        self._logger.debug(f"Generated GeoJSON filename: {filename}")
        return filename
    
    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename by replacing invalid characters.
        
        Replaces slashes, colons, and other problematic characters with underscores.
        
        Args:
            filename: Original filename to sanitize
            
        Returns:
            str: Sanitized filename safe for filesystem use
        """
        if not filename:
            return "unnamed"
        
        # Replace problematic characters with underscores
        # This includes: / \ : * ? " < > | and control characters
        sanitized = re.sub(r'[/\\:*?"<>|\x00-\x1f\x7f]', '_', filename)
        
        # Replace multiple consecutive underscores with single underscore
        sanitized = re.sub(r'_+', '_', sanitized)
        
        # Remove leading/trailing underscores and whitespace
        sanitized = sanitized.strip('_ ')
        
        # Ensure filename is not empty after sanitization
        if not sanitized:
            sanitized = "unnamed"
        
        # Limit length to reasonable filesystem limits
        if len(sanitized) > 200:
            sanitized = sanitized[:200]
        
        self._logger.debug(f"Sanitized filename: '{filename}' -> '{sanitized}'")
        return sanitized
    
    def get_full_path(self, filename: str) -> str:
        """Get full path for a filename in the output directory.
        
        Args:
            filename: Filename to get full path for
            
        Returns:
            str: Full path to the file
        """
        return os.path.join(self.config.output_dir, filename)
    
    def write_svg_file(self, svg_content: str, filename: str) -> str:
        """Write SVG content to file.
        
        Args:
            svg_content: SVG content as string
            filename: Filename to write to
            
        Returns:
            str: Full path to the written file
            
        Raises:
            WriteFailedError: If file writing fails
        """
        full_path = self.get_full_path(filename)
        
        try:
            # Ensure parent directory exists
            parent_dir = os.path.dirname(full_path)
            if parent_dir and not os.path.exists(parent_dir):
                os.makedirs(parent_dir, exist_ok=True)
            
            # Write SVG content
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(svg_content)
            
            self._logger.info(f"Successfully wrote SVG file: {full_path}")
            return full_path
            
        except PermissionError as e:
            raise WriteFailedError(
                file_path=full_path,
                original_error=e
            )
        except OSError as e:
            raise WriteFailedError(
                file_path=full_path,
                original_error=e
            )
        except Exception as e:
            raise WriteFailedError(
                file_path=full_path,
                original_error=e
            )
    
    def write_geojson_file(self, geojson_content: str, filename: str) -> str:
        """Write GeoJSON content to file.
        
        Args:
            geojson_content: GeoJSON content as string
            filename: Filename to write to
            
        Returns:
            str: Full path to the written file
            
        Raises:
            WriteFailedError: If file writing fails
        """
        full_path = self.get_full_path(filename)
        
        try:
            # Ensure parent directory exists
            parent_dir = os.path.dirname(full_path)
            if parent_dir and not os.path.exists(parent_dir):
                os.makedirs(parent_dir, exist_ok=True)
            
            # Write GeoJSON content
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(geojson_content)
            
            self._logger.info(f"Successfully wrote GeoJSON file: {full_path}")
            return full_path
            
        except PermissionError as e:
            raise WriteFailedError(
                file_path=full_path,
                original_error=e
            )
        except OSError as e:
            raise WriteFailedError(
                file_path=full_path,
                original_error=e
            )
        except Exception as e:
            raise WriteFailedError(
                file_path=full_path,
                original_error=e
            )
    
    def write_manifest_file(self, manifest_content: str, filename: Optional[str] = None) -> str:
        """Write manifest content to file.
        
        Args:
            manifest_content: Manifest content as JSON string
            filename: Optional custom filename, uses config default if None
            
        Returns:
            str: Full path to the written file
            
        Raises:
            WriteFailedError: If file writing fails
        """
        if filename is None:
            filename = self.config.output.manifest_filename
        
        full_path = self.get_full_path(filename)
        
        try:
            # Ensure parent directory exists
            parent_dir = os.path.dirname(full_path)
            if parent_dir and not os.path.exists(parent_dir):
                os.makedirs(parent_dir, exist_ok=True)
            
            # Write manifest content
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(manifest_content)
            
            self._logger.info(f"Successfully wrote manifest file: {full_path}")
            return full_path
            
        except PermissionError as e:
            raise WriteFailedError(
                file_path=full_path,
                original_error=e
            )
        except OSError as e:
            raise WriteFailedError(
                file_path=full_path,
                original_error=e
            )
        except Exception as e:
            raise WriteFailedError(
                file_path=full_path,
                original_error=e
            )
    
    def _ensure_output_directory(self) -> None:
        """Ensure the output directory exists.
        
        Raises:
            ProcessingError: If directory creation fails
        """
        try:
            if not os.path.exists(self.config.output_dir):
                os.makedirs(self.config.output_dir, exist_ok=True)
                self._logger.info(f"Created output directory: {self.config.output_dir}")
            else:
                self._logger.debug(f"Output directory exists: {self.config.output_dir}")
                
        except PermissionError as e:
            raise ProcessingError(
                error_code="OUTPUT_DIR_FAILED",
                message=f"Kunne ikke lage output-mappe: {self.config.output_dir}",
                context={"output_dir": self.config.output_dir, "error": str(e)}
            )
        except Exception as e:
            raise ProcessingError(
                error_code="OUTPUT_DIR_FAILED", 
                message=f"Feil ved opprettelse av output-mappe: {str(e)}",
                context={"output_dir": self.config.output_dir, "error": str(e)}
            )
    
    def check_write_permissions(self) -> bool:
        """Check if we have write permissions to the output directory.
        
        Returns:
            bool: True if we can write to the output directory
        """
        try:
            # Try to create a temporary file
            test_file = os.path.join(self.config.output_dir, '.write_test')
            with open(test_file, 'w') as f:
                f.write('test')
            
            # Clean up test file
            os.remove(test_file)
            return True
            
        except Exception as e:
            self._logger.warning(f"No write permission to output directory: {e}")
            return False
    
    def get_output_info(self) -> Dict[str, Any]:
        """Get information about output configuration and status.
        
        Returns:
            Dict containing output information
        """
        return {
            "output_dir": self.config.output_dir,
            "svg_pattern": self.config.output.svg_filename_pattern,
            "geojson_pattern": self.config.output.geojson_filename_pattern,
            "manifest_filename": self.config.output.manifest_filename,
            "write_geojson": self.config.output.write_geojson,
            "directory_exists": os.path.exists(self.config.output_dir),
            "write_permissions": self.check_write_permissions()
        }
    
    def list_output_files(self) -> Dict[str, list]:
        """List existing output files in the output directory.
        
        Returns:
            Dict with lists of existing files by type
        """
        if not os.path.exists(self.config.output_dir):
            return {"svg": [], "geojson": [], "manifest": [], "other": []}
        
        files = {"svg": [], "geojson": [], "manifest": [], "other": []}
        
        try:
            for filename in os.listdir(self.config.output_dir):
                file_path = os.path.join(self.config.output_dir, filename)
                if os.path.isfile(file_path):
                    if filename.endswith('.svg'):
                        files["svg"].append(filename)
                    elif filename.endswith('.geo.json') or filename.endswith('.geojson'):
                        files["geojson"].append(filename)
                    elif filename == self.config.output.manifest_filename:
                        files["manifest"].append(filename)
                    else:
                        files["other"].append(filename)
        except Exception as e:
            self._logger.warning(f"Could not list output files: {e}")
        
        return files