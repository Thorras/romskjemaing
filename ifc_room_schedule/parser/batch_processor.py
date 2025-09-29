"""
Batch Processor for IFC Parsing

Processes large IFC files in batches to optimize memory usage and performance.
"""

import time
import gc
from typing import List, Dict, Any, Optional, Iterator, Callable, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import multiprocessing as mp
from queue import Queue, Empty
import threading

from ..utils.enhanced_logging import enhanced_logger
from .performance_monitor import PerformanceMonitor


@dataclass
class BatchConfig:
    """Configuration for batch processing."""
    
    batch_size: int = 100
    max_workers: int = 4
    memory_threshold_mb: float = 1000.0
    use_multiprocessing: bool = False
    enable_caching: bool = True
    progress_callback: Optional[Callable] = None


@dataclass
class BatchResult:
    """Result of batch processing."""
    
    batch_index: int
    success: bool
    items_processed: int
    processing_time: float
    memory_usage_mb: float
    error_message: Optional[str] = None
    results: List[Any] = None


class BatchProcessor:
    """Processes IFC data in batches for optimal performance."""
    
    def __init__(self, config: Optional[BatchConfig] = None):
        """Initialize batch processor."""
        self.config = config or BatchConfig()
        self.performance_monitor = PerformanceMonitor()
        self.results_queue = Queue()
        self.progress = 0
        self.total_items = 0
        self.lock = threading.Lock()
    
    def process_spaces_batch(self, spaces: List[Any], 
                           processor_func: Callable[[Any], Any],
                           config: Optional[BatchConfig] = None) -> List[Any]:
        """
        Process spaces in batches.
        
        Args:
            spaces: List of space entities to process
            processor_func: Function to process each space
            config: Optional batch configuration
            
        Returns:
            List of processed results
        """
        if config:
            self.config = config
        
        self.total_items = len(spaces)
        self.progress = 0
        all_results = []
        
        # Start performance monitoring
        self.performance_monitor.start_monitoring()
        
        try:
            # Process in batches
            for i in range(0, len(spaces), self.config.batch_size):
                batch = spaces[i:i + self.config.batch_size]
                batch_index = i // self.config.batch_size
                
                # Process batch
                batch_result = self._process_single_batch(
                    batch, batch_index, processor_func
                )
                
                # Collect results
                if batch_result.success and batch_result.results:
                    all_results.extend(batch_result.results)
                
                # Update progress
                self._update_progress(batch_result.items_processed)
                
                # Check memory usage
                if self._check_memory_threshold():
                    self._force_cleanup()
            
            return all_results
            
        finally:
            # Stop performance monitoring
            self.performance_monitor.stop_monitoring()
    
    def _process_single_batch(self, batch: List[Any], batch_index: int, 
                            processor_func: Callable[[Any], Any]) -> BatchResult:
        """Process a single batch of items."""
        start_time = time.time()
        start_memory = self._get_memory_usage()
        
        try:
            results = []
            
            if self.config.use_multiprocessing and len(batch) > 10:
                # Use multiprocessing for large batches
                results = self._process_batch_multiprocessing(batch, processor_func)
            else:
                # Use threading for smaller batches
                results = self._process_batch_threading(batch, processor_func)
            
            processing_time = time.time() - start_time
            end_memory = self._get_memory_usage()
            memory_usage = end_memory - start_memory
            
            return BatchResult(
                batch_index=batch_index,
                success=True,
                items_processed=len(batch),
                processing_time=processing_time,
                memory_usage_mb=memory_usage,
                results=results
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            enhanced_logger.logger.error(f"Error processing batch {batch_index}: {e}")
            
            return BatchResult(
                batch_index=batch_index,
                success=False,
                items_processed=0,
                processing_time=processing_time,
                memory_usage_mb=0.0,
                error_message=str(e),
                results=[]
            )
    
    def _process_batch_threading(self, batch: List[Any], 
                               processor_func: Callable[[Any], Any]) -> List[Any]:
        """Process batch using threading."""
        results = []
        
        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            # Submit all tasks
            future_to_item = {
                executor.submit(processor_func, item): item 
                for item in batch
            }
            
            # Collect results
            for future in as_completed(future_to_item):
                try:
                    result = future.result()
                    if result is not None:
                        results.append(result)
                except Exception as e:
                    enhanced_logger.logger.warning(f"Error processing item: {e}")
        
        return results
    
    def _process_batch_multiprocessing(self, batch: List[Any], 
                                     processor_func: Callable[[Any], Any]) -> List[Any]:
        """Process batch using multiprocessing."""
        results = []
        
        with ProcessPoolExecutor(max_workers=self.config.max_workers) as executor:
            # Submit all tasks
            future_to_item = {
                executor.submit(processor_func, item): item 
                for item in batch
            }
            
            # Collect results
            for future in as_completed(future_to_item):
                try:
                    result = future.result()
                    if result is not None:
                        results.append(result)
                except Exception as e:
                    enhanced_logger.logger.warning(f"Error processing item: {e}")
        
        return results
    
    def process_with_streaming(self, items: Iterator[Any], 
                             processor_func: Callable[[Any], Any],
                             config: Optional[BatchConfig] = None) -> Iterator[Any]:
        """
        Process items with streaming for memory efficiency.
        
        Args:
            items: Iterator of items to process
            processor_func: Function to process each item
            config: Optional batch configuration
            
        Yields:
            Processed results as they become available
        """
        if config:
            self.config = config
        
        batch = []
        batch_index = 0
        
        for item in items:
            batch.append(item)
            
            # Process batch when it reaches the configured size
            if len(batch) >= self.config.batch_size:
                batch_result = self._process_single_batch(
                    batch, batch_index, processor_func
                )
                
                # Yield results
                if batch_result.success and batch_result.results:
                    for result in batch_result.results:
                        yield result
                
                # Reset batch
                batch = []
                batch_index += 1
                
                # Check memory usage
                if self._check_memory_threshold():
                    self._force_cleanup()
        
        # Process remaining items
        if batch:
            batch_result = self._process_single_batch(
                batch, batch_index, processor_func
            )
            
            if batch_result.success and batch_result.results:
                for result in batch_result.results:
                    yield result
    
    def _update_progress(self, items_processed: int):
        """Update progress tracking."""
        with self.lock:
            self.progress += items_processed
            
            if self.config.progress_callback:
                progress_percent = (self.progress / self.total_items) * 100
                self.config.progress_callback(progress_percent, self.progress, self.total_items)
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / (1024 * 1024)
        except Exception:
            return 0.0
    
    def _check_memory_threshold(self) -> bool:
        """Check if memory usage exceeds threshold."""
        current_memory = self._get_memory_usage()
        return current_memory > self.config.memory_threshold_mb
    
    def _force_cleanup(self):
        """Force cleanup to free memory."""
        enhanced_logger.logger.info("Forcing cleanup due to memory threshold")
        
        # Force garbage collection
        collected = gc.collect()
        enhanced_logger.logger.info(f"Garbage collection freed {collected} objects")
        
        # Apply system optimizations
        self.performance_monitor.optimize_system()
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics."""
        with self.lock:
            return {
                "total_items": self.total_items,
                "processed_items": self.progress,
                "progress_percent": (self.progress / self.total_items) * 100 if self.total_items > 0 else 0,
                "remaining_items": self.total_items - self.progress
            }
    
    def optimize_for_large_files(self):
        """Optimize processor for large files."""
        enhanced_logger.logger.info("Optimizing processor for large files")
        
        # Reduce batch size for large files
        self.config.batch_size = min(self.config.batch_size, 50)
        
        # Enable multiprocessing
        self.config.use_multiprocessing = True
        
        # Reduce memory threshold
        self.config.memory_threshold_mb = 500.0
        
        # Force initial cleanup
        self._force_cleanup()
    
    def optimize_for_small_files(self):
        """Optimize processor for small files."""
        enhanced_logger.logger.info("Optimizing processor for small files")
        
        # Increase batch size for small files
        self.config.batch_size = max(self.config.batch_size, 200)
        
        # Disable multiprocessing for small files
        self.config.use_multiprocessing = False
        
        # Increase memory threshold
        self.config.memory_threshold_mb = 2000.0
    
    def cleanup(self):
        """Clean up processor resources."""
        self.performance_monitor.cleanup()
        self.results_queue = Queue()
        self.progress = 0
        self.total_items = 0


# Example usage and testing
if __name__ == "__main__":
    # Test batch processor
    processor = BatchProcessor()
    
    # Test data
    test_spaces = [f"Space_{i}" for i in range(1000)]
    
    def process_space(space):
        """Test processing function."""
        time.sleep(0.001)  # Simulate processing
        return f"Processed_{space}"
    
    def progress_callback(percent, processed, total):
        """Test progress callback."""
        print(f"Progress: {percent:.1f}% ({processed}/{total})")
    
    # Configure processor
    config = BatchConfig(
        batch_size=50,
        max_workers=4,
        progress_callback=progress_callback
    )
    
    print("Batch Processor Test:")
    print("=" * 40)
    
    # Process spaces
    results = processor.process_spaces_batch(test_spaces, process_space, config)
    
    print(f"Processed {len(results)} spaces")
    
    # Get stats
    stats = processor.get_processing_stats()
    print(f"Stats: {stats}")
    
    # Test streaming
    print("\nStreaming Test:")
    stream_results = list(processor.process_with_streaming(
        iter(test_spaces[:100]), process_space, config
    ))
    print(f"Streamed {len(stream_results)} results")
    
    # Cleanup
    processor.cleanup()
    print("Processor cleaned up")
