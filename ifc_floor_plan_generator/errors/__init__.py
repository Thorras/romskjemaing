"""
Error handling module for IFC Floor Plan Generator.

Provides centralized error handling with structured error codes and Norwegian messages.
"""

from .handler import ErrorHandler
from .exceptions import (
    ProcessingError,
    IFCOpenError,
    NoStoreysFoundError,
    EmptyCutResultError,
    GeometryShapeError,
    WriteFailedError,
    ConfigurationError,
    UnitsDetectionError,
    MultiprocessingError,
    CacheError,
    ToleranceError,
    ValidationError
)

__all__ = [
    "ErrorHandler",
    "ProcessingError",
    "IFCOpenError",
    "NoStoreysFoundError", 
    "EmptyCutResultError",
    "GeometryShapeError",
    "WriteFailedError",
    "ConfigurationError",
    "UnitsDetectionError",
    "MultiprocessingError",
    "CacheError",
    "ToleranceError",
    "ValidationError"
]