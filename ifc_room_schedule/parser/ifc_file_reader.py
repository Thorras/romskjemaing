"""
IFC File Reader

Handles reading and basic validation of IFC files using IfcOpenShell.
Enhanced with detailed logging, structured error reporting, and performance optimizations.
"""

import os
from typing import Tuple, Optional
import ifcopenshell
import ifcopenshell.util.element
from ..utils.enhanced_logging import (
    enhanced_logger, ErrorCategory, ErrorSeverity, MemoryErrorAnalyzer
)
from .optimized_ifc_parser import OptimizedIFCParser, CacheConfig
from .performance_monitor import PerformanceMonitor
from .batch_processor import BatchProcessor, BatchConfig


class IfcFileReader:
    """Handles IFC file loading and validation using IfcOpenShell with performance optimizations."""

    def __init__(self, enable_optimizations: bool = True):
        self.ifc_file = None
        self.file_path = None
        self.enable_optimizations = enable_optimizations
        
        # Initialize performance components if optimizations are enabled
        if self.enable_optimizations:
            self.optimized_parser = OptimizedIFCParser(
                CacheConfig(
                    max_size=128,
                    ttl_seconds=3600,
                    enable_geometry_cache=True,
                    enable_property_cache=True,
                    enable_relationship_cache=True
                )
            )
            self.performance_monitor = PerformanceMonitor()
            self.batch_processor = BatchProcessor(
                BatchConfig(
                    batch_size=100,
                    max_workers=4,
                    memory_threshold_mb=1000.0
                )
            )
        else:
            self.optimized_parser = None
            self.performance_monitor = None
            self.batch_processor = None

    def load_file(self, file_path: str) -> Tuple[bool, str]:
        """
        Load and validate an IFC file with comprehensive error handling and detailed logging.

        Args:
            file_path: Path to the IFC file

        Returns:
            Tuple of (success: bool, message: str)
        """
        # Start operation timing for detailed performance logging
        operation_id = enhanced_logger.start_operation_timing("ifc_file_load", file_path)
        
        try:
            enhanced_logger.logger.info(f"Starting IFC file validation: {file_path}")
            
            # Input validation with enhanced error reporting
            if not file_path or not file_path.strip():
                error_report = enhanced_logger.create_error_report(
                    ErrorCategory.USER_INPUT, ErrorSeverity.LOW,
                    "No File Path", "No file path provided",
                    user_guidance="Please select an IFC file to load.",
                    recovery_suggestions=["Use the 'Load IFC File' button to select a file"]
                )
                enhanced_logger.finish_operation_timing(operation_id)
                return False, "No file path provided"
            
            file_path = file_path.strip()
            enhanced_logger.logger.debug(f"Processing file path: {file_path}")
            
            # Check file extension first with detailed guidance
            if not file_path.lower().endswith(('.ifc', '.ifcxml')):
                error_report = enhanced_logger.create_error_report(
                    ErrorCategory.USER_INPUT, ErrorSeverity.LOW,
                    "Invalid File Format", f"File does not have IFC extension: {os.path.basename(file_path)}",
                    user_guidance="Only IFC and IFCXML files are supported for room schedule generation.",
                    recovery_suggestions=[
                        "Select a file with .ifc or .ifcxml extension",
                        "Convert your file to IFC format using CAD software",
                        "Verify the file is actually an IFC file despite the extension"
                    ]
                )
                enhanced_logger.finish_operation_timing(operation_id)
                return False, ("Invalid file format. Please select an IFC "
                               "or IFCXML file (.ifc or .ifcxml)")

            # Check if file exists and is accessible with detailed error reporting
            if not os.path.exists(file_path):
                error_report = enhanced_logger.create_error_report(
                    ErrorCategory.IO, ErrorSeverity.MEDIUM,
                    "File Not Found", f"File does not exist: {file_path}",
                    user_guidance="The selected file could not be found. It may have been moved, deleted, or renamed.",
                    recovery_suggestions=[
                        "Verify the file path is correct",
                        "Check if the file was moved or renamed",
                        "Select a different IFC file",
                        "Restore the file from backup if available"
                    ]
                )
                enhanced_logger.finish_operation_timing(operation_id)
                return False, f"File not found: {file_path}"
            
            if not os.path.isfile(file_path):
                error_report = enhanced_logger.create_error_report(
                    ErrorCategory.IO, ErrorSeverity.MEDIUM,
                    "Invalid File Path", f"Path is not a file: {file_path}",
                    user_guidance="The selected path points to a directory or special file, not a regular file.",
                    recovery_suggestions=[
                        "Select a file, not a directory",
                        "Navigate into the directory to find the IFC file",
                        "Check if the path contains the correct filename"
                    ]
                )
                enhanced_logger.finish_operation_timing(operation_id)
                return False, f"Path is not a file: {file_path}"
            
            if not os.access(file_path, os.R_OK):
                error_report = enhanced_logger.create_error_report(
                    ErrorCategory.IO, ErrorSeverity.MEDIUM,
                    "File Access Denied", f"File is not readable: {file_path}",
                    user_guidance="The application does not have permission to read this file.",
                    recovery_suggestions=[
                        "Run the application as administrator",
                        "Check file permissions and grant read access",
                        "Copy the file to a location with appropriate permissions",
                        "Contact your system administrator"
                    ]
                )
                enhanced_logger.finish_operation_timing(operation_id)
                return False, f"File is not readable (permission denied): {file_path}"

            # Enhanced file size analysis and memory validation with detailed logging
            try:
                file_size = os.path.getsize(file_path)
                size_mb = file_size / (1024*1024)
                enhanced_logger.logger.info(f"File size analysis: {size_mb:.1f}MB ({file_size:,} bytes)")
                
                if file_size == 0:
                    error_report = enhanced_logger.create_error_report(
                        ErrorCategory.VALIDATION, ErrorSeverity.MEDIUM,
                        "Empty File", "File is empty (0 bytes)",
                        user_guidance="The selected file contains no data and cannot be processed.",
                        recovery_suggestions=[
                            "Select a different IFC file",
                            "Check if the file was corrupted during transfer",
                            "Re-export the file from the original CAD software"
                        ]
                    )
                    enhanced_logger.finish_operation_timing(operation_id)
                    return False, "File is empty (0 bytes)"
                
                # Get memory recommendations for user guidance
                memory_recommendations = MemoryErrorAnalyzer.get_memory_recommendations(size_mb)
                enhanced_logger.logger.debug(f"Memory recommendations: {memory_recommendations}")
                
                # Smart memory validation based on file size with enhanced error reporting
                if file_size < 10 * 1024 * 1024:  # Files under 10MB - minimal validation
                    enhanced_logger.logger.info(f"Small file detected ({size_mb:.1f}MB) - using optimized loading")
                    # For small files, just do basic checks
                    if file_size > 500 * 1024 * 1024:  # Still check for extremely large files
                        error_report = enhanced_logger.create_error_report(
                            ErrorCategory.MEMORY, ErrorSeverity.HIGH,
                            "File Too Large", f"File is extremely large ({size_mb:.1f}MB)",
                            user_guidance="Files over 500MB are not supported due to memory limitations.",
                            recovery_suggestions=[
                                "Split the IFC file into smaller parts",
                                "Use a more powerful system with more RAM",
                                "Process only specific building sections",
                                "Contact support for large file processing options"
                            ]
                        )
                        enhanced_logger.finish_operation_timing(operation_id)
                        return False, (f"File is extremely large ({size_mb:.1f}MB). "
                                       f"Files over 500MB are not supported due to memory limitations.")
                else:
                    # Enhanced memory check for larger files using psutil
                    try:
                        import psutil
                        available_memory = psutil.virtual_memory().available
                        available_mb = available_memory / (1024*1024)
                        enhanced_logger.logger.info(f"System memory check: {available_mb:.1f}MB available")
                        
                        # More reasonable memory estimation for different file sizes
                        if file_size < 50 * 1024 * 1024:  # 10-50MB files
                            estimated_memory_needed = file_size * 2  # Less conservative for medium files
                            memory_threshold = 0.4  # Use max 40% of available memory
                            category = "medium"
                        elif file_size < 100 * 1024 * 1024:  # 50-100MB files
                            estimated_memory_needed = file_size * 3  # Moderate estimate
                            memory_threshold = 0.5  # Use max 50% of available memory
                            category = "large"
                        else:  # Files over 100MB
                            estimated_memory_needed = file_size * 4  # Conservative estimate
                            memory_threshold = 0.6  # Use max 60% of available memory
                            category = "very_large"
                        
                        estimated_mb = estimated_memory_needed / (1024*1024)
                        enhanced_logger.logger.info(f"Memory estimation for {category} file: ~{estimated_mb:.1f}MB needed")
                        
                        if estimated_memory_needed > available_memory * memory_threshold:
                            # Create detailed memory error with specific guidance
                            guidance, suggestions = MemoryErrorAnalyzer.analyze_memory_error(
                                file_size, available_memory
                            )
                            
                            error_report = enhanced_logger.create_error_report(
                                ErrorCategory.MEMORY, ErrorSeverity.HIGH,
                                "Insufficient Memory", f"Not enough memory to process file ({size_mb:.1f}MB)",
                                user_guidance=guidance,
                                recovery_suggestions=suggestions
                            )
                            enhanced_logger.finish_operation_timing(operation_id)
                            
                            return False, (f"Insufficient memory to process file ({size_mb:.1f}MB). "
                                         f"Estimated memory needed: {estimated_mb:.1f}MB, "
                                         f"Available: {available_mb:.1f}MB. "
                                         f"Recommended system RAM: {memory_recommendations['recommended_ram']}. "
                                         f"Try closing other applications or processing a smaller file.")
                    except ImportError:
                        # Fallback to simple file size check if psutil not available
                        enhanced_logger.logger.warning("psutil not available, using basic file size check")
                
                # Adjusted file size limits with enhanced error messages
                if file_size > 500 * 1024 * 1024:  # 500MB
                    error_report = enhanced_logger.create_error_report(
                        ErrorCategory.MEMORY, ErrorSeverity.HIGH,
                        "File Extremely Large", f"File size ({size_mb:.1f}MB) exceeds maximum supported size",
                        user_guidance=f"Files over 500MB are not supported. Recommended maximum is 200MB. "
                                    f"Expected processing time would be: {memory_recommendations['processing_time']}",
                        recovery_suggestions=[
                            "Split the IFC model into smaller sections",
                            "Export only specific building levels or zones",
                            "Use IFC filtering tools to reduce file size",
                            "Process on a high-performance workstation"
                        ]
                    )
                    enhanced_logger.finish_operation_timing(operation_id)
                    return False, (f"File is extremely large ({size_mb:.1f}MB). "
                                   f"Files over 500MB are not supported due to memory limitations.")
                elif file_size > 200 * 1024 * 1024:  # 200MB
                    error_report = enhanced_logger.create_error_report(
                        ErrorCategory.MEMORY, ErrorSeverity.MEDIUM,
                        "File Very Large", f"File size ({size_mb:.1f}MB) may cause performance issues",
                        user_guidance=f"Large files may cause memory issues or slow processing. "
                                    f"Expected processing time: {memory_recommendations['processing_time']}. "
                                    f"Recommended system RAM: {memory_recommendations['recommended_ram']}",
                        recovery_suggestions=[
                            "Ensure sufficient free memory before processing",
                            "Close other applications to free up RAM",
                            "Consider processing during off-peak hours",
                            "Split the file into smaller sections if possible"
                        ]
                    )
                    enhanced_logger.finish_operation_timing(operation_id)
                    return False, (f"File is very large ({size_mb:.1f}MB). "
                                   f"Files over 200MB may cause memory issues. "
                                   f"Recommended system RAM: {memory_recommendations['recommended_ram']}. "
                                   f"Try processing a smaller file or increase available memory.")
                elif file_size > 100 * 1024 * 1024:  # 100MB
                    enhanced_logger.logger.warning(f"Large file detected: {size_mb:.1f}MB - processing may take {memory_recommendations['processing_time']}")
                    # Continue but warn - let the UI handle this decision
                    
            except OSError as e:
                error_report = enhanced_logger.create_error_report(
                    ErrorCategory.IO, ErrorSeverity.MEDIUM,
                    "File Access Error", f"Cannot access file information: {str(e)}",
                    exception=e,
                    user_guidance="Unable to read file properties. The file may be locked or corrupted.",
                    recovery_suggestions=[
                        "Check if the file is open in another application",
                        "Verify file permissions",
                        "Try copying the file to a different location",
                        "Restart the application and try again"
                    ]
                )
                enhanced_logger.finish_operation_timing(operation_id)
                return False, f"Cannot access file information: {str(e)}"

            # Try to open with IfcOpenShell with enhanced error handling and timing
            parsing_start = enhanced_logger.start_operation_timing("ifc_parsing", file_path)
            try:
                enhanced_logger.logger.info(f"Starting IFC parsing: {file_path} ({size_mb:.1f}MB)")
                
                # Use optimized parser if available
                if self.enable_optimizations and self.optimized_parser:
                    success, message = self.optimized_parser.load_file_optimized(file_path)
                    if success:
                        self.ifc_file = self.optimized_parser.ifc_file
                        self.file_path = file_path
                        enhanced_logger.logger.info(f"IFC file loaded with optimizations: {message}")
                    else:
                        # Fallback to standard loading
                        enhanced_logger.logger.warning(f"Optimized loading failed, falling back to standard: {message}")
                        self.ifc_file = ifcopenshell.open(file_path)
                        self.file_path = file_path
                else:
                    # Standard loading
                    self.ifc_file = ifcopenshell.open(file_path)
                    self.file_path = file_path
                
                parsing_timing = enhanced_logger.finish_operation_timing(parsing_start)
                enhanced_logger.logger.info(f"IFC file parsed successfully in {parsing_timing.duration_seconds:.2f}s")
                
            except MemoryError as e:
                enhanced_logger.finish_operation_timing(parsing_start)
                
                # Get detailed memory analysis
                try:
                    import psutil
                    available_memory = psutil.virtual_memory().available
                    guidance, suggestions = MemoryErrorAnalyzer.analyze_memory_error(
                        file_size, available_memory, e
                    )
                except ImportError:
                    guidance = f"Memory error loading IFC file ({size_mb:.1f}MB). IFC processing requires significant memory."
                    suggestions = [
                        "Close other applications to free up memory",
                        "Restart the application to clear memory leaks",
                        "Try processing a smaller file",
                        "Upgrade system memory for large IFC files"
                    ]
                
                error_report = enhanced_logger.create_error_report(
                    ErrorCategory.MEMORY, ErrorSeverity.HIGH,
                    "Memory Error During IFC Parsing", f"Out of memory while parsing IFC file ({size_mb:.1f}MB)",
                    exception=e,
                    user_guidance=guidance,
                    recovery_suggestions=suggestions
                )
                enhanced_logger.finish_operation_timing(operation_id)
                
                return False, (f"Memory error loading IFC file ({size_mb:.1f}MB). "
                              f"File size: {file_size:,} bytes. "
                              f"{guidance} Error: {str(e)}")
                              
            except Exception as e:
                enhanced_logger.finish_operation_timing(parsing_start)
                
                error_msg = str(e).lower()
                enhanced_logger.logger.error(f"IFC parsing failed: {e}")
                
                # Classify and provide specific guidance for different parsing errors
                if "not a valid ifc file" in error_msg or "parse error" in error_msg:
                    error_report = enhanced_logger.create_error_report(
                        ErrorCategory.PARSING, ErrorSeverity.HIGH,
                        "Invalid IFC File", f"File is not a valid IFC format: {os.path.basename(file_path)}",
                        exception=e,
                        user_guidance="The file appears to be corrupted or not in valid IFC format.",
                        recovery_suggestions=[
                            "Verify the file was exported correctly from CAD software",
                            "Try opening the file in another IFC viewer to confirm validity",
                            "Re-export the file from the original CAD application",
                            "Check if the file was corrupted during transfer"
                        ]
                    )
                    enhanced_logger.finish_operation_timing(operation_id)
                    return False, (f"Invalid or corrupted IFC file. "
                                   f"The file may be damaged or not a valid IFC format. "
                                   f"Try re-exporting from your CAD software. Error: {str(e)}")
                                   
                elif "unsupported" in error_msg or "schema" in error_msg:
                    error_report = enhanced_logger.create_error_report(
                        ErrorCategory.PARSING, ErrorSeverity.MEDIUM,
                        "Unsupported IFC Format", f"Unsupported IFC schema or version: {os.path.basename(file_path)}",
                        exception=e,
                        user_guidance="The IFC file uses a schema version that is not supported.",
                        recovery_suggestions=[
                            "Export the file using IFC2x3 or IFC4 schema",
                            "Check the IFC export settings in your CAD software",
                            "Convert the file to a supported IFC version",
                            "Contact support for information about supported IFC versions"
                        ]
                    )
                    enhanced_logger.finish_operation_timing(operation_id)
                    return False, (f"Unsupported IFC file format or version. "
                                   f"Supported versions: IFC2x3, IFC4. "
                                   f"Error: {str(e)}")
                                   
                elif "encoding" in error_msg or "character" in error_msg:
                    error_report = enhanced_logger.create_error_report(
                        ErrorCategory.PARSING, ErrorSeverity.MEDIUM,
                        "File Encoding Error", f"Character encoding issue in IFC file: {os.path.basename(file_path)}",
                        exception=e,
                        user_guidance="The file contains characters that cannot be properly decoded.",
                        recovery_suggestions=[
                            "Re-export the file with UTF-8 encoding",
                            "Check for special characters in object names",
                            "Use ASCII-only characters in IFC export settings",
                            "Try opening the file in a text editor to check encoding"
                        ]
                    )
                    enhanced_logger.finish_operation_timing(operation_id)
                    return False, (f"File encoding error in IFC file. "
                                   f"Try re-exporting with UTF-8 encoding. "
                                   f"Error: {str(e)}")
                else:
                    error_report = enhanced_logger.create_error_report(
                        ErrorCategory.PARSING, ErrorSeverity.HIGH,
                        "IFC Parsing Error", f"Unexpected error parsing IFC file: {os.path.basename(file_path)}",
                        exception=e,
                        user_guidance="An unexpected error occurred while parsing the IFC file.",
                        recovery_suggestions=[
                            "Verify the file is not corrupted",
                            "Try processing a different IFC file to isolate the issue",
                            "Re-export the file from the original CAD software",
                            "Contact support with the error details"
                        ]
                    )
                    enhanced_logger.finish_operation_timing(operation_id)
                    return False, f"Error loading IFC file: {str(e)}"

            # Enhanced validation - check file structure with detailed logging
            validation_start = enhanced_logger.start_operation_timing("ifc_validation", file_path)
            try:
                enhanced_logger.logger.info("Starting IFC file structure validation...")
                products = self.ifc_file.by_type("IfcProduct")
                
                if len(products) == 0:
                    self.ifc_file = None
                    self.file_path = None
                    enhanced_logger.finish_operation_timing(validation_start)
                    
                    error_report = enhanced_logger.create_error_report(
                        ErrorCategory.VALIDATION, ErrorSeverity.HIGH,
                        "Empty IFC Structure", "IFC file contains no building elements",
                        user_guidance="The IFC file appears to be empty or contains no building elements (IfcProduct entities).",
                        recovery_suggestions=[
                            "Verify the IFC export included building geometry",
                            "Check export settings to include all building elements",
                            "Try exporting from a different view or model state",
                            "Ensure the model contains actual building components"
                        ]
                    )
                    enhanced_logger.finish_operation_timing(operation_id)
                    return False, ("IFC file appears to be empty or contains no "
                                   "building elements (IfcProduct entities).")
                
                validation_timing = enhanced_logger.finish_operation_timing(validation_start)
                enhanced_logger.logger.info(f"Found {len(products)} building products in {validation_timing.duration_seconds:.2f}s")
                
            except MemoryError as e:
                self.ifc_file = None
                self.file_path = None
                enhanced_logger.finish_operation_timing(validation_start)
                
                # Get detailed memory analysis for validation error
                try:
                    import psutil
                    available_memory = psutil.virtual_memory().available
                    guidance, suggestions = MemoryErrorAnalyzer.analyze_memory_error(
                        file_size, available_memory, e
                    )
                except ImportError:
                    guidance = f"Memory error during file validation ({size_mb:.1f}MB). The file may be too complex."
                    suggestions = [
                        "Restart the application to clear memory",
                        "Close other applications",
                        "Try a smaller or simpler IFC file"
                    ]
                
                error_report = enhanced_logger.create_error_report(
                    ErrorCategory.MEMORY, ErrorSeverity.HIGH,
                    "Memory Error During Validation", f"Out of memory while validating IFC structure ({size_mb:.1f}MB)",
                    exception=e,
                    user_guidance=guidance,
                    recovery_suggestions=suggestions
                )
                enhanced_logger.finish_operation_timing(operation_id)
                
                return False, (f"Memory error during file validation ({size_mb:.1f}MB). "
                              f"File size: {file_size:,} bytes. "
                              f"The file may be too large for available memory. Error: {str(e)}")
                              
            except Exception as e:
                self.ifc_file = None
                self.file_path = None
                enhanced_logger.finish_operation_timing(validation_start)
                
                error_report = enhanced_logger.create_error_report(
                    ErrorCategory.VALIDATION, ErrorSeverity.HIGH,
                    "IFC Validation Error", f"Error reading IFC entities during validation",
                    exception=e,
                    user_guidance="An error occurred while validating the IFC file structure.",
                    recovery_suggestions=[
                        "Verify the IFC file is not corrupted",
                        "Try opening the file in another IFC viewer",
                        "Re-export the file from the original CAD software",
                        "Check if the file contains complex or unusual geometry"
                    ]
                )
                enhanced_logger.finish_operation_timing(operation_id)
                return False, f"Error reading IFC entities: {str(e)}"

            # Enhanced space validation with detailed analysis
            space_validation_start = enhanced_logger.start_operation_timing("space_validation", file_path)
            try:
                enhanced_logger.logger.info("Starting IfcSpace entity validation...")
                spaces = self.ifc_file.by_type("IfcSpace")
                
                if len(spaces) == 0:
                    # Fail if no spaces found - this is a room schedule application
                    self.ifc_file = None
                    self.file_path = None
                    enhanced_logger.finish_operation_timing(space_validation_start)
                    
                    error_report = enhanced_logger.create_error_report(
                        ErrorCategory.VALIDATION, ErrorSeverity.HIGH,
                        "No Spaces Found", "IFC file contains no IfcSpace entities",
                        user_guidance="This application requires IFC files with room/space data for generating room schedules.",
                        recovery_suggestions=[
                            "Ensure spaces/rooms are included in the IFC export",
                            "Check IFC export settings to include space boundaries",
                            "Verify the model contains room/space objects",
                            "Try exporting with 'Include Spaces' option enabled",
                            "Use an IFC file that contains architectural space data"
                        ]
                    )
                    enhanced_logger.finish_operation_timing(operation_id)
                    return False, ("No IfcSpace entities found in the file. "
                                  "This application requires IFC files with room/space data.")
                
                enhanced_logger.logger.info(f"Found {len(spaces)} IfcSpace entities")
                
                # Enhanced validation for space data quality with detailed analysis
                valid_spaces = 0
                spaces_with_names = 0
                spaces_with_geometry = 0
                sample_size = min(10, len(spaces))  # Check up to 10 spaces for quality
                
                for i, space in enumerate(spaces[:sample_size]):
                    if hasattr(space, 'GlobalId') and space.GlobalId:
                        valid_spaces += 1
                    if hasattr(space, 'Name') and space.Name:
                        spaces_with_names += 1
                    if hasattr(space, 'Representation') and space.Representation:
                        spaces_with_geometry += 1
                
                space_validation_timing = enhanced_logger.finish_operation_timing(space_validation_start)
                enhanced_logger.logger.info(f"Space quality analysis completed in {space_validation_timing.duration_seconds:.2f}s:")
                enhanced_logger.logger.info(f"  - Valid spaces: {valid_spaces}/{sample_size}")
                enhanced_logger.logger.info(f"  - Named spaces: {spaces_with_names}/{sample_size}")
                enhanced_logger.logger.info(f"  - Spaces with geometry: {spaces_with_geometry}/{sample_size}")
                
                if valid_spaces == 0:
                    enhanced_logger.logger.warning("Spaces found but appear to have missing or invalid GlobalId data")
                    # Don't fail, but warn the user
                    return True, (f"IFC file loaded with {len(spaces)} spaces, but space data "
                                  f"may be incomplete or invalid. Processing may encounter issues.")
                
                # Provide quality feedback
                quality_percentage = (valid_spaces / sample_size) * 100
                if quality_percentage < 50:
                    enhanced_logger.logger.warning(f"Low space data quality: {quality_percentage:.0f}% of sampled spaces have valid data")
                elif quality_percentage < 80:
                    enhanced_logger.logger.info(f"Moderate space data quality: {quality_percentage:.0f}% of sampled spaces have valid data")
                else:
                    enhanced_logger.logger.info(f"Good space data quality: {quality_percentage:.0f}% of sampled spaces have valid data")
                
            except MemoryError as e:
                self.ifc_file = None
                self.file_path = None
                enhanced_logger.finish_operation_timing(space_validation_start)
                
                # Get detailed memory analysis for space validation error
                try:
                    import psutil
                    available_memory = psutil.virtual_memory().available
                    guidance, suggestions = MemoryErrorAnalyzer.analyze_memory_error(
                        file_size, available_memory, e
                    )
                except ImportError:
                    guidance = f"Memory error reading space data from file ({size_mb:.1f}MB). The file may contain too many spaces."
                    suggestions = [
                        "Try processing a smaller file with fewer spaces",
                        "Restart the application to clear memory",
                        "Close other applications to free up memory"
                    ]
                
                error_report = enhanced_logger.create_error_report(
                    ErrorCategory.MEMORY, ErrorSeverity.HIGH,
                    "Memory Error Reading Spaces", f"Out of memory while reading IfcSpace entities ({size_mb:.1f}MB)",
                    exception=e,
                    user_guidance=guidance,
                    recovery_suggestions=suggestions
                )
                enhanced_logger.finish_operation_timing(operation_id)
                
                return False, (f"Memory error reading space data from file ({size_mb:.1f}MB). "
                              f"File size: {file_size:,} bytes. "
                              f"Try processing a smaller file or restart the application. Error: {str(e)}")
                              
            except Exception as e:
                enhanced_logger.finish_operation_timing(space_validation_start)
                
                error_report = enhanced_logger.create_error_report(
                    ErrorCategory.VALIDATION, ErrorSeverity.HIGH,
                    "Space Validation Error", f"Error reading IfcSpace entities",
                    exception=e,
                    user_guidance="An error occurred while reading space data from the IFC file.",
                    recovery_suggestions=[
                        "Verify the IFC file contains valid space data",
                        "Check if the file was exported with space information",
                        "Try opening the file in another IFC viewer",
                        "Re-export the file with space/room data included"
                    ]
                )
                enhanced_logger.finish_operation_timing(operation_id)
                return False, f"Error reading IfcSpace entities: {str(e)}"

            # Get comprehensive file information for user feedback
            schema = getattr(self.ifc_file, 'schema', 'Unknown')
            
            # Get additional file statistics for detailed logging
            try:
                total_entities = len(self.ifc_file)
                building_elements = len(self.ifc_file.by_type("IfcBuildingElement"))
                enhanced_logger.logger.info(f"IFC file statistics: {total_entities} total entities, {building_elements} building elements")
            except:
                total_entities = "Unknown"
                building_elements = "Unknown"
            
            # Complete operation timing and log success
            final_timing = enhanced_logger.finish_operation_timing(operation_id)
            
            success_msg = (f"Successfully loaded IFC file ({schema}) with "
                          f"{len(spaces)} spaces found in {final_timing.duration_seconds:.2f}s.")
            
            # Add performance and size context to success message
            if size_mb > 50:  # Warn about large files
                memory_recommendations = MemoryErrorAnalyzer.get_memory_recommendations(size_mb)
                success_msg += f" Note: Large file ({size_mb:.1f}MB) - processing took {final_timing.duration_seconds:.1f}s."
                enhanced_logger.logger.info(f"Large file processing completed: {size_mb:.1f}MB in {final_timing.duration_seconds:.2f}s "
                                          f"(rate: {size_mb/final_timing.duration_seconds:.2f}MB/s)")
            else:
                enhanced_logger.logger.info(f"Small file processing completed efficiently: {size_mb:.1f}MB in {final_timing.duration_seconds:.2f}s")
            
            enhanced_logger.logger.info(f"IFC file load operation completed successfully: {success_msg}")
            return True, success_msg

        except MemoryError as e:
            self.ifc_file = None
            self.file_path = None
            
            # Enhanced memory error handling with detailed analysis
            try:
                file_size = os.path.getsize(file_path)
                size_mb = file_size / (1024*1024)
                
                # Get system memory info for detailed error report
                try:
                    import psutil
                    available_memory = psutil.virtual_memory().available
                    guidance, suggestions = MemoryErrorAnalyzer.analyze_memory_error(
                        file_size, available_memory, e
                    )
                except ImportError:
                    guidance = f"Memory error loading IFC file ({size_mb:.1f}MB). Insufficient memory for processing."
                    suggestions = [
                        "Close other applications to free up memory",
                        "Restart the application",
                        "Try processing a smaller file",
                        "Upgrade system memory"
                    ]
                
                error_report = enhanced_logger.create_error_report(
                    ErrorCategory.MEMORY, ErrorSeverity.CRITICAL,
                    "Critical Memory Error", f"Out of memory loading IFC file ({size_mb:.1f}MB)",
                    exception=e,
                    user_guidance=guidance,
                    recovery_suggestions=suggestions
                )
                enhanced_logger.finish_operation_timing(operation_id)
                
                return False, (f"Memory error loading IFC file ({size_mb:.1f}MB). "
                              f"File size: {file_size:,} bytes. "
                              f"{guidance} Error: {str(e)}")
            except:
                error_report = enhanced_logger.create_error_report(
                    ErrorCategory.MEMORY, ErrorSeverity.CRITICAL,
                    "Critical Memory Error", "Out of memory loading IFC file",
                    exception=e,
                    user_guidance="Insufficient memory to load the IFC file.",
                    recovery_suggestions=[
                        "Close other applications",
                        "Restart the application",
                        "Try a smaller file"
                    ]
                )
                enhanced_logger.finish_operation_timing(operation_id)
                return False, (f"Memory error loading IFC file: {str(e)}. "
                              f"Try closing other applications or processing a smaller file.")
                              
        except OSError as e:
            self.ifc_file = None
            self.file_path = None
            
            error_report = enhanced_logger.create_error_report(
                ErrorCategory.IO, ErrorSeverity.HIGH,
                "File System Error", f"Operating system error accessing file: {os.path.basename(file_path)}",
                exception=e,
                user_guidance="A file system error occurred while trying to access the IFC file.",
                recovery_suggestions=[
                    "Check if the file is locked by another application",
                    "Verify file permissions and access rights",
                    "Try copying the file to a different location",
                    "Check available disk space",
                    "Run the application as administrator if needed"
                ]
            )
            enhanced_logger.finish_operation_timing(operation_id)
            return False, f"File system error: {str(e)}"
            
        except Exception as e:
            self.ifc_file = None
            self.file_path = None
            
            error_report = enhanced_logger.create_error_report(
                ErrorCategory.UNKNOWN, ErrorSeverity.HIGH,
                "Unexpected Error", f"Unexpected error loading IFC file: {os.path.basename(file_path)}",
                exception=e,
                user_guidance="An unexpected error occurred while loading the IFC file.",
                recovery_suggestions=[
                    "Try loading the file again",
                    "Restart the application",
                    "Verify the file is not corrupted",
                    "Try processing a different IFC file to isolate the issue",
                    "Contact support with the error details"
                ]
            )
            enhanced_logger.finish_operation_timing(operation_id)
            return False, f"Unexpected error loading IFC file: {str(e)}"

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
        
        # Clean up performance components
        if self.enable_optimizations:
            if self.optimized_parser:
                self.optimized_parser.close()
            if self.performance_monitor:
                self.performance_monitor.cleanup()
            if self.batch_processor:
                self.batch_processor.cleanup()
    
    def get_spaces_optimized(self):
        """Get spaces with performance optimizations."""
        if not self.ifc_file:
            return []
        
        if self.enable_optimizations and self.optimized_parser:
            return self.optimized_parser.get_spaces_cached()
        else:
            return self.ifc_file.by_type("IfcSpace")
    
    def get_space_properties_optimized(self, space_guid: str):
        """Get space properties with caching."""
        if not self.ifc_file:
            return None
        
        if self.enable_optimizations and self.optimized_parser:
            return self.optimized_parser.get_space_properties_cached(space_guid)
        else:
            # Fallback to standard method
            spaces = self.ifc_file.by_type("IfcSpace")
            for space in spaces:
                if hasattr(space, 'GlobalId') and space.GlobalId == space_guid:
                    return ifcopenshell.util.element.get_properties(space)
            return None
    
    def get_space_boundaries_optimized(self, space_guid: str):
        """Get space boundaries with caching."""
        if not self.ifc_file:
            return []
        
        if self.enable_optimizations and self.optimized_parser:
            return self.optimized_parser.get_space_boundaries_cached(space_guid)
        else:
            # Fallback to standard method
            return []
    
    def process_spaces_batch(self, processor_func, batch_size: int = None):
        """Process spaces in batches for optimal performance."""
        if not self.ifc_file:
            return []
        
        spaces = self.get_spaces_optimized()
        
        if self.enable_optimizations and self.batch_processor:
            if batch_size:
                self.batch_processor.config.batch_size = batch_size
            return self.batch_processor.process_spaces_batch(spaces, processor_func)
        else:
            # Fallback to standard processing
            return [processor_func(space) for space in spaces]
    
    def get_performance_metrics(self):
        """Get comprehensive performance metrics."""
        if not self.enable_optimizations:
            return {"optimizations_disabled": True}
        
        metrics = {}
        
        if self.optimized_parser:
            parser_metrics = self.optimized_parser.get_metrics()
            cache_stats = self.optimized_parser.get_cache_stats()
            metrics.update({
                "parser_metrics": parser_metrics,
                "cache_stats": cache_stats
            })
        
        if self.performance_monitor:
            performance_stats = self.performance_monitor.get_performance_stats()
            metrics["performance_stats"] = performance_stats
        
        if self.batch_processor:
            processing_stats = self.batch_processor.get_processing_stats()
            metrics["processing_stats"] = processing_stats
        
        return metrics
    
    def optimize_performance(self):
        """Apply performance optimizations based on current metrics."""
        if not self.enable_optimizations:
            return
        
        enhanced_logger.logger.info("Applying performance optimizations")
        
        # Get current metrics
        metrics = self.get_performance_metrics()
        
        # Apply optimizations based on file size
        if self.ifc_file:
            try:
                file_size = os.path.getsize(self.file_path)
                file_size_mb = file_size / (1024 * 1024)
                
                if file_size_mb < 10:
                    # Small files - disable caching
                    if self.optimized_parser:
                        self.optimized_parser.cache_config.enable_geometry_cache = False
                        self.optimized_parser.cache_config.enable_property_cache = False
                    if self.batch_processor:
                        self.batch_processor.config.batch_size = 50
                        self.batch_processor.config.use_multiprocessing = False
                
                elif file_size_mb < 100:
                    # Medium files - enable selective caching
                    if self.optimized_parser:
                        self.optimized_parser.cache_config.enable_geometry_cache = True
                        self.optimized_parser.cache_config.enable_property_cache = True
                        self.optimized_parser.cache_config.enable_relationship_cache = False
                    if self.batch_processor:
                        self.batch_processor.config.batch_size = 100
                        self.batch_processor.config.use_multiprocessing = False
                
                else:
                    # Large files - enable all optimizations
                    if self.optimized_parser:
                        self.optimized_parser.cache_config.enable_geometry_cache = True
                        self.optimized_parser.cache_config.enable_property_cache = True
                        self.optimized_parser.cache_config.enable_relationship_cache = True
                    if self.batch_processor:
                        self.batch_processor.config.batch_size = 50
                        self.batch_processor.config.use_multiprocessing = True
                        self.batch_processor.config.memory_threshold_mb = 500.0
                
                enhanced_logger.logger.info(f"Performance optimizations applied for {file_size_mb:.1f}MB file")
                
            except Exception as e:
                enhanced_logger.logger.warning(f"Error applying performance optimizations: {e}")
    
    def get_optimization_recommendations(self):
        """Get optimization recommendations based on current performance."""
        if not self.enable_optimizations:
            return ["Enable optimizations to get recommendations"]
        
        recommendations = []
        
        try:
            metrics = self.get_performance_metrics()
            
            # Cache recommendations
            if "cache_stats" in metrics:
                cache_stats = metrics["cache_stats"]
                hit_ratio = cache_stats.get("hit_ratio", 0)
                if hit_ratio < 0.5:
                    recommendations.append("Low cache hit ratio - consider increasing cache size or TTL")
            
            # Memory recommendations
            if "cache_stats" in metrics:
                memory_usage = metrics["cache_stats"].get("memory_usage_mb", 0)
                if memory_usage > 500:
                    recommendations.append("High cache memory usage - consider reducing cache size")
            
            # Processing recommendations
            if "parser_metrics" in metrics:
                processing_rate = metrics["parser_metrics"].get("processing_rate_mb_per_second", 0)
                if processing_rate < 1.0:
                    recommendations.append("Slow processing rate - consider enabling multiprocessing or reducing batch size")
            
            # File size recommendations
            if self.ifc_file and self.file_path:
                file_size = os.path.getsize(self.file_path)
                file_size_mb = file_size / (1024 * 1024)
                if file_size_mb > 100:
                    recommendations.append("Large file detected - consider using streaming processing")
            
        except Exception as e:
            recommendations.append(f"Error getting recommendations: {e}")
        
        return recommendations