"""
Configuration module for IFC Room Schedule

Handles configuration management for export settings, section activation,
and fallback strategies.
"""

from .section_configuration import (
    SectionConfiguration,
    ExportProfile,
    SectionSettings,
    ExportConfiguration
)

__all__ = [
    'SectionConfiguration',
    'ExportProfile', 
    'SectionSettings',
    'ExportConfiguration'
]


