#!/usr/bin/env python3
"""
Test script for enhanced logging and error reporting system.
"""

import sys
import os
import tempfile
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

def test_enhanced_logging():
    """Test the enhanced logging system."""
    print("Testing Enhanced Logging System...")
    
    try:
        from ifc_room_schedule.utils.enhanced_logging import (
            enhanced_logger, ErrorCategory, ErrorSeverity, MemoryErrorAnalyzer
        )
        print("✓ Enhanced logging module imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import enhanced logging: {e}")
        return False
    
    # Test basic logging
    try:
        enhanced_logger.logger.info("Test info message")
        enhanced_logger.logger.warning("Test warning message")
        enhanced_logger.logger.error("Test error message")
        print("✓ Basic logging works")
    except Exception as e:
        print(f"✗ Basic logging failed: {e}")
        return False
    
    # Test operation timing
    try:
        operation_id = enhanced_logger.start_operation_timing("test_operation")
        import time
        time.sleep(0.1)  # Simulate work
        timing = enhanced_logger.finish_operation_timing(operation_id)
        if timing and timing.duration_seconds > 0:
            print(f"✓ Operation timing works: {timing.duration_seconds:.3f}s")
        else:
            print("✗ Operation timing failed")
            return False
    except Exception as e:
        print(f"✗ Operation timing failed: {e}")
        return False
    
    # Test error reporting
    try:
        error_report = enhanced_logger.create_error_report(
            ErrorCategory.MEMORY,
            ErrorSeverity.HIGH,
            "Test Error",
            "This is a test error message",
            user_guidance="Test guidance",
            recovery_suggestions=["Test suggestion 1", "Test suggestion 2"]
        )
        if error_report and error_report.error_id:
            print(f"✓ Error reporting works: {error_report.error_id}")
        else:
            print("✗ Error reporting failed")
            return False
    except Exception as e:
        print(f"✗ Error reporting failed: {e}")
        return False
    
    # Test memory error analyzer
    try:
        guidance, suggestions = MemoryErrorAnalyzer.analyze_memory_error(
            50 * 1024 * 1024,  # 50MB file
            100 * 1024 * 1024  # 100MB available memory
        )
        if guidance and suggestions:
            print(f"✓ Memory error analyzer works")
            print(f"  Guidance: {guidance[:50]}...")
            print(f"  Suggestions: {len(suggestions)} items")
        else:
            print("✗ Memory error analyzer failed")
            return False
    except Exception as e:
        print(f"✗ Memory error analyzer failed: {e}")
        return False
    
    # Test memory recommendations
    try:
        recommendations = MemoryErrorAnalyzer.get_memory_recommendations(25.0)
        if recommendations and 'recommended_ram' in recommendations:
            print(f"✓ Memory recommendations work: {recommendations['recommended_ram']}")
        else:
            print("✗ Memory recommendations failed")
            return False
    except Exception as e:
        print(f"✗ Memory recommendations failed: {e}")
        return False
    
    return True

def test_ifc_file_reader_integration():
    """Test integration with IFC file reader."""
    print("\nTesting IFC File Reader Integration...")
    
    try:
        from ifc_room_schedule.parser.ifc_file_reader import IfcFileReader
        print("✓ IFC file reader imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import IFC file reader: {e}")
        return False
    
    # Test with non-existent file (should generate enhanced error)
    try:
        reader = IfcFileReader()
        success, message = reader.load_file("non_existent_file.ifc")
        if not success and "not found" in message.lower():
            print("✓ Enhanced error handling for missing file works")
        else:
            print(f"✗ Unexpected result for missing file: {success}, {message}")
            return False
    except Exception as e:
        print(f"✗ Error testing missing file: {e}")
        return False
    
    # Test with invalid file format
    try:
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as temp_file:
            temp_file.write(b"This is not an IFC file")
            temp_file_path = temp_file.name
        
        success, message = reader.load_file(temp_file_path)
        if not success and "invalid file format" in message.lower():
            print("✓ Enhanced error handling for invalid format works")
        else:
            print(f"✗ Unexpected result for invalid format: {success}, {message}")
            return False
        
        # Clean up
        os.unlink(temp_file_path)
        
    except Exception as e:
        print(f"✗ Error testing invalid format: {e}")
        return False
    
    return True

def main():
    """Run all tests."""
    print("=" * 60)
    print("ENHANCED LOGGING AND ERROR REPORTING TESTS")
    print("=" * 60)
    
    success = True
    
    # Test enhanced logging system
    if not test_enhanced_logging():
        success = False
    
    # Test IFC file reader integration
    if not test_ifc_file_reader_integration():
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("✅ All enhanced logging tests passed!")
        print("\nEnhanced logging features:")
        print("- Structured error reporting with categories and severity")
        print("- Detailed operation timing and performance logging")
        print("- Memory error analysis with specific guidance")
        print("- Enhanced error messages with recovery suggestions")
        print("- System context collection for debugging")
    else:
        print("❌ Some enhanced logging tests failed!")
        print("Check the error messages above for details.")
    
    print("=" * 60)
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())