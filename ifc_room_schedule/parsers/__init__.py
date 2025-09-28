"""
Parsers Module

Parsers for IFC data and Norwegian standards (NS 8360/NS 3940).
"""

from .ns8360_name_parser import NS8360NameParser, NS8360ParsedName

__all__ = [
    'NS8360NameParser',
    'NS8360ParsedName'
]
