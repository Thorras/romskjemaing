#!/usr/bin/env python3
"""
Romskjema Generator - Main Application

Enhanced room schedule generator with Phase 2B and 2C features,
data quality analysis, and advanced export capabilities.
"""

import sys
import os
import argparse
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from ifc_room_schedule.parser.ifc_file_reader import IfcFileReader
from ifc_room_schedule.parser.ifc_space_extractor import IfcSpaceExtractor
from ifc_room_schedule.export.enhanced_json_builder import EnhancedJsonBuilder
from ifc_room_schedule.analysis.data_quality_analyzer import DataQualityAnalyzer
from ifc_room_schedule.parser.batch_processor import BatchProcessor
from ifc_room_schedule.utils.caching_manager import CachingManager, CacheConfig
from ifc_room_schedule.export.csv_exporter import CsvExporter
from ifc_room_schedule.export.excel_exporter import ExcelExporter
from ifc_room_schedule.export.pdf_exporter import PdfExporter
from ifc_room_schedule.export.azure_sql_exporter import AzureSQLExporter
from ifc_room_schedule.data.space_model import SpaceData


class RomskjemaGenerator:
    """Main application class for the Romskjema Generator."""
    
    def __init__(self):
        """Initialize the application."""
        self.version = "2.0.0"
        self.ifc_reader = IfcFileReader()
        self.space_extractor = IfcSpaceExtractor()
        self.json_builder = EnhancedJsonBuilder()
        self.quality_analyzer = DataQualityAnalyzer()
        self.batch_processor = BatchProcessor()
        self.cache_manager = CachingManager()
        
        # Exporters
        self.csv_exporter = CsvExporter()
        self.excel_exporter = ExcelExporter()
        self.pdf_exporter = PdfExporter()
        self.sql_exporter = None  # Initialized when needed
    
    def process_ifc_file(self, 
                        ifc_path: str, 
                        output_path: str,
                        export_profile: str = "production",
                        export_format: str = "json",
                        batch_mode: bool = False,
                        chunk_size: int = 100,
                        azure_connection_string: str = None,
                        azure_table_name: str = "room_schedule") -> Dict[str, Any]:
        """
        Process IFC file and generate room schedule.
        
        Args:
            ifc_path: Path to IFC file
            output_path: Path for output file
            export_profile: Export profile (core, advanced, production)
            export_format: Export format (json, csv, excel, pdf, azure-sql)
            batch_mode: Enable batch processing
            chunk_size: Chunk size for batch processing
            azure_connection_string: Azure SQL connection string (required for azure-sql export)
            azure_table_name: Azure SQL table name for export
            
        Returns:
            Processing statistics
        """
        print(f"Romskjema Generator v{self.version}")
        print("=" * 50)
        
        start_time = time.time()
        
        try:
            # Load IFC file
            print(f"Loading IFC file: {ifc_path}")
            success, message = self.ifc_reader.load_file(ifc_path)
            if not success:
                return {"error": f"Failed to load IFC file: {message}"}
            
            # Extract spaces
            self.space_extractor.set_ifc_file(self.ifc_reader.get_ifc_file())
            spaces = self.space_extractor.extract_spaces()
            print(f"Loaded {len(spaces)} spaces")
            
            if not spaces:
                print("Warning: No spaces found in IFC file")
                return {"error": "No spaces found"}
            
            # Analyze data quality
            print("Analyzing data quality...")
            quality_report = self.quality_analyzer.analyze_spaces_quality(spaces)
            self._print_quality_report(quality_report)
            
            # Process spaces
            if batch_mode and len(spaces) > chunk_size:
                print(f"Processing {len(spaces)} spaces in batch mode (chunk size: {chunk_size})")
                stats = self._process_batch(spaces, output_path, export_profile, export_format, chunk_size, azure_connection_string, azure_table_name)
            else:
                print(f"Processing {len(spaces)} spaces in standard mode")
                stats = self._process_standard(spaces, output_path, export_profile, export_format, azure_connection_string, azure_table_name)
            
            # Final statistics
            processing_time = time.time() - start_time
            stats["total_processing_time"] = processing_time
            stats["spaces_processed"] = len(spaces)
            
            print(f"\nProcessing completed in {processing_time:.2f} seconds")
            print(f"Output saved to: {output_path}")
            
            return stats
            
        except Exception as e:
            print(f"Error processing IFC file: {str(e)}")
            return {"error": str(e)}
    
    def _process_standard(self, 
                         spaces: List[SpaceData], 
                         output_path: str,
                         export_profile: str,
                         export_format: str,
                         azure_connection_string: str = None,
                         azure_table_name: str = "room_schedule") -> Dict[str, Any]:
        """Process spaces in standard mode."""
        try:
            if export_format == "json":
                # Build enhanced JSON structure
                enhanced_data = self.json_builder.build_enhanced_json_structure(
                    spaces=spaces,
                    export_profile=export_profile
                )
                
                # Write to file
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(enhanced_data, f, indent=2, ensure_ascii=False)
                
                return {"success": True, "format": "json"}
            
            elif export_format == "csv":
                success = self.csv_exporter.export_to_csv(spaces, output_path)
                return {"success": success, "format": "csv"}
            
            elif export_format == "excel":
                success = self.excel_exporter.export_to_excel(spaces, output_path)
                return {"success": success, "format": "excel"}
            
            elif export_format == "pdf":
                success = self.pdf_exporter.export_to_pdf(spaces, output_path)
                return {"success": success, "format": "pdf"}
            
            elif export_format == "azure-sql":
                try:
                    # Initialize SQL exporter if not already done
                    if not self.sql_exporter:
                        if azure_connection_string:
                            # Use provided connection string
                            self.sql_exporter = AzureSQLExporter(azure_connection_string)
                        else:
                            # Use default configuration
                            self.sql_exporter = AzureSQLExporter.create_with_default_config()
                            print("Using default Azure SQL database configuration")
                    
                    # Build enhanced JSON structure for SQL export
                    enhanced_data = self.json_builder.build_enhanced_json_structure(
                        spaces=spaces,
                        export_profile=export_profile
                    )
                    
                    # Use provided table name or default
                    table_name = azure_table_name or "room_schedule"
                    
                    # Export to Azure SQL
                    success = self.sql_exporter.export_data(enhanced_data, table_name)
                    return {"success": success, "format": "azure-sql"}
                    
                except Exception as e:
                    return {"error": f"Azure SQL export failed: {str(e)}"}
            
            else:
                return {"error": f"Unsupported export format: {export_format}"}
                
        except Exception as e:
            return {"error": str(e)}
    
    def _process_batch(self, 
                      spaces: List[SpaceData], 
                      output_path: str,
                      export_profile: str,
                      export_format: str,
                      chunk_size: int,
                      azure_connection_string: str = None,
                      azure_table_name: str = "room_schedule") -> Dict[str, Any]:
        """Process spaces in batch mode."""
        try:
            if export_format == "json":
                # Use batch processor for JSON export
                stats = self.batch_processor.process_spaces_batch(
                    spaces=spaces,
                    output_path=output_path,
                    export_profile=export_profile
                )
                return stats
            
            else:
                # For other formats, use standard processing
                return self._process_standard(spaces, output_path, export_profile, export_format, azure_connection_string, azure_table_name)
                
        except Exception as e:
            return {"error": str(e)}
    
    def _print_quality_report(self, quality_report: Dict[str, Any]):
        """Print data quality report."""
        if not quality_report:
            return
        
        print("\nData Quality Report:")
        print("-" * 30)
        
        total_spaces = quality_report.get("total_spaces", 0)
        print(f"Total spaces: {total_spaces}")
        
        compliance_stats = quality_report.get("compliance_stats", {})
        for metric, count in compliance_stats.items():
            percentage = (count / total_spaces * 100) if total_spaces > 0 else 0
            print(f"{metric}: {count}/{total_spaces} ({percentage:.1f}%)")
        
        # Print recommendations
        recommendations = quality_report.get("recommendations", [])
        if recommendations:
            print("\nRecommendations:")
            for rec in recommendations:
                print(f"  • {rec}")
    
    def run_gui(self):
        """Run the GUI application."""
        try:
            from PyQt6.QtWidgets import QApplication
            from ifc_room_schedule.ui.main_window import MainWindow
            
            app = QApplication(sys.argv)
            window = MainWindow()
            window.show()
            
            return app.exec()
            
        except ImportError:
            print("PyQt6 not available. GUI mode not supported.")
            print("Please install PyQt6 to use the GUI: pip install PyQt6")
            return 1
        except Exception as e:
            print(f"Error starting GUI: {str(e)}")
            return 1
    
    def run_cli(self, args):
        """Run the CLI application."""
        if args.version:
            print(f"Romskjema Generator v{self.version}")
            return 0
        
        if not args.input:
            print("Error: Input IFC file is required")
            return 1
        
        if not os.path.exists(args.input):
            print(f"Error: Input file not found: {args.input}")
            return 1
        
        # Determine output path
        if args.output:
            output_path = args.output
        else:
            input_name = Path(args.input).stem
            output_path = f"{input_name}_room_schedule.{args.format}"
        
        # Validate Azure SQL parameters if needed
        if args.format == "azure-sql":
            if not args.azure_connection_string:
                print("Info: Using default Azure SQL database configuration")
                print("Set AZURE_SQL_PASSWORD environment variable or use --azure-connection-string")
        
        # Process IFC file
        stats = self.process_ifc_file(
            ifc_path=args.input,
            output_path=output_path,
            export_profile=args.profile,
            export_format=args.format,
            batch_mode=args.batch,
            chunk_size=args.chunk_size,
            azure_connection_string=getattr(args, 'azure_connection_string', None),
            azure_table_name=getattr(args, 'azure_table_name', None)
        )
        
        if "error" in stats:
            print(f"Error: {stats['error']}")
            return 1
        
        if stats.get("success", False):
            print("Export completed successfully!")
            return 0
        else:
            print("Export failed!")
            return 1


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Romskjema Generator - Enhanced room schedule generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python main.py --input building.ifc --output room_schedule.json
  
  # Advanced export with specific profile
  python main.py --input building.ifc --output room_schedule.json --profile production
  
  # Batch processing for large files
  python main.py --input large_building.ifc --output room_schedule.json --batch --chunk-size 200
  
  # Export to different formats
  python main.py --input building.ifc --output room_schedule.csv --format csv
  python main.py --input building.ifc --output room_schedule.xlsx --format excel
  python main.py --input building.ifc --output room_schedule.pdf --format pdf
  
  # Export to Azure SQL (using default configuration)
  python main.py --input building.ifc --format azure-sql
  
  # Export to Azure SQL (with custom connection)
  python main.py --input building.ifc --format azure-sql --azure-connection-string "Server=..." --azure-table-name "rooms"
  
  # GUI mode
  python main.py --gui
        """
    )
    
    parser.add_argument(
        "--input", "-i",
        help="Input IFC file path"
    )
    
    parser.add_argument(
        "--output", "-o",
        help="Output file path (default: auto-generated)"
    )
    
    parser.add_argument(
        "--profile", "-p",
        choices=["core", "advanced", "production"],
        default="production",
        help="Export profile (default: production)"
    )
    
    parser.add_argument(
        "--format", "-f",
        choices=["json", "csv", "excel", "pdf", "azure-sql"],
        default="json",
        help="Export format (default: json)"
    )
    
    parser.add_argument(
        "--batch", "-b",
        action="store_true",
        help="Enable batch processing for large files"
    )
    
    parser.add_argument(
        "--chunk-size", "-c",
        type=int,
        default=100,
        help="Chunk size for batch processing (default: 100)"
    )
    
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Run in GUI mode"
    )
    
    parser.add_argument(
        "--azure-connection-string",
        help="Azure SQL connection string (required for azure-sql format)"
    )
    
    parser.add_argument(
        "--azure-table-name",
        default="room_schedule",
        help="Azure SQL table name (default: room_schedule)"
    )
    
    parser.add_argument(
        "--version", "-v",
        action="store_true",
        help="Show version information"
    )
    
    args = parser.parse_args()
    
    # Create application instance
    app = RomskjemaGenerator()
    
    # Run appropriate mode
    if args.gui:
        return app.run_gui()
    else:
        return app.run_cli(args)


if __name__ == "__main__":
    sys.exit(main())