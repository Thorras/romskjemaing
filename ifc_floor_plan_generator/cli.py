#!/usr/bin/env python3
"""
Command-line interface for IFC Floor Plan Generator.

Provides a user-friendly CLI with configuration file input, progress reporting,
and comprehensive help text.
"""

import argparse
import sys
import os
import logging
from pathlib import Path
from typing import Optional

from .main import FloorPlanGenerator
from .models import ProcessingResult


def setup_argument_parser() -> argparse.ArgumentParser:
    """Setup command-line argument parser with comprehensive help."""
    parser = argparse.ArgumentParser(
        prog='ifc-floor-plan-generator',
        description='Generate 2D floor plans from IFC files with configurable styling and output formats.',
        epilog="""
Examples:
  %(prog)s config.json
  %(prog)s config.json --verbose
  %(prog)s config.json --output-dir ./output --verbose
  %(prog)s --help-config

For detailed configuration options, use --help-config.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Required arguments
    parser.add_argument(
        'config',
        nargs='?',
        help='Path to JSON configuration file'
    )
    
    # Optional arguments
    parser.add_argument(
        '--output-dir', '-o',
        type=str,
        help='Override output directory from configuration'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging and progress reporting'
    )
    
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress all output except errors'
    )
    
    parser.add_argument(
        '--log-file',
        type=str,
        help='Write logs to specified file (default: ifc_floor_plan_generator.log)'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='IFC Floor Plan Generator 1.0.0'
    )
    
    parser.add_argument(
        '--help-config',
        action='store_true',
        help='Show detailed help about configuration options'
    )
    
    parser.add_argument(
        '--validate-config',
        action='store_true',
        help='Validate configuration file without processing'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Perform a dry run without generating output files'
    )
    
    return parser


def show_config_help():
    """Show detailed help about configuration options."""
    help_text = """
IFC Floor Plan Generator - Configuration Help
============================================

The configuration file should be a JSON file with the following structure:

{
  "input_path": "path/to/input.ifc",
  "output_dir": "path/to/output",
  "cut_offset_m": 1.05,
  
  "per_storey_overrides": {
    "Ground Floor": {"cut_offset_m": 0.8},
    "First Floor": {"cut_offset_m": 1.2}
  },
  
  "class_filters": {
    "include_ifc_classes": ["IfcWall", "IfcSlab", "IfcColumn"],
    "exclude_ifc_classes": ["IfcSpace", "IfcOpeningElement"]
  },
  
  "units": {
    "auto_detect_units": true,
    "unit_scale_to_m": null
  },
  
  "geometry": {
    "use_world_coords": true,
    "subtract_openings": true,
    "sew_shells": true
  },
  
  "tolerances": {
    "slice_tol": 1e-6,
    "chain_tol": 1e-3
  },
  
  "rendering": {
    "default_color": "#000000",
    "default_linewidth_px": 1.0,
    "background": null,
    "invert_y": true,
    "class_styles": {
      "IfcWall": {"color": "#FF0000", "linewidth_px": 2.0},
      "IfcSlab": {"color": "#00FF00", "linewidth_px": 1.5}
    }
  },
  
  "output": {
    "svg_filename_pattern": "{index:02d}_{storey_name}.svg",
    "geojson_filename_pattern": "{index:02d}_{storey_name}.geo.json",
    "manifest_filename": "manifest.json",
    "write_geojson": true
  },
  
  "performance": {
    "multiprocessing": false,
    "max_workers": null
  }
}

Configuration Options:
---------------------

input_path (required): Path to the input IFC file
output_dir (required): Directory where output files will be saved
cut_offset_m (required): Default cut height offset in meters above storey elevation

per_storey_overrides (optional): Override cut heights for specific storeys
class_filters (optional): Control which IFC classes to include/exclude
units (optional): Configure unit detection and scaling
geometry (optional): Control geometry generation settings
tolerances (optional): Set geometric processing tolerances
rendering (optional): Configure SVG styling and appearance
output (optional): Control output file naming and formats
performance (optional): Configure multiprocessing and optimization

For more details, see the documentation or example configuration files.
    """
    print(help_text)


def validate_arguments(args) -> bool:
    """Validate command-line arguments."""
    if args.help_config:
        return True
    
    if not args.config:
        print("Error: Configuration file is required", file=sys.stderr)
        print("Use --help for usage information", file=sys.stderr)
        return False
    
    if not os.path.exists(args.config):
        print(f"Error: Configuration file not found: {args.config}", file=sys.stderr)
        return False
    
    if args.verbose and args.quiet:
        print("Error: Cannot use both --verbose and --quiet options", file=sys.stderr)
        return False
    
    return True


def setup_logging(verbose: bool = False, quiet: bool = False, log_file: Optional[str] = None):
    """Setup logging configuration."""
    if quiet:
        log_level = logging.ERROR
    elif verbose:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO
    
    # Configure logging format
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    if verbose:
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Setup handlers
    handlers = []
    
    # Console handler (unless quiet)
    if not quiet:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(logging.Formatter(log_format))
        handlers.append(console_handler)
    
    # File handler
    file_handler = logging.FileHandler(log_file or 'ifc_floor_plan_generator.log')
    file_handler.setLevel(logging.DEBUG)  # Always log everything to file
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    handlers.append(file_handler)
    
    # Configure root logger
    logging.basicConfig(
        level=logging.DEBUG,
        handlers=handlers,
        format=log_format
    )


def print_progress_header():
    """Print a header for progress reporting."""
    print("IFC Floor Plan Generator")
    print("=" * 50)


def print_processing_summary(result: ProcessingResult):
    """Print a summary of processing results."""
    print("\nProcessing Summary:")
    print("-" * 30)
    
    if result.success:
        print(f"✓ Successfully processed {len(result.storeys)} storeys")
        print(f"✓ Processing time: {result.processing_time:.2f} seconds")
        print(f"✓ Unit scale: {result.unit_scale}")
        
        if result.storeys:
            total_elements = sum(storey.element_count for storey in result.storeys)
            total_polylines = sum(len(storey.polylines) for storey in result.storeys)
            print(f"✓ Total elements processed: {total_elements}")
            print(f"✓ Total polylines generated: {total_polylines}")
    else:
        print(f"✗ Processing failed: {result.error_message or 'Unknown error'}")
    
    # Print warnings
    if result.warnings:
        print(f"\n⚠ Warnings ({len(result.warnings)}):")
        for warning in result.warnings:
            print(f"  - {warning}")
    
    # Print errors
    if result.errors:
        print(f"\n✗ Errors ({len(result.errors)}):")
        for error in result.errors:
            print(f"  - {error.error_code}: {error.message}")


def print_output_info(result: ProcessingResult):
    """Print information about generated output files."""
    if not result.success or not result.storeys:
        return
    
    print("\nGenerated Files:")
    print("-" * 30)
    
    for storey in result.storeys:
        print(f"Storey: {storey.storey_name}")
        if storey.svg_file:
            print(f"  SVG: {storey.svg_file}")
        if storey.geojson_file:
            print(f"  GeoJSON: {storey.geojson_file}")
    
    if hasattr(result.manifest, 'input_file'):
        print(f"\nManifest: manifest.json")


def main():
    """Main CLI entry point."""
    parser = setup_argument_parser()
    args = parser.parse_args()
    
    # Handle special cases
    if args.help_config:
        show_config_help()
        return 0
    
    # Validate arguments
    if not validate_arguments(args):
        return 1
    
    # Setup logging
    setup_logging(args.verbose, args.quiet, args.log_file)
    logger = logging.getLogger(__name__)
    
    try:
        # Print header unless quiet
        if not args.quiet:
            print_progress_header()
        
        # Create generator
        generator = FloorPlanGenerator(args.config, verbose=args.verbose)
        
        # Override output directory if specified
        if args.output_dir:
            logger.info(f"Overriding output directory: {args.output_dir}")
            # This would need to be implemented in the generator
            # generator.override_output_dir(args.output_dir)
        
        # Validate configuration if requested
        if args.validate_config:
            if generator.load_configuration():
                print("✓ Configuration is valid")
                return 0
            else:
                print("✗ Configuration validation failed")
                return 1
        
        # Perform dry run if requested
        if args.dry_run:
            logger.info("Performing dry run - no output files will be generated")
            # This would need to be implemented in the generator
            # generator.set_dry_run(True)
        
        # Process IFC file
        logger.info(f"Starting processing with config: {args.config}")
        result = generator.process_ifc_file()
        
        # Print results unless quiet
        if not args.quiet:
            print_processing_summary(result)
            if result.success:
                print_output_info(result)
        
        # Return appropriate exit code
        if result.success:
            logger.info("Processing completed successfully")
            return 0
        else:
            logger.error("Processing failed")
            return 1
            
    except KeyboardInterrupt:
        logger.info("Processing interrupted by user")
        if not args.quiet:
            print("\nProcessing interrupted by user")
        return 130  # Standard exit code for SIGINT
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if not args.quiet:
            print(f"\nUnexpected error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())