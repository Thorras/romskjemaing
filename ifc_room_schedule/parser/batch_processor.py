"""
Batch Processor

Optimized batch processing for large room sets with memory management
and streaming export capabilities.
"""

import json
import os
import gc
from typing import List, Dict, Any, Optional, Iterator, Callable
from pathlib import Path
from datetime import datetime
import threading
import queue
import time

from ..data.space_model import SpaceData
from ..export.enhanced_json_builder import EnhancedJsonBuilder
from ..analysis.data_quality_analyzer import DataQualityAnalyzer


class BatchProcessor:
    """Optimized batch processor for large room sets."""
    
    def __init__(self, max_memory_mb: int = 512, chunk_size: int = 100):
        """
        Initialize batch processor.
        
        Args:
            max_memory_mb: Maximum memory usage in MB
            chunk_size: Number of spaces to process in each chunk
        """
        self.max_memory_mb = max_memory_mb
        self.chunk_size = chunk_size
        self.builder = EnhancedJsonBuilder()
        self.analyzer = DataQualityAnalyzer()
        
        # Performance monitoring
        self.processing_stats = {
            "total_spaces": 0,
            "processed_spaces": 0,
            "processing_time": 0.0,
            "memory_peak_mb": 0.0,
            "chunks_processed": 0
        }
    
    def process_spaces_batch(self, 
                           spaces: List[SpaceData], 
                           output_path: str,
                           export_profile: str = "production",
                           progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Process spaces in batches with memory management.
        
        Args:
            spaces: List of spaces to process
            output_path: Output file path
            export_profile: Export profile to use
            progress_callback: Optional progress callback function
            
        Returns:
            Processing statistics
        """
        start_time = time.time()
        self.processing_stats["total_spaces"] = len(spaces)
        self.processing_stats["processed_spaces"] = 0
        self.processing_stats["chunks_processed"] = 0
        
        try:
            # Process in chunks
            chunks = self._create_chunks(spaces, self.chunk_size)
            processed_data = []
            
            for i, chunk in enumerate(chunks):
                # Process chunk
                chunk_data = self._process_chunk(chunk, export_profile)
                processed_data.extend(chunk_data)
                
                # Update statistics
                self.processing_stats["processed_spaces"] += len(chunk)
                self.processing_stats["chunks_processed"] += 1
                
                # Memory management
                self._manage_memory()
                
                # Progress callback
                if progress_callback:
                    progress = (i + 1) / len(chunks) * 100
                    progress_callback(int(progress), f"Processed chunk {i + 1}/{len(chunks)}")
                
                # Yield control to allow UI updates
                time.sleep(0.001)
            
            # Write output
            self._write_output(processed_data, output_path)
            
            # Final statistics
            self.processing_stats["processing_time"] = time.time() - start_time
            self.processing_stats["memory_peak_mb"] = self._get_memory_usage()
            
            return self.processing_stats
            
        except Exception as e:
            raise Exception(f"Batch processing failed: {str(e)}")
    
    def process_spaces_streaming(self, 
                               spaces: List[SpaceData], 
                               output_path: str,
                               export_profile: str = "production",
                               progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Process spaces with streaming export to reduce memory usage.
        
        Args:
            spaces: List of spaces to process
            output_path: Output file path
            export_profile: Export profile to use
            progress_callback: Optional progress callback function
            
        Returns:
            Processing statistics
        """
        start_time = time.time()
        self.processing_stats["total_spaces"] = len(spaces)
        self.processing_stats["processed_spaces"] = 0
        self.processing_stats["chunks_processed"] = 0
        
        try:
            # Create chunks
            chunks = self._create_chunks(spaces, self.chunk_size)
            
            # Stream write to file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write('{\n')
                f.write('  "metadata": {\n')
                f.write(f'    "generated_at": "{datetime.now().isoformat()}",\n')
                f.write(f'    "total_spaces": {len(spaces)},\n')
                f.write(f'    "export_profile": "{export_profile}"\n')
                f.write('  },\n')
                f.write('  "spaces": [\n')
                
                first_chunk = True
                for i, chunk in enumerate(chunks):
                    # Process chunk
                    chunk_data = self._process_chunk(chunk, export_profile)
                    
                    # Write chunk data
                    for j, space_data in enumerate(chunk_data):
                        if not first_chunk or j > 0:
                            f.write(',\n')
                        
                        json.dump(space_data, f, indent=4, ensure_ascii=False)
                        first_chunk = False
                    
                    # Update statistics
                    self.processing_stats["processed_spaces"] += len(chunk)
                    self.processing_stats["chunks_processed"] += 1
                    
                    # Memory management
                    self._manage_memory()
                    
                    # Progress callback
                    if progress_callback:
                        progress = (i + 1) / len(chunks) * 100
                        progress_callback(int(progress), f"Streamed chunk {i + 1}/{len(chunks)}")
                    
                    # Yield control
                    time.sleep(0.001)
                
                f.write('\n  ]\n')
                f.write('}\n')
            
            # Final statistics
            self.processing_stats["processing_time"] = time.time() - start_time
            self.processing_stats["memory_peak_mb"] = self._get_memory_usage()
            
            return self.processing_stats
            
        except Exception as e:
            raise Exception(f"Streaming processing failed: {str(e)}")
    
    def process_spaces_parallel(self, 
                              spaces: List[SpaceData], 
                              output_path: str,
                              export_profile: str = "production",
                              num_threads: int = 4,
                              progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """
        Process spaces in parallel using multiple threads.
        
        Args:
            spaces: List of spaces to process
            output_path: Output file path
            export_profile: Export profile to use
            num_threads: Number of threads to use
            progress_callback: Optional progress callback function
            
        Returns:
            Processing statistics
        """
        start_time = time.time()
        self.processing_stats["total_spaces"] = len(spaces)
        self.processing_stats["processed_spaces"] = 0
        self.processing_stats["chunks_processed"] = 0
        
        try:
            # Create chunks
            chunks = self._create_chunks(spaces, self.chunk_size)
            
            # Thread-safe queues
            input_queue = queue.Queue()
            output_queue = queue.Queue()
            
            # Add chunks to input queue
            for chunk in chunks:
                input_queue.put(chunk)
            
            # Add sentinel values to signal end
            for _ in range(num_threads):
                input_queue.put(None)
            
            # Worker threads
            threads = []
            for i in range(num_threads):
                thread = threading.Thread(
                    target=self._worker_thread,
                    args=(input_queue, output_queue, export_profile, i)
                )
                thread.start()
                threads.append(thread)
            
            # Collect results
            processed_data = []
            completed_chunks = 0
            
            while completed_chunks < len(chunks):
                try:
                    result = output_queue.get(timeout=1.0)
                    if result is not None:
                        processed_data.extend(result)
                        completed_chunks += 1
                        
                        # Update statistics
                        self.processing_stats["processed_spaces"] += len(result)
                        self.processing_stats["chunks_processed"] += 1
                        
                        # Progress callback
                        if progress_callback:
                            progress = completed_chunks / len(chunks) * 100
                            progress_callback(int(progress), f"Completed {completed_chunks}/{len(chunks)} chunks")
                        
                except queue.Empty:
                    continue
            
            # Wait for threads to complete
            for thread in threads:
                thread.join()
            
            # Write output
            self._write_output(processed_data, output_path)
            
            # Final statistics
            self.processing_stats["processing_time"] = time.time() - start_time
            self.processing_stats["memory_peak_mb"] = self._get_memory_usage()
            
            return self.processing_stats
            
        except Exception as e:
            raise Exception(f"Parallel processing failed: {str(e)}")
    
    def _create_chunks(self, spaces: List[SpaceData], chunk_size: int) -> List[List[SpaceData]]:
        """Create chunks from spaces list."""
        chunks = []
        for i in range(0, len(spaces), chunk_size):
            chunk = spaces[i:i + chunk_size]
            chunks.append(chunk)
        return chunks
    
    def _process_chunk(self, chunk: List[SpaceData], export_profile: str) -> List[Dict[str, Any]]:
        """Process a chunk of spaces."""
        chunk_data = []
        
        for space in chunk:
            try:
                # Build enhanced space data
                space_data = self.builder._build_enhanced_space_dict(space, export_profile)
                chunk_data.append(space_data)
                
            except Exception as e:
                # Log error but continue processing
                print(f"Error processing space {space.name}: {str(e)}")
                continue
        
        return chunk_data
    
    def _worker_thread(self, input_queue: queue.Queue, output_queue: queue.Queue, 
                      export_profile: str, thread_id: int):
        """Worker thread for parallel processing."""
        while True:
            try:
                chunk = input_queue.get(timeout=1.0)
                if chunk is None:
                    break
                
                # Process chunk
                chunk_data = self._process_chunk(chunk, export_profile)
                output_queue.put(chunk_data)
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Worker thread {thread_id} error: {str(e)}")
                output_queue.put([])
    
    def _manage_memory(self):
        """Manage memory usage."""
        current_memory = self._get_memory_usage()
        
        if current_memory > self.max_memory_mb:
            # Force garbage collection
            gc.collect()
            
            # If still over limit, increase chunk size
            if self._get_memory_usage() > self.max_memory_mb:
                self.chunk_size = max(10, self.chunk_size // 2)
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            # Fallback to basic memory estimation
            return 0.0
    
    def _write_output(self, data: List[Dict[str, Any]], output_path: str):
        """Write processed data to output file."""
        output_data = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "total_spaces": len(data),
                "processing_stats": self.processing_stats
            },
            "spaces": data
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get current processing statistics."""
        return self.processing_stats.copy()
    
    def reset_stats(self):
        """Reset processing statistics."""
        self.processing_stats = {
            "total_spaces": 0,
            "processed_spaces": 0,
            "processing_time": 0.0,
            "memory_peak_mb": 0.0,
            "chunks_processed": 0
        }


class MemoryManager:
    """Memory management utilities for batch processing."""
    
    @staticmethod
    def get_memory_info() -> Dict[str, Any]:
        """Get current memory information."""
        try:
            import psutil
            memory = psutil.virtual_memory()
            return {
                "total_mb": memory.total / 1024 / 1024,
                "available_mb": memory.available / 1024 / 1024,
                "used_mb": memory.used / 1024 / 1024,
                "percent_used": memory.percent
            }
        except ImportError:
            return {
                "total_mb": 0,
                "available_mb": 0,
                "used_mb": 0,
                "percent_used": 0
            }
    
    @staticmethod
    def optimize_memory():
        """Optimize memory usage."""
        # Force garbage collection
        gc.collect()
        
        # Clear Python cache
        import sys
        if hasattr(sys, '_clear_type_cache'):
            sys._clear_type_cache()
    
    @staticmethod
    def estimate_memory_usage(spaces: List[SpaceData], export_profile: str) -> float:
        """Estimate memory usage for processing spaces."""
        # Rough estimation based on space count and profile
        base_memory_per_space = 0.1  # MB per space
        
        if export_profile == "production":
            multiplier = 3.0
        elif export_profile == "advanced":
            multiplier = 2.0
        else:
            multiplier = 1.0
        
        estimated_memory = len(spaces) * base_memory_per_space * multiplier
        return estimated_memory


# Example usage
if __name__ == "__main__":
    from ..data.space_model import SpaceData
    
    # Create sample spaces
    sample_spaces = [
        SpaceData(
            guid=f"test_space_{i}",
            name=f"SPC-02-A101-111-{i:03d}",
            long_name=f"Test Space {i} | 02/A101 | NS3940:111",
            description=f"Test space {i}",
            object_type="IfcSpace",
            zone_category="A101",
            number=f"{i:03d}",
            elevation=0.0,
            quantities={"Height": 2.4, "NetArea": 25.0},
            surfaces=[],
            space_boundaries=[],
            relationships=[]
        )
        for i in range(1000)  # Create 1000 test spaces
    ]
    
    # Test batch processing
    processor = BatchProcessor(max_memory_mb=256, chunk_size=50)
    
    def progress_callback(progress: int, status: str):
        print(f"Progress: {progress}% - {status}")
    
    try:
        stats = processor.process_spaces_batch(
            sample_spaces, 
            "test_batch_output.json",
            "production",
            progress_callback
        )
        
        print("Batch processing completed!")
        print(f"Statistics: {stats}")
        
    except Exception as e:
        print(f"Batch processing failed: {str(e)}")