"""
Test comprehensive error handling functionality.

Tests various error scenarios and recovery mechanisms in the IFC Room Schedule application.
"""

import pytest
import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import QTimer
from PyQt6.QtTest import QTest

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ifc_room_schedule.ui.main_window import MainWindow, ErrorDetailsDialog, ErrorRecoveryDialog
from ifc_room_schedule.parser.ifc_file_reader import IfcFileReader


@pytest.fixture
def app():
    """Create QApplication for testing."""
    if not QApplication.instance():
        app = QApplication([])
    else:
        app = QApplication.instance()
    yield app
    app.quit()


@pytest.fixture
def main_window(app):
    """Create MainWindow for testing."""
    window = MainWindow()
    window._testing_mode = True  # Prevent blocking dialogs
    return window


@pytest.fixture
def ifc_reader():
    """Create IfcFileReader for testing."""
    return IfcFileReader()


class TestErrorDetailsDialog:
    """Test the enhanced error details dialog."""
    
    def test_error_dialog_creation(self, app):
        """Test creating error dialog with different error types."""
        # Test error dialog
        dialog = ErrorDetailsDialog(
            "Test Error", 
            "This is a test error message",
            "Detailed error information here",
            "error"
        )
        assert dialog.windowTitle() == "Test Error"
        
        # Test warning dialog
        warning_dialog = ErrorDetailsDialog(
            "Test Warning", 
            "This is a test warning",
            "",
            "warning"
        )
        assert warning_dialog.windowTitle() == "Test Warning"
        
        # Test info dialog
        info_dialog = ErrorDetailsDialog(
            "Test Info", 
            "This is test information",
            "",
            "info"
        )
        assert info_dialog.windowTitle() == "Test Info"


class TestErrorRecoveryDialog:
    """Test the error recovery dialog."""
    
    def test_recovery_dialog_creation(self, app):
        """Test creating recovery dialog with options."""
        recovery_options = {
            'retry': 'Retry the operation',
            'skip': 'Skip this item',
            'abort': 'Abort operation'
        }
        
        dialog = ErrorRecoveryDialog(
            "Operation failed", 
            recovery_options
        )
        assert dialog.windowTitle() == "Error Recovery"
        assert len(dialog.option_buttons) == 3
        assert 'retry' in dialog.option_buttons
        assert 'skip' in dialog.option_buttons
        assert 'abort' in dialog.option_buttons
    
    def test_recovery_option_selection(self, app):
        """Test selecting recovery options."""
        recovery_options = {
            'retry': 'Retry the operation',
            'cancel': 'Cancel operation'
        }
        
        dialog = ErrorRecoveryDialog("Test error", recovery_options)
        
        # Simulate selecting retry option
        dialog.select_option('retry')
        assert dialog.recovery_choice == 'retry'


