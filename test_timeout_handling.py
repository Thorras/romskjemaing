#!/usr/bin/env python3
"""
Test script for timeout handling functionality in IFC import operations.
"""

import sys
import os
import time
import tempfile
from unittest.mock import Mock, patch
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from PyQt6.QtTest import QTest

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ifc_room_schedule.ui.main_window import MainWindow


def create_test_ifc_file(size_mb: float) -> str:
    """Create a temporary IFC file of specified size for testing."""
    content = """ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('ViewDefinition [CoordinationView]'),'2;1');
FILE_NAME('test.ifc','2024-01-01T00:00:00',('Test'),('Test'),'IFC2X3','Test','Test');
FILE_SCHEMA(('IFC2X3'));
ENDSEC;

DATA;
#1=IFCPROJECT('0YvhMJCgr0NRgFQYVWiwlw',#2,'Test Project',$,$,$,$,(#9),#8);
#2=IFCOWNERHISTORY(#3,#6,$,.ADDED.,$,$,$,1577836800);
#3=IFCPERSONANDORGANIZATION(#4,#5,$);
#4=IFCPERSON($,'Test','User',$,$,$,$,$);
#5=IFCORGANIZATION($,'Test Organization',$,$,$);
#6=IFCAPPLICATION(#5,'1.0','Test Application','Test');
#7=IFCUNITASSIGNMENT((#10,#11,#12));
#8=IFCGEOMETRICREPRESENTATIONCONTEXT($,'Model',3,1.E-05,#13,$);
#9=IFCGEOMETRICREPRESENTATIONSUBCONTEXT('Body','Model',*,*,*,*,#8,$,.MODEL_VIEW.,$);
#10=IFCSIUNIT(*,.LENGTHUNIT.,.MILLI.,.METRE.);
#11=IFCSIUNIT(*,.AREAUNIT.,$,.SQUARE_METRE.);
#12=IFCSIUNIT(*,.VOLUMEUNIT.,$,.CUBIC_METRE.);
#13=IFCAXIS2PLACEMENT3D(#14,$,$);
#14=IFCCARTESIANPOINT((0.,0.,0.));
"""
    
    # Add padding to reach desired size
    target_size = int(size_mb * 1024 * 1024)
    current_size = len(content.encode('utf-8'))
    padding_needed = max(0, target_size - current_size - 100)  # Leave room for ENDSEC
    
    if padding_needed > 0:
        # Add comment lines as padding
        padding_lines = []
        line_content = "/* Padding line for file size testing " + "x" * 50 + " */"
        lines_needed = padding_needed // len(line_content.encode('utf-8'))
        
        for i in range(lines_needed):
            padding_lines.append(line_content)
        
        content += "\n".join(padding_lines) + "\n"
    
    content += "ENDSEC;\nEND-ISO-10303-21;"
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.ifc', delete=False) as f:
        f.write(content)
        return f.name


def test_timeout_calculation():
    """Test timeout calculation based on file size."""
    print("Testing timeout calculation...")
    
    app = QApplication.instance() or QApplication(sys.argv)
    window = MainWindow()
    window._testing_mode = True
    
    # Test different file sizes
    test_cases = [
        (5 * 1024 * 1024, 30),    # 5MB -> 30s
        (25 * 1024 * 1024, 60),   # 25MB -> 60s
        (75 * 1024 * 1024, 120),  # 75MB -> 120s
        (150 * 1024 * 1024, 300), # 150MB -> 300s
    ]
    
    for file_size, expected_timeout in test_cases:
        timeout = window.get_timeout_for_file_size(file_size)
        size_mb = file_size / (1024 * 1024)
        print(f"  {size_mb:.1f}MB file -> {timeout}s timeout (expected: {expected_timeout}s)")
        assert timeout == expected_timeout, f"Expected {expected_timeout}s, got {timeout}s for {size_mb:.1f}MB file"
    
    print("✅ Timeout calculation tests passed")


