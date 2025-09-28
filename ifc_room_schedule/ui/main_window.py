"""
Main Window for IFC Room Schedule Application

Main window with file dialog functionality for IFC file loading.
"""

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QPushButton, QFileDialog, QMessageBox, 
                            QMenuBar, QStatusBar, QProgressBar, QSplitter,
                            QTabWidget, QToolBar, QTextEdit, QDialog, QDialogButtonBox)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QObject, QTimer
from PyQt6.QtGui import QAction, QIcon, QTextCursor
import os
import logging
import traceback
import sys
import time
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum

from ..parser.ifc_file_reader import IfcFileReader
from ..parser.ifc_space_extractor import IfcSpaceExtractor
from ..parser.ifc_surface_extractor import IfcSurfaceExtractor
from ..parser.ifc_space_boundary_parser import IfcSpaceBoundaryParser
from ..parser.ifc_relationship_parser import IfcRelationshipParser
from ..utils.enhanced_logging import (
    enhanced_logger, ErrorCategory, ErrorSeverity, MemoryErrorAnalyzer
)
from .space_list_widget import SpaceListWidget
from .space_detail_widget import SpaceDetailWidget
from .surface_editor_widget import SurfaceEditorWidget
from .export_dialog_widget import ExportDialogWidget


class FileSizeCategory(Enum):
    """File size categories for smart loading strategy."""
    SMALL = "small"      # < 10MB - Direct loading
    MEDIUM = "medium"    # 10-50MB - Threaded with progress
    LARGE = "large"      # 50-100MB - Threaded with warning
    HUGE = "huge"        # > 100MB - Require confirmation


class ErrorDetailsDialog(QDialog):
    """Enhanced error dialog with detailed error information and recovery options."""
    
    def __init__(self, title: str, message: str, details: str = "", 
                 error_type: str = "error", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.resize(600, 400)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Error icon and main message
        header_layout = QHBoxLayout()
        
        # Icon based on error type
        icon_label = QLabel()
        if error_type == "warning":
            icon_label.setText("⚠️")
        elif error_type == "info":
            icon_label.setText("ℹ️")
        else:
            icon_label.setText("❌")
        icon_label.setStyleSheet("font-size: 24px; margin-right: 10px;")
        header_layout.addWidget(icon_label)
        
        # Main message
        message_label = QLabel(message)
        message_label.setWordWrap(True)
        message_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        header_layout.addWidget(message_label, 1)
        
        layout.addLayout(header_layout)
        
        # Details section (collapsible)
        if details:
            details_label = QLabel("Error Details:")
            details_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
            layout.addWidget(details_label)
            
            details_text = QTextEdit()
            details_text.setPlainText(details)
            details_text.setReadOnly(True)
            details_text.setMaximumHeight(200)
            details_text.setStyleSheet("""
                QTextEdit {
                    background-color: #f8f9fa;
                    border: 1px solid #dee2e6;
                    border-radius: 4px;
                    font-family: monospace;
                    font-size: 11px;
                }
            """)
            layout.addWidget(details_text)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)


