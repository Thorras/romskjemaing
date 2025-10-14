"""
Main processing orchestrator for IFC Floor Plan Generator.

This module provides the FloorPlanGenerator class that coordinates all components
to implement the complete pipeline from IFC input to final output.
"""

import os
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from concurrent.futures import ProcessPoolExecutor, as_completed
import time

from .config import ConfigurationManager, Config
from .parsing import IFCParser, ElementFilter
from .geometry import GeometryEngine, SectionProcessor, GeometryCache
from .rendering import SVGRenderer, GeoJSONRenderer, ManifestGenerator, OutputCoordinator
from .performance import PerformanceOptimizer, PerformanceMonitor
from .errors import ErrorHandler, ProcessingError
from .models import StoreyResult, ProcessingResult, Polyline2D, ManifestData


class FloorPlanGenerator:
    """
    Main orchestrator class that coordinates all components to generate floor plans from IFC files.
    
    This class implements the complete pipeline:
    1. Load and validate configuration
    2. Parse IFC file and extract storeys
    3. Generate geometry for each storey
    4. Process sections and create 2D polylines
    5. Render to SVG and GeoJSON formats
    6. Generate manifest and coordinate output
    """
    
    def __init__(self, config_path: str, verbose: bool = False):
        """
        Initialize the floor plan generator.
        
        Args:
            config_path: Path to the configuration JSON file
            verbose: Enable verbose logging
        """
        self.config_path = config_path
        self.verbose = verbose
        self.config: Optional[Config] = None
        
        # Initialize components
        self.config_manager = ConfigurationManager()
        self.error_handler = ErrorHandler()
        self.performance_monitor = PerformanceMonitor()
        
        # Component instances (initialized during processing)
        self.ifc_parser: Optional[IFCParser] = None
        self.element_filter: Optional[ElementFilter] = None
        self.geometry_engine: Optional[GeometryEngine] = None
        self.geometry_cache: Optional[GeometryCache] = None
        self.section_processor: Optional[SectionProcessor] = None
        self.svg_renderer: Optional[SVGRenderer] = None
        self.geojson_renderer: Optional[GeoJSONRenderer] = None
        self.manifest_generator: Optional[ManifestGenerator] = None
        self.output_coordinator: Optional[OutputCoordinator] = None
        self.performance_optimizer: Optional[PerformanceOptimizer] = None
        
        # Setup logging
        self._setup_logging()
        
        # Processing state
        self.processing_errors: List[ProcessingError] = []
        self.processing_warnings: List[str] = []
        
    def _setup_logging(self):
        """Setup logging configuration based on verbosity level."""
        log_level = logging.DEBUG if self.verbose else logging.INFO
        
        # Configure root logger
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('ifc_floor_plan_generator.log')
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        
    def load_configuration(self) -> bool:
        """
        Load and validate configuration from file.
        
        Returns:
            True if configuration loaded successfully, False otherwise
        """
        try:
            self.logger.info(f"Loading configuration from: {self.config_path}")
            self.config = self.config_manager.load_config(self.config_path)
            
            # Validate configuration
            if not self.config_manager.validate_config(self.config.__dict__):
                error = self.error_handler.handle_error("CONFIG_VALIDATION_FAILED", {
                    "config_path": self.config_path
                })
                self.processing_errors.append(error)
                return False
                
            self.logger.info("Configuration loaded and validated successfully")
            return True
            
        except Exception as e:
            error = self.error_handler.handle_error("CONFIG_LOAD_FAILED", {
                "config_path": self.config_path,
                "error": str(e)
            })
            self.processing_errors.append(error)
            self.logger.error(f"Failed to load configuration: {e}")
            return False
    
    def _initialize_components(self) -> bool:
        """
        Initialize all processing components based on configuration.
        
        Returns:
            True if all components initialized successfully, False otherwise
        """
        try:
            self.logger.info("Initializing processing components")
            
            # Initialize IFC parser
            self.ifc_parser = IFCParser(self.error_handler)
            
            # Initialize element filter
            self.element_filter = ElementFilter(
                self.config.class_filters,
                self.error_handler
            )
            
            # Initialize geometry cache if enabled
            if self.config.geometry.cache_geometry:
                self.geometry_cache = GeometryCache(
                    max_memory_mb=100.0,  # Default 100MB cache
                    max_entries=5000,
                    ttl_hours=24.0
                )
            
            # Initialize geometry engine
            self.geometry_engine = GeometryEngine(
                self.config.geometry,
                self.geometry_cache,
                self.error_handler
            )
            
            # Initialize section processor
            self.section_processor = SectionProcessor(
                slice_tolerance=self.config.tolerances.slice_tol,
                chain_tolerance=self.config.tolerances.chain_tol
            )
            
            # Initialize renderers
            self.svg_renderer = SVGRenderer(self.config.rendering)
            
            if self.config.output.write_geojson:
                self.geojson_renderer = GeoJSONRenderer(self.config)
            
            # Manifest generator is handled by output coordinator
            
            # Initialize output coordinator
            self.output_coordinator = OutputCoordinator(self.config)
            
            # Initialize performance optimizer if multiprocessing enabled
            if self.config.performance.multiprocessing:
                self.performance_optimizer = PerformanceOptimizer(self.config)
            
            self.logger.info("All components initialized successfully")
            return True
            
        except Exception as e:
            error = self.error_handler.handle_error("COMPONENT_INIT_FAILED", {
                "error": str(e)
            })
            self.processing_errors.append(error)
            self.logger.error(f"Failed to initialize components: {e}")
            return False
    
    def process_ifc_file(self) -> ProcessingResult:
        """
        Process the IFC file and generate floor plans.
        
        Returns:
            ProcessingResult containing all generated data and metadata
        """
        start_time = time.time()
        self.logger.info("Starting IFC file processing")
        
        try:
            # Load configuration
            if not self.load_configuration():
                return self._create_error_result("Configuration loading failed")
            
            self.logger.info(f"Processing IFC file: {self.config.input_path}")
            
            # Initialize components
            if not self._initialize_components():
                return self._create_error_result("Component initialization failed")
            
            # Output directory is ensured by output coordinator
            
            # Load IFC file
            self.logger.info("Loading IFC file")
            ifc_file = self.ifc_parser.open_file(self.config.input_path)
            if not ifc_file:
                return self._create_error_result("IFC file loading failed")
            
            # Extract storeys
            self.logger.info("Extracting building storeys")
            storeys = self.ifc_parser.extract_storeys(ifc_file)
            if not storeys:
                error = self.error_handler.handle_error("NO_STOREYS_FOUND", {
                    "input_path": self.config.input_path
                })
                self.processing_errors.append(error)
                return self._create_error_result("No building storeys found")
            
            self.logger.info(f"Found {len(storeys)} building storeys")
            
            # Detect units if auto-detection enabled
            if self.config.units.auto_detect_units:
                unit_scale = self.ifc_parser.detect_units(ifc_file)
                self.logger.info(f"Detected unit scale: {unit_scale}")
            else:
                unit_scale = self.config.units.unit_scale_to_m or 1.0
                self.logger.info(f"Using manual unit scale: {unit_scale}")
            
            # Process storeys
            if self.config.performance.multiprocessing and len(storeys) > 1:
                storey_results = self._process_storeys_parallel(ifc_file, storeys, unit_scale)
            else:
                storey_results = self._process_storeys_sequential(ifc_file, storeys, unit_scale)
            
            # Filter out failed storeys
            successful_results = [r for r in storey_results if r is not None]
            
            if not successful_results:
                return self._create_error_result("No storeys processed successfully")
            
            self.logger.info(f"Successfully processed {len(successful_results)}/{len(storeys)} storeys")
            
            # Generate output files
            processing_time = time.time() - start_time
            output_summary = self._generate_output_files(successful_results, processing_time)
            
            # Create final result
            final_processing_time = time.time() - start_time
            self.logger.info(f"Processing completed in {final_processing_time:.2f} seconds")
            
            # Create manifest data structure for the result
            from datetime import datetime
            manifest_data = ManifestData(
                input_file=self.config.input_path,
                generated_at=datetime.now(),
                storeys=[
                    {
                        "name": storey.storey_name,
                        "index": storey.storey_index,
                        "elevation": storey.elevation,
                        "cut_height": storey.cut_height,
                        "element_count": storey.element_count,
                        "svg_file": storey.svg_file,
                        "geojson_file": storey.geojson_file
                    }
                    for storey in successful_results
                ],
                config_used=self.config.__dict__,
                total_elements=sum(storey.element_count for storey in successful_results),
                processing_time_seconds=final_processing_time
            )
            
            result = ProcessingResult(
                storeys=successful_results,
                manifest=manifest_data,
                errors=self.processing_errors,
                warnings=self.processing_warnings,
                processing_time=final_processing_time,
                unit_scale=unit_scale
            )
            
            # Log performance statistics
            if self.geometry_cache:
                cache_stats = self.geometry_cache.get_stats()
                self.logger.info(f"Geometry cache stats: {cache_stats}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Unexpected error during processing: {e}")
            error = self.error_handler.handle_error("PROCESSING_FAILED", {
                "error": str(e)
            })
            self.processing_errors.append(error)
            return self._create_error_result(f"Processing failed: {e}")
    
    def _process_storeys_sequential(self, ifc_file, storeys: List, unit_scale: float) -> List[Optional[StoreyResult]]:
        """Process storeys sequentially."""
        results = []
        
        for i, storey in enumerate(storeys):
            self.logger.info(f"Processing storey {i+1}/{len(storeys)}: {storey.Name}")
            result = self._process_single_storey(ifc_file, storey, i, unit_scale)
            results.append(result)
            
        return results
    
    def _process_storeys_parallel(self, ifc_file, storeys: List, unit_scale: float) -> List[Optional[StoreyResult]]:
        """Process storeys in parallel using multiprocessing."""
        self.logger.info(f"Processing {len(storeys)} storeys in parallel")
        
        # Use performance optimizer for parallel processing
        return self.performance_optimizer.process_storeys_parallel(
            ifc_file,
            storeys,
            unit_scale,
            self.config,
            self._process_single_storey
        )
    
    def _process_single_storey(self, ifc_file, storey, storey_index: int, unit_scale: float) -> Optional[StoreyResult]:
        """
        Process a single building storey.
        
        Args:
            ifc_file: The IFC file object
            storey: The building storey to process
            storey_index: Index of the storey for naming
            unit_scale: Unit scale factor
            
        Returns:
            StoreyResult if successful, None if failed
        """
        try:
            storey_name = getattr(storey, 'Name', f'Storey_{storey.id()}')
            self.logger.debug(f"Processing storey: {storey_name}")
            
            # Get storey elevation
            elevation = self._get_storey_elevation(storey, unit_scale)
            
            # Get cut height for this storey
            cut_height = self.config_manager.get_storey_cut_height(storey_name)
            
            self.logger.debug(f"Storey {storey_name}: elevation={elevation:.2f}m, cut_height={cut_height:.2f}m")
            
            # Get elements in this storey
            elements = self.ifc_parser.get_elements_by_storey(storey)
            if not elements:
                self.processing_warnings.append(f"No elements found in storey: {storey_name}")
                return None
            
            # Filter elements by class
            filtered_elements = self.element_filter.filter_elements(elements)
            if not filtered_elements:
                self.processing_warnings.append(f"No elements remaining after filtering in storey: {storey_name}")
                return None
            
            self.logger.debug(f"Processing {len(filtered_elements)} elements in {storey_name}")
            
            # Generate geometry and process sections
            polylines = []
            element_count = 0
            
            for element in filtered_elements:
                try:
                    # Generate 3D geometry
                    shape = self.geometry_engine.generate_shape(element)
                    if not shape:
                        continue
                    
                    # Create section at cut height
                    element_guid = getattr(element, 'GlobalId', f'element_{element.id()}')
                    ifc_class = element.is_a()
                    section_polylines = self.section_processor.process_shape_section(
                        shape, cut_height, ifc_class, element_guid
                    )
                    
                    if section_polylines:
                        polylines.extend(section_polylines)
                        element_count += 1
                        
                except Exception as e:
                    self.logger.warning(f"Failed to process element {element.id()}: {e}")
                    continue
            
            if not polylines:
                error = self.error_handler.handle_error("EMPTY_CUT_RESULT", {
                    "storey_name": storey_name,
                    "cut_height": cut_height
                })
                self.processing_errors.append(error)
                return None
            
            # Calculate bounds
            bounds = self._calculate_bounds(polylines)
            
            # Create storey result
            result = StoreyResult(
                storey_name=storey_name,
                storey_index=storey_index,
                elevation=elevation,
                cut_height=cut_height,
                polylines=polylines,
                bounds=bounds,
                element_count=element_count
            )
            
            self.logger.debug(f"Storey {storey_name}: generated {len(polylines)} polylines from {element_count} elements")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to process storey {storey_name}: {e}")
            error = self.error_handler.handle_error("STOREY_PROCESSING_FAILED", {
                "storey_name": storey_name,
                "error": str(e)
            })
            self.processing_errors.append(error)
            return None
    
    def _get_storey_elevation(self, storey, unit_scale: float) -> float:
        """Get the elevation of a building storey."""
        try:
            if hasattr(storey, 'Elevation') and storey.Elevation is not None:
                return float(storey.Elevation) * unit_scale
            
            # Try to get from placement
            if hasattr(storey, 'ObjectPlacement') and storey.ObjectPlacement:
                placement = storey.ObjectPlacement
                if hasattr(placement, 'RelativePlacement') and placement.RelativePlacement:
                    rel_placement = placement.RelativePlacement
                    if hasattr(rel_placement, 'Location') and rel_placement.Location:
                        coords = rel_placement.Location.Coordinates
                        if len(coords) >= 3:
                            return float(coords[2]) * unit_scale
            
            return 0.0
            
        except Exception as e:
            self.logger.warning(f"Failed to get storey elevation: {e}")
            return 0.0
    
    def _calculate_bounds(self, polylines: List[Polyline2D]) -> Dict[str, float]:
        """Calculate bounding box for a list of polylines."""
        if not polylines:
            return {"min_x": 0, "min_y": 0, "max_x": 0, "max_y": 0}
        
        min_x = min_y = float('inf')
        max_x = max_y = float('-inf')
        
        for polyline in polylines:
            for x, y in polyline.points:
                min_x = min(min_x, x)
                min_y = min(min_y, y)
                max_x = max(max_x, x)
                max_y = max(max_y, y)
        
        return {
            "min_x": min_x,
            "min_y": min_y,
            "max_x": max_x,
            "max_y": max_y
        }
    
    def _generate_output_files(self, storey_results: List[StoreyResult], processing_time: float) -> Dict[str, Any]:
        """Generate SVG and GeoJSON output files for all storeys."""
        self.logger.info("Generating output files")
        
        try:
            # Use output coordinator to generate all outputs
            output_info = self.output_coordinator.generate_all_outputs(
                storey_results,
                self.config.input_path,
                processing_time
            )
            
            self.logger.info(f"Generated {len(output_info.get('svg_files', []))} SVG files")
            if self.config.output.write_geojson:
                self.logger.info(f"Generated {len(output_info.get('geojson_files', []))} GeoJSON files")
            
            return output_info
            
        except Exception as e:
            self.logger.error(f"Failed to generate output files: {e}")
            error = self.error_handler.handle_error("WRITE_FAILED", {
                "error": str(e)
            })
            self.processing_errors.append(error)
            return {"errors": [str(e)]}
    
    def _create_error_result(self, message: str) -> ProcessingResult:
        """Create a ProcessingResult for error cases."""
        return ProcessingResult(
            storeys=[],
            manifest={},
            errors=self.processing_errors,
            warnings=self.processing_warnings,
            processing_time=0.0,
            unit_scale=1.0,
            success=False,
            error_message=message
        )
    
    def get_progress_callback(self):
        """Get a progress callback function for monitoring."""
        def progress_callback(current: int, total: int, message: str = ""):
            if self.verbose:
                percentage = (current / total) * 100 if total > 0 else 0
                self.logger.info(f"Progress: {current}/{total} ({percentage:.1f}%) - {message}")
        
        return progress_callback