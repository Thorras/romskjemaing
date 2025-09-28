# 📚 IFC Room Schedule - API Documentation

## Overview

The IFC Room Schedule application provides a comprehensive API for processing IFC files and extracting space data. This documentation covers all major components and their usage.

---

## 🏗️ Core Components

### 1. IFC File Reader (`ifc_file_reader.py`)

#### `IfcFileReader`
Main class for loading and validating IFC files.

```python
from ifc_room_schedule.parser.ifc_file_reader import IfcFileReader

# Initialize reader
reader = IfcFileReader()

# Load IFC file
success, message = reader.load_file("path/to/file.ifc")
if success:
    ifc_file = reader.ifc_file
```

**Methods:**
- `load_file(file_path: str) -> Tuple[bool, str]`
- `validate_file(file_path: str) -> Tuple[bool, str]`
- `get_file_info() -> Dict[str, Any]`
- `close_file() -> None`

---

### 2. Space Extractor (`ifc_space_extractor.py`)

#### `IfcSpaceExtractor`
Extracts space data from IFC files with performance optimization.

```python
from ifc_room_schedule.parser.ifc_space_extractor import IfcSpaceExtractor

# Initialize extractor
extractor = IfcSpaceExtractor(ifc_file)

# Extract spaces with lazy loading
spaces = extractor.extract_spaces(lazy_load=True, batch_size=50)

# Get specific space
space = extractor.get_space_by_guid("space_guid_here")
```

**Methods:**
- `extract_spaces(lazy_load: bool = False, batch_size: int = 50) -> List[SpaceData]`
- `get_space_by_guid(guid: str) -> Optional[SpaceData]`
- `get_space_count() -> int`
- `validate_spaces() -> Tuple[bool, List[str]]`

**Performance Features:**
- **Lazy Loading**: Process spaces in batches to reduce memory usage
- **Caching**: Automatic caching of extracted data
- **Batch Processing**: Configurable batch sizes for large files

---

### 3. Export System

#### JSON Export (`json_builder.py`)

```python
from ifc_room_schedule.export.json_builder import JsonBuilder

builder = JsonBuilder()
builder.set_source_file("input.ifc")

# Export with validation
success, messages = builder.export_to_json(
    spaces=spaces,
    filename="output.json",
    validate=True
)
```

#### CSV Export (`csv_exporter.py`)

```python
from ifc_room_schedule.export.csv_exporter import CsvExporter

exporter = CsvExporter()
success, message = exporter.export_to_csv(
    spaces=spaces,
    filename="output.csv",
    include_surfaces=True,
    include_boundaries=True
)
```

#### Excel Export (`excel_exporter.py`)

```python
from ifc_room_schedule.export.excel_exporter import ExcelExporter

exporter = ExcelExporter()
success, message = exporter.export_to_excel(
    spaces=spaces,
    filename="output.xlsx",
    include_surfaces=True
)
```

#### PDF Export (`pdf_exporter.py`)

```python
from ifc_room_schedule.export.pdf_exporter import PdfExporter

exporter = PdfExporter()
success, message = exporter.export_to_pdf(
    spaces=spaces,
    filename="output.pdf",
    page_size=A4
)
```

---

## 📊 Data Models

### `SpaceData`
Core data structure for IFC spaces.

```python
from ifc_room_schedule.data.space_model import SpaceData

space = SpaceData(
    guid="unique_identifier",
    name="Room Name",
    long_name="Full Room Description",
    description="Room purpose",
    object_type="IfcSpace",
    elevation=0.0,
    floor_height=3.0,
    area=25.5,
    volume=76.5
)

# Add surfaces
space.add_surface(surface_data)

# Add relationships
space.add_relationship(relationship_data)

# Get area calculations
total_area = space.get_total_surface_area()
wall_area = space.get_surface_area_by_type("Wall")
```

### `SurfaceData`
Structure for surface information.

```python
from ifc_room_schedule.data.surface_model import SurfaceData

surface = SurfaceData(
    surface_id="surface_123",
    surface_type="Wall",
    area=12.5,
    material="Concrete",
    orientation="North"
)
```

---

## 🎛️ UI Components

### Main Window (`main_window.py`)

```python
from ifc_room_schedule.ui.main_window import MainWindow

# Create application
app = QApplication(sys.argv)
window = MainWindow()

# Load file programmatically
window.process_ifc_file("path/to/file.ifc")

# Show window
window.show()
app.exec()
```

**Key Features:**
- **Threading Support**: Non-blocking operations with progress feedback
- **Error Handling**: Comprehensive error reporting and recovery
- **Performance Monitoring**: Built-in resource monitoring
- **Keyboard Shortcuts**: Full keyboard navigation support

---

## ⚡ Performance Optimization

### Lazy Loading
For large IFC files, use lazy loading to process data in batches:

```python
# Enable lazy loading with custom batch size
spaces = extractor.extract_spaces(lazy_load=True, batch_size=25)
```

### Memory Management
Automatic memory management with manual cleanup options:

```python
# Manual memory cleanup
main_window.free_memory_resources()

# Check memory usage
stats = main_window.get_memory_stats()
```

### Caching System
All extractors implement intelligent caching:

```python
# First call - extracts and caches
spaces = extractor.extract_spaces()

# Subsequent calls - returns cached data
spaces_cached = extractor.extract_spaces()

# Clear cache when needed
extractor._spaces_cache = None
```

---

## 🔧 Enhanced Logging

### Using Enhanced Logger

