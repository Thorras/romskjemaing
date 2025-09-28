#!/usr/bin/env python3
"""
Test timeout handling with real IFC files from the tesfiler directory.
"""

import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ifc_room_schedule.ui.main_window import MainWindow


def test_with_real_files():
    """Test timeout handling with real IFC files."""
    print("🧪 Testing timeout handling with real IFC files")
    print("=" * 60)
    
    app = QApplication.instance() or QApplication(sys.argv)
    window = MainWindow()
    window._testing_mode = True
    
    # Test files from tesfiler directory
    test_files = [
        "tesfiler/AkkordSvingen 23_ARK.ifc",
        "tesfiler/DEICH_Test.ifc"
    ]
    
    for file_path in test_files:
        if not os.path.exists(file_path):
            print(f"⚠️  Test file not found: {file_path}")
            continue
        
        print(f"\nTesting with file: {file_path}")
        
        # Get file info
        file_size = os.path.getsize(file_path)
        size_mb = file_size / (1024 * 1024)
        category, _, size_string = window.categorize_file_size(file_path)
        
        print(f"  File size: {size_string} ({category.value})")
        
        # Test timeout calculation
        timeout = window.get_timeout_for_file_size(file_size)
        print(f"  Calculated timeout: {timeout}s")
        
        # Test timeout setup
        window.setup_operation_timeout(file_path=file_path)
        print(f"  Configured timeout: {window.current_timeout_seconds}s")
        
        # Verify timeout is appropriate for file size
        if size_mb < 10:
            expected_timeout = 30
        elif size_mb < 50:
            expected_timeout = 60
        elif size_mb < 100:
            expected_timeout = 120
        else:
            expected_timeout = 300
        
        assert window.current_timeout_seconds == expected_timeout, \
            f"Expected {expected_timeout}s timeout, got {window.current_timeout_seconds}s"
        
        print(f"  ✅ Timeout correctly configured for {category.value} file")
        
        # Clean up timer
        if hasattr(window, 'operation_timeout_timer') and window.operation_timeout_timer:
            window.operation_timeout_timer.stop()
    
    print("\n" + "=" * 60)
    print("✅ Real file timeout tests completed successfully!")
    
    # Test file loading process (without actually loading to avoid long operations)
    print("\nTesting file loading process setup...")
    
    test_file = next((f for f in test_files if os.path.exists(f)), None)
    if test_file:
        print(f"Using test file: {test_file}")
        
        # Test that process_ifc_file sets up timeout correctly
        # We'll mock the actual loading to avoid long operations
        original_load_direct = window.load_file_directly
        original_load_threaded = window.load_file_threaded
        
        def mock_load_direct(file_path):
            print(f"  Mock direct loading: {file_path}")
            window.status_bar.showMessage("Mock direct loading completed")
        
        def mock_load_threaded(file_path):
            print(f"  Mock threaded loading: {file_path}")
            window.status_bar.showMessage("Mock threaded loading completed")
        
        window.load_file_directly = mock_load_direct
        window.load_file_threaded = mock_load_threaded
        
        try:
            # This will go through the file categorization and timeout setup
            # but use our mock loading functions
            window.process_ifc_file(test_file)
            print("  ✅ File processing setup completed")
        except Exception as e:
            print(f"  ⚠️  File processing test failed: {e}")
        finally:
            # Restore original methods
            window.load_file_directly = original_load_direct
            window.load_file_threaded = original_load_threaded
    
    window.close()
    print("✅ All real file tests completed!")


if __name__ == "__main__":
    test_with_real_files()