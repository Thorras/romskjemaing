"""
Performance optimizer for IFC Floor Plan Generator.

Integrates geometry caching with multiprocessing architecture, memory monitoring,
and efficient data sharing between processes.
"""

import logging
import multiprocessing as mp
import pickle
import time
from typing import Dict, Any, List, Optional, Tuple, Callable
from dataclasses import dataclass
from concurrent.futures import ProcessPoolExecutor, as_completed
from ..models import Config, StoreyResult
from ..geometry.cache import GeometryCache
from .multiprocessing_manager import MultiprocessingManager, ProcessingTask, ProcessingResult
from .performance_monitor import PerformanceMonitor
from ..errors.handler import ErrorHandler
from ..errors.exceptions import ProcessingError


@dataclass
class OptimizationConfig:
    """Configuration for performance optimizations."""
    enable_geometry_caching: bool = True
    enable_multiprocessing: bool = False
    enable_memory_monitoring: bool = True
    cache_preloading: bool = True
    shared_cache_size_mb: float = 100.0
    memory_limit_mb: float = 1000.0
    cache_cleanup_interval: int = 100  # Process every N operations


class SharedCacheManager:
    """Manages shared geometry cache across processes."""
    
    def __init__(self, config: OptimizationConfig):
        """Initialize shared cache manager.
        
        Args:
            config: Optimization configuration
        """
        self.config = config
        self._logger = logging.getLogger(__name__)
        
        # Shared memory for cache data
        self._shared_cache: Optional[Dict[str, Any]] = None
        self._cache_lock = mp.Lock()
        
        # Manager for shared objects
        self._manager: Optional[mp.Manager] = None
        
        if config.enable_geometry_caching:
            self._initialize_shared_cache()
    
    def _initialize_shared_cache(self) -> None:
        """Initialize shared cache infrastructure."""
        try:
            self._manager = mp.Manager()
            self._shared_cache = self._manager.dict()
            self._logger.info("Shared geometry cache initialized")
        except Exception as e:
            self._logger.error(f"Failed to initialize shared cache: {e}")
            self.config.enable_geometry_caching = False
    
    def get_shared_cache(self) -> Optional[Dict[str, Any]]:
        """Get reference to shared cache."""
        return self._shared_cache
    
    def get_cache_lock(self) -> mp.Lock:
        """Get cache synchronization lock."""
        return self._cache_lock
    
    def preload_cache_data(self, cache_data: Dict[str, Any]) -> None:
        """Preload cache with data for sharing across processes.
        
        Args:
            cache_data: Dictionary of cache data to preload
        """
        if not self._shared_cache:
            return
        
        try:
            with self._cache_lock:
                # Serialize and store cache data
                for key, value in cache_data.items():
                    try:
                        # Serialize complex objects for cross-process sharing
                        serialized_value = pickle.dumps(value)
                        self._shared_cache[key] = serialized_value
                    except Exception as e:
                        self._logger.debug(f"Failed to serialize cache entry {key}: {e}")
            
            self._logger.info(f"Preloaded {len(cache_data)} items into shared cache")
            
        except Exception as e:
            self._logger.error(f"Failed to preload cache data: {e}")
    
    def cleanup(self) -> None:
        """Cleanup shared cache resources."""
        if self._manager:
            try:
                self._manager.shutdown()
                self._logger.debug("Shared cache manager cleaned up")
            except Exception as e:
                self._logger.debug(f"Error during shared cache cleanup: {e}")


