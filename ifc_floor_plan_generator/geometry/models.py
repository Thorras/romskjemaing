"""
Geometry data models for IFC Floor Plan Generator.

Re-exports geometry-related classes from the main models module for convenience.
"""

# Import geometry classes from main models module
from ..models import BoundingBox

__all__ = [
    "BoundingBox"
]