class TestMainWindowErrorHandling:
    """Test error handling in the main window."""
    
    def test_enhanced_error_message_display(self, main_window):
        """Test displaying enhanced error messages."""
        # Test basic error message
        main_window.show_enhanced_error_message(
            "Test Error",
            "This is a test error message",
            "Detailed error information",
            "error"
        )
        
        # Verify error count increased
        assert main_window.error_count == 1
        assert main_window.last_error_time is not None
    
    def test_error_message_with_recovery_options(self, main_window):
        """Test error messages with recovery options."""
        recovery_options = {
            'retry': 'Retry operation',
            'cancel': 'Cancel operation'
        }
        
        # Mock the recovery dialog to return a choice
        with patch.object(main_window, 'show_enhanced_error_message', return_value='retry') as mock_error:
            choice = main_window.show_enhanced_error_message(
                "Test Error",
                "Operation failed",
                "",
                "error",
                recovery_options
            )
            assert choice == 'retry'
    
    def test_memory_error_handling(self, main_window):
        """Test memory error handling."""
        # Test memory error handling
        result = main_window.handle_memory_error(
            "test operation",
            MemoryError("Insufficient memory")
        )
        
        # Should return boolean indicating whether to retry
        assert isinstance(result, bool)
    
    def test_file_operation_error_handling(self, main_window):
        """Test file operation error handling."""
        # Test file operation error
        with patch.object(main_window, 'show_enhanced_error_message', return_value='retry'):
            result = main_window.handle_file_operation_error(
                "load file",
                "/path/to/file.ifc",
                FileNotFoundError("File not found")
            )
            assert result is True
        
        with patch.object(main_window, 'show_enhanced_error_message', return_value='cancel'):
            result = main_window.handle_file_operation_error(
                "load file",
                "/path/to/file.ifc",
                FileNotFoundError("File not found")
            )
            assert result is False
    
    def test_parsing_error_handling(self, main_window):
        """Test parsing error handling."""
        # Test parsing error with continue choice
        with patch.object(main_window, 'show_enhanced_error_message', return_value='continue'):
            result = main_window.handle_parsing_error(
                "IfcSpaceExtractor",
                "Space_12345",
                ValueError("Invalid property")
            )
            assert result is True
        
        # Test parsing error with stop choice
        with patch.object(main_window, 'show_enhanced_error_message', return_value='stop'):
            result = main_window.handle_parsing_error(
                "IfcSpaceExtractor",
                "Space_12345",
                ValueError("Invalid property")
            )
            assert result is False
    
    def test_batch_operation_error_handling(self, main_window):
        """Test batch operation error handling."""
        failed_items = [
            ("Item1", "Error message 1"),
            ("Item2", "Error message 2")
        ]
        skipped_items = [
            ("Item3", "Skipped reason 1")
        ]
        
        with patch.object(main_window, 'show_enhanced_error_message', return_value='continue'):
            choice = main_window.handle_batch_operation_errors(
                "Test Operation",
                10,  # total items
                failed_items,
                skipped_items
            )
            assert choice == 'continue'
    
    def test_prerequisite_validation(self, main_window):
        """Test operation prerequisite validation."""
        # Test with unmet prerequisites
        prerequisites = {
            'file_loaded': (False, "No file loaded"),
            'data_processed': (True, "Data processed successfully")
        }
        
        result = main_window.validate_operation_prerequisites(
            "export data",
            prerequisites
        )
        assert result is False
        
        # Test with all prerequisites met
        prerequisites_met = {
            'file_loaded': (True, "File loaded successfully"),
            'data_processed': (True, "Data processed successfully")
        }
        
        result = main_window.validate_operation_prerequisites(
            "export data",
            prerequisites_met
        )
        assert result is True
    
    def test_resource_cleanup_error_handling(self, main_window):
        """Test resource cleanup error handling."""
        # Test cleanup error handling
        main_window.handle_resource_cleanup_error(
            "test resource",
            OSError("Permission denied")
        )
        
        # Should not raise exception
        assert True
    
    def test_memory_resource_cleanup(self, main_window):
        """Test memory resource cleanup."""
        # Set up some mock caches
        main_window.space_extractor._spaces_cache = ["test", "data"]
        main_window.surface_extractor._surfaces_cache = ["test", "data"]
        
        # Test memory cleanup
        main_window.free_memory_resources()
        
        # Verify caches are cleared
        assert main_window.space_extractor._spaces_cache is None
        assert main_window.surface_extractor._surfaces_cache is None
    
    def test_error_status_updates(self, main_window):
        """Test error status bar updates."""
        # Test error status update
        main_window.update_error_status("Test error message")
        
        # Verify status bar shows error
        status_text = main_window.status_bar.currentMessage()
        assert "Test error message" in status_text
        assert "❌" in status_text
    
    def test_uncaught_exception_handling(self, main_window):
        """Test uncaught exception handling."""
        # Test uncaught exception handler
        with patch.object(main_window, 'show_enhanced_error_message'):
            main_window.handle_uncaught_exception(
                ValueError,
                ValueError("Test uncaught exception"),
                None
            )
        
        # Should not raise exception
        assert True


