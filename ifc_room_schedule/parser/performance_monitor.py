"""
Performance Monitor for IFC Parsing

Monitors and optimizes IFC parsing performance with detailed metrics and recommendations.
"""

import time
import psutil
import gc
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import threading
from contextlib import contextmanager

from ..utils.enhanced_logging import enhanced_logger


@dataclass
class PerformanceSnapshot:
    """Snapshot of system performance at a point in time."""
    
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_available_mb: float
    memory_used_mb: float
    disk_io_read_mb: float
    disk_io_write_mb: float
    process_memory_mb: float
    process_cpu_percent: float


@dataclass
class ParsingPerformanceMetrics:
    """Comprehensive performance metrics for IFC parsing."""
    
    # File metrics
    file_size_mb: float
    file_entities_count: int
    spaces_count: int
    
    # Timing metrics
    total_parsing_time: float
    file_loading_time: float
    entity_processing_time: float
    cache_operations_time: float
    
    # Memory metrics
    peak_memory_mb: float
    average_memory_mb: float
    memory_growth_mb: float
    garbage_collections: int
    
    # Cache metrics
    cache_hits: int
    cache_misses: int
    cache_hit_ratio: float
    cache_memory_mb: float
    
    # Performance rates
    entities_per_second: float
    spaces_per_second: float
    mb_per_second: float
    
    # System metrics
    average_cpu_percent: float
    peak_cpu_percent: float
    system_memory_usage_percent: float


