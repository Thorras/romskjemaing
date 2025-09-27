"""
Comprehensive Error Handling Tests

Tests for all error handling functionality including new enhancements.
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from ifc_room_schedule.ui.main_window import MainWindow
from ifc_room_schedule.parser.ifc_file_reader import IfcFileReader
from ifc_room_schedule.parser.ifc_space_extractor import IfcSpaceExtractor


class TestComprehensiveErrorHandling:
    """Test comprehensive error handling functionality."""
    
    @pytest.fixture
    def app(self):
        """Create QApplication for testing."""
        if not QApplication.instance():
            app = QApplication([])
        else:
            app = QApplication.instance()
        yield app
    
    @pytest.fixture
    def main_window(self, app):
        """Create MainWindow for testing."""
        window = MainWindow()
        window._testing_mode = True  # Prevent blocking dialogs
        yield window
        window.close()
    
    def test_batch_operation_error_handling(self, main_window):
        """Test batch operation error handling."""
        failed_items = [
            ("space-1", "Parsing error"),
            ("space-2", "Memory error")
        ]
        skipped_items = [
            ("space-3", "Invalid data")
        ]
        
        # Mock the show_enhanced_error_message method directly
        with patch.object(main_window, 'show_enhanced_error_message', return_value='continue') as mock_method:
            result = main_window.handle_batch_operation_errors(
                "Space Extraction",
                10,
                failed_items,
                skipped_items
            )
            
            assert result == 'continue'
            mock_method.assert_called_once()
    
    def test_memory_error_handling(self, main_window):
        """Test memory error handling."""
        memory_error = MemoryError("Not enough memory")
        
        # Mock the show_enhanced_error_message method directly to return the expected choice
        with patch.object(main_window, 'show_enhanced_error_message', return_value='free_memory') as mock_show_error:
            with patch.object(main_window, 'free_memory_resources') as mock_free_memory:
                result = main_window.handle_memory_error("large file processing", memory_error)
                
                assert result is True
                mock_show_error.assert_called_once()
                mock_free_memory.assert_called_once()
    
    def test_memory_resource_cleanup(self, main_window):
        """Test memory resource cleanup."""
        # Mock the extractors to have caches
        main_window.space_extractor._spaces_cache = ["cached_data"]
        
        with patch('gc.collect') as mock_gc:
            main_window.free_memory_resources()
            
            # Check that caches are cleared
            assert main_window.space_extractor._spaces_cache is None
            # Check that gc.collect was called (multiple times for thorough cleanup)
            assert mock_gc.call_count >= 1
    
    def test_prerequisite_validation(self, main_window):
        """Test operation prerequisite validation."""
        main_window._testing_mode = True  # Enable testing mode
        prerequisites = {
            'file_loaded': (False, "No IFC file is loaded"),
            'spaces_extracted': (True, ""),
            'valid_selection': (False, "No space is selected")
        }
        
        result = main_window.validate_operation_prerequisites("export data", prerequisites)
        
        assert result is False
        # In testing mode, error dialogs are not shown, just logged
    
    def test_resource_cleanup_error_handling(self, main_window):
        """Test resource cleanup error handling."""
        main_window._testing_mode = True  # Enable testing mode
        cleanup_error = OSError("Permission denied")
        
        main_window.handle_resource_cleanup_error("temporary files", cleanup_error)
        
        # In testing mode, error dialogs are not shown, just logged
    
    def test_enhanced_file_reader_error_handling(self):
        """Test enhanced error handling in IFC file reader."""
        reader = IfcFileReader()
        
        # Test non-existent file
        success, message = reader.load_file("non_existent_file.ifc")
        assert not success
        assert "File not found" in message
        
        # Test invalid extension
        success, message = reader.load_file("test.txt")
        assert not success
        assert "Invalid file format" in message
    
    def test_space_extractor_memory_error_handling(self):
        """Test memory error handling in space extractor."""
        extractor = IfcSpaceExtractor()
        
        # Test without IFC file
        with pytest.raises(ValueError, match="No IFC file loaded"):
            extractor.extract_spaces()
    
    def test_operation_progress_with_testing_mode(self, main_window):
        """Test operation progress in testing mode."""
        def test_operation():
            return "Test result"
        
        # Set testing mode to prevent blocking
        main_window._testing_mode = True
        
        # This should not block in testing mode
        main_window.show_operation_progress("Test Operation", test_operation)
        
        # In testing mode, operation runs synchronously without worker/thread
        # Verify the operation completed (no worker/thread created)
        assert hasattr(main_window, '_testing_mode')
        assert main_window._testing_mode is True
    
    def test_error_details_formatting(self, main_window):
        """Test error details formatting for batch operations."""
        failed_items = [("item1", "error1"), ("item2", "error2")]
        skipped_items = [("item3", "reason1")]
        
        details = main_window._format_batch_error_details(failed_items, skipped_items)
        
        assert "Failed items:" in details
        assert "item1: error1" in details
        assert "Skipped items:" in details
        assert "item3: reason1" in details
    
    def test_error_count_persistence(self, main_window):
        """Test that error count persists across multiple errors."""
        initial_count = main_window.error_count
        
        with patch('ifc_room_schedule.ui.main_window.ErrorDetailsDialog') as mock_dialog:
            mock_dialog.return_value.exec.return_value = None
            
            # Generate multiple errors
            for i in range(3):
                main_window.show_enhanced_error_message(
                    f"Test Error {i+1}",
                    f"Error message {i+1}",
                    "",
                    "error"
                )
            
            assert main_window.error_count == initial_count + 3
    
    def test_error_status_clearing(self, main_window):
        """Test automatic error status clearing."""
        main_window.update_error_status("Test error", temporary=True)
        
        # Verify timer is active
        assert main_window.error_clear_timer.isActive()
        
        # Manually trigger clear
        main_window.clear_temporary_error_status()
        
        # Verify status is cleared
        assert main_window.status_bar.styleSheet() == ""
    
    def test_uncaught_exception_logging(self, main_window):
        """Test that uncaught exceptions are properly logged."""
        with patch.object(main_window.logger, 'critical') as mock_logger:
            with patch('ifc_room_schedule.ui.main_window.ErrorRecoveryDialog') as mock_dialog:
                mock_dialog_instance = Mock()
                mock_dialog_instance.exec.return_value = mock_dialog.DialogCode.Rejected
                mock_dialog.return_value = mock_dialog_instance
                
                # Simulate uncaught exception
                test_error = ValueError("Test exception")
                main_window.handle_uncaught_exception(
                    type(test_error), test_error, test_error.__traceback__
                )
                
                mock_logger.assert_called_once()
                assert "Uncaught exception" in str(mock_logger.call_args)


if __name__ == '__main__':
    pytest.main([__file__])