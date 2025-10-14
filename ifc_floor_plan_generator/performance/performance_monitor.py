"""
Performance monitoring for IFC Floor Plan Generator.

Provides performance monitoring, profiling, and optimization recommendations.
"""

import time
import psutil
import logging
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from contextlib import contextmanager
from ..errors.handler import ErrorHandler


@dataclass
class PerformanceMetrics:
    """Performance metrics for a processing operation."""
    operation_name: str
    start_time: float
    end_time: float
    cpu_usage_start: float
    cpu_usage_end: float
    memory_usage_start: float  # MB
    memory_usage_end: float    # MB
    additional_metrics: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration(self) -> float:
        """Get operation duration in seconds."""
        return self.end_time - self.start_time
    
    @property
    def cpu_usage_delta(self) -> float:
        """Get CPU usage change during operation."""
        return self.cpu_usage_end - self.cpu_usage_start
    
    @property
    def memory_usage_delta(self) -> float:
        """Get memory usage change during operation (MB)."""
        return self.memory_usage_end - self.memory_usage_start


class PerformanceMonitor:
    """Monitors performance metrics for multiprocessing operations."""
    
    def __init__(self):
        """Initialize performance monitor."""
        self._logger = logging.getLogger(__name__)
        self._error_handler = ErrorHandler()
        self._metrics_history: List[PerformanceMetrics] = []
        self._current_operation: Optional[str] = None
        self._operation_start_time: Optional[float] = None
        self._operation_start_cpu: Optional[float] = None
        self._operation_start_memory: Optional[float] = None
    
    def start_monitoring(self, operation_name: str) -> None:
        """Start monitoring a performance operation.
        
        Args:
            operation_name: Name of the operation being monitored
        """
        self._current_operation = operation_name
        self._operation_start_time = time.time()
        
        try:
            # Get initial system metrics
            self._operation_start_cpu = psutil.cpu_percent(interval=None)
            memory_info = psutil.virtual_memory()
            self._operation_start_memory = memory_info.used / (1024 * 1024)  # Convert to MB
            
            self._logger.debug(f"Started monitoring operation: {operation_name}")
            
        except Exception as e:
            self._logger.warning(f"Could not collect initial system metrics: {e}")
            self._operation_start_cpu = 0.0
            self._operation_start_memory = 0.0
    
    def stop_monitoring(self, additional_metrics: Optional[Dict[str, Any]] = None) -> PerformanceMetrics:
        """Stop monitoring and return performance metrics.
        
        Args:
            additional_metrics: Optional additional metrics to include
            
        Returns:
            PerformanceMetrics: Collected performance metrics
            
        Raises:
            ValueError: If monitoring was not started
        """
        if self._current_operation is None or self._operation_start_time is None:
            raise ValueError("Performance monitoring was not started")
        
        end_time = time.time()
        
        try:
            # Get final system metrics
            end_cpu = psutil.cpu_percent(interval=None)
            memory_info = psutil.virtual_memory()
            end_memory = memory_info.used / (1024 * 1024)  # Convert to MB
            
        except Exception as e:
            self._logger.warning(f"Could not collect final system metrics: {e}")
            end_cpu = 0.0
            end_memory = 0.0
        
        # Create metrics object
        metrics = PerformanceMetrics(
            operation_name=self._current_operation,
            start_time=self._operation_start_time,
            end_time=end_time,
            cpu_usage_start=self._operation_start_cpu or 0.0,
            cpu_usage_end=end_cpu,
            memory_usage_start=self._operation_start_memory or 0.0,
            memory_usage_end=end_memory,
            additional_metrics=additional_metrics or {}
        )
        
        # Store in history
        self._metrics_history.append(metrics)
        
        # Reset current operation
        self._current_operation = None
        self._operation_start_time = None
        self._operation_start_cpu = None
        self._operation_start_memory = None
        
        self._logger.debug(f"Stopped monitoring operation: {metrics.operation_name} (duration: {metrics.duration:.2f}s)")
        
        return metrics
    
    @contextmanager
    def monitor_operation(self, operation_name: str, additional_metrics: Optional[Dict[str, Any]] = None):
        """Context manager for monitoring an operation.
        
        Args:
            operation_name: Name of the operation being monitored
            additional_metrics: Optional additional metrics to include
            
        Yields:
            PerformanceMetrics: Will be populated when the context exits
        """
        self.start_monitoring(operation_name)
        
        try:
            yield
        finally:
            metrics = self.stop_monitoring(additional_metrics)
            return metrics
    
    def get_metrics_history(self) -> List[PerformanceMetrics]:
        """Get all collected performance metrics.
        
        Returns:
            List[PerformanceMetrics]: All collected metrics
        """
        return self._metrics_history.copy()
    
    def get_operation_metrics(self, operation_name: str) -> List[PerformanceMetrics]:
        """Get metrics for a specific operation.
        
        Args:
            operation_name: Name of the operation to get metrics for
            
        Returns:
            List[PerformanceMetrics]: Metrics for the specified operation
        """
        return [m for m in self._metrics_history if m.operation_name == operation_name]
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get summary of all performance metrics.
        
        Returns:
            Dict[str, Any]: Performance summary
        """
        if not self._metrics_history:
            return {
                "total_operations": 0,
                "total_duration": 0.0,
                "average_duration": 0.0,
                "operations": {}
            }
        
        total_duration = sum(m.duration for m in self._metrics_history)
        
        # Group by operation name
        operations_summary = {}
        for metrics in self._metrics_history:
            op_name = metrics.operation_name
            if op_name not in operations_summary:
                operations_summary[op_name] = {
                    "count": 0,
                    "total_duration": 0.0,
                    "average_duration": 0.0,
                    "min_duration": float('inf'),
                    "max_duration": 0.0,
                    "total_memory_delta": 0.0,
                    "average_memory_delta": 0.0
                }
            
            op_summary = operations_summary[op_name]
            op_summary["count"] += 1
            op_summary["total_duration"] += metrics.duration
            op_summary["min_duration"] = min(op_summary["min_duration"], metrics.duration)
            op_summary["max_duration"] = max(op_summary["max_duration"], metrics.duration)
            op_summary["total_memory_delta"] += metrics.memory_usage_delta
        
        # Calculate averages
        for op_summary in operations_summary.values():
            if op_summary["count"] > 0:
                op_summary["average_duration"] = op_summary["total_duration"] / op_summary["count"]
                op_summary["average_memory_delta"] = op_summary["total_memory_delta"] / op_summary["count"]
                if op_summary["min_duration"] == float('inf'):
                    op_summary["min_duration"] = 0.0
        
        return {
            "total_operations": len(self._metrics_history),
            "total_duration": total_duration,
            "average_duration": total_duration / len(self._metrics_history),
            "operations": operations_summary
        }
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get current system performance information.
        
        Returns:
            Dict[str, Any]: System performance information
        """
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory_info = psutil.virtual_memory()
            disk_info = psutil.disk_usage('/')
            
            return {
                "cpu_percent": cpu_percent,
                "cpu_count": psutil.cpu_count(),
                "cpu_count_logical": psutil.cpu_count(logical=True),
                "memory_total_mb": memory_info.total / (1024 * 1024),
                "memory_used_mb": memory_info.used / (1024 * 1024),
                "memory_available_mb": memory_info.available / (1024 * 1024),
                "memory_percent": memory_info.percent,
                "disk_total_gb": disk_info.total / (1024 * 1024 * 1024),
                "disk_used_gb": disk_info.used / (1024 * 1024 * 1024),
                "disk_free_gb": disk_info.free / (1024 * 1024 * 1024),
                "disk_percent": (disk_info.used / disk_info.total) * 100
            }
            
        except Exception as e:
            self._logger.error(f"Could not collect system information: {e}")
            return {
                "error": f"Could not collect system information: {e}"
            }
    
    def analyze_performance_bottlenecks(self) -> Dict[str, Any]:
        """Analyze performance metrics to identify potential bottlenecks.
        
        Returns:
            Dict[str, Any]: Analysis results with recommendations
        """
        if not self._metrics_history:
            return {
                "analysis": "No performance data available",
                "recommendations": []
            }
        
        analysis = {
            "analysis": "",
            "recommendations": [],
            "bottlenecks": []
        }
        
        # Analyze operation durations
        durations = [m.duration for m in self._metrics_history]
        avg_duration = sum(durations) / len(durations)
        max_duration = max(durations)
        
        if max_duration > avg_duration * 3:
            analysis["bottlenecks"].append("Some operations take significantly longer than average")
            analysis["recommendations"].append("Consider investigating slow operations for optimization opportunities")
        
        # Analyze memory usage
        memory_deltas = [m.memory_usage_delta for m in self._metrics_history]
        avg_memory_delta = sum(memory_deltas) / len(memory_deltas)
        
        if avg_memory_delta > 100:  # More than 100MB average increase
            analysis["bottlenecks"].append("High memory usage detected")
            analysis["recommendations"].append("Consider implementing memory optimization or garbage collection")
        
        # Analyze system resources
        system_info = self.get_system_info()
        if "memory_percent" in system_info and system_info["memory_percent"] > 80:
            analysis["bottlenecks"].append("High system memory usage")
            analysis["recommendations"].append("System memory usage is high - consider reducing worker count or batch size")
        
        if "cpu_percent" in system_info and system_info["cpu_percent"] > 90:
            analysis["bottlenecks"].append("High CPU usage")
            analysis["recommendations"].append("CPU usage is very high - multiprocessing may not provide additional benefits")
        
        # Generate overall analysis
        if not analysis["bottlenecks"]:
            analysis["analysis"] = "No significant performance bottlenecks detected"
        else:
            analysis["analysis"] = f"Detected {len(analysis['bottlenecks'])} potential bottlenecks"
        
        return analysis
    
    def clear_metrics_history(self) -> None:
        """Clear all collected performance metrics."""
        self._metrics_history.clear()
        self._logger.debug("Performance metrics history cleared")
    
    def export_metrics_to_dict(self) -> Dict[str, Any]:
        """Export all metrics to a dictionary for serialization.
        
        Returns:
            Dict[str, Any]: All metrics in dictionary format
        """
        return {
            "metrics_history": [
                {
                    "operation_name": m.operation_name,
                    "start_time": m.start_time,
                    "end_time": m.end_time,
                    "duration": m.duration,
                    "cpu_usage_start": m.cpu_usage_start,
                    "cpu_usage_end": m.cpu_usage_end,
                    "cpu_usage_delta": m.cpu_usage_delta,
                    "memory_usage_start": m.memory_usage_start,
                    "memory_usage_end": m.memory_usage_end,
                    "memory_usage_delta": m.memory_usage_delta,
                    "additional_metrics": m.additional_metrics
                }
                for m in self._metrics_history
            ],
            "summary": self.get_performance_summary(),
            "system_info": self.get_system_info(),
            "bottleneck_analysis": self.analyze_performance_bottlenecks()
        }