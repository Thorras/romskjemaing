"""
Exception classes for IFC Floor Plan Generator.

Defines custom exceptions used throughout the system.
"""

from typing import Dict, Any, Optional


class ProcessingError(Exception):
    """Base exception for IFC floor plan processing errors."""
    
    def __init__(
        self, 
        error_code: str, 
        message: str, 
        context: Optional[Dict[str, Any]] = None
    ):
        """Initialize processing error.
        
        Args:
            error_code: Structured error code for categorization
            message: Human-readable error message
            context: Additional context information
        """
        self.error_code = error_code
        self.message = message
        self.context = context or {}
        super().__init__(f"[{error_code}] {message}")
    
    def __str__(self) -> str:
        """String representation of the error."""
        return f"[{self.error_code}] {self.message}"
    
    def __repr__(self) -> str:
        """Detailed representation of the error."""
        return f"ProcessingError(error_code='{self.error_code}', message='{self.message}', context={self.context})"


class IFCOpenError(ProcessingError):
    """Exception raised when IFC file cannot be opened."""
    
    def __init__(self, file_path: str, original_error: Optional[Exception] = None):
        context = {"file_path": file_path}
        if original_error:
            context["original_error"] = str(original_error)
        
        super().__init__(
            error_code="IFC_OPEN_FAILED",
            message=f"Kunne ikke åpne IFC-fil: {file_path}",
            context=context
        )


class NoStoreysFoundError(ProcessingError):
    """Exception raised when no IfcBuildingStorey elements are found."""
    
    def __init__(self, file_path: str):
        super().__init__(
            error_code="NO_STOREYS_FOUND",
            message="Ingen IfcBuildingStorey elementer funnet i IFC-filen. Kontroller romstrukturen.",
            context={"file_path": file_path}
        )


class EmptyCutResultError(ProcessingError):
    """Exception raised when section cut produces no geometry."""
    
    def __init__(self, storey_name: str, cut_height: float):
        super().__init__(
            error_code="EMPTY_CUT_RESULT",
            message=f"Snitt på høyde {cut_height}m ga ingen segmenter for etasje '{storey_name}'. Verifiser cut_z og elementfiltre.",
            context={"storey_name": storey_name, "cut_height": cut_height}
        )


class GeometryShapeError(ProcessingError):
    """Exception raised when geometry shape generation fails."""
    
    def __init__(self, element_guid: str, ifc_class: str, original_error: Optional[Exception] = None):
        context = {"element_guid": element_guid, "ifc_class": ifc_class}
        if original_error:
            context["original_error"] = str(original_error)
        
        super().__init__(
            error_code="GEOMETRY_SHAPE_FAILED",
            message=f"Shape-generering feilet for {ifc_class} element {element_guid}. Sjekk representasjoner og åpningsinnstillinger.",
            context=context
        )


class WriteFailedError(ProcessingError):
    """Exception raised when file writing fails."""
    
    def __init__(self, file_path: str, original_error: Optional[Exception] = None):
        context = {"file_path": file_path}
        if original_error:
            context["original_error"] = str(original_error)
        
        super().__init__(
            error_code="WRITE_FAILED",
            message=f"Kunne ikke skrive fil: {file_path}. Sjekk rettigheter og diskplass.",
            context=context
        )


class ConfigurationError(ProcessingError):
    """Exception raised for configuration-related errors."""
    
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            error_code="CONFIG_ERROR",
            message=f"Konfigurasjonsfeil: {message}",
            context=context
        )


class UnitsDetectionError(ProcessingError):
    """Exception raised when units detection fails."""
    
    def __init__(self, file_path: str, fallback_scale: float = 1.0):
        super().__init__(
            error_code="UNITS_DETECTION_FAILED",
            message="Kunne ikke detektere enheter fra IFC-fil",
            context={"file_path": file_path, "fallback_scale": fallback_scale}
        )


class MultiprocessingError(ProcessingError):
    """Exception raised for multiprocessing-related errors."""
    
    def __init__(self, details: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            error_code="MULTIPROCESSING_ERROR",
            message=f"Feil i parallell prosessering: {details}",
            context=context
        )


class CacheError(ProcessingError):
    """Exception raised for cache-related errors."""
    
    def __init__(self, details: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(
            error_code="CACHE_ERROR",
            message=f"Feil i geometri-cache: {details}",
            context=context
        )


class ToleranceError(ProcessingError):
    """Exception raised for invalid tolerance values."""
    
    def __init__(self, tolerance_type: str, value: float, context: Optional[Dict[str, Any]] = None):
        context = context or {}
        context.update({"tolerance_type": tolerance_type, "value": value})
        super().__init__(
            error_code="TOLERANCE_ERROR",
            message=f"Ugyldig toleranse-verdi: {tolerance_type} = {value}",
            context=context
        )


class ValidationError(ProcessingError):
    """Exception raised for input validation errors."""
    
    def __init__(self, field: str, value: Any, reason: str, context: Optional[Dict[str, Any]] = None):
        context = context or {}
        context.update({"field": field, "value": value, "reason": reason})
        super().__init__(
            error_code="VALIDATION_ERROR",
            message=f"Valideringsfeil for {field}: {reason}",
            context=context
        )