class PerformanceMonitor:
    """Monitors and optimizes IFC parsing performance."""
    
    def __init__(self, monitoring_interval: float = 0.1):
        """Initialize performance monitor."""
        self.monitoring_interval = monitoring_interval
        self.snapshots: List[PerformanceSnapshot] = []
        self.monitoring = False
        self.monitor_thread = None
        self.start_time = None
        self.end_time = None
        
        # Performance thresholds
        self.memory_warning_threshold = 80.0  # 80% memory usage
        self.cpu_warning_threshold = 90.0     # 90% CPU usage
        self.slow_processing_threshold = 1.0  # 1 MB/s processing rate
    
    def start_monitoring(self):
        """Start performance monitoring."""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.start_time = time.time()
        self.snapshots.clear()
        
        # Start monitoring thread
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        enhanced_logger.logger.info("Performance monitoring started")
    
    def stop_monitoring(self):
        """Stop performance monitoring."""
        if not self.monitoring:
            return
        
        self.monitoring = False
        self.end_time = time.time()
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)
        
        enhanced_logger.logger.info("Performance monitoring stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop."""
        while self.monitoring:
            try:
                snapshot = self._take_snapshot()
                self.snapshots.append(snapshot)
                
                # Check for performance warnings
                self._check_performance_warnings(snapshot)
                
                time.sleep(self.monitoring_interval)
            except Exception as e:
                enhanced_logger.logger.error(f"Error in monitoring loop: {e}")
                break
    
    def _take_snapshot(self) -> PerformanceSnapshot:
        """Take a performance snapshot."""
        try:
            # System metrics
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            disk_io = psutil.disk_io_counters()
            
            # Process metrics
            process = psutil.Process()
            process_memory = process.memory_info()
            process_cpu = process.cpu_percent()
            
            return PerformanceSnapshot(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_available_mb=memory.available / (1024 * 1024),
                memory_used_mb=memory.used / (1024 * 1024),
                disk_io_read_mb=disk_io.read_bytes / (1024 * 1024) if disk_io else 0,
                disk_io_write_mb=disk_io.write_bytes / (1024 * 1024) if disk_io else 0,
                process_memory_mb=process_memory.rss / (1024 * 1024),
                process_cpu_percent=process_cpu
            )
        except Exception as e:
            enhanced_logger.logger.warning(f"Error taking performance snapshot: {e}")
            return PerformanceSnapshot(
                timestamp=datetime.now(),
                cpu_percent=0.0,
                memory_percent=0.0,
                memory_available_mb=0.0,
                memory_used_mb=0.0,
                disk_io_read_mb=0.0,
                disk_io_write_mb=0.0,
                process_memory_mb=0.0,
                process_cpu_percent=0.0
            )
    
    def _check_performance_warnings(self, snapshot: PerformanceSnapshot):
        """Check for performance warnings and log them."""
        warnings = []
        
        # Memory warnings
        if snapshot.memory_percent > self.memory_warning_threshold:
            warnings.append(f"High memory usage: {snapshot.memory_percent:.1f}%")
        
        # CPU warnings
        if snapshot.cpu_percent > self.cpu_warning_threshold:
            warnings.append(f"High CPU usage: {snapshot.cpu_percent:.1f}%")
        
        # Process memory warnings
        if snapshot.process_memory_mb > 1000:  # 1GB
            warnings.append(f"High process memory: {snapshot.process_memory_mb:.1f}MB")
        
        # Log warnings
        for warning in warnings:
            enhanced_logger.logger.warning(f"Performance warning: {warning}")
    
    @contextmanager
    def monitor_operation(self, operation_name: str):
        """Context manager for monitoring specific operations."""
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / (1024 * 1024)
        start_gc_count = len(gc.get_objects())
        
        enhanced_logger.logger.info(f"Starting operation: {operation_name}")
        
        try:
            yield
        finally:
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss / (1024 * 1024)
            end_gc_count = len(gc.get_objects())
            
            duration = end_time - start_time
            memory_delta = end_memory - start_memory
            gc_delta = end_gc_count - start_gc_count
            
            enhanced_logger.logger.info(
                f"Operation '{operation_name}' completed: "
                f"{duration:.2f}s, memory: {memory_delta:+.1f}MB, "
                f"objects: {gc_delta:+d}"
            )
    
    def get_performance_metrics(self, file_size_mb: float, entities_count: int, 
                              spaces_count: int, cache_hits: int = 0, 
                              cache_misses: int = 0) -> ParsingPerformanceMetrics:
        """Calculate comprehensive performance metrics."""
        if not self.snapshots:
            return ParsingPerformanceMetrics(
                file_size_mb=file_size_mb,
                file_entities_count=entities_count,
                spaces_count=spaces_count,
                total_parsing_time=0.0,
                file_loading_time=0.0,
                entity_processing_time=0.0,
                cache_operations_time=0.0,
                peak_memory_mb=0.0,
                average_memory_mb=0.0,
                memory_growth_mb=0.0,
                garbage_collections=0,
                cache_hits=cache_hits,
                cache_misses=cache_misses,
                cache_hit_ratio=0.0,
                cache_memory_mb=0.0,
                entities_per_second=0.0,
                spaces_per_second=0.0,
                mb_per_second=0.0,
                average_cpu_percent=0.0,
                peak_cpu_percent=0.0,
                system_memory_usage_percent=0.0
            )
        
        # Calculate timing metrics
        total_time = (self.end_time - self.start_time) if self.end_time and self.start_time else 0.0
        
        # Calculate memory metrics
        memory_values = [s.process_memory_mb for s in self.snapshots]
        peak_memory = max(memory_values) if memory_values else 0.0
        average_memory = sum(memory_values) / len(memory_values) if memory_values else 0.0
        memory_growth = (memory_values[-1] - memory_values[0]) if len(memory_values) > 1 else 0.0
        
        # Calculate CPU metrics
        cpu_values = [s.cpu_percent for s in self.snapshots]
        average_cpu = sum(cpu_values) / len(cpu_values) if cpu_values else 0.0
        peak_cpu = max(cpu_values) if cpu_values else 0.0
        
        # Calculate system memory usage
        system_memory_values = [s.memory_percent for s in self.snapshots]
        system_memory_usage = sum(system_memory_values) / len(system_memory_values) if system_memory_values else 0.0
        
        # Calculate cache metrics
        total_cache_ops = cache_hits + cache_misses
        cache_hit_ratio = cache_hits / total_cache_ops if total_cache_ops > 0 else 0.0
        
        # Calculate performance rates
        entities_per_second = entities_count / total_time if total_time > 0 else 0.0
        spaces_per_second = spaces_count / total_time if total_time > 0 else 0.0
        mb_per_second = file_size_mb / total_time if total_time > 0 else 0.0
        
        return ParsingPerformanceMetrics(
            file_size_mb=file_size_mb,
            file_entities_count=entities_count,
            spaces_count=spaces_count,
            total_parsing_time=total_time,
            file_loading_time=total_time * 0.3,  # Estimate
            entity_processing_time=total_time * 0.5,  # Estimate
            cache_operations_time=total_time * 0.2,  # Estimate
            peak_memory_mb=peak_memory,
            average_memory_mb=average_memory,
            memory_growth_mb=memory_growth,
            garbage_collections=0,  # Would need to track GC calls
            cache_hits=cache_hits,
            cache_misses=cache_misses,
            cache_hit_ratio=cache_hit_ratio,
            cache_memory_mb=0.0,  # Would need cache size tracking
            entities_per_second=entities_per_second,
            spaces_per_second=spaces_per_second,
            mb_per_second=mb_per_second,
            average_cpu_percent=average_cpu,
            peak_cpu_percent=peak_cpu,
            system_memory_usage_percent=system_memory_usage
        )
    
    def get_performance_recommendations(self, metrics: ParsingPerformanceMetrics) -> List[str]:
        """Get performance optimization recommendations."""
        recommendations = []
        
        # Memory recommendations
        if metrics.peak_memory_mb > 1000:  # 1GB
            recommendations.append("Consider using batch processing for large files")
        
        if metrics.memory_growth_mb > 500:  # 500MB growth
            recommendations.append("Memory usage is growing significantly - check for memory leaks")
        
        # CPU recommendations
        if metrics.average_cpu_percent > 80:
            recommendations.append("High CPU usage detected - consider reducing processing complexity")
        
        # Processing rate recommendations
        if metrics.mb_per_second < self.slow_processing_threshold:
            recommendations.append("Processing rate is slow - consider enabling caching or reducing data complexity")
        
        # Cache recommendations
        if metrics.cache_hit_ratio < 0.5 and metrics.cache_hits + metrics.cache_misses > 100:
            recommendations.append("Low cache hit ratio - consider adjusting cache strategy")
        
        # System recommendations
        if metrics.system_memory_usage_percent > 90:
            recommendations.append("System memory usage is very high - close other applications")
        
        return recommendations
    
    def get_performance_summary(self, metrics: ParsingPerformanceMetrics) -> Dict[str, Any]:
        """Get a summary of performance metrics."""
        return {
            "file_info": {
                "size_mb": metrics.file_size_mb,
                "entities": metrics.file_entities_count,
                "spaces": metrics.spaces_count
            },
            "timing": {
                "total_time": f"{metrics.total_parsing_time:.2f}s",
                "entities_per_second": f"{metrics.entities_per_second:.0f}",
                "spaces_per_second": f"{metrics.spaces_per_second:.0f}",
                "mb_per_second": f"{metrics.mb_per_second:.2f}"
            },
            "memory": {
                "peak_mb": f"{metrics.peak_memory_mb:.1f}",
                "average_mb": f"{metrics.average_memory_mb:.1f}",
                "growth_mb": f"{metrics.memory_growth_mb:+.1f}"
            },
            "system": {
                "average_cpu": f"{metrics.average_cpu_percent:.1f}%",
                "peak_cpu": f"{metrics.peak_cpu_percent:.1f}%",
                "memory_usage": f"{metrics.system_memory_usage_percent:.1f}%"
            },
            "cache": {
                "hit_ratio": f"{metrics.cache_hit_ratio:.1%}",
                "hits": metrics.cache_hits,
                "misses": metrics.cache_misses
            }
        }
    
    def optimize_system(self):
        """Apply system optimizations."""
        enhanced_logger.logger.info("Applying system optimizations...")
        
        # Force garbage collection
        collected = gc.collect()
        enhanced_logger.logger.info(f"Garbage collection freed {collected} objects")
        
        # Set process priority to high (if possible)
        try:
            process = psutil.Process()
            process.nice(psutil.HIGH_PRIORITY_CLASS)
            enhanced_logger.logger.info("Process priority set to high")
        except Exception as e:
            enhanced_logger.logger.warning(f"Could not set process priority: {e}")
        
        # Clear system caches (if possible)
        try:
            # This is platform-specific and may require admin privileges
            pass
        except Exception as e:
            enhanced_logger.logger.warning(f"Could not clear system caches: {e}")
    
    def cleanup(self):
        """Clean up monitoring resources."""
        self.stop_monitoring()
        self.snapshots.clear()
        enhanced_logger.logger.info("Performance monitor cleaned up")


# Example usage and testing
if __name__ == "__main__":
    monitor = PerformanceMonitor()
    
    print("Performance Monitor Test:")
    print("=" * 40)
    
    # Start monitoring
    monitor.start_monitoring()
    
    # Simulate some work
    import time
    time.sleep(2)
    
    # Stop monitoring
    monitor.stop_monitoring()
    
    # Get metrics
    metrics = monitor.get_performance_metrics(
        file_size_mb=50.0,
        entities_count=10000,
        spaces_count=100,
        cache_hits=50,
        cache_misses=10
    )
    
    print(f"Total parsing time: {metrics.total_parsing_time:.2f}s")
    print(f"Peak memory: {metrics.peak_memory_mb:.1f}MB")
    print(f"Processing rate: {metrics.mb_per_second:.2f}MB/s")
    print(f"Cache hit ratio: {metrics.cache_hit_ratio:.1%}")
    
    # Get recommendations
    recommendations = monitor.get_performance_recommendations(metrics)
    if recommendations:
        print("\nRecommendations:")
        for rec in recommendations:
            print(f"- {rec}")
    
    # Get summary
    summary = monitor.get_performance_summary(metrics)
    print(f"\nPerformance Summary: {summary}")
    
    # Cleanup
    monitor.cleanup()