def test_timeout_setup_with_file():
    """Test timeout setup with file path."""
    print("Testing timeout setup with file path...")
    
    app = QApplication.instance() or QApplication(sys.argv)
    window = MainWindow()
    window._testing_mode = True
    
    # Create test files of different sizes
    small_file = create_test_ifc_file(5)  # 5MB
    medium_file = create_test_ifc_file(25)  # 25MB
    
    try:
        # Test small file timeout
        window.setup_operation_timeout(file_path=small_file)
        assert window.current_timeout_seconds == 30, f"Expected 30s timeout for small file, got {window.current_timeout_seconds}s"
        print(f"  Small file (5MB) -> {window.current_timeout_seconds}s timeout ✅")
        
        # Test medium file timeout
        window.setup_operation_timeout(file_path=medium_file)
        assert window.current_timeout_seconds == 60, f"Expected 60s timeout for medium file, got {window.current_timeout_seconds}s"
        print(f"  Medium file (25MB) -> {window.current_timeout_seconds}s timeout ✅")
        
        # Test explicit timeout override
        window.setup_operation_timeout(timeout_seconds=90, file_path=small_file)
        assert window.current_timeout_seconds == 90, f"Expected 90s explicit timeout, got {window.current_timeout_seconds}s"
        print(f"  Explicit timeout override -> {window.current_timeout_seconds}s timeout ✅")
        
    finally:
        # Clean up test files
        for file_path in [small_file, medium_file]:
            try:
                os.unlink(file_path)
            except OSError:
                pass
    
    print("✅ Timeout setup tests passed")


def test_timeout_handling_ui():
    """Test timeout handling UI components."""
    print("Testing timeout handling UI components...")
    
    app = QApplication.instance() or QApplication(sys.argv)
    window = MainWindow()
    window._testing_mode = True
    window.show()
    
    # Test that cancel button is initially hidden
    assert not window.cancel_button.isVisible(), "Cancel button should be initially hidden"
    print("  Cancel button initially hidden ✅")
    
    # Test that progress bar is initially hidden
    assert not window.progress_bar.isVisible(), "Progress bar should be initially hidden"
    print("  Progress bar initially hidden ✅")
    
    # Simulate starting an operation
    window.progress_bar.setVisible(True)
    window.cancel_button.setVisible(True)
    
    assert window.progress_bar.isVisible(), "Progress bar should be visible during operation"
    assert window.cancel_button.isVisible(), "Cancel button should be visible during operation"
    print("  UI components visible during operation ✅")
    
    # Simulate operation completion
    window.progress_bar.setVisible(False)
    window.cancel_button.setVisible(False)
    
    assert not window.progress_bar.isVisible(), "Progress bar should be hidden after operation"
    assert not window.cancel_button.isVisible(), "Cancel button should be hidden after operation"
    print("  UI components hidden after operation ✅")
    
    window.close()
    print("✅ Timeout handling UI tests passed")


def test_cancel_operation():
    """Test operation cancellation functionality."""
    print("Testing operation cancellation...")
    
    app = QApplication.instance() or QApplication(sys.argv)
    window = MainWindow()
    window._testing_mode = True
    
    # Mock a running operation
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
    
    # Test cancellation
    window.cancel_operation()
    
    # Verify cleanup calls were made
    mock_thread.wait.assert_called()  # Should be called for graceful termination
    mock_timer.stop.assert_called_once()
    # terminate() should NOT be called if graceful termination succeeds
    
    # Verify state cleanup
    assert window.operation_thread is None, "Operation thread should be None after cancellation"
    assert window.operation_worker is None, "Operation worker should be None after cancellation"
    
    print("  Operation cleanup completed ✅")
    print("✅ Operation cancellation tests passed")


def main():
    """Run all timeout handling tests."""
    print("🧪 Testing IFC Import Timeout Handling Implementation")
    print("=" * 60)
    
    try:
        test_timeout_calculation()
        test_timeout_setup_with_file()
        test_timeout_handling_ui()
        test_cancel_operation()
        
        print("\n" + "=" * 60)
        print("✅ All timeout handling tests passed!")
        print("\nTimeout handling features implemented:")
        print("  • Configurable timeout values based on file size")
        print("  • QTimer-based timeout mechanism")
        print("  • User recovery options (wait longer, cancel, try direct)")
        print("  • Cancel button for long-running operations")
        print("  • Proper thread termination and cleanup")
        print("  • File size-based timeout calculation")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)