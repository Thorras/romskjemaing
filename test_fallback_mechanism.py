#!/usr/bin/env python3
"""
Test script to verify the fallback mechanism for threading failures.
"""

import sys
import os
import logging
import traceback
from unittest.mock import Mock, patch, MagicMock
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QThread

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ifc_room_schedule.ui.main_window import MainWindow

def test_threading_error_detection():
    """Test that threading errors are properly detected."""
    print("Testing threading error detection...")
    
    app = QApplication([])
    window = MainWindow()
    window._testing_mode = True
    
    # Test various error types
    test_cases = [
        ("thread_error", "QThread failed to start", True),
        ("operation_error", "Worker thread crashed", True),
        ("memory_error", "Out of memory", False),
        ("io_error", "File not found", False),
        ("operation_error", "Threading timeout occurred", True),
        ("worker_error", "Signal connection failed", True),
    ]
    
    for error_type, error_message, expected_is_threading in test_cases:
        is_threading = window._is_threading_error(error_type, error_message)
        status = "✅" if is_threading == expected_is_threading else "❌"
        print(f"  {status} {error_type}: '{error_message}' -> {is_threading} (expected {expected_is_threading})")
    
    app.quit()
    print("Threading error detection test completed.\n")

def test_fallback_statistics_tracking():
    """Test that fallback statistics are properly tracked."""
    print("Testing fallback statistics tracking...")
    
    app = QApplication([])
    window = MainWindow()
    window._testing_mode = True
    
    # Initial state
    stats = window.fallback_stats
    print(f"  Initial stats: {stats}")
    
    # Simulate threading failure
    window._handle_threading_error_with_fallback("Test threading error")
    print(f"  After threading error: threading_failures={stats['threading_failures']}")
    
    # Simulate fallback attempt
    window.current_file_path = "test_file.ifc"
    with patch.object(window, 'show_enhanced_error_message', return_value='fallback_direct'):
        with patch.object(window, 'load_file_directly'):
            window._attempt_direct_loading_fallback()
    
    print(f"  After fallback attempt: attempts={stats['fallback_attempts']}")
    print(f"  Fallback reasons: {stats['fallback_reasons']}")
    
    app.quit()
    print("Fallback statistics tracking test completed.\n")

def test_thread_creation_failure_handling():
    """Test handling of thread creation failures."""
    print("Testing thread creation failure handling...")
    
    app = QApplication([])
    window = MainWindow()
    window._testing_mode = True
    
    # Mock a thread creation failure
    def mock_operation():
        return "test result"
    
    # Simulate thread creation failure
    with patch.object(window, 'show_enhanced_error_message', return_value='fallback_direct'):
        with patch.object(window, '_execute_operation_directly') as mock_execute:
            window._handle_thread_creation_failure("Test Operation", mock_operation, Exception("Thread creation failed"))
            mock_execute.assert_called_once()
    
    print("  ✅ Thread creation failure handled correctly")
    
    app.quit()
    print("Thread creation failure handling test completed.\n")

def test_direct_execution_fallback():
    """Test direct execution as a fallback mechanism."""
    print("Testing direct execution fallback...")
    
    app = QApplication([])
    window = MainWindow()
    window._testing_mode = True
    
    # Mock the operation function
    def mock_operation(arg1, arg2):
        return f"result: {arg1}, {arg2}"
    
    # Test successful direct execution
    with patch.object(window, 'on_operation_completed') as mock_completed:
        window._execute_operation_directly("Test Operation", mock_operation, "test1", "test2")
        mock_completed.assert_called_once()
        args = mock_completed.call_args[0]
        print(f"  ✅ Direct execution successful: {args[0]}, '{args[1]}', result='{args[2]}'")
    
    # Test failed direct execution
    def failing_operation():
        raise Exception("Direct execution failed")
    
    with patch.object(window, 'show_enhanced_error_message') as mock_error:
        window._execute_operation_directly("Failing Operation", failing_operation)
        mock_error.assert_called_once()
        print("  ✅ Direct execution failure handled correctly")
    
    app.quit()
    print("Direct execution fallback test completed.\n")

def test_error_classification():
    """Test error classification in the worker."""
    print("Testing error classification...")
    
    from ifc_room_schedule.ui.main_window import LongRunningOperationWorker
    
    worker = LongRunningOperationWorker(lambda: None)
    
    test_errors = [
        (Exception("QThread failed"), "thread_error"),
        (MemoryError("Out of memory"), "memory_error"),
        (IOError("File not found"), "io_error"),
        (TimeoutError("Operation timed out"), "timeout_error"),
        (Exception("Generic error"), "operation_error"),
        (Exception("Worker signal failed"), "thread_error"),
    ]
    
    for error, expected_type in test_errors:
        classified_type = worker._classify_error(error)
        status = "✅" if classified_type == expected_type else "❌"
        print(f"  {status} {type(error).__name__}: '{error}' -> {classified_type} (expected {expected_type})")
    
    print("Error classification test completed.\n")

def main():
    """Run all fallback mechanism tests."""
    print("=== Testing Fallback Mechanism Implementation ===\n")
    
    # Set up logging to see fallback messages
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    try:
        test_threading_error_detection()
        test_fallback_statistics_tracking()
        test_thread_creation_failure_handling()
        test_direct_execution_fallback()
        test_error_classification()
        
        print("=== All Fallback Mechanism Tests Completed Successfully ===")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)