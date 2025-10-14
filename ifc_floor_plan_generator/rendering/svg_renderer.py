"""
SVG renderer for IFC Floor Plan Generator.

Renders polylines to SVG format with configurable styling per IFC class.
"""

import logging
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Tuple, Optional
from ..models import Polyline2D, BoundingBox
from ..config.models import RenderingConfig
from .models import StyleAttributes
from ..errors.handler import ErrorHandler
from ..errors.exceptions import ProcessingError


class SVGRenderer:
    """Renders polylines to SVG format with configurable styling."""
    
    def __init__(self, config: RenderingConfig):
        """Initialize SVG renderer with configuration.
        
        Args:
            config: Rendering configuration including colors, line widths, and class styles
        """
        self.config = config
        self._viewport_bounds: Optional[BoundingBox] = None
        self._viewport_width: float = 800.0  # Default viewport width
        self._viewport_height: float = 600.0  # Default viewport height
        self._margin: float = 20.0  # Margin around content
        self._logger = logging.getLogger(__name__)
        self._error_handler = ErrorHandler()
    
    def render_polylines(self, polylines: List[Polyline2D], metadata: Dict[str, Any]) -> str:
        """Render polylines to SVG string.
        
        Args:
            polylines: List of polylines to render
            metadata: Additional metadata for the SVG (title, description, etc.)
            
        Returns:
            str: Complete SVG document as string
            
        Raises:
            ProcessingError: If SVG generation fails
        """
        try:
            if not polylines:
                self._logger.warning("No polylines to render")
                return self._create_empty_svg(metadata)
            
            # Calculate bounding box if not set
            if self._viewport_bounds is None:
                self._calculate_viewport_from_polylines(polylines)
            
            # Create SVG root element
            svg_root = self._create_svg_root()
            
            # Add metadata
            self._add_svg_metadata(svg_root, metadata)
            
            # Add background if configured
            if self.config.background:
                self._add_background(svg_root)
            
            # Create group for polylines
            polylines_group = ET.SubElement(svg_root, "g")
            polylines_group.set("id", "polylines")
            
            # Render each polyline
            for i, polyline in enumerate(polylines):
                try:
                    self._render_single_polyline(polylines_group, polyline, i)
                except Exception as e:
                    self._logger.warning(f"Failed to render polyline {i}: {e}")
                    continue
            
            # Convert to string
            svg_string = self._element_to_string(svg_root)
            
            self._logger.debug(f"Successfully rendered {len(polylines)} polylines to SVG")
            return svg_string
            
        except Exception as e:
            self._logger.error(f"SVG rendering failed: {e}")
            raise ProcessingError(
                error_code="SVG_RENDER_FAILED",
                message=f"SVG-rendering feilet: {str(e)}",
                context={"error": str(e), "polyline_count": len(polylines)}
            )
    
    def apply_styling(self, ifc_class: str) -> StyleAttributes:
        """Apply styling based on IFC class.
        
        Args:
            ifc_class: IFC class name to get styling for
            
        Returns:
            StyleAttributes: Style attributes for the IFC class
        """
        # Check if there's a specific style for this IFC class
        if ifc_class in self.config.class_styles:
            class_style = self.config.class_styles[ifc_class]
            color = class_style.get("color", self.config.default_color)
            linewidth = class_style.get("linewidth_px", self.config.default_linewidth_px)
        else:
            # Use default styling
            color = self.config.default_color
            linewidth = self.config.default_linewidth_px
        
        return StyleAttributes(
            stroke=color,
            stroke_width=linewidth,
            fill="none"
        )
    
    def set_viewport(self, bounds: BoundingBox) -> None:
        """Set SVG viewport based on bounding box.
        
        Args:
            bounds: Bounding box to use for viewport calculation
        """
        self._viewport_bounds = bounds
        
        # Calculate viewport dimensions maintaining aspect ratio
        content_width = bounds.width
        content_height = bounds.height
        
        if content_width > 0 and content_height > 0:
            # Add margins
            total_width = content_width + 2 * self._margin
            total_height = content_height + 2 * self._margin
            
            # Set viewport dimensions
            self._viewport_width = total_width
            self._viewport_height = total_height
            
            self._logger.debug(f"Set viewport: {self._viewport_width}x{self._viewport_height}")
    
    def _create_svg_root(self) -> ET.Element:
        """Create SVG root element with proper attributes.
        
        Returns:
            ET.Element: SVG root element
        """
        svg = ET.Element("svg")
        svg.set("xmlns", "http://www.w3.org/2000/svg")
        svg.set("version", "1.1")
        svg.set("width", str(self._viewport_width))
        svg.set("height", str(self._viewport_height))
        
        if self._viewport_bounds:
            # Set viewBox to show the content with margins
            viewbox_x = self._viewport_bounds.min_x - self._margin
            viewbox_y = self._viewport_bounds.min_y - self._margin
            viewbox_width = self._viewport_bounds.width + 2 * self._margin
            viewbox_height = self._viewport_bounds.height + 2 * self._margin
            
            # Apply Y-inversion if configured
            if self.config.invert_y:
                # Flip the viewBox for Y-inversion
                viewbox_y = -(self._viewport_bounds.max_y + self._margin)
            
            svg.set("viewBox", f"{viewbox_x} {viewbox_y} {viewbox_width} {viewbox_height}")
        
        return svg
    
    def _add_svg_metadata(self, svg_root: ET.Element, metadata: Dict[str, Any]) -> None:
        """Add metadata elements to SVG.
        
        Args:
            svg_root: SVG root element
            metadata: Metadata dictionary
        """
        # Add title if provided
        title = metadata.get("title", "IFC Floor Plan")
        title_elem = ET.SubElement(svg_root, "title")
        title_elem.text = title
        
        # Add description if provided
        description = metadata.get("description", "Generated by IFC Floor Plan Generator")
        desc_elem = ET.SubElement(svg_root, "desc")
        desc_elem.text = description
        
        # Add generator metadata
        metadata_group = ET.SubElement(svg_root, "metadata")
        generator = ET.SubElement(metadata_group, "generator")
        generator.text = "IFC Floor Plan Generator"
        
        # Add creation date if provided
        if "created_at" in metadata:
            created = ET.SubElement(metadata_group, "created")
            created.text = str(metadata["created_at"])
    
    def _add_background(self, svg_root: ET.Element) -> None:
        """Add background rectangle to SVG.
        
        Args:
            svg_root: SVG root element
        """
        background = ET.SubElement(svg_root, "rect")
        background.set("x", "0")
        background.set("y", "0")
        background.set("width", "100%")
        background.set("height", "100%")
        background.set("fill", self.config.background)
        background.set("id", "background")
    
    def _render_single_polyline(self, parent: ET.Element, polyline: Polyline2D, index: int) -> None:
        """Render a single polyline to SVG.
        
        Args:
            parent: Parent SVG element
            polyline: Polyline to render
            index: Index of the polyline (for ID generation)
        """
        if len(polyline.points) < 2:
            return
        
        # Get styling for this IFC class
        style = self.apply_styling(polyline.ifc_class)
        
        # Create polyline or polygon element based on whether it's closed
        if polyline.is_closed and len(polyline.points) > 2:
            element = ET.SubElement(parent, "polygon")
            points_str = self._points_to_svg_polygon(polyline.points)
            element.set("points", points_str)
        else:
            element = ET.SubElement(parent, "polyline")
            points_str = self._points_to_svg_polyline(polyline.points)
            element.set("points", points_str)
        
        # Set styling
        element.set("style", style.to_svg_style())
        
        # Set ID and class for CSS styling
        element.set("id", f"polyline_{index}")
        element.set("class", f"ifc-{polyline.ifc_class.lower()}")
        
        # Add data attributes for metadata
        element.set("data-ifc-class", polyline.ifc_class)
        element.set("data-element-guid", polyline.element_guid)
    
    def _points_to_svg_polyline(self, points: List[Tuple[float, float]]) -> str:
        """Convert points to SVG polyline points string.
        
        Args:
            points: List of 2D points
            
        Returns:
            str: SVG points string
        """
        transformed_points = self._transform_points_for_svg(points)
        return " ".join(f"{x},{y}" for x, y in transformed_points)
    
    def _points_to_svg_polygon(self, points: List[Tuple[float, float]]) -> str:
        """Convert points to SVG polygon points string.
        
        Args:
            points: List of 2D points
            
        Returns:
            str: SVG points string
        """
        transformed_points = self._transform_points_for_svg(points)
        return " ".join(f"{x},{y}" for x, y in transformed_points)
    
    def _transform_points_for_svg(self, points: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """Transform points for SVG coordinate system.
        
        Args:
            points: Original points
            
        Returns:
            List[Tuple[float, float]]: Transformed points
        """
        if not self.config.invert_y or not self._viewport_bounds:
            return points
        
        # Apply Y-inversion by flipping around the center Y coordinate
        center_y = (self._viewport_bounds.min_y + self._viewport_bounds.max_y) / 2
        transformed = []
        
        for x, y in points:
            new_y = 2 * center_y - y
            transformed.append((x, new_y))
        
        return transformed
    
    def _calculate_viewport_from_polylines(self, polylines: List[Polyline2D]) -> None:
        """Calculate viewport bounds from polylines.
        
        Args:
            polylines: List of polylines to calculate bounds from
        """
        if not polylines:
            return
        
        # Find bounding box of all points
        all_x = []
        all_y = []
        
        for polyline in polylines:
            for x, y in polyline.points:
                all_x.append(x)
                all_y.append(y)
        
        if all_x and all_y:
            bounds = BoundingBox(
                min_x=min(all_x),
                min_y=min(all_y),
                max_x=max(all_x),
                max_y=max(all_y)
            )
            self.set_viewport(bounds)
    
    def _create_empty_svg(self, metadata: Dict[str, Any]) -> str:
        """Create an empty SVG document.
        
        Args:
            metadata: Metadata for the SVG
            
        Returns:
            str: Empty SVG document
        """
        svg = ET.Element("svg")
        svg.set("xmlns", "http://www.w3.org/2000/svg")
        svg.set("version", "1.1")
        svg.set("width", "400")
        svg.set("height", "300")
        
        self._add_svg_metadata(svg, metadata)
        
        # Add message about empty content
        text = ET.SubElement(svg, "text")
        text.set("x", "200")
        text.set("y", "150")
        text.set("text-anchor", "middle")
        text.set("font-family", "Arial, sans-serif")
        text.set("font-size", "16")
        text.set("fill", "#666666")
        text.text = "No geometry to display"
        
        return self._element_to_string(svg)
    
    def _element_to_string(self, element: ET.Element) -> str:
        """Convert XML element to formatted string.
        
        Args:
            element: XML element to convert
            
        Returns:
            str: Formatted XML string
        """
        # Format the XML with proper indentation
        self._indent_xml(element)
        
        # Convert to string
        xml_str = ET.tostring(element, encoding='unicode', method='xml')
        
        # Add XML declaration
        formatted_svg = '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_str
        
        return formatted_svg
    
    def _indent_xml(self, elem: ET.Element, level: int = 0) -> None:
        """Add proper indentation to XML elements.
        
        Args:
            elem: XML element to indent
            level: Current indentation level
        """
        indent = "\n" + level * "  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = indent + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = indent
            for child in elem:
                self._indent_xml(child, level + 1)
            if not child.tail or not child.tail.strip():
                child.tail = indent
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = indent
    
    def set_viewport_dimensions(self, width: float, height: float) -> None:
        """Set custom viewport dimensions.
        
        Args:
            width: Viewport width
            height: Viewport height
        """
        self._viewport_width = width
        self._viewport_height = height
        self._logger.debug(f"Set custom viewport dimensions: {width}x{height}")
    
    def set_margin(self, margin: float) -> None:
        """Set margin around content.
        
        Args:
            margin: Margin size in coordinate units
        """
        self._margin = margin
        self._logger.debug(f"Set margin: {margin}")
    
    def get_viewport_info(self) -> Dict[str, Any]:
        """Get current viewport information.
        
        Returns:
            Dict containing viewport information
        """
        return {
            "width": self._viewport_width,
            "height": self._viewport_height,
            "margin": self._margin,
            "bounds": self._viewport_bounds.__dict__ if self._viewport_bounds else None,
            "invert_y": self.config.invert_y
        }
    
    def render_and_save(self, polylines: List[Polyline2D], output_manager, 
                       storey_name: str, index: int, metadata: Dict[str, Any]) -> str:
        """Render polylines to SVG and save to file.
        
        This is a convenience method that combines rendering and file writing.
        
        Args:
            polylines: List of polylines to render
            output_manager: OutputManager instance for file operations
            storey_name: Name of the storey for filename generation
            index: Index for filename generation
            metadata: Metadata for the SVG
            
        Returns:
            str: Full path to the saved SVG file
            
        Raises:
            WriteFailedError: If file writing fails
            ProcessingError: If SVG generation fails
        """
        # Generate SVG content
        svg_content = self.render_polylines(polylines, metadata)
        
        # Generate filename
        filename = output_manager.generate_svg_filename(storey_name, index)
        
        # Write to file
        file_path = output_manager.write_svg_file(svg_content, filename)
        
        self._logger.info(f"Rendered and saved SVG: {file_path}")
        return file_path