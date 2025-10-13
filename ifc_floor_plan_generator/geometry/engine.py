"""
Geometry engine for IFC Floor Plan Generator.

Generates 3D geometry from IFC elements using IfcOpenShell with configurable settings.
"""

import logging
from typing import Any, Optional, Dict, List, Tuple
from ..models import BoundingBox, GeometryConfig
from ..errors.handler import ErrorHandler
from ..errors.exceptions import GeometryShapeError
from .cache import GeometryCache, CacheStats

# IfcOpenShell imports with error handling
try:
    import ifcopenshell
    import ifcopenshell.geom
    from OCC.Core import TopoDS_Shape, Bnd_Box, BRepBndLib_Add, BRepTools_ShapeSet
    from OCC.Core.gp import gp_Pnt
    HAS_IFCOPENSHELL = True
except ImportError:
    HAS_IFCOPENSHELL = False
    # Create placeholder classes for type hints when IfcOpenShell is not available
    class TopoDS_Shape:
        pass


class GeometryEngine:
    """Generates 3D geometry from IFC elements with configurable settings."""
    
    def __init__(self, config: GeometryConfig, error_handler: Optional[ErrorHandler] = None,
                 cache_config: Optional[Dict[str, Any]] = None):
        """Initialize geometry engine with configuration.
        
        Args:
            config: Geometry configuration settings
            error_handler: Error handler for structured error reporting
            cache_config: Optional cache configuration parameters
            
        Raises:
            ImportError: If IfcOpenShell is not available
        """
        if not HAS_IFCOPENSHELL:
            raise ImportError(
                "IfcOpenShell is required for geometry generation. "
                "Install with: pip install ifcopenshell"
            )
        
        self.config = config
        self.error_handler = error_handler or ErrorHandler()
        self.logger = logging.getLogger(__name__)
        
        # Initialize IfcOpenShell geometry settings
        self._geometry_settings = self._create_geometry_settings()
        
        # Initialize sophisticated geometry cache
        if self.config.cache_geometry:
            cache_params = cache_config or {}
            self._geometry_cache = GeometryCache(
                max_memory_mb=cache_params.get('max_memory_mb', 500.0),
                max_entries=cache_params.get('max_entries', 10000),
                ttl_hours=cache_params.get('ttl_hours', 24.0),
                enable_disk_cache=cache_params.get('enable_disk_cache', False),
                disk_cache_dir=cache_params.get('disk_cache_dir')
            )
            
            # Update cache with current configuration
            config_dict = {
                'use_world_coords': self.config.use_world_coords,
                'subtract_openings': self.config.subtract_openings,
                'sew_shells': self.config.sew_shells,
            }
            self._geometry_cache.update_configuration(config_dict)
        else:
            self._geometry_cache = None
        
        self.logger.info("GeometryEngine initialized with IfcOpenShell and sophisticated caching")
    
    def _create_geometry_settings(self) -> 'ifcopenshell.geom.settings':
        """Create IfcOpenShell geometry settings based on configuration.
        
        Returns:
            ifcopenshell.geom.settings: Configured geometry settings
        """
        settings = ifcopenshell.geom.settings()
        
        # Configure based on GeometryConfig
        settings.set(settings.USE_WORLD_COORDS, self.config.use_world_coords)
        settings.set(settings.DISABLE_OPENING_SUBTRACTIONS, not self.config.subtract_openings)
        settings.set(settings.SEW_SHELLS, self.config.sew_shells)
        
        # Additional settings for better geometry quality
        settings.set(settings.USE_BREP_DATA, True)
        settings.set(settings.INCLUDE_CURVES, True)
        
        self.logger.debug(f"Geometry settings: world_coords={self.config.use_world_coords}, "
                         f"subtract_openings={self.config.subtract_openings}, "
                         f"sew_shells={self.config.sew_shells}")
        
        return settings
    
    def generate_shape(self, element: Any) -> Optional[TopoDS_Shape]:
        """Generate 3D shape from IFC element.
        
        Args:
            element: IFC element (IfcProduct or similar)
            
        Returns:
            TopoDS_Shape or None: Generated 3D shape, None if generation failed
            
        Raises:
            GeometryShapeError: If shape generation fails critically
        """
        if not hasattr(element, 'GlobalId'):
            self.error_handler.log_warning(
                "Element missing GlobalId, skipping geometry generation",
                {"element_type": type(element).__name__}
            )
            return None
        
        element_guid = element.GlobalId
        ifc_class = element.is_a() if hasattr(element, 'is_a') else 'Unknown'
        
        try:
            # Check cache first (if caching is enabled)
            if self.config.cache_geometry and self._geometry_cache is not None:
                cached_shape = self._geometry_cache.get(element_guid)
                if cached_shape is not None:
                    self.logger.debug(f"Using cached geometry for {element_guid}")
                    return cached_shape
            
            # Generate shape using IfcOpenShell
            self.logger.debug(f"Generating shape for {ifc_class} element {element_guid}")
            
            # Create shape using IfcOpenShell geometry engine
            shape_data = ifcopenshell.geom.create_shape(self._geometry_settings, element)
            
            if shape_data is None:
                self.error_handler.log_warning(
                    f"No geometry data generated for element {element_guid}",
                    {
                        "element_guid": element_guid,
                        "ifc_class": ifc_class,
                        "reason": "IfcOpenShell returned None"
                    }
                )
                return None
            
            # Extract the TopoDS_Shape from the shape data
            if hasattr(shape_data, 'geometry'):
                shape = shape_data.geometry
            else:
                # Fallback for different IfcOpenShell versions
                shape = shape_data
            
            # Validate the shape
            if not self._is_valid_shape(shape):
                self.error_handler.log_warning(
                    f"Generated invalid shape for element {element_guid}",
                    {
                        "element_guid": element_guid,
                        "ifc_class": ifc_class,
                        "reason": "Shape validation failed"
                    }
                )
                return None
            
            # Cache the shape if caching is enabled
            if self.config.cache_geometry and self._geometry_cache is not None:
                self._geometry_cache.put(element_guid, shape)
            
            self.logger.debug(f"Successfully generated shape for {element_guid}")
            return shape
            
        except Exception as e:
            # Handle geometry generation errors
            error_context = {
                "element_guid": element_guid,
                "ifc_class": ifc_class,
                "original_error": str(e),
                "error_type": type(e).__name__
            }
            
            # Check if this is a recoverable error
            if self.error_handler.handle_recoverable_error("GEOMETRY_SHAPE_FAILED", error_context):
                # Error was handled gracefully, return None to skip this element
                return None
            else:
                # Critical error, re-raise as GeometryShapeError
                raise GeometryShapeError(
                    element_guid=element_guid,
                    ifc_class=ifc_class,
                    original_error=e
                )
    
    def _is_valid_shape(self, shape: TopoDS_Shape) -> bool:
        """Validate that a TopoDS_Shape is valid and usable.
        
        Args:
            shape: The shape to validate
            
        Returns:
            bool: True if shape is valid, False otherwise
        """
        try:
            # Basic validation - check if shape exists and is not null
            if shape is None:
                return False
            
            # Check if shape has any geometry content
            # This is a basic check - more sophisticated validation could be added
            return True
            
        except Exception as e:
            self.logger.debug(f"Shape validation failed: {e}")
            return False
    
    def get_element_bounds(self, shape: TopoDS_Shape) -> Optional[BoundingBox]:
        """Get bounding box of a 3D shape.
        
        Args:
            shape: The 3D shape to get bounds for
            
        Returns:
            BoundingBox or None: 2D bounding box (X,Y only), None if calculation failed
        """
        try:
            if shape is None:
                return None
            
            # Create bounding box using OpenCASCADE
            bbox = Bnd_Box()
            BRepBndLib_Add(shape, bbox)
            
            # Get the bounds
            if bbox.IsVoid():
                self.logger.debug("Shape has void bounding box")
                return None
            
            # Extract min/max coordinates
            xmin, ymin, zmin, xmax, ymax, zmax = bbox.Get()
            
            # Return 2D bounding box (ignore Z for floor plan purposes)
            return BoundingBox(
                min_x=float(xmin),
                min_y=float(ymin),
                max_x=float(xmax),
                max_y=float(ymax)
            )
            
        except Exception as e:
            self.logger.warning(f"Failed to calculate bounding box: {e}")
            return None
    
    def get_shape_vertices(self, shape: TopoDS_Shape) -> List[tuple]:
        """Get all vertices from a shape as coordinate tuples.
        
        Args:
            shape: The 3D shape to extract vertices from
            
        Returns:
            List[tuple]: List of (x, y, z) coordinate tuples
        """
        vertices = []
        try:
            # This is a placeholder for vertex extraction
            # In a full implementation, you would iterate through the shape's vertices
            # using OpenCASCADE topology exploration
            pass
        except Exception as e:
            self.logger.warning(f"Failed to extract vertices: {e}")
        
        return vertices
    
    def update_cache_configuration(self, config_dict: Dict[str, Any]) -> None:
        """Update cache configuration and invalidate if necessary.
        
        Args:
            config_dict: Configuration dictionary with geometry settings
        """
        if self.config.cache_geometry and self._geometry_cache is not None:
            self._geometry_cache.update_configuration(config_dict)
    
    def clear_cache(self) -> None:
        """Clear the geometry cache."""
        if self.config.cache_geometry and self._geometry_cache is not None:
            self._geometry_cache.clear()
            self.logger.info("Cleared geometry cache")
        else:
            self.logger.debug("Cache not enabled or not initialized")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Dict containing cache statistics
        """
        if not self.config.cache_geometry or self._geometry_cache is None:
            return {
                "cache_enabled": False,
                "cached_items": 0,
                "cache_type": "disabled"
            }
        
        stats = self._geometry_cache.get_stats()
        return {
            "cache_enabled": True,
            "cached_items": stats.cached_items,
            "cache_type": "sophisticated",
            "hit_rate_percent": stats.hit_rate,
            "total_requests": stats.total_requests,
            "cache_hits": stats.cache_hits,
            "cache_misses": stats.cache_misses,
            "memory_usage_mb": stats.memory_usage_mb,
            "invalidations": stats.invalidations
        }
    
    def cleanup_expired_cache(self) -> int:
        """Clean up expired cache entries.
        
        Returns:
            int: Number of expired entries removed
        """
        if self.config.cache_geometry and self._geometry_cache is not None:
            return self._geometry_cache.cleanup_expired()
        return 0
    
    def is_cached(self, guid: str) -> bool:
        """Check if geometry is cached for the given GUID.
        
        Args:
            guid: Element GUID to check
            
        Returns:
            bool: True if geometry is cached, False otherwise
        """
        if not self.config.cache_geometry or self._geometry_cache is None:
            return False
        return guid in self._geometry_cache
    
    def generate_shapes_batch(self, elements: List[Any]) -> Dict[str, Optional[TopoDS_Shape]]:
        """Generate shapes for multiple elements in batch with optimized caching.
        
        Args:
            elements: List of IFC elements to process
            
        Returns:
            Dict mapping element GUIDs to their shapes (None if generation failed)
        """
        results = {}
        cache_misses = []
        
        # First pass: check cache for all elements
        if self.config.cache_geometry and self._geometry_cache is not None:
            for element in elements:
                if hasattr(element, 'GlobalId'):
                    guid = element.GlobalId
                    cached_shape = self._geometry_cache.get(guid)
                    if cached_shape is not None:
                        results[guid] = cached_shape
                        self.logger.debug(f"Batch cache hit for {guid}")
                    else:
                        cache_misses.append(element)
                else:
                    cache_misses.append(element)
        else:
            cache_misses = elements
        
        # Second pass: generate shapes for cache misses
        newly_generated = []
        for element in cache_misses:
            if hasattr(element, 'GlobalId'):
                guid = element.GlobalId
                try:
                    shape = self.generate_shape(element)
                    results[guid] = shape
                    if shape is not None:
                        newly_generated.append((guid, shape))
                except Exception as e:
                    self.logger.warning(f"Failed to generate shape for {guid}: {e}")
                    results[guid] = None
            else:
                self.logger.warning(f"Element missing GlobalId: {type(element).__name__}")
        
        # Log batch processing statistics
        total_elements = len(elements)
        cache_hits = total_elements - len(cache_misses)
        if total_elements > 0:
            hit_rate = (cache_hits / total_elements) * 100
            self.logger.info(f"Batch processed {total_elements} elements: "
                           f"{cache_hits} cache hits ({hit_rate:.1f}%), "
                           f"{len(newly_generated)} newly generated")
        
        return results
    
    def preload_geometry_cache(self, elements: List[Any]) -> int:
        """Preload geometry cache with shapes from elements.
        
        This method can be used to warm up the cache before processing,
        which is useful for repeated operations on the same elements.
        
        Args:
            elements: List of IFC elements to preload
            
        Returns:
            int: Number of shapes successfully preloaded
        """
        if not self.config.cache_geometry or self._geometry_cache is None:
            self.logger.debug("Cache not enabled, skipping preload")
            return 0
        
        preload_pairs = []
        
        for element in elements:
            if hasattr(element, 'GlobalId'):
                guid = element.GlobalId
                
                # Skip if already cached
                if self.is_cached(guid):
                    continue
                
                try:
                    # Generate shape without caching (to avoid double-caching)
                    shape_data = ifcopenshell.geom.create_shape(self._geometry_settings, element)
                    
                    if shape_data is not None:
                        if hasattr(shape_data, 'geometry'):
                            shape = shape_data.geometry
                        else:
                            shape = shape_data
                        
                        if self._is_valid_shape(shape):
                            preload_pairs.append((guid, shape))
                
                except Exception as e:
                    self.logger.debug(f"Failed to preload shape for {guid}: {e}")
        
        # Bulk load into cache
        if preload_pairs:
            return self._geometry_cache.preload_shapes(preload_pairs)
        
        return 0
    
    def get_cache_efficiency_report(self) -> Dict[str, Any]:
        """Get comprehensive cache efficiency report.
        
        Returns:
            Dict with detailed cache performance metrics
        """
        if not self.config.cache_geometry or self._geometry_cache is None:
            return {
                "cache_enabled": False,
                "message": "Geometry caching is disabled"
            }
        
        basic_stats = self.get_cache_stats()
        efficiency_metrics = self._geometry_cache.get_cache_efficiency_metrics()
        
        return {
            "cache_enabled": True,
            "basic_stats": basic_stats,
            "efficiency_metrics": efficiency_metrics,
            "recommendations": self._generate_cache_recommendations(efficiency_metrics)
        }
    
    def _generate_cache_recommendations(self, metrics: Dict[str, float]) -> List[str]:
        """Generate cache optimization recommendations based on metrics.
        
        Args:
            metrics: Cache efficiency metrics
            
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        # Hit rate recommendations
        if metrics['hit_rate_percent'] < 50:
            recommendations.append(
                "Low cache hit rate (<50%). Consider increasing cache size or TTL."
            )
        elif metrics['hit_rate_percent'] > 90:
            recommendations.append(
                "Excellent cache hit rate (>90%). Cache is working optimally."
            )
        
        # Memory efficiency recommendations
        if metrics['memory_efficiency'] < 10:
            recommendations.append(
                "Low memory efficiency. Consider reducing cache size or enabling disk cache."
            )
        
        # Cache utilization recommendations
        if metrics['cache_utilization'] > 0.9:
            recommendations.append(
                "Cache utilization is high (>90%). Consider increasing max_entries."
            )
        elif metrics['cache_utilization'] < 0.3:
            recommendations.append(
                "Cache utilization is low (<30%). Consider reducing max_entries to save memory."
            )
        
        # Eviction rate recommendations
        if metrics['eviction_rate'] > 0.1:
            recommendations.append(
                "High eviction rate (>10%). Consider increasing cache size or TTL."
            )
        
        if not recommendations:
            recommendations.append("Cache performance is within optimal parameters.")
        
        return recommendations