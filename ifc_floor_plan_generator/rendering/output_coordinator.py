"""
Output coordinator for IFC Floor Plan Generator.

Coordinates all output file generation including SVG, GeoJSON, and manifest files.
Ensures consistent filename patterns and unified pipeline integration.
"""

import logging
from typing import List, Dict, Any, Optional
from ..models import StoreyResult, Config
from .svg_renderer import SVGRenderer
from .geojson_renderer import GeoJSONRenderer
from .manifest_generator import ManifestGenerator
from .output_manager import OutputManager
from ..errors.handler import ErrorHandler
from ..errors.exceptions import ProcessingError


class OutputCoordinator:
    """Coordinates all output file generation with consistent patterns and organization."""
    
    def __init__(self, config: Config):
        """Initialize output coordinator with configuration.
        
        Args:
            config: Main configuration containing all output settings
        """
        self.config = config
        self._logger = logging.getLogger(__name__)
        self._error_handler = ErrorHandler()
        
        # Initialize renderers and managers
        self.svg_renderer = SVGRenderer(config.rendering)
        self.geojson_renderer = GeoJSONRenderer(config)
        self.manifest_generator = ManifestGenerator()
        self.output_manager = OutputManager(config)
    
    def generate_all_outputs(
        self, 
        storeys: List[StoreyResult], 
        input_file: str,
        processing_time: float
    ) -> Dict[str, Any]:
        """Generate all output files for processed storeys.
        
        Args:
            storeys: List of processed storey results
            input_file: Path to the input IFC file
            processing_time: Total processing time in seconds
            
        Returns:
            Dict[str, Any]: Summary of generated files and metadata
            
        Raises:
            ProcessingError: If output generation fails
        """
        try:
            output_summary = {
                "svg_files": [],
                "geojson_files": [],
                "manifest_file": None,
                "total_files": 0,
                "errors": []
            }
            
            # Generate SVG and GeoJSON files for each storey
            for index, storey in enumerate(storeys):
                try:
                    # Generate SVG file
                    svg_file = self._generate_svg_for_storey(storey, index)
                    if svg_file:
                        output_summary["svg_files"].append(svg_file)
                        storey.svg_file = svg_file
                    
                    # Generate GeoJSON file (conditional)
                    geojson_file = self._generate_geojson_for_storey(storey, index)
                    if geojson_file:
                        output_summary["geojson_files"].append(geojson_file)
                        storey.geojson_file = geojson_file
                        
                except Exception as e:
                    error_msg = f"Failed to generate outputs for storey {storey.storey_name}: {e}"
                    self._logger.error(error_msg)
                    output_summary["errors"].append(error_msg)
            
            # Generate manifest file
            try:
                manifest_file = self.manifest_generator.generate_and_save_manifest(
                    storeys, self.config, input_file, processing_time, self.output_manager
                )
                output_summary["manifest_file"] = manifest_file
            except Exception as e:
                error_msg = f"Failed to generate manifest: {e}"
                self._logger.error(error_msg)
                output_summary["errors"].append(error_msg)
            
            # Calculate total files generated
            output_summary["total_files"] = (
                len(output_summary["svg_files"]) + 
                len(output_summary["geojson_files"]) + 
                (1 if output_summary["manifest_file"] else 0)
            )
            
            self._logger.info(f"Generated {output_summary['total_files']} output files")
            return output_summary
            
        except Exception as e:
            self._logger.error(f"Output coordination failed: {e}")
            raise ProcessingError(
                error_code="OUTPUT_COORDINATION_FAILED",
                message=f"Output-koordinering feilet: {str(e)}",
                context={
                    "input_file": input_file,
                    "storey_count": len(storeys),
                    "error": str(e)
                }
            )
    
    def _generate_svg_for_storey(self, storey: StoreyResult, index: int) -> Optional[str]:
        """Generate SVG file for a single storey.
        
        Args:
            storey: StoreyResult containing storey data
            index: Index for filename generation
            
        Returns:
            Optional[str]: Path to generated SVG file, or None if generation fails
        """
        try:
            if not storey.polylines:
                self._logger.debug(f"No polylines to render for storey {storey.storey_name}")
                return None
            
            # Set viewport based on storey bounds
            if storey.bounds:
                self.svg_renderer.set_viewport(storey.bounds)
            
            # Create metadata for SVG
            metadata = {
                "title": f"Floor Plan - {storey.storey_name}",
                "description": f"IFC floor plan for storey {storey.storey_name} at cut height {storey.cut_height}m",
                "storey_name": storey.storey_name,
                "cut_height": storey.cut_height,
                "element_count": storey.element_count,
                "created_at": "Generated by IFC Floor Plan Generator"
            }
            
            # Render and save SVG
            svg_file = self.svg_renderer.render_and_save(
                storey.polylines, 
                self.output_manager, 
                storey.storey_name, 
                index, 
                metadata
            )
            
            self._logger.debug(f"Generated SVG for storey {storey.storey_name}: {svg_file}")
            return svg_file
            
        except Exception as e:
            self._logger.error(f"SVG generation failed for storey {storey.storey_name}: {e}")
            return None
    
    def _generate_geojson_for_storey(self, storey: StoreyResult, index: int) -> Optional[str]:
        """Generate GeoJSON file for a single storey (conditional).
        
        Args:
            storey: StoreyResult containing storey data
            index: Index for filename generation
            
        Returns:
            Optional[str]: Path to generated GeoJSON file, or None if generation is disabled/fails
        """
        try:
            # Check if GeoJSON generation is enabled
            if not self.geojson_renderer.should_generate_geojson():
                return None
            
            if not storey.polylines:
                self._logger.debug(f"No polylines to render for storey {storey.storey_name}")
                return None
            
            # Create metadata for GeoJSON
            metadata = {
                "storey_name": storey.storey_name,
                "cut_height": storey.cut_height,
                "element_count": storey.element_count,
                "created_at": "Generated by IFC Floor Plan Generator"
            }
            
            # Render and save GeoJSON conditionally
            geojson_file = self.geojson_renderer.render_and_save_conditional(
                storey.polylines,
                self.output_manager,
                storey.storey_name,
                index,
                metadata
            )
            
            if geojson_file:
                self._logger.debug(f"Generated GeoJSON for storey {storey.storey_name}: {geojson_file}")
            
            return geojson_file
            
        except Exception as e:
            self._logger.error(f"GeoJSON generation failed for storey {storey.storey_name}: {e}")
            return None
    
    def ensure_consistent_filenames(self, storeys: List[StoreyResult]) -> None:
        """Ensure all output files follow consistent filename patterns.
        
        Args:
            storeys: List of storey results to check filename consistency
        """
        for index, storey in enumerate(storeys):
            # Check SVG filename consistency
            if storey.svg_file:
                expected_svg = self.output_manager.generate_svg_filename(storey.storey_name, index)
                expected_path = self.output_manager.get_full_path(expected_svg)
                if storey.svg_file != expected_path:
                    self._logger.warning(f"SVG filename inconsistency for {storey.storey_name}")
            
            # Check GeoJSON filename consistency
            if storey.geojson_file:
                expected_geojson = self.output_manager.generate_geojson_filename(storey.storey_name, index)
                expected_path = self.output_manager.get_full_path(expected_geojson)
                if storey.geojson_file != expected_path:
                    self._logger.warning(f"GeoJSON filename inconsistency for {storey.storey_name}")
    
    def get_output_organization_info(self) -> Dict[str, Any]:
        """Get information about output file organization.
        
        Returns:
            Dict[str, Any]: Output organization information
        """
        return {
            "output_manager_info": self.output_manager.get_output_info(),
            "svg_renderer_viewport": self.svg_renderer.get_viewport_info(),
            "geojson_config": self.geojson_renderer.get_configuration_summary(),
            "existing_files": self.output_manager.list_output_files()
        }
    
    def validate_output_configuration(self) -> Dict[str, Any]:
        """Validate output configuration for potential issues.
        
        Returns:
            Dict[str, Any]: Validation results with warnings and errors
        """
        validation_results = {
            "valid": True,
            "warnings": [],
            "errors": []
        }
        
        # Check output directory permissions
        if not self.output_manager.check_write_permissions():
            validation_results["valid"] = False
            validation_results["errors"].append("No write permissions to output directory")
        
        # Check filename patterns
        try:
            test_svg = self.output_manager.generate_svg_filename("Test_Storey", 1)
            test_geojson = self.output_manager.generate_geojson_filename("Test_Storey", 1)
        except Exception as e:
            validation_results["valid"] = False
            validation_results["errors"].append(f"Invalid filename patterns: {e}")
        
        # Check GeoJSON configuration consistency
        geojson_config = self.geojson_renderer.get_configuration_summary()
        if not geojson_config["config_loaded"]:
            validation_results["warnings"].append("GeoJSON renderer has no configuration loaded")
        
        return validation_results
    
    def cleanup_output_directory(self, keep_manifest: bool = True) -> Dict[str, int]:
        """Clean up output directory by removing old files.
        
        Args:
            keep_manifest: Whether to keep existing manifest files
            
        Returns:
            Dict[str, int]: Count of files removed by type
        """
        cleanup_results = {
            "svg_removed": 0,
            "geojson_removed": 0,
            "manifest_removed": 0,
            "other_removed": 0
        }
        
        try:
            existing_files = self.output_manager.list_output_files()
            
            # Remove SVG files
            for svg_file in existing_files["svg"]:
                file_path = self.output_manager.get_full_path(svg_file)
                try:
                    import os
                    os.remove(file_path)
                    cleanup_results["svg_removed"] += 1
                except Exception as e:
                    self._logger.warning(f"Could not remove SVG file {svg_file}: {e}")
            
            # Remove GeoJSON files
            for geojson_file in existing_files["geojson"]:
                file_path = self.output_manager.get_full_path(geojson_file)
                try:
                    import os
                    os.remove(file_path)
                    cleanup_results["geojson_removed"] += 1
                except Exception as e:
                    self._logger.warning(f"Could not remove GeoJSON file {geojson_file}: {e}")
            
            # Remove manifest files if requested
            if not keep_manifest:
                for manifest_file in existing_files["manifest"]:
                    file_path = self.output_manager.get_full_path(manifest_file)
                    try:
                        import os
                        os.remove(file_path)
                        cleanup_results["manifest_removed"] += 1
                    except Exception as e:
                        self._logger.warning(f"Could not remove manifest file {manifest_file}: {e}")
            
            self._logger.info(f"Cleanup completed: {sum(cleanup_results.values())} files removed")
            
        except Exception as e:
            self._logger.error(f"Cleanup failed: {e}")
        
        return cleanup_results