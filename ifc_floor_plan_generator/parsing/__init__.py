"""
IFC parsing module for IFC Floor Plan Generator.

Provides wrapper around IfcOpenShell for robust IFC file handling and element extraction.
"""

from .ifc_parser import IFCParser
from .element_filter import ElementFilter

__all__ = [
    "IFCParser",
    "ElementFilter"
]