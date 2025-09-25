"""
IFC Parser Module

Handles IFC file import, validation, and entity extraction.
"""

from .ifc_file_reader import IfcFileReader
from .ifc_space_extractor import IfcSpaceExtractor
from .ifc_relationship_parser import IfcRelationshipParser

__all__ = ['IfcFileReader', 'IfcSpaceExtractor', 'IfcRelationshipParser']