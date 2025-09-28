#!/usr/bin/env python3
"""
Test script for enhanced operation cancellation functionality.
"""

import sys
import os
import time
import threading
from unittest.mock import Mock, patch, MagicMock
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer, QThread
from PyQt6.QtTest import QTest

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ifc_room_schedule.ui.main_window import MainWindow, LongRunningOperationWorker


def slow_operation(*args, **kwargs):
    """Simulate a slow operation that can be cancelled."""
    for i in range(100):
        time.sleep(0.1)  # 10 seconds total
        # In a real operation, we would check for cancellation here
    return "Operation completed"


def cancellable_operation(worker):
    """Simulate an operation that checks for cancellation."""
    for i in range(100):
        if worker.is_cancelled():
            raise InterruptedError("Operation was cancelled")
        time.sleep(0.05)  # 5 seconds total
    return "Operation completed successfully"


def test_worker_cancellation_support():
    """Test that the worker class supports cancellation properly."""
    print("Testing worker cancellation support...")
    
    app = QApplication.instance() or QApplication(sys.argv)
    
    # Test worker initialization
    worker = LongRunningOperationWorker(slow_operation)
    assert not worker.is_cancelled(), "Worker should not be cancelled initially"
    assert not worker._cancel_requested, "Cancel should not be requested initially"
    print("  Worker initialization ✅")
    
    # Test cancellation request
    worker.request_cancellation()
    assert worker.is_cancelled(), "Worker should be cancelled after request"
    assert worker._cancel_requested, "Cancel should be requested after request"
    print("  Cancellation request ✅")
    
    # Test that cancelled worker emits cancellation signal
    cancellation_emitted = False
    def on_cancelled(message):
        nonlocal cancellation_emitted
        cancellation_emitted = True
        assert "cancelled before starting" in message.lower()
    
    worker.operation_cancelled.connect(on_cancelled)
    worker.run_operation()
    
    assert cancellation_emitted, "Cancellation signal should be emitted"
    print("  Cancellation signal emission ✅")
    
    print("✅ Worker cancellation support tests passed")


def test_cancel_button_functionality():
    """Test that the cancel button works properly."""
    print("Testing cancel button functionality...")
    
    app = QApplication.instance() or QApplication(sys.argv)
    window = MainWindow()
    window._testing_mode = True
    window.show()
    
    # Test initial state
    assert not window.cancel_button.isVisible(), "Cancel button should be initially hidden"
    assert not window.progress_bar.isVisible(), "Progress bar should be initially hidden"
    print("  Initial UI state ✅")
    
    # Simulate starting an operation
    window.progress_bar.setVisible(True)
    window.cancel_button.setVisible(True)
    window.cancel_button.setEnabled(True)
    
    # Create mock operation components
    mock_thread = Mock()
    mock_thread.isRunning.return_value = True
    mock_thread.wait.return_value = True
    mock_worker = Mock()
    mock_timer = Mock()
    
    window.operation_thread = mock_thread
    window.operation_worker = mock_worker
    window.operation_timeout_timer = mock_timer
    from datetime import datetime
    window.operation_start_time = datetime.now()
    
    # Test that cancel button is clickable
    assert window.cancel_button.isEnabled(), "Cancel button should be enabled during operation"
    print("  Cancel button enabled during operation ✅")
    
    # Test clicking cancel button
    window.cancel_button.click()
    
    # Verify that cancellation was requested
    mock_worker.request_cancellation.assert_called_once()
    mock_thread.wait.assert_called()
    mock_timer.stop.assert_called_once()
    
    # Verify UI cleanup
    assert not window.cancel_button.isVisible(), "Cancel button should be hidden after cancellation"
    assert not window.progress_bar.isVisible(), "Progress bar should be hidden after cancellation"
    print("  UI cleanup after cancellation ✅")
    
    window.close()
    print("✅ Cancel button functionality tests passed")


def test_graceful_vs_forced_termination():
    """Test graceful vs forced thread termination."""
    print("Testing graceful vs forced termination...")
    
    app = QApplication.instance() or QApplication(sys.argv)
    window = MainWindow()
    window._testing_mode = True
    
    # Test graceful termination
    mock_thread = Mock()
    mock_thread.isRunning.return_value = True
    mock_thread.wait.return_value = True  # Simulate successful graceful termination
    mock_worker = Mock()
    
    window.operation_thread = mock_thread
    window.operation_worker = mock_worker
    from datetime import datetime
    window.operation_start_time = datetime.now()
    
    window.cancel_operation()
    
    # Verify graceful termination was attempted
    mock_worker.request_cancellation.assert_called_once()
    mock_thread.wait.assert_called()
    mock_thread.terminate.assert_not_called()  # Should not force terminate if graceful works
    print("  Graceful termination ✅")
    
    # Test forced termination
    mock_thread.reset_mock()
    mock_worker.reset_mock()
    mock_thread.isRunning.return_value = True
    mock_thread.wait.side_effect = [False, True]  # First wait fails, second succeeds
    
    window.operation_thread = mock_thread
    window.operation_worker = mock_worker
    window.operation_start_time = datetime.now()
    
    window.cancel_operation()
    
    # Verify forced termination was used
    mock_worker.request_cancellation.assert_called_once()
    assert mock_thread.wait.call_count == 2  # Called twice (graceful + forced)
    mock_thread.terminate.assert_called_once()  # Should force terminate when graceful fails
    print("  Forced termination ✅")
    
    print("✅ Graceful vs forced termination tests passed")


