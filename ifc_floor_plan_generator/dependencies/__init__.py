"""
Dependency management for IFC Floor Plan Generator.

Handles optional dependencies with graceful degradation.
"""

from .occ_wrapper import (
    HAS_OCC,
    OCCDependencyError,
    get_occ_status,
    require_occ,
    mock_occ_classes
)

__all__ = [
    'HAS_OCC',
    'OCCDependencyError', 
    'get_occ_status',
    'require_occ',
    'mock_occ_classes'
]