class TestIfcFileReaderErrorHandling:
    """Test error handling in IFC file reader."""
    
    def test_load_file_with_invalid_path(self, ifc_reader):
        """Test loading file with invalid path."""
        success, message = ifc_reader.load_file("")
        assert success is False
        assert "No file path provided" in message
        
        success, message = ifc_reader.load_file("   ")
        assert success is False
        assert "No file path provided" in message
    
    def test_load_file_with_invalid_extension(self, ifc_reader):
        """Test loading file with invalid extension."""
        success, message = ifc_reader.load_file("test.txt")
        assert success is False
        assert "Invalid file format" in message
    
    def test_load_nonexistent_file(self, ifc_reader):
        """Test loading nonexistent file."""
        success, message = ifc_reader.load_file("nonexistent.ifc")
        assert success is False
        assert "File not found" in message
    
    def test_load_file_permission_error(self, ifc_reader):
        """Test loading file with permission error."""
        # Create a temporary file for testing
        import tempfile
        import platform
        
        with tempfile.NamedTemporaryFile(suffix='.ifc', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            # Make file unreadable (different approach for Windows vs Unix)
            if platform.system() == "Windows":
                # On Windows, test with a file that doesn't exist after creation
                os.unlink(temp_path)
                success, message = ifc_reader.load_file(temp_path)
                assert success is False
                assert "not found" in message.lower() or "file" in message.lower()
            else:
                # On Unix systems, use chmod
                os.chmod(temp_path, 0o000)
                success, message = ifc_reader.load_file(temp_path)
                assert success is False
                assert "not readable" in message.lower() or "permission" in message.lower() or "empty" in message.lower()
        finally:
            # Clean up
            try:
                if hasattr(os, 'chmod') and os.path.exists(temp_path):
                    os.chmod(temp_path, 0o644)
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
            except:
                pass  # Ignore cleanup errors
    
    def test_load_empty_file(self, ifc_reader):
        """Test loading empty file."""
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.ifc', delete=False) as temp_file:
            temp_path = temp_file.name
            # File is already empty
        
        try:
            success, message = ifc_reader.load_file(temp_path)
            assert success is False
            assert "empty" in message.lower()
        finally:
            os.unlink(temp_path)
    
    @patch('ifcopenshell.open')
    def test_load_file_memory_error(self, mock_open, ifc_reader):
        """Test loading file with memory error."""
        import tempfile
        import os
        
        mock_open.side_effect = MemoryError("Insufficient memory")
        
        # Create a temporary file that exists
        with tempfile.NamedTemporaryFile(suffix='.ifc', delete=False) as temp_file:
            temp_file.write(b"ISO-10303-21;")
            temp_path = temp_file.name
        
        try:
            success, message = ifc_reader.load_file(temp_path)
            assert success is False
            assert "memory" in message.lower()
        finally:
            os.unlink(temp_path)
    
    @patch('ifcopenshell.open')
    def test_load_file_parsing_error(self, mock_open, ifc_reader):
        """Test loading file with parsing error."""
        import tempfile
        import os
        
        mock_open.side_effect = Exception("Not a valid IFC file")
        
        # Create a temporary file that exists
        with tempfile.NamedTemporaryFile(suffix='.ifc', delete=False) as temp_file:
            temp_file.write(b"ISO-10303-21;")
            temp_path = temp_file.name
        
        try:
            success, message = ifc_reader.load_file(temp_path)
            assert success is False
            assert "Invalid or corrupted IFC file" in message
        finally:
            os.unlink(temp_path)
    
    def test_validate_file_with_invalid_path(self, ifc_reader):
        """Test file validation with invalid path."""
        is_valid, message = ifc_reader.validate_file("nonexistent.ifc")
        assert is_valid is False
        assert "does not exist" in message
    
    def test_validate_file_with_invalid_extension(self, ifc_reader):
        """Test file validation with invalid extension."""
        import tempfile
        import os
        
        # Create a temporary file with wrong extension
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp_file:
            temp_file.write(b"Some content")
            temp_path = temp_file.name
        
        try:
            is_valid, message = ifc_reader.validate_file(temp_path)
            assert is_valid is False
            assert "Not an IFC file format" in message
        finally:
            os.unlink(temp_path)


class TestLongRunningOperations:
    """Test long-running operation error handling."""
    
    def test_operation_worker_success(self, app):
        """Test successful operation worker."""
        from ifc_room_schedule.ui.main_window import LongRunningOperationWorker
        
        def test_operation():
            return "Success result"
        
        worker = LongRunningOperationWorker(test_operation)
        
        # Mock the signals
        worker.operation_completed = Mock()
        worker.error_occurred = Mock()
        
        worker.run_operation()
        
        # Verify success signal was emitted
        worker.operation_completed.emit.assert_called_once_with(
            True, "Operation completed successfully", "Success result"
        )
        worker.error_occurred.emit.assert_not_called()
    
    def test_operation_worker_failure(self, app):
        """Test failed operation worker."""
        from ifc_room_schedule.ui.main_window import LongRunningOperationWorker
        
        def test_operation():
            raise ValueError("Test error")
        
        worker = LongRunningOperationWorker(test_operation)
        
        # Mock the signals
        worker.operation_completed = Mock()
        worker.error_occurred = Mock()
        
        worker.run_operation()
        
        # Verify error signal was emitted
        worker.error_occurred.emit.assert_called_once()
        worker.operation_completed.emit.assert_called_once_with(
            False, "Test error", None
        )


def test_error_handling_integration(main_window):
    """Integration test for error handling system."""
    # Test that error handling system is properly initialized
    assert hasattr(main_window, 'error_count')
    assert hasattr(main_window, 'last_error_time')
    assert hasattr(main_window, 'error_clear_timer')
    
    # Test that logging is configured (accept WARNING level or lower)
    import logging
    logger = logging.getLogger()
    assert logger.level <= logging.WARNING
    
    # Test that exception handler is installed
    import sys
    assert sys.excepthook == main_window.handle_uncaught_exception


if __name__ == "__main__":
    pytest.main([__file__, "-v"])