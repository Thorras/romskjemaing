# Performance Monitor Hook

## Trigger
- **Event**: File saved
- **File Pattern**: `**/parser*.py, **/ifc*.py, **/*performance*.py`
- **Manual**: Button click for "Run Performance Tests"

## Description
Monitors performance of IFC parsing and processing operations to detect performance regressions early.

## Instructions
When performance-critical code is modified:

1. Run performance benchmarks:
   ```python
   import time
   import memory_profiler
   
   # Benchmark IFC file loading
   # Benchmark space extraction
   # Benchmark surface calculations
   ```

2. Test with various file sizes:
   - Small IFC files (< 1MB)
   - Medium IFC files (1-10MB)
   - Large IFC files (> 10MB)
   - Complex building models

3. Monitor key metrics:
   - File loading time
   - Memory usage during parsing
   - Space extraction performance
   - Surface calculation speed
   - Export generation time

4. Generate performance report:
   ```markdown
   # Performance Report
   
   ## File Loading Performance
   - Small files: X seconds
   - Large files: Y seconds
   
   ## Memory Usage
   - Peak memory: X MB
   - Memory efficiency: Y%
   
   ## Processing Speed
   - Spaces per second: X
   - Surfaces per second: Y
   ```

5. Compare against baseline performance:
   - Track performance trends over time
   - Identify performance regressions
   - Flag significant slowdowns

6. Profile critical functions:
   ```python
   import cProfile
   # Profile IFC parsing functions
   # Profile data processing operations
   ```

7. Generate optimization recommendations:
   - Identify bottlenecks
   - Suggest algorithmic improvements
   - Recommend caching strategies

8. Test scalability:
   - Multiple concurrent file processing
   - Large dataset handling
   - Memory cleanup efficiency

## Success Criteria
- Performance regressions detected early
- Consistent monitoring of critical operations
- Clear performance trend tracking
- Actionable optimization recommendations