class ErrorRecoveryDialog(QDialog):
    """Dialog for error recovery options."""
    
    def __init__(self, error_message: str, recovery_options: Dict[str, str], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Error Recovery")
        self.setModal(True)
        self.resize(500, 300)
        self.recovery_choice = None
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Error message
        error_label = QLabel(f"❌ {error_message}")
        error_label.setWordWrap(True)
        error_label.setStyleSheet("font-size: 14px; font-weight: bold; margin-bottom: 15px;")
        layout.addWidget(error_label)
        
        # Recovery options
        options_label = QLabel("Choose a recovery option:")
        options_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(options_label)
        
        # Create buttons for each recovery option
        self.option_buttons = {}
        for option_key, option_text in recovery_options.items():
            button = QPushButton(option_text)
            button.clicked.connect(lambda checked, key=option_key: self.select_option(key))
            button.setStyleSheet("""
                QPushButton {
                    text-align: left;
                    padding: 10px;
                    margin: 2px;
                    border: 1px solid #ced4da;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #e9ecef;
                }
            """)
            layout.addWidget(button)
            self.option_buttons[option_key] = button
        
        # Cancel button
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                padding: 8px 16px;
                margin-top: 10px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        layout.addWidget(cancel_button)
    
    def select_option(self, option_key: str):
        """Select a recovery option and close dialog."""
        self.recovery_choice = option_key
        self.accept()


class LongRunningOperationWorker(QObject):
    """Worker for long-running operations with progress reporting and cancellation support."""
    
    progress_updated = pyqtSignal(int, str)  # progress, status
    operation_completed = pyqtSignal(bool, str, object)  # success, message, result
    error_occurred = pyqtSignal(str, str)  # error_type, error_message
    operation_cancelled = pyqtSignal(str)  # cancellation_message
    
    def __init__(self, operation_func, *args, **kwargs):
        super().__init__()
        self.operation_func = operation_func
        self.args = args
        self.kwargs = kwargs
        self._is_cancelled = False
        self._cancel_requested = False
    
    def request_cancellation(self):
        """Request cancellation of the current operation."""
        self._cancel_requested = True
        self._is_cancelled = True
    
    def is_cancelled(self):
        """Check if the operation has been cancelled."""
        return self._is_cancelled
    
    def run_operation(self):
        """Execute the long-running operation with cancellation support and enhanced error reporting."""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            logger.debug(f"Worker thread starting operation: {self.operation_func.__name__}")
            
            # Check for cancellation before starting
            if self._cancel_requested:
                logger.info("Operation cancelled before starting")
                self.operation_cancelled.emit("Operation cancelled before starting")
                return
            
            # Execute the operation with threading context logging
            logger.info(f"Executing operation in worker thread: {self.operation_func.__name__}")
            result = self.operation_func(*self.args, **self.kwargs)
            
            # Check for cancellation after completion
            if self._cancel_requested:
                logger.info("Operation cancelled after completion")
                self.operation_cancelled.emit("Operation cancelled after completion")
                return
            
            logger.info(f"Operation completed successfully in worker thread: {self.operation_func.__name__}")
            self.operation_completed.emit(True, "Operation completed successfully", result)
            
        except Exception as e:
            # Enhanced error classification and logging
            error_type = self._classify_error(e)
            logger.error(f"Operation failed in worker thread ({error_type}): {str(e)}")
            
            # Check if this is a cancellation-related exception
            if self._cancel_requested:
                logger.info(f"Operation cancelled due to error: {str(e)}")
                self.operation_cancelled.emit(f"Operation cancelled due to error: {str(e)}")
                return
            
            error_details = traceback.format_exc()
            logger.debug(f"Full error traceback: {error_details}")
            
            # Emit error with classification
            self.error_occurred.emit(error_type, f"Operation failed: {str(e)}")
            self.operation_completed.emit(False, str(e), None)
    
    def _classify_error(self, error: Exception) -> str:
        """
        Classify the type of error for better handling.
        
        Args:
            error: The exception that occurred
            
        Returns:
            String classification of the error type
        """
        error_str = str(error).lower()
        error_type_name = type(error).__name__.lower()
        
        # Threading-related errors
        if any(keyword in error_str or keyword in error_type_name for keyword in 
               ['thread', 'worker', 'signal', 'slot', 'qthread', 'concurrent']):
            return "thread_error"
        
        # Memory-related errors
        if isinstance(error, MemoryError) or 'memory' in error_str:
            return "memory_error"
        
        # Timeout-related errors (check before I/O errors)
        if 'timeout' in error_str or isinstance(error, TimeoutError):
            return "timeout_error"
        
        # I/O related errors
        if isinstance(error, (IOError, OSError)) or any(keyword in error_str for keyword in 
                                                       ['file', 'io', 'read', 'write', 'access']):
            return "io_error"
        
        # Default classification
        return "operation_error"


class MainWindow(QMainWindow):
    """Main application window with IFC file loading functionality."""
    
    # Signals
    ifc_file_loaded = pyqtSignal(str)  # Emitted when IFC file is successfully loaded
    
    def __init__(self):
        super().__init__()
        self.logger = enhanced_logger.logger  # Use enhanced logger
        self.ifc_reader = IfcFileReader()
        self.space_extractor = IfcSpaceExtractor()
        self.surface_extractor = IfcSurfaceExtractor()
        self.boundary_parser = IfcSpaceBoundaryParser()
        self.relationship_parser = IfcRelationshipParser()
        self.current_file_path = None
        self.spaces = []
        
        # Enhanced error handling state with detailed tracking
        self.error_count = 0
        self.last_error_time = None
        self.operation_thread = None
        self.operation_worker = None
        self.current_operation_id = None  # Track current operation for timing
        
        # Fallback tracking for logging and diagnostics
        self.fallback_stats = {
            'threading_failures': 0,
            'fallback_attempts': 0,
            'fallback_successes': 0,
            'fallback_failures': 0,
            'last_fallback_time': None,
            'fallback_reasons': []
        }
        
        # Resource monitoring and cleanup verification
        self.resource_monitor = {
            'active_threads': set(),
            'active_workers': set(),
            'active_timers': set(),
            'memory_snapshots': [],
            'cleanup_history': [],
            'resource_leaks_detected': 0,
            'last_cleanup_verification': None
        }
        
        # Setup error handling
        self.setup_error_handling()
        
        self.setup_ui()
        self.setup_menu()
        self.setup_toolbar()
        self.setup_status_bar()
        self.connect_signals()
        
        # Setup resource monitoring timer
        self.setup_resource_monitoring()
        
        # Ensure initial state is correct
        self.update_file_info()
    
    def categorize_file_size(self, file_path: str) -> tuple[FileSizeCategory, int, str]:
        """
        Categorize file size for smart loading strategy.
        
        Args:
            file_path: Path to the IFC file
            
        Returns:
            Tuple of (category, size_bytes, size_string)
        """
        try:
            size_bytes = os.path.getsize(file_path)
            size_mb = size_bytes / (1024 * 1024)
            
            # Create human-readable size string
            if size_bytes < 1024:
                size_string = f"{size_bytes} B"
            elif size_bytes < 1024 * 1024:
                size_string = f"{size_bytes / 1024:.1f} KB"
            else:
                size_string = f"{size_mb:.1f} MB"
            
            # Categorize based on size
            if size_bytes < 10 * 1024 * 1024:  # < 10MB
                category = FileSizeCategory.SMALL
            elif size_bytes < 50 * 1024 * 1024:  # 10-50MB
                category = FileSizeCategory.MEDIUM
            elif size_bytes < 100 * 1024 * 1024:  # 50-100MB
                category = FileSizeCategory.LARGE
            else:  # > 100MB
                category = FileSizeCategory.HUGE
            
            self.logger.info(f"File categorized as {category.value}: {size_string}")
            return category, size_bytes, size_string
            
        except OSError as e:
            self.logger.error(f"Error getting file size: {e}")
            # Default to medium category if we can't determine size
            return FileSizeCategory.MEDIUM, 0, "Unknown size"
    
    def setup_error_handling(self):
        """Set up comprehensive error handling system."""
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('ifc_room_schedule.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        # Install global exception handler
        sys.excepthook = self.handle_uncaught_exception
        
        # Create error status timer for clearing temporary error messages
        self.error_clear_timer = QTimer()
        self.error_clear_timer.setSingleShot(True)
        self.error_clear_timer.timeout.connect(self.clear_temporary_error_status)
    
    def handle_uncaught_exception(self, exc_type, exc_value, exc_traceback):
        """Handle uncaught exceptions with user-friendly error dialog."""
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        error_msg = f"An unexpected error occurred: {exc_value}"
        error_details = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        
        self.logger.critical(f"Uncaught exception: {error_msg}", exc_info=(exc_type, exc_value, exc_traceback))
        
        # Show error dialog with recovery options
        recovery_options = {
            'continue': 'Continue working (may cause instability)',
            'restart': 'Restart application',
            'exit': 'Exit application'
        }
        
        recovery_dialog = ErrorRecoveryDialog(
            error_msg, recovery_options, self
        )
        
        if recovery_dialog.exec() == QDialog.DialogCode.Accepted:
            choice = recovery_dialog.recovery_choice
            if choice == 'restart':
                self.restart_application()
            elif choice == 'exit':
                self.close()
            # 'continue' does nothing, just continues execution
    
    def show_enhanced_error_message(self, title: str, message: str, 
                                  details: str = "", error_type: str = "error",
                                  recovery_options: Optional[Dict[str, str]] = None) -> Optional[str]:
        """
        Show enhanced error message with details and optional recovery options.
        Uses the enhanced logging system for structured error reporting.
        
        Args:
            title: Error dialog title
            message: Main error message
            details: Detailed error information
            error_type: Type of error ('error', 'warning', 'info')
            recovery_options: Dict of recovery option keys and descriptions
            
        Returns:
            Selected recovery option key if recovery options provided, None otherwise
        """
        self.error_count += 1
        self.last_error_time = datetime.now()
        
        # Map error types to enhanced logging categories and severities
        if error_type == "error":
            category = ErrorCategory.UNKNOWN
            severity = ErrorSeverity.HIGH
        elif error_type == "warning":
            category = ErrorCategory.UNKNOWN
            severity = ErrorSeverity.MEDIUM
        else:
            category = ErrorCategory.UNKNOWN
            severity = ErrorSeverity.LOW
        
        # Create structured error report
        error_report = enhanced_logger.create_error_report(
            category=category,
            severity=severity,
            title=title,
            message=message,
            user_guidance=message,
            recovery_suggestions=list(recovery_options.values()) if recovery_options else []
        )
        
        # Update status bar with error count and enhanced context
        self.update_error_status(f"Error #{self.error_count}: {message}")
        
        # In testing mode, don't show dialogs to avoid blocking tests
        if hasattr(self, '_testing_mode') and self._testing_mode:
            # Return first recovery option if available, otherwise None
            if recovery_options:
                return list(recovery_options.keys())[0]
            return None
        
        # Show recovery dialog if options provided
        if recovery_options:
            recovery_dialog = ErrorRecoveryDialog(message, recovery_options, self)
            if recovery_dialog.exec() == QDialog.DialogCode.Accepted:
                return recovery_dialog.recovery_choice
            return None
        
        # Show detailed error dialog
        error_dialog = ErrorDetailsDialog(title, message, details, error_type, self)
        error_dialog.exec()
        return None
    
    def update_error_status(self, message: str, temporary: bool = True):
        """Update status bar with error message."""
        self.status_bar.showMessage(f"❌ {message}")
        self.status_bar.setStyleSheet("QStatusBar { color: #dc3545; }")
        
        if temporary:
            # Clear error status after 10 seconds
            self.error_clear_timer.start(10000)
    
    def clear_temporary_error_status(self):
        """Clear temporary error status and restore normal status."""
        self.status_bar.setStyleSheet("")  # Reset to default style
        if self.ifc_reader.is_loaded():
            self.status_bar.showMessage("Ready")
        else:
            self.status_bar.showMessage("Ready to load IFC file...")
    
    def show_operation_progress(self, title: str, operation_func, *args, **kwargs):
        """
        Execute long-running operation in separate thread with non-blocking progress indication.
        
        Args:
            title: Progress operation title
            operation_func: Function to execute
            *args, **kwargs: Arguments for the operation function
        """
        # In test mode, execute synchronously to avoid threading issues
        if hasattr(self, '_testing_mode') and self._testing_mode:
            try:
                result = operation_func(*args, **kwargs)
                self.on_operation_completed(True, "Operation completed successfully", result)
                return
            except Exception as e:
                self.on_operation_error("operation_error", f"Operation failed: {str(e)}")
                return
        
        # Show non-blocking progress indication using status bar
        self.show_non_blocking_progress(title, operation_func, *args, **kwargs)
    
    def show_non_blocking_progress(self, title: str, operation_func, *args, **kwargs):
        """
        Show non-blocking progress indication using QProgressBar in status bar.
        Enhanced with detailed operation timing and logging.
        
        Args:
            title: Progress operation title
            operation_func: Function to execute
            *args, **kwargs: Arguments for the operation function
        """
        # Start enhanced operation timing
        self.current_operation_id = enhanced_logger.start_operation_timing(
            f"ui_operation_{title.lower().replace(' ', '_')}", 
            self.current_file_path
        )
        
        # Update status bar with operation title and enhanced context
        file_context = ""
        if self.current_file_path:
            try:
                file_size = os.path.getsize(self.current_file_path)
                size_mb = file_size / (1024 * 1024)
                file_context = f" ({size_mb:.1f}MB)"
            except OSError:
                pass
        
        self.status_bar.showMessage(f"{title}{file_context}...")
        enhanced_logger.logger.info(f"Starting UI operation: {title}{file_context}")
        
        # Show progress bar in main UI (not status bar to avoid conflicts)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        
        # Show cancel button during operation
        if hasattr(self, 'cancel_button'):
            self.cancel_button.setVisible(True)
            self.cancel_button.setEnabled(True)
        
        # Create worker thread with error handling
        try:
            self.operation_thread = QThread()
            self.operation_worker = LongRunningOperationWorker(operation_func, *args, **kwargs)
            self.operation_worker.moveToThread(self.operation_thread)
            
            # Register thread and worker for monitoring
            self.register_thread(self.operation_thread, operation_name)
            self.register_worker(self.operation_worker, operation_name)
            
            # Connect signals for non-blocking progress updates
            self.operation_worker.progress_updated.connect(self.update_progress_status)
            self.operation_worker.operation_completed.connect(self.on_operation_completed)
            self.operation_worker.error_occurred.connect(self.on_operation_error)
            self.operation_worker.operation_cancelled.connect(self.on_operation_cancelled)
            
            self.operation_thread.started.connect(self.operation_worker.run_operation)
            self.operation_thread.finished.connect(self.operation_thread.deleteLater)
            
            # Add error handling for thread creation and startup
            self.operation_thread.finished.connect(self._on_thread_finished)
            
            # Set timeout timer for long operations with file-based timeout if available
            timeout_file = getattr(self, 'current_file_path', None)
            self.setup_operation_timeout(file_path=timeout_file)
            
            # Start operation (non-blocking) with error handling
            try:
                self.operation_thread.start()
                self.logger.info(f"Threading operation '{title}' started successfully")
            except Exception as thread_start_error:
                self.logger.error(f"Failed to start thread for operation '{title}': {thread_start_error}")
                self._handle_thread_startup_failure(title, operation_func, thread_start_error, *args, **kwargs)
                
        except Exception as thread_creation_error:
            self.logger.error(f"Failed to create thread for operation '{title}': {thread_creation_error}")
            self._handle_thread_creation_failure(title, operation_func, thread_creation_error, *args, **kwargs)
    
    def update_progress_status(self, progress: int, status: str):
        """
        Update progress indication without blocking the main thread.
        
        Args:
            progress: Progress percentage (0-100)
            status: Status message
        """
        # Update status bar message
        self.status_bar.showMessage(f"{status}...")
        
        # Update progress bar if we have specific progress
        if progress >= 0:
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(progress)
        else:
            # Keep indeterminate progress
            self.progress_bar.setRange(0, 0)
    
    def get_timeout_for_file_size(self, file_size_bytes: int) -> int:
        """
        Get appropriate timeout value based on file size.
        
        Args:
            file_size_bytes: File size in bytes
            
        Returns:
            Timeout in seconds
        """
        size_mb = file_size_bytes / (1024 * 1024)
        
        if size_mb < 10:  # Small files
            return 30  # 30 seconds
        elif size_mb < 50:  # Medium files
            return 60  # 1 minute
        elif size_mb < 100:  # Large files
            return 120  # 2 minutes
        else:  # Huge files
            return 300  # 5 minutes
    
    def setup_operation_timeout(self, timeout_seconds: int = None, file_path: str = None):
        """
        Set up timeout handling for long operations with configurable timeout based on file size.
        
        Args:
            timeout_seconds: Explicit timeout in seconds (optional)
            file_path: Path to file for size-based timeout calculation (optional)
        """
        if hasattr(self, 'operation_timeout_timer') and self.operation_timeout_timer:
            self.operation_timeout_timer.stop()
        
        # Determine timeout value
        if timeout_seconds is None:
            if file_path and os.path.exists(file_path):
                try:
                    file_size = os.path.getsize(file_path)
                    timeout_seconds = self.get_timeout_for_file_size(file_size)
                    self.logger.info(f"Using file size-based timeout: {timeout_seconds}s for {file_size/(1024*1024):.1f}MB file")
                except OSError:
                    timeout_seconds = 60  # Default fallback
            else:
                timeout_seconds = 60  # Default timeout
        
        self.current_timeout_seconds = timeout_seconds
        self.operation_start_time = datetime.now()
        
        self.operation_timeout_timer = QTimer()
        self.operation_timeout_timer.setSingleShot(True)
        self.operation_timeout_timer.timeout.connect(self.handle_operation_timeout)
        self.operation_timeout_timer.start(timeout_seconds * 1000)  # Convert to milliseconds
        
        self.logger.info(f"Operation timeout set to {timeout_seconds} seconds")
    
    def handle_operation_timeout(self):
        """Handle operation timeout with user recovery options."""
        if self.operation_thread and self.operation_thread.isRunning():
            # Calculate elapsed time
            elapsed_time = (datetime.now() - self.operation_start_time).total_seconds()
            elapsed_minutes = int(elapsed_time // 60)
            elapsed_seconds = int(elapsed_time % 60)
            
            # Determine appropriate extension time based on current timeout
            if self.current_timeout_seconds <= 60:
                extension_time = 60  # 1 minute extension for short timeouts
            elif self.current_timeout_seconds <= 120:
                extension_time = 120  # 2 minute extension for medium timeouts
            else:
                extension_time = 180  # 3 minute extension for long timeouts
            
            recovery_options = {
                'wait_longer': f'Wait {extension_time//60} more minute(s)',
                'cancel': 'Cancel operation',
                'force_direct': 'Try direct loading (may freeze)'
            }
            
            # Add file size context if available
            file_context = ""
            if hasattr(self, 'current_file_path') and self.current_file_path:
                try:
                    file_size = os.path.getsize(self.current_file_path)
                    size_mb = file_size / (1024 * 1024)
                    file_context = f"\nFile size: {size_mb:.1f}MB"
                except OSError:
                    pass
            
            choice = self.show_enhanced_error_message(
                "Operation Timeout",
                f"The operation has been running for {elapsed_minutes}m {elapsed_seconds}s and exceeded the timeout limit.",
                f"Expected timeout: {self.current_timeout_seconds}s{file_context}\n\n"
                f"This may indicate:\n"
                f"- Large or complex file requiring more processing time\n"
                f"- System performance issues or high memory usage\n"
                f"- File corruption or parsing difficulties\n\n"
                f"Recovery options:\n"
                f"- Wait longer: Continue the operation with extended timeout\n"
                f"- Cancel: Stop the operation and return to ready state\n"
                f"- Force direct: Attempt synchronous loading (may cause UI freezing)",
                "warning",
                recovery_options
            )
            
            if choice == 'wait_longer':
                # Extend timeout with appropriate duration
                self.setup_operation_timeout(extension_time)
                self.status_bar.showMessage(f"Extending timeout by {extension_time//60} minute(s)...")
                self.logger.info(f"Operation timeout extended by {extension_time}s (total elapsed: {elapsed_time:.1f}s)")
            elif choice == 'cancel':
                self.logger.info(f"Operation cancelled by user after {elapsed_time:.1f}s")
                self.cancel_operation()
            elif choice == 'force_direct':
                self.logger.warning(f"Forcing direct loading after timeout ({elapsed_time:.1f}s)")
                self.cancel_operation()
                if hasattr(self, 'current_file_path') and self.current_file_path:
                    self.load_file_directly(self.current_file_path)
    
    def on_operation_completed(self, success: bool, message: str, result: Any):
        """Handle completion of long-running operation with enhanced logging."""
        # Complete operation timing if active
        if self.current_operation_id:
            operation_timing = enhanced_logger.finish_operation_timing(self.current_operation_id)
            if operation_timing:
                enhanced_logger.logger.info(f"UI operation completed: {operation_timing.operation_name} "
                                          f"in {operation_timing.duration_seconds:.2f}s")
            self.current_operation_id = None
        
        # Clean up thread and worker
        if self.operation_thread:
            self.operation_thread.quit()
            self.operation_thread.wait()
            self.operation_thread = None
        self.operation_worker = None
        
        # Clean up timeout timer
        if hasattr(self, 'operation_timeout_timer'):
            self.operation_timeout_timer.stop()
        
        # Hide progress bar and cancel button
        self.progress_bar.setVisible(False)
        if hasattr(self, 'cancel_button'):
            self.cancel_button.setVisible(False)
        
        if success:
            self.status_bar.showMessage(f"✅ {message}")
            self.status_bar.setStyleSheet("QStatusBar { color: #28a745; }")
            QTimer.singleShot(5000, self.clear_temporary_error_status)
            
            # Finalize space extraction if this was a space extraction operation
            if hasattr(self, 'spaces') and self.spaces:
                self.finalize_space_extraction()
        else:
            self.show_enhanced_error_message("Operation Failed", message)
    
    def on_operation_error(self, error_type: str, error_message: str):
        """Handle error during long-running operation with enhanced logging and fallback to direct loading."""
        # Complete operation timing with error status
        if self.current_operation_id:
            operation_timing = enhanced_logger.finish_operation_timing(self.current_operation_id)
            if operation_timing:
                enhanced_logger.logger.error(f"UI operation failed: {operation_timing.operation_name} "
                                           f"after {operation_timing.duration_seconds:.2f}s - {error_message}")
            self.current_operation_id = None
        
        # Clean up timeout timer
        if hasattr(self, 'operation_timeout_timer') and self.operation_timeout_timer:
            self.operation_timeout_timer.stop()
        
        # Hide progress bar and cancel button
        self.progress_bar.setVisible(False)
        if hasattr(self, 'cancel_button'):
            self.cancel_button.setVisible(False)
        
        # Create structured error report for operation failure
        category = self._map_error_type_to_category(error_type)
        severity = self._determine_error_severity(error_type, error_message)
        
        error_report = enhanced_logger.create_error_report(
            category=category,
            severity=severity,
            title="Operation Error",
            message=f"Operation failed: {error_message}",
            user_guidance=self._get_error_guidance(error_type, error_message),
            recovery_suggestions=self._get_recovery_suggestions(error_type, error_message)
        )
        
        # Check if this is a threading-related error and offer fallback
        if self._is_threading_error(error_type, error_message):
            enhanced_logger.logger.warning(f"Threading error detected, attempting fallback: {error_message}")
            self._handle_threading_error_with_fallback(error_message)
        else:
            # Enhanced error message with detailed guidance
            recovery_options = self._get_recovery_options(error_type, error_message)
            self.show_enhanced_error_message(
                "Operation Error", 
                error_message,
                f"Error type: {error_type}\n\nGuidance: {self._get_error_guidance(error_type, error_message)}",
                "error",
                recovery_options
            )
    
    def _map_error_type_to_category(self, error_type: str) -> ErrorCategory:
        """Map error type string to ErrorCategory enum."""
        error_type_lower = error_type.lower()
        if 'memory' in error_type_lower:
            return ErrorCategory.MEMORY
        elif 'thread' in error_type_lower or 'worker' in error_type_lower:
            return ErrorCategory.THREADING
        elif 'timeout' in error_type_lower:
            return ErrorCategory.TIMEOUT
        elif 'io' in error_type_lower or 'file' in error_type_lower:
            return ErrorCategory.IO
        elif 'parsing' in error_type_lower or 'validation' in error_type_lower:
            return ErrorCategory.PARSING
        else:
            return ErrorCategory.UNKNOWN
    
    def _determine_error_severity(self, error_type: str, error_message: str) -> ErrorSeverity:
        """Determine error severity based on type and message."""
        error_text = f"{error_type} {error_message}".lower()
        
        if any(keyword in error_text for keyword in ['critical', 'fatal', 'crash', 'corrupt']):
            return ErrorSeverity.CRITICAL
        elif any(keyword in error_text for keyword in ['memory', 'timeout', 'thread', 'fail']):
            return ErrorSeverity.HIGH
        elif any(keyword in error_text for keyword in ['warning', 'slow', 'performance']):
            return ErrorSeverity.MEDIUM
        else:
            return ErrorSeverity.LOW
    
    def _get_error_guidance(self, error_type: str, error_message: str) -> str:
        """Get user-friendly guidance based on error type and message."""
        error_type_lower = error_type.lower()
        error_message_lower = error_message.lower()
        
        if 'memory' in error_type_lower:
            return "The operation ran out of memory. Try closing other applications or processing a smaller file."
        elif 'thread' in error_type_lower:
            return "A threading error occurred. The operation will be retried using direct processing."
        elif 'timeout' in error_type_lower:
            return "The operation took too long to complete. You can try waiting longer or cancel the operation."
        elif 'io' in error_type_lower:
            return "A file access error occurred. Check that the file is accessible and not locked by another application."
        else:
            return "An unexpected error occurred during the operation."
    
    def _get_recovery_suggestions(self, error_type: str, error_message: str) -> List[str]:
        """Get recovery suggestions based on error type and message."""
        error_type_lower = error_type.lower()
        
        if 'memory' in error_type_lower:
            return [
                "Close other applications to free up memory",
                "Restart the application",
                "Try processing a smaller file",
                "Upgrade system memory if processing large files regularly"
            ]
        elif 'thread' in error_type_lower:
            return [
                "The operation will be retried automatically",
                "If the issue persists, restart the application",
                "Try processing the file again"
            ]
        elif 'timeout' in error_type_lower:
            return [
                "Wait longer for the operation to complete",
                "Cancel and try with a smaller file",
                "Check system performance and close other applications"
            ]
        else:
            return [
                "Try the operation again",
                "Restart the application if the issue persists",
                "Check the file and system status"
            ]
    
    def _get_recovery_options(self, error_type: str, error_message: str) -> Optional[Dict[str, str]]:
        """Get recovery options for user selection based on error type."""
        error_type_lower = error_type.lower()
        
        if 'thread' in error_type_lower:
            return {
                'retry_direct': 'Retry with direct processing',
                'cancel': 'Cancel operation'
            }
        elif 'timeout' in error_type_lower:
            return {
                'wait_longer': 'Wait longer',
                'cancel': 'Cancel operation',
                'retry': 'Retry operation'
            }
        else:
            return {
                'retry': 'Try again',
                'cancel': 'Cancel'
            }

    def on_operation_cancelled(self, cancellation_message: str):
        """Handle cancellation of long-running operation."""
        self.logger.info(f"Operation cancelled: {cancellation_message}")
        
        # Clean up timeout timer
        if hasattr(self, 'operation_timeout_timer') and self.operation_timeout_timer:
            self.operation_timeout_timer.stop()
        
        # Hide progress bar and cancel button
        self.progress_bar.setVisible(False)
        if hasattr(self, 'cancel_button'):
            self.cancel_button.setVisible(False)
        
        # Update UI state
        self.update_ui_state(False)  # Disable file-related actions
        
        # Update status bar with cancellation message
        self.status_bar.showMessage(f"✋ {cancellation_message}")
        self.status_bar.setStyleSheet("QStatusBar { color: #fd7e14; }")  # Orange color for cancellation
        
        # Clear status after 5 seconds
        QTimer.singleShot(5000, self.clear_temporary_error_status)
    
    def cancel_operation(self):
        """Cancel the current long-running operation with comprehensive cleanup."""
        self.logger.info("Cancelling current operation...")
        
        # Calculate elapsed time if available
        elapsed_time = 0
        if hasattr(self, 'operation_start_time') and self.operation_start_time:
            if isinstance(self.operation_start_time, datetime):
                elapsed_time = (datetime.now() - self.operation_start_time).total_seconds()
            else:
                # Handle case where operation_start_time might be a timestamp
                elapsed_time = time.time() - float(self.operation_start_time)
        
        # Use the comprehensive cleanup method
        self._cleanup_thread_worker_pair(self.operation_thread, self.operation_worker, "cancelled operation")
        
        # Clear references
        self.operation_thread = None
        self.operation_worker = None
        
        # Clean up timeout timer
        if hasattr(self, 'operation_timeout_timer') and self.operation_timeout_timer:
            self.operation_timeout_timer.stop()
            self.operation_timeout_timer.deleteLater()
            self.operation_timeout_timer = None
        
        # Perform memory cleanup for cancelled operation
        self._cleanup_cancelled_operation_memory()
        
        # Reset operation state
        self._reset_operation_state()
        
        # Hide progress bar and cancel button, update UI
        self.progress_bar.setVisible(False)
        if hasattr(self, 'cancel_button'):
            self.cancel_button.setVisible(False)
        self.update_ui_state(False)  # Disable file-related actions
        
        # Update status
        if elapsed_time > 0:
            self.status_bar.showMessage(f"Operation cancelled after {elapsed_time:.1f}s")
        else:
            self.status_bar.showMessage("Operation cancelled")
        
        self.logger.info("Operation cancellation completed")
    
    def _cleanup_cancelled_operation_memory(self):
        """Clean up memory specifically for cancelled operations."""
        try:
            self.logger.debug("Cleaning up memory for cancelled operation...")
            
            # Clear any partially loaded data
            if hasattr(self, '_partial_spaces_data'):
                self._partial_spaces_data = None
            if hasattr(self, '_partial_surfaces_data'):
                self._partial_surfaces_data = None
            if hasattr(self, '_processing_cache'):
                self._processing_cache = None
            
            # Clear extractor state that might be in progress
            extractors = [self.space_extractor, self.surface_extractor, 
                         self.boundary_parser, self.relationship_parser]
            
            for extractor in extractors:
                if extractor and hasattr(extractor, '_processing_state'):
                    extractor._processing_state = None
                if extractor and hasattr(extractor, '_current_file'):
                    extractor._current_file = None
            
            # Force garbage collection for cancelled operation cleanup
            import gc
            collected = gc.collect()
            self.logger.debug(f"Cancelled operation cleanup: collected {collected} objects")
            
        except Exception as e:
            self.logger.warning(f"Error during cancelled operation memory cleanup: {e}")
    
    def _is_threading_error(self, error_type: str, error_message: str) -> bool:
        """
        Determine if an error is related to threading operations.
        
        Args:
            error_type: Type of error that occurred
            error_message: Error message text
            
        Returns:
            True if this appears to be a threading-related error
        """
        threading_indicators = [
            'thread',
            'worker',
            'qthread',
            'movetothread',
            'signal',
            'slot',
            'connection',
            'threading',
            'concurrent',
            'async',
            'timeout',
            'deadlock',
            'race condition'
        ]
        
        error_text = f"{error_type} {error_message}".lower()
        
        # Check for threading-related keywords
        for indicator in threading_indicators:
            if indicator in error_text:
                self.logger.info(f"Threading error detected: '{indicator}' found in error message")
                return True
        
        # Check for specific error types that commonly occur in threading
        if error_type in ['operation_error', 'worker_error', 'thread_error']:
            self.logger.info(f"Threading error detected: error type '{error_type}' indicates threading issue")
            return True
        
        return False
    
    def _handle_threading_error_with_fallback(self, error_message: str):
        """
        Handle threading errors with fallback to direct loading.
        
        Args:
            error_message: The original error message from the threading operation
        """
        # Update fallback statistics
        self.fallback_stats['threading_failures'] += 1
        self.fallback_stats['fallback_reasons'].append(f"Threading error: {error_message}")
        
        self.logger.warning(f"Threading operation failed (failure #{self.fallback_stats['threading_failures']}): {error_message}")
        
        # Check if we have a current file to fall back to
        if not hasattr(self, 'current_file_path') or not self.current_file_path:
            self.logger.error("No current file path available for fallback")
            self.show_enhanced_error_message(
                "Threading Error", 
                f"Threading operation failed and no fallback available: {error_message}"
            )
            return
        
        # Log the fallback attempt
        self.logger.info(f"Attempting fallback to direct loading for file: {self.current_file_path}")
        
        # Offer recovery options to the user
        recovery_options = {
            'fallback_direct': 'Try direct loading (may freeze UI temporarily)',
            'retry_threading': 'Retry with threading',
            'select_different': 'Select a different file',
            'cancel': 'Cancel operation'
        }
        
        choice = self.show_enhanced_error_message(
            "Threading Operation Failed",
            f"The threaded operation failed: {error_message}",
            f"File: {os.path.basename(self.current_file_path)}\n\n"
            f"Threading errors can occur due to:\n"
            f"- System resource constraints\n"
            f"- Qt threading limitations\n"
            f"- Memory pressure\n"
            f"- File complexity\n\n"
            f"Fallback options:\n"
            f"- Direct loading: Load the file synchronously (may cause temporary UI freezing)\n"
            f"- Retry threading: Attempt the threaded operation again\n"
            f"- Select different: Choose a different file to load\n"
            f"- Cancel: Return to ready state",
            "warning",
            recovery_options
        )
        
        if choice == 'fallback_direct':
            self._attempt_direct_loading_fallback()
        elif choice == 'retry_threading':
            self._retry_threading_operation()
        elif choice == 'select_different':
            self.load_ifc_file()
        else:  # cancel
            self.status_bar.showMessage("Operation cancelled due to threading error")
            self.update_ui_state(False)
    
    def _attempt_direct_loading_fallback(self):
        """
        Attempt to load the current file using direct loading as a fallback.
        """
        if not self.current_file_path:
            self.logger.error("No file path available for direct loading fallback")
            return
        
        # Update fallback statistics
        self.fallback_stats['fallback_attempts'] += 1
        self.fallback_stats['last_fallback_time'] = datetime.now()
        
        file_size_info = ""
        try:
            file_size = os.path.getsize(self.current_file_path)
            file_size_info = f" ({file_size/(1024*1024):.1f}MB)"
        except OSError:
            pass
        
        self.logger.info(f"Starting direct loading fallback #{self.fallback_stats['fallback_attempts']} for: {self.current_file_path}{file_size_info}")
        
        try:
            # Show warning about potential UI freezing
            self.status_bar.showMessage("⚠️ Attempting direct loading - UI may freeze temporarily...")
            self.status_bar.setStyleSheet("QStatusBar { color: #fd7e14; }")  # Orange warning color
            
            # Force a UI update before starting direct loading
            self.repaint()
            
            # Attempt direct loading
            self.load_file_directly(self.current_file_path)
            
            # Log successful fallback
            self.fallback_stats['fallback_successes'] += 1
            self.logger.info(f"Direct loading fallback completed successfully (success #{self.fallback_stats['fallback_successes']})")
            self._log_fallback_statistics()
            
        except Exception as e:
            # Update failure statistics
            self.fallback_stats['fallback_failures'] += 1
            self.logger.error(f"Direct loading fallback failed (failure #{self.fallback_stats['fallback_failures']}): {e}")
            self._log_fallback_statistics()
            error_details = traceback.format_exc()
            
            # Both threading and direct loading failed - this is a serious issue
            self.show_enhanced_error_message(
                "All Loading Methods Failed",
                f"Both threaded and direct loading failed for this file: {str(e)}",
                f"File: {os.path.basename(self.current_file_path)}\n"
                f"Threading error occurred first, then direct loading also failed.\n\n"
                f"This may indicate:\n"
                f"- File corruption or invalid format\n"
                f"- Insufficient system resources\n"
                f"- Application configuration issues\n\n"
                f"Error details:\n{error_details}",
                "error"
            )
            
            # Reset UI state
            self.update_ui_state(False)
            self.status_bar.showMessage("All loading methods failed")
    
    def _handle_thread_creation_failure(self, title: str, operation_func, error: Exception, *args, **kwargs):
        """
        Handle failure to create a thread for an operation.
        
        Args:
            title: Operation title
            operation_func: The function that was supposed to run in the thread
            error: The exception that occurred during thread creation
            *args, **kwargs: Arguments for the operation function
        """
        self.logger.error(f"Thread creation failed for '{title}': {error}")
        
        # Clean up any partially created resources
        if hasattr(self, 'operation_thread'):
            self.operation_thread = None
        if hasattr(self, 'operation_worker'):
            self.operation_worker = None
        
        # Hide progress indicators
        self.progress_bar.setVisible(False)
        if hasattr(self, 'cancel_button'):
            self.cancel_button.setVisible(False)
        
        # Offer fallback to direct execution
        recovery_options = {
            'fallback_direct': 'Execute directly (may freeze UI)',
            'retry_threading': 'Retry threading operation',
            'cancel': 'Cancel operation'
        }
        
        choice = self.show_enhanced_error_message(
            "Thread Creation Failed",
            f"Failed to create thread for '{title}': {str(error)}",
            f"This may be due to:\n"
            f"- System resource limitations\n"
            f"- Qt threading constraints\n"
            f"- Memory pressure\n\n"
            f"Error details: {str(error)}",
            "error",
            recovery_options
        )
        
        if choice == 'fallback_direct':
            self.logger.info(f"Falling back to direct execution for '{title}'")
            self._execute_operation_directly(title, operation_func, *args, **kwargs)
        elif choice == 'retry_threading':
            self.logger.info(f"Retrying threading operation for '{title}'")
            self.show_non_blocking_progress(title, operation_func, *args, **kwargs)
        else:
            self.status_bar.showMessage(f"Operation '{title}' cancelled due to threading error")
    
    def _handle_thread_startup_failure(self, title: str, operation_func, error: Exception, *args, **kwargs):
        """
        Handle failure to start a thread for an operation.
        
        Args:
            title: Operation title
            operation_func: The function that was supposed to run in the thread
            error: The exception that occurred during thread startup
            *args, **kwargs: Arguments for the operation function
        """
        self.logger.error(f"Thread startup failed for '{title}': {error}")
        
        # Clean up the failed thread
        if hasattr(self, 'operation_thread') and self.operation_thread:
            self.operation_thread.quit()
            self.operation_thread.wait(1000)  # Wait up to 1 second
            self.operation_thread = None
        if hasattr(self, 'operation_worker'):
            self.operation_worker = None
        
        # Clean up timeout timer
        if hasattr(self, 'operation_timeout_timer') and self.operation_timeout_timer:
            self.operation_timeout_timer.stop()
        
        # Hide progress indicators
        self.progress_bar.setVisible(False)
        if hasattr(self, 'cancel_button'):
            self.cancel_button.setVisible(False)
        
        # Offer fallback options
        recovery_options = {
            'fallback_direct': 'Execute directly (may freeze UI)',
            'retry_threading': 'Retry threading operation',
            'cancel': 'Cancel operation'
        }
        
        choice = self.show_enhanced_error_message(
            "Thread Startup Failed",
            f"Failed to start thread for '{title}': {str(error)}",
            f"The thread was created but failed to start properly.\n\n"
            f"This may be due to:\n"
            f"- Qt event loop issues\n"
            f"- System threading limitations\n"
            f"- Resource contention\n\n"
            f"Error details: {str(error)}",
            "error",
            recovery_options
        )
        
        if choice == 'fallback_direct':
            self.logger.info(f"Falling back to direct execution for '{title}' after startup failure")
            self._execute_operation_directly(title, operation_func, *args, **kwargs)
        elif choice == 'retry_threading':
            self.logger.info(f"Retrying threading operation for '{title}' after startup failure")
            # Add a small delay before retry to let system recover
            QTimer.singleShot(1000, lambda: self.show_non_blocking_progress(title, operation_func, *args, **kwargs))
        else:
            self.status_bar.showMessage(f"Operation '{title}' cancelled due to thread startup failure")
    
    def _execute_operation_directly(self, title: str, operation_func, *args, **kwargs):
        """
        Execute an operation directly (synchronously) as a fallback when threading fails.
        
        Args:
            title: Operation title
            operation_func: The function to execute
            *args, **kwargs: Arguments for the operation function
        """
        # Update fallback statistics
        self.fallback_stats['fallback_attempts'] += 1
        self.fallback_stats['last_fallback_time'] = datetime.now()
        self.fallback_stats['fallback_reasons'].append(f"Direct execution fallback for '{title}'")
        
        self.logger.info(f"Executing '{title}' directly as fallback (attempt #{self.fallback_stats['fallback_attempts']})")
        
        try:
            # Show warning about potential UI freezing
            self.status_bar.showMessage(f"⚠️ Executing '{title}' directly - UI may freeze temporarily...")
            self.status_bar.setStyleSheet("QStatusBar { color: #fd7e14; }")  # Orange warning color
            
            # Force UI update before starting
            self.repaint()
            
            # Execute the operation directly
            result = operation_func(*args, **kwargs)
            
            # Handle successful completion
            self.fallback_stats['fallback_successes'] += 1
            self.on_operation_completed(True, f"'{title}' completed successfully (direct execution)", result)
            
            self.logger.info(f"Direct execution of '{title}' completed successfully (success #{self.fallback_stats['fallback_successes']})")
            self._log_fallback_statistics()
            
        except Exception as e:
            self.fallback_stats['fallback_failures'] += 1
            self.logger.error(f"Direct execution of '{title}' failed (failure #{self.fallback_stats['fallback_failures']}): {e}")
            self._log_fallback_statistics()
            error_details = traceback.format_exc()
            
            # Both threading and direct execution failed
            self.show_enhanced_error_message(
                "All Execution Methods Failed",
                f"Both threaded and direct execution failed for '{title}': {str(e)}",
                f"Threading failed first, then direct execution also failed.\n\n"
                f"This indicates a fundamental issue with the operation or system state.\n\n"
                f"Error details:\n{error_details}",
                "error"
            )
            
            # Reset UI state
            self.update_ui_state(False)
            self.status_bar.showMessage(f"All execution methods failed for '{title}'")
    
    def _log_fallback_statistics(self):
        """Log comprehensive fallback statistics for debugging and monitoring."""
        stats = self.fallback_stats
        
        self.logger.info("=== Fallback Statistics ===")
        self.logger.info(f"Threading failures: {stats['threading_failures']}")
        self.logger.info(f"Fallback attempts: {stats['fallback_attempts']}")
        self.logger.info(f"Fallback successes: {stats['fallback_successes']}")
        self.logger.info(f"Fallback failures: {stats['fallback_failures']}")
        
        if stats['fallback_attempts'] > 0:
            success_rate = (stats['fallback_successes'] / stats['fallback_attempts']) * 100
            self.logger.info(f"Fallback success rate: {success_rate:.1f}%")
        
        if stats['last_fallback_time']:
            self.logger.info(f"Last fallback attempt: {stats['last_fallback_time']}")
        
        # Log recent fallback reasons (last 5)
        if stats['fallback_reasons']:
            recent_reasons = stats['fallback_reasons'][-5:]
            self.logger.info("Recent fallback reasons:")
            for i, reason in enumerate(recent_reasons, 1):
                self.logger.info(f"  {i}. {reason}")
        
        self.logger.info("=== End Fallback Statistics ===")
    
    def _on_thread_finished(self):
        """Handle thread finished signal for cleanup and logging."""
        self.logger.debug("Operation thread finished")
        
        # Additional cleanup if needed
        if hasattr(self, 'operation_timeout_timer') and self.operation_timeout_timer:
            self.operation_timeout_timer.stop()
    
    def _retry_threading_operation(self):
        """
        Retry the threading operation that previously failed.
        """
        if not self.current_file_path:
            self.logger.error("No file path available for threading retry")
            return
        
        self.logger.info(f"Retrying threading operation for: {self.current_file_path}")
        
        try:
            # Determine file size category to use appropriate loading method
            category, size_bytes, size_string = self.categorize_file_size(self.current_file_path)
            
            if category == FileSizeCategory.SMALL:
                # For small files, direct loading is actually preferred
                self.logger.info("File is small, using direct loading instead of threading")
                self.load_file_directly(self.current_file_path)
            else:
                # Retry threaded loading for larger files
                self.logger.info(f"Retrying threaded loading for {category.value} file ({size_string})")
                self.load_file_threaded(self.current_file_path)
                
        except Exception as e:
            self.logger.error(f"Threading retry failed: {e}")
            self.show_enhanced_error_message(
                "Retry Failed",
                f"Failed to retry the operation: {str(e)}",
                traceback.format_exc(),
                "error"
            )
    
    def handle_memory_error(self, operation: str, error: MemoryError) -> bool:
        """
        Handle memory errors with recovery options.
        
        Args:
            operation: Description of the operation that caused the memory error
            error: The MemoryError that occurred
            
        Returns:
            True if operation should be retried with reduced scope, False otherwise
        """
        recovery_options = {
            'reduce_scope': 'Reduce operation scope and retry',
            'free_memory': 'Free memory and retry',
            'abort': 'Abort operation'
        }
        
        choice = self.show_enhanced_error_message(
            "Memory Error",
            f"Insufficient memory for {operation}. The operation requires more memory than available.",
            f"Error: {str(error)}\n\nSuggestions:\n"
            f"- Close other applications to free memory\n"
            f"- Process smaller batches of data\n"
            f"- Restart the application to clear memory leaks",
            "error",
            recovery_options
        )
        
        if choice == 'free_memory':
            self.free_memory_resources()
            return True
        elif choice == 'reduce_scope':
            return True
        
        return False
    
    def free_memory_resources(self):
        """Free memory resources and perform garbage collection."""
        import gc
        import weakref
        
        try:
            self.logger.info("Starting comprehensive memory cleanup...")
            initial_memory = self._get_memory_usage()
            
            # 1. Clean up threads and workers first
            self._cleanup_all_threads_and_workers()
            
            # 2. Clear all extractor caches
            extractors = [
                self.space_extractor,
                self.surface_extractor, 
                self.boundary_parser,
                self.relationship_parser
            ]
            
            for extractor in extractors:
                if extractor:
                    try:
                        # Clear various cache attributes that might exist
                        cache_attrs = ['_spaces_cache', '_surfaces_cache', '_boundaries_cache', 
                                     '_relationships_cache', '_cache', '_data_cache', 
                                     '_ifc_file', '_parsed_data', '_entity_cache']
                        for attr in cache_attrs:
                            if hasattr(extractor, attr):
                                old_value = getattr(extractor, attr)
                                setattr(extractor, attr, None)
                                # Force deletion of the old value if it's a large object
                                if old_value is not None:
                                    del old_value
                                self.logger.debug(f"Cleared {attr} from {extractor.__class__.__name__}")
                        
                        # Call clear_cache method if available
                        if hasattr(extractor, 'clear_cache'):
                            extractor.clear_cache()
                            
                    except Exception as e:
                        self.handle_resource_cleanup_error(f"{extractor.__class__.__name__}", e)
            
            # 3. Clear IFC file reader data
            if hasattr(self, 'ifc_reader') and self.ifc_reader:
                try:
                    if hasattr(self.ifc_reader, 'ifc_file'):
                        self.ifc_reader.ifc_file = None
                    if hasattr(self.ifc_reader, '_file_cache'):
                        self.ifc_reader._file_cache = None
                except Exception as e:
                    self.handle_resource_cleanup_error("IFC Reader", e)
            
            # 4. Clear main window data
            if hasattr(self, 'spaces'):
                try:
                    self.spaces.clear()
                    self.spaces = []
                except Exception as e:
                    self.handle_resource_cleanup_error("spaces data", e)
            
            # 5. Clear UI data
            self._cleanup_ui_data()
            
            # 6. Clear operation state
            self._reset_operation_state()
            
            # 7. Force multiple garbage collection passes for better cleanup
            for i in range(3):
                collected = gc.collect()
                self.logger.debug(f"Garbage collection pass {i+1}: collected {collected} objects")
            
            # 8. Log memory usage comparison
            final_memory = self._get_memory_usage()
            if initial_memory and final_memory:
                freed_mb = (initial_memory - final_memory) / (1024 * 1024)
                self.logger.info(f"Memory cleanup completed. Freed: {freed_mb:.1f}MB")
            
            self.status_bar.showMessage("Memory resources freed", 3000)
            
        except Exception as e:
            self.logger.error(f"Error during memory cleanup: {e}")
            self.status_bar.showMessage(f"Memory cleanup error: {str(e)}", 5000)
    
    def _cleanup_all_threads_and_workers(self):
        """Clean up all active threads and workers with proper resource management."""
        try:
            # Clean up main operation thread and worker
            if hasattr(self, 'operation_thread') and self.operation_thread:
                self._cleanup_thread_worker_pair(self.operation_thread, self.operation_worker, "main operation")
                self.operation_thread = None
                self.operation_worker = None
            
            # Clean up any other threads that might be running
            active_threads = []
            for attr_name in dir(self):
                if attr_name.endswith('_thread') and hasattr(self, attr_name):
                    thread = getattr(self, attr_name)
                    if thread and hasattr(thread, 'isRunning') and thread.isRunning():
                        active_threads.append((attr_name, thread))
            
            for thread_name, thread in active_threads:
                self.logger.info(f"Cleaning up active thread: {thread_name}")
                self._cleanup_thread_worker_pair(thread, None, thread_name)
                setattr(self, thread_name, None)
            
            # Clean up timeout timers
            if hasattr(self, 'operation_timeout_timer') and self.operation_timeout_timer:
                self.operation_timeout_timer.stop()
                self.operation_timeout_timer.deleteLater()
                self.operation_timeout_timer = None
                
        except Exception as e:
            self.logger.error(f"Error during thread cleanup: {e}")
    
    def _cleanup_thread_worker_pair(self, thread, worker, operation_name="unknown"):
        """Clean up a specific thread-worker pair with proper resource management."""
        try:
            cleanup_start_time = datetime.now()
            
            # Clean up worker first
            if worker:
                try:
                    # Unregister from monitoring
                    self.unregister_worker(worker, operation_name)
                    
                    # Request cancellation if possible
                    if hasattr(worker, 'request_cancellation'):
                        worker.request_cancellation()
                    
                    # Disconnect all signals to prevent callbacks during cleanup
                    if hasattr(worker, 'disconnect'):
                        worker.disconnect()
                    
                    # Delete the worker
                    worker.deleteLater()
                    self.logger.debug(f"Worker for {operation_name} cleaned up")
                except Exception as e:
                    self.logger.warning(f"Error cleaning up worker for {operation_name}: {e}")
            
            # Clean up thread
            if thread and hasattr(thread, 'isRunning'):
                try:
                    # Unregister from monitoring
                    self.unregister_thread(thread, operation_name)
                    
                    if thread.isRunning():
                        self.logger.info(f"Terminating running thread for {operation_name}")
                        
                        # Try graceful shutdown first
                        thread.quit()
                        if not thread.wait(2000):  # Wait 2 seconds
                            self.logger.warning(f"Graceful shutdown failed for {operation_name}, forcing termination")
                            thread.terminate()
                            
                            # Wait for forced termination
                            if not thread.wait(3000):  # Wait 3 more seconds
                                self.logger.error(f"Thread for {operation_name} did not terminate, potential resource leak")
                                
                                # Record resource leak
                                self.resource_monitor['cleanup_history'].append({
                                    'timestamp': datetime.now(),
                                    'event': 'thread_cleanup_failed',
                                    'operation': operation_name,
                                    'details': 'Thread did not terminate after forced termination'
                                })
                            else:
                                self.logger.info(f"Thread for {operation_name} terminated successfully")
                        else:
                            self.logger.info(f"Thread for {operation_name} shut down gracefully")
                    
                    # Delete the thread
                    thread.deleteLater()
                    self.logger.debug(f"Thread for {operation_name} cleaned up")
                    
                except Exception as e:
                    self.logger.warning(f"Error cleaning up thread for {operation_name}: {e}")
            
            # Record successful cleanup
            cleanup_duration = (datetime.now() - cleanup_start_time).total_seconds()
            self.resource_monitor['cleanup_history'].append({
                'timestamp': cleanup_start_time,
                'event': 'thread_worker_cleanup',
                'operation': operation_name,
                'duration_seconds': cleanup_duration,
                'success': True
            })
                    
        except Exception as e:
            self.logger.error(f"Error in thread-worker cleanup for {operation_name}: {e}")
            
            # Record failed cleanup
            self.resource_monitor['cleanup_history'].append({
                'timestamp': datetime.now(),
                'event': 'thread_worker_cleanup',
                'operation': operation_name,
                'success': False,
                'error': str(e)
            })
    
    def _cleanup_ui_data(self):
        """Clean up UI-related data and widgets."""
        try:
            # Clear UI data
            if hasattr(self, 'space_list_widget') and self.space_list_widget:
                try:
                    self.space_list_widget.clear_selection()
                    # Clear the spaces list in the widget
                    if hasattr(self.space_list_widget, 'spaces'):
                        self.space_list_widget.spaces.clear()
                    if hasattr(self.space_list_widget, '_cached_data'):
                        self.space_list_widget._cached_data = None
                except Exception as e:
                    self.handle_resource_cleanup_error("space list widget", e)
                    
            if hasattr(self, 'space_detail_widget') and self.space_detail_widget:
                try:
                    self.space_detail_widget.clear_selection()
                    if hasattr(self.space_detail_widget, '_current_space'):
                        self.space_detail_widget._current_space = None
                except Exception as e:
                    self.handle_resource_cleanup_error("space detail widget", e)
                    
            if hasattr(self, 'surface_editor_widget') and self.surface_editor_widget:
                try:
                    if hasattr(self.surface_editor_widget, 'clear_data'):
                        self.surface_editor_widget.clear_data()
                    if hasattr(self.surface_editor_widget, '_surfaces_data'):
                        self.surface_editor_widget._surfaces_data = None
                except Exception as e:
                    self.handle_resource_cleanup_error("surface editor widget", e)
                    
        except Exception as e:
            self.logger.error(f"Error during UI data cleanup: {e}")
    
    def _reset_operation_state(self):
        """Reset all operation-related state variables."""
        try:
            # Reset operation tracking
            self.current_file_path = None
            if hasattr(self, 'current_operation_id'):
                self.current_operation_id = None
            if hasattr(self, 'operation_start_time'):
                self.operation_start_time = None
            if hasattr(self, 'current_timeout_seconds'):
                self.current_timeout_seconds = None
            
            # Reset fallback statistics
            if hasattr(self, 'fallback_stats'):
                self.fallback_stats = {
                    'threading_failures': 0,
                    'fallback_attempts': 0,
                    'fallback_successes': 0,
                    'fallback_failures': 0,
                    'last_fallback_time': None,
                    'fallback_reasons': []
                }
            
        except Exception as e:
            self.logger.error(f"Error resetting operation state: {e}")
    
    def _get_memory_usage(self):
        """Get current memory usage in bytes, return None if unavailable."""
        try:
            import psutil
            return psutil.Process().memory_info().rss
        except (ImportError, Exception):
            return None
    
    def setup_resource_monitoring(self):
        """Setup periodic resource monitoring and cleanup verification."""
        try:
            # Create a timer for periodic resource monitoring
            self.resource_monitor_timer = QTimer()
            self.resource_monitor_timer.timeout.connect(self.verify_resource_cleanup)
            self.resource_monitor_timer.start(30000)  # Check every 30 seconds
            
            # Register the timer in our monitor
            self.resource_monitor['active_timers'].add(id(self.resource_monitor_timer))
            
            self.logger.debug("Resource monitoring setup completed")
            
        except Exception as e:
            self.logger.error(f"Error setting up resource monitoring: {e}")
    
    def register_thread(self, thread, operation_name="unknown"):
        """Register a thread for monitoring."""
        if thread:
            thread_id = id(thread)
            self.resource_monitor['active_threads'].add(thread_id)
            self.logger.debug(f"Registered thread {thread_id} for operation: {operation_name}")
    
    def register_worker(self, worker, operation_name="unknown"):
        """Register a worker for monitoring."""
        if worker:
            worker_id = id(worker)
            self.resource_monitor['active_workers'].add(worker_id)
            self.logger.debug(f"Registered worker {worker_id} for operation: {operation_name}")
    
    def unregister_thread(self, thread, operation_name="unknown"):
        """Unregister a thread from monitoring."""
        if thread:
            thread_id = id(thread)
            self.resource_monitor['active_threads'].discard(thread_id)
            self.logger.debug(f"Unregistered thread {thread_id} for operation: {operation_name}")
    
    def unregister_worker(self, worker, operation_name="unknown"):
        """Unregister a worker from monitoring."""
        if worker:
            worker_id = id(worker)
            self.resource_monitor['active_workers'].discard(worker_id)
            self.logger.debug(f"Unregistered worker {worker_id} for operation: {operation_name}")
    
    def verify_resource_cleanup(self):
        """Verify that resources have been properly cleaned up."""
        try:
            from datetime import datetime
            verification_time = datetime.now()
            
            # Take memory snapshot
            current_memory = self._get_memory_usage()
            if current_memory:
                self.resource_monitor['memory_snapshots'].append({
                    'timestamp': verification_time,
                    'memory_bytes': current_memory,
                    'memory_mb': current_memory / (1024 * 1024)
                })
                
                # Keep only last 10 snapshots
                if len(self.resource_monitor['memory_snapshots']) > 10:
                    self.resource_monitor['memory_snapshots'].pop(0)
            
            # Check for resource leaks
            leaks_detected = 0
            leak_details = []
            
            # Check for orphaned threads
            active_threads = []
            for attr_name in dir(self):
                if attr_name.endswith('_thread') and hasattr(self, attr_name):
                    thread = getattr(self, attr_name)
                    if thread and hasattr(thread, 'isRunning') and thread.isRunning():
                        active_threads.append(attr_name)
            
            if active_threads:
                leaks_detected += len(active_threads)
                leak_details.append(f"Active threads: {', '.join(active_threads)}")
            
            # Check for orphaned timers
            active_timers = 0
            for attr_name in dir(self):
                if attr_name.endswith('_timer') and hasattr(self, attr_name):
                    timer = getattr(self, attr_name)
                    if timer and hasattr(timer, 'isActive') and timer.isActive():
                        active_timers += 1
            
            if active_timers > 1:  # Allow resource_monitor_timer
                leaks_detected += active_timers - 1
                leak_details.append(f"Unexpected active timers: {active_timers - 1}")
            
            # Update resource monitor
            self.resource_monitor['resource_leaks_detected'] = leaks_detected
            self.resource_monitor['last_cleanup_verification'] = verification_time
            
            # Log results
            if leaks_detected > 0:
                self.logger.warning(f"Resource leaks detected: {leaks_detected} - {'; '.join(leak_details)}")
            else:
                self.logger.debug("Resource cleanup verification: all clean")
            
            # Check memory growth
            self._check_memory_growth()
            
        except Exception as e:
            self.logger.error(f"Error during resource cleanup verification: {e}")
    
    def _check_memory_growth(self):
        """Check for concerning memory growth patterns."""
        try:
            snapshots = self.resource_monitor['memory_snapshots']
            if len(snapshots) < 5:
                return  # Need at least 5 snapshots to detect trends
            
            # Check if memory has grown consistently over last 5 snapshots
            recent_snapshots = snapshots[-5:]
            memory_values = [s['memory_mb'] for s in recent_snapshots]
            
            # Simple trend detection: check if each value is larger than the previous
            is_growing = all(memory_values[i] > memory_values[i-1] for i in range(1, len(memory_values)))
            
            if is_growing:
                growth = memory_values[-1] - memory_values[0]
                if growth > 50:  # More than 50MB growth
                    self.logger.warning(f"Significant memory growth detected: {growth:.1f}MB over last 5 checks")
                    
                    # Record this in cleanup history
                    self.resource_monitor['cleanup_history'].append({
                        'timestamp': datetime.now(),
                        'event': 'memory_growth_detected',
                        'details': f"Growth: {growth:.1f}MB",
                        'memory_mb': memory_values[-1]
                    })
                    
        except Exception as e:
            self.logger.error(f"Error checking memory growth: {e}")
    
    def get_resource_monitor_report(self):
        """Get a comprehensive resource monitoring report."""
        try:
            report = {
                'active_threads_count': len(self.resource_monitor['active_threads']),
                'active_workers_count': len(self.resource_monitor['active_workers']),
                'active_timers_count': len(self.resource_monitor['active_timers']),
                'resource_leaks_detected': self.resource_monitor['resource_leaks_detected'],
                'last_verification': self.resource_monitor['last_cleanup_verification'],
                'cleanup_events': len(self.resource_monitor['cleanup_history']),
                'memory_snapshots_count': len(self.resource_monitor['memory_snapshots'])
            }
            
            # Add current memory if available
            current_memory = self._get_memory_usage()
            if current_memory:
                report['current_memory_mb'] = current_memory / (1024 * 1024)
            
            # Add memory trend if we have enough snapshots
            if len(self.resource_monitor['memory_snapshots']) >= 2:
                first_snapshot = self.resource_monitor['memory_snapshots'][0]['memory_mb']
                last_snapshot = self.resource_monitor['memory_snapshots'][-1]['memory_mb']
                report['memory_change_mb'] = last_snapshot - first_snapshot
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating resource monitor report: {e}")
            return {'error': str(e)}
    
    def handle_resource_cleanup_error(self, resource_name: str, error: Exception):
        """
        Handle errors during resource cleanup.
        
        Args:
            resource_name: Name of the resource being cleaned up
            error: The exception that occurred during cleanup
        """
        self.logger.warning(f"Failed to cleanup {resource_name}: {str(error)}")
        
        # Don't show dialog for cleanup errors unless they're critical
        if isinstance(error, (OSError, IOError)):
            self.show_enhanced_error_message(
                "Resource Cleanup Warning",
                f"Failed to properly cleanup {resource_name}. This may cause resource leaks.",
                f"Error: {str(error)}\n\nThis is usually not critical but may affect performance.",
                "warning"
            )
    
    def restart_application(self):
        """Restart the application."""
        self.logger.info("Restarting application...")
        self.close()
        os.execl(sys.executable, sys.executable, *sys.argv)
    
    def handle_batch_operation_errors(self, operation_name: str, total_items: int, 
                                    failed_items: list, skipped_items: list) -> str:
        """
        Handle errors from batch operations with user choice for continuation.
        
        Args:
            operation_name: Name of the operation being performed
            total_items: Total number of items being processed
            failed_items: List of (item_id, error_message) tuples for failed items
            skipped_items: List of (item_id, reason) tuples for skipped items
            
        Returns:
            User's choice: 'continue', 'retry_failed', 'abort'
        """
        if not failed_items and not skipped_items:
            return 'continue'
        
        success_count = total_items - len(failed_items) - len(skipped_items)
        
        summary_parts = []
        if success_count > 0:
            summary_parts.append(f"{success_count} successful")
        if failed_items:
            summary_parts.append(f"{len(failed_items)} failed")
        if skipped_items:
            summary_parts.append(f"{len(skipped_items)} skipped")
        
        summary = f"{operation_name} results: {', '.join(summary_parts)} out of {total_items} items"
        
        recovery_options = {
            'continue': 'Continue with successful items',
            'abort': 'Abort the entire operation'
        }
        
        if failed_items:
            recovery_options['retry_failed'] = f'Retry {len(failed_items)} failed items'
        
        choice = self.show_enhanced_error_message(
            f"{operation_name} Partial Failure",
            summary,
            self._format_batch_error_details(failed_items, skipped_items),
            "warning",
            recovery_options
        )
        
        return choice if choice else 'abort'
    
    def _format_batch_error_details(self, failed_items: list, skipped_items: list) -> str:
        """Format detailed error information for batch operations."""
        details = []
        
        if failed_items:
            details.append("Failed items:")
            for item_id, error in failed_items[:10]:  # Limit to first 10
                details.append(f"  - {item_id}: {str(error)[:100]}...")
            if len(failed_items) > 10:
                details.append(f"  ... and {len(failed_items) - 10} more failed items")
        
        if skipped_items:
            if details:
                details.append("")
            details.append("Skipped items:")
            for item_id, reason in skipped_items[:10]:  # Limit to first 10
                details.append(f"  - {item_id}: {reason}")
            if len(skipped_items) > 10:
                details.append(f"  ... and {len(skipped_items) - 10} more skipped items")
        
        return '\n'.join(details)
    
    def validate_operation_prerequisites(self, operation_name: str, prerequisites: dict) -> bool:
        """
        Validate prerequisites for an operation and show appropriate error messages.
        
        Args:
            operation_name: Name of the operation
            prerequisites: Dict of prerequisite_name -> (is_met, error_message)
            
        Returns:
            True if all prerequisites are met, False otherwise
        """
        failed_prerequisites = []
        
        for prereq_name, (is_met, error_msg) in prerequisites.items():
            if not is_met:
                failed_prerequisites.append((prereq_name, error_msg))
        
        if failed_prerequisites:
            error_details = []
            for prereq_name, error_msg in failed_prerequisites:
                error_details.append(f"- {prereq_name}: {error_msg}")
            
            self.show_enhanced_error_message(
                f"Cannot {operation_name}",
                f"Operation cannot proceed due to {len(failed_prerequisites)} unmet prerequisites",
                '\n'.join(error_details),
                "error"
            )
            return False
        
        return True
    
    def handle_file_operation_error(self, operation: str, file_path: str, error: Exception) -> bool:
        """
        Handle file operation errors with recovery options.
        
        Args:
            operation: Description of the operation that failed
            file_path: Path to the file involved
            error: The exception that occurred
            
        Returns:
            True if operation should be retried, False otherwise
        """
        error_msg = f"Failed to {operation}: {str(error)}"
        
        recovery_options = {
            'retry': f'Retry {operation}',
            'select_different': 'Select a different file',
            'cancel': 'Cancel operation'
        }
        
        choice = self.show_enhanced_error_message(
            f"File Operation Error",
            error_msg,
            f"File: {file_path}\nError: {str(error)}",
            "error",
            recovery_options
        )
        
        if choice == 'retry':
            return True
        elif choice == 'select_different':
            self.load_ifc_file()
            return False
        else:  # cancel
            return False
    
    def handle_parsing_error(self, parser_name: str, entity_id: str, error: Exception) -> bool:
        """
        Handle parsing errors with graceful degradation options.
        
        Args:
            parser_name: Name of the parser that failed
            entity_id: ID of the entity being parsed
            error: The exception that occurred
            
        Returns:
            True if parsing should continue with other entities, False to stop
        """
        error_msg = f"{parser_name} failed to parse entity {entity_id}"
        
        recovery_options = {
            'continue': 'Continue with remaining entities',
            'skip_type': f'Skip all entities of this type',
            'stop': 'Stop processing'
        }
        
        choice = self.show_enhanced_error_message(
            "Parsing Error",
            error_msg,
            f"Entity: {entity_id}\nParser: {parser_name}\nError: {str(error)}",
            "warning",
            recovery_options
        )
        
        return choice in ['continue', 'skip_type']
        
    def setup_ui(self):
        """Set up the main user interface."""
        self.setWindowTitle("IFC Room Schedule")
        self.setGeometry(100, 100, 1400, 800)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create main layout
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # File loading section with enhanced styling
        file_section = QWidget()
        file_section.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                margin: 5px;
            }
        """)
        file_layout = QHBoxLayout()
        file_section.setLayout(file_layout)
        
        # File info with icon-like styling
        self.file_label = QLabel("No IFC file loaded")
        self.file_label.setStyleSheet("""
            QLabel {
                padding: 12px 16px;
                background-color: white;
                border: 1px solid #ced4da;
                border-radius: 4px;
                color: #495057;
                font-size: 13px;
            }
        """)
        file_layout.addWidget(self.file_label, 1)  # Give it more space
        
        self.load_button = QPushButton("Load IFC File")
        self.load_button.clicked.connect(self.load_ifc_file)
        self.load_button.setStyleSheet("""
            QPushButton {
                padding: 12px 24px;
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #004085;
            }
        """)
        file_layout.addWidget(self.load_button)
        
        main_layout.addWidget(file_section)
        
        # Progress bar with enhanced styling
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ced4da;
                border-radius: 4px;
                text-align: center;
                background-color: #f8f9fa;
                height: 20px;
            }
            QProgressBar::chunk {
                background-color: #28a745;
                border-radius: 3px;
            }
        """)
        main_layout.addWidget(self.progress_bar)
        
        # Cancel button for long operations
        self.cancel_button = QPushButton("Cancel Operation")
        self.cancel_button.clicked.connect(self.cancel_operation)
        self.cancel_button.setVisible(False)
        self.cancel_button.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:pressed {
                background-color: #bd2130;
            }
        """)
        main_layout.addWidget(self.cancel_button)
        
        # Create splitter for main content
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #dee2e6;
                width: 2px;
            }
            QSplitter::handle:hover {
                background-color: #adb5bd;
            }
        """)
        main_layout.addWidget(self.main_splitter)
        
        # Left panel: Space list with enhanced container
        left_panel = QWidget()
        left_panel.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border-right: 1px solid #dee2e6;
            }
        """)
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(8, 8, 8, 8)
        left_panel.setLayout(left_layout)
        
        self.space_list_widget = SpaceListWidget()
        left_layout.addWidget(self.space_list_widget)
        
        left_panel.setMinimumWidth(320)
        left_panel.setMaximumWidth(450)
        self.main_splitter.addWidget(left_panel)
        
        # Right panel: Space details and editor with enhanced container
        right_panel = QWidget()
        right_panel.setStyleSheet("""
            QWidget {
                background-color: white;
            }
        """)
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(8, 8, 8, 8)
        right_panel.setLayout(right_layout)
        
        # Create horizontal splitter for details and editor
        self.details_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.details_splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #dee2e6;
                width: 2px;
            }
            QSplitter::handle:hover {
                background-color: #adb5bd;
            }
        """)
        
        # Space details widget
        self.space_detail_widget = SpaceDetailWidget()
        self.details_splitter.addWidget(self.space_detail_widget)
        
        # Surface editor widget
        self.surface_editor_widget = SurfaceEditorWidget()
        self.details_splitter.addWidget(self.surface_editor_widget)
        
        # Set proportions (60% details, 40% editor)
        self.details_splitter.setSizes([600, 400])
        
        right_layout.addWidget(self.details_splitter)
        self.main_splitter.addWidget(right_panel)
        
        # Set splitter proportions (30% left, 70% right)
        self.main_splitter.setSizes([320, 800])
        
        # Initially hide the main content until file is loaded
        self.main_splitter.setVisible(False)
        
        # Enhanced welcome message
        self.welcome_label = QLabel("Welcome to IFC Room Schedule\n\nSelect an IFC file to begin analyzing spaces...")
        self.welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.welcome_label.setStyleSheet("""
            QLabel {
                padding: 60px;
                color: #6c757d;
                font-size: 16px;
                line-height: 1.5;
                background-color: #f8f9fa;
                border: 2px dashed #dee2e6;
                border-radius: 8px;
                margin: 20px;
            }
        """)
        self.welcome_label.setVisible(True)  # Ensure it's visible initially
        main_layout.addWidget(self.welcome_label)
        
    def setup_menu(self):
        """Set up the application menu bar with comprehensive options."""
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar {
                background-color: #f8f9fa;
                border-bottom: 1px solid #dee2e6;
                padding: 4px;
            }
            QMenuBar::item {
                padding: 6px 12px;
                background-color: transparent;
                border-radius: 4px;
            }
            QMenuBar::item:selected {
                background-color: #e9ecef;
            }
        """)
        
        # File menu
        file_menu = menubar.addMenu('&File')
        
        # Open action with enhanced properties
        open_action = QAction('&Open IFC File...', self)
        open_action.setShortcut('Ctrl+O')
        open_action.setStatusTip('Open an IFC file for processing')
        open_action.triggered.connect(self.load_ifc_file)
        file_menu.addAction(open_action)
        
        # Recent files submenu (enhanced for future implementation)
        recent_menu = file_menu.addMenu('&Recent Files')
        recent_menu.setEnabled(False)  # Disabled for now
        recent_menu.setStatusTip('Recently opened IFC files')
        
        file_menu.addSeparator()
        
        # Close action
        close_action = QAction('&Close File', self)
        close_action.setShortcut('Ctrl+W')
        close_action.setStatusTip('Close the current IFC file')
        close_action.triggered.connect(self.close_file)
        close_action.setEnabled(False)  # Initially disabled
        file_menu.addAction(close_action)
        self.close_action = close_action
        
        file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction('E&xit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.setStatusTip('Exit the application')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu with enhanced options
        view_menu = menubar.addMenu('&View')
        
        # Refresh action
        refresh_action = QAction('&Refresh', self)
        refresh_action.setShortcut('F5')
        refresh_action.setStatusTip('Refresh the current view and reload space data')
        refresh_action.triggered.connect(self.refresh_view)
        refresh_action.setEnabled(False)
        view_menu.addAction(refresh_action)
        self.refresh_action = refresh_action
        
        view_menu.addSeparator()
        
        # Panel visibility actions
        show_spaces_action = QAction('Show &Spaces Panel', self)
        show_spaces_action.setCheckable(True)
        show_spaces_action.setChecked(True)
        show_spaces_action.setStatusTip('Show or hide the spaces navigation panel')
        show_spaces_action.triggered.connect(self.toggle_spaces_panel)
        view_menu.addAction(show_spaces_action)
        self.show_spaces_action = show_spaces_action
        
        # Zoom actions for future implementation
        view_menu.addSeparator()
        zoom_in_action = QAction('Zoom &In', self)
        zoom_in_action.setShortcut('Ctrl++')
        zoom_in_action.setEnabled(False)  # Future implementation
        view_menu.addAction(zoom_in_action)
        
        zoom_out_action = QAction('Zoom &Out', self)
        zoom_out_action.setShortcut('Ctrl+-')
        zoom_out_action.setEnabled(False)  # Future implementation
        view_menu.addAction(zoom_out_action)
        
        # Navigation menu
        nav_menu = menubar.addMenu('&Navigate')
        
        # Space navigation actions
        next_space_action = QAction('&Next Space', self)
        next_space_action.setShortcut('Ctrl+Right')
        next_space_action.setStatusTip('Navigate to the next space')
        next_space_action.triggered.connect(self.navigate_next_space)
        next_space_action.setEnabled(False)
        nav_menu.addAction(next_space_action)
        self.next_space_action = next_space_action
        
        prev_space_action = QAction('&Previous Space', self)
        prev_space_action.setShortcut('Ctrl+Left')
        prev_space_action.setStatusTip('Navigate to the previous space')
        prev_space_action.triggered.connect(self.navigate_previous_space)
        prev_space_action.setEnabled(False)
        nav_menu.addAction(prev_space_action)
        self.prev_space_action = prev_space_action
        
        nav_menu.addSeparator()
        
        # Go to space action
        goto_space_action = QAction('&Go to Space...', self)
        goto_space_action.setShortcut('Ctrl+G')
        goto_space_action.setStatusTip('Go to a specific space by number or name')
        goto_space_action.triggered.connect(self.show_goto_space_dialog)
        goto_space_action.setEnabled(False)
        nav_menu.addAction(goto_space_action)
        self.goto_space_action = goto_space_action
        
        # Tools menu with enhanced export options
        tools_menu = menubar.addMenu('&Tools')
        
        # Export submenu
        export_menu = tools_menu.addMenu('&Export')
        
        # JSON export
        export_json_action = QAction('Export as &JSON...', self)
        export_json_action.setShortcut('Ctrl+E')
        export_json_action.setStatusTip('Export space data to JSON file')
        export_json_action.setEnabled(False)
        export_json_action.triggered.connect(self.export_json)
        export_menu.addAction(export_json_action)
        self.export_action = export_json_action
        
        # Additional export formats (for future implementation)
        export_csv_action = QAction('Export as &CSV...', self)
        export_csv_action.setStatusTip('Export space data to CSV file')
        export_csv_action.setEnabled(False)
        export_menu.addAction(export_csv_action)
        
        export_excel_action = QAction('Export as &Excel...', self)
        export_excel_action.setStatusTip('Export space data to Excel file')
        export_excel_action.setEnabled(False)
        export_menu.addAction(export_excel_action)
        
        tools_menu.addSeparator()
        
        # Validation tools
        validate_action = QAction('&Validate Data', self)
        validate_action.setShortcut('Ctrl+Shift+V')
        validate_action.setStatusTip('Validate current space data for completeness')
        validate_action.triggered.connect(self.validate_data)
        validate_action.setEnabled(False)
        tools_menu.addAction(validate_action)
        self.validate_action = validate_action
        
        # Help menu
        help_menu = menubar.addMenu('&Help')
        
        # User guide action
        user_guide_action = QAction('&User Guide', self)
        user_guide_action.setShortcut('F1')
        user_guide_action.setStatusTip('Open the user guide')
        user_guide_action.triggered.connect(self.show_user_guide)
        help_menu.addAction(user_guide_action)
        
        help_menu.addSeparator()
        
        # About action
        about_action = QAction('&About', self)
        about_action.setStatusTip('About IFC Room Schedule application')
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def setup_toolbar(self):
        """Set up the application toolbar with comprehensive tools."""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        toolbar.setStyleSheet("""
            QToolBar {
                background-color: #f8f9fa;
                border-bottom: 1px solid #dee2e6;
                spacing: 4px;
                padding: 4px;
            }
            QToolButton {
                background-color: transparent;
                border: 1px solid transparent;
                border-radius: 4px;
                padding: 6px;
                margin: 2px;
                min-width: 60px;
            }
            QToolButton:hover {
                background-color: #e9ecef;
                border-color: #adb5bd;
            }
            QToolButton:pressed {
                background-color: #dee2e6;
            }
            QToolButton:disabled {
                color: #6c757d;
                background-color: transparent;
            }
        """)
        self.addToolBar(toolbar)
        
        # File operations section
        open_action = QAction('📁\nOpen', self)
        open_action.setStatusTip('Open an IFC file for processing')
        open_action.triggered.connect(self.load_ifc_file)
        toolbar.addAction(open_action)
        
        close_action = QAction('❌\nClose', self)
        close_action.setStatusTip('Close the current IFC file')
        close_action.triggered.connect(self.close_file)
        close_action.setEnabled(False)
        toolbar.addAction(close_action)
        self.toolbar_close_action = close_action
        
        toolbar.addSeparator()
        
        # View operations section
        refresh_action = QAction('🔄\nRefresh', self)
        refresh_action.setStatusTip('Refresh the current view and reload space data')
        refresh_action.triggered.connect(self.refresh_view)
        refresh_action.setEnabled(False)
        toolbar.addAction(refresh_action)
        self.toolbar_refresh_action = refresh_action
        
        # Navigation section
        toolbar.addSeparator()
        
        prev_action = QAction('⬅️\nPrevious', self)
        prev_action.setStatusTip('Navigate to the previous space')
        prev_action.triggered.connect(self.navigate_previous_space)
        prev_action.setEnabled(False)
        toolbar.addAction(prev_action)
        self.toolbar_prev_action = prev_action
        
        next_action = QAction('➡️\nNext', self)
        next_action.setStatusTip('Navigate to the next space')
        next_action.triggered.connect(self.navigate_next_space)
        next_action.setEnabled(False)
        toolbar.addAction(next_action)
        self.toolbar_next_action = next_action
        
        # Tools section
        toolbar.addSeparator()
        
        validate_action = QAction('✅\nValidate', self)
        validate_action.setStatusTip('Validate current space data for completeness')
        validate_action.triggered.connect(self.validate_data)
        validate_action.setEnabled(False)
        toolbar.addAction(validate_action)
        self.toolbar_validate_action = validate_action
        
        export_action = QAction('💾\nExport', self)
        export_action.setStatusTip('Export space data to JSON file')
        export_action.triggered.connect(self.export_json)
        export_action.setEnabled(False)
        toolbar.addAction(export_action)
        self.toolbar_export_action = export_action
        
        # Add spacer to push status info to the right
        spacer = QWidget()
        from PyQt6.QtWidgets import QSizePolicy
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar.addWidget(spacer)
        
        # Status information in toolbar
        self.toolbar_status_label = QLabel("Ready")
        self.toolbar_status_label.setStyleSheet("""
            QLabel {
                color: #495057;
                font-size: 12px;
                padding: 4px 8px;
                background-color: #e9ecef;
                border-radius: 4px;
                margin: 2px;
            }
        """)
        toolbar.addWidget(self.toolbar_status_label)
        
    def setup_status_bar(self):
        """Set up the status bar with enhanced styling."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready to load IFC file...")
        
        # Style the status bar
        self.status_bar.setStyleSheet("""
            QStatusBar {
                background-color: #f8f9fa;
                border-top: 1px solid #dee2e6;
                padding: 4px 8px;
                color: #495057;
            }
        """)
        
    def connect_signals(self):
        """Connect widget signals."""
        # Connect space list signals
        self.space_list_widget.space_selected.connect(self.on_space_selected)
        self.space_list_widget.spaces_loaded.connect(self.on_spaces_loaded)
        
        # Connect space detail signals
        self.space_detail_widget.surface_selected.connect(self.on_surface_selected)
        self.space_detail_widget.boundary_selected.connect(self.on_boundary_selected)
        
        # Connect surface editor signals
        self.surface_editor_widget.surface_description_changed.connect(self.on_surface_description_changed)
        self.surface_editor_widget.boundary_description_changed.connect(self.on_boundary_description_changed)
        
    def load_ifc_file(self):
        """Open file dialog and load selected IFC file."""
        file_dialog = QFileDialog(self)
        file_dialog.setWindowTitle("Select IFC File")
        file_dialog.setNameFilter("IFC Files (*.ifc *.ifcxml);;All Files (*)")
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        
        if file_dialog.exec():
            file_paths = file_dialog.selectedFiles()
            if file_paths:
                self.process_ifc_file(file_paths[0])
    
    def process_ifc_file(self, file_path: str):
        """Process the selected IFC file with smart loading strategy based on file size."""
        self.status_bar.showMessage("Analyzing file...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        
        try:
            # Categorize file size for smart loading strategy
            file_category, file_size_bytes, file_size_string = self.categorize_file_size(file_path)
            
            self.logger.info(f"Processing {file_category.value} file: {file_size_string}")
            
            # First validate the file
            is_valid, validation_message = self.ifc_reader.validate_file(file_path)
            
            if not is_valid:
                recovery_options = {
                    'select_different': 'Select a different IFC file',
                    'force_load': 'Try to load anyway (may cause errors)',
                    'cancel': 'Cancel operation'
                }
                
                choice = self.show_enhanced_error_message(
                    "File Validation Error", 
                    validation_message,
                    f"File: {file_path}",
                    "error",
                    recovery_options
                )
                
                if choice == 'select_different':
                    self.load_ifc_file()
                elif choice == 'force_load':
                    self.logger.warning(f"Force loading invalid file: {file_path}")
                    # Continue with loading
                else:
                    self.progress_bar.setVisible(False)
                    self.status_bar.showMessage("File validation cancelled")
                    return
            
            # Apply smart loading strategy based on file size
            if file_category == FileSizeCategory.SMALL:
                # Direct loading for small files (< 10MB) to avoid threading overhead
                self.logger.info("Using direct loading strategy for small file")
                self.status_bar.showMessage(f"Loading small file ({file_size_string}) directly...")
                self.load_file_directly(file_path)
                
            elif file_category == FileSizeCategory.MEDIUM:
                # Threaded loading for medium files (10-50MB)
                self.logger.info("Using threaded loading strategy for medium file")
                self.status_bar.showMessage(f"Loading medium file ({file_size_string}) with progress...")
                self.load_file_threaded(file_path)
                
            elif file_category == FileSizeCategory.LARGE:
                # Threaded loading with warning for large files (50-100MB)
                self.logger.info("Using threaded loading strategy for large file with warning")
                
                # Show warning for large files
                recovery_options = {
                    'continue': f'Continue loading large file ({file_size_string})',
                    'select_different': 'Select a smaller file',
                    'cancel': 'Cancel operation'
                }
                
                choice = self.show_enhanced_error_message(
                    "Large File Warning",
                    f"This is a large IFC file ({file_size_string}). Loading may take time and use significant memory.",
                    f"File: {file_path}\nSize: {file_size_string}\n\nLarge files may cause the application to become temporarily unresponsive during loading.",
                    "warning",
                    recovery_options
                )
                
                if choice == 'continue':
                    self.status_bar.showMessage(f"Loading large file ({file_size_string}) with progress...")
                    self.load_file_threaded(file_path)
                elif choice == 'select_different':
                    self.load_ifc_file()
                    return
                else:
                    self.progress_bar.setVisible(False)
                    self.status_bar.showMessage("Large file loading cancelled")
                    return
                    
            else:  # FileSizeCategory.HUGE
                # Require explicit confirmation for huge files (> 100MB)
                self.logger.warning("Huge file detected - requiring user confirmation")
                
                recovery_options = {
                    'force_load': f'Force load huge file ({file_size_string}) - may cause issues',
                    'select_different': 'Select a smaller file',
                    'cancel': 'Cancel operation'
                }
                
                choice = self.show_enhanced_error_message(
                    "Huge File Warning",
                    f"This is an extremely large IFC file ({file_size_string}). Loading is not recommended and may cause memory issues or application freezing.",
                    f"File: {file_path}\nSize: {file_size_string}\n\nHuge files (>100MB) may:\n- Cause memory errors\n- Make the application unresponsive\n- Take very long to process\n\nConsider using a smaller file or processing the file in parts.",
                    "error",
                    recovery_options
                )
                
                if choice == 'force_load':
                    self.logger.warning(f"Force loading huge file: {file_path}")
                    self.status_bar.showMessage(f"Force loading huge file ({file_size_string})...")
                    self.load_file_threaded(file_path)
                elif choice == 'select_different':
                    self.load_ifc_file()
                    return
                else:
                    self.progress_bar.setVisible(False)
                    self.status_bar.showMessage("Huge file loading cancelled")
                    return
                
        except Exception as e:
            error_details = traceback.format_exc()
            recovery_options = {
                'retry': 'Retry loading the file',
                'select_different': 'Select a different file',
                'cancel': 'Cancel operation'
            }
            
            choice = self.show_enhanced_error_message(
                "Unexpected Error", 
                f"An unexpected error occurred while loading the file: {str(e)}",
                error_details,
                "error",
                recovery_options
            )
            
            if choice == 'retry':
                self.process_ifc_file(file_path)
            elif choice == 'select_different':
                self.load_ifc_file()
            
            self.status_bar.showMessage("Error loading file")
        
        finally:
            self.progress_bar.setVisible(False)
    
    def load_file_directly(self, file_path: str):
        """
        Load small files directly without threading to avoid overhead.
        
        Args:
            file_path: Path to the IFC file
        """
        try:
            self.logger.info(f"Loading file directly: {file_path}")
            
            # Load the file synchronously
            success, load_message = self.ifc_reader.load_file(file_path)
            
            if success:
                self.current_file_path = file_path
                self.update_file_info()
                self.update_ui_state(True)  # Enable file-related actions
                self.status_bar.showMessage("File loaded successfully. Extracting spaces...")
                
                # Extract spaces directly (synchronously) for small files
                self.logger.info("Extracting spaces directly for small file")
                result = self.extract_spaces_internal()
                
                if result is not None:
                    self.finalize_space_extraction()
                    self.ifc_file_loaded.emit(file_path)
                    self.status_bar.showMessage(f"✅ Small file loaded successfully with {len(self.spaces)} spaces")
                else:
                    self.status_bar.showMessage("❌ Error extracting spaces from file")
                    
            else:
                # Handle load failure with recovery options
                if not self.handle_file_operation_error("load IFC file", file_path, Exception(load_message)):
                    self.status_bar.showMessage("File loading cancelled")
                    self.update_ui_state(False)
                    
        except Exception as e:
            self.logger.error(f"Error in direct file loading: {e}")
            error_details = traceback.format_exc()
            
            recovery_options = {
                'retry_threaded': 'Retry with threaded loading',
                'select_different': 'Select a different file',
                'cancel': 'Cancel operation'
            }
            
            choice = self.show_enhanced_error_message(
                "Direct Loading Error", 
                f"Error loading file directly: {str(e)}",
                error_details,
                "error",
                recovery_options
            )
            
            if choice == 'retry_threaded':
                self.logger.info("Falling back to threaded loading")
                self.load_file_threaded(file_path)
            elif choice == 'select_different':
                self.load_ifc_file()
            else:
                self.status_bar.showMessage("Direct loading cancelled")
                self.update_ui_state(False)
        
        finally:
            self.progress_bar.setVisible(False)
    
    def load_file_threaded(self, file_path: str):
        """
        Load medium/large files using threaded approach with progress indication.
        
        Args:
            file_path: Path to the IFC file
        """
        try:
            self.logger.info(f"Loading file with threading: {file_path}")
            
            # Store file path for timeout calculation
            self.current_file_path = file_path
            
            # Load the file
            success, load_message = self.ifc_reader.load_file(file_path)
            
            if success:
                self.update_file_info()
                self.update_ui_state(True)  # Enable file-related actions
                self.status_bar.showMessage("File loaded successfully. Extracting spaces...")
                
                # Extract spaces using threaded operation for larger files
                self.extract_spaces_threaded()
                
                self.ifc_file_loaded.emit(file_path)
            else:
                # Handle load failure with recovery options
                if not self.handle_file_operation_error("load IFC file", file_path, Exception(load_message)):
                    self.status_bar.showMessage("File loading cancelled")
                    self.update_ui_state(False)
                    
        except Exception as e:
            self.logger.error(f"Error in threaded file loading: {e}")
            error_details = traceback.format_exc()
            
            recovery_options = {
                'retry_direct': 'Retry with direct loading (may freeze)',
                'select_different': 'Select a different file',
                'cancel': 'Cancel operation'
            }
            
            choice = self.show_enhanced_error_message(
                "Threaded Loading Error", 
                f"Error loading file with threading: {str(e)}",
                error_details,
                "error",
                recovery_options
            )
            
            if choice == 'retry_direct':
                self.logger.info("Falling back to direct loading")
                self.load_file_directly(file_path)
            elif choice == 'select_different':
                self.load_ifc_file()
            else:
                self.status_bar.showMessage("Threaded loading cancelled")
                self.update_ui_state(False)
        
        finally:
            self.progress_bar.setVisible(False)
    
    def update_file_info(self):
        """Update the UI with information about the loaded file."""
        if not self.ifc_reader.is_loaded() or not self.current_file_path:
            self.file_label.setText("No IFC file loaded")
            self.welcome_label.setText("Welcome to IFC Room Schedule\n\nSelect an IFC file to begin analyzing spaces...")
            self.main_splitter.setVisible(False)
            self.welcome_label.setVisible(True)
            self.update_ui_state(False)
            return
        
        # Update file path display
        file_name = os.path.basename(self.current_file_path)
        file_size = self.get_file_size_string(self.current_file_path)
        self.file_label.setText(f"📄 {file_name} ({file_size})")
        self.update_ui_state(True)
        
    def get_file_size_string(self, file_path: str) -> str:
        """Get human-readable file size string."""
        try:
            size_bytes = os.path.getsize(file_path)
            if size_bytes < 1024:
                return f"{size_bytes} B"
            elif size_bytes < 1024 * 1024:
                return f"{size_bytes / 1024:.1f} KB"
            else:
                return f"{size_bytes / (1024 * 1024):.1f} MB"
        except:
            return "Unknown size"
        
    def extract_spaces(self):
        """Extract spaces - public method for tests and direct calls."""
        return self.extract_spaces_internal()
    
    def extract_spaces_threaded(self):
        """Extract spaces using threaded operation for better UI responsiveness."""
        # In test mode, call extract_spaces directly for synchronous behavior
        if hasattr(self, '_testing_mode') and self._testing_mode:
            try:
                result = self.extract_spaces_internal()
                self.finalize_space_extraction()
                return result
            except Exception as e:
                self.show_enhanced_error_message(
                    "Space Extraction Error", 
                    f"Error extracting spaces from IFC file: {str(e)}",
                    traceback.format_exc(),
                    "error"
                )
                return None
        
        def extraction_operation():
            return self.extract_spaces_internal()
        
        # Show progress dialog for space extraction
        self.show_operation_progress("Extracting Spaces", extraction_operation)
    
    def extract_spaces_internal(self):
        """Internal method for extracting spaces with comprehensive error handling."""
        try:
            # Set the IFC file for the extractors
            self.space_extractor.set_ifc_file(self.ifc_reader.get_ifc_file())
            self.surface_extractor.set_ifc_file(self.ifc_reader.get_ifc_file())
            self.boundary_parser.set_ifc_file(self.ifc_reader.get_ifc_file())
            self.relationship_parser.set_ifc_file(self.ifc_reader.get_ifc_file())
            
            # Extract spaces
            self.spaces = self.space_extractor.extract_spaces()
            
            if self.spaces:
                # Extract surfaces, boundaries, and relationships for each space
                self.extract_surfaces_for_spaces_with_error_handling()
                self.extract_boundaries_for_spaces_with_error_handling()
                self.extract_relationships_for_spaces_with_error_handling()
                
                # Load spaces into the list widget (must be done in main thread)
                if hasattr(self, '_testing_mode') and self._testing_mode:
                    # In test mode, call directly to avoid timing issues
                    self.finalize_space_extraction()
                else:
                    # In normal mode, use QTimer to ensure main thread execution
                    QTimer.singleShot(0, lambda: self.finalize_space_extraction())
                
                return f"Successfully extracted {len(self.spaces)} spaces"
            else:
                if hasattr(self, '_testing_mode') and self._testing_mode:
                    # In test mode, call directly
                    self.show_enhanced_error_message(
                        "No Spaces Found", 
                        "No spaces were found in the IFC file. The file may not contain space data.",
                        "",
                        "info"
                    )
                else:
                    # In normal mode, use QTimer
                    QTimer.singleShot(0, lambda: self.show_enhanced_error_message(
                        "No Spaces Found", 
                        "No spaces were found in the IFC file. The file may not contain space data.",
                        "",
                        "info"
                    ))
                return "No spaces found in file"
                
        except Exception as e:
            error_details = traceback.format_exc()
            if hasattr(self, '_testing_mode') and self._testing_mode:
                # In test mode, call directly
                self.show_enhanced_error_message(
                    "Space Extraction Error", 
                    f"Error extracting spaces from IFC file: {str(e)}",
                    error_details,
                    "error"
                )
            else:
                # In normal mode, use QTimer
                QTimer.singleShot(0, lambda: self.show_enhanced_error_message(
                    "Space Extraction Error", 
                    f"Error extracting spaces from IFC file: {str(e)}",
                    error_details,
                    "error"
                ))
            raise e
    
    def finalize_space_extraction(self):
        """Finalize space extraction in the main thread."""
        try:
            # Load spaces into the list widget
            self.space_list_widget.load_spaces(self.spaces)
            
            # Show the main interface
            self.main_splitter.setVisible(True)
            self.welcome_label.setVisible(False)
            
            # Update UI state with spaces loaded
            self.update_ui_state(True)
            
            total_surfaces = sum(len(space.surfaces) for space in self.spaces)
            total_boundaries = sum(len(getattr(space, 'space_boundaries', [])) for space in self.spaces)
            self.status_bar.showMessage(f"Successfully loaded {len(self.spaces)} spaces with {total_surfaces} surfaces and {total_boundaries} boundaries")
            self.status_bar.setStyleSheet("QStatusBar { color: #28a745; }")
            QTimer.singleShot(5000, self.clear_temporary_error_status)
            
        except Exception as e:
            self.show_enhanced_error_message(
                "UI Update Error",
                f"Error updating interface after space extraction: {str(e)}",
                traceback.format_exc(),
                "error"
            )
    
    def extract_surfaces_for_spaces_with_error_handling(self):
        """Extract surface data for all loaded spaces with comprehensive error handling."""
        failed_spaces = []
        skipped_spaces = []
        
        try:
            for i, space in enumerate(self.spaces):
                try:
                    # Update progress
                    self.logger.info(f"Extracting surfaces for space {i+1}/{len(self.spaces)}: {space.number}")
                    
                    # Extract surfaces for this space
                    surfaces = self.surface_extractor.extract_surfaces_for_space(space.guid)
                    
                    # Add surfaces to the space
                    for surface in surfaces:
                        space.add_surface(surface)
                    
                    # Validate surfaces
                    if surfaces:
                        is_valid, messages = self.surface_extractor.validate_surfaces(surfaces)
                        if not is_valid:
                            self.logger.warning(f"Surface validation issues for space {space.guid}: {messages}")
                    
                except Exception as e:
                    self.logger.error(f"Error extracting surfaces for space {space.guid}: {e}")
                    failed_spaces.append((space.guid, str(e)))
                    
                    # Ask user how to handle this error
                    should_continue = self.handle_parsing_error(
                        "Surface Extractor", 
                        space.guid, 
                        e
                    )
                    
                    if not should_continue:
                        break
                    
                    # Continue with other spaces
                    continue
                    
        except Exception as e:
            self.logger.error(f"Critical error in surface extraction process: {e}")
            raise
        
        # Report summary of extraction issues
        if failed_spaces or skipped_spaces:
            self.report_extraction_issues("Surface Extraction", failed_spaces, skipped_spaces)
    
    def extract_boundaries_for_spaces_with_error_handling(self):
        """Extract space boundary data for all loaded spaces with comprehensive error handling."""
        failed_spaces = []
        skipped_spaces = []
        
        try:
            for i, space in enumerate(self.spaces):
                try:
                    # Update progress
                    self.logger.info(f"Extracting boundaries for space {i+1}/{len(self.spaces)}: {space.number}")
                    
                    # Extract space boundaries for this space
                    boundaries = self.boundary_parser.extract_space_boundaries(space.guid)
                    
                    # Add boundaries to the space
                    for boundary in boundaries:
                        space.add_space_boundary(boundary)
                    
                    # Validate boundaries
                    if boundaries:
                        is_valid, messages = self.boundary_parser.validate_boundaries(boundaries)
                        if not is_valid:
                            self.logger.warning(f"Boundary validation issues for space {space.guid}: {messages}")
                    
                except Exception as e:
                    self.logger.error(f"Error extracting boundaries for space {space.guid}: {e}")
                    failed_spaces.append((space.guid, str(e)))
                    
                    # Ask user how to handle this error
                    should_continue = self.handle_parsing_error(
                        "Boundary Parser", 
                        space.guid, 
                        e
                    )
                    
                    if not should_continue:
                        break
                    
                    # Continue with other spaces
                    continue
                    
        except Exception as e:
            self.logger.error(f"Critical error in boundary extraction process: {e}")
            raise
        
        # Report summary of extraction issues
        if failed_spaces or skipped_spaces:
            self.report_extraction_issues("Boundary Extraction", failed_spaces, skipped_spaces)
    
    def extract_relationships_for_spaces_with_error_handling(self):
        """Extract relationship data for all loaded spaces with comprehensive error handling."""
        failed_spaces = []
        skipped_spaces = []
        
        try:
            for i, space in enumerate(self.spaces):
                try:
                    # Update progress
                    self.logger.info(f"Extracting relationships for space {i+1}/{len(self.spaces)}: {space.number}")
                    
                    # Extract relationships for this space
                    relationships = self.relationship_parser.get_space_relationships(space.guid)
                    
                    # Add relationships to the space
                    for relationship in relationships:
                        space.add_relationship(relationship)
                    
                    # Log relationship summary
                    if relationships:
                        summary = self.relationship_parser.get_relationship_summary(space.guid)
                        self.logger.info(f"Found {len(relationships)} relationships for space {space.guid}: {summary}")
                    
                except Exception as e:
                    self.logger.error(f"Error extracting relationships for space {space.guid}: {e}")
                    failed_spaces.append((space.guid, str(e)))
                    
                    # Ask user how to handle this error
                    should_continue = self.handle_parsing_error(
                        "Relationship Parser", 
                        space.guid, 
                        e
                    )
                    
                    if not should_continue:
                        break
                    
                    # Continue with other spaces
                    continue
                    
        except Exception as e:
            self.logger.error(f"Critical error in relationship extraction process: {e}")
            raise
        
        # Report summary of extraction issues
        if failed_spaces or skipped_spaces:
            self.report_extraction_issues("Relationship Extraction", failed_spaces, skipped_spaces)
    
    def report_extraction_issues(self, operation_name: str, failed_spaces: list, skipped_spaces: list):
        """Report summary of extraction issues to the user."""
        if not failed_spaces and not skipped_spaces:
            return
        
        issue_summary = []
        if failed_spaces:
            issue_summary.append(f"Failed to process {len(failed_spaces)} spaces")
        if skipped_spaces:
            issue_summary.append(f"Skipped {len(skipped_spaces)} spaces")
        
        details = []
        if failed_spaces:
            details.append("Failed spaces:")
            for space_guid, error in failed_spaces[:10]:  # Limit to first 10
                details.append(f"  - {space_guid}: {error}")
            if len(failed_spaces) > 10:
                details.append(f"  ... and {len(failed_spaces) - 10} more")
        
        if skipped_spaces:
            details.append("Skipped spaces:")
            for space_guid, reason in skipped_spaces[:10]:  # Limit to first 10
                details.append(f"  - {space_guid}: {reason}")
            if len(skipped_spaces) > 10:
                details.append(f"  ... and {len(skipped_spaces) - 10} more")
        
        self.show_enhanced_error_message(
            f"{operation_name} Issues",
            f"{operation_name} completed with issues: {', '.join(issue_summary)}",
            '\n'.join(details),
            "warning"
        )

    def close_file(self):
        """Close the currently loaded IFC file."""
        if self.ifc_reader.is_loaded():
            self.ifc_reader.close_file()
            self.current_file_path = None
            self.spaces = []
            
            # Clear parser caches
            self.relationship_parser.clear_cache()
            
            # Clear UI
            self.space_list_widget.load_spaces([])
            self.space_detail_widget.clear_selection()
            
            self.update_file_info()
            self.status_bar.showMessage("File closed")
    
    def show_error_message(self, title: str, message: str):
        """Show an error message dialog (legacy method - use show_enhanced_error_message for new code)."""
        self.show_enhanced_error_message(title, message, "", "error")
    
    def show_info_message(self, title: str, message: str):
        """Show an information message dialog (legacy method - use show_enhanced_error_message for new code)."""
        self.show_enhanced_error_message(title, message, "", "info")
    
    def get_ifc_reader(self) -> IfcFileReader:
        """Get the IFC file reader instance."""
        return self.ifc_reader
        
    def get_space_extractor(self) -> IfcSpaceExtractor:
        """Get the space extractor instance."""
        return self.space_extractor
        
    def get_boundary_parser(self) -> IfcSpaceBoundaryParser:
        """Get the space boundary parser instance."""
        return self.boundary_parser
        
    def on_space_selected(self, space_guid: str):
        """Handle space selection from the space list."""
        # Find the space by GUID
        selected_space = None
        for space in self.spaces:
            if space.guid == space_guid:
                selected_space = space
                break
                
        if selected_space:
            # Display space details
            self.space_detail_widget.display_space(selected_space)
            
            # Set space context in surface editor and show empty state
            self.surface_editor_widget.set_space_context(selected_space.guid)
            self.surface_editor_widget.show_empty_state()
            
            self.status_bar.showMessage(f"Selected space: {selected_space.number} - {selected_space.name}")
        else:
            self.status_bar.showMessage("Space not found")
            
    def on_spaces_loaded(self, count: int):
        """Handle spaces loaded event."""
        if count > 0:
            self.status_bar.showMessage(f"Loaded {count} spaces")
        else:
            self.status_bar.showMessage("No spaces loaded")
            
    def on_surface_selected(self, surface_id: str):
        """Handle surface selection from space details."""
        self.status_bar.showMessage(f"Selected surface: {surface_id}")
        
        # Find the surface data
        current_space = self.space_detail_widget.get_current_space()
        if current_space:
            for surface in current_space.surfaces:
                if surface.id == surface_id:
                    # Prepare surface data for editor
                    surface_data = {
                        'type': surface.type,
                        'area': surface.area,
                        'material': surface.material,
                        'user_description': surface.user_description
                    }
                    
                    # Set space context and start editing
                    self.surface_editor_widget.set_space_context(current_space.guid)
                    self.surface_editor_widget.edit_surface(surface_id, surface_data)
                    break
        
    def on_boundary_selected(self, boundary_guid: str):
        """Handle space boundary selection from space details."""
        self.status_bar.showMessage(f"Selected boundary: {boundary_guid}")
        
        # Find the boundary data
        current_space = self.space_detail_widget.get_current_space()
        if current_space and hasattr(current_space, 'space_boundaries'):
            for boundary in current_space.space_boundaries:
                if boundary.guid == boundary_guid:
                    # Prepare boundary data for editor
                    boundary_data = {
                        'display_label': boundary.display_label,
                        'physical_or_virtual_boundary': boundary.physical_or_virtual_boundary,
                        'boundary_orientation': boundary.boundary_orientation,
                        'calculated_area': boundary.calculated_area,
                        'related_building_element_type': boundary.related_building_element_type,
                        'user_description': boundary.user_description
                    }
                    
                    # Set space context and start editing
                    self.surface_editor_widget.set_space_context(current_space.guid)
                    self.surface_editor_widget.edit_boundary(boundary_guid, boundary_data)
                    break
                    
    def on_surface_description_changed(self, surface_id: str, description: str):
        """Handle surface description changes from the editor."""
        # Find and update the surface
        current_space = self.space_detail_widget.get_current_space()
        if current_space:
            for surface in current_space.surfaces:
                if surface.id == surface_id:
                    surface.user_description = description
                    # Mark space as processed
                    current_space.processed = True
                    # Refresh the space details view
                    self.space_detail_widget.update_surfaces_tab()
                    self.logger.info(f"Updated surface description for {surface_id}")
                    break
                    
    def on_boundary_description_changed(self, boundary_guid: str, description: str):
        """Handle boundary description changes from the editor."""
        # Find and update the boundary
        current_space = self.space_detail_widget.get_current_space()
        if current_space and hasattr(current_space, 'space_boundaries'):
            for boundary in current_space.space_boundaries:
                if boundary.guid == boundary_guid:
                    boundary.user_description = description
                    # Mark space as processed
                    current_space.processed = True
                    # Refresh the space details view
                    self.space_detail_widget.update_boundaries_tab()
                    self.logger.info(f"Updated boundary description for {boundary_guid}")
                    break
        
    def get_current_spaces(self):
        """Get the currently loaded spaces."""
        return self.spaces
        
    def refresh_view(self):
        """Refresh the current view."""
        if self.ifc_reader.is_loaded():
            # Refresh space list
            self.space_list_widget.refresh_spaces()
            
            # Refresh current space details if one is selected
            current_space = self.space_list_widget.get_selected_space()
            if current_space:
                self.space_detail_widget.display_space(current_space)
                
            self.status_bar.showMessage("View refreshed")
        else:
            self.status_bar.showMessage("No file loaded to refresh")
            
    def toggle_spaces_panel(self, checked: bool):
        """Toggle the visibility of the spaces panel."""
        self.space_list_widget.setVisible(checked)
        if checked:
            self.status_bar.showMessage("Spaces panel shown")
        else:
            self.status_bar.showMessage("Spaces panel hidden")
            
    def show_about(self):
        """Show the about dialog."""
        about_text = """
        <h3>IFC Room Schedule Application</h3>
        <p>Version 1.0</p>
        <p>A desktop application for importing IFC files, analyzing spatial data, 
        and generating structured room schedules.</p>
        <p>Built with Python and PyQt6</p>
        <p>Uses IfcOpenShell for IFC file processing</p>
        """
        
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.setWindowTitle("About IFC Room Schedule")
        msg_box.setText(about_text)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.exec()
        
    def navigate_next_space(self):
        """Navigate to the next space in the list."""
        if not self.spaces:
            return
            
        current_guid = self.space_list_widget.get_selected_space_guid()
        if not current_guid:
            # Select first space if none selected
            if self.spaces:
                self.space_list_widget.select_space_by_index(0)
            return
            
        # Find current space index
        current_index = -1
        for i, space in enumerate(self.spaces):
            if space.guid == current_guid:
                current_index = i
                break
                
        # Navigate to next space
        if current_index >= 0 and current_index < len(self.spaces) - 1:
            self.space_list_widget.select_space_by_index(current_index + 1)
            self.status_bar.showMessage(f"Navigated to next space")
        else:
            self.status_bar.showMessage("Already at last space")
            
    def navigate_previous_space(self):
        """Navigate to the previous space in the list."""
        if not self.spaces:
            return
            
        current_guid = self.space_list_widget.get_selected_space_guid()
        if not current_guid:
            # Select last space if none selected
            if self.spaces:
                self.space_list_widget.select_space_by_index(len(self.spaces) - 1)
            return
            
        # Find current space index
        current_index = -1
        for i, space in enumerate(self.spaces):
            if space.guid == current_guid:
                current_index = i
                break
                
        # Navigate to previous space
        if current_index > 0:
            self.space_list_widget.select_space_by_index(current_index - 1)
            self.status_bar.showMessage(f"Navigated to previous space")
        else:
            self.status_bar.showMessage("Already at first space")
            
    def show_goto_space_dialog(self):
        """Show dialog to go to a specific space."""
        from PyQt6.QtWidgets import QInputDialog
        
        if not self.spaces:
            self.show_info_message("No Spaces", "No spaces are currently loaded.")
            return
            
        # Create list of space identifiers
        space_options = []
        for space in self.spaces:
            identifier = f"{space.number} - {space.name}" if space.name != space.number else space.number
            space_options.append(identifier)
            
        # Show selection dialog
        item, ok = QInputDialog.getItem(
            self, 
            "Go to Space", 
            "Select a space to navigate to:",
            space_options,
            0,
            False
        )
        
        if ok and item:
            # Find the selected space
            selected_index = space_options.index(item)
            self.space_list_widget.select_space_by_index(selected_index)
            self.status_bar.showMessage(f"Navigated to space: {item}")
            
    def validate_data(self):
        """Validate current space data for completeness."""
        if not self.spaces:
            self.show_info_message("No Data", "No spaces are currently loaded to validate.")
            return
            
        # Perform validation checks
        validation_results = []
        total_spaces = len(self.spaces)
        spaces_with_surfaces = 0
        spaces_with_boundaries = 0
        spaces_with_descriptions = 0
        
        for space in self.spaces:
            if space.surfaces:
                spaces_with_surfaces += 1
            if hasattr(space, 'space_boundaries') and space.space_boundaries:
                spaces_with_boundaries += 1
            if any(surface.user_description for surface in space.surfaces):
                spaces_with_descriptions += 1
                
        # Generate validation report
        validation_results.append(f"Total Spaces: {total_spaces}")
        validation_results.append(f"Spaces with Surfaces: {spaces_with_surfaces}")
        validation_results.append(f"Spaces with Boundaries: {spaces_with_boundaries}")
        validation_results.append(f"Spaces with Descriptions: {spaces_with_descriptions}")
        
        # Calculate completeness percentage
        completeness = (spaces_with_descriptions / total_spaces * 100) if total_spaces > 0 else 0
        validation_results.append(f"\nData Completeness: {completeness:.1f}%")
        
        # Show validation results
        self.show_info_message("Data Validation Results", "\n".join(validation_results))
        
    def export_json(self):
        """Export space data to JSON file with enhanced error handling."""
        if not self.spaces:
            self.show_enhanced_error_message(
                "No Data", 
                "No space data available for export. Please load an IFC file first.",
                "",
                "warning"
            )
            return
        
        try:
            # Create and show export dialog
            export_dialog = ExportDialogWidget(
                spaces=self.spaces,
                source_file_path=self.current_file_path,
                parent=self
            )
            
            # Connect export completion signal
            export_dialog.export_completed.connect(self.on_export_completed)
            
            # Show dialog
            export_dialog.exec()
            
        except Exception as e:
            error_details = traceback.format_exc()
            self.show_enhanced_error_message(
                "Export Dialog Error",
                f"Failed to open export dialog: {str(e)}",
                error_details,
                "error"
            )
    
    def on_export_completed(self, success: bool, message: str):
        """Handle export completion from export dialog."""
        if success:
            self.status_bar.showMessage(f"Export completed: {message}")
        else:
            self.status_bar.showMessage(f"Export failed: {message}")
        
    def show_user_guide(self):
        """Show the user guide."""
        guide_text = """
        <h3>IFC Room Schedule - User Guide</h3>
        
        <h4>Getting Started:</h4>
        <ol>
        <li><b>Load IFC File:</b> Use File → Open IFC File or click the Load button</li>
        <li><b>Navigate Spaces:</b> Select spaces from the left panel or use navigation buttons</li>
        <li><b>View Details:</b> Space properties, surfaces, and boundaries appear in the right panel</li>
        <li><b>Add Descriptions:</b> Click on surfaces or boundaries to add custom descriptions</li>
        <li><b>Export Data:</b> Use Tools → Export to save your work</li>
        </ol>
        
        <h4>Keyboard Shortcuts:</h4>
        <ul>
        <li><b>Ctrl+O:</b> Open IFC file</li>
        <li><b>Ctrl+W:</b> Close current file</li>
        <li><b>F5:</b> Refresh view</li>
        <li><b>Ctrl+Left/Right:</b> Navigate between spaces</li>
        <li><b>Ctrl+G:</b> Go to specific space</li>
        <li><b>Ctrl+E:</b> Export data</li>
        </ul>
        
        <h4>Tips:</h4>
        <ul>
        <li>Use the search box to filter spaces by name or type</li>
        <li>Validate your data before exporting to ensure completeness</li>
        <li>Space boundaries provide detailed geometric information</li>
        </ul>
        """
        
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.setWindowTitle("User Guide")
        msg_box.setText(guide_text)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.exec()
        
    def update_ui_state(self, file_loaded: bool):
        """Update UI state based on whether a file is loaded."""
        has_spaces = file_loaded and len(self.spaces) > 0
        
        # Update menu actions
        self.close_action.setEnabled(file_loaded)
        self.refresh_action.setEnabled(file_loaded)
        self.export_action.setEnabled(has_spaces)
        self.next_space_action.setEnabled(has_spaces)
        self.prev_space_action.setEnabled(has_spaces)
        self.goto_space_action.setEnabled(has_spaces)
        self.validate_action.setEnabled(has_spaces)
        
        # Update toolbar actions
        self.toolbar_close_action.setEnabled(file_loaded)
        self.toolbar_refresh_action.setEnabled(file_loaded)
        self.toolbar_export_action.setEnabled(has_spaces)
        self.toolbar_next_action.setEnabled(has_spaces)
        self.toolbar_prev_action.setEnabled(has_spaces)
        self.toolbar_validate_action.setEnabled(has_spaces)
        
        # Update toolbar status
        if file_loaded:
            if has_spaces:
                self.toolbar_status_label.setText(f"{len(self.spaces)} spaces loaded")
            else:
                self.toolbar_status_label.setText("File loaded, no spaces found")
        else:
            self.toolbar_status_label.setText("Ready")
