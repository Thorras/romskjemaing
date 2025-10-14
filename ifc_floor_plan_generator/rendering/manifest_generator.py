"""
Manifest generator for IFC Floor Plan Generator.

Generates comprehensive manifest files with processing metadata, storey information, 
and configuration snapshots for reproducibility.
"""

import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
from ..models import StoreyResult, ManifestData, Config
from ..errors.handler import ErrorHandler
from ..errors.exceptions import ProcessingError


class ManifestGenerator:
    """Generates manifest files with processing metadata."""
    
    def __init__(self):
        """Initialize manifest generator."""
        self._logger = logging.getLogger(__name__)
        self._error_handler = ErrorHandler()
    
    def generate_manifest(
        self, 
        storeys: List[StoreyResult], 
        config: Config,
        input_file: str,
        processing_time: float
    ) -> ManifestData:
        """Generate manifest data from processing results.
        
        Args:
            storeys: List of processed storey results
            config: Configuration used for processing
            input_file: Path to the input IFC file
            processing_time: Total processing time in seconds
            
        Returns:
            ManifestData: Complete manifest data structure
            
        Raises:
            ProcessingError: If manifest generation fails
        """
        try:
            # Calculate total elements across all storeys
            total_elements = sum(storey.element_count for storey in storeys)
            
            # Create storey metadata list
            storey_metadata_list = []
            for storey in storeys:
                storey_metadata = self.create_storey_metadata(storey)
                storey_metadata_list.append(storey_metadata)
            
            # Create configuration snapshot
            config_snapshot = self.create_config_snapshot(config)
            
            # Create manifest data
            manifest = ManifestData(
                input_file=input_file,
                generated_at=datetime.now(),
                storeys=storey_metadata_list,
                config_used=config_snapshot,
                total_elements=total_elements,
                processing_time_seconds=processing_time
            )
            
            self._logger.info(f"Generated manifest for {len(storeys)} storeys with {total_elements} total elements")
            return manifest
            
        except Exception as e:
            self._logger.error(f"Manifest generation failed: {e}")
            raise ProcessingError(
                error_code="MANIFEST_GENERATION_FAILED",
                message=f"Manifest-generering feilet: {str(e)}",
                context={
                    "input_file": input_file,
                    "storey_count": len(storeys),
                    "error": str(e)
                }
            )
    
    def create_storey_metadata(self, storey: StoreyResult) -> Dict[str, Any]:
        """Create metadata dictionary for a storey.
        
        Args:
            storey: StoreyResult containing storey processing results
            
        Returns:
            Dict[str, Any]: Comprehensive storey metadata
        """
        # Basic storey information
        metadata = {
            "name": storey.storey_name,
            "cut_height": storey.cut_height,
            "element_count": storey.element_count,
            "polyline_count": len(storey.polylines)
        }
        
        # Bounding box information
        if storey.bounds:
            metadata["bounds"] = {
                "min_x": storey.bounds.min_x,
                "min_y": storey.bounds.min_y,
                "max_x": storey.bounds.max_x,
                "max_y": storey.bounds.max_y,
                "width": storey.bounds.width,
                "height": storey.bounds.height,
                "center": storey.bounds.center
            }
        else:
            metadata["bounds"] = None
        
        # Output file references
        metadata["output_files"] = {}
        if storey.svg_file:
            metadata["output_files"]["svg"] = storey.svg_file
        if storey.geojson_file:
            metadata["output_files"]["geojson"] = storey.geojson_file
        
        # Polyline statistics
        if storey.polylines:
            metadata["polyline_statistics"] = self._calculate_polyline_statistics(storey.polylines)
        
        # IFC class distribution
        metadata["ifc_class_distribution"] = self._calculate_ifc_class_distribution(storey.polylines)
        
        return metadata
    
    def create_config_snapshot(self, config: Config) -> Dict[str, Any]:
        """Create configuration snapshot for reproducibility.
        
        Args:
            config: Configuration object to snapshot
            
        Returns:
            Dict[str, Any]: Complete configuration snapshot
        """
        snapshot = {
            # Basic configuration
            "input_path": config.input_path,
            "output_dir": config.output_dir,
            "cut_offset_m": config.cut_offset_m,
            
            # Per-storey overrides
            "per_storey_overrides": {
                name: {
                    "cut_offset_m": override.cut_offset_m
                }
                for name, override in config.per_storey_overrides.items()
            },
            
            # Class filters
            "class_filters": {
                "include_ifc_classes": config.class_filters.include_ifc_classes,
                "exclude_ifc_classes": config.class_filters.exclude_ifc_classes
            },
            
            # Units configuration
            "units": {
                "auto_detect_units": config.units.auto_detect_units,
                "unit_scale_to_m": config.units.unit_scale_to_m
            },
            
            # Geometry configuration
            "geometry": {
                "use_world_coords": config.geometry.use_world_coords,
                "subtract_openings": config.geometry.subtract_openings,
                "sew_shells": config.geometry.sew_shells,
                "cache_geometry": config.geometry.cache_geometry
            },
            
            # Tolerances
            "tolerances": {
                "slice_tol": config.tolerances.slice_tol,
                "chain_tol": config.tolerances.chain_tol
            },
            
            # Rendering configuration
            "rendering": {
                "default_color": config.rendering.default_color,
                "default_linewidth_px": config.rendering.default_linewidth_px,
                "background": config.rendering.background,
                "invert_y": config.rendering.invert_y,
                "class_styles": config.rendering.class_styles
            },
            
            # Output configuration
            "output": {
                "svg_filename_pattern": config.output.svg_filename_pattern,
                "geojson_filename_pattern": config.output.geojson_filename_pattern,
                "manifest_filename": config.output.manifest_filename,
                "write_geojson": config.output.write_geojson
            },
            
            # Performance configuration
            "performance": {
                "multiprocessing": config.performance.multiprocessing,
                "max_workers": config.performance.max_workers
            }
        }
        
        return snapshot
    
    def _calculate_polyline_statistics(self, polylines: List) -> Dict[str, Any]:
        """Calculate statistics for polylines in a storey.
        
        Args:
            polylines: List of polylines to analyze
            
        Returns:
            Dict[str, Any]: Polyline statistics
        """
        if not polylines:
            return {
                "total_polylines": 0,
                "closed_polylines": 0,
                "open_polylines": 0,
                "total_points": 0,
                "average_points_per_polyline": 0.0,
                "min_points": 0,
                "max_points": 0
            }
        
        closed_count = sum(1 for p in polylines if p.is_closed)
        open_count = len(polylines) - closed_count
        
        point_counts = [len(p.points) for p in polylines]
        total_points = sum(point_counts)
        
        return {
            "total_polylines": len(polylines),
            "closed_polylines": closed_count,
            "open_polylines": open_count,
            "total_points": total_points,
            "average_points_per_polyline": total_points / len(polylines),
            "min_points": min(point_counts) if point_counts else 0,
            "max_points": max(point_counts) if point_counts else 0
        }
    
    def _calculate_ifc_class_distribution(self, polylines: List) -> Dict[str, int]:
        """Calculate distribution of IFC classes in polylines.
        
        Args:
            polylines: List of polylines to analyze
            
        Returns:
            Dict[str, int]: Count of polylines per IFC class
        """
        distribution = {}
        for polyline in polylines:
            ifc_class = polyline.ifc_class
            distribution[ifc_class] = distribution.get(ifc_class, 0) + 1
        
        return distribution
    
    def generate_manifest_json(
        self, 
        storeys: List[StoreyResult], 
        config: Config,
        input_file: str,
        processing_time: float,
        indent: Optional[int] = 2
    ) -> str:
        """Generate manifest as JSON string.
        
        Args:
            storeys: List of processed storey results
            config: Configuration used for processing
            input_file: Path to the input IFC file
            processing_time: Total processing time in seconds
            indent: JSON indentation (None for compact output)
            
        Returns:
            str: Manifest as formatted JSON string
            
        Raises:
            ProcessingError: If manifest generation or serialization fails
        """
        manifest_data = self.generate_manifest(storeys, config, input_file, processing_time)
        
        try:
            # Convert ManifestData to dictionary for JSON serialization
            manifest_dict = {
                "input_file": manifest_data.input_file,
                "generated_at": manifest_data.generated_at.isoformat(),
                "storeys": manifest_data.storeys,
                "config_used": manifest_data.config_used,
                "total_elements": manifest_data.total_elements,
                "processing_time_seconds": manifest_data.processing_time_seconds,
                "generator": "IFC Floor Plan Generator",
                "manifest_version": "1.0"
            }
            
            return json.dumps(manifest_dict, indent=indent, ensure_ascii=False)
            
        except Exception as e:
            raise ProcessingError(
                error_code="MANIFEST_SERIALIZE_FAILED",
                message=f"Manifest serialisering feilet: {str(e)}",
                context={"error": str(e)}
            )
    
    def generate_and_save_manifest(
        self,
        storeys: List[StoreyResult], 
        config: Config,
        input_file: str,
        processing_time: float,
        output_manager
    ) -> str:
        """Generate manifest and save to file.
        
        Args:
            storeys: List of processed storey results
            config: Configuration used for processing
            input_file: Path to the input IFC file
            processing_time: Total processing time in seconds
            output_manager: OutputManager instance for file operations
            
        Returns:
            str: Full path to the saved manifest file
            
        Raises:
            WriteFailedError: If file writing fails
            ProcessingError: If manifest generation fails
        """
        # Generate manifest JSON
        manifest_json = self.generate_manifest_json(storeys, config, input_file, processing_time)
        
        # Write to file using output manager
        file_path = output_manager.write_manifest_file(manifest_json)
        
        self._logger.info(f"Generated and saved manifest: {file_path}")
        return file_path
    
    def create_summary_statistics(self, storeys: List[StoreyResult]) -> Dict[str, Any]:
        """Create summary statistics across all storeys.
        
        Args:
            storeys: List of storey results to summarize
            
        Returns:
            Dict[str, Any]: Summary statistics
        """
        if not storeys:
            return {
                "total_storeys": 0,
                "total_elements": 0,
                "total_polylines": 0,
                "total_points": 0,
                "ifc_classes_found": [],
                "output_files_generated": 0
            }
        
        total_elements = sum(storey.element_count for storey in storeys)
        total_polylines = sum(len(storey.polylines) for storey in storeys)
        
        # Calculate total points
        total_points = 0
        all_ifc_classes = set()
        output_files_count = 0
        
        for storey in storeys:
            for polyline in storey.polylines:
                total_points += len(polyline.points)
                all_ifc_classes.add(polyline.ifc_class)
            
            # Count output files
            if storey.svg_file:
                output_files_count += 1
            if storey.geojson_file:
                output_files_count += 1
        
        return {
            "total_storeys": len(storeys),
            "total_elements": total_elements,
            "total_polylines": total_polylines,
            "total_points": total_points,
            "ifc_classes_found": sorted(list(all_ifc_classes)),
            "output_files_generated": output_files_count,
            "average_elements_per_storey": total_elements / len(storeys),
            "average_polylines_per_storey": total_polylines / len(storeys)
        }
    
    def validate_manifest_data(self, manifest_data: ManifestData) -> bool:
        """Validate manifest data for completeness and consistency.
        
        Args:
            manifest_data: Manifest data to validate
            
        Returns:
            bool: True if manifest is valid
        """
        try:
            # Check required fields
            if not manifest_data.input_file:
                self._logger.error("Manifest validation failed: missing input_file")
                return False
            
            if not manifest_data.storeys:
                self._logger.warning("Manifest has no storeys")
            
            if not manifest_data.config_used:
                self._logger.error("Manifest validation failed: missing config_used")
                return False
            
            # Validate storey data
            for i, storey_data in enumerate(manifest_data.storeys):
                if "name" not in storey_data:
                    self._logger.error(f"Storey {i} missing name field")
                    return False
                
                if "element_count" not in storey_data:
                    self._logger.error(f"Storey {i} missing element_count field")
                    return False
            
            self._logger.debug("Manifest validation passed")
            return True
            
        except Exception as e:
            self._logger.error(f"Manifest validation error: {e}")
            return False