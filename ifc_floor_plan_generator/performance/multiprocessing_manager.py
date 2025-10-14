"""
Multiprocessing manager for IFC Floor Plan Generator.

Implements parallel processing per storey with configurable worker pools and thread-safe error handling.
"""

import logging
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import List, Dict, Any, Optional, Callable, Tuple
from dataclasses import dataclass
from ..models import StoreyResult, Config
from ..errors.handler import ErrorHandler
from ..errors.exceptions import ProcessingError


@dataclass
class ProcessingTask:
    """Represents a processing task for a single storey."""
    storey_index: int
    storey_name: str
    task_data: Dict[str, Any]
    task_id: str


@dataclass
class ProcessingResult:
    """Result from processing a single storey."""
    task_id: str
    storey_index: int
    storey_name: str
    success: bool
    result_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    processing_time: float = 0.0


class MultiprocessingManager:
    """Manages parallel processing of storeys with configurable worker pools."""
    
    def __init__(self, config: Config):
        """Initialize multiprocessing manager with configuration.
        
        Args:
            config: Main configuration containing performance settings
        """
        self.config = config
        self._logger = logging.getLogger(__name__)
        self._error_handler = ErrorHandler()
        
        # Determine number of workers
        self._max_workers = self._determine_worker_count()
        
        # Multiprocessing enabled flag
        self._multiprocessing_enabled = config.performance.multiprocessing
        
        self._logger.info(f"Multiprocessing manager initialized: enabled={self._multiprocessing_enabled}, workers={self._max_workers}")
    
    def _determine_worker_count(self) -> int:
        """Determine optimal number of worker processes.
        
        Returns:
            int: Number of worker processes to use
        """
        if self.config.performance.max_workers is not None:
            # Use configured worker count
            return max(1, self.config.performance.max_workers)
        else:
            # Use CPU count with reasonable limits
            cpu_count = mp.cpu_count()
            # Use 75% of available CPUs, minimum 1, maximum 8
            return max(1, min(8, int(cpu_count * 0.75)))
    
    def is_multiprocessing_enabled(self) -> bool:
        """Check if multiprocessing is enabled.
        
        Returns:
            bool: True if multiprocessing is enabled
        """
        return self._multiprocessing_enabled
    
    def process_storeys_parallel(
        self, 
        storeys: List[StoreyResult], 
        processing_function: Callable[[ProcessingTask], ProcessingResult],
        task_data_generator: Callable[[StoreyResult, int], Dict[str, Any]]
    ) -> List[ProcessingResult]:
        """Process storeys in parallel using multiprocessing.
        
        Args:
            storeys: List of storeys to process
            processing_function: Function to process each storey
            task_data_generator: Function to generate task data for each storey
            
        Returns:
            List[ProcessingResult]: Results from processing all storeys
            
        Raises:
            ProcessingError: If multiprocessing setup or execution fails
        """
        if not self._multiprocessing_enabled:
            # Fall back to sequential processing
            return self._process_storeys_sequential(storeys, processing_function, task_data_generator)
        
        if len(storeys) <= 1:
            # No benefit from multiprocessing with single storey
            return self._process_storeys_sequential(storeys, processing_function, task_data_generator)
        
        try:
            # Create processing tasks
            tasks = []
            for index, storey in enumerate(storeys):
                task_data = task_data_generator(storey, index)
                task = ProcessingTask(
                    storey_index=index,
                    storey_name=storey.storey_name,
                    task_data=task_data,
                    task_id=f"storey_{index}_{storey.storey_name}"
                )
                tasks.append(task)
            
            # Process tasks in parallel
            results = self._execute_parallel_tasks(tasks, processing_function)
            
            self._logger.info(f"Parallel processing completed: {len(results)} storeys processed")
            return results
            
        except Exception as e:
            self._logger.error(f"Parallel processing failed: {e}")
            # Fall back to sequential processing
            self._logger.info("Falling back to sequential processing")
            return self._process_storeys_sequential(storeys, processing_function, task_data_generator)
    
    def _process_storeys_sequential(
        self,
        storeys: List[StoreyResult],
        processing_function: Callable[[ProcessingTask], ProcessingResult],
        task_data_generator: Callable[[StoreyResult, int], Dict[str, Any]]
    ) -> List[ProcessingResult]:
        """Process storeys sequentially (fallback method).
        
        Args:
            storeys: List of storeys to process
            processing_function: Function to process each storey
            task_data_generator: Function to generate task data for each storey
            
        Returns:
            List[ProcessingResult]: Results from processing all storeys
        """
        results = []
        
        for index, storey in enumerate(storeys):
            try:
                task_data = task_data_generator(storey, index)
                task = ProcessingTask(
                    storey_index=index,
                    storey_name=storey.storey_name,
                    task_data=task_data,
                    task_id=f"storey_{index}_{storey.storey_name}"
                )
                
                result = processing_function(task)
                results.append(result)
                
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
    
    def _execute_parallel_tasks(
        self, 
        tasks: List[ProcessingTask], 
        processing_function: Callable[[ProcessingTask], ProcessingResult]
    ) -> List[ProcessingResult]:
        """Execute tasks in parallel using ProcessPoolExecutor.
        
        Args:
            tasks: List of processing tasks
            processing_function: Function to process each task
            
        Returns:
            List[ProcessingResult]: Results from all tasks
            
        Raises:
            ProcessingError: If parallel execution fails
        """
        results = []
        
        try:
            with ProcessPoolExecutor(max_workers=self._max_workers) as executor:
                # Submit all tasks
                future_to_task = {
                    executor.submit(processing_function, task): task 
                    for task in tasks
                }
                
                # Collect results as they complete
                for future in as_completed(future_to_task):
                    task = future_to_task[future]
                    
                    try:
                        result = future.result()
                        results.append(result)
                        
                        if result.success:
                            self._logger.debug(f"Task {task.task_id} completed successfully")
                        else:
                            self._logger.warning(f"Task {task.task_id} failed: {result.error_message}")
                            
                    except Exception as e:
                        # Create error result for failed task
                        error_result = ProcessingResult(
                            task_id=task.task_id,
                            storey_index=task.storey_index,
                            storey_name=task.storey_name,
                            success=False,
                            error_message=str(e)
                        )
                        results.append(error_result)
                        self._logger.error(f"Task {task.task_id} raised exception: {e}")
            
            # Sort results by storey index to maintain order
            results.sort(key=lambda r: r.storey_index)
            
            return results
            
        except Exception as e:
            raise ProcessingError(
                error_code="MULTIPROCESSING_ERROR",
                message=f"Feil i parallell prosessering: {str(e)}",
                context={
                    "max_workers": self._max_workers,
                    "task_count": len(tasks),
                    "error": str(e)
                }
            )
    
    def get_performance_info(self) -> Dict[str, Any]:
        """Get information about multiprocessing configuration and capabilities.
        
        Returns:
            Dict[str, Any]: Performance configuration information
        """
        return {
            "multiprocessing_enabled": self._multiprocessing_enabled,
            "max_workers": self._max_workers,
            "cpu_count": mp.cpu_count(),
            "configured_workers": self.config.performance.max_workers,
            "worker_determination": "configured" if self.config.performance.max_workers else "automatic"
        }
    
    def estimate_processing_time(self, storey_count: int, avg_time_per_storey: float) -> Dict[str, float]:
        """Estimate processing time for sequential vs parallel execution.
        
        Args:
            storey_count: Number of storeys to process
            avg_time_per_storey: Average processing time per storey in seconds
            
        Returns:
            Dict[str, float]: Time estimates for different execution modes
        """
        sequential_time = storey_count * avg_time_per_storey
        
        if self._multiprocessing_enabled and storey_count > 1:
            # Estimate parallel time with overhead
            parallel_time = (storey_count / self._max_workers) * avg_time_per_storey
            # Add 20% overhead for multiprocessing coordination
            parallel_time *= 1.2
        else:
            parallel_time = sequential_time
        
        return {
            "sequential_estimate": sequential_time,
            "parallel_estimate": parallel_time,
            "estimated_speedup": sequential_time / parallel_time if parallel_time > 0 else 1.0,
            "workers_used": self._max_workers if self._multiprocessing_enabled else 1
        }
    
    def validate_multiprocessing_environment(self) -> Dict[str, Any]:
        """Validate that the environment supports multiprocessing.
        
        Returns:
            Dict[str, Any]: Validation results
        """
        validation = {
            "supported": True,
            "warnings": [],
            "errors": []
        }
        
        try:
            # Test basic multiprocessing functionality
            with ProcessPoolExecutor(max_workers=1) as executor:
                future = executor.submit(lambda: "test")
                result = future.result(timeout=5)
                if result != "test":
                    validation["supported"] = False
                    validation["errors"].append("Basic multiprocessing test failed")
        
        except Exception as e:
            validation["supported"] = False
            validation["errors"].append(f"Multiprocessing test failed: {e}")
        
        # Check for common issues
        if mp.cpu_count() == 1:
            validation["warnings"].append("Single CPU detected - multiprocessing may not provide benefits")
        
        if self._max_workers > mp.cpu_count():
            validation["warnings"].append(f"Configured workers ({self._max_workers}) exceed CPU count ({mp.cpu_count()})")
        
        return validation