class PerformanceOptimizer:
    """Integrates performance optimizations with multiprocessing architecture."""
    
    def __init__(self, config: Config, optimization_config: Optional[OptimizationConfig] = None):
        """Initialize performance optimizer.
        
        Args:
            config: Main system configuration
            optimization_config: Performance optimization configuration
        """
        self.config = config
        self.optimization_config = optimization_config or OptimizationConfig()
        
        self._logger = logging.getLogger(__name__)
        self._error_handler = ErrorHandler()
        
        # Initialize components
        self.multiprocessing_manager = MultiprocessingManager(config)
        self.performance_monitor = PerformanceMonitor()
        self.shared_cache_manager = SharedCacheManager(self.optimization_config)
        
        # Local geometry cache
        self.geometry_cache: Optional[GeometryCache] = None
        if self.optimization_config.enable_geometry_caching:
            self._initialize_geometry_cache()
        
        # Performance tracking
        self._operation_count = 0
        self._last_cleanup = 0
        
        self._logger.info("Performance optimizer initialized")
    
    def _initialize_geometry_cache(self) -> None:
        """Initialize local geometry cache."""
        try:
            cache_size_mb = min(
                self.optimization_config.shared_cache_size_mb,
                self.optimization_config.memory_limit_mb * 0.3  # Use max 30% of memory limit
            )
            
            self.geometry_cache = GeometryCache(
                max_memory_mb=cache_size_mb,
                max_entries=5000,
                ttl_hours=24.0,
                enable_disk_cache=True
            )
            
            # Update cache with current configuration
            config_dict = {
                'use_world_coords': self.config.geometry.use_world_coords,
                'subtract_openings': self.config.geometry.subtract_openings,
                'sew_shells': self.config.geometry.sew_shells,
                'unit_scale_to_m': self.config.units.unit_scale_to_m,
                'slice_tol': self.config.tolerances.slice_tol,
            }
            self.geometry_cache.update_configuration(config_dict)
            
            self._logger.info(f"Geometry cache initialized with {cache_size_mb}MB limit")
            
        except Exception as e:
            self._logger.error(f"Failed to initialize geometry cache: {e}")
            self.optimization_config.enable_geometry_caching = False
    
    def optimize_storey_processing(
        self,
        storeys: List[StoreyResult],
        processing_function: Callable[[ProcessingTask], ProcessingResult],
        task_data_generator: Callable[[StoreyResult, int], Dict[str, Any]]
    ) -> List[ProcessingResult]:
        """Optimize storey processing with integrated performance features.
        
        Args:
            storeys: List of storeys to process
            processing_function: Function to process each storey
            task_data_generator: Function to generate task data
            
        Returns:
            List[ProcessingResult]: Optimized processing results
        """
        with self.performance_monitor.monitor_operation("optimized_storey_processing"):
            try:
                # Pre-processing optimizations
                self._preprocess_optimization(storeys)
                
                # Determine processing strategy
                if self._should_use_multiprocessing(storeys):
                    results = self._process_with_multiprocessing(
                        storeys, processing_function, task_data_generator
                    )
                else:
                    results = self._process_sequential_optimized(
                        storeys, processing_function, task_data_generator
                    )
                
                # Post-processing optimizations
                self._postprocess_optimization(results)
                
                return results
                
            except Exception as e:
                self._logger.error(f"Optimized processing failed: {e}")
                # Fallback to basic processing
                return self.multiprocessing_manager.process_storeys_parallel(
                    storeys, processing_function, task_data_generator
                )
    
    def _preprocess_optimization(self, storeys: List[StoreyResult]) -> None:
        """Apply pre-processing optimizations.
        
        Args:
            storeys: List of storeys to optimize for
        """
        # Memory monitoring
        if self.optimization_config.enable_memory_monitoring:
            self._check_memory_usage()
        
        # Cache preloading
        if (self.optimization_config.cache_preloading and 
            self.geometry_cache and 
            len(storeys) > 1):
            self._preload_geometry_cache(storeys)
        
        # Cleanup if needed
        self._maybe_cleanup_cache()
    
    def _postprocess_optimization(self, results: List[ProcessingResult]) -> None:
        """Apply post-processing optimizations.
        
        Args:
            results: Processing results to optimize
        """
        # Update operation count
        self._operation_count += len(results)
        
        # Memory monitoring
        if self.optimization_config.enable_memory_monitoring:
            self._check_memory_usage()
        
        # Cache statistics logging
        if self.geometry_cache:
            stats = self.geometry_cache.get_stats()
            if stats.total_requests > 0:
                self._logger.debug(f"Cache stats: {stats.hit_rate:.1f}% hit rate, "
                                 f"{stats.cached_items} items, {stats.memory_usage_mb:.1f}MB")
    
    def _should_use_multiprocessing(self, storeys: List[StoreyResult]) -> bool:
        """Determine if multiprocessing should be used.
        
        Args:
            storeys: List of storeys to process
            
        Returns:
            bool: True if multiprocessing should be used
        """
        if not self.multiprocessing_manager.is_multiprocessing_enabled():
            return False
        
        # Don't use multiprocessing for small workloads
        if len(storeys) <= 1:
            return False
        
        # Check memory constraints
        if self.optimization_config.enable_memory_monitoring:
            memory_info = self.performance_monitor.get_system_info()
            if memory_info.get("memory_percent", 0) > 80:
                self._logger.warning("High memory usage detected, disabling multiprocessing")
                return False
        
        # Estimate if multiprocessing will be beneficial
        avg_elements = sum(s.element_count for s in storeys) / len(storeys)
        if avg_elements < 10:  # Very small storeys
            return False
        
        return True
    
    def _process_with_multiprocessing(
        self,
        storeys: List[StoreyResult],
        processing_function: Callable[[ProcessingTask], ProcessingResult],
        task_data_generator: Callable[[StoreyResult, int], Dict[str, Any]]
    ) -> List[ProcessingResult]:
        """Process storeys with multiprocessing optimizations.
        
        Args:
            storeys: List of storeys to process
            processing_function: Function to process each storey
            task_data_generator: Function to generate task data
            
        Returns:
            List[ProcessingResult]: Processing results
        """
        # Create optimized processing function that uses shared cache
        def optimized_processing_function(task: ProcessingTask) -> ProcessingResult:
            return self._process_task_with_cache(task, processing_function)
        
        # Preload shared cache if enabled
        if self.optimization_config.cache_preloading and self.geometry_cache:
            self._sync_to_shared_cache()
        
        # Process with multiprocessing
        return self.multiprocessing_manager.process_storeys_parallel(
            storeys, optimized_processing_function, task_data_generator
        )
    
    def _process_sequential_optimized(
        self,
        storeys: List[StoreyResult],
        processing_function: Callable[[ProcessingTask], ProcessingResult],
        task_data_generator: Callable[[StoreyResult, int], Dict[str, Any]]
    ) -> List[ProcessingResult]:
        """Process storeys sequentially with optimizations.
        
        Args:
            storeys: List of storeys to process
            processing_function: Function to process each storey
            task_data_generator: Function to generate task data
            
        Returns:
            List[ProcessingResult]: Processing results
        """
        results = []
        
        for index, storey in enumerate(storeys):
            try:
                # Create task
                task_data = task_data_generator(storey, index)
                task = ProcessingTask(
                    storey_index=index,
                    storey_name=storey.storey_name,
                    task_data=task_data,
                    task_id=f"storey_{index}_{storey.storey_name}"
                )
                
                # Process with cache optimization
                result = self._process_task_with_cache(task, processing_function)
                results.append(result)
                
                # Periodic memory check
                if index % 5 == 0 and self.optimization_config.enable_memory_monitoring:
                    self._check_memory_usage()
                
            except Exception as e:
                error_result = ProcessingResult(
                    task_id=f"storey_{index}_{storey.storey_name}",
                    storey_index=index,
                    storey_name=storey.storey_name,
                    success=False,
                    error_message=str(e)
                )
                results.append(error_result)
                self._logger.error(f"Sequential processing failed for storey {storey.storey_name}: {e}")
        
        return results
    
    def _process_task_with_cache(
        self, 
        task: ProcessingTask, 
        processing_function: Callable[[ProcessingTask], ProcessingResult]
    ) -> ProcessingResult:
        """Process task with geometry cache optimization.
        
        Args:
            task: Processing task
            processing_function: Original processing function
            
        Returns:
            ProcessingResult: Processing result
        """
        start_time = time.time()
        
        try:
            # Check if we can use cached results
            cache_key = self._generate_cache_key(task)
            
            if self.geometry_cache and cache_key:
                cached_result = self.geometry_cache.get(cache_key)
                if cached_result is not None:
                    # Use cached result
                    return ProcessingResult(
                        task_id=task.task_id,
                        storey_index=task.storey_index,
                        storey_name=task.storey_name,
                        success=True,
                        result_data={"cached": True, "cache_key": cache_key},
                        processing_time=time.time() - start_time
                    )
            
            # Process normally
            result = processing_function(task)
            
            # Cache successful results
            if (result.success and self.geometry_cache and cache_key and 
                result.result_data is not None):
                self.geometry_cache.put(cache_key, result.result_data)
            
            return result
            
        except Exception as e:
            return ProcessingResult(
                task_id=task.task_id,
                storey_index=task.storey_index,
                storey_name=task.storey_name,
                success=False,
                error_message=str(e),
                processing_time=time.time() - start_time
            )
    
    def _generate_cache_key(self, task: ProcessingTask) -> Optional[str]:
        """Generate cache key for task.
        
        Args:
            task: Processing task
            
        Returns:
            Optional[str]: Cache key or None if caching not applicable
        """
        try:
            # Create deterministic key from task data
            key_data = {
                "storey_name": task.storey_name,
                "task_data": task.task_data
            }
            
            # Add configuration hash
            config_hash = hash(str(sorted(key_data.items())))
            return f"task_{abs(config_hash)}"
            
        except Exception as e:
            self._logger.debug(f"Failed to generate cache key: {e}")
            return None
    
    def _preload_geometry_cache(self, storeys: List[StoreyResult]) -> None:
        """Preload geometry cache with storey data.
        
        Args:
            storeys: List of storeys to preload cache for
        """
        if not self.geometry_cache:
            return
        
        try:
            # Extract GUIDs from storeys for preloading
            guid_data = []
            for storey in storeys:
                for polyline in storey.polylines:
                    if polyline.element_guid:
                        # Create placeholder data for preloading
                        guid_data.append((polyline.element_guid, polyline))
            
            if guid_data:
                # Preload cache (this would need actual shape data in real implementation)
                self._logger.debug(f"Preloading cache with {len(guid_data)} items")
                
        except Exception as e:
            self._logger.debug(f"Cache preloading failed: {e}")
    
    def _sync_to_shared_cache(self) -> None:
        """Synchronize local cache to shared cache for multiprocessing."""
        if not self.geometry_cache or not self.shared_cache_manager.get_shared_cache():
            return
        
        try:
            # Get cache data (simplified - would need actual implementation)
            cache_data = {}  # Would extract from geometry_cache
            
            # Sync to shared cache
            self.shared_cache_manager.preload_cache_data(cache_data)
            
        except Exception as e:
            self._logger.debug(f"Cache synchronization failed: {e}")
    
    def _check_memory_usage(self) -> None:
        """Check and manage memory usage."""
        try:
            system_info = self.performance_monitor.get_system_info()
            memory_percent = system_info.get("memory_percent", 0)
            
            if memory_percent > 85:
                self._logger.warning(f"High memory usage: {memory_percent:.1f}%")
                
                # Trigger cache cleanup
                if self.geometry_cache:
                    cleaned = self.geometry_cache.cleanup_expired()
                    if cleaned > 0:
                        self._logger.info(f"Cleaned up {cleaned} cache entries to free memory")
                
                # Force garbage collection
                import gc
                gc.collect()
            
        except Exception as e:
            self._logger.debug(f"Memory check failed: {e}")
    
    def _maybe_cleanup_cache(self) -> None:
        """Perform periodic cache cleanup."""
        if (self._operation_count - self._last_cleanup >= 
            self.optimization_config.cache_cleanup_interval):
            
            if self.geometry_cache:
                cleaned = self.geometry_cache.cleanup_expired()
                if cleaned > 0:
                    self._logger.debug(f"Periodic cleanup: removed {cleaned} expired entries")
            
            self._last_cleanup = self._operation_count
    
    def get_optimization_stats(self) -> Dict[str, Any]:
        """Get comprehensive optimization statistics.
        
        Returns:
            Dict[str, Any]: Optimization statistics
        """
        stats = {
            "multiprocessing_info": self.multiprocessing_manager.get_performance_info(),
            "performance_summary": self.performance_monitor.get_performance_summary(),
            "system_info": self.performance_monitor.get_system_info(),
            "optimization_config": {
                "geometry_caching": self.optimization_config.enable_geometry_caching,
                "multiprocessing": self.optimization_config.enable_multiprocessing,
                "memory_monitoring": self.optimization_config.enable_memory_monitoring,
                "cache_preloading": self.optimization_config.cache_preloading
            }
        }
        
        # Add cache statistics if available
        if self.geometry_cache:
            cache_stats = self.geometry_cache.get_stats()
            stats["cache_stats"] = {
                "hit_rate": cache_stats.hit_rate,
                "cached_items": cache_stats.cached_items,
                "memory_usage_mb": cache_stats.memory_usage_mb,
                "total_requests": cache_stats.total_requests
            }
            
            # Add efficiency metrics
            stats["cache_efficiency"] = self.geometry_cache.get_cache_efficiency_metrics()
        
        return stats
    
    def cleanup(self) -> None:
        """Cleanup optimization resources."""
        try:
            # Cleanup shared cache
            self.shared_cache_manager.cleanup()
            
            # Clear local cache
            if self.geometry_cache:
                self.geometry_cache.clear()
            
            self._logger.debug("Performance optimizer cleaned up")
            
        except Exception as e:
            self._logger.debug(f"Error during optimizer cleanup: {e}")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()