def test_cancellation_during_timeout():
    """Test cancellation when timeout occurs."""
    print("Testing cancellation during timeout...")
    
    app = QApplication.instance() or QApplication(sys.argv)
    window = MainWindow()
    window._testing_mode = True
    
    # Mock a running operation that times out
    mock_thread = Mock()
    mock_thread.isRunning.return_value = True
    mock_thread.wait.return_value = True
    mock_worker = Mock()
    
    window.operation_thread = mock_thread
    window.operation_worker = mock_worker
    from datetime import datetime
    window.operation_start_time = datetime.now()
    window.current_timeout_seconds = 30
    
    # Simulate timeout handling choosing to cancel
    with patch.object(window, 'show_enhanced_error_message', return_value='cancel'):
        window.handle_operation_timeout()
    
    # Verify cancellation was triggered
    mock_worker.request_cancellation.assert_called_once()
    mock_thread.wait.assert_called()
    print("  Timeout-triggered cancellation ✅")
    
    print("✅ Cancellation during timeout tests passed")


def test_operation_state_cleanup():
    """Test that operation state is properly cleaned up after cancellation."""
    print("Testing operation state cleanup...")
    
    app = QApplication.instance() or QApplication(sys.argv)
    window = MainWindow()
    window._testing_mode = True
    
    # Set up operation state
    mock_thread = Mock()
    mock_thread.isRunning.return_value = True
    mock_thread.wait.return_value = True
    mock_worker = Mock()
    mock_timer = Mock()
    
    window.operation_thread = mock_thread
    window.operation_worker = mock_worker
    window.operation_timeout_timer = mock_timer
    from datetime import datetime
    window.operation_start_time = datetime.now()
    window.current_timeout_seconds = 60
    
    # Verify state is set
    assert window.operation_thread is not None
    assert window.operation_worker is not None
    assert window.operation_timeout_timer is not None
    assert window.operation_start_time is not None
    assert window.current_timeout_seconds is not None
    print("  Operation state setup ✅")
    
    # Cancel operation
    window.cancel_operation()
    
    # Verify complete cleanup
    assert window.operation_thread is None, "Operation thread should be None after cancellation"
    assert window.operation_worker is None, "Operation worker should be None after cancellation"
    assert window.operation_timeout_timer is None, "Timeout timer should be None after cancellation"
    assert window.operation_start_time is None, "Start time should be None after cancellation"
    assert window.current_timeout_seconds is None, "Timeout seconds should be None after cancellation"
    print("  Complete state cleanup ✅")
    
    print("✅ Operation state cleanup tests passed")


def test_ui_responsiveness_during_cancellation():
    """Test that UI remains responsive during cancellation."""
    print("Testing UI responsiveness during cancellation...")
    
    app = QApplication.instance() or QApplication(sys.argv)
    window = MainWindow()
    window._testing_mode = True
    window.show()
    
    # Start a mock operation
    window.progress_bar.setVisible(True)
    window.cancel_button.setVisible(True)
    
    # Mock components
    mock_thread = Mock()
    mock_thread.isRunning.return_value = True
    mock_thread.wait.return_value = True
    mock_worker = Mock()
    
    window.operation_thread = mock_thread
    window.operation_worker = mock_worker
    from datetime import datetime
    window.operation_start_time = datetime.now()
    
    # Test that UI is responsive before cancellation
    assert window.cancel_button.isEnabled(), "Cancel button should be enabled"
    print("  UI responsive before cancellation ✅")
    
    # Cancel operation
    window.cancel_operation()
    
    # Test that UI is responsive after cancellation
    assert not window.cancel_button.isVisible(), "Cancel button should be hidden"
    assert not window.progress_bar.isVisible(), "Progress bar should be hidden"
    print("  UI responsive after cancellation ✅")
    
    # Test that status bar is updated
    status_text = window.status_bar.currentMessage()
    assert "cancelled" in status_text.lower(), f"Status should indicate cancellation, got: {status_text}"
    print("  Status bar updated ✅")
    
    window.close()
    print("✅ UI responsiveness tests passed")


def main():
    """Run all cancellation functionality tests."""
    print("🧪 Testing Enhanced Operation Cancellation Functionality")
    print("=" * 65)
    
    try:
        test_worker_cancellation_support()
        test_cancel_button_functionality()
        test_graceful_vs_forced_termination()
        test_cancellation_during_timeout()
        test_operation_state_cleanup()
        test_ui_responsiveness_during_cancellation()
        
        print("\n" + "=" * 65)
        print("✅ All cancellation functionality tests passed!")
        print("\nEnhanced cancellation features implemented:")
        print("  • Cancel button visible during long operations")
        print("  • Graceful cancellation request to worker threads")
        print("  • Forced termination fallback for unresponsive threads")
        print("  • Proper thread termination and cleanup")
        print("  • Complete operation state cleanup")
        print("  • UI returns to ready state after cancellation")
        print("  • Cancellation signal handling in worker class")
        print("  • Timeout-triggered cancellation support")
        print("  • Status bar updates for cancellation feedback")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)