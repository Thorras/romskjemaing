"""
IFC Floor Plan Generator

A system for converting IFC files to 2D floor plan representations in SVG and GeoJSON formats.
"""

__version__ = "1.0.0"
__author__ = "IFC Floor Plan Generator Team"

from .models import Config, Polyline2D, StoreyResult, ProcessingResult
from .errors import ProcessingError

__all__ = [
    "Config",
    "Polyline2D", 
    "StoreyResult",
    "ProcessingResult",
    "ProcessingError"
]