def create_storey_processing_task_data(storey: StoreyResult, index: int) -> Dict[str, Any]:
    """Create task data for storey processing (example implementation).
    
    Args:
        storey: StoreyResult to create task data for
        index: Index of the storey
        
    Returns:
        Dict[str, Any]: Task data for the storey
    """
    return {
        "storey_name": storey.storey_name,
        "cut_height": storey.cut_height,
        "element_count": storey.element_count,
        "polyline_count": len(storey.polylines),
        "bounds": storey.bounds.__dict__ if storey.bounds else None,
        "index": index
    }


def example_storey_processing_function(task: ProcessingTask) -> ProcessingResult:
    """Example processing function for a storey (to be customized).
    
    Args:
        task: ProcessingTask containing storey data
        
    Returns:
        ProcessingResult: Result of processing the storey
    """
    import time
    start_time = time.time()
    
    try:
        # Simulate processing work
        storey_name = task.task_data["storey_name"]
        element_count = task.task_data["element_count"]
        
        # Simulate processing time based on element count
        processing_time = element_count * 0.001  # 1ms per element
        time.sleep(min(processing_time, 0.1))  # Cap at 100ms for testing
        
        result_data = {
            "processed_elements": element_count,
            "processing_method": "parallel" if mp.current_process().name != "MainProcess" else "sequential"
        }
        
        return ProcessingResult(
            task_id=task.task_id,
            storey_index=task.storey_index,
            storey_name=task.storey_name,
            success=True,
            result_data=result_data,
            processing_time=time.time() - start_time
        )
        
    except Exception as e:
        return ProcessingResult(
            task_id=task.task_id,
            storey_index=task.storey_index,
            storey_name=task.storey_name,
            success=False,
            error_message=str(e),
            processing_time=time.time() - start_time
        )