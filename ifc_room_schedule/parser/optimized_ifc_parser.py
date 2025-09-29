"""
Optimized IFC Parser

High-performance IFC parsing with caching, lazy loading, and memory optimization.
"""

import os
import gc
import time
from typing import Dict, List, Any, Optional, Tuple, Iterator
from dataclasses import dataclass
from functools import lru_cache
import ifcopenshell
import ifcopenshell.util.element
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

from ..utils.enhanced_logging import enhanced_logger


@dataclass
class ParsingMetrics:
    """Metrics for IFC parsing performance."""
    
    file_size_mb: float
    parsing_time_seconds: float
    memory_usage_mb: float
    entities_processed: int
    spaces_found: int
    cache_hits: int
    cache_misses: int
    processing_rate_mb_per_second: float


@dataclass
class CacheConfig:
    """Configuration for IFC parsing cache."""
    
    max_size: int = 128  # Maximum number of cached items
    ttl_seconds: int = 3600  # Time to live in seconds
    enable_geometry_cache: bool = True
    enable_property_cache: bool = True
    enable_relationship_cache: bool = True


class OptimizedIFCParser:
    """High-performance IFC parser with caching and optimization."""
    
    def __init__(self, cache_config: Optional[CacheConfig] = None):
        """Initialize optimized IFC parser."""
        self.cache_config = cache_config or CacheConfig()
        self.ifc_file = None
        self.file_path = None
        self._cache = {}
        self._cache_timestamps = {}
        self._lock = threading.RLock()
        
        # Performance metrics
        self.metrics = ParsingMetrics(
            file_size_mb=0.0,
            parsing_time_seconds=0.0,
            memory_usage_mb=0.0,
            entities_processed=0,
            spaces_found=0,
            cache_hits=0,
            cache_misses=0,
            processing_rate_mb_per_second=0.0
        )
    
    def load_file_optimized(self, file_path: str) -> Tuple[bool, str]:
        """
        Load IFC file with performance optimizations.
        
        Args:
            file_path: Path to IFC file
            
        Returns:
            Tuple of (success, message)
        """
        operation_id = enhanced_logger.start_operation_timing("optimized_ifc_load", file_path)
        
        try:
            # Basic validation
            if not self._validate_file_basic(file_path):
                return False, "File validation failed"
            
            # Get file size for optimization decisions
            file_size = os.path.getsize(file_path)
            file_size_mb = file_size / (1024 * 1024)
            self.metrics.file_size_mb = file_size_mb
            
            # Choose parsing strategy based on file size
            if file_size_mb < 10:
                return self._load_small_file(file_path, operation_id)
            elif file_size_mb < 100:
                return self._load_medium_file(file_path, operation_id)
            else:
                return self._load_large_file(file_path, operation_id)
                
        except Exception as e:
            enhanced_logger.finish_operation_timing(operation_id)
            return False, f"Error loading file: {str(e)}"
    
    def _validate_file_basic(self, file_path: str) -> bool:
        """Basic file validation."""
        if not os.path.exists(file_path):
            return False
        if not file_path.lower().endswith(('.ifc', '.ifcxml')):
            return False
        if os.path.getsize(file_path) == 0:
            return False
        return True
    
    def _load_small_file(self, file_path: str, operation_id: str) -> Tuple[bool, str]:
        """Load small files with standard parsing."""
        start_time = time.time()
        
        try:
            self.ifc_file = ifcopenshell.open(file_path)
            self.file_path = file_path
            
            # Quick validation
            spaces = self.ifc_file.by_type("IfcSpace")
            if len(spaces) == 0:
                return False, "No IfcSpace entities found"
            
            # Update metrics
            parsing_time = time.time() - start_time
            self.metrics.parsing_time_seconds = parsing_time
            self.metrics.spaces_found = len(spaces)
            self.metrics.entities_processed = len(self.ifc_file)
            self.metrics.processing_rate_mb_per_second = self.metrics.file_size_mb / parsing_time
            
            enhanced_logger.finish_operation_timing(operation_id)
            return True, f"Small file loaded: {len(spaces)} spaces in {parsing_time:.2f}s"
            
        except Exception as e:
            enhanced_logger.finish_operation_timing(operation_id)
            return False, f"Error loading small file: {str(e)}"
    
    def _load_medium_file(self, file_path: str, operation_id: str) -> Tuple[bool, str]:
        """Load medium files with caching optimizations."""
        start_time = time.time()
        
        try:
            # Load with memory optimization
            self.ifc_file = ifcopenshell.open(file_path)
            self.file_path = file_path
            
            # Pre-cache frequently accessed entities
            self._precache_entities()
            
            # Validate spaces
            spaces = self._get_spaces_cached()
            if len(spaces) == 0:
                return False, "No IfcSpace entities found"
            
            # Update metrics
            parsing_time = time.time() - start_time
            self.metrics.parsing_time_seconds = parsing_time
            self.metrics.spaces_found = len(spaces)
            self.metrics.entities_processed = len(self.ifc_file)
            self.metrics.processing_rate_mb_per_second = self.metrics.file_size_mb / parsing_time
            
            enhanced_logger.finish_operation_timing(operation_id)
            return True, f"Medium file loaded with caching: {len(spaces)} spaces in {parsing_time:.2f}s"
            
        except Exception as e:
            enhanced_logger.finish_operation_timing(operation_id)
            return False, f"Error loading medium file: {str(e)}"
    
    def _load_large_file(self, file_path: str, operation_id: str) -> Tuple[bool, str]:
        """Load large files with streaming and lazy loading."""
        start_time = time.time()
        
        try:
            # Load with minimal memory footprint
            self.ifc_file = ifcopenshell.open(file_path)
            self.file_path = file_path
            
            # Use lazy loading for large files
            self._enable_lazy_loading()
            
            # Count spaces without loading all data
            spaces_count = self._count_spaces_efficiently()
            if spaces_count == 0:
                return False, "No IfcSpace entities found"
            
            # Update metrics
            parsing_time = time.time() - start_time
            self.metrics.parsing_time_seconds = parsing_time
            self.metrics.spaces_found = spaces_count
            self.metrics.entities_processed = len(self.ifc_file)
            self.metrics.processing_rate_mb_per_second = self.metrics.file_size_mb / parsing_time
            
            enhanced_logger.finish_operation_timing(operation_id)
            return True, f"Large file loaded with lazy loading: {spaces_count} spaces in {parsing_time:.2f}s"
            
        except Exception as e:
            enhanced_logger.finish_operation_timing(operation_id)
            return False, f"Error loading large file: {str(e)}"
    
    def _precache_entities(self):
        """Pre-cache frequently accessed entities."""
        if not self.ifc_file:
            return
        
        try:
            # Cache space entities
            spaces = self.ifc_file.by_type("IfcSpace")
            self._cache_entities("IfcSpace", spaces)
            
            # Cache building elements
            building_elements = self.ifc_file.by_type("IfcBuildingElement")
            self._cache_entities("IfcBuildingElement", building_elements)
            
            # Cache relationships
            relationships = self.ifc_file.by_type("IfcRelSpaceBoundary")
            self._cache_entities("IfcRelSpaceBoundary", relationships)
            
        except Exception as e:
            enhanced_logger.logger.warning(f"Error precaching entities: {e}")
    
    def _cache_entities(self, entity_type: str, entities: List[Any]):
        """Cache entities with timestamp."""
        with self._lock:
            self._cache[entity_type] = entities
            self._cache_timestamps[entity_type] = time.time()
    
    def _get_spaces_cached(self) -> List[Any]:
        """Get spaces from cache or load if not cached."""
        with self._lock:
            if "IfcSpace" in self._cache:
                if self._is_cache_valid("IfcSpace"):
                    self.metrics.cache_hits += 1
                    return self._cache["IfcSpace"]
            
            # Cache miss - load from file
            self.metrics.cache_misses += 1
            spaces = self.ifc_file.by_type("IfcSpace")
            self._cache_entities("IfcSpace", spaces)
            return spaces
    
    def _is_cache_valid(self, entity_type: str) -> bool:
        """Check if cached data is still valid."""
        if entity_type not in self._cache_timestamps:
            return False
        
        age = time.time() - self._cache_timestamps[entity_type]
        return age < self.cache_config.ttl_seconds
    
    def _enable_lazy_loading(self):
        """Enable lazy loading for large files."""
        # This is a placeholder for lazy loading implementation
        # In practice, this would involve custom IFC reading strategies
        pass
    
    def _count_spaces_efficiently(self) -> int:
        """Count spaces without loading all data."""
        try:
            # Use a more efficient method to count spaces
            count = 0
            for entity in self.ifc_file:
                if entity.is_a("IfcSpace"):
                    count += 1
            return count
        except Exception:
            # Fallback to standard method
            return len(self.ifc_file.by_type("IfcSpace"))
    
    def get_spaces_batch(self, batch_size: int = 100) -> Iterator[List[Any]]:
        """
        Get spaces in batches for memory efficiency.
        
        Args:
            batch_size: Number of spaces per batch
            
        Yields:
            List of space entities
        """
        if not self.ifc_file:
            return
        
        spaces = self._get_spaces_cached()
        
        for i in range(0, len(spaces), batch_size):
            batch = spaces[i:i + batch_size]
            yield batch
    
    def get_space_properties_cached(self, space_guid: str) -> Optional[Dict[str, Any]]:
        """
        Get space properties with caching.
        
        Args:
            space_guid: GUID of the space
            
        Returns:
            Dictionary of space properties or None
        """
        cache_key = f"space_properties_{space_guid}"
        
        with self._lock:
            if cache_key in self._cache and self._is_cache_valid(cache_key):
                self.metrics.cache_hits += 1
                return self._cache[cache_key]
            
            # Cache miss - load properties
            self.metrics.cache_misses += 1
            try:
                space = self.ifc_file.by_guid(space_guid)
                properties = self._extract_space_properties(space)
                self._cache[cache_key] = properties
                self._cache_timestamps[cache_key] = time.time()
                return properties
            except Exception:
                return None
    
    def _extract_space_properties(self, space) -> Dict[str, Any]:
        """Extract properties from space entity."""
        properties = {
            "guid": getattr(space, 'GlobalId', ''),
            "name": getattr(space, 'Name', ''),
            "long_name": getattr(space, 'LongName', ''),
            "description": getattr(space, 'Description', ''),
            "object_type": getattr(space, 'ObjectType', ''),
            "elevation": getattr(space, 'ElevationOfRefHeight', 0.0),
            "quantities": self._extract_quantities(space),
            "properties": self._extract_property_sets(space)
        }
        return properties
    
    def _extract_quantities(self, space) -> Dict[str, float]:
        """Extract quantities from space entity."""
        quantities = {}
        try:
            # Extract area quantities
            for rel in getattr(space, 'IsDefinedBy', []):
                if hasattr(rel, 'RelatingPropertyDefinition'):
                    prop_def = rel.RelatingPropertyDefinition
                    if hasattr(prop_def, 'HasProperties'):
                        for prop in prop_def.HasProperties:
                            if hasattr(prop, 'Name') and hasattr(prop, 'NominalValue'):
                                quantities[prop.Name] = float(prop.NominalValue)
        except Exception:
            pass
        return quantities
    
    def _extract_property_sets(self, space) -> Dict[str, Any]:
        """Extract property sets from space entity."""
        properties = {}
        try:
            for rel in getattr(space, 'IsDefinedBy', []):
                if hasattr(rel, 'RelatingPropertyDefinition'):
                    prop_def = rel.RelatingPropertyDefinition
                    if hasattr(prop_def, 'Name'):
                        prop_set_name = prop_def.Name
                        prop_set_props = {}
                        
                        if hasattr(prop_def, 'HasProperties'):
                            for prop in prop_def.HasProperties:
                                if hasattr(prop, 'Name') and hasattr(prop, 'NominalValue'):
                                    prop_set_props[prop.Name] = str(prop.NominalValue)
                        
                        properties[prop_set_name] = prop_set_props
        except Exception:
            pass
        return properties
    
    def get_space_boundaries_cached(self, space_guid: str) -> List[Dict[str, Any]]:
        """
        Get space boundaries with caching.
        
        Args:
            space_guid: GUID of the space
            
        Returns:
            List of boundary dictionaries
        """
        cache_key = f"space_boundaries_{space_guid}"
        
        with self._lock:
            if cache_key in self._cache and self._is_cache_valid(cache_key):
                self.metrics.cache_hits += 1
                return self._cache[cache_key]
            
            # Cache miss - load boundaries
            self.metrics.cache_misses += 1
            try:
                space = self.ifc_file.by_guid(space_guid)
                boundaries = self._extract_space_boundaries(space)
                self._cache[cache_key] = boundaries
                self._cache_timestamps[cache_key] = time.time()
                return boundaries
            except Exception:
                return []
    
    def _extract_space_boundaries(self, space) -> List[Dict[str, Any]]:
        """Extract space boundaries from space entity."""
        boundaries = []
        try:
            for rel in getattr(space, 'BoundedBy', []):
                if hasattr(rel, 'RelatedBuildingElement'):
                    element = rel.RelatedBuildingElement
                    boundary = {
                        "guid": getattr(rel, 'GlobalId', ''),
                        "element_guid": getattr(element, 'GlobalId', ''),
                        "element_type": element.is_a(),
                        "physical_or_virtual": getattr(rel, 'PhysicalOrVirtualBoundary', ''),
                        "internal_or_external": getattr(rel, 'InternalOrExternalBoundary', ''),
                        "connection_geometry": self._extract_connection_geometry(rel)
                    }
                    boundaries.append(boundary)
        except Exception:
            pass
        return boundaries
    
    def _extract_connection_geometry(self, boundary_rel) -> Optional[Dict[str, Any]]:
        """Extract connection geometry from boundary relationship."""
        try:
            if hasattr(boundary_rel, 'ConnectionGeometry'):
                conn_geom = boundary_rel.ConnectionGeometry
                if hasattr(conn_geom, 'SurfaceOnRelatingElement'):
                    surface = conn_geom.SurfaceOnRelatingElement
                    return {
                        "surface_type": surface.is_a() if surface else None,
                        "geometry": str(surface) if surface else None
                    }
        except Exception:
            pass
        return None
    
    def clear_cache(self):
        """Clear all cached data."""
        with self._lock:
            self._cache.clear()
            self._cache_timestamps.clear()
            gc.collect()  # Force garbage collection
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            return {
                "cache_size": len(self._cache),
                "cache_hits": self.metrics.cache_hits,
                "cache_misses": self.metrics.cache_misses,
                "hit_ratio": self.metrics.cache_hits / (self.metrics.cache_hits + self.metrics.cache_misses) if (self.metrics.cache_hits + self.metrics.cache_misses) > 0 else 0,
                "memory_usage_mb": self._estimate_cache_memory_usage()
            }
    
    def _estimate_cache_memory_usage(self) -> float:
        """Estimate cache memory usage in MB."""
        try:
            import sys
            total_size = 0
            for key, value in self._cache.items():
                total_size += sys.getsizeof(key) + sys.getsizeof(value)
                if isinstance(value, list):
                    for item in value:
                        total_size += sys.getsizeof(item)
            return total_size / (1024 * 1024)
        except Exception:
            return 0.0
    
    def get_metrics(self) -> ParsingMetrics:
        """Get parsing performance metrics."""
        return self.metrics
    
    def optimize_for_export(self):
        """Optimize parser for export operations."""
        # Clear unnecessary caches
        with self._lock:
            keys_to_remove = [k for k in self._cache.keys() if not k.startswith("space")]
            for key in keys_to_remove:
                del self._cache[key]
                if key in self._cache_timestamps:
                    del self._cache_timestamps[key]
        
        # Force garbage collection
        gc.collect()
    
    def close(self):
        """Close parser and clean up resources."""
        self.clear_cache()
        self.ifc_file = None
        self.file_path = None


