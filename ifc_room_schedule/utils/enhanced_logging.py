"""
Enhanced Logging and Error Reporting System

Provides structured logging and error reporting for debugging freeze issues
and improving user experience with detailed error messages.
"""

import logging
import sys
import time
import traceback
import psutil
import os
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from enum import Enum


class ErrorSeverity(Enum):
    """Error severity levels for structured error reporting."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Categories of errors for better classification and handling."""
    MEMORY = "memory"
    IO = "io"
    THREADING = "threading"
    TIMEOUT = "timeout"
    PARSING = "parsing"
    VALIDATION = "validation"
    SYSTEM = "system"
    USER_INPUT = "user_input"
    UNKNOWN = "unknown"


@dataclass
class OperationTiming:
    """Track timing information for operations."""
    operation_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    file_path: Optional[str] = None
    file_size_mb: Optional[float] = None
    memory_usage_mb: Optional[float] = None
    
    def finish(self):
        """Mark operation as finished and calculate duration."""
        self.end_time = datetime.now()
        self.duration_seconds = (self.end_time - self.start_time).total_seconds()


@dataclass
class ErrorReport:
    """Structured error report for debugging and user feedback."""
    error_id: str
    timestamp: datetime
    category: ErrorCategory
    severity: ErrorSeverity
    title: str
    message: str
    technical_details: str = ""
    user_guidance: str = ""
    recovery_suggestions: List[str] = field(default_factory=list)
    system_context: Dict[str, Any] = field(default_factory=dict)
    operation_context: Optional[OperationTiming] = None
    stack_trace: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error report to dictionary for logging."""
        return {
            'error_id': self.error_id,
            'timestamp': self.timestamp.isoformat(),
            'category': self.category.value,
            'severity': self.severity.value,
            'title': self.title,
            'message': self.message,
            'technical_details': self.technical_details,
            'user_guidance': self.user_guidance,
            'recovery_suggestions': self.recovery_suggestions,
            'system_context': self.system_context,
            'operation_context': self.operation_context.__dict__ if self.operation_context else None,
            'stack_trace': self.stack_trace
        }


class EnhancedLogger:
    """Enhanced logger with structured error reporting and timing capabilities."""
    
    def __init__(self, name: str = __name__):
        self.logger = logging.getLogger(name)
        self.operation_timings: Dict[str, OperationTiming] = {}
        self.error_count = 0
        self.session_start = datetime.now()
        
        # Configure structured logging format
        self._setup_logging()
    
    def _setup_logging(self):
        """Set up enhanced logging configuration."""
        # Create formatter with more detailed information
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
        )
        
        # Ensure handlers are configured
        if not self.logger.handlers:
            # File handler for persistent logging
            file_handler = logging.FileHandler('ifc_room_schedule_detailed.log')
            file_handler.setFormatter(formatter)
            file_handler.setLevel(logging.DEBUG)
            self.logger.addHandler(file_handler)
            
            # Console handler for immediate feedback
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            console_handler.setLevel(logging.INFO)
            self.logger.addHandler(console_handler)
        
        self.logger.setLevel(logging.DEBUG)
    
    def start_operation_timing(self, operation_name: str, file_path: str = None) -> str:
        """
        Start timing an operation.
        
        Args:
            operation_name: Name of the operation
            file_path: Optional file path being processed
            
        Returns:
            Operation ID for tracking
        """
        operation_id = f"{operation_name}_{int(time.time())}"
        
        # Get file size if path provided
        file_size_mb = None
        if file_path and os.path.exists(file_path):
            try:
                file_size_bytes = os.path.getsize(file_path)
                file_size_mb = file_size_bytes / (1024 * 1024)
            except OSError:
                pass
        
        # Get current memory usage
        memory_usage_mb = None
        try:
            process = psutil.Process()
            memory_usage_mb = process.memory_info().rss / (1024 * 1024)
        except:
            pass
        
        timing = OperationTiming(
            operation_name=operation_name,
            start_time=datetime.now(),
            file_path=file_path,
            file_size_mb=file_size_mb,
            memory_usage_mb=memory_usage_mb
        )
        
        self.operation_timings[operation_id] = timing
        
        # Log operation start with context
        context_info = []
        if file_size_mb:
            context_info.append(f"file_size={file_size_mb:.1f}MB")
        if memory_usage_mb:
            context_info.append(f"memory_usage={memory_usage_mb:.1f}MB")
        
        context_str = f" ({', '.join(context_info)})" if context_info else ""
        self.logger.info(f"OPERATION_START: {operation_name}{context_str}")
        
        return operation_id
    
    def finish_operation_timing(self, operation_id: str) -> Optional[OperationTiming]:
        """
        Finish timing an operation and log results.
        
        Args:
            operation_id: Operation ID from start_operation_timing
            
        Returns:
            OperationTiming object with results
        """
        if operation_id not in self.operation_timings:
            self.logger.warning(f"Unknown operation ID for timing: {operation_id}")
            return None
        
        timing = self.operation_timings[operation_id]
        timing.finish()
        
        # Log operation completion with detailed timing
        duration_str = f"{timing.duration_seconds:.2f}s"
        context_info = [f"duration={duration_str}"]
        
        if timing.file_size_mb:
            context_info.append(f"file_size={timing.file_size_mb:.1f}MB")
            # Calculate processing rate
            rate_mb_per_sec = timing.file_size_mb / timing.duration_seconds
            context_info.append(f"rate={rate_mb_per_sec:.2f}MB/s")
        
        if timing.memory_usage_mb:
            context_info.append(f"memory_usage={timing.memory_usage_mb:.1f}MB")
        
        context_str = f" ({', '.join(context_info)})"
        self.logger.info(f"OPERATION_COMPLETE: {timing.operation_name}{context_str}")
        
        # Clean up timing record
        del self.operation_timings[operation_id]
        
        return timing
    
    def get_system_context(self) -> Dict[str, Any]:
        """Get current system context for error reporting."""
        try:
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('.')
            
            return {
                'memory_total_gb': round(memory.total / (1024**3), 2),
                'memory_available_gb': round(memory.available / (1024**3), 2),
                'memory_percent_used': memory.percent,
                'disk_free_gb': round(disk.free / (1024**3), 2),
                'disk_percent_used': round((disk.used / disk.total) * 100, 1),
                'cpu_count': psutil.cpu_count(),
                'platform': sys.platform,
                'python_version': sys.version.split()[0]
            }
        except Exception as e:
            return {'error_getting_context': str(e)}
    
    def create_error_report(self, 
                          category: ErrorCategory,
                          severity: ErrorSeverity,
                          title: str,
                          message: str,
                          exception: Exception = None,
                          operation_timing: OperationTiming = None,
                          user_guidance: str = "",
                          recovery_suggestions: List[str] = None) -> ErrorReport:
        """
        Create a structured error report.
        
        Args:
            category: Error category
            severity: Error severity
            title: Error title
            message: Error message
            exception: Optional exception object
            operation_timing: Optional operation timing context
            user_guidance: User-friendly guidance
            recovery_suggestions: List of recovery suggestions
            
        Returns:
            ErrorReport object
        """
        self.error_count += 1
        error_id = f"ERR_{int(time.time())}_{self.error_count:03d}"
        
        # Get technical details from exception
        technical_details = ""
        stack_trace = ""
        if exception:
            technical_details = f"Exception: {type(exception).__name__}: {str(exception)}"
            stack_trace = traceback.format_exc()
        
        # Create error report
        report = ErrorReport(
            error_id=error_id,
            timestamp=datetime.now(),
            category=category,
            severity=severity,
            title=title,
            message=message,
            technical_details=technical_details,
            user_guidance=user_guidance,
            recovery_suggestions=recovery_suggestions or [],
            system_context=self.get_system_context(),
            operation_context=operation_timing,
            stack_trace=stack_trace
        )
        
        # Log the error report
        self._log_error_report(report)
        
        return report
    
    def _log_error_report(self, report: ErrorReport):
        """Log the error report with appropriate level."""
        # Determine log level based on severity
        if report.severity == ErrorSeverity.CRITICAL:
            log_func = self.logger.critical
        elif report.severity == ErrorSeverity.HIGH:
            log_func = self.logger.error
        elif report.severity == ErrorSeverity.MEDIUM:
            log_func = self.logger.warning
        else:
            log_func = self.logger.info
        
        # Log structured error information
        log_func(f"ERROR_REPORT: {report.error_id} - {report.title}")
        log_func(f"  Category: {report.category.value}, Severity: {report.severity.value}")
        log_func(f"  Message: {report.message}")
        
        if report.technical_details:
            log_func(f"  Technical: {report.technical_details}")
        
        if report.user_guidance:
            log_func(f"  Guidance: {report.user_guidance}")
        
        if report.recovery_suggestions:
            log_func(f"  Recovery: {', '.join(report.recovery_suggestions)}")
        
        # Log system context for debugging
        if report.system_context:
            context_items = []
            for key, value in report.system_context.items():
                if key not in ['platform', 'python_version']:  # Skip less critical info
                    context_items.append(f"{key}={value}")
            if context_items:
                self.logger.debug(f"  System: {', '.join(context_items)}")
        
        # Log operation context if available
        if report.operation_context:
            op = report.operation_context
            context_items = [f"operation={op.operation_name}"]
            if op.duration_seconds:
                context_items.append(f"duration={op.duration_seconds:.2f}s")
            if op.file_size_mb:
                context_items.append(f"file_size={op.file_size_mb:.1f}MB")
            self.logger.debug(f"  Operation: {', '.join(context_items)}")
        
        # Log stack trace for debugging (only for higher severity errors)
        if report.stack_trace and report.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            self.logger.debug(f"  Stack trace:\n{report.stack_trace}")


class MemoryErrorAnalyzer:
    """Analyzer for memory-related errors with specific guidance."""
    
    @staticmethod
    def analyze_memory_error(file_size_bytes: int, available_memory_bytes: int, 
                           exception: Exception = None) -> Tuple[str, List[str]]:
        """
        Analyze memory error and provide specific guidance.
        
        Args:
            file_size_bytes: Size of file being processed
            available_memory_bytes: Available system memory
            exception: Optional memory exception
            
        Returns:
            Tuple of (user_guidance, recovery_suggestions)
        """
        file_size_mb = file_size_bytes / (1024 * 1024)
        available_mb = available_memory_bytes / (1024 * 1024)
        
        # Analyze the memory situation
        memory_ratio = file_size_bytes / available_memory_bytes if available_memory_bytes > 0 else float('inf')
        
        # Generate specific guidance based on the situation
        if memory_ratio > 0.8:  # File uses more than 80% of available memory
            guidance = (f"The file ({file_size_mb:.1f}MB) is too large for your available memory "
                       f"({available_mb:.1f}MB). IFC processing typically requires 3-5x the file size in memory.")
            suggestions = [
                "Close other applications to free up memory",
                "Try processing the file on a system with more RAM",
                "Split the IFC file into smaller parts if possible",
                "Restart the application to clear memory leaks"
            ]
        elif memory_ratio > 0.5:  # File uses 50-80% of available memory
            guidance = (f"The file ({file_size_mb:.1f}MB) is large relative to your available memory "
                       f"({available_mb:.1f}MB). Processing may be slow or fail.")
            suggestions = [
                "Close unnecessary applications",
                "Try processing during off-peak system usage",
                "Consider upgrading system memory for large IFC files"
            ]
        elif file_size_mb > 100:  # Large file but sufficient memory
            guidance = (f"Large file ({file_size_mb:.1f}MB) encountered memory issues despite sufficient "
                       f"available memory ({available_mb:.1f}MB). This may indicate file complexity or corruption.")
            suggestions = [
                "Verify the IFC file is not corrupted",
                "Try opening the file in another IFC viewer first",
                "Check if the file has unusually complex geometry",
                "Restart the application to clear any memory fragmentation"
            ]
        else:  # Small file with memory issues
            guidance = (f"Unexpected memory error with small file ({file_size_mb:.1f}MB). "
                       f"This may indicate system issues or file corruption.")
            suggestions = [
                "Restart the application",
                "Check system memory usage in Task Manager",
                "Verify the IFC file is not corrupted",
                "Try processing a different IFC file to isolate the issue"
            ]
        
        return guidance, suggestions
    
    @staticmethod
    def get_memory_recommendations(file_size_mb: float) -> Dict[str, str]:
        """
        Get memory recommendations based on file size.
        
        Args:
            file_size_mb: File size in megabytes
            
        Returns:
            Dictionary with memory recommendations
        """
        if file_size_mb < 10:
            return {
                'recommended_ram': '4GB or more',
                'processing_time': 'Under 30 seconds',
                'memory_usage': f'~{file_size_mb * 2:.0f}MB'
            }
        elif file_size_mb < 50:
            return {
                'recommended_ram': '8GB or more',
                'processing_time': '30 seconds to 2 minutes',
                'memory_usage': f'~{file_size_mb * 3:.0f}MB'
            }
        elif file_size_mb < 100:
            return {
                'recommended_ram': '16GB or more',
                'processing_time': '2 to 5 minutes',
                'memory_usage': f'~{file_size_mb * 4:.0f}MB'
            }
        else:
            return {
                'recommended_ram': '32GB or more',
                'processing_time': '5+ minutes',
                'memory_usage': f'~{file_size_mb * 5:.0f}MB'
            }


# Global enhanced logger instance
enhanced_logger = EnhancedLogger(__name__)