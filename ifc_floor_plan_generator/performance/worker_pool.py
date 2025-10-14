"""
Worker pool management for IFC Floor Plan Generator.

Provides advanced worker pool management with result aggregation and error handling.
"""

import logging
import threading
import queue
import time
from concurrent.futures import ThreadPoolExecutor, Future
from typing import List, Dict, Any, Optional, Callable, Iterator
from dataclasses import dataclass, field
from threading import Lock
from ..errors.handler import ErrorHandler
from ..errors.exceptions import ProcessingError


@dataclass
class WorkerResult:
    """Result from a worker task with metadata."""
    task_id: str
    worker_id: str
    success: bool
    result_data: Optional[Any] = None
    error_message: Optional[str] = None
    start_time: float = 0.0
    end_time: float = 0.0
    
    @property
    def processing_time(self) -> float:
        """Get processing time in seconds."""
        return self.end_time - self.start_time if self.end_time > self.start_time else 0.0


@dataclass
class WorkerStats:
    """Statistics for worker pool performance."""
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    total_processing_time: float = 0.0
    average_task_time: float = 0.0
    worker_utilization: Dict[str, float] = field(default_factory=dict)
    
    def update_stats(self, results: List[WorkerResult]) -> None:
        """Update statistics from worker results."""
        self.total_tasks = len(results)
        self.completed_tasks = sum(1 for r in results if r.success)
        self.failed_tasks = self.total_tasks - self.completed_tasks
        
        if results:
            self.total_processing_time = sum(r.processing_time for r in results)
            self.average_task_time = self.total_processing_time / len(results)
            
            # Calculate worker utilization
            worker_times = {}
            for result in results:
                if result.worker_id not in worker_times:
                    worker_times[result.worker_id] = 0.0
                worker_times[result.worker_id] += result.processing_time
            
            if worker_times:
                max_time = max(worker_times.values())
                self.worker_utilization = {
                    worker_id: (time_spent / max_time) * 100 if max_time > 0 else 0.0
                    for worker_id, time_spent in worker_times.items()
                }


class WorkerPool:
    """Advanced worker pool with thread-safe result aggregation."""
    
    def __init__(self, max_workers: int, pool_name: str = "WorkerPool"):
        """Initialize worker pool.
        
        Args:
            max_workers: Maximum number of worker threads
            pool_name: Name for the worker pool (for logging)
        """
        self.max_workers = max_workers
        self.pool_name = pool_name
        self._logger = logging.getLogger(__name__)
        self._error_handler = ErrorHandler()
        
        # Thread-safe result collection
        self._results: List[WorkerResult] = []
        self._results_lock = Lock()
        
        # Task queue and completion tracking
        self._task_queue: queue.Queue = queue.Queue()
        self._completed_tasks = 0
        self._total_tasks = 0
        self._completion_lock = Lock()
        
        # Worker pool state
        self._executor: Optional[ThreadPoolExecutor] = None
        self._is_running = False
        
        self._logger.info(f"Worker pool '{pool_name}' initialized with {max_workers} workers")
    
    def submit_task(
        self, 
        task_function: Callable[..., Any], 
        task_id: str, 
        *args, 
        **kwargs
    ) -> Future:
        """Submit a task to the worker pool.
        
        Args:
            task_function: Function to execute
            task_id: Unique identifier for the task
            *args: Positional arguments for the task function
            **kwargs: Keyword arguments for the task function
            
        Returns:
            Future: Future object for the submitted task
            
        Raises:
            ProcessingError: If worker pool is not running
        """
        if not self._is_running or self._executor is None:
            raise ProcessingError(
                error_code="WORKER_POOL_NOT_RUNNING",
                message="Worker pool is not running",
                context={"pool_name": self.pool_name}
            )
        
        # Wrap the task function to capture results
        def wrapped_task():
            worker_id = threading.current_thread().name
            start_time = time.time()
            
            try:
                result_data = task_function(*args, **kwargs)
                end_time = time.time()
                
                worker_result = WorkerResult(
                    task_id=task_id,
                    worker_id=worker_id,
                    success=True,
                    result_data=result_data,
                    start_time=start_time,
                    end_time=end_time
                )
                
            except Exception as e:
                end_time = time.time()
                
                worker_result = WorkerResult(
                    task_id=task_id,
                    worker_id=worker_id,
                    success=False,
                    error_message=str(e),
                    start_time=start_time,
                    end_time=end_time
                )
                
                self._logger.error(f"Task {task_id} failed in worker {worker_id}: {e}")
            
            # Thread-safe result collection
            with self._results_lock:
                self._results.append(worker_result)
            
            # Update completion counter
            with self._completion_lock:
                self._completed_tasks += 1
            
            return worker_result
        
        # Submit wrapped task
        future = self._executor.submit(wrapped_task)
        
        with self._completion_lock:
            self._total_tasks += 1
        
        return future
    
    def start(self) -> None:
        """Start the worker pool."""
        if self._is_running:
            self._logger.warning(f"Worker pool '{self.pool_name}' is already running")
            return
        
        try:
            self._executor = ThreadPoolExecutor(
                max_workers=self.max_workers,
                thread_name_prefix=f"{self.pool_name}_Worker"
            )
            self._is_running = True
            
            # Reset counters
            with self._completion_lock:
                self._completed_tasks = 0
                self._total_tasks = 0
            
            with self._results_lock:
                self._results.clear()
            
            self._logger.info(f"Worker pool '{self.pool_name}' started with {self.max_workers} workers")
            
        except Exception as e:
            raise ProcessingError(
                error_code="WORKER_POOL_START_FAILED",
                message=f"Failed to start worker pool: {str(e)}",
                context={"pool_name": self.pool_name, "error": str(e)}
            )
    
    def shutdown(self, wait: bool = True, timeout: Optional[float] = None) -> None:
        """Shutdown the worker pool.
        
        Args:
            wait: Whether to wait for running tasks to complete
            timeout: Maximum time to wait for shutdown (seconds)
        """
        if not self._is_running or self._executor is None:
            return
        
        try:
            self._is_running = False
            self._executor.shutdown(wait=wait, timeout=timeout)
            self._executor = None
            
            self._logger.info(f"Worker pool '{self.pool_name}' shutdown completed")
            
        except Exception as e:
            self._logger.error(f"Error during worker pool shutdown: {e}")
    
    def get_results(self) -> List[WorkerResult]:
        """Get all collected results thread-safely.
        
        Returns:
            List[WorkerResult]: All worker results collected so far
        """
        with self._results_lock:
            return self._results.copy()
    
    def get_completion_status(self) -> Dict[str, int]:
        """Get current completion status.
        
        Returns:
            Dict[str, int]: Completion status information
        """
        with self._completion_lock:
            return {
                "total_tasks": self._total_tasks,
                "completed_tasks": self._completed_tasks,
                "pending_tasks": self._total_tasks - self._completed_tasks
            }
    
    def wait_for_completion(self, timeout: Optional[float] = None) -> bool:
        """Wait for all submitted tasks to complete.
        
        Args:
            timeout: Maximum time to wait (seconds)
            
        Returns:
            bool: True if all tasks completed, False if timeout occurred
        """
        if not self._is_running:
            return True
        
        start_time = time.time()
        
        while True:
            status = self.get_completion_status()
            
            if status["pending_tasks"] == 0:
                return True
            
            if timeout is not None and (time.time() - start_time) > timeout:
                return False
            
            time.sleep(0.1)  # Small delay to avoid busy waiting
    
    def get_statistics(self) -> WorkerStats:
        """Get comprehensive statistics for the worker pool.
        
        Returns:
            WorkerStats: Statistics about worker pool performance
        """
        results = self.get_results()
        stats = WorkerStats()
        stats.update_stats(results)
        return stats
    
    def is_running(self) -> bool:
        """Check if the worker pool is currently running.
        
        Returns:
            bool: True if the worker pool is running
        """
        return self._is_running
    
    def get_pool_info(self) -> Dict[str, Any]:
        """Get information about the worker pool configuration and state.
        
        Returns:
            Dict[str, Any]: Worker pool information
        """
        status = self.get_completion_status()
        stats = self.get_statistics()
        
        return {
            "pool_name": self.pool_name,
            "max_workers": self.max_workers,
            "is_running": self._is_running,
            "total_tasks": status["total_tasks"],
            "completed_tasks": status["completed_tasks"],
            "pending_tasks": status["pending_tasks"],
            "success_rate": (stats.completed_tasks / stats.total_tasks * 100) if stats.total_tasks > 0 else 0.0,
            "average_task_time": stats.average_task_time,
            "worker_utilization": stats.worker_utilization
        }
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.shutdown()