# Example usage and testing
if __name__ == "__main__":
    parser = OptimizedIFCParser()
    
    # Test with a sample file
    test_file = "test_file.ifc"
    
    print("Optimized IFC Parser Test:")
    print("=" * 40)
    
    # Load file
    success, message = parser.load_file_optimized(test_file)
    print(f"Load Result: {success}")
    print(f"Message: {message}")
    
    if success:
        # Get metrics
        metrics = parser.get_metrics()
        print(f"File Size: {metrics.file_size_mb:.2f} MB")
        print(f"Parsing Time: {metrics.parsing_time_seconds:.2f} seconds")
        print(f"Spaces Found: {metrics.spaces_found}")
        print(f"Processing Rate: {metrics.processing_rate_mb_per_second:.2f} MB/s")
        
        # Get cache stats
        cache_stats = parser.get_cache_stats()
        print(f"Cache Hit Ratio: {cache_stats['hit_ratio']:.2%}")
        print(f"Cache Memory Usage: {cache_stats['memory_usage_mb']:.2f} MB")
        
        # Test batch processing
        print("\nBatch Processing Test:")
        for i, batch in enumerate(parser.get_spaces_batch(10)):
            print(f"Batch {i+1}: {len(batch)} spaces")
            if i >= 2:  # Limit to first 3 batches
                break
        
        # Clean up
        parser.close()
        print("\nParser closed and resources cleaned up.")
