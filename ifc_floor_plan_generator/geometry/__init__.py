"""
Geometry processing module for IFC Floor Plan Generator.

Handles 3D geometry generation, caching, and section processing operations.
"""

from .engine import GeometryEngine
from .section_processor import SectionProcessor
from .cache import GeometryCache, CacheEntry, CacheStats
from ..models import BoundingBox

__all__ = [
    "GeometryEngine",
    "SectionProcessor", 
    "GeometryCache",
    "CacheEntry",
    "CacheStats",
    "BoundingBox"
]