class ResultAggregator:
    """Thread-safe result aggregation utility."""
    
    def __init__(self):
        """Initialize result aggregator."""
        self._results: Dict[str, List[WorkerResult]] = {}
        self._lock = Lock()
        self._logger = logging.getLogger(__name__)
    
    def add_results(self, category: str, results: List[WorkerResult]) -> None:
        """Add results to a specific category.
        
        Args:
            category: Category name for the results
            results: List of worker results to add
        """
        with self._lock:
            if category not in self._results:
                self._results[category] = []
            self._results[category].extend(results)
    
    def get_results(self, category: Optional[str] = None) -> Dict[str, List[WorkerResult]]:
        """Get results by category.
        
        Args:
            category: Specific category to get, or None for all categories
            
        Returns:
            Dict[str, List[WorkerResult]]: Results by category
        """
        with self._lock:
            if category is not None:
                return {category: self._results.get(category, [])}
            else:
                return {k: v.copy() for k, v in self._results.items()}
    
    def get_aggregated_stats(self) -> Dict[str, WorkerStats]:
        """Get aggregated statistics for all categories.
        
        Returns:
            Dict[str, WorkerStats]: Statistics by category
        """
        stats_by_category = {}
        
        with self._lock:
            for category, results in self._results.items():
                stats = WorkerStats()
                stats.update_stats(results)
                stats_by_category[category] = stats
        
        return stats_by_category
    
    def clear_results(self, category: Optional[str] = None) -> None:
        """Clear results for a category or all categories.
        
        Args:
            category: Specific category to clear, or None for all categories
        """
        with self._lock:
            if category is not None:
                self._results.pop(category, None)
            else:
                self._results.clear()
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all aggregated results.
        
        Returns:
            Dict[str, Any]: Summary information
        """
        with self._lock:
            total_results = sum(len(results) for results in self._results.values())
            total_successful = sum(
                sum(1 for r in results if r.success) 
                for results in self._results.values()
            )
            
            return {
                "categories": list(self._results.keys()),
                "total_results": total_results,
                "successful_results": total_successful,
                "failed_results": total_results - total_successful,
                "success_rate": (total_successful / total_results * 100) if total_results > 0 else 0.0,
                "results_per_category": {
                    category: len(results) 
                    for category, results in self._results.items()
                }
            }