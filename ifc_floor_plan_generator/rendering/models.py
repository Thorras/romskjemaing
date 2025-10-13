"""
Rendering data models for IFC Floor Plan Generator.

Defines data structures specific to rendering operations.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class RenderStyle:
    """Style configuration for rendering IFC elements."""
    color: str = "#000000"
    linewidth_px: float = 1.0
    
    def __post_init__(self):
        """Validate render style after initialization."""
        if self.linewidth_px <= 0:
            raise ValueError("Linewidth must be positive")
        if not self.color:
            raise ValueError("Color is required")


@dataclass
class StyleAttributes:
    """SVG style attributes for an element."""
    stroke: str
    stroke_width: float
    fill: str = "none"
    
    def to_svg_style(self) -> str:
        """Convert to SVG style string."""
        return f"stroke:{self.stroke};stroke-width:{self.stroke_width};fill:{self.fill}"


__all__ = [
    "RenderStyle",
    "StyleAttributes"
]