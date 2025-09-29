"""
Optimized IFC File Reader

Enhanced IFC file reader with performance optimizations, caching, and batch processing.
"""

import os
import time
from typing import Tuple, Optional, List, Dict, Any, Iterator
from dataclasses import dataclass

import ifcopenshell
from ..utils.enhanced_logging import enhanced_logger
from .optimized_ifc_parser import OptimizedIFCParser, CacheConfig
from .performance_monitor import PerformanceMonitor
from .batch_processor import BatchProcessor, BatchConfig


@dataclass
class OptimizationConfig:
    """Configuration for IFC file reading optimizations."""
    
    # File size thresholds (MB)
    small_file_threshold: float = 10.0
    medium_file_threshold: float = 100.0
    
    # Caching configuration
    enable_caching: bool = True
    cache_size: int = 128
    cache_ttl: int = 3600
    
    # Batch processing configuration
    batch_size: int = 100
    max_workers: int = 4
    memory_threshold_mb: float = 1000.0
    
    # Performance monitoring
    enable_monitoring: bool = True
    monitoring_interval: float = 0.1


class OptimizedIfcFileReader:
    """Optimized IFC file reader with performance enhancements."""
    
    def __init__(self, config: Optional[OptimizationConfig] = None):
        """Initialize optimized IFC file reader."""
        self.config = config or OptimizationConfig()
        self.parser = OptimizedIFCParser(
            CacheConfig(
                max_size=self.config.cache_size,
                ttl_seconds=self.config.cache_ttl,
                enable_geometry_cache=self.config.enable_caching,
                enable_property_cache=self.config.enable_caching,
                enable_relationship_cache=self.config.enable_caching
            )
        )
        self.performance_monitor = PerformanceMonitor(
            monitoring_interval=self.config.monitoring_interval
        )
        self.batch_processor = BatchProcessor(
            BatchConfig(
                batch_size=self.config.batch_size,
                max_workers=self.config.max_workers,
                memory_threshold_mb=self.config.memory_threshold_mb
            )
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
            # Start performance monitoring
            if self.config.enable_monitoring:
                self.performance_monitor.start_monitoring()
            
            # Load file with optimized parser
            success, message = self.parser.load_file_optimized(file_path)
            
            if success:
                # Get file size for optimization decisions
                file_size = os.path.getsize(file_path)
                file_size_mb = file_size / (1024 * 1024)
                
                # Apply optimizations based on file size
                if file_size_mb < self.config.small_file_threshold:
                    self._optimize_for_small_files()
                elif file_size_mb < self.config.medium_file_threshold:
                    self._optimize_for_medium_files()
                else:
                    self._optimize_for_large_files()
                
                # Stop performance monitoring
                if self.config.enable_monitoring:
                    self.performance_monitor.stop_monitoring()
                
                # Get performance metrics
                metrics = self.parser.get_metrics()
                enhanced_logger.logger.info(
                    f"File loaded with optimizations: {metrics.file_size_mb:.1f}MB "
                    f"in {metrics.parsing_time_seconds:.2f}s "
                    f"({metrics.processing_rate_mb_per_second:.2f}MB/s)"
                )
            
            enhanced_logger.finish_operation_timing(operation_id)
            return success, message
            
        except Exception as e:
            if self.config.enable_monitoring:
                self.performance_monitor.stop_monitoring()
            enhanced_logger.finish_operation_timing(operation_id)
            return False, f"Error loading file: {str(e)}"
    
    def get_spaces_optimized(self) -> List[Any]:
        """
        Get spaces with optimizations.
        
        Returns:
            List of space entities
        """
        if not self.parser.ifc_file:
            return []
        
        try:
            # Use cached spaces if available
            spaces = self.parser._get_spaces_cached()
            
            # Apply additional optimizations
            if len(spaces) > 1000:
                # For large numbers of spaces, use batch processing
                return self._process_spaces_in_batches(spaces)
            else:
                return spaces
                
        except Exception as e:
            enhanced_logger.logger.error(f"Error getting spaces: {e}")
            return []
    
    def get_space_properties_optimized(self, space_guid: str) -> Optional[Dict[str, Any]]:
        """
        Get space properties with caching.
        
        Args:
            space_guid: GUID of the space
            
        Returns:
            Dictionary of space properties or None
        """
        return self.parser.get_space_properties_cached(space_guid)
    
    def get_space_boundaries_optimized(self, space_guid: str) -> List[Dict[str, Any]]:
        """
        Get space boundaries with caching.
        
        Args:
            space_guid: GUID of the space
            
        Returns:
            List of boundary dictionaries
        """
        return self.parser.get_space_boundaries_cached(space_guid)
    
    def process_spaces_batch(self, processor_func, batch_size: Optional[int] = None) -> List[Any]:
        """
        Process spaces in batches for optimal performance.
        
        Args:
            processor_func: Function to process each space
            batch_size: Optional batch size override
            
        Returns:
            List of processed results
        """
        spaces = self.get_spaces_optimized()
        
        if not spaces:
            return []
        
        # Configure batch processor
        if batch_size:
            self.batch_processor.config.batch_size = batch_size
        
        # Process spaces in batches
        return self.batch_processor.process_spaces_batch(spaces, processor_func)
    
    def process_spaces_streaming(self, processor_func) -> Iterator[Any]:
        """
        Process spaces with streaming for memory efficiency.
        
        Args:
            processor_func: Function to process each space
            
        Yields:
            Processed results as they become available
        """
        spaces = self.get_spaces_optimized()
        
        if not spaces:
            return
        
        # Process with streaming
        yield from self.batch_processor.process_with_streaming(
            iter(spaces), processor_func
        )
    
    def _optimize_for_small_files(self):
        """Apply optimizations for small files."""
        enhanced_logger.logger.info("Applying optimizations for small files")
        
        # Disable caching for small files (not needed)
        self.parser.cache_config.enable_geometry_cache = False
        self.parser.cache_config.enable_property_cache = False
        
        # Use smaller batch sizes
        self.batch_processor.config.batch_size = 50
        
        # Disable multiprocessing
        self.batch_processor.config.use_multiprocessing = False
    
    def _optimize_for_medium_files(self):
        """Apply optimizations for medium files."""
        enhanced_logger.logger.info("Applying optimizations for medium files")
        
        # Enable selective caching
        self.parser.cache_config.enable_geometry_cache = True
        self.parser.cache_config.enable_property_cache = True
        self.parser.cache_config.enable_relationship_cache = False
        
        # Use moderate batch sizes
        self.batch_processor.config.batch_size = 100
        
        # Enable threading
        self.batch_processor.config.use_multiprocessing = False
    
    def _optimize_for_large_files(self):
        """Apply optimizations for large files."""
        enhanced_logger.logger.info("Applying optimizations for large files")
        
        # Enable all caching
        self.parser.cache_config.enable_geometry_cache = True
        self.parser.cache_config.enable_property_cache = True
        self.parser.cache_config.enable_relationship_cache = True
        
        # Use smaller batch sizes for memory efficiency
        self.batch_processor.config.batch_size = 50
        
        # Enable multiprocessing
        self.batch_processor.config.use_multiprocessing = True
        
        # Reduce memory threshold
        self.batch_processor.config.memory_threshold_mb = 500.0
    
    def _process_spaces_in_batches(self, spaces: List[Any]) -> List[Any]:
        """Process spaces in batches for large files."""
        enhanced_logger.logger.info(f"Processing {len(spaces)} spaces in batches")
        
        # Use batch processor
        return self.batch_processor.process_spaces_batch(spaces, lambda x: x)
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics."""
        parser_metrics = self.parser.get_metrics()
        cache_stats = self.parser.get_cache_stats()
        processing_stats = self.batch_processor.get_processing_stats()
        
        return {
            "file_metrics": {
                "size_mb": parser_metrics.file_size_mb,
                "parsing_time": parser_metrics.parsing_time_seconds,
                "processing_rate": parser_metrics.processing_rate_mb_per_second,
                "spaces_found": parser_metrics.spaces_found
            },
            "cache_metrics": cache_stats,
            "processing_metrics": processing_stats,
            "optimization_config": {
                "caching_enabled": self.config.enable_caching,
                "batch_size": self.config.batch_size,
                "max_workers": self.config.max_workers,
                "memory_threshold": self.config.memory_threshold_mb
            }
        }
    
    def get_optimization_recommendations(self) -> List[str]:
        """Get optimization recommendations based on current performance."""
        recommendations = []
        
        # Get current metrics
        metrics = self.get_performance_metrics()
        
        # Cache recommendations
        cache_hit_ratio = metrics["cache_metrics"]["hit_ratio"]
        if cache_hit_ratio < 0.5:
            recommendations.append("Low cache hit ratio - consider increasing cache size or TTL")
        
        # Memory recommendations
        memory_usage = metrics["cache_metrics"]["memory_usage_mb"]
        if memory_usage > 500:
            recommendations.append("High cache memory usage - consider reducing cache size")
        
        # Processing recommendations
        processing_rate = metrics["file_metrics"]["processing_rate"]
        if processing_rate < 1.0:
            recommendations.append("Slow processing rate - consider enabling multiprocessing or reducing batch size")
        
        # File size recommendations
        file_size = metrics["file_metrics"]["size_mb"]
        if file_size > 100:
            recommendations.append("Large file detected - consider using streaming processing")
        
        return recommendations
    
    def optimize_performance(self):
        """Apply performance optimizations based on current metrics."""
        enhanced_logger.logger.info("Applying performance optimizations")
        
        # Get current metrics
        metrics = self.get_performance_metrics()
        
        # Apply optimizations based on metrics
        file_size = metrics["file_metrics"]["size_mb"]
        
        if file_size < 10:
            self._optimize_for_small_files()
        elif file_size < 100:
            self._optimize_for_medium_files()
        else:
            self._optimize_for_large_files()
        
        # Apply system optimizations
        self.performance_monitor.optimize_system()
        
        # Clear cache if memory usage is high
        cache_memory = metrics["cache_metrics"]["memory_usage_mb"]
        if cache_memory > 1000:
            self.parser.clear_cache()
            enhanced_logger.logger.info("Cache cleared due to high memory usage")
    
    def cleanup(self):
        """Clean up all resources."""
        enhanced_logger.logger.info("Cleaning up optimized IFC file reader")
        
        # Clean up parser
        self.parser.close()
        
        # Clean up performance monitor
        self.performance_monitor.cleanup()
        
        # Clean up batch processor
        self.batch_processor.cleanup()
    
    def is_loaded(self) -> bool:
        """Check if a file is currently loaded."""
        return self.parser.ifc_file is not None
    
    def get_file_info(self) -> Optional[Dict[str, Any]]:
        """Get information about the loaded file."""
        if not self.parser.ifc_file:
            return None
        
        try:
            return {
                "file_path": self.parser.file_path,
                "schema": self.parser.ifc_file.schema,
                "total_entities": len(self.parser.ifc_file),
                "spaces_count": self.parser.metrics.spaces_found,
                "file_size_mb": self.parser.metrics.file_size_mb,
                "parsing_time": self.parser.metrics.parsing_time_seconds
            }
        except Exception as e:
            return {"error": f"Error getting file info: {e}"}


# Example usage and testing
if __name__ == "__main__":
    # Test optimized IFC file reader
    reader = OptimizedIfcFileReader()
    
    print("Optimized IFC File Reader Test:")
    print("=" * 40)
    
    # Test file loading
    test_file = "test_file.ifc"
    success, message = reader.load_file_optimized(test_file)
    
    print(f"Load Result: {success}")
    print(f"Message: {message}")
    
    if success:
        # Get file info
        file_info = reader.get_file_info()
        print(f"File Info: {file_info}")
        
        # Get performance metrics
        metrics = reader.get_performance_metrics()
        print(f"Performance Metrics: {metrics}")
        
        # Get optimization recommendations
        recommendations = reader.get_optimization_recommendations()
        if recommendations:
            print("Recommendations:")
            for rec in recommendations:
                print(f"- {rec}")
        
        # Test space processing
        spaces = reader.get_spaces_optimized()
        print(f"Found {len(spaces)} spaces")
        
        # Test batch processing
        def process_space(space):
            return f"Processed_{space}"
        
        results = reader.process_spaces_batch(process_space, batch_size=50)
        print(f"Processed {len(results)} spaces in batches")
        
        # Cleanup
        reader.cleanup()
        print("Reader cleaned up")