```python
from ifc_room_schedule.utils.enhanced_logging import enhanced_logger, ErrorCategory, ErrorSeverity

# Log with performance timing
operation_id = enhanced_logger.start_operation_timing("my_operation", "file.ifc")
# ... perform operation ...
timing = enhanced_logger.finish_operation_timing(operation_id)

# Create structured error reports
error_report = enhanced_logger.create_error_report(
    ErrorCategory.MEMORY,
    ErrorSeverity.HIGH,
    "Operation Failed",
    "Detailed error message",
    exception=exception_object,
    recovery_suggestions=["Try smaller file", "Restart application"]
)
```

### Error Categories
- `MEMORY`: Memory-related errors
- `IO`: File input/output errors  
- `THREADING`: Threading and concurrency issues
- `TIMEOUT`: Operation timeout errors
- `PARSING`: IFC parsing errors
- `VALIDATION`: Data validation errors
- `SYSTEM`: System-level errors
- `USER_INPUT`: User input validation errors

---

## 🧪 Testing and Validation

### Data Validation

```python
# Validate spaces
is_valid, errors = extractor.validate_spaces()
if not is_valid:
    for error in errors:
        print(f"Validation error: {error}")

# Validate export data
is_valid, errors = json_builder.validate_export_data(json_data)
```

### Performance Testing

```python
# Monitor operation performance
with enhanced_logger.operation_timing("test_operation"):
    # Your operation here
    result = perform_operation()
```

---

## 🔌 Integration Examples

### Basic File Processing

```python
from ifc_room_schedule.parser import IfcFileReader, IfcSpaceExtractor
from ifc_room_schedule.export import JsonBuilder

# Load file
reader = IfcFileReader()
success, message = reader.load_file("building.ifc")

if success:
    # Extract spaces
    extractor = IfcSpaceExtractor(reader.ifc_file)
    spaces = extractor.extract_spaces(lazy_load=True)
    
    # Export to JSON
    builder = JsonBuilder()
    builder.set_source_file("building.ifc")
    success, messages = builder.export_to_json(spaces, "output.json")
    
    if success:
        print(f"Exported {len(spaces)} spaces successfully")
```

### Batch Processing

```python
import os
from pathlib import Path

def process_ifc_folder(folder_path: str, output_folder: str):
    """Process all IFC files in a folder."""
    reader = IfcFileReader()
    extractor = IfcSpaceExtractor()
    builder = JsonBuilder()
    
    for ifc_file in Path(folder_path).glob("*.ifc"):
        print(f"Processing {ifc_file.name}...")
        
        # Load file
        success, message = reader.load_file(str(ifc_file))
        if not success:
            print(f"Failed to load {ifc_file.name}: {message}")
            continue
        
        # Extract spaces with performance optimization
        extractor.set_ifc_file(reader.ifc_file)
        spaces = extractor.extract_spaces(lazy_load=True, batch_size=25)
        
        # Export
        output_file = os.path.join(output_folder, f"{ifc_file.stem}.json")
        builder.set_source_file(str(ifc_file))
        success, messages = builder.export_to_json(spaces, output_file)
        
        if success:
            print(f"Exported {len(spaces)} spaces from {ifc_file.name}")
        else:
            print(f"Export failed: {messages}")
        
        # Clean up for next file
        extractor._spaces_cache = None
```

---

## 🚀 Advanced Features

### Custom Progress Callbacks

```python
def progress_callback(current: int, total: int, operation: str, detail: str):
    """Custom progress callback function."""
    percent = (current / total) * 100 if total > 0 else 0
    print(f"{operation}: {percent:.1f}% - {detail}")

# Use with UI components
main_window.operation_worker.detailed_progress_updated.connect(progress_callback)
```

### Error Recovery

```python
# Implement custom error recovery
def custom_error_handler(error_category: ErrorCategory, error: Exception):
    """Custom error handling logic."""
    if error_category == ErrorCategory.MEMORY:
        # Handle memory errors
        return "retry_with_smaller_batch"
    elif error_category == ErrorCategory.PARSING:
        # Handle parsing errors
        return "skip_invalid_entities"
    return "abort"
```

---

## 📋 Configuration

### Performance Settings

```python
# Configure batch sizes for different file sizes
PERFORMANCE_CONFIG = {
    "small_file_threshold": 10 * 1024 * 1024,  # 10MB
    "medium_file_threshold": 50 * 1024 * 1024,  # 50MB
    "large_file_threshold": 100 * 1024 * 1024,  # 100MB
    "batch_sizes": {
        "small": 100,
        "medium": 50,
        "large": 25,
        "huge": 10
    }
}
```

### Export Settings

```python
# Configure export options
EXPORT_CONFIG = {
    "json": {"indent": 2, "ensure_ascii": False},
    "csv": {"delimiter": ",", "encoding": "utf-8"},
    "excel": {"engine": "openpyxl"},
    "pdf": {"page_size": "A4", "margin": 72}
}
```

---

## 🔍 Debugging

### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Or use enhanced logger
enhanced_logger.logger.setLevel(logging.DEBUG)
```

### Performance Profiling

```python
# Profile memory usage
import psutil
process = psutil.Process()
memory_before = process.memory_info().rss

# Your operation here
spaces = extractor.extract_spaces()

memory_after = process.memory_info().rss
memory_used = (memory_after - memory_before) / (1024 * 1024)
print(f"Memory used: {memory_used:.1f}MB")
```

---

*API Documentation Version: 1.0.0*
*Last Updated: September 28, 2025*
