#!/usr/bin/env python3
"""
Integration test to verify fallback mechanism works with real IFC files.
"""

import sys
import os
import logging
from unittest.mock import patch, MagicMock
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QThread

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ifc_room_schedule.ui.main_window import MainWindow

def test_fallback_with_real_file():
    """Test fallback mechanism with a real IFC file."""
    print("Testing fallback mechanism with real IFC file...")
    
    # Find a test file
    test_files = [
        "tesfiler/AkkordSvingen 23_ARK.ifc",
        "tesfiler/DEICH_Test.ifc"
    ]
    
    test_file = None
    for file_path in test_files:
        if os.path.exists(file_path):
            test_file = file_path
            break
    
    if not test_file:
        print("  ⚠️ No test files found, skipping integration test")
        return True
    
    print(f"  Using test file: {test_file}")
    
    app = QApplication([])
    window = MainWindow()
    window._testing_mode = True
    
    # Set the file path
    window.current_file_path = test_file
    
    # Test 1: Simulate threading failure and verify fallback is offered
    print("  Testing threading failure detection...")
    
    with patch.object(window, 'show_enhanced_error_message', return_value='fallback_direct') as mock_dialog:
        window._handle_threading_error_with_fallback("Simulated threading error")
        
        # Verify that the error dialog was shown with fallback options
        mock_dialog.assert_called_once()
        call_args = mock_dialog.call_args
        assert 'fallback_direct' in str(call_args), "Fallback option not offered"
        print("    ✅ Threading failure properly detected and fallback offered")
    
    # Test 2: Test direct loading fallback
    print("  Testing direct loading fallback...")
    
    # Mock the load_file_directly method to avoid actually loading the file
    with patch.object(window, 'load_file_directly') as mock_load:
        window._attempt_direct_loading_fallback()
        mock_load.assert_called_once_with(test_file)
        print("    ✅ Direct loading fallback attempted correctly")
    
    # Test 3: Verify statistics are tracked
    print("  Testing statistics tracking...")
    stats = window.fallback_stats
    assert stats['threading_failures'] > 0, "Threading failures not tracked"
    assert stats['fallback_attempts'] > 0, "Fallback attempts not tracked"
    assert len(stats['fallback_reasons']) > 0, "Fallback reasons not tracked"
    print(f"    ✅ Statistics tracked: {stats['threading_failures']} failures, {stats['fallback_attempts']} attempts")
    
    app.quit()
    print("  Integration test completed successfully\n")
    return True

def test_thread_startup_failure_simulation():
    """Test thread startup failure with mocked QThread."""
    print("Testing thread startup failure simulation...")
    
    app = QApplication([])
    window = MainWindow()
    window._testing_mode = True
    
    # Mock QThread to fail on start
    original_qthread = QThread
    
    class FailingQThread(QThread):
        def start(self):
            raise RuntimeError("Simulated thread startup failure")
    
    def mock_operation():
        return "test result"
    
    with patch('ifc_room_schedule.ui.main_window.QThread', FailingQThread):
        with patch.object(window, 'show_enhanced_error_message', return_value='fallback_direct'):
            with patch.object(window, '_execute_operation_directly') as mock_execute:
                # This should trigger the thread startup failure handling
                window.show_non_blocking_progress("Test Operation", mock_operation)
                
                # Verify fallback was attempted
                mock_execute.assert_called_once()
                print("  ✅ Thread startup failure handled with fallback")
    
    app.quit()
    print("Thread startup failure simulation completed\n")
    return True

def main():
    """Run integration tests for fallback mechanism."""
    print("=== Integration Testing Fallback Mechanism ===\n")
    
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    try:
        success1 = test_fallback_with_real_file()
        success2 = test_thread_startup_failure_simulation()
        
        if success1 and success2:
            print("=== All Integration Tests Passed ===")
            return True
        else:
            print("❌ Some integration tests failed")
            return False
            
    except Exception as e:
        print(f"❌ Integration test failed with error: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)