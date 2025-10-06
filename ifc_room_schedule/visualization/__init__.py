"""
Interactive 2D Floor Plans Visualization Module

This module provides interactive 2D floor plan visualization capabilities
for the IFC Room Schedule application, including geometric data extraction,
rendering, and user interaction components.
"""

from .geometry_models import Point2D, Polygon2D, FloorLevel, FloorGeometry
from .geometry_extractor import GeometryExtractor, GeometryExtractionError

__all__ = [
    'Point2D',
    'Polygon2D', 
    'FloorLevel',
    'FloorGeometry',
    'GeometryExtractor',
    'GeometryExtractionError'
]