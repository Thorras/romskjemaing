#!/usr/bin/env python3
"""
Demo script to test comprehensive error handling in IFC Room Schedule Application.

This script demonstrates various error scenarios and recovery mechanisms.
"""

import sys
import logging
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from ifc_room_schedule.ui.main_window import MainWindow


def create_test_scenarios():
    """Create various test scenarios for error handling."""
    scenarios = {
        'invalid_file': {
            'description': 'Test invalid file format error',
            'file_path': 'test_files/invalid.txt',
            'expected_error': 'Invalid file format'
        },
        'missing_file': {
            'description': 'Test missing file error',
            'file_path': 'test_files/nonexistent.ifc',
            'expected_error': 'File not found'
        },
        'memory_error': {
            'description': 'Test memory error handling',
            'action': 'simulate_memory_error',
            'expected_behavior': 'Show recovery options'
        },
        'parsing_error': {
            'description': 'Test IFC parsing error',
            'action': 'simulate_parsing_error',
            'expected_behavior': 'Continue with partial data'
        },
        'export_error': {
            'description': 'Test export error handling',
            'action': 'simulate_export_error',
            'expected_behavior': 'Show detailed error message'
        }
    }
    return scenarios


def test_file_operation_errors(main_window):
    """Test file operation error handling."""
    print("\n=== Testing File Operation Errors ===")
    
    # Test invalid file format
    print("1. Testing invalid file format...")
    result = main_window.handle_file_operation_error(
        "load invalid file",
        "test.txt",
        ValueError("Invalid file format")
    )
    print(f"   Result: {'Retry' if result else 'Cancel'}")

    # Test file not found
    print("2. Testing file not found...")
    result = main_window.handle_file_operation_error(
        "load missing file",
        "missing.ifc",
        FileNotFoundError("File not found")
    )
    print(f"   Result: {'Retry' if result else 'Cancel'}")

    # Test permission error
    print("3. Testing permission error...")
    result = main_window.handle_file_operation_error(
        "save export file",
        "/root/protected.json",
        PermissionError("Permission denied")
    )
    print(f"   Result: {'Retry' if result else 'Cancel'}")


def test_memory_error_handling(main_window):
    """Test memory error handling."""
    print("\n=== Testing Memory Error Handling ===")
    
    # Simulate memory error during IFC loading
    print("1. Testing memory error during IFC loading...")
    result = main_window.handle_memory_error(
        "IFC file loading",
        MemoryError("Insufficient memory for large IFC file")
    )
    print(f"   Result: {'Retry with reduced scope' if result else 'Abort'}")

    # Test memory cleanup
    print("2. Testing memory cleanup...")
    main_window.free_memory_resources()
    print("   Memory resources freed")


def test_parsing_error_handling(main_window):
    """Test parsing error handling."""
    print("\n=== Testing Parsing Error Handling ===")
    
    # Test space parsing error
    print("1. Testing space parsing error...")
    result = main_window.handle_parsing_error(
        "IfcSpaceExtractor",
        "Space_12345",
        AttributeError("Missing required property")
    )
    print(f"   Result: {'Continue parsing' if result else 'Stop parsing'}")

    # Test boundary parsing error
    print("2. Testing boundary parsing error...")
    result = main_window.handle_parsing_error(
        "IfcSpaceBoundaryParser",
        "Boundary_67890",
        ValueError("Invalid geometry data")
    )
    print(f"   Result: {'Continue parsing' if result else 'Stop parsing'}")


def test_batch_operation_errors(main_window):
    """Test batch operation error handling."""
    print("\n=== Testing Batch Operation Errors ===")
    
    # Simulate batch processing with some failures
    failed_items = [
        ("Space_001", "Missing geometry data"),
        ("Space_002", "Invalid property values"),
        ("Space_003", "Corrupted boundary data")
    ]
    
    skipped_items = [
        ("Space_004", "No space boundaries found"),
        ("Space_005", "Unsupported space type")
    ]
    
    print("1. Testing batch space processing errors...")
    choice = main_window.handle_batch_operation_errors(
        "Space Processing",
        10,  # total items
        failed_items,
        skipped_items
    )
    print(f"   User choice: {choice}")


def test_prerequisite_validation(main_window):
    """Test operation prerequisite validation."""
    print("\n=== Testing Prerequisite Validation ===")
    
    # Test export prerequisites
    prerequisites = {
        'ifc_file_loaded': (False, "No IFC file is currently loaded"),
        'spaces_extracted': (False, "No spaces have been extracted"),
        'export_path_selected': (True, "Export path is valid")
    }
    
    print("1. Testing export prerequisites...")
    result = main_window.validate_operation_prerequisites("export data", prerequisites)
    print(f"   Prerequisites met: {result}")
    
    # Test with all prerequisites met
    prerequisites_met = {
        'ifc_file_loaded': (True, "IFC file loaded successfully"),
        'spaces_extracted': (True, "Spaces extracted successfully"),
        'export_path_selected': (True, "Export path is valid")
    }
    
    print("2. Testing with all prerequisites met...")
    result = main_window.validate_operation_prerequisites("export data", prerequisites_met)
    print(f"   Prerequisites met: {result}")


def test_enhanced_error_messages(main_window):
    """Test enhanced error message display."""
    print("\n=== Testing Enhanced Error Messages ===")
    
    # Test error message with details
    print("1. Testing detailed error message...")
    main_window.show_enhanced_error_message(
        "IFC Processing Error",
        "Failed to process space boundaries",
        "Error details:\n- Missing geometry data for 3 boundaries\n- Invalid property values in 2 spaces\n- Corrupted data in boundary Space_001_Wall_North",
        "error"
    )
    
    # Test warning message
    print("2. Testing warning message...")
    main_window.show_enhanced_error_message(
        "Data Completeness Warning",
        "Some spaces have incomplete data",
        "5 spaces are missing surface descriptions\n3 spaces have no boundary data",
        "warning"
    )
    
    # Test info message
    print("3. Testing info message...")
    main_window.show_enhanced_error_message(
        "Processing Complete",
        "IFC file processed successfully with minor issues",
        "Successfully processed 95 of 100 spaces\n5 spaces skipped due to missing data",
        "info"
    )


def test_resource_cleanup_errors(main_window):
    """Test resource cleanup error handling."""
    print("\n=== Testing Resource Cleanup Errors ===")
    
    # Test cleanup error
    print("1. Testing resource cleanup error...")
    main_window.handle_resource_cleanup_error(
        "temporary cache files",
        OSError("Permission denied when deleting cache")
    )

    # Test critical cleanup error
    print("2. Testing critical cleanup error...")
    main_window.handle_resource_cleanup_error(
        "IFC file handle",
        IOError("Failed to close file handle")
    )


def test_error_recovery_scenarios(main_window):
    """Test various error recovery scenarios."""
    print("\n=== Testing Error Recovery Scenarios ===")
    
    # Test with recovery options
    recovery_options = {
        'retry': 'Retry the operation',
        'skip': 'Skip this item and continue',
        'abort': 'Abort the entire operation'
    }
    
    print("1. Testing error recovery options...")
    choice = main_window.show_enhanced_error_message(
        "Operation Failed",
        "Failed to process space boundary data",
        "Geometry calculation failed for boundary Space_001_Wall_North",
        "error",
        recovery_options
    )
    print(f"   Recovery choice: {choice}")


def run_error_handling_demo():
    """Run the comprehensive error handling demo."""
    print("IFC Room Schedule - Error Handling Demo")
    print("=" * 50)
    
    # Create QApplication
    app = QApplication(sys.argv)
    
    # Create main window
    main_window = MainWindow()
    main_window._testing_mode = True  # Prevent blocking dialogs in test mode
    main_window.show()
    
    # Schedule tests to run after the window is shown
    def run_tests():
        try:
            test_file_operation_errors(main_window)
            test_memory_error_handling(main_window)
            test_parsing_error_handling(main_window)
            test_batch_operation_errors(main_window)
            test_prerequisite_validation(main_window)
            test_enhanced_error_messages(main_window)
            test_resource_cleanup_errors(main_window)
            test_error_recovery_scenarios(main_window)
            
            print("\n" + "=" * 50)
            print("Error handling demo completed successfully!")
            print("All error scenarios have been tested.")
            print("\nThe application now has comprehensive error handling with:")
            print("- Enhanced error dialogs with detailed information")
            print("- Recovery options for various error scenarios")
            print("- Memory error handling with cleanup options")
            print("- Batch operation error management")
            print("- Prerequisite validation for operations")
            print("- Resource cleanup error handling")
            print("- Long-running operation progress tracking")
            print("- Graceful degradation for partial failures")
            
        except Exception as e:
            print(f"\nDemo error: {e}")
            import traceback
            traceback.print_exc()
        
        # Close the application after a delay
        QTimer.singleShot(2000, app.quit)
    
    # Run tests after a short delay to ensure UI is ready
    QTimer.singleShot(1000, run_tests)
    
    # Start the application
    return app.exec()


if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run the demo
    sys.exit(run_error_handling_demo())