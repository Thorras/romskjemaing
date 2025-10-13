"""
Error handler for IFC Floor Plan Generator.

Centralized error handling with structured error codes and Norwegian messages.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from .exceptions import (
    ProcessingError, 
    IFCOpenError, 
    NoStoreysFoundError, 
    EmptyCutResultError,
    GeometryShapeError, 
    WriteFailedError, 
    ConfigurationError
)


class ErrorHandler:
    """Centralized error handling with structured error codes and Norwegian messages."""
    
    def __init__(self, errors_json_path: Optional[str] = None):
        """Initialize error handler.
        
        Args:
            errors_json_path: Path to errors.json file. If None, uses default location.
        """
        self._error_messages: Dict[str, Dict[str, Any]] = {}
        self._warning_messages: Dict[str, Dict[str, Any]] = {}
        self._logger = logging.getLogger(__name__)
        
        # Load error messages from JSON file
        if errors_json_path is None:
            errors_json_path = Path(__file__).parent / "errors.json"
        
        self.load_error_messages(str(errors_json_path))
    
    def load_error_messages(self, errors_json_path: str) -> None:
        """Load error messages from JSON file.
        
        Args:
            errors_json_path: Path to the errors.json file
            
        Raises:
            ConfigurationError: If the errors.json file cannot be loaded
        """
        try:
            with open(errors_json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self._error_messages = data.get('error_messages', {})
            self._warning_messages = data.get('warning_messages', {})
            
            self._logger.info(f"Loaded {len(self._error_messages)} error messages and {len(self._warning_messages)} warning messages")
            
        except FileNotFoundError:
            raise ConfigurationError(f"Finner ikke errors.json fil: {errors_json_path}")
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Ugyldig JSON i errors.json: {e}")
        except Exception as e:
            raise ConfigurationError(f"Kunne ikke laste error messages: {e}")
    
    def handle_error(self, error_code: str, context: Optional[Dict[str, Any]] = None) -> ProcessingError:
        """Handle error with structured error code and context.
        
        Args:
            error_code: The structured error code
            context: Additional context information for the error
            
        Returns:
            ProcessingError: The appropriate exception instance
        """
        context = context or {}
        
        # Get the error message template
        message = self.get_error_message(error_code)
        
        # Format the message with context
        try:
            formatted_message = message.format(**context)
        except KeyError as e:
            # If formatting fails, use the template as-is and log the issue
            formatted_message = message
            self._logger.warning(f"Could not format error message for {error_code}: missing key {e}")
        
        # Create specific exception types based on error code
        if error_code == "IFC_OPEN_FAILED":
            return IFCOpenError(
                file_path=context.get('file_path', 'unknown'),
                original_error=context.get('original_error')
            )
        elif error_code == "NO_STOREYS_FOUND":
            return NoStoreysFoundError(
                file_path=context.get('file_path', 'unknown')
            )
        elif error_code == "EMPTY_CUT_RESULT":
            return EmptyCutResultError(
                storey_name=context.get('storey_name', 'unknown'),
                cut_height=context.get('cut_height', 0.0)
            )
        elif error_code == "GEOMETRY_SHAPE_FAILED":
            return GeometryShapeError(
                element_guid=context.get('element_guid', 'unknown'),
                ifc_class=context.get('ifc_class', 'unknown'),
                original_error=context.get('original_error')
            )
        elif error_code == "WRITE_FAILED":
            return WriteFailedError(
                file_path=context.get('file_path', 'unknown'),
                original_error=context.get('original_error')
            )
        else:
            # Generic ProcessingError for other error codes
            return ProcessingError(
                error_code=error_code,
                message=formatted_message,
                context=context
            )
    
    def get_error_message(self, error_code: str) -> str:
        """Get localized error message for error code.
        
        Args:
            error_code: The structured error code
            
        Returns:
            str: The localized error message
        """
        error_info = self._error_messages.get(error_code)
        if error_info:
            return error_info.get('message', f'Ukjent feil: {error_code}')
        else:
            return f'Ukjent feilkode: {error_code}'
    
    def get_error_description(self, error_code: str) -> str:
        """Get detailed description for error code.
        
        Args:
            error_code: The structured error code
            
        Returns:
            str: The error description
        """
        error_info = self._error_messages.get(error_code)
        if error_info:
            return error_info.get('description', 'Ingen beskrivelse tilgjengelig')
        else:
            return 'Ukjent feilkode'
    
    def get_suggested_actions(self, error_code: str) -> List[str]:
        """Get suggested actions for error code.
        
        Args:
            error_code: The structured error code
            
        Returns:
            List[str]: List of suggested actions
        """
        error_info = self._error_messages.get(error_code)
        if error_info:
            return error_info.get('suggested_actions', [])
        else:
            return []
    
    def format_error_details(self, error_code: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Format complete error details including message, description, and suggested actions.
        
        Args:
            error_code: The structured error code
            context: Additional context information
            
        Returns:
            Dict containing formatted error details
        """
        context = context or {}
        
        # Format the message with context, handling missing keys gracefully
        message_template = self.get_error_message(error_code)
        try:
            formatted_message = message_template.format(**context)
        except KeyError:
            # If formatting fails, use the template as-is
            formatted_message = message_template
        
        return {
            'error_code': error_code,
            'message': formatted_message,
            'description': self.get_error_description(error_code),
            'suggested_actions': self.get_suggested_actions(error_code),
            'context': context
        }
    
    def log_warning(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Log warning with contextual information.
        
        Args:
            message: Warning message
            context: Additional context information
        """
        context = context or {}
        
        # Create structured log entry
        log_data = {
            'message': message,
            'context': context
        }
        
        # Log with structured data
        self._logger.warning(message, extra={'warning_context': context})
    
    def log_error(self, error_code: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Log error with structured information.
        
        Args:
            error_code: The structured error code
            context: Additional context information
        """
        context = context or {}
        error_details = self.format_error_details(error_code, context)
        
        # Log with structured data
        self._logger.error(
            f"[{error_code}] {error_details['message']}", 
            extra={
                'error_code': error_code,
                'error_context': context,
                'suggested_actions': error_details['suggested_actions']
            }
        )
    
    def log_info(self, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Log informational message with context.
        
        Args:
            message: Info message
            context: Additional context information
        """
        context = context or {}
        self._logger.info(message, extra={'info_context': context})
    
    def setup_logging(self, log_level: str = "INFO", log_file: Optional[str] = None) -> None:
        """Set up structured logging configuration.
        
        Args:
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Optional log file path. If None, logs to console only.
        """
        # Create formatter for structured logging
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Set up console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, log_level.upper()))
        root_logger.addHandler(console_handler)
        
        # Add file handler if specified
        if log_file:
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
    
    def handle_recoverable_error(self, error_code: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """Handle recoverable errors with graceful degradation.
        
        Args:
            error_code: The structured error code
            context: Additional context information
            
        Returns:
            bool: True if error was handled and processing can continue, False otherwise
        """
        context = context or {}
        
        # Define which errors are recoverable
        recoverable_errors = {
            "GEOMETRY_SHAPE_FAILED": self._handle_geometry_failure,
            "EMPTY_CUT_RESULT": self._handle_empty_cut,
            "ELEMENT_SKIPPED": self._handle_element_skip,
            "CACHE_ERROR": self._handle_cache_error,
            "UNITS_DETECTION_FAILED": self._handle_units_fallback
        }
        
        if error_code in recoverable_errors:
            try:
                return recoverable_errors[error_code](context)
            except Exception as e:
                self.log_error("RECOVERY_FAILED", {
                    "original_error_code": error_code,
                    "recovery_error": str(e),
                    "context": context
                })
                return False
        else:
            # Non-recoverable error
            self.log_error(error_code, context)
            return False
    
    def _handle_geometry_failure(self, context: Dict[str, Any]) -> bool:
        """Handle geometry generation failure by skipping the element.
        
        Args:
            context: Error context containing element information
            
        Returns:
            bool: True (element skipped, processing continues)
        """
        element_guid = context.get('element_guid', 'unknown')
        ifc_class = context.get('ifc_class', 'unknown')
        
        self.log_warning(
            f"Hoppet over element {element_guid} ({ifc_class}) på grunn av geometri-feil",
            context
        )
        return True
    
    def _handle_empty_cut(self, context: Dict[str, Any]) -> bool:
        """Handle empty cut result by logging warning and continuing.
        
        Args:
            context: Error context containing storey information
            
        Returns:
            bool: True (storey skipped, processing continues)
        """
        storey_name = context.get('storey_name', 'unknown')
        cut_height = context.get('cut_height', 0.0)
        
        self.log_warning(
            f"Tomt snitt for etasje '{storey_name}' på høyde {cut_height}m",
            context
        )
        return True
    
    def _handle_element_skip(self, context: Dict[str, Any]) -> bool:
        """Handle element skip by logging and continuing.
        
        Args:
            context: Error context containing element information
            
        Returns:
            bool: True (element skipped, processing continues)
        """
        element_guid = context.get('element_guid', 'unknown')
        reason = context.get('reason', 'ukjent årsak')
        
        self.log_warning(f"Hoppet over element {element_guid}: {reason}", context)
        return True
    
    def _handle_cache_error(self, context: Dict[str, Any]) -> bool:
        """Handle cache error by disabling cache and continuing.
        
        Args:
            context: Error context containing cache information
            
        Returns:
            bool: True (cache disabled, processing continues)
        """
        self.log_warning("Cache-feil, fortsetter uten cache", context)
        return True
    
    def _handle_units_fallback(self, context: Dict[str, Any]) -> bool:
        """Handle units detection failure by using fallback scale.
        
        Args:
            context: Error context containing units information
            
        Returns:
            bool: True (fallback used, processing continues)
        """
        fallback_scale = context.get('fallback_scale', 1.0)
        self.log_warning(f"Bruker fallback enhets-skalering: {fallback_scale}